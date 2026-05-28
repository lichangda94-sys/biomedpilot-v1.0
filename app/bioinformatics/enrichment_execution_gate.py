from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.enrichment_backend import build_enrichment_backend_gate
from app.bioinformatics.enrichment_resources import build_enrichment_resource_gate


ENRICHMENT_EXECUTION_GATE_SCHEMA_VERSION = "biomedpilot.enrichment_execution_gate.v1"
ENRICHMENT_PARAMETER_MANIFEST_SCHEMA_VERSION = "biomedpilot.enrichment_parameter_manifest.v2"
ENRICHMENT_CONFIRMATION_SCHEMA_VERSION = "biomedpilot.enrichment_parameter_confirmation.v1"
ENRICHMENT_CONFIRMATION_PATH = Path("manifests") / "enrichment" / "enrichment_parameter_confirmation.json"

SUPPORTED_ANALYSIS_TYPES = {"ora", "gsea_preranked"}
DEFAULT_BACKEND_CAPABILITY = {
    "ora": "ora_enricher",
    "ora_reactome": "ora_reactome",
    "gsea_preranked": "gsea_preranked_fgsea",
}


def build_enrichment_parameter_manifest(
    project_root: str | Path,
    *,
    analysis_type: str,
    source_result_id: str,
    source_result_semantics: str = "formal_computed_result",
    resource_id: str = "",
    required_species: str = "human",
    required_gene_id_type: str = "symbol",
    p_value_cutoff: float = 0.05,
    fdr_cutoff: float = 0.25,
    min_gene_set_size: int = 1,
    max_gene_set_size: int = 500,
    ranking_metric: str = "statistic",
    backend_detection_path: str | Path | None = None,
) -> dict[str, Any]:
    resource_gate = build_enrichment_resource_gate(
        project_root,
        analysis_type=analysis_type,
        required_species=required_species,
        required_gene_id_type=required_gene_id_type,
        resource_id=resource_id,
    )
    backend_gate = build_enrichment_backend_gate(
        project_root,
        analysis_type=analysis_type,
        required_capabilities=[DEFAULT_BACKEND_CAPABILITY.get(analysis_type, "")],
        detection_path=backend_detection_path,
    )
    blockers: list[str] = []
    warnings: list[str] = []
    if analysis_type not in SUPPORTED_ANALYSIS_TYPES:
        blockers.append(f"unsupported_enrichment_analysis_type:{analysis_type}")
    if not source_result_id:
        blockers.append("enrichment_source_result_id_missing")
    if source_result_semantics != "formal_computed_result":
        blockers.append(f"enrichment_source_result_not_formal:{source_result_semantics or 'missing'}")
    if not 0 < p_value_cutoff <= 1:
        blockers.append("invalid_enrichment_p_value_cutoff")
    if not 0 < fdr_cutoff <= 1:
        blockers.append("invalid_enrichment_fdr_cutoff")
    if min_gene_set_size < 1:
        blockers.append("invalid_min_gene_set_size")
    if max_gene_set_size < min_gene_set_size:
        blockers.append("invalid_max_gene_set_size")
    if analysis_type == "gsea_preranked" and not ranking_metric:
        blockers.append("gsea_ranking_metric_missing")
    if resource_gate.get("status") != "passed":
        blockers.extend(str(item) for item in resource_gate.get("blockers", []) or [])
    if backend_gate.get("status") != "passed":
        blockers.extend(str(item) for item in backend_gate.get("blockers", []) or [])
    warnings.extend(str(item) for item in resource_gate.get("warnings", []) or [])
    warnings.extend(str(item) for item in backend_gate.get("warnings", []) or [])
    manifest = {
        "schema_version": ENRICHMENT_PARAMETER_MANIFEST_SCHEMA_VERSION,
        "created_at": _now(),
        "analysis_type": analysis_type,
        "source_result_id": source_result_id,
        "source_result_semantics": source_result_semantics,
        "input_package_id": f"enrichment_from:{source_result_id}" if source_result_id else "",
        "resource_id": str(resource_gate.get("selected_resource_id") or resource_id),
        "resource_gate": resource_gate,
        "backend_gate": backend_gate,
        "engine_candidate": "r_clusterProfiler_enricher" if analysis_type == "ora" else "r_fgsea_preranked",
        "required_backend_capability": DEFAULT_BACKEND_CAPABILITY.get(analysis_type, ""),
        "required_species": required_species,
        "required_gene_id_type": required_gene_id_type,
        "p_value_cutoff": p_value_cutoff,
        "fdr_cutoff": fdr_cutoff,
        "min_gene_set_size": min_gene_set_size,
        "max_gene_set_size": max_gene_set_size,
        "ranking_metric": ranking_metric if analysis_type == "gsea_preranked" else "",
        "dependency_snapshot": backend_gate,
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
    }
    manifest["manifest_hash"] = _hash_manifest(manifest)
    manifest["status"] = "blocked" if manifest["blockers"] else "passed"
    return manifest


