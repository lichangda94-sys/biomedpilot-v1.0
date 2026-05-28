from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.gsea.models import GSEA_TASK_TYPE, REQUIRED_GSEA_RESULT_TABLE_COLUMNS
from app.bioinformatics.gsea.result_schema import validate_gsea_result_index_entry, validate_gsea_result_table_row
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry

from .models import ORA_RESULT_TASK_TYPE, REQUIRED_ORA_TABLE_COLUMNS
from .result_schema import validate_ora_result_index_entry, validate_ora_result_table_row


ENRICHMENT_RESOURCE_LOCK_SCHEMA_VERSION = "biomedpilot.releasebuild.enrichment_resource_lock.v1"
ENRICHMENT_BACKGROUND_IDENTIFIER_SCHEMA_VERSION = "biomedpilot.releasebuild.enrichment_background_identifier_gate.v1"
ENRICHMENT_STATISTICAL_POLICY_SCHEMA_VERSION = "biomedpilot.releasebuild.enrichment_statistical_policy.v1"
ENRICHMENT_PRODUCTION_RESULT_SCHEMA_VERSION = "biomedpilot.releasebuild.enrichment_production_result_schema_gate.v1"
ENRICHMENT_PRODUCTION_AUDIT_PACKAGE_SCHEMA_VERSION = "biomedpilot.releasebuild.enrichment_production_audit_package.v1"
ENRICHMENT_PRODUCTION_PREVIEW_SCHEMA_VERSION = "biomedpilot.releasebuild.enrichment_production_preview.v1"

SUPPORTED_ANALYSIS_TYPES = {"ora_enrichment", "gsea_preranked"}
FDR_POLICIES = {"BH", "fdr_bh", "Benjamini-Hochberg"}


