from __future__ import annotations

from app.bioinformatics.deg_engine.r_adapter_contract import (
    build_r_deg_adapter_contract,
    build_r_deg_runtime_gate,
    validate_r_deg_output_schema,
    validate_r_deg_result_registration_bundle,
)


def test_r_deg_adapter_contract_blocks_missing_r_runtime() -> None:
    gate = build_r_deg_runtime_gate(
        method="limma",
        multi_factor_preflight=_preflight(method="limma", method_family="limma_normalized_expression"),
        external_capabilities={
            "runtime.r.available": {"available": False},
            "runtime.bioconductor.available": {"available": True},
            "package.r.limma.available": {"available": True},
        },
    )

    assert gate["status"] == "blocked"
    assert "external_capability_not_available:runtime.r.available" in gate["blockers"]
    assert gate["formal_execution_enabled"] is False
    assert gate["writes_result_index"] is False


def test_r_deg_adapter_contract_blocks_missing_bioconductor() -> None:
    gate = build_r_deg_runtime_gate(
        method="deseq2",
        multi_factor_preflight=_preflight(method="deseq2", method_family="deseq2_count_model"),
        external_capabilities={
            "runtime.r.available": {"available": True},
            "runtime.bioconductor.available": {"available": False},
            "package.r.deseq2.available": {"available": True},
        },
    )

    assert "external_capability_not_available:runtime.bioconductor.available" in gate["blockers"]


def test_r_deg_adapter_contract_blocks_missing_method_package() -> None:
    gate = build_r_deg_runtime_gate(
        method="edgeR",
        multi_factor_preflight=_preflight(method="edger", method_family="edger_count_model"),
        external_capabilities={
            "runtime.r.available": {"available": True},
            "runtime.bioconductor.available": {"available": True},
            "package.r.edger.available": {"available": False},
        },
    )

    assert "external_capability_not_available:package.r.edger.available" in gate["blockers"]


def test_r_deg_adapter_contract_blocks_bad_input_gate() -> None:
    gate = build_r_deg_runtime_gate(
        method="limma",
        multi_factor_preflight={"status": "blocked", "blockers": ["design_matrix_not_full_rank"], "method": "limma"},
        external_capabilities=_all_capabilities("limma"),
    )

    assert gate["status"] == "blocked"
    assert "design_matrix_not_full_rank" in gate["blockers"]


def test_r_deg_output_schema_is_method_specific() -> None:
    assert validate_r_deg_output_schema("limma", ["feature_id", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val"])["status"] == "passed"
    deseq = validate_r_deg_output_schema("deseq2", ["feature_id", "baseMean", "log2FoldChange", "lfcSE", "stat", "pvalue"])
    edger = validate_r_deg_output_schema("edgeR", ["feature_id", "logFC", "logCPM", "PValue", "FDR"])

    assert deseq["status"] == "blocked"
    assert "missing_output_column:padj" in deseq["blockers"]
    assert edger["status"] == "passed"


def test_failed_r_execution_cannot_generate_formal_result() -> None:
    validation = validate_r_deg_result_registration_bundle(
        method="limma",
        execution_status="failed",
        output_columns=["feature_id", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val"],
        result_entry={"result_semantics": "formal_computed_result", "validation_status": "passed"},
        dependency_snapshot={"status": "passed"},
    )

    assert validation["status"] == "blocked"
    assert "r_deg_execution_not_succeeded" in validation["blockers"]
    assert "failed_execution_must_not_create_formal_result" in validation["blockers"]
    assert validation["result_semantics_allowed"] is False


def test_successful_r_bundle_requires_formal_semantics_and_dependency_provenance() -> None:
    dependency_snapshot = {"status": "passed", "capabilities": _all_capabilities("limma")}
    validation = validate_r_deg_result_registration_bundle(
        method="limma",
        execution_status="succeeded",
        output_columns=["feature_id", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val", "B"],
        result_entry={
            "result_semantics": "formal_computed_result",
            "input_package_id": "input-1",
            "parameters_manifest": {"method": "limma"},
            "dependency_snapshot": dependency_snapshot,
            "validation_status": "passed",
        },
        dependency_snapshot=dependency_snapshot,
    )

    assert validation["status"] == "passed"
    assert validation["result_semantics_allowed"] is True


def test_contract_records_result_index_and_review_boundaries() -> None:
    contract = build_r_deg_adapter_contract("deseq2")

    assert contract["adapter_semantics"] == "contract_only_no_r_invocation"
    assert "result_semantics" in contract["result_index_contract"]["required_fields"]
    assert contract["result_review_contract"]["table_columns_remain_method_specific"] is True
    assert contract["result_review_contract"]["clinical_interpretation_forbidden"] is True


def _preflight(*, method: str, method_family: str) -> dict[str, object]:
    return {
        "status": "design_ready",
        "method": method,
        "method_family": method_family,
        "result_semantics": "preflight_only",
        "blockers": [],
        "warnings": [],
    }


def _all_capabilities(method: str) -> dict[str, object]:
    package_key = {
        "limma": "package.r.limma.available",
        "limma_voom": "package.r.limma.available",
        "deseq2": "package.r.deseq2.available",
        "edger": "package.r.edger.available",
    }[method]
    return {
        "runtime.r.available": {"available": True, "version": "4.4"},
        "runtime.bioconductor.available": {"available": True, "version": "3.20"},
        package_key: {"available": True, "version": "1.0"},
    }
