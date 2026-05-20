from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.registry import load_registry

from .models import REPORT_PACKAGE_SCHEMA_VERSION
from .readiness import evaluate_report_ready_gate


def create_report_export_package(
    project_root: str | Path,
    *,
    report_markdown: str,
    include_result_ids: list[str] | None = None,
    test_report_mode: bool = False,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gate = evaluate_report_ready_gate(root, include_result_ids=include_result_ids, test_report_mode=test_report_mode)
    if gate["status"] == "blocked":
        return {"schema_version": REPORT_PACKAGE_SCHEMA_VERSION, "status": "blocked", "gate": gate, "package_path": "", "blockers": gate["blockers"]}
    package_dir = root / "report_package"
    tables_dir = package_dir / "tables"
    plots_dir = package_dir / "plots"
    manifests_dir = package_dir / "manifests"
    logs_dir = package_dir / "logs"
    for directory in (tables_dir, plots_dir, manifests_dir / "input_package_manifests", manifests_dir / "parameters_manifests", logs_dir):
        directory.mkdir(parents=True, exist_ok=True)
    (package_dir / "report.md").write_text(report_markdown, encoding="utf-8")
    registry = load_registry(root)
    _write_json(manifests_dir / "result_index_snapshot.json", registry)
    _write_json(manifests_dir / "dependency_snapshot.json", _dependency_snapshot(registry))
    _write_json(manifests_dir / "validation_report.json", gate)
    _write_json(manifests_dir / "warnings.json", {"warnings": gate.get("warnings", [])})
    _write_parameters_manifests(manifests_dir / "parameters_manifests", registry)
    (package_dir / "README_limitations.md").write_text(
        "# Limitations\n\n"
        "- This package is for internal research review only.\n"
        "- This package does not provide clinical advice.\n"
        "- Testing, exploratory, and imported results remain labeled by source semantics.\n",
        encoding="utf-8",
    )
    _copy_registered_artifacts(root, registry, tables_dir=tables_dir, plots_dir=plots_dir, logs_dir=logs_dir)
    manifest = {
        "schema_version": REPORT_PACKAGE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "report_ready_package_created" if gate["status"] == "eligible_for_internal_report" else gate["status"],
        "package_path": str(package_dir),
        "gate": gate,
    }
    _write_json(package_dir / "report_package_manifest.json", manifest)
    return manifest


def _dependency_snapshot(registry: dict[str, Any]) -> dict[str, Any]:
    snapshots = {}
    for entry in registry.get("results", []) or []:
        if isinstance(entry, dict) and entry.get("dependency_snapshot"):
            snapshots[str(entry.get("result_id") or "")] = entry.get("dependency_snapshot")
    return snapshots


def _write_parameters_manifests(target: Path, registry: dict[str, Any]) -> None:
    for entry in registry.get("results", []) or []:
        if isinstance(entry, dict) and entry.get("parameters_manifest"):
            result_id = str(entry.get("result_id") or "result")
            _write_json(target / f"{result_id}.parameters.json", entry.get("parameters_manifest"))


def _copy_registered_artifacts(root: Path, registry: dict[str, Any], *, tables_dir: Path, plots_dir: Path, logs_dir: Path) -> None:
    for entry in registry.get("results", []) or []:
        if not isinstance(entry, dict):
            continue
        for artifact in entry.get("output_artifacts", []) or []:
            _copy_artifact(root, artifact, tables_dir)
        for artifact in entry.get("plot_artifacts", []) or []:
            _copy_artifact(root, artifact, plots_dir)
        for artifact in entry.get("log_artifacts", []) or []:
            _copy_artifact(root, artifact, logs_dir)


def _copy_artifact(root: Path, artifact: object, target_dir: Path) -> None:
    if not isinstance(artifact, dict):
        return
    path = Path(str(artifact.get("path") or artifact.get("file_path") or "")).expanduser()
    if not path.is_absolute():
        path = root / path
    if path.is_file():
        shutil.copy2(path, target_dir / path.name)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
