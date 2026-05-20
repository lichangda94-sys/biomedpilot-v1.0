from __future__ import annotations

from app.bioinformatics.deg_engine import validate_deg_result_bundle, validate_deg_result_entry


def test_deg_result_schema_requires_fdr_and_dependency_snapshot() -> None:
    row = {
        "feature_id": "TP53",
        "gene_symbol": "TP53",
        "base_mean_or_mean_expression": 7.5,
        "case_mean": 10,
        "control_mean": 5,
        "log2_fold_change": 1,
        "statistic": 2,
        "p_value": 0.05,
        "adjusted_p_value": 0.1,
        "significance_label": "not_significant",
        "warnings": [],
    }
    assert validate_deg_result_entry(row)["status"] == "passed"

    bundle = {"result_semantics": "formal_computed_result", "rows": [row], "parameters_manifest": {}, "dependency_snapshot": {}}
    validation = validate_deg_result_bundle(bundle)
    assert validation["status"] == "blocked"
    assert "missing_field:engine_name" in validation["blockers"]
