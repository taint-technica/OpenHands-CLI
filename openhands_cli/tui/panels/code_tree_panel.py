"""Code tree side panel widget for displaying and navigating project structure.

This panel displays a tree view of the project's file structure, allowing users
to easily browse and mention files/folders by clicking or pressing Enter.

The panel integrates with InputField to insert @mentions when a file is selected.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.css.query import NoMatches
from textual.widgets import Button, Input, Static, Tree
from textual.widgets.tree import TreeNode

from openhands_cli.locations import get_work_dir
from openhands_cli.tui.panels.code_tree_panel_style import CODE_TREE_PANEL_STYLE


if TYPE_CHECKING:
    from openhands_cli.tui.textual_app import OpenHandsApp


logger = logging.getLogger(__name__)


class CodeTreeSidePanel(Container):
    """Side panel widget that displays the project code tree.

    This panel provides a navigable tree view of the project structure,
    allowing users to click or press Enter on files to mention them in
    the input field (inserts @path/to/file).

    Features:
    - Expandable/collapsible directory nodes
    - File and folder icons (📁 for directories, 📄 for files)
    - Filter input to quickly find files
    - Keyboard navigation (arrow keys, Enter to expand/select)
    - Integration with InputField for @mentions
    """

    DEFAULT_CSS = CODE_TREE_PANEL_STYLE

    # File extensions to prioritize (show first in listings)
    PRIORITY_EXTENSIONS: ClassVar[set[str]] = {
        ".py",
        ".js",
        ".ts",
        ".java",
        ".go",
        ".rs",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".cs",
        ".rb",
        ".php",
        ".swift",
        ".kt",
        ".scala",
        ".sh",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".md",
        ".txt",
        ".sql",
        ".html",
        ".css",
        ".scss",
        ".vue",
        ".jsx",
        ".tsx",
    }

    # Directories to skip by default
    SKIP_DIRECTORIES: ClassVar[set[str]] = {
        ".git",
        ".svn",
        ".hg",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".venv",
        "venv",
        "env",
        ".env",
        "node_modules",
        ".idea",
        ".vscode",
        "dist",
        "build",
        ".tox",
        ".eggs",
        "*.egg-info",
    }

    # File extensions to skip
    SKIP_EXTENSIONS: ClassVar[set[str]] = {
        ".pyc",
        ".pyo",
        ".so",
        ".dll",
        ".dylib",
        ".exe",
        ".bin",
        ".o",
        ".a",
        ".lib",
        ".lock",
        ".bak",
        ".swp",
        ".swo",
        "*~",
    }

    def __init__(
        self,
        app: OpenHandsApp,
        **kwargs,
    ):
        """Initialize the code tree side panel.

        Args:
            app: The OpenHands app instance
        """
        super().__init__(**kwargs)
        self._oh_app = app
        self._work_dir = Path(get_work_dir())
        self._filter_text = ""

    @classmethod
    def toggle(cls, app: OpenHandsApp) -> None:
        """Toggle the code tree side panel on/off.

        Args:
            app: The OpenHands app instance
        """
        try:
            existing = app.query_one(cls)
        except NoMatches:
            existing = None

        if existing is not None:
            existing.remove()
            return

        content_area = app.query_one("#content_area", Horizontal)
        panel = cls(app=app)
        content_area.mount(panel)

    def compose(self) -> ComposeResult:
        """Compose the code tree side panel content."""
        with Horizontal(classes="code-tree-header-row"):
            yield Static("Code Tree", classes="code-tree-header", id="code-tree-header")
            yield Button("✕", id="code-tree-close-btn", classes="code-tree-close-btn")
        yield Input(
            placeholder="Filter files...",
            id="code-tree-filter",
        )
        yield VerticalScroll(id="code-tree-container")

    def on_mount(self) -> None:
        """Called when the panel is mounted."""
        self._build_tree()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle close button press."""
        if event.button.id == "code-tree-close-btn":
            self.remove()

    def key_escape(self) -> None:
        """Handle Escape key: close the panel."""
        self.remove()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter input changes."""
        if event.input.id == "code-tree-filter":
            self._filter_text = event.value.lower()
            self._apply_filter()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection (file or folder)."""
        node = event.node
        if node.data is None:
            # Directory node - toggle expansion
            node.toggle()
            return

        # File node - mention it
        file_path = node.data
        if isinstance(file_path, Path):
            self._mention_file(file_path)

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        """Handle tree node expansion."""
        node = event.node
        if node.data is None and not node.children:
            # Directory node that hasn't been loaded yet
            self._load_directory(node)

    def _build_tree(self) -> None:
        """Build the initial tree structure."""
        container = self.query_one("#code-tree-container", VerticalScroll)
        container.remove_children()

        tree = Tree("📁 " + self._work_dir.name, id="code-tree")
        tree.guide_depth = 4
        tree.show_root = True
        tree.show_guides = True

        # Load root directory contents
        self._load_directory(tree.root)

        container.mount(tree)

        # Focus the filter input
        self.query_one("#code-tree-filter", Input).focus()

    def _load_directory(self, node: TreeNode) -> None:
        """Load directory contents into a tree node.

        Args:
            node: The tree node to populate with directory contents
        """
        if node.data is None:
            # Root node or directory node
            dir_path = self._work_dir
            if node != node.tree.root:
                # Get path from parent
                parent_path = node.parent.data if node.parent else self._work_dir
                if parent_path and isinstance(parent_path, Path):
                    dir_path = parent_path
        else:
            dir_path = node.data

        if not isinstance(dir_path, Path) or not dir_path.is_dir():
            return

        try:
            items = list(dir_path.iterdir())
        except (OSError, PermissionError) as e:
            logger.warning("Cannot access directory %s: %s", dir_path, e)
            node.set_label(f"⚠️ {dir_path.name} (access denied)")
            return

        # Separate files and directories
        directories = []
        files = []

        for item in items:
            # Skip hidden files unless filter is active
            if item.name.startswith(".") and not self._filter_text:
                continue

            # Skip excluded directories and files
            if self._should_skip(item):
                continue

            if item.is_dir():
                directories.append(item)
            elif item.is_file():
                files.append(item)

        # Sort: directories first, then files (priority extensions first)
        directories.sort(key=lambda x: x.name.lower())
        files.sort(key=lambda x: (self._get_priority(x), x.name.lower()))

        # Add directories as nodes (without data - will be loaded on expand)
        for directory in directories:
            if self._filter_text and self._filter_text not in directory.name.lower():
                continue
            label = f"📁 {directory.name}/"
            node.add(label, data=None)  # None = directory, load on expand

        # Add files as nodes (with Path data)
        for file in files:
            if self._filter_text and self._filter_text not in file.name.lower():
                continue
            icon = self._get_file_icon(file)
            label = f"{icon} {file.name}"
            node.add(label, data=file)

        # Note: Children are already sorted when added, no need to call sort_children

    def _get_file_icon(self, file_path: Path) -> str:
        """Get an appropriate icon for a file based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            Icon emoji for the file type
        """
        extension = file_path.suffix.lower()

        icon_map = {
            ".py": "🐍",
            ".js": "📜",
            ".ts": "📘",
            ".java": "☕",
            ".go": "🔹",
            ".rs": "🦀",
            ".cpp": "⚙️",
            ".c": "⚙️",
            ".h": "📐",
            ".cs": "🔷",
            ".rb": "💎",
            ".php": "🐘",
            ".swift": "🍎",
            ".kt": "📱",
            ".scala": "📈",
            ".sh": "📟",
            ".yaml": "⚙️",
            ".yml": "⚙️",
            ".json": "📋",
            ".toml": "⚙️",
            ".md": "📝",
            ".txt": "📄",
            ".sql": "🗄️",
            ".html": "🌐",
            ".css": "🎨",
            ".scss": "🎨",
            ".vue": "📱",
            ".jsx": "⚛️",
            ".tsx": "⚛️",
            ".xml": "📋",
            ".ini": "⚙️",
            ".cfg": "⚙️",
            ".conf": "⚙️",
            ".env": "🔒",
            ".lock": "🔒",
            ".gitignore": "🙈",
            ".dockerfile": "🐳",
            ".pyi": "🐍",
        }

        return icon_map.get(extension, "📄")

    def _get_priority(self, file_path: Path) -> int:
        """Get sort priority for a file (lower = higher priority).

        Args:
            file_path: Path to the file

        Returns:
            Priority value (0 for priority extensions, 1 for others)
        """
        return 0 if file_path.suffix.lower() in self.PRIORITY_EXTENSIONS else 1

    def _should_skip(self, item: Path) -> bool:
        """Check if an item should be skipped.

        Args:
            item: Path to the file or directory

        Returns:
            True if the item should be skipped, False otherwise
        """
        # Check directory names
        if item.name in self.SKIP_DIRECTORIES:
            return True

        # Check if any skip pattern matches
        for pattern in self.SKIP_DIRECTORIES:
            if pattern.endswith("*") and item.name.startswith(pattern[:-1]):
                return True

        # Check file extensions
        if item.is_file():
            if item.suffix.lower() in self.SKIP_EXTENSIONS:
                return True

        return False

    def _apply_filter(self) -> None:
        """Apply the current filter to the tree."""
        tree = self.query_one("#code-tree", Tree)
        if not tree:
            return

        # Rebuild tree with filter
        tree.clear()
        self._load_directory(tree.root)

    def _mention_file(self, file_path: Path) -> None:
        """Insert a file mention into the input field.

        Args:
            file_path: Path to the file to mention
        """
        try:
            # Use InputField's built-in method for inserting file mentions
            self._oh_app.input_field.insert_file_mention(file_path)

            # Notify user
            self._oh_app.notify(
                f"Added {file_path.name}",
                title="File mentioned",
                timeout=1.5,
            )

        except Exception as e:
            logger.warning("Failed to mention file %s: %s", file_path, e)
            self._oh_app.notify(
                f"Could not add {file_path.name}",
                title="Error",
                severity="error",
                timeout=2,
            )
