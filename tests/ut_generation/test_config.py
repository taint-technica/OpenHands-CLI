"""Unit tests for openhands_cli.ut_generation.config module."""

from openhands_cli.ut_generation.config import (
    DEFAULT_JAVA_HOME,
    LANGUAGE_MAP,
    OUTPUT_SCRIPT_NAME,
)


class TestOutputScriptName:
    def test_value(self):
        assert OUTPUT_SCRIPT_NAME == "Gen_UnitTest.sh"

    def test_is_string(self):
        assert isinstance(OUTPUT_SCRIPT_NAME, str)

    def test_has_sh_extension(self):
        assert OUTPUT_SCRIPT_NAME.endswith(".sh")


class TestDefaultJavaHome:
    def test_value(self):
        assert DEFAULT_JAVA_HOME == "/usr/lib/jvm/java-21-openjdk-amd64"

    def test_is_string(self):
        assert isinstance(DEFAULT_JAVA_HOME, str)

    def test_is_absolute_path(self):
        assert DEFAULT_JAVA_HOME.startswith("/")


class TestLanguageMap:
    def test_python_extension(self):
        assert LANGUAGE_MAP[".py"] == "python"

    def test_java_extension(self):
        assert LANGUAGE_MAP[".java"] == "java"

    def test_contains_two_entries(self):
        assert len(LANGUAGE_MAP) == 2

    def test_unsupported_extension_not_in_map(self):
        assert ".js" not in LANGUAGE_MAP
        assert ".ts" not in LANGUAGE_MAP
        assert ".go" not in LANGUAGE_MAP
        assert ".rs" not in LANGUAGE_MAP

    def test_is_dict(self):
        assert isinstance(LANGUAGE_MAP, dict)
