"""Settings tab component for the settings modal."""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Input, Label, Select, Static

from openhands_cli.tui.modals.settings.model_recommendations import (
    render_model_recommendations,
)


class SettingsTab(Container):
    """Settings tab component containing LiteLLM Proxy configuration."""

    def compose(self) -> ComposeResult:
        """Compose the settings tab content."""
        with VerticalScroll(id="settings_form"):
            with Container(id="form_content"):
                # LiteLLM Proxy Configuration Section
                with Container(classes="form_group"):
                    yield Label("LiteLLM Proxy URL:", classes="form_label")
                    yield Input(
                        placeholder="http://localhost:4000",
                        id="proxy_url_input",
                        classes="form_input",
                        value="http://localhost:4000",
                    )

                    # API Key Section
                with Container(classes="form_group"):
                    yield Label("API Key:", classes="form_label")
                    yield Input(
                        placeholder="Enter your API key",
                        password=True,
                        id="api_key_input",
                        classes="form_input",
                        disabled=True,  # Enabled after model selection
                    )

                # Model Discovery Section
                with Container(classes="form_group"):
                    yield Label("Model Selection:", classes="form_label")
                    yield Button(
                        "🔄 Fetch Available Models",
                        id="fetch_models_button",
                        classes="fetch_models_button",
                    )
                    yield Static(
                        "Click to fetch models from LiteLLM Proxy",
                        classes="form_help",
                        id="fetch_help_text",
                    )

                # Model Select (populated after fetch)
                with Container(classes="form_group"):
                    yield Label("LLM Model:", classes="form_label")
                    yield Select(
                        [("Fetch models first", "")],
                        id="model_select",
                        classes="form_select",
                        type_to_search=True,
                        disabled=True,  # Enabled after fetch
                    )

                # Advanced Settings Section
                with Container(classes="form_group"):
                    yield Label("Advanced Settings:", classes="form_label")

                    # Timeout
                    with Container(classes="form_group_inline"):
                        yield Label("Timeout (s):", classes="form_label_inline")
                        yield Input(
                            placeholder="300",
                            id="timeout_input",
                            classes="form_input_inline",
                            disabled=True,
                        )

                    # Max Tokens
                    with Container(classes="form_group_inline"):
                        yield Label("Max Tokens:", classes="form_label_inline")
                        yield Input(
                            placeholder="128000",
                            id="max_tokens_input",
                            classes="form_input_inline",
                            disabled=True,
                        )

                    # Max Size
                    with Container(classes="form_group_inline"):
                        yield Label("Condenser Max Size:", classes="form_label_inline")
                        yield Input(
                            placeholder="240",
                            id="max_size_input",
                            classes="form_input_inline",
                            disabled=True,
                        )

                # Memory Condensation
                with Container(classes="form_group"):
                    yield Label("Memory Condensation:", classes="form_label")
                    yield Select(
                        [("Enabled", True), ("Disabled", False)],
                        value=True,
                        id="memory_condensation_select",
                        classes="form_select",
                        disabled=True,  # Enabled after API key entered
                    )
                    yield Static(
                        "Memory condensation helps reduce token usage by "
                        "summarizing old conversation history.",
                        classes="form_help",
                    )

                # Model Recommendations Section
                with Container(classes="form_group"):
                    yield Static("Model Recommendations", classes="form_section_title")
                    yield Static(
                        "Based on OpenHands evaluations using the SWE-bench dataset. "
                        "These models have been verified to work well with OpenHands. "
                        "For more details, see: https://docs.openhands.dev/openhands/usage/llms/llms",
                        classes="form_help",
                    )

                    # Render model recommendations
                    yield from render_model_recommendations()

                # Help Section
                with Container(classes="form_group"):
                    yield Static("Configuration Help", classes="form_section_title")
                    yield Static(
                        "• Configure LiteLLM Proxy URL to connect to your "
                        "LiteLLM instance\n"
                        "• Click 'Fetch Available Models' to load models "
                        "from the proxy\n"
                        "• API Keys are stored securely and masked in the "
                        "interface\n"
                        "• Changes take effect immediately after saving",
                        classes="form_help",
                    )
