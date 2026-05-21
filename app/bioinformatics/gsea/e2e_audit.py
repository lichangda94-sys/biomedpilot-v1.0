from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from app.bioinformatics.results.registry import load_registry

from .gene_set_gate import build_gsea_gene_set_resource_gate
from .input_gate import build_gsea_preranked_input_gate
from .parameter_gate import build_gsea_parameter_manifest
from .review import build_gsea_result_review


GSEA_E2E_AUDIT_SCHEMA_VERSION = "biomedpilot.gsea_e2e_acceptance_audit.v1"


def audit_gsea_e2e_acceptance(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    allow_table_only_report: bool = False,
) -> dict[str, Any]:
    from app.bioinformatics.plots.gsea import build_gsea_plot_gate
    from app.bioinformatics.reports.gsea import evaluate_gsea_report_ready_gate

    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    selected = _select_gsea(entries, result_id)
    blockers: list[str] = []
    warnings: list[str] = []
    traceability: dict[str, Any] = {}
    consistency: dict[str, bool] = {}
    if selected is None:
        blockers.append("gsea_e2e_result_missing")
    else:
        source_id = str(selected.get("source_deg_result_id") or "")
        traceability = {
            "source_deg_result_id": source_id,
            "gsea_result_id": str(selected.get("result_id") or ""),
            "gene_set_resource_id": str(selected.get("gene_set_resource_id") or ""),
            "rank_metric": str((selected.get("parameters_manifest") or {}).get("rank_metric", "") if isinstance(selected.get("parameters_manifest"), dict) else ""),
            "parameter_manifest_id": str((selected.get("parameters_manifest") or {}).get("gsea_parameter_id", "") if isinstance(selected.get("parameters_manifest"), dict) else ""),
            "dependency_snapshot_present": bool(selected.get("dependency_snapshot")),
            "task_run_log": selected.get("log_artifacts", []),
            "package_artifacts": selected.get("report_artifacts", []),
        }
        parameters = selected.get("parameters_manifest") if isinstance(selected.get("parameters_manifest"), dict) else {}
        min_gene_set_size = int(parameters.get("min_gene_set_size") or 1)
        max_gene_set_size = int(parameters.get("max_gene_set_size") or 500)
        input_gate = build_gsea_preranked_input_gate(root, result_id=source_id or None, minimum_ranked_gene_count=int(parameters.get("minimum_ranked_gene_count") or 1))
        gene_set_gate = build_gsea_gene_set_resource_gate(root, gsea_input=input_gate, resource_id=str(selected.get("gene_set_resource_id") or ""), min_gene_set_size=min_gene_set_size, max_gene_set_size=max_gene_set_size)
        parameter_gate = build_gsea_parameter_manifest(input_gate, gene_set_gate, min_gene_set_size=min_gene_set_size, max_gene_set_size=max_gene_set_size)
        review = build_gsea_result_review(root, result_id=str(selected.get("result_id") or ""))
        plot_gate = build_gsea_plot_gate(root, result_id=str(selected.get("result_id") or ""))
        report_gate = evaluate_gsea_report_ready_gate(root, result_id=str(selected.get("result_id") or ""), allow_table_only_report=allow_table_only_report)
        for name, gate in (("input", input_gate), ("gene_set", gene_set_gate), ("parameter", parameter_gate), ("review", review), ("plot", plot_gate), ("report", report_gate)):
            if gate.get("status") in {"blocked", "failed"}:
                blockers.extend(f"{name}:{item}" for item in gate.get("blockers", []) or [f"{name}_gate_blocked"])
            warnings.extend(f"{name}:{item}" for item in gate.get("warnings", []) or [])
        source_table = _gsea_table_path(root, selected)
        review_rows = review.get("rows", []) if isinstance(review.get("rows"), list) else []
        consistency["review_table_matches_source_table"] = len(_read_rows(source_table)) == len(review_rows)
        consistency["plot_artifact_in_result_index"] = bool(selected.get("plot_artifacts")) or allow_table_only_report
        consistency["gate_snapshot_records_blockers_warnings_provenance"] = all(key in report_gate for key in ("blockers", "warnings", "provenance_required"))
        package = _latest_package(root, selected)
        if package:
            packaged_table = package / "tables" / "gsea_result_table.tsv"
            consistency["packaged_gsea_table_matches_result_table"] = packaged_table.is_file() and source_table.is_file() and packaged_table.read_text(encoding="utf-8") == source_table.read_text(encoding="utf-8")
            consistency["package_independently_reviewable"] = all((package / path).is_file() for path in ("gsea_report.md", "README_limitations.md", "manifests/gate_snapshot.json", "logs/task_run_log.json"))
            traceability["latest_package_path"] = str(package)
        else:
            consistency["packaged_gsea_table_matches_result_table"] = False
            consistency["package_independently_reviewable"] = False
            blockers.append("gsea_e2e_report_package_missing")
        for check_name, passed in consistency.items():
            if not passed:
                blockers.append(check_name)
    return {
        "schema_version": GSEA_E2E_AUDIT_SCHEMA_VERSION,
        "status": "passed" if not blockers else "blocked",
        "traceability": traceability,
        "consistency": consistency,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _select_gsea(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    candidates = [entry for entry in entries if str(entry.get("task_type") or "") == "gsea_preranked"]
    return candidates[-1] if candidates else None


def _gsea_table_path(root: Path, entry: dict[str, Any]) -> Path:
    artifacts = entry.get("output_artifacts") if isinstance(entry.get("output_artifacts"), list) else []
    artifact = next((item for item in artifacts if isinstance(item, dict) and item.get("artifact_type") == "gsea_result_table"), {})
    path = Path(str(artifact.get("path") or ""))
    return path if path.is_absolute() else root / path


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        first = handle.readline()
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        return list(csv.DictReader([first, *handle.readlines()], delimiter=delimiter))


def _latest_package(root: Path, entry: dict[str, Any]) -> Path | None:
    artifacts = entry.get("report_artifacts") if isinstance(entry.get("report_artifacts"), list) else []
    paths: list[Path] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        path = Path(str(artifact.get("path") or ""))
        path = path if path.is_absolute() else root / path
        if path.name == "gsea_report_package_manifest.json":
            paths.append(path.parent)
    if not paths:
        base = root / "report_package" / "gsea" / str(entry.get("result_id") or "")
        paths = [path for path in base.glob("*") if path.is_dir()] if base.is_dir() else []
    return sorted(paths)[-1] if paths else None
