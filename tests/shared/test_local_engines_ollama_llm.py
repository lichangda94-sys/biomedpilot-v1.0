from __future__ import annotations

import json
import subprocess
from pathlib import Path
from urllib.error import URLError

from app.shared.ai_gateway import DEFAULT_LOCAL_OLLAMA_ROLE_MODEL_MAPPING, desktop_local_ollama_config, load_ai_gateway_config, save_ai_gateway_config
from app.shared.local_engines import (
    ENGINE_STATUS_AVAILABLE,
    ENGINE_STATUS_FAILED,
    ENGINE_STATUS_NOT_CONFIGURED,
    OLLAMA_LLM_ENGINE_FAMILY,
    OllamaInstalledModel,
    default_ollama_llm_runtime_manifest_path,
    detect_ollama_llm_engine,
    load_ollama_llm_runtime_manifest,
    ollama_model_role_registry,
    ollama_role_model_mapping,
    run_ollama_llm_preflight,
    run_ollama_llm_smoke_tests,
)


def test_model_role_registry_contains_required_default_roles() -> None:
    roles = {role.role_id: role for role in ollama_model_role_registry()}

    assert ollama_role_model_mapping() == {
        "general_3b": "qwen2.5:3b",
        "translator": "translategemma:latest",
        "medical": "medgemma:4b",
    }
    assert roles["general_3b"].provider == "ollama"
    assert roles["general_3b"].required is True
    assert "bio_generate_dataset_query_draft" in roles["general_3b"].allowed_task_types
    assert "bio_translate_dataset_detail" in roles["translator"].allowed_task_types
    assert "local_only" in roles["medical"].privacy_note


def test_missing_ollama_command_returns_engine_missing() -> None:
    calls: list[object] = []

    status, manifest = detect_ollama_llm_engine(
        command_finder=lambda _name: None,
        preferred_paths=(),
        urlopen_func=_recording_urlopen(calls),
        runner=_version_runner,
        run_smoke=True,
    )

    assert status.status == ENGINE_STATUS_NOT_CONFIGURED
    assert manifest.ollama_command_path == ""
    assert manifest.service_available is False
    assert set(manifest.missing_models) == {"qwen2.5:3b", "translategemma:latest", "medgemma:4b"}
    assert {result.status for result in manifest.smoke_results} == {"skipped"}
    assert calls == []


def test_ollama_command_without_http_service_reports_unavailable() -> None:
    status, manifest = detect_ollama_llm_engine(
        command_finder=lambda _name: "/usr/local/bin/ollama",
        preferred_paths=(),
        runner=_version_runner,
        urlopen_func=_raising_urlopen(URLError("refused")),
        run_smoke=True,
    )

    assert status.status == ENGINE_STATUS_FAILED
    assert manifest.ollama_command_path == "/usr/local/bin/ollama"
    assert "ollama version is 0.21.0" in manifest.ollama_version
    assert manifest.service_available is False
    assert "qwen2.5:3b" in manifest.missing_models
    assert all(result.status == "skipped" for result in manifest.smoke_results)


def test_tags_response_identifies_all_model_roles_and_manifest_round_trip(tmp_path: Path) -> None:
    status, manifest = detect_ollama_llm_engine(
        command_finder=lambda _name: "/opt/homebrew/bin/ollama",
        preferred_paths=(),
        runner=_version_runner,
        urlopen_func=_urlopen_sequence([_FakeResponse(_tags_payload("qwen2.5:3b", "translategemma:latest", "medgemma:4b"))]),
        run_smoke=False,
    )
    result = run_ollama_llm_preflight(
        manifest_path=tmp_path / "ollama_llm_runtime_manifest.json",
        command_finder=lambda _name: "/opt/homebrew/bin/ollama",
        preferred_paths=(),
        runner=_version_runner,
        urlopen_func=_urlopen_sequence([_FakeResponse(_tags_payload("qwen2.5:3b", "translategemma:latest", "medgemma:4b"))]),
        run_smoke=False,
    )
    loaded = load_ollama_llm_runtime_manifest(result.manifest_path)

    assert status.status == ENGINE_STATUS_AVAILABLE
    assert manifest.service_available is True
    assert manifest.missing_models == ()
    assert {model.name for model in manifest.installed_models} == {"qwen2.5:3b", "translategemma:latest", "medgemma:4b"}
    assert result.manifest.engine_family == OLLAMA_LLM_ENGINE_FAMILY
    assert result.manifest_path == str(tmp_path / "ollama_llm_runtime_manifest.json")
    assert loaded.to_dict() == result.manifest.to_dict()


