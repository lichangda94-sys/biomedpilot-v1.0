from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.shared.local_engines.engine_status import EngineStatus
from app.shared.local_engines.ollama_llm_engine import (
    CommandFinder,
    Runner,
    UrlOpen,
    detect_ollama_llm_engine,
)
from app.shared.local_engines.ollama_llm_manifest import (
    OllamaLLMRuntimeManifest,
    write_ollama_llm_runtime_manifest,
)
from app.shared.local_engines.ollama_llm_registry import OLLAMA_LLM_HTTP_ENDPOINT


@dataclass(frozen=True)
class OllamaLLMPreflightResult:
    status: EngineStatus
    manifest: OllamaLLMRuntimeManifest
    manifest_path: str = ""

    @property
    def service_available(self) -> bool:
        return self.manifest.service_available

    @property
    def missing_models(self) -> tuple[str, ...]:
        return self.manifest.missing_models


def run_ollama_llm_preflight(
    *,
    endpoint: str = OLLAMA_LLM_HTTP_ENDPOINT,
    manifest_path: str | Path | None = None,
    write_manifest: bool = True,
    run_smoke: bool = True,
    command_finder: CommandFinder | None = None,
    preferred_paths: tuple[str, ...] | None = None,
    runner: Runner | None = None,
    urlopen_func: UrlOpen | None = None,
    timeout_seconds: int = 5,
) -> OllamaLLMPreflightResult:
    kwargs = {}
    if command_finder is not None:
        kwargs["command_finder"] = command_finder
    if preferred_paths is not None:
        kwargs["preferred_paths"] = preferred_paths
    if runner is not None:
        kwargs["runner"] = runner
    if urlopen_func is not None:
        kwargs["urlopen_func"] = urlopen_func
    status, manifest = detect_ollama_llm_engine(
        endpoint=endpoint,
        timeout_seconds=timeout_seconds,
        run_smoke=run_smoke,
        **kwargs,
    )
    resolved_manifest_path = ""
    if write_manifest:
        resolved_manifest_path = str(write_ollama_llm_runtime_manifest(manifest, manifest_path))
    return OllamaLLMPreflightResult(status=status, manifest=manifest, manifest_path=resolved_manifest_path)