def build_enrichment_execution_gate(
    project_root: str | Path,
    *,
    analysis_type: str,
    source_result_id: str,
    source_result_semantics: str = "formal_computed_result",
    resource_id: str = "",
    backend_detection_path: str | Path | None = None,
    confirmation: dict[str, Any] | None = None,
    **parameter_options: Any,
) -> dict[str, Any]:
    manifest = build_enrichment_parameter_manifest(
        project_root,
        analysis_type=analysis_type,
        source_result_id=source_result_id,
        source_result_semantics=source_result_semantics,
        resource_id=resource_id,
        backend_detection_path=backend_detection_path,
        **parameter_options,
    )
    confirmation_gate = validate_enrichment_parameter_confirmation(confirmation or load_enrichment_parameter_confirmation(project_root), parameter_manifest=manifest)
    blockers = [*[str(item) for item in manifest.get("blockers", []) or []], *[str(item) for item in confirmation_gate.get("blockers", []) or []]]
    warnings = [*[str(item) for item in manifest.get("warnings", []) or []], *[str(item) for item in confirmation_gate.get("warnings", []) or []]]
    return {
        "schema_version": ENRICHMENT_EXECUTION_GATE_SCHEMA_VERSION,
        "created_at": _now(),
        "analysis_type": analysis_type,
        "status": "blocked" if blockers else "passed",
        "parameter_manifest": manifest,
        "confirmation_gate": confirmation_gate,
        "can_execute_controlled_r_adapter": not blockers,
        "formal_ui_button_enabled": False,
        "disabled_reason": "" if not blockers else "; ".join(dict.fromkeys(blockers)),
        "boundary": "execution_gate_only_formal_ui_activation_requires_later_stage",
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
    }


def save_enrichment_parameter_confirmation(project_root: str | Path, parameter_manifest: dict[str, Any], *, confirmed_by: str = "user") -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    confirmation = {
        "schema_version": ENRICHMENT_CONFIRMATION_SCHEMA_VERSION,
        "confirmed_at": _now(),
        "confirmed_by": confirmed_by,
        "analysis_type": str(parameter_manifest.get("analysis_type") or ""),
        "source_result_id": str(parameter_manifest.get("source_result_id") or ""),
        "resource_id": str(parameter_manifest.get("resource_id") or ""),
        "engine_candidate": str(parameter_manifest.get("engine_candidate") or ""),
        "manifest_hash": str(parameter_manifest.get("manifest_hash") or ""),
        "parameter_manifest": parameter_manifest,
        "acknowledgements": [
            "statistical_research_only_no_clinical_conclusion",
            "no_network_download_or_auto_install",
            "plot_and_report_ready_remain_separate_gates",
        ],
    }
    path = root / ENRICHMENT_CONFIRMATION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(confirmation, ensure_ascii=False, indent=2), encoding="utf-8")
    return confirmation


def load_enrichment_parameter_confirmation(project_root: str | Path) -> dict[str, Any]:
    path = Path(project_root).expanduser().resolve() / ENRICHMENT_CONFIRMATION_PATH
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"schema_version": ENRICHMENT_CONFIRMATION_SCHEMA_VERSION, "blockers": ["enrichment_parameter_confirmation_invalid_json"]}
    return payload if isinstance(payload, dict) else {}


def validate_enrichment_parameter_confirmation(confirmation: dict[str, Any], *, parameter_manifest: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if parameter_manifest.get("status") != "passed":
        blockers.extend(str(item) for item in parameter_manifest.get("blockers", []) or ["enrichment_parameter_manifest_not_passed"])
    if not confirmation:
        blockers.append("enrichment_parameter_confirmation_missing")
    elif confirmation.get("schema_version") != ENRICHMENT_CONFIRMATION_SCHEMA_VERSION:
        blockers.append("enrichment_parameter_confirmation_schema_mismatch")
    else:
        for field_name in ("analysis_type", "source_result_id", "resource_id", "engine_candidate"):
            if str(confirmation.get(field_name) or "") != str(parameter_manifest.get(field_name) or ""):
                blockers.append(f"enrichment_confirmation_mismatch:{field_name}")
        if str(confirmation.get("manifest_hash") or "") != str(parameter_manifest.get("manifest_hash") or ""):
            blockers.append("enrichment_parameter_confirmation_stale")
        acknowledgements = set(str(item) for item in confirmation.get("acknowledgements", []) or [])
        required = {
            "statistical_research_only_no_clinical_conclusion",
            "no_network_download_or_auto_install",
            "plot_and_report_ready_remain_separate_gates",
        }
        missing = sorted(required - acknowledgements)
        blockers.extend(f"enrichment_confirmation_ack_missing:{item}" for item in missing)
    return {
        "schema_version": "biomedpilot.enrichment_confirmation_gate.v1",
        "status": "blocked" if blockers else "passed",
        "confirmed_at": str(confirmation.get("confirmed_at") or ""),
        "warnings": warnings,
        "blockers": list(dict.fromkeys(blockers)),
    }


def _hash_manifest(manifest: dict[str, Any]) -> str:
    payload = {key: value for key, value in manifest.items() if key not in {"manifest_hash", "created_at", "status"}}
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
