from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.shared.local_engines.engine_status import (
    ENGINE_STATUS_AVAILABLE,
    ENGINE_STATUS_FAILED,
    ENGINE_STATUS_NOT_CONFIGURED,
    EngineStatus,
    UNKNOWN_VERSION,
    utc_now,
)
from app.shared.local_engines.ollama_llm_manifest import OllamaInstalledModel, OllamaLLMRuntimeManifest, OllamaSmokeResult
from app.shared.local_engines.ollama_llm_registry import (
    OLLAMA_LLM_ENGINE_FAMILY,
    OLLAMA_LLM_ENGINE_ID,
    OLLAMA_LLM_ENGINE_NAME,
    OLLAMA_LLM_ENGINE_TYPE,
    OLLAMA_LLM_HTTP_ENDPOINT,
    ollama_model_role_registry,
    ollama_model_role_registry_payload,
)


Runner = Callable[..., subprocess.CompletedProcess[str]]
UrlOpen = Callable[..., Any]
CommandFinder = Callable[[str], str | None]

DEFAULT_OLLAMA_COMMAND_PATHS = ("/opt/homebrew/bin/ollama",)
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 5
OLLAMA_LLM_INSTALL_GUIDE = (
    "Ollama 本地 LLM 外部引擎只检测本机命令、HTTP 服务和模型；BioMedPilot 不会静默安装 Ollama 或自动 pull 大模型。"
)


def default_ollama_llm_status(
    status: str = ENGINE_STATUS_NOT_CONFIGURED,
    *,
    configured_path: str = "",
    detected_version: str = UNKNOWN_VERSION,
    last_error: str = "",
    smoke_test_result: str = "",
) -> EngineStatus:
    return EngineStatus(
        engine_id=OLLAMA_LLM_ENGINE_ID,
        engine_name=OLLAMA_LLM_ENGINE_NAME,
        engine_type=OLLAMA_LLM_ENGINE_TYPE,
        configured_path_or_endpoint=configured_path,
        detected_version=detected_version,
        recommended_version="Ollama local service with qwen2.5:3b, translategemma:latest, medgemma:4b",
        status=status,
        last_check_at=utc_now(),
        last_error=last_error,
        smoke_test_result=smoke_test_result,
        install_guide_url_or_text=OLLAMA_LLM_INSTALL_GUIDE,
    )


def find_ollama_command(
    *,
    preferred_paths: tuple[str, ...] = DEFAULT_OLLAMA_COMMAND_PATHS,
    command_finder: CommandFinder = shutil.which,
) -> str:
    for candidate in preferred_paths:
        path = Path(candidate).expanduser()
        if path.is_file():
            return str(path)
    found = command_finder("ollama")
    return str(found or "")


