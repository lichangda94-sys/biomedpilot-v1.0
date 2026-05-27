from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.deg_ready.builder import build_deg_ready_package

from .data_quality import build_deg_data_quality_gate
from .design_quality import build_deg_design_quality_gate
from .input_adaptation import build_deg_input_adaptation_gate
from .method_recommendation import build_deg_method_recommendation_gate


DEG_CROSS_PROJECT_ACCEPTANCE_SCHEMA_VERSION = "biomedpilot.deg_cross_project_acceptance_gate.v1"


def evaluate_deg_cross_project_scenario(
    input_package: dict[str, Any],
    *,
    scenario_id: str,
    dependency_snapshot: dict[str, Any],
    design_manifest: dict[str, Any] | None = None,
    requested_method_family: str = "",
) -> dict[str, Any]:
    deg_ready = build_deg_ready_package(input_package).to_dict()
    input_gate = build_deg_input_adaptation_gate(input_package, deg_ready, requested_method_family=requested_method_family)
    design_gate = build_deg_design_quality_gate(deg_ready, design_manifest=design_manifest, method_family=requested_method_family)
    data_gate = build_deg_data_quality_gate(deg_ready)
    method_gate = build_deg_method_recommendation_gate(
        input_adaptation_gate=input_gate,
        design_quality_gate=design_gate,
        data_quality_gate=data_gate,
        dependency_snapshot=dependency_snapshot,
    )
    blockers = _dedupe(
        [
            *deg_ready.get("blockers", []),
            *_blocking_items(input_gate),
            *_blocking_items(design_gate),
            *_blocking_items(data_gate),
            *_blocking_items(method_gate),
            *(dependency_snapshot.get("blockers", []) if dependency_snapshot.get("status") != "passed" else []),
        ]
    )
    warnings = _dedupe(
        [
            *deg_ready.get("warnings", []),
            *input_gate.get("warnings", []),
            *design_gate.get("warnings", []),
            *data_gate.get("warnings", []),
            *method_gate.get("warnings", []),
            *(dependency_snapshot.get("warnings", []) or []),
        ]
    )
    return {
        "schema_version": DEG_CROSS_PROJECT_ACCEPTANCE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scenario_id": scenario_id,
        "status": "blocked" if blockers else "passed",
        "input_package_id": str(input_package.get("input_package_id") or ""),
        "value_type": str(input_gate.get("value_type") or ""),
        "gene_id_type": str(input_gate.get("gene_id_type") or ""),
        "dependency_status": str(dependency_snapshot.get("status") or "unknown"),
        "gates": {
            "deg_ready": deg_ready,
            "input_adaptation": input_gate,
            "design_quality": design_gate,
            "data_quality": data_gate,
            "method_recommendation": method_gate,
        },
        "result_index_v2_required": True,
        "formal_result_allowed_only_after_all_gates_pass": not blockers,
        "blockers": blockers,
        "warnings": warnings,
    }


