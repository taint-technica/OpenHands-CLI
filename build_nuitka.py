#!/usr/bin/env python3
"""
Build script for OpenHands CLI using Nuitka.

This Python script provides more control over the Nuitka build process
compared to the shell script version.

Nuitka compiles Python to C++ and then to machine code, providing:
- Better protection than PyInstaller (cannot easily decompile)
- Potential performance improvements (optimized C code)
- Single binary distribution

Usage:
    python build_nuitka.py

Requirements:
    - Python 3.12+
    - Nuitka (installed automatically if missing)
    - C compiler (gcc/g++ on Linux, Xcode on macOS, MSVC on Windows)

Example:
    $ python build_nuitka.py
    🚀 Building OpenHands CLI with Nuitka...
    ✅ Build completed!
    📁 Binary: dist/openhands
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def print_info(message: str) -> None:
    """Print info message."""
    print(f"ℹ️  {message}")


def print_success(message: str) -> None:
    """Print success message."""
    print(f"✅ {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"⚠️  {message}")


def print_error(message: str) -> None:
    """Print error message."""
    print(f"❌ {message}")


def check_nuitka() -> bool:
    """Check if Nuitka is installed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        version = result.stdout.strip().split("\n")[0]
        print_success(f"Nuitka found: {version}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_nuitka() -> None:
    """Install Nuitka and dependencies."""
    print_warning("Nuitka not found. Installing...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "nuitka", "zstandard"],
        check=True,
    )
    print_success("Nuitka installed successfully")


def check_c_compiler() -> bool:
    """Check if C compiler is available."""
    compilers = ["gcc", "clang", "cl"]
    for compiler in compilers:
        try:
            result = subprocess.run(
                [compiler, "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            version = result.stdout.strip().split("\n")[0]
            print_success(f"C compiler found: {compiler} - {version}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    print_error("No C compiler found. Please install:")
    print_error("  Ubuntu/Debian: sudo apt-get install build-essential")
    print_error("  macOS: xcode-select --install")
    print_error("  Windows: Install MSVC or MinGW")
    return False


def clean_build_directories() -> None:
    """Clean up previous build artifacts."""
    print_info("Cleaning previous build artifacts...")

    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)

    # Clean __pycache__ and .pyc files recursively
    for root, dirs, files in os.walk("."):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                shutil.rmtree(os.path.join(root, dir_name), ignore_errors=True)
        for file in files:
            if file.endswith(".pyc"):
                os.remove(os.path.join(root, file))

    print_success("Cleanup complete")


def build_with_nuitka() -> bool:
    """Build the executable using Nuitka."""
    print_info("Starting Nuitka compilation...")
    print_info("This may take 2-5 minutes depending on your system...")
    print()

    # Build command
    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--enable-plugin=pylint-warnings",
        "--output-dir=dist",
        "--output-filename=openhands",
        "--include-package=openhands_cli",
        "--include-package=openhands.sdk",
        "--include-package=openhands.tools",
        "--include-package=textual",
        "--include-package=rich",
        "--include-package=prompt_toolkit",
        "--include-package=pydantic",
        "--include-package=litellm",
        "--include-package=tiktoken",
        "--include-package=fastmcp",
        "--include-package=mcp",
        "--include-package=agent_client_protocol",
        "--include-package=textual_autocomplete",
        "--include-package=textual_serve",
        "--include-package=typer",
        "--include-package=click",
        "--include-package=httpx",
        "--include-package=h11",
        "--include-package=anyio",
        "--include-package=sniffio",
        "--include-package=certifi",
        "--include-package=dotenv",
        "--nofollow-imports",
        "--assume-yes-for-downloads",
        "--python-flag=no_site",
        "--python-flag=optimize",
        "--standalone",
        "openhands_cli/entrypoint.py",
    ]

    print(f"Running: {' '.join(cmd)}")
    print()

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Build failed: {e}")
        return False


def verify_build() -> tuple[bool, str]:
    """Verify the build succeeded and return binary path."""
    dist_dir = Path("dist")
    if not dist_dir.exists():
        return False, ""

    # Find the binary
    binary_names = ["openhands", "openhands.bin", "openhands.exe"]
    for name in binary_names:
        binary_path = dist_dir / name
        if binary_path.exists():
            return True, str(binary_path)

    return False, ""


def verify_protection(binary_path: str) -> None:
    """Verify that instructions are protected in the binary."""
    print_info("Verifying protection...")
    print()

    try:
        # Try to find hardcoded instructions in binary strings
        if os.name == "nt":  # Windows
            print_warning("String extraction on Windows requires additional tools")
        else:
            result = subprocess.run(
                ["strings", binary_path],
                capture_output=True,
                text=True,
                check=False,
            )
            output = result.stdout

            # Check for sensitive strings
            sensitive_patterns = [
                "core_coding_instructions",
                "security_guidelines",
                "Your proprietary instructions",
            ]

            found_sensitive = False
            for pattern in sensitive_patterns:
                if pattern in output:
                    print_warning(f"⚠️  Found sensitive string: {pattern}")
                    found_sensitive = True

            if not found_sensitive:
                print_success("No hardcoded instructions found in binary strings")
                print_success("✅ Protection verification passed")
    except Exception as e:
        print_warning(f"Could not verify protection: {e}")

    print()


def main() -> int:
    """Main function."""
    print("🚀 OpenHands CLI - Nuitka Build Script")
    print("=" * 50)
    print()

    # Check if running from correct directory
    if not Path("openhands_cli/entrypoint.py").exists():
        print_error("Must run from project root directory")
        print_error("(where openhands_cli/ folder exists)")
        return 1

    # Check Python version
    print_info(f"Python version: {sys.version}")

    # Check/install Nuitka
    if not check_nuitka():
        install_nuitka()

    # Check C compiler
    if not check_c_compiler():
        return 1

    # Clean previous builds
    clean_build_directories()

    # Build
    if not build_with_nuitka():
        return 1

    # Verify build
    success, binary_path = verify_build()
    if not success:
        print_error("Build failed! Binary not found in dist/")
        return 1

    print()
    print_success("Build completed successfully!")
    print()

    # Get file size
    file_size_mb = Path(binary_path).stat().st_size / (1024 * 1024)
    print(f"📁 Binary location: {binary_path}")
    print(f"📊 Binary size: {file_size_mb:.1f} MB")
    print()

    # Verify protection
    verify_protection(binary_path)

    # Print usage instructions
    print_info("To test the binary:")
    if os.name == "nt":  # Windows
        print(f"  {binary_path} --help")
        print(f"  {binary_path} -t \"Write a hello world function\"")
    else:
        print(f"  ./{binary_path} --help")
        print(f"  ./{binary_path} -t \"Write a hello world function\"")
    print()

    print_success("🎉 Build process completed!")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n")
        print_warning("Build cancelled by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Build failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
