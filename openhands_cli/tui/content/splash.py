"""Welcome message utilities for OpenHands CLI textual app."""

from textual.theme import Theme

from openhands_cli.version_check import check_for_updates


def get_conversation_text(conversation_id: str, *, theme: Theme) -> str:
    """Get the formatted conversation initialization text.

    Args:
        conversation_id: The conversation ID to display
        theme: Theme to use for colors

    Returns:
        Formatted string with conversation initialization message
    """
    return f"[{theme.accent}]Initialized conversation[/] {conversation_id}"


def get_openhands_banner() -> str:
    """Get the OpenHands ASCII art banner."""

    banner_lines = r"""
        [#253b8f]▄[/][#683293]▄▄▄▄▄[/]    [#fcb42d]▄▄▄▄▄▄[/][#ef5c31]▄[/]
        [#253b8f]█[/]     [#a92062]▀▄[/]        [#ef5c31]█[/]
        [#253b8f]█[/]       [#a92062]▀▄[/]      [#ef5c31]█[/]
        [#253b8f]█[/][#0f72b9]▄▄▄▄▄[/]    [#a92062]▀[/][#ed212e]▄▄▄▄▄[/][#ef5c31]█[/]
            [#35b0e4]▀▄[/]         
                [#35b0e4]▀▄[/]       
            [#8bc63f]▄[/]   [#1a8f85]█[/]      
            [#8bc63f]█[/]   [#1a8f85]█[/]      
            [#8bc63f]█[/]   [#1a8f85]█[/]      
            [#8bc63f]█[/]   [#1a8f85]█[/]      
            [#34b45a]▀▀▀▀▀[/]
    """

    banner_lines = [
        r"[#253b8f]▄[/][#683293]▄▄▄▄▄[/]    [#fcb42d]▄▄▄▄▄▄[/][#ef5c31]▄[/]",
        r"[#253b8f]█[/]     [#a92062]▀▄[/]        [#ef5c31]█[/]",
        r"[#253b8f]█[/]       [#a92062]▀▄[/]      [#ef5c31]█[/]",
        r"[#253b8f]█[/][#0f72b9]▄▄▄▄▄[/]    [#a92062]▀[/][#ed212e]▄▄▄▄▄[/][#ef5c31]█[/]",
        r"      [#35b0e4]▀▄[/]         ",
        r"        [#35b0e4]▀▄[/]       ",
        r"      [#8bc63f]▄[/]   [#1a8f85]█[/]      ",
        r"      [#8bc63f]█[/]   [#1a8f85]█[/]      ",
        r"      [#8bc63f]█[/]   [#1a8f85]█[/]      ",
        r"      [#8bc63f]█[/]   [#1a8f85]█[/]      ",
        r"[#34b45a]▀▀▀▀▀[/]",
    ]

    return "\n".join(banner_lines)


def get_splash_content(
    conversation_id: str,
    *,
    theme: Theme,
    has_critic: bool = False,
) -> dict:
    """Get structured splash screen content for native Textual widgets.

    Args:
        conversation_id: Optional conversation ID to display
        theme: Theme to use for colors
        has_critic: Whether the agent has a critic configured
    """
    # Use theme colors
    primary_color = theme.primary

    # Use Rich markup for colored banner (apply color to each line)
    banner_lines = get_openhands_banner().split("\n")
    colored_banner_lines = [f"[{primary_color}]{line}[/]" for line in banner_lines]
    banner = "\n".join(colored_banner_lines)

    # Get version information
    version_info = check_for_updates()

    # Create structured content as dictionary
    content = {
        "banner": banner,
        "version": f"\nTechnica CLI v{version_info.current_version}",
        "status_text": "All set up!",
        "conversation_text": get_conversation_text(conversation_id, theme=theme),
        "conversation_id": conversation_id,
        "instructions_header": f"[{primary_color}]What do you want to build?[/]",
        "instructions": [
            "1. Ask questions, edit files, or run commands.",
            "2. Use @ to look up a file in the folder structure",
            (
                "3. Type /help for help, /feedback to leave anonymous feedback, "
                "or / to scroll through available commands"
            ),
        ],
        "update_notice": None,
        "critic_notice": None,
    }

    # Add update notification if needed
    if version_info.needs_update and version_info.latest_version:
        content["update_notice"] = (
            f"[{primary_color}]⚠ Update available: {version_info.latest_version}[/]\n"
            "Run 'uv tool upgrade openhands' to update"
        )

    # Add critic notification if enabled
    if has_critic:
        content["critic_notice"] = (
            f"\n[{primary_color}]Experimental Feature: "
            "Critic + Iterative Refinement Mode[/]\n"
            "[dim]Using OpenHands provider enables a free critic to predict task "
            "success. Enable Iterative Refinement in settings to auto-prompt the "
            "agent when work appears incomplete. "
            "Anonymized data collected. Disable in settings.[/dim]"
        )

    return content
