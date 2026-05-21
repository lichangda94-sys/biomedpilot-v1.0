from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import load_registry, save_registry

from .basic_renderers import build_basic_plot_spec
from .models import PlotArtifact
from .schema import validate_plot_artifact


def create_plot_artifact(project_root: str | Path, source_result_id: str, plot_type: str, *, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = load_registry(project_root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    source = next((entry for entry in entries if str(entry.get("result_id") or "") == source_result_id), None)
    if source is None:
        return _blocked_artifact(source_result_id, plot_type, ["missing_source_result"])
    spec = build_basic_plot_spec(source, plot_type, parameters=parameters)
    artifact = PlotArtifact(
        plot_id=_plot_id(source_result_id, plot_type),
        plot_type=plot_type,
        source_result_id=source_result_id,
        source_result_semantics=str(source.get("result_semantics") or ""),
        plot_semantics=normalize_result_semantics(source.get("canonical_result_semantics") or source.get("result_semantics")),
        input_package_id=str(source.get("input_package_id") or ""),
        task_run_id=str(source.get("task_run_id") or ""),
        parameters_manifest=parameters or {},
        plot_spec_artifact=spec,
        warnings=tuple(spec.get("warnings", []) or []),
        blockers=tuple(spec.get("blockers", []) or []),
    ).to_dict()
    validation = validate_plot_artifact(artifact)
    artifact["warnings"] = list(dict.fromkeys([*artifact.get("warnings", []), *validation["warnings"]]))
    artifact["blockers"] = list(dict.fromkeys([*artifact.get("blockers", []), *validation["blockers"]]))
    if not artifact["blockers"]:
        existing_plots = list(source.get("plot_artifacts", []) or [])
        source["plot_artifacts"] = [*existing_plots, artifact]
        save_registry(project_root, entries)
    return artifact


def _blocked_artifact(source_result_id: str, plot_type: str, blockers: list[str]) -> dict[str, Any]:
    return PlotArtifact(
        plot_id=_plot_id(source_result_id or "missing", plot_type),
        plot_type=plot_type,
        source_result_id=source_result_id,
        source_result_semantics="blocked",
        blockers=tuple(blockers),
    ).to_dict()


def _plot_id(source_result_id: str, plot_type: str) -> str:
    return f"plot-{hashlib.sha1(f'{source_result_id}|{plot_type}'.encode('utf-8')).hexdigest()[:12]}"
