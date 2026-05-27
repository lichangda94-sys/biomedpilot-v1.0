from __future__ import annotations

from app.bioinformatics.deg_engine import build_deg_method_recommendation_gate


def test_method_recommendation_prefers_count_methods_for_raw_counts() -> None:
    gate = build_deg_method_recommendation_gate(
        input_adaptation_gate={"status": "passed", "value_type": "count", "blockers": []},
        design_quality_gate={"status": "passed", "sample_count": 8, "blockers": []},
        data_quality_gate={"status": "passed", "sample_count": 8, "blockers": []},
        dependency_snapshot=_dependency(),
    )

    methods = {row["method"]: row for row in gate["methods"]}
    assert gate["status"] == "passed"
    assert methods["DESeq2"]["state"] == "recommended"
    assert methods["edgeR"]["state"] == "available"
    assert methods["limma"]["state"] in {"available", "recommended"}


def test_method_recommendation_disables_count_models_for_tpm() -> None:
    gate = build_deg_method_recommendation_gate(
        input_adaptation_gate={"status": "passed", "value_type": "TPM", "blockers": []},
        design_quality_gate={"status": "passed", "sample_count": 8, "blockers": []},
        data_quality_gate={"status": "passed", "sample_count": 8, "blockers": []},
        dependency_snapshot=_dependency(),
    )

    methods = {row["method"]: row for row in gate["methods"]}
    assert methods["DESeq2"]["state"] == "disabled"
    assert methods["edgeR"]["disabled_reason"] == "tpm_fpkm_or_log_expression_not_allowed_for_count_model_deg"
    assert methods["limma"]["state"] == "recommended"


def test_method_recommendation_carries_upstream_blockers() -> None:
    gate = build_deg_method_recommendation_gate(
        input_adaptation_gate={"status": "blocked", "value_type": "unknown", "blockers": ["unknown_value_type_blocks_formal_deg"]},
        design_quality_gate={"status": "passed", "sample_count": 4, "blockers": []},
        data_quality_gate={"status": "passed", "sample_count": 4, "blockers": []},
        dependency_snapshot=_dependency(),
    )

    assert gate["status"] == "blocked"
    assert "unknown_value_type_blocks_formal_deg" in gate["blockers"]
    assert all(row["state"] == "disabled" for row in gate["methods"])


def test_method_recommendation_warns_small_sample_size() -> None:
    gate = build_deg_method_recommendation_gate(
        input_adaptation_gate={"status": "passed", "value_type": "count", "blockers": []},
        design_quality_gate={"status": "passed", "sample_count": 4, "blockers": []},
        data_quality_gate={"status": "passed", "sample_count": 4, "blockers": []},
        dependency_snapshot=_dependency(),
    )

    assert "small_sample_size_method_limitations_require_review" in gate["warnings"]


def _dependency() -> dict[str, object]:
    return {
        "packages": {
            "numpy": {"available": True},
            "pandas": {"available": True},
            "scipy": {"available": True},
            "statsmodels": {"available": True},
        },
        "r_backend": {"packages": {"limma": {"available": True}, "DESeq2": {"available": True}, "edgeR": {"available": True}}},
    }