def detect_ollama_version(
    command_path: str | Path,
    *,
    runner: Runner = subprocess.run,
    timeout_seconds: int = DEFAULT_OLLAMA_TIMEOUT_SECONDS,
) -> str:
    if not str(command_path).strip():
        return UNKNOWN_VERSION
    try:
        completed = runner(
            [str(command_path), "--version"],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (subprocess.TimeoutExpired, OSError):
        return UNKNOWN_VERSION
    text = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
    return text or UNKNOWN_VERSION


def fetch_ollama_installed_models(
    *,
    endpoint: str = OLLAMA_LLM_HTTP_ENDPOINT,
    urlopen_func: UrlOpen = urlopen,
    timeout_seconds: int = DEFAULT_OLLAMA_TIMEOUT_SECONDS,
) -> tuple[bool, tuple[OllamaInstalledModel, ...], str]:
    request = Request(_join_url(endpoint, "/api/tags"), method="GET")
    try:
        with urlopen_func(request, timeout=timeout_seconds) as response:
            status_code = int(getattr(response, "status", 200))
            if not 200 <= status_code < 300:
                return False, (), f"Ollama /api/tags returned HTTP {status_code}"
            body = response.read()
    except HTTPError as exc:
        return False, (), f"Ollama /api/tags returned HTTP {exc.code}"
    except (TimeoutError, URLError, OSError) as exc:
        return False, (), f"Ollama service unavailable: {exc.__class__.__name__}"
    except Exception as exc:
        return False, (), f"Ollama service detection failed: {exc.__class__.__name__}"
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        return False, (), "Ollama /api/tags returned invalid JSON"
    if not isinstance(payload, dict):
        return False, (), "Ollama /api/tags JSON was not an object"
    models_payload = payload.get("models")
    if not isinstance(models_payload, list):
        return True, (), ""
    models = tuple(_installed_model_from_tags(item) for item in models_payload if isinstance(item, dict))
    return True, tuple(model for model in models if model.name), ""


def detect_ollama_llm_engine(
    *,
    endpoint: str = OLLAMA_LLM_HTTP_ENDPOINT,
    command_finder: CommandFinder = shutil.which,
    preferred_paths: tuple[str, ...] = DEFAULT_OLLAMA_COMMAND_PATHS,
    runner: Runner = subprocess.run,
    urlopen_func: UrlOpen = urlopen,
    timeout_seconds: int = DEFAULT_OLLAMA_TIMEOUT_SECONDS,
    run_smoke: bool = False,
) -> tuple[EngineStatus, OllamaLLMRuntimeManifest]:
    detected_at = utc_now()
    command_path = find_ollama_command(preferred_paths=preferred_paths, command_finder=command_finder)
    version = detect_ollama_version(command_path, runner=runner, timeout_seconds=timeout_seconds) if command_path else UNKNOWN_VERSION
    service_available = False
    installed_models: tuple[OllamaInstalledModel, ...] = ()
    service_error = ""
    warnings: list[str] = []
    notes: list[str] = []

    if not command_path:
        warnings.append("未检测到 ollama 命令。请先安装 Ollama，再由用户触发模型准备。")
    else:
        service_available, installed_models, service_error = fetch_ollama_installed_models(
            endpoint=endpoint,
            urlopen_func=urlopen_func,
            timeout_seconds=timeout_seconds,
        )
        if service_error:
            warnings.append(service_error)

    installed_names = {model.name for model in installed_models}
    missing_models = tuple(role.default_model for role in ollama_model_role_registry() if role.default_model not in installed_names)
    if missing_models:
        warnings.append("缺失默认本地模型：" + ", ".join(missing_models))

    smoke_results: tuple[OllamaSmokeResult, ...] = ()
    if run_smoke:
        smoke_results = run_ollama_llm_smoke_tests(
            installed_models=installed_models,
            service_available=service_available,
            endpoint=endpoint,
            urlopen_func=urlopen_func,
            timeout_seconds=timeout_seconds,
        )
    else:
        smoke_results = tuple(
            OllamaSmokeResult(role.role_id, role.default_model, "skipped", error_summary="smoke test not requested")
            for role in ollama_model_role_registry()
        )

    if command_path and service_available and not missing_models:
        engine_status = ENGINE_STATUS_AVAILABLE
        notes.append("Ollama command, HTTP service, and default role models are available.")
    elif not command_path:
        engine_status = ENGINE_STATUS_NOT_CONFIGURED
    else:
        engine_status = ENGINE_STATUS_FAILED

    manifest = OllamaLLMRuntimeManifest(
        detected_at=detected_at,
        ollama_command_path=command_path,
        ollama_version=version,
        http_endpoint=endpoint,
        service_available=service_available,
        model_roles=tuple(ollama_model_role_registry_payload()),
        installed_models=installed_models,
        missing_models=missing_models,
        smoke_results=smoke_results,
        notes=tuple(notes),
        warnings=tuple(dict.fromkeys(warnings)),
    )
    smoke_summary = _smoke_summary(smoke_results)
    status = default_ollama_llm_status(
        engine_status,
        configured_path=endpoint,
        detected_version=version,
        last_error="; ".join(warnings),
        smoke_test_result=smoke_summary,
    )
    return status, manifest


def run_ollama_llm_smoke_tests(
    *,
    installed_models: tuple[OllamaInstalledModel, ...],
    service_available: bool,
    endpoint: str = OLLAMA_LLM_HTTP_ENDPOINT,
    urlopen_func: UrlOpen = urlopen,
    timeout_seconds: int = DEFAULT_OLLAMA_TIMEOUT_SECONDS,
) -> tuple[OllamaSmokeResult, ...]:
    installed_names = {model.name for model in installed_models}
    results: list[OllamaSmokeResult] = []
    for role in ollama_model_role_registry():
        if not service_available:
            results.append(OllamaSmokeResult(role.role_id, role.default_model, "skipped", error_summary="ollama service unavailable"))
            continue
        if role.default_model not in installed_names:
            results.append(OllamaSmokeResult(role.role_id, role.default_model, "skipped", error_summary="model not installed"))
            continue
        results.append(
            run_ollama_model_smoke_test(
                role_id=role.role_id,
                model_name=role.default_model,
                endpoint=endpoint,
                urlopen_func=urlopen_func,
                timeout_seconds=timeout_seconds,
            )
        )
    return tuple(results)


def run_ollama_model_smoke_test(
    *,
    role_id: str,
    model_name: str,
    endpoint: str = OLLAMA_LLM_HTTP_ENDPOINT,
    urlopen_func: UrlOpen = urlopen,
    timeout_seconds: int = DEFAULT_OLLAMA_TIMEOUT_SECONDS,
) -> OllamaSmokeResult:
    payload = {
        "model": model_name,
        "prompt": "Reply with OK only.",
        "stream": False,
        "options": {"temperature": 0},
    }
    request = Request(
        _join_url(endpoint, "/api/generate"),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen_func(request, timeout=timeout_seconds) as response:
            status_code = int(getattr(response, "status", 200))
            if not 200 <= status_code < 300:
                return OllamaSmokeResult(role_id, model_name, "failed", error_summary=f"Ollama smoke HTTP {status_code}")
            body = response.read()
    except HTTPError as exc:
        return OllamaSmokeResult(role_id, model_name, "failed", error_summary=f"Ollama smoke HTTP {exc.code}")
    except (TimeoutError, URLError, OSError) as exc:
        return OllamaSmokeResult(role_id, model_name, "failed", error_summary=f"Ollama smoke failed: {exc.__class__.__name__}")
    except Exception as exc:
        return OllamaSmokeResult(role_id, model_name, "failed", error_summary=f"Ollama smoke failed: {exc.__class__.__name__}")
    try:
        response_payload = json.loads(body.decode("utf-8"))
    except Exception:
        return OllamaSmokeResult(role_id, model_name, "failed", error_summary="Ollama smoke returned invalid JSON")
    if not isinstance(response_payload, dict):
        return OllamaSmokeResult(role_id, model_name, "failed", error_summary="Ollama smoke JSON was not an object")
    response_text = str(response_payload.get("response") or "").strip()
    if not response_text:
        return OllamaSmokeResult(role_id, model_name, "failed", error_summary="Ollama smoke returned empty response")
    return OllamaSmokeResult(role_id, model_name, "passed", response_summary=_safe_summary(response_text))


def _installed_model_from_tags(payload: dict[str, Any]) -> OllamaInstalledModel:
    name = str(payload.get("name") or payload.get("model") or "").strip()
    size_value = payload.get("size")
    details = payload.get("details") if isinstance(payload.get("details"), dict) else {}
    return OllamaInstalledModel(
        name=name,
        size=size_value if isinstance(size_value, int) and not isinstance(size_value, bool) else None,
        modified_at=str(payload.get("modified_at") or ""),
        digest=str(payload.get("digest") or ""),
        details={str(key): value for key, value in details.items()},
    )


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _safe_summary(text: str, limit: int = 120) -> str:
    return " ".join(text.split())[:limit]


def _smoke_summary(results: tuple[OllamaSmokeResult, ...]) -> str:
    if not results:
        return "not_run"
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))