def build_enrichment_resource_lock(analysis_type: str, gene_set_gate: dict[str, Any]) -> dict[str, Any]:
    blockers = [str(item) for item in gene_set_gate.get("blockers", []) or []]
    warnings = [str(item) for item in gene_set_gate.get("warnings", []) or []]
    if analysis_type not in SUPPORTED_ANALYSIS_TYPES:
        blockers.append(f"unsupported_enrichment_analysis_type:{analysis_type or 'missing'}")
    resource_path = str(gene_set_gate.get("resource_path") or "")
    checksum = str(gene_set_gate.get("checksum") or "")
    file_size = _path_size(resource_path)
    if not gene_set_gate.get("gene_set_resource_id"):
        blockers.append("enrichment_resource_id_missing")
    if not resource_path:
        blockers.append("enrichment_resource_path_missing")
    if not checksum:
        blockers.append("enrichment_resource_checksum_missing")
    if file_size <= 0:
        blockers.append("enrichment_resource_file_size_missing")
    if not str(gene_set_gate.get("source") or "").strip():
        blockers.append("enrichment_resource_source_missing")
    if not str(gene_set_gate.get("license_warning") or "").strip():
        warnings.append("enrichment_resource_license_note_missing")
    return {
        "schema_version": ENRICHMENT_RESOURCE_LOCK_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "analysis_type": analysis_type,
        "resource_id": str(gene_set_gate.get("gene_set_resource_id") or ""),
        "resource_name": str(gene_set_gate.get("resource_name") or ""),
        "resource_path": resource_path,
        "resource_type": str(gene_set_gate.get("resource_type") or gene_set_gate.get("collection_name") or ""),
        "species": str(gene_set_gate.get("species") or "unknown"),
        "gene_id_type": str(gene_set_gate.get("gene_id_type") or "unknown"),
        "term_count": int(gene_set_gate.get("term_count") or 0),
        "checksum": checksum,
        "file_size": file_size,
        "source": str(gene_set_gate.get("source") or ""),
        "license_note": str(gene_set_gate.get("license_warning") or ""),
        "semantic_boundary": "resource_lock_only_no_download_no_execution",
        "network_downloads": False,
        "auto_install": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def build_enrichment_background_identifier_gate(analysis_type: str, input_gate: dict[str, Any], gene_set_gate: dict[str, Any]) -> dict[str, Any]:
    blockers = [str(item) for item in input_gate.get("blockers", []) or []]
    warnings = [str(item) for item in input_gate.get("warnings", []) or []]
    source_gene_id_type = str(input_gate.get("source_gene_id_type") or "unknown")
    resource_gene_id_type = str(gene_set_gate.get("gene_id_type") or "unknown")
    if analysis_type == ORA_RESULT_TASK_TYPE:
        background_count = int(input_gate.get("background_universe_count") or 0)
        selected_count = int(input_gate.get("gene_list_count") or 0)
        if background_count <= 0:
            blockers.append("ora_background_universe_empty")
        if selected_count <= 0:
            blockers.append("ora_selected_gene_list_empty")
    elif analysis_type == GSEA_TASK_TYPE:
        background_count = int(input_gate.get("ranked_gene_count") or 0)
        selected_count = int(input_gate.get("ranked_gene_count") or 0)
        if background_count <= 0:
            blockers.append("gsea_ranked_gene_list_missing_or_empty")
        if int(gene_set_gate.get("overlapping_term_count") or 0) <= 0:
            blockers.append("gsea_gene_set_no_overlap_with_ranked_genes")
    else:
        background_count = 0
        selected_count = 0
        blockers.append(f"unsupported_enrichment_analysis_type:{analysis_type or 'missing'}")
    if source_gene_id_type in {"", "unknown"}:
        blockers.append("enrichment_source_gene_id_type_unknown")
    if resource_gene_id_type in {"", "unknown"}:
        blockers.append("enrichment_resource_gene_id_type_unknown")
    if source_gene_id_type not in {"", "unknown"} and resource_gene_id_type not in {"", "unknown"} and source_gene_id_type != resource_gene_id_type:
        blockers.append(f"enrichment_source_resource_gene_id_type_mismatch:{source_gene_id_type}!={resource_gene_id_type}")
    return {
        "schema_version": ENRICHMENT_BACKGROUND_IDENTIFIER_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "analysis_type": analysis_type,
        "source_result_id": str(input_gate.get("source_result_id") or ""),
        "source_result_semantics": str(input_gate.get("source_result_semantics") or ""),
        "source_gene_id_type": source_gene_id_type,
        "resource_gene_id_type": resource_gene_id_type,
        "background_count": background_count,
        "selected_or_ranked_count": selected_count,
        "background_policy": "releasebuild_ora_background_or_gsea_ranked_gene_list_from_deg_result",
        "identifier_policy": "require_matching_gene_id_type_or_explicit_mapping_before_execution",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def build_enrichment_statistical_policy(analysis_type: str, parameter_manifest: dict[str, Any]) -> dict[str, Any]:
    blockers = [str(item) for item in parameter_manifest.get("blockers", []) or []]
    warnings = [str(item) for item in parameter_manifest.get("warnings", []) or []]
    fdr_policy = str(parameter_manifest.get("multiple_testing_policy") or "")
    if parameter_manifest.get("status") != "passed":
        blockers.append("enrichment_parameter_manifest_not_passed")
    if fdr_policy not in FDR_POLICIES:
        blockers.append(f"unsupported_enrichment_fdr_policy:{fdr_policy or 'missing'}")
    for field_name in ("p_value_threshold", "fdr_threshold"):
        blockers.extend(_threshold_blockers(field_name, parameter_manifest.get(field_name)))
    if analysis_type == ORA_RESULT_TASK_TYPE:
        if str(parameter_manifest.get("test_method") or "") not in {"hypergeometric", "fisher_exact"}:
            blockers.append("ora_test_method_not_allowed")
    elif analysis_type == GSEA_TASK_TYPE:
        if int(parameter_manifest.get("permutation_count") or 0) <= 0:
            blockers.append("gsea_parameter_permutation_count_invalid")
        if not str(parameter_manifest.get("rank_metric") or ""):
            blockers.append("gsea_parameter_invalid_rank_metric")
    else:
        blockers.append(f"unsupported_enrichment_analysis_type:{analysis_type or 'missing'}")
    return {
        "schema_version": ENRICHMENT_STATISTICAL_POLICY_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "analysis_type": analysis_type,
        "multiple_testing_policy": fdr_policy,
        "p_value_threshold": parameter_manifest.get("p_value_threshold"),
        "fdr_threshold": parameter_manifest.get("fdr_threshold"),
        "statistical_boundary": "statistical_research_only_no_pathway_activation_or_clinical_conclusion",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def build_enrichment_production_result_schema_gate(
    project_root: str | Path,
    *,
    analysis_type: str,
    result_id: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    selected = _select_result(root, analysis_type, result_id)
    blockers: list[str] = []
    warnings: list[str] = []
    table_validation: dict[str, Any] = {}
    if selected is None:
        blockers.append("enrichment_result_not_found")
    else:
        semantics = _semantics(selected)
        if semantics != "formal_computed_result":
            blockers.append(f"enrichment_production_requires_formal_result:{semantics or 'unknown'}")
        if analysis_type == ORA_RESULT_TASK_TYPE:
            validation = validate_ora_result_index_entry(_schema_entry(selected))
            table_validation = _validate_result_table(root, selected, required=REQUIRED_ORA_TABLE_COLUMNS, row_validator=validate_ora_result_table_row)
        elif analysis_type == GSEA_TASK_TYPE:
            validation = validate_gsea_result_index_entry(_schema_entry(selected))
            table_validation = _validate_result_table(root, selected, required=REQUIRED_GSEA_RESULT_TABLE_COLUMNS, row_validator=validate_gsea_result_table_row)
        else:
            validation = {"status": "blocked", "blockers": [f"unsupported_enrichment_analysis_type:{analysis_type or 'missing'}"], "warnings": []}
            table_validation = {"status": "blocked", "blockers": ["enrichment_result_table_not_validated"], "warnings": []}
        blockers.extend(str(item) for item in validation.get("blockers", []) or [])
        warnings.extend(str(item) for item in validation.get("warnings", []) or [])
        blockers.extend(str(item) for item in table_validation.get("blockers", []) or [])
        warnings.extend(str(item) for item in table_validation.get("warnings", []) or [])
    return {
        "schema_version": ENRICHMENT_PRODUCTION_RESULT_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "analysis_type": analysis_type,
        "selected_result_id": str((selected or {}).get("result_id") or result_id or ""),
        "result_index_path": str(root / RESULT_INDEX),
        "table_validation": table_validation,
        "semantic_boundary": "formal_enrichment_result_schema_gate_no_interpretation",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def build_enrichment_production_preview(
    project_root: str | Path,
    *,
    ora_state: dict[str, Any],
    gsea_state: dict[str, Any],
) -> dict[str, Any]:
    ora = _analysis_preview(project_root, ORA_RESULT_TASK_TYPE, ora_state)
    gsea = _analysis_preview(project_root, GSEA_TASK_TYPE, gsea_state)
    blockers = [*ora.get("blockers", []), *gsea.get("blockers", [])]
    warnings = [*ora.get("warnings", []), *gsea.get("warnings", [])]
    return {
        "schema_version": ENRICHMENT_PRODUCTION_PREVIEW_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "analysis_previews": {"ora_enrichment": ora, "gsea_preranked": gsea},
        "gate_rows": [
            *_preview_rows("ORA", ora),
            *_preview_rows("GSEA", gsea),
        ],
        "action_boundary": "preview_only_no_package_write_no_report_ready_upgrade",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def create_enrichment_production_audit_package(
    project_root: str | Path,
    *,
    analysis_type: str,
    result_id: str,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    schema_gate = build_enrichment_production_result_schema_gate(root, analysis_type=analysis_type, result_id=result_id)
    selected = _select_result(root, analysis_type, result_id)
    blockers = [str(item) for item in schema_gate.get("blockers", []) or []]
    if selected is None:
        blockers.append("enrichment_result_not_found")
    if blockers:
        return {
            "schema_version": ENRICHMENT_PRODUCTION_AUDIT_PACKAGE_SCHEMA_VERSION,
            "status": "blocked",
            "package_path": "",
            "analysis_type": analysis_type,
            "result_id": result_id,
            "blockers": list(dict.fromkeys(blockers)),
            "warnings": list(schema_gate.get("warnings", []) or []),
        }
    package_dir = _next_package_dir(root, selected, output_dir)
    tables_dir = package_dir / "tables"
    manifests_dir = package_dir / "manifests"
    logs_dir = package_dir / "logs"
    for directory in (tables_dir, manifests_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)
    table_path = _result_table_path(root, selected)
    if table_path.is_file():
        shutil.copy2(table_path, tables_dir / table_path.name)
    for artifact in selected.get("log_artifacts", []) or []:
        if isinstance(artifact, dict):
            path = _artifact_path(root, artifact)
            if path.is_file():
                shutil.copy2(path, logs_dir / path.name)
    _write_json(manifests_dir / "result_index_snapshot.json", selected)
    _write_json(manifests_dir / "parameters_manifest.json", selected.get("parameters_manifest", {}))
    _write_json(manifests_dir / "dependency_snapshot.json", selected.get("dependency_snapshot", {}))
    _write_json(manifests_dir / "schema_gate_snapshot.json", schema_gate)
    (package_dir / "README_limitations.md").write_text(_limitations_markdown(analysis_type), encoding="utf-8")
    inventory = _inventory(package_dir)
    manifest = {
        "schema_version": ENRICHMENT_PRODUCTION_AUDIT_PACKAGE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "enrichment_production_audit_package_created",
        "analysis_type": analysis_type,
        "result_id": result_id,
        "package_path": str(package_dir),
        "overwrite_policy": "create_new_timestamped_package_directory",
        "package_inventory": inventory,
        "result_semantics": _semantics(selected),
        "report_ready_eligible": False,
        "gsea_enabled": analysis_type == GSEA_TASK_TYPE,
        "clinical_conclusion_enabled": False,
        "blockers": [],
        "warnings": list(schema_gate.get("warnings", []) or []),
    }
    _write_json(package_dir / "enrichment_production_audit_package_manifest.json", manifest)
    return manifest


def _analysis_preview(project_root: str | Path, analysis_type: str, state: dict[str, Any]) -> dict[str, Any]:
    resource = build_enrichment_resource_lock(analysis_type, state.get("gene_set_gate") if isinstance(state.get("gene_set_gate"), dict) else {})
    background = build_enrichment_background_identifier_gate(analysis_type, state.get("input_gate") if isinstance(state.get("input_gate"), dict) else {}, state.get("gene_set_gate") if isinstance(state.get("gene_set_gate"), dict) else {})
    statistical = build_enrichment_statistical_policy(analysis_type, state.get("parameter_gate") if isinstance(state.get("parameter_gate"), dict) else {})
    schema = build_enrichment_production_result_schema_gate(project_root, analysis_type=analysis_type)
    blockers = [*resource.get("blockers", []), *background.get("blockers", []), *statistical.get("blockers", []), *schema.get("blockers", [])]
    warnings = [*resource.get("warnings", []), *background.get("warnings", []), *statistical.get("warnings", []), *schema.get("warnings", [])]
    return {
        "status": "blocked" if blockers else "passed",
        "analysis_type": analysis_type,
        "resource_lock": resource,
        "background_identifier_gate": background,
        "statistical_policy": statistical,
        "result_schema_gate": schema,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _preview_rows(label: str, preview: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _row(f"{label} resource lock", preview["resource_lock"]),
        _row(f"{label} background / identifier", preview["background_identifier_gate"]),
        _row(f"{label} statistical policy", preview["statistical_policy"]),
        _row(f"{label} production result schema", preview["result_schema_gate"]),
    ]


def _row(name: str, gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "gate": name,
        "status": str(gate.get("status") or "blocked"),
        "basis": str(gate.get("semantic_boundary") or gate.get("statistical_boundary") or gate.get("background_policy") or ""),
        "blockers": "; ".join(str(item) for item in gate.get("blockers", []) or []),
        "warnings": "; ".join(str(item) for item in gate.get("warnings", []) or []),
    }


def _select_result(root: Path, analysis_type: str, result_id: str | None) -> dict[str, Any] | None:
    entries = [entry for entry in load_registry(root).get("results", []) if isinstance(entry, dict)]
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    candidates = [entry for entry in entries if str(entry.get("task_type") or "") == analysis_type]
    formal = [entry for entry in candidates if _semantics(entry) == "formal_computed_result"]
    return (formal or candidates or [None])[-1]


def _schema_entry(entry: dict[str, Any]) -> dict[str, Any]:
    clone = dict(entry)
    clone["report_ready_eligible"] = False
    return clone


def _validate_result_table(root: Path, entry: dict[str, Any], *, required: tuple[str, ...], row_validator: Any) -> dict[str, Any]:
    path = _result_table_path(root, entry)
    if not path.is_file():
        return {"status": "blocked", "path": str(path), "row_count": 0, "blockers": ["enrichment_result_table_missing"], "warnings": []}
    rows = _read_rows(path)
    blockers: list[str] = []
    if not rows:
        blockers.append("enrichment_result_table_empty")
    header = set(rows[0].keys()) if rows else set()
    blockers.extend(f"enrichment_result_table_missing_column:{column}" for column in required if column not in header)
    for index, row in enumerate(rows, start=1):
        validation = row_validator(row)
        blockers.extend(f"row_{index}:{item}" for item in validation.get("blockers", []) or [])
    return {"status": "blocked" if blockers else "passed", "path": str(path), "row_count": len(rows), "blockers": list(dict.fromkeys(blockers)), "warnings": []}


def _result_table_path(root: Path, entry: dict[str, Any]) -> Path:
    for artifact in entry.get("output_artifacts", []) or []:
        if isinstance(artifact, dict) and str(artifact.get("artifact_type") or "") in {"ora_result_table", "gsea_result_table"}:
            return _artifact_path(root, artifact)
    return Path()


def _artifact_path(root: Path, artifact: dict[str, Any]) -> Path:
    path = Path(str(artifact.get("path") or artifact.get("file_path") or ""))
    return path if path.is_absolute() else root / path


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(2048)
        handle.seek(0)
        delimiter = "\t" if "\t" in sample and sample.count("\t") >= sample.count(",") else ","
        return [dict(row) for row in csv.DictReader(handle, delimiter=delimiter)]


def _path_size(raw_path: str) -> int:
    path = Path(raw_path).expanduser()
    return path.stat().st_size if path.is_file() else 0


def _threshold_blockers(name: str, value: object) -> list[str]:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return [f"enrichment_{name}_invalid"]
    if not 0 <= number <= 1:
        return [f"enrichment_{name}_invalid"]
    return []


def _next_package_dir(root: Path, entry: dict[str, Any], output_dir: str | Path | None) -> Path:
    base = Path(output_dir).expanduser() if output_dir else root / "reports" / "enrichment_audit"
    base.mkdir(parents=True, exist_ok=True)
    stem = f"{entry.get('task_type')}-{entry.get('result_id')}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    path = base / stem
    counter = 1
    while path.exists():
        counter += 1
        path = base / f"{stem}-{counter}"
    path.mkdir(parents=True)
    return path


def _inventory(package_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(item for item in package_dir.rglob("*") if item.is_file()):
        rows.append({"path": str(path.relative_to(package_dir)), "size": path.stat().st_size})
    return rows


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _limitations_markdown(analysis_type: str) -> str:
    return (
        "# Enrichment Audit Package Limitations\n\n"
        f"- Analysis type: `{analysis_type}`.\n"
        "- Statistical enrichment evidence only.\n"
        "- No pathway activation or inhibition conclusion.\n"
        "- No clinical conclusion, prognosis, diagnosis, or treatment recommendation.\n"
        "- This audit package does not make the result report-ready.\n"
    )


def _semantics(entry: dict[str, Any]) -> str:
    return normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
