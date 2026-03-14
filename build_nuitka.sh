#!/bin/bash
#
# Build script for OpenHands CLI using Nuitka.
#
# Nuitka compiles Python to C++ and then to machine code, providing:
# - Better protection than PyInstaller (cannot easily decompile)
# - Potential performance improvements
# - Single binary distribution
#
# Usage:
#   ./build_nuitka.sh
#
# Requirements:
#   - Python 3.12+
#   - Nuitka (installed automatically if missing)
#   - C compiler (gcc/g++ on Linux, Xcode on macOS, MSVC on Windows)
#

set -e  # Exit on any error

echo "🚀 OpenHands CLI - Nuitka Build Script"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running in correct directory
if [ ! -f "openhands_cli/entrypoint.py" ]; then
    print_error "Must run from project root directory (where openhands_cli/ folder exists)"
    exit 1
fi

# Check Python version
print_info "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_info "Python version: $PYTHON_VERSION"

# Check if Nuitka is installed
print_info "Checking for Nuitka..."

# Try using uv run first (preferred method for this project)
if command -v uv &> /dev/null; then
    if uv run python -m nuitka --version &> /dev/null; then
        NUKITA_VERSION=$(uv run python -m nuitka --version 2>&1 | head -1)
        print_success "Nuitka found via uv: $NUKITA_VERSION"
        PYTHON_CMD="uv run python"
    else
        print_warning "Nuitka not found. Installing with uv..."
        uv add --dev nuitka zstandard --quiet
        PYTHON_CMD="uv run python"
        print_success "Nuitka installed via uv"
    fi
elif [ -f ".venv/bin/python" ]; then
    # Fallback to .venv if uv not available
    if .venv/bin/python -m nuitka --version &> /dev/null; then
        NUKITA_VERSION=$(.venv/bin/python -m nuitka --version 2>&1 | head -1)
        print_success "Nuitka found: $NUKITA_VERSION"
        PYTHON_CMD=".venv/bin/python"
    else
        print_error "Nuitka not found in .venv and uv not available."
        print_error "Please install with: uv add --dev nuitka zstandard"
        exit 1
    fi
else
    # Last resort: system python
    if python3 -m nuitka --version &> /dev/null; then
        NUKITA_VERSION=$(python3 -m nuitka --version 2>&1 | head -1)
        print_success "Nuitka found: $NUKITA_VERSION"
        PYTHON_CMD="python3"
    else
        print_error "Nuitka not found. Please install:"
        print_error "  Option 1 (recommended): uv add --dev nuitka zstandard"
        print_error "  Option 2: pip3 install --break-system-packages nuitka zstandard"
        exit 1
    fi
fi

# Check for C compiler
print_info "Checking for C compiler..."
if command -v gcc &> /dev/null; then
    GCC_VERSION=$(gcc --version | head -1)
    print_success "GCC found: $GCC_VERSION"
elif command -v clang &> /dev/null; then
    CLANG_VERSION=$(clang --version | head -1)
    print_success "Clang found: $CLANG_VERSION"
else
    print_error "No C compiler found. Please install gcc or clang."
    print_error "  Ubuntu/Debian: sudo apt-get install build-essential"
    print_error "  macOS: xcode-select --install"
    print_error "  Windows: Install MSVC or MinGW"
    exit 1
fi

# Check for patchelf (required for Linux standalone mode)
print_info "Checking for patchelf (required for Linux standalone mode)..."
USE_STANDALONE=true
if ! command -v patchelf &> /dev/null; then
    print_warning "patchelf not found (required for Nuitka standalone mode)"
    print_warning "Building without --standalone flag (will create larger output with dependencies)"
    print_info "To enable standalone mode, install patchelf:"
    print_info "  sudo apt-get install patchelf"
    USE_STANDALONE=false
else
    PATCHELF_VERSION=$(patchelf --version)
    print_success "patchelf found: $PATCHELF_VERSION"
fi

# Clean previous builds
print_info "Cleaning previous build artifacts..."
rm -rf build/ dist/ __pycache__/
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
print_success "Cleanup complete"

# Build with Nuitka
print_info "Starting Nuitka compilation..."
print_info "This may take 2-5 minutes depending on your system..."
echo ""

# Build command - conditionally include --standalone
NUKITA_CMD=(
    $PYTHON_CMD -m nuitka
    --onefile
    --enable-plugin=pylint-warnings
    --output-dir=dist
    --output-filename=openhands
    --include-package=openhands_cli
    --include-package=openhands.sdk
    --include-package=openhands.tools
    --include-package=textual
    --include-package=rich
    --include-package=prompt_toolkit
    --include-package=pydantic
    --include-package=litellm
    --include-package=tiktoken
    --include-package=fastmcp
    --include-package=mcp
    --include-package=acp
    --include-package=textual_autocomplete
    --include-package=textual_serve
    --include-package=typer
    --include-package=click
    --include-package=httpx
    --include-package=h11
    --include-package=anyio
    --include-package=sniffio
    --include-package=certifi
    --include-package=dotenv
    --assume-yes-for-downloads
    --python-flag=no_site
)

# Note: Removed --nofollow-imports for onefile mode (causes issues)
# Note: Removed --python-flag=optimize (not supported in Nuitka 4.x)

# Add --standalone only if patchelf is available
if [ "$USE_STANDALONE" = true ]; then
    NUKITA_CMD+=(--standalone)
    print_info "Building in standalone mode (single binary)"
else
    print_info "Building in non-standalone mode (requires .dist folder)"
fi

NUKITA_CMD+=(openhands_cli/entrypoint.py)

"${NUKITA_CMD[@]}"

# Check if build succeeded
if [ -f "dist/openhands" ] || [ -f "dist/openhands.bin" ]; then
    print_success "Build completed successfully!"
    echo ""

    # Find the actual binary name
    if [ -f "dist/openhands.bin" ]; then
        BINARY="dist/openhands.bin"
    elif [ -f "dist/openhands" ]; then
        BINARY="dist/openhands"
    fi

    # Get file size
    FILE_SIZE=$(du -h "$BINARY" | cut -f1)

    echo "📁 Binary location: $BINARY"
    echo "📊 Binary size: $FILE_SIZE"
    echo ""

    # Verify protection
    print_info "Verifying protection..."
    echo ""
    print_warning "Testing if strings can extract content (should show minimal output):"
    strings "$BINARY" 2>/dev/null | grep -i "core_coding_instructions" || echo "  ✅ No hardcoded instructions found in binary strings"
    echo ""

    print_info "To test the binary:"
    if [ -f ".venv/bin/python" ]; then
        echo "  (Binary is standalone, can run directly)"
    fi
    echo "  $BINARY --help"
    echo "  $BINARY -t \"Write a hello world function\""
    echo ""

    print_success "🎉 Build process completed!"

else
    print_error "Build failed! Binary not found in dist/"
    exit 1
fi