def test_missing_models_are_reported_explicitly() -> None:
    status, manifest = detect_ollama_llm_engine(
        command_finder=lambda _name: "/opt/homebrew/bin/ollama",
        preferred_paths=(),
        runner=_version_runner,
        urlopen_func=_urlopen_sequence([_FakeResponse(_tags_payload("qwen2.5:3b"))]),
        run_smoke=False,
    )

    assert status.status == ENGINE_STATUS_FAILED
    assert set(manifest.missing_models) == {"translategemma:latest", "medgemma:4b"}
    assert "缺失默认本地模型" in status.last_error


def test_smoke_tests_cover_pass_fail_and_skip() -> None:
    results = run_ollama_llm_smoke_tests(
        installed_models=(
            OllamaInstalledModel("qwen2.5:3b"),
            OllamaInstalledModel("translategemma:latest"),
        ),
        service_available=True,
        urlopen_func=_urlopen_sequence(
            [
                _FakeResponse({"response": "OK"}),
                _FakeResponse({"response": ""}),
            ]
        ),
    )

    by_role = {result.role_id: result for result in results}
    assert by_role["general_3b"].status == "passed"
    assert by_role["translator"].status == "failed"
    assert by_role["medical"].status == "skipped"
    assert "model not installed" in by_role["medical"].error_summary


def test_ai_gateway_config_default_disabled_and_enabled_role_mapping(tmp_path: Path) -> None:
    missing_config = load_ai_gateway_config(tmp_path / "missing_ai_gateway_config.json")
    enabled_config = desktop_local_ollama_config(
        enabled=True,
        base_url="http://localhost:11434",
        default_model="medgemma:4b",
    )
    saved_path = save_ai_gateway_config(enabled_config, tmp_path / "ai_gateway_config.json")
    reloaded = load_ai_gateway_config(saved_path)

    assert missing_config.default_provider == "disabled"
    assert missing_config.role_model_mapping == {}
    assert enabled_config.default_provider == "ollama"
    assert enabled_config.role_model_mapping == DEFAULT_LOCAL_OLLAMA_ROLE_MODEL_MAPPING
    assert reloaded.role_model_mapping["translator"] == "translategemma:latest"
    assert reloaded.allow_external_model is False
    assert reloaded.store_raw_prompts is False


def test_default_manifest_path_uses_project_storage() -> None:
    assert default_ollama_llm_runtime_manifest_path().as_posix().endswith("project_storage/local_engines/ollama_llm_runtime_manifest.json")


class _FakeResponse:
    def __init__(self, payload: object, *, status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def _tags_payload(*names: str) -> dict[str, object]:
    return {
        "models": [
            {
                "name": name,
                "model": name,
                "size": index + 100,
                "modified_at": f"2026-05-18T00:00:0{index}Z",
                "digest": f"digest-{index}",
                "details": {"family": "test"},
            }
            for index, name in enumerate(names)
        ]
    }


def _version_runner(command, **kwargs):
    return subprocess.CompletedProcess(command, 0, stdout="ollama version is 0.21.0\n", stderr="")


def _urlopen_sequence(responses: list[_FakeResponse]):
    remaining = list(responses)

    def _urlopen(request, timeout=None):
        if not remaining:
            raise AssertionError("unexpected urlopen call")
        return remaining.pop(0)

    return _urlopen


def _recording_urlopen(calls: list[object]):
    def _urlopen(request, timeout=None):
        calls.append({"url": getattr(request, "full_url", ""), "timeout": timeout})
        raise AssertionError("urlopen should not be called")

    return _urlopen


def _raising_urlopen(exc: Exception):
    def _urlopen(request, timeout=None):
        raise exc

    return _urlopen

