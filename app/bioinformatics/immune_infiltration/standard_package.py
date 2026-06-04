from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_immune_scoring_standard_result_package(
    root: Path,
    *,
    result_id: str,
    score_matrix_path: Path,
    coverage_path: Path,
    sample_summary_path: Path,
    manifest_path: Path,
    receipt_path: Path,
    manifest: dict[str, Any],
    receipt: dict[str, Any],
) -> Path:
    package_dir = root / "analysis" / "standard_packages" / result_id
    for dirname in ("tables", "plots", "reports", "logs"):
        (package_dir / dirname).mkdir(parents=True, exist_ok=True)

    table_artifacts = [
        _copy_artifact(package_dir, "tables", score_matrix_path, "immune_score_matrix"),
        _copy_artifact(package_dir, "tables", coverage_path, "immune_signature_coverage"),
        _copy_artifact(package_dir, "tables", sample_summary_path, "immune_sample_score_summary"),
    ]
    _copy_artifact(package_dir, "logs", manifest_path, "immune_scoring_manifest")
    _copy_artifact(package_dir, "logs", receipt_path, "immune_scoring_receipt")
    (package_dir / "logs" / "worker.log").write_text(
        "\n".join(
            [
                "status=passed",
                "module_id=immune_infiltration",
                "mode=lite",
                "source=app.bioinformatics.immune_infiltration.scoring.run_immune_scoring",
                "runtime_install_policy=forbidden",
                "resource_download_policy=forbidden",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (package_dir / "reports" / "README_limitations.md").write_text(
        "\n".join(
            [
                "# Immune / TME scoring standard package",
                "",
                "This standard result package mirrors exploratory bulk immune / TME signature scoring outputs.",
                "It is testing-level output for package-contract validation and UI artifact discovery.",
                "It does not create report-ready output, clinical interpretation, diagnosis, prognosis, risk grouping, treatment recommendations, GSVA, CellChat, Seurat, CIBERSORT, xCell, or ESTIMATE results.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result_payload = {
        "schema_version": "biomedpilot.analysis.result.v1",
        "module_id": "immune_infiltration",
        "mode": "lite",
        "task_id": result_id,
        "status": "passed",
        "result_semantics": "testing_level",
        "summary": {
            "message": "Exploratory immune / TME signature scoring mirrored into a standard result package.",
            "analysis_type": "immune_tme_scoring",
            "source_result_id": result_id,
            "scoring_method": str(manifest.get("scoring_method") or ""),
            "value_transform": str(manifest.get("value_transform") or ""),
            "sample_count": int(manifest.get("sample_count") or 0),
            "gene_count": int(manifest.get("gene_count") or 0),
            "signature_count": int(manifest.get("signature_count") or 0),
            "scored_signature_count": int(manifest.get("scored_signature_count") or 0),
            "clinical_conclusion_status": "not_generated",
            "worker_boundary_status": "sidecar_only_not_isolated_standard_worker",
        },
        "tables": table_artifacts,
        "plots": [],
        "reports": [{"artifact_type": "standard_package_limitations_report", "path": "reports/README_limitations.md"}],
        "blockers": [],
        "warnings": [
            "standard_package_sidecar_for_existing_immune_scoring_service",
            "testing_level_exploratory_signature_score",
            "report_ready_not_enabled_by_standard_package",
            "clinical_conclusion_not_generated",
        ],
        "created_at": now,
    }
    provenance_payload = {
        "schema_version": "biomedpilot.analysis.provenance.v1",
        "module_id": "immune_infiltration",
        "mode": "lite",
        "task_id": result_id,
        "created_at": now,
        "input_path": str(manifest.get("input_expression_matrix_path") or ""),
        "input_hash": _sha256_file(Path(str(manifest.get("input_expression_matrix_path") or ""))),
        "parameter_hash": _sha256_json(_parameter_projection(manifest)),
        "random_seed": None,
        "engine": {"name": "biomedpilot_bulk_signature_scoring", "version": "1"},
        "runtime": {
            "r_version": "not_used_python_exploratory_service",
            "bioconductor_version": "not_used_python_exploratory_service",
            "package_versions": {},
            "external_tool_versions": {},
        },
        "command": "app.bioinformatics.immune_infiltration.scoring.run_immune_scoring",
        "worker_boundary": {
            "boundary_type": "legacy_service_adapter_sidecar",
            "standard_worker_entrypoint": "not_used",
            "subprocess_owner": "app.bioinformatics.immune_infiltration.scoring",
            "migration_status": "sidecar_only_not_isolated_standard_worker",
            "task_system_invocation": "not_yet_migrated",
        },
        "source_result_id": result_id,
        "source_manifest_hash": _sha256_json(manifest),
        "source_receipt_hash": _sha256_json(receipt),
        "source_table_hashes": {
            "immune_score_matrix": _sha256_file(score_matrix_path),
            "immune_signature_coverage": _sha256_file(coverage_path),
            "immune_sample_score_summary": _sha256_file(sample_summary_path),
        },
    }
    (package_dir / "result.json").write_text(json.dumps(result_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (package_dir / "provenance.json").write_text(json.dumps(provenance_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return package_dir


def _copy_artifact(package_dir: Path, group: str, source: Path, artifact_type: str) -> dict[str, str]:
    target = package_dir / group / source.name
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return {"artifact_type": artifact_type, "path": f"{group}/{source.name}"}


def _parameter_projection(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset_id": manifest.get("dataset_id") or "",
        "input_value_type": manifest.get("input_value_type") or "",
        "gene_id_column": manifest.get("gene_id_column") or "",
        "sample_columns": manifest.get("sample_columns") or [],
        "scoring_method": manifest.get("scoring_method") or "",
        "value_transform": manifest.get("value_transform") or "",
        "signature_count": manifest.get("signature_count") or 0,
    }


def _sha256_json(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""
