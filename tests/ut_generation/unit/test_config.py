from openhands_cli.ut_generation.config import DEFAULT_JAVA_HOME, LANGUAGE_MAP, OUTPUT_SCRIPT_NAME


class TestOutputScriptName:
    def test_value(self):
        assert OUTPUT_SCRIPT_NAME == "Gen_UnitTest.sh"

    def test_is_sh_file(self):
        assert OUTPUT_SCRIPT_NAME.endswith(".sh")


class TestLanguageMap:
    def test_python_extension(self):
        assert LANGUAGE_MAP[".py"] == "python"

    def test_java_extension(self):
        assert LANGUAGE_MAP[".java"] == "java"

    def test_only_two_entries(self):
        assert len(LANGUAGE_MAP) == 2

    def test_no_uppercase_extensions(self):
        for key in LANGUAGE_MAP:
            assert key == key.lower(), f"Extension {key!r} should be lowercase"


class TestDefaultJavaHome:
    def test_is_string(self):
        assert isinstance(DEFAULT_JAVA_HOME, str)

    def test_not_empty(self):
        assert DEFAULT_JAVA_HOME != ""

    def test_is_absolute_path(self):
        assert DEFAULT_JAVA_HOME.startswith("/")