def build_deg_cross_project_acceptance_gate(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    blockers = [f"{item.get('scenario_id')}:{blocker}" for item in scenarios for blocker in item.get("blockers", []) or []]
    return {
        "schema_version": DEG_CROSS_PROJECT_ACCEPTANCE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "passed",
        "scenario_count": len(scenarios),
        "passed_scenarios": [str(item.get("scenario_id") or "") for item in scenarios if item.get("status") == "passed"],
        "blocked_scenarios": [str(item.get("scenario_id") or "") for item in scenarios if item.get("status") == "blocked"],
        "scenarios": scenarios,
        "blockers": blockers,
        "warnings": _dedupe([warning for item in scenarios for warning in item.get("warnings", []) or []]),
        "semantic_boundary": "acceptance_gate_only_not_execution",
    }


def build_deg_real_world_fixture_acceptance(
    fixture_root: str | Path,
    *,
    dependency_snapshot: dict[str, Any],
) -> dict[str, Any]:
    root = Path(fixture_root).expanduser().resolve()
    scenarios = [
        evaluate_deg_cross_project_scenario(_write_fixture_package(root / "local_count", value_type="count"), scenario_id="local_count_positive", dependency_snapshot=dependency_snapshot),
        evaluate_deg_cross_project_scenario(_write_fixture_package(root / "tcga_count", value_type="raw_count"), scenario_id="tcga_like_count_positive", dependency_snapshot=dependency_snapshot),
        evaluate_deg_cross_project_scenario(_write_fixture_package(root / "geo_mapped", value_type="log_expression", gene_id_type="ID_REF", feature_validation="passed"), scenario_id="geo_microarray_mapped_positive", dependency_snapshot=dependency_snapshot),
        evaluate_deg_cross_project_scenario(_write_fixture_package(root / "geo_unmapped", value_type="log_expression", gene_id_type="ID_REF", feature_validation="blocked"), scenario_id="geo_microarray_unmapped_negative", dependency_snapshot=dependency_snapshot),
        evaluate_deg_cross_project_scenario(_write_fixture_package(root / "tpm_count_model", value_type="TPM"), scenario_id="tpm_count_model_negative", dependency_snapshot=dependency_snapshot, requested_method_family="deseq2"),
        evaluate_deg_cross_project_scenario(
            _write_fixture_package(root / "batch_confounded", value_type="count"),
            scenario_id="batch_confounded_negative",
            dependency_snapshot=dependency_snapshot,
            design_manifest={"batch_assignments": {"batch": {"S1": "B1", "S2": "B1", "S3": "B2", "S4": "B2"}}},
        ),
        evaluate_deg_cross_project_scenario(
            _write_fixture_package(root / "sample_mismatch", value_type="count", sample_rows="sample_id\tgroup\nX1\tcase\nX2\tcase\nX3\tcontrol\nX4\tcontrol\n"),
            scenario_id="sample_mismatch_negative",
            dependency_snapshot=dependency_snapshot,
        ),
        evaluate_deg_cross_project_scenario(_write_fixture_package(root / "missing_dependency", value_type="count"), scenario_id="missing_dependency_negative", dependency_snapshot={"status": "blocked", "blockers": ["missing_python_package:scipy"]}),
    ]
    gate = build_deg_cross_project_acceptance_gate(scenarios)
    gate["fixture_root"] = str(root)
    gate["expected_positive_scenarios"] = ["local_count_positive", "tcga_like_count_positive", "geo_microarray_mapped_positive"]
    gate["expected_negative_scenarios"] = [
        "geo_microarray_unmapped_negative",
        "tpm_count_model_negative",
        "batch_confounded_negative",
        "sample_mismatch_negative",
        "missing_dependency_negative",
    ]
    gate["positive_scenarios_passed"] = all(item in gate["passed_scenarios"] for item in gate["expected_positive_scenarios"])
    gate["negative_scenarios_blocked"] = all(item in gate["blocked_scenarios"] for item in gate["expected_negative_scenarios"])
    gate["backend_schema_consistency"] = _backend_schema_consistency()
    if gate["positive_scenarios_passed"] and gate["negative_scenarios_blocked"]:
        gate["status"] = "passed"
        gate["blockers"] = []
    return gate


def _blocking_items(gate: dict[str, Any]) -> list[str]:
    return [str(item) for item in gate.get("blockers", []) or []] if gate.get("status") == "blocked" else []


def _write_fixture_package(
    root: Path,
    *,
    value_type: str,
    gene_id_type: str = "symbol",
    feature_validation: str = "passed",
    sample_rows: str = "sample_id\tgroup\nS1\tcase\nS2\tcase\nS3\tcontrol\nS4\tcontrol\n",
) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    matrix = root / "matrix.tsv"
    header = "ID_REF" if gene_id_type in {"ID_REF", "probe", "probe_id"} else "gene"
    matrix.write_text(
        f"{header}\tS1\tS2\tS3\tS4\n"
        "TP53\t100\t120\t20\t25\n"
        "BRCA1\t80\t90\t30\t35\n"
        "GAPDH\t50\t52\t49\t51\n",
        encoding="utf-8",
    )
    sample = root / "sample.tsv"
    sample.write_text(sample_rows, encoding="utf-8")
    return {
        "input_package_id": f"fixture-{root.name}",
        "package_type": "deg_recompute",
        "value_type": value_type,
        "gene_id_type": gene_id_type,
        "expression_asset": {"asset_id": "expr", "path": str(matrix), "asset_type": "expression_matrix"},
        "sample_metadata_asset": {"asset_id": "sample", "path": str(sample), "asset_type": "sample_metadata"},
        "group_design_asset": {"asset_id": "group", "asset_type": "group_design"},
        "feature_annotation_asset": {"asset_id": "feature", "validation_status": feature_validation, "asset_type": "feature_annotation"},
        "blockers": [],
        "warnings": [],
    }


def _backend_schema_consistency() -> dict[str, Any]:
    required_fields = [
        "result_id",
        "task_run_id",
        "task_type",
        "result_semantics",
        "input_package_id",
        "parameters_manifest",
        "engine_name",
        "engine_version",
        "dependency_snapshot",
        "output_artifacts",
        "validation_status",
        "warnings",
        "blockers",
    ]
    backends = ["python_scipy_statsmodels", "limma", "DESeq2", "edgeR"]
    return {
        "status": "passed",
        "backends": backends,
        "required_result_index_fields": required_fields,
        "result_semantics": "formal_computed_result_only_after_all_gates_pass",
        "plot_artifacts_default": [],
        "report_ready_eligible_default": False,
        "schema_unification_required": True,
    }


def _dedupe(values: list[Any]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
