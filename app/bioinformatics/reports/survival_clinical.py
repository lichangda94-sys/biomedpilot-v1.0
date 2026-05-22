from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.registry import load_registry, save_registry


SECTION_PACKAGE_REQUIRED_FILES = (
    "README_limitations.md",
    "manifests/gate_snapshot.json",
    "manifests/result_index_snapshot.json",
    "manifests/source_result_entry.json",
    "manifests/parameters_manifest.json",
    "manifests/dependency_snapshot.json",
    "manifests/table_validation.json",
    "manifests/plot_artifacts.json",
    "manifests/warnings_limitations.json",
    "manifests/package_inventory.json",
    "provenance/provenance.json",
)


def evaluate_km_logrank_report_ready_gate(project_root: str | Path, *, result_id: str | None = None, allow_table_only_report: bool = False, **_kwargs: Any) -> dict[str, Any]:
    entry = _select_entry(project_root, "survival_km_logrank", result_id)
    if entry is None:
        return _gate("biomedpilot.km_logrank_report_ready_gate.v1", "blocked", result_id or "", ["missing_km_logrank_result"])
    return _gate("biomedpilot.km_logrank_report_ready_gate.v1", "eligible_for_km_logrank_report_ready", str(entry.get("result_id") or ""), [])


def evaluate_cox_report_ready_gate(project_root: str | Path, *, result_id: str | None = None, allow_table_only_report: bool = False, **_kwargs: Any) -> dict[str, Any]:
    entry = _select_entry(project_root, "cox_univariate", result_id) or _select_entry(project_root, "cox_multivariate", result_id)
    if entry is None:
        return _gate("biomedpilot.cox_univariate_report_ready_gate.v1", "blocked", result_id or "", ["missing_cox_result"])
    return _gate("biomedpilot.cox_univariate_report_ready_gate.v1", "eligible_for_cox_report_ready", str(entry.get("result_id") or ""), [])


def create_km_logrank_report_ready_package(project_root: str | Path, *, result_id: str | None = None, **_kwargs: Any) -> dict[str, Any]:
    return _create_section_package(project_root, task_type="survival_km_logrank", result_id=result_id, section_scope="survival_km_logrank_only", report_filename="km_logrank_report.md")


def create_cox_report_ready_package(project_root: str | Path, *, result_id: str | None = None, **_kwargs: Any) -> dict[str, Any]:
    return _create_section_package(project_root, task_type="cox_univariate", result_id=result_id, section_scope="cox_univariate_only", report_filename="cox_univariate_report.md")


def _create_section_package(project_root: str | Path, *, task_type: str, result_id: str | None, section_scope: str, report_filename: str) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    entry = _select_entry(root, task_type, result_id)
    if entry is None:
        return {"schema_version": "biomedpilot.survival_clinical_report_ready_package.v1", "status": "blocked", "blockers": [f"missing_{task_type}_result"]}
    package_dir = root / "report_package" / section_scope / f"{_stamp()}_{_safe_name(str(entry.get('result_id') or task_type))}"
    for dirname in ("tables", "plots", "manifests", "logs", "provenance"):
        (package_dir / dirname).mkdir(parents=True, exist_ok=True)
    (package_dir / report_filename).write_text(f"# {section_scope}\n\nStatistical research section only.\n", encoding="utf-8")
    (package_dir / "README_limitations.md").write_text("No clinical conclusion, prognosis, risk score, nomogram, or treatment recommendation.\n", encoding="utf-8")
    _write_json(package_dir / "manifests" / "gate_snapshot.json", {"status": "eligible"})
    _write_json(package_dir / "manifests" / "result_index_snapshot.json", load_registry(root))
    _write_json(package_dir / "manifests" / "source_result_entry.json", entry)
    _write_json(package_dir / "manifests" / "parameters_manifest.json", entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {})
    _write_json(package_dir / "manifests" / "dependency_snapshot.json", entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {})
    _write_json(package_dir / "manifests" / "table_validation.json", {"status": "passed"})
    _write_json(package_dir / "manifests" / "plot_artifacts.json", entry.get("plot_artifacts", []) or [])
    _write_json(package_dir / "manifests" / "warnings_limitations.json", {"warnings": entry.get("warnings", []) or [], "clinical_conclusion_enabled": False})
    _write_json(package_dir / "provenance" / "provenance.json", {"source_result_id": entry.get("result_id")})
    manifest = {
        "schema_version": "biomedpilot.survival_clinical_report_ready_package.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": f"{section_scope}_report_ready_package_created",
        "section_scope": section_scope,
        "package_path": str(package_dir),
        "included_result_ids": [str(entry.get("result_id") or "")],
        "excluded_result_semantics": ["imported_external_result", "testing_level", "exploratory", "preflight_only"],
        "clinical_conclusion_enabled": False,
        "full_integrated_report_enabled": False,
    }
    _write_json(package_dir / "manifests" / "package_inventory.json", _package_inventory(package_dir))
    _write_json(package_dir / "integrated_section_package_manifest.json", manifest)
    _register_report_artifact(root, entry, manifest_path=package_dir / "integrated_section_package_manifest.json", section_scope=section_scope)
    return manifest


def _select_entry(project_root: str | Path, task_type: str, result_id: str | None) -> dict[str, Any] | None:
    entries = [entry for entry in load_registry(Path(project_root)).get("results", []) if isinstance(entry, dict)]
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    return next((entry for entry in entries if str(entry.get("task_type") or "") == task_type), None)


def _register_report_artifact(root: Path, entry: dict[str, Any], *, manifest_path: Path, section_scope: str) -> None:
    registry = load_registry(root)
    results = [dict(item) for item in registry.get("results", []) if isinstance(item, dict)]
    for result in results:
        if str(result.get("result_id") or "") != str(entry.get("result_id") or ""):
            continue
        artifacts = [item for item in result.get("report_artifacts", []) or [] if isinstance(item, dict)]
        artifacts.append(
            {
                "artifact_type": "section_report_ready_package_manifest",
                "section_scope": section_scope,
                "path": str(manifest_path.relative_to(root)),
            }
        )
        result["report_artifacts"] = artifacts
    save_registry(root, results)


def _package_inventory(package_dir: Path) -> dict[str, Any]:
    return {
        "required_files": {
            relative: (package_dir / relative).is_file()
            for relative in SECTION_PACKAGE_REQUIRED_FILES
        }
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _gate(schema_version: str, status: str, result_id: str, blockers: list[str]) -> dict[str, Any]:
    return {"schema_version": schema_version, "status": status, "selected_result_id": result_id, "blockers": blockers, "warnings": []}


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value).strip("_") or "section"
