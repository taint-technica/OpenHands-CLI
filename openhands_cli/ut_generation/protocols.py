from typing import Dict, Protocol, Tuple


class LanguageHandler(Protocol):

    def get_template_and_placeholders(
        self,
        source_file_path: str,
        expected_coverage: int,
        max_iteration: int,
        api_key: str,
        llm_base_url: str,
        model: str,
        trace_source: str,
        trace_flow: str,
        project_name: str,
    ) -> Tuple[str, Dict[str, str]]: ...
