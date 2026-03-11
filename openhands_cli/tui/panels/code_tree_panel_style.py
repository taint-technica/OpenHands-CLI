"""CSS styles for the code tree side panel."""

CODE_TREE_PANEL_STYLE = """
    CodeTreeSidePanel {
        split: right;
        width: 33%;
        min-width: 30;
        max-width: 60;
        border-left: vkey $foreground 30%;
        padding: 0 1;
        layout: vertical;
        height: 100%;
    }

    .code-tree-header-row {
        width: 100%;
        height: 1;
        align-vertical: middle;
        margin-bottom: 1;
    }

    .code-tree-header {
        color: $primary;
        text-style: bold;
        width: 1fr;
        height: 1;
    }

    #code-tree-close-btn {
        min-width: 3;
        width: auto;
        height: 1;
        background: transparent;
        color: #aaaaaa;
        border: none;
        padding: 0;
        margin: 0;
        text-style: bold;
    }

    #code-tree-close-btn:hover {
        background: #333333;
        color: $error;
        border: none;
    }

    #code-tree-close-btn:focus {
        background: transparent;
        color: #aaaaaa;
        border: none;
        text-style: bold;
    }

    #code-tree-close-btn.-active {
        background: #333333;
        color: $error;
        border: none;
    }

    #code-tree-filter {
        width: 100%;
        height: 3;
        margin-bottom: 1;
        background: $surface;
        color: $foreground;
        border: round $primary;
    }

    #code-tree-filter:focus {
        border: round $primary;
        background: $surface;
    }

    #code-tree-container {
        height: 1fr;
        overflow-y: auto;
        scrollbar-size-vertical: 1;
    }

    Tree {
        background: $surface;
        color: $foreground;
    }

    Tree > .tree--cursor {
        background: $primary 50%;
        color: $text;
    }

    Tree > .tree--highlight {
        background: $primary 30%;
    }

    .code-tree-empty {
        color: $warning;
        text-style: italic;
        margin-top: 1;
    }

    .code-tree-loading {
        color: $primary;
        text-style: italic;
        margin-top: 1;
    }
"""
