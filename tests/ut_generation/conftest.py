import pytest


@pytest.fixture
def common_params():
    return {
        "expected_coverage": 85,
        "max_iteration": 5,
        "api_key": "test-api-key",
        "llm_base_url": "https://api.test.com/v1",
        "model": "gpt-4o",
    }


@pytest.fixture
def maven_project(tmp_path, monkeypatch):
    (tmp_path / "pom.xml").write_text("<project/>")
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def gradle_project(tmp_path, monkeypatch):
    (tmp_path / "build.gradle").write_text("plugins { id 'java' }")
    (tmp_path / "gradlew").write_text("#!/bin/sh")
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def gradle_project_no_wrapper(tmp_path, monkeypatch):
    (tmp_path / "build.gradle").write_text("plugins { id 'java' }")
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def empty_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path
