from __future__ import annotations

import csv
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.plots.models import PlotArtifact
from app.bioinformatics.plots.schema import validate_plot_artifact
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry, save_registry


ENRICHMENT_PLOT_GATE_SCHEMA_VERSION = "biomedpilot.enrichment_plot_gate.v1"
ENRICHMENT_REPORT_READY_GATE_SCHEMA_VERSION = "biomedpilot.enrichment_section_report_ready_gate.v1"
ENRICHMENT_REPORT_PACKAGE_SCHEMA_VERSION = "biomedpilot.enrichment_section_report_package.v1"
ENRICHMENT_TASK_TYPES = {"ora", "gsea_preranked"}
ENRICHMENT_PLOT_TYPES = {"ora_barplot", "ora_dotplot", "gsea_preranked_plot"}


def build_enrichment_plot_gate(project_root: str | Path, *, result_id: str | None = None, plot_type: str = "ora_dotplot") -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    entries = _entries(root)
    selected = _select_enrichment_result(entries, result_id)
    blockers: list[str] = []
    warnings: list[str] = []
    if plot_type not in ENRICHMENT_PLOT_TYPES:
        blockers.append(f"unsupported_enrichment_plot_type:{plot_type}")
    if selected is None:
        blockers.append("formal_enrichment_result_not_found")
    else:
        blockers.extend(_source_blockers(root, selected))
        task_type = str(selected.get("task_type") or "")
        if task_type == "ora" and plot_type == "gsea_preranked_plot":
            blockers.append("ora_result_cannot_use_gsea_plot")
        if task_type == "gsea_preranked" and plot_type in {"ora_barplot", "ora_dotplot"}:
            blockers.append("gsea_result_cannot_use_ora_plot")
    return {
        "schema_version": ENRICHMENT_PLOT_GATE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "selected_result_id": str((selected or {}).get("result_id") or result_id or ""),
        "plot_type": plot_type,
        "allowed_plot_types": sorted(ENRICHMENT_PLOT_TYPES),
        "source_result_semantics": normalize_result_semantics((selected or {}).get("canonical_result_semantics") or (selected or {}).get("result_semantics"), default=""),
        "guard_copy": _guard_copy(),
        "report_ready_eligible_changed": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def create_enrichment_plot_artifact(project_root: str | Path, *, result_id: str | None = None, plot_type: str = "ora_dotplot") -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gate = build_enrichment_plot_gate(root, result_id=result_id, plot_type=plot_type)
    if gate.get("status") != "passed":
        return {"schema_version": ENRICHMENT_PLOT_GATE_SCHEMA_VERSION, "status": "blocked", "plot_artifact": {}, "blockers": gate.get("blockers", []), "warnings": gate.get("warnings", [])}
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    source = next(entry for entry in entries if str(entry.get("result_id") or "") == str(gate["selected_result_id"]))
    table_path = _table_path(root, source)
    rows = _read_plot_rows(table_path, str(source.get("task_type") or ""))
    svg_path = _write_svg(root, source, plot_type, rows)
    source_semantics = normalize_result_semantics(source.get("canonical_result_semantics") or source.get("result_semantics"), default="")
    artifact = PlotArtifact(
        plot_id=f"{source.get('result_id')}-{plot_type}",
        plot_type=plot_type,
        source_result_id=str(source.get("result_id") or ""),
        source_result_semantics=source_semantics,
        source_task_type=str(source.get("task_type") or ""),
        plot_semantics=source_semantics,
        plot_artifact_scope="formal_enrichment_plot",
        input_package_id=str(source.get("input_package_id") or ""),
        task_run_id=str(source.get("task_run_id") or ""),
        parameters_manifest={"source_parameters_manifest": source.get("parameters_manifest", {}), "plot_policy": "formal_enrichment_section_plot_only"},
        plot_parameters={"top_n": 10},
        plot_spec_artifact={"schema_version": "biomedpilot.enrichment_plot_spec.v1", "plot_type": plot_type, "row_count": len(rows)},
        image_artifacts=({"artifact_type": "svg", "path": str(svg_path.relative_to(root)), "mime_type": "image/svg+xml"},),
        table_artifacts=({"artifact_type": "source_enrichment_table", "path": str(table_path.relative_to(root) if table_path.is_relative_to(root) else table_path)},),
        engine_name="biomedpilot_enrichment_svg_renderer",
        engine_version="0.1.0",
        dependency_snapshot={"renderer": "stdlib_svg", "status": "passed"},
        warnings=(),
        blockers=(),
    ).to_dict()
    validation = validate_plot_artifact(artifact)
    artifact["warnings"] = validation.get("warnings", [])
    artifact["blockers"] = validation.get("blockers", [])
    if artifact["blockers"]:
        return {"schema_version": ENRICHMENT_PLOT_GATE_SCHEMA_VERSION, "status": "blocked", "plot_artifact": artifact, "blockers": artifact["blockers"], "warnings": artifact["warnings"]}
    existing = [item for item in source.get("plot_artifacts", []) or [] if isinstance(item, dict) and item.get("plot_id") != artifact["plot_id"]]
    source["plot_artifacts"] = [*existing, artifact]
    source["report_ready_eligible"] = False
    source["updated_at"] = _now()
    save_registry(root, entries)
    return {
        "schema_version": ENRICHMENT_PLOT_GATE_SCHEMA_VERSION,
        "status": "passed",
        "result_id": str(source.get("result_id") or ""),
        "plot_artifact": artifact,
        "plot_artifacts": source["plot_artifacts"],
        "report_ready_eligible": False,
        "blockers": [],
        "warnings": artifact["warnings"],
    }


def evaluate_enrichment_section_report_ready_gate(project_root: str | Path, *, result_id: str | None = None, allow_table_only_report: bool = False) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    selected = _select_enrichment_result(_entries(root), result_id)
    blockers: list[str] = []
    warnings: list[str] = []
    checks = {
        "formal_enrichment_result_present": selected is not None,
        "result_index_v2_complete": False,
        "dependency_snapshot_passed": False,
        "result_table_present": False,
        "plot_artifact_or_table_only_mode": False,
        "section_only_no_full_integrated_report": True,
        "no_clinical_interpretation": True,
    }
    if selected is None:
        blockers.append("formal_enrichment_result_not_found")
    else:
        source_blockers = _source_blockers(root, selected)
        blockers.extend(source_blockers)
        checks["result_index_v2_complete"] = not source_blockers
        dependency = selected.get("dependency_snapshot") if isinstance(selected.get("dependency_snapshot"), dict) else {}
        checks["dependency_snapshot_passed"] = dependency.get("status") == "passed"
        if not checks["dependency_snapshot_passed"]:
            blockers.append("enrichment_dependency_snapshot_not_passed")
        table_path = _table_path(root, selected)
        checks["result_table_present"] = table_path.is_file()
        if not checks["result_table_present"]:
            blockers.append("enrichment_result_table_missing")
        plot_artifacts = [item for item in selected.get("plot_artifacts", []) or [] if isinstance(item, dict) and item.get("plot_artifact_scope") == "formal_enrichment_plot"]
        checks["plot_artifact_or_table_only_mode"] = bool(plot_artifacts) or allow_table_only_report
        if allow_table_only_report and not plot_artifacts:
            warnings.append("enrichment_table_only_report_mode_no_plot_artifact")
        if not checks["plot_artifact_or_table_only_mode"]:
            blockers.append("enrichment_report_ready_requires_plot_artifact_or_table_only_mode")
    return {
        "schema_version": ENRICHMENT_REPORT_READY_GATE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "eligible_for_enrichment_section_report_ready" if not blockers else "blocked",
        "selected_result_id": str((selected or {}).get("result_id") or result_id or ""),
        "checks": checks,
        "allow_table_only_report": allow_table_only_report,
        "section_scope": "formal_enrichment_only",
        "full_integrated_report_enabled": False,
        "clinical_interpretation_enabled": False,
        "guard_copy": _guard_copy(),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def create_enrichment_section_report_package(project_root: str | Path, *, result_id: str | None = None, allow_table_only_report: bool = False) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gate = evaluate_enrichment_section_report_ready_gate(root, result_id=result_id, allow_table_only_report=allow_table_only_report)
    if gate.get("status") != "eligible_for_enrichment_section_report_ready":
        return {"schema_version": ENRICHMENT_REPORT_PACKAGE_SCHEMA_VERSION, "status": "blocked", "package_path": "", "gate": gate, "blockers": gate.get("blockers", []), "warnings": gate.get("warnings", [])}
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    selected = next(entry for entry in entries if str(entry.get("result_id") or "") == str(gate["selected_result_id"]))
    package_dir = _next_package_dir(root, str(selected.get("result_id") or "enrichment"))
    tables_dir = package_dir / "tables"
    plots_dir = package_dir / "plots"
    manifests_dir = package_dir / "manifests"
    logs_dir = package_dir / "logs"
    for directory in (tables_dir, plots_dir, manifests_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)
    table_path = _table_path(root, selected)
    if table_path.is_file():
        shutil.copy2(table_path, tables_dir / table_path.name)
    _copy_plot_artifacts(root, selected.get("plot_artifacts", []) or [], plots_dir)
    _copy_logs(root, selected.get("log_artifacts", []) or [], logs_dir)
    _write_json(manifests_dir / "result_index_snapshot.json", registry)
    _write_json(manifests_dir / "enrichment_result_entry.json", selected)
    _write_json(manifests_dir / "parameters_manifest.json", selected.get("parameters_manifest", {}))
    _write_json(manifests_dir / "dependency_snapshot.json", selected.get("dependency_snapshot", {}))
    _write_json(manifests_dir / "plot_artifacts.json", selected.get("plot_artifacts", []) or [])
    _write_json(manifests_dir / "gate_snapshot.json", gate)
    (package_dir / "README_limitations.md").write_text(_limitations_markdown(), encoding="utf-8")
    (package_dir / "enrichment_section_report.md").write_text(_section_markdown(selected, gate), encoding="utf-8")
    manifest = {
        "schema_version": ENRICHMENT_REPORT_PACKAGE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "enrichment_section_report_package_created",
        "package_path": str(package_dir),
        "section_scope": "formal_enrichment_only",
        "included_result_ids": [str(selected.get("result_id") or "")],
        "full_integrated_report_enabled": False,
        "clinical_interpretation_enabled": False,
        "allow_table_only_report": allow_table_only_report,
        "gate": gate,
    }
    _write_json(package_dir / "enrichment_section_report_package_manifest.json", manifest)
    selected["report_ready_eligible"] = True
    selected["report_artifacts"] = [
        *[item for item in selected.get("report_artifacts", []) or [] if isinstance(item, dict) and item.get("artifact_type") != "enrichment_section_report_package"],
        {"artifact_type": "enrichment_section_report_package", "path": str((package_dir / "enrichment_section_report_package_manifest.json").relative_to(root)), "schema": ENRICHMENT_REPORT_PACKAGE_SCHEMA_VERSION, "section_scope": "formal_enrichment_only"},
    ]
    selected["updated_at"] = _now()
    save_registry(root, entries)
    return manifest


def _entries(root: Path) -> list[dict[str, Any]]:
    return [entry for entry in load_registry(root).get("results", []) if isinstance(entry, dict)]


def _select_enrichment_result(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    candidates = [entry for entry in entries if _is_formal_enrichment(entry)]
    return candidates[-1] if candidates else None


def _is_formal_enrichment(entry: dict[str, Any]) -> bool:
    return normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="") == "formal_computed_result" and str(entry.get("task_type") or "") in ENRICHMENT_TASK_TYPES


def _source_blockers(root: Path, entry: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not _is_formal_enrichment(entry):
        blockers.append("enrichment_plot_requires_formal_computed_enrichment_result")
    for field_name in ("input_package_id", "parameters_manifest", "engine_name", "engine_version", "dependency_snapshot"):
        if not entry.get(field_name):
            blockers.append(f"enrichment_result_missing:{field_name}")
    if entry.get("validation_status") not in {"passed", "warning"}:
        blockers.append("enrichment_result_validation_not_passed")
    if entry.get("blockers"):
        blockers.append("enrichment_result_has_blockers")
    if not _table_path(root, entry).is_file():
        blockers.append("enrichment_result_table_missing")
    return blockers


def _table_path(root: Path, entry: dict[str, Any]) -> Path:
    expected = {"ora_result_table", "gsea_preranked_result_table"}
    for artifact in entry.get("output_artifacts", []) or []:
        if isinstance(artifact, dict) and artifact.get("artifact_type") in expected:
            path = Path(str(artifact.get("path") or ""))
            return path if path.is_absolute() else root / path
    return root / "missing_enrichment_result_table.tsv"


def _read_plot_rows(path: Path, task_type: str) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if task_type == "gsea_preranked":
        rows.sort(key=lambda row: abs(_float(row.get("NES")) or 0.0), reverse=True)
    else:
        rows.sort(key=lambda row: _float(row.get("p.adjust")) if _float(row.get("p.adjust")) is not None else 1.0)
    return rows[:10]


def _write_svg(root: Path, source: dict[str, Any], plot_type: str, rows: list[dict[str, Any]]) -> Path:
    result_id = str(source.get("result_id") or "enrichment")
    path = root / "results" / "plots" / f"{_safe_name(result_id)}_{plot_type}.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    width = 760
    row_height = 34
    height = max(160, 80 + row_height * max(1, len(rows)))
    labels = [_label(row, str(source.get("task_type") or "")) for row in rows]
    values = [_plot_value(row, str(source.get("task_type") or "")) for row in rows]
    max_value = max([abs(value) for value in values] or [1.0]) or 1.0
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="#ffffff"/>', f'<text x="24" y="34" font-family="Arial" font-size="18" font-weight="700">{_escape(plot_type)}: {_escape(result_id)}</text>']
    for index, (label, value) in enumerate(zip(labels, values, strict=False)):
        y = 70 + index * row_height
        bar_width = int(420 * abs(value) / max_value)
        color = "#2d6cdf" if value >= 0 else "#b44545"
        lines.append(f'<text x="24" y="{y + 17}" font-family="Arial" font-size="12">{_escape(label[:42])}</text>')
        lines.append(f'<rect x="300" y="{y}" width="{bar_width}" height="20" fill="{color}" rx="2"/>')
        lines.append(f'<text x="{310 + bar_width}" y="{y + 15}" font-family="Arial" font-size="12">{value:.3g}</text>')
    lines.append('<text x="24" y="' + str(height - 18) + '" font-family="Arial" font-size="11" fill="#555">Statistical research visualization only. No clinical conclusion.</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _copy_plot_artifacts(root: Path, artifacts: list[object], plots_dir: Path) -> None:
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        _write_json(plots_dir / f"{_safe_name(str(artifact.get('plot_id') or 'plot'))}.plot_artifact.json", artifact)
        for image in artifact.get("image_artifacts", []) or []:
            if not isinstance(image, dict):
                continue
            path = Path(str(image.get("path") or ""))
            source = path if path.is_absolute() else root / path
            if source.is_file():
                shutil.copy2(source, plots_dir / source.name)


def _copy_logs(root: Path, artifacts: list[object], logs_dir: Path) -> None:
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        path = Path(str(artifact.get("path") or ""))
        source = path if path.is_absolute() else root / path
        if source.is_file():
            shutil.copy2(source, logs_dir / source.name)


def _next_package_dir(root: Path, result_id: str) -> Path:
    base = root / "report_package" / "enrichment" / _safe_name(result_id)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = base / timestamp
    suffix = 1
    while candidate.exists():
        suffix += 1
        candidate = base / f"{timestamp}_{suffix}"
    return candidate


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _section_markdown(entry: dict[str, Any], gate: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Enrichment Section Report",
            "",
            f"Result id: {entry.get('result_id')}",
            f"Analysis type: {entry.get('task_type')}",
            f"Engine: {entry.get('engine_name')} {entry.get('engine_version')}",
            "",
            "This package contains a formal enrichment section only. It is not a full integrated report.",
            "Statistical research result only. No clinical conclusion, prognosis, diagnosis, or treatment recommendation is provided.",
            "",
            f"Gate status: {gate.get('status')}",
        ]
    )


def _limitations_markdown() -> str:
    return "\n".join(
        [
            "# Limitations",
            "",
            "- Enrichment output is a statistical research result only.",
            "- No clinical conclusion, prognosis, diagnosis, or treatment recommendation is included.",
            "- This is an enrichment section package, not a full integrated report.",
            "- ReactomePA/msigdbr-dependent outputs are included only after their own gates pass.",
        ]
    )


def _guard_copy() -> str:
    return "Formal enrichment plot/report artifacts visualize statistical research results only; they are not clinical conclusions or treatment recommendations."


def _label(row: dict[str, Any], task_type: str) -> str:
    return str(row.get("Description") or row.get("ID") or row.get("pathway") or task_type)


def _plot_value(row: dict[str, Any], task_type: str) -> float:
    if task_type == "gsea_preranked":
        return _float(row.get("NES")) or 0.0
    adjusted = _float(row.get("p.adjust")) or 1.0
    return max(0.0, -1.0 * math.log10(max(adjusted, 1e-300)))


def _float(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value) or "enrichment"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
