from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.analysis_runtime.standard_package import write_legacy_service_adapter_invocation_manifest


def write_correlation_standard_result_package(
    project_root: Path,
    *,
    result_id: str,
    result_path: Path,
    summary_path: Path,
    summary: dict[str, Any],
) -> Path:
    package_dir = project_root / "analysis" / "standard_packages" / result_id
    for dirname in ("tables", "plots", "reports", "logs"):
        (package_dir / dirname).mkdir(parents=True, exist_ok=True)

    table_name = result_path.name
    summary_name = summary_path.name
    (package_dir / "tables" / table_name).write_text(result_path.read_text(encoding="utf-8"), encoding="utf-8")
    (package_dir / "logs" / summary_name).write_text(summary_path.read_text(encoding="utf-8"), encoding="utf-8")
    (package_dir / "logs" / "worker.log").write_text(
        "\n".join(
            [
                "status=passed",
                "module_id=correlation",
                "mode=lite",
                "source=app.bioinformatics.services.correlation_runner.run_expression_correlation",
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
                "# Correlation standard package",
                "",
                "This standard result package mirrors a local Pearson expression-correlation result.",
                "It is testing-level output for package-contract validation and UI artifact discovery.",
                "It does not create report-ready output, causal interpretation, clinical interpretation, diagnosis, prognosis, risk grouping, or treatment recommendations.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result_payload = {
        "schema_version": "biomedpilot.analysis.result.v1",
        "module_id": "correlation",
        "mode": "lite",
        "task_id": result_id,
        "status": "passed",
        "result_semantics": "testing_level",
        "summary": {
            "message": "Local Pearson expression correlation mirrored into a standard result package.",
            "analysis_type": "correlation",
            "source_result_id": result_id,
            "dataset_id": str(summary.get("dataset_id") or ""),
            "target_gene": str(summary.get("target_gene") or ""),
            "method": str(summary.get("method") or "pearson"),
            "sample_count": int(summary.get("sample_count") or 0),
            "gene_count_tested": int(summary.get("gene_count_tested") or 0),
            "returned_result_count": int(summary.get("returned_result_count") or 0),
            "clinical_conclusion_status": "not_generated",
            "worker_boundary_status": "sidecar_only_not_isolated_standard_worker",
        },
        "tables": [{"artifact_type": "correlation_result_table", "path": f"tables/{table_name}"}],
        "plots": [],
        "reports": [{"artifact_type": "standard_package_limitations_report", "path": "reports/README_limitations.md"}],
        "blockers": [],
        "warnings": [
            "standard_package_sidecar_for_existing_correlation_runner",
            "testing_level_local_pearson_correlation",
            "report_ready_not_enabled_by_standard_package",
            "clinical_conclusion_not_generated",
        ],
        "created_at": now,
    }
    provenance_payload = {
        "schema_version": "biomedpilot.analysis.provenance.v1",
        "module_id": "correlation",
        "mode": "lite",
        "task_id": result_id,
        "created_at": now,
        "input_path": str(summary.get("source_expression_path") or ""),
        "input_hash": _sha256_file(Path(str(summary.get("source_expression_path") or ""))),
        "parameter_hash": _sha256_json(
            {
                "target_gene": summary.get("target_gene") or "",
                "dataset_id": summary.get("dataset_id") or "",
                "method": summary.get("method") or "pearson",
                "max_results": summary.get("returned_result_count") or 0,
            }
        ),
        "random_seed": None,
        "engine": {"name": "biomedpilot_local_pearson_correlation", "version": "1"},
        "runtime": {
            "r_version": "not_used_python_correlation_runner",
            "bioconductor_version": "not_used_python_correlation_runner",
            "package_versions": {},
            "external_tool_versions": {},
        },
        "command": "app.bioinformatics.services.correlation_runner.run_expression_correlation",
        "worker_boundary": {
            "boundary_type": "legacy_service_adapter_sidecar",
            "standard_worker_entrypoint": "not_used",
            "subprocess_owner": "app.bioinformatics.services.correlation_runner",
            "migration_status": "sidecar_only_not_isolated_standard_worker",
            "task_system_invocation": "not_yet_migrated",
        },
        "source_result_id": result_id,
        "source_summary_hash": _sha256_json(summary),
        "source_result_table_hash": _sha256_file(result_path),
    }
    (package_dir / "result.json").write_text(json.dumps(result_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (package_dir / "provenance.json").write_text(json.dumps(provenance_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_legacy_service_adapter_invocation_manifest(
        package_dir,
        module_id="correlation",
        mode="lite",
        task_id=result_id,
        subprocess_owner="app.bioinformatics.services.correlation_runner",
        command="app.bioinformatics.services.correlation_runner.run_expression_correlation",
        created_at=now,
    )
    return package_dir


def _sha256_json(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""
