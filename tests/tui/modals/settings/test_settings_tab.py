"""Minimal, high-impact tests for SettingsTab component."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Input, Select, Static

from openhands_cli.tui.modals.settings import model_recommendations
from openhands_cli.tui.modals.settings.components.settings_tab import SettingsTab


class _TestApp(App):
    def compose(self) -> ComposeResult:
        yield SettingsTab()


class TestSettingsTab:
    @pytest.mark.asyncio
    async def test_smoke_mount_and_key_widgets_exist(self):
        """Smoke test: component mounts and key widgets are queryable by ID."""
        app = _TestApp()

        async with app.run_test():
            tab = app.query_one(SettingsTab)

            # Core containers
            assert tab.query_one("#settings_form") is not None
            assert tab.query_one("#form_content") is not None

            # Key widgets by ID + type
            tab.query_one("#model_select", Select)
            tab.query_one("#proxy_url_input", Input)
            tab.query_one("#api_key_input", Input)

            tab.query_one("#memory_condensation_select", Select)
            tab.query_one("#timeout_input", Input)
            tab.query_one("#max_tokens_input", Input)
            tab.query_one("#max_size_input", Input)
            # Ensure fetch_models_button exists as a widget; type assertion is
            # intentionally loose here because it can be rendered as Button
            # depending on Textual version/layout.
            tab.query_one("#fetch_models_button")

    @pytest.mark.asyncio
    async def test_initial_state_defaults_and_disabled_flags(self):
        """High-impact: defaults + enabled/disabled contract."""
        app = _TestApp()

        async with app.run_test():
            tab = app.query_one(SettingsTab)

            model = tab.query_one("#model_select", Select)
            proxy_url = tab.query_one("#proxy_url_input", Input)

            api_key = tab.query_one("#api_key_input", Input)
            memory = tab.query_one("#memory_condensation_select", Select)
            timeout_input = tab.query_one("#timeout_input", Input)
            max_tokens_input = tab.query_one("#max_tokens_input", Input)
            max_size_input = tab.query_one("#max_size_input", Input)

            # Proxy URL has a default value, but model selection is disabled
            # until models are fetched.
            assert proxy_url.value.startswith("http://") or proxy_url.value.startswith(
                "https://"
            )
            assert model.disabled is True

            # API key masked + disabled until models are fetched/fill flow
            assert api_key.disabled is True

            # Memory condensation defaults on + disabled until later steps
            assert memory.value is True
            assert memory.disabled is True

            assert timeout_input.disabled is True
            assert max_tokens_input.disabled is True
            assert max_size_input.disabled is True

    @pytest.mark.asyncio
    async def test_model_select_has_provider_first_placeholder(self):
        """High-impact: model select starts with placeholder option."""
        app = _TestApp()

        async with app.run_test():
            tab = app.query_one(SettingsTab)
            model = tab.query_one("#model_select", Select)

            # Avoid deep testing options; just assert the placeholder is present.
            # Select stores options internally; _options is the most direct way.
            options = list(model._options)  # noqa: SLF001 (private access)
            assert ("Fetch models first", "") in options

    @pytest.mark.asyncio
    async def test_api_key_input_is_masked(self):
        """High-impact: ensure API key field is a password input."""
        app = _TestApp()

        async with app.run_test():
            tab = app.query_one(SettingsTab)
            api_key = tab.query_one("#api_key_input", Input)
            assert api_key.password is True

    @pytest.mark.asyncio
    async def test_placeholders_are_set_for_inputs(self):
        """High-impact: placeholders guide correct user input."""
        app = _TestApp()

        async with app.run_test():
            tab = app.query_one(SettingsTab)

            proxy_url = tab.query_one("#proxy_url_input", Input)
            api_key = tab.query_one("#api_key_input", Input)
            assert "localhost:4000" in (proxy_url.placeholder or "")
            assert "Enter your API key" in (api_key.placeholder or "")

    @pytest.mark.asyncio
    async def test_model_recommendations_are_present(self):
        """Test that model recommendations section is present in settings tab."""
        app = _TestApp()

        async with app.run_test():
            tab = app.query_one(SettingsTab)
            # Find all Static widgets with model-related classes
            category_titles: list[Static] = [
                w for w in tab.query(".model_category_title") if isinstance(w, Static)
            ]
            model_names: list[Static] = [
                w for w in tab.query(".model_name") if isinstance(w, Static)
            ]
            # Check that category titles are present
            widget_texts = [str(w.content) for w in category_titles]
            assert any(
                model_recommendations.CLOUD_CATEGORY_TITLE in text
                for text in widget_texts
            )
            assert any(
                model_recommendations.LOCAL_CATEGORY_TITLE in text
                for text in widget_texts
            )
            # Check that recommended models have the indicator
            model_name_texts = [str(w.content) for w in model_names]
            all_models = (
                model_recommendations.CLOUD_MODELS + model_recommendations.LOCAL_MODELS
            )
            for model in all_models:
                model_display = model.format_display_name()
                # Find the widget text that contains this model
                matching_text = next(
                    (text for text in model_name_texts if model_display in text), None
                )
                assert matching_text is not None, f"Model {model.name} not found"

                if model.is_recommended:
                    assert (
                        model_recommendations.RECOMMENDED_INDICATOR in matching_text
                    ), f"Recommended model {model.name} missing indicator"
                else:
                    assert (
                        model_recommendations.RECOMMENDED_INDICATOR not in matching_text
                    ), f"Non-recommended model {model.name} has indicator"
