from __future__ import annotations

from app.bioinformatics.enrichment.parameter_gate import build_ora_parameter_manifest


def test_valid_ora_parameter_manifest_passes() -> None:
    manifest = build_ora_parameter_manifest(_ora_input(), _gene_set())

    assert manifest["status"] == "passed"
    assert manifest["test_method"] == "hypergeometric"
    assert manifest["multiple_testing_policy"] == "BH"
    assert manifest["blockers"] == []


def test_empty_selected_gene_list_blocks_parameters() -> None:
    ora_input = _ora_input()
    ora_input["gene_list_count"] = 0

    manifest = build_ora_parameter_manifest(ora_input, _gene_set())

    assert manifest["status"] == "blocked"
    assert "ora_selected_gene_list_empty" in manifest["blockers"]


def test_invalid_thresholds_and_missing_policy_block_parameters() -> None:
    manifest = build_ora_parameter_manifest(
        _ora_input(),
        _gene_set(),
        p_value_threshold=1.5,
        fdr_threshold=-0.1,
        multiple_testing_policy="",
        test_method="unsupported",
        min_gene_set_size=600,
        max_gene_set_size=10,
    )

    assert "ora_p_value_threshold_invalid" in manifest["blockers"]
    assert "ora_fdr_threshold_invalid" in manifest["blockers"]
    assert "ora_missing_multiple_testing_policy" in manifest["blockers"]
    assert "ora_test_method_not_allowed" in manifest["blockers"]
    assert "ora_gene_set_size_bounds_invalid" in manifest["blockers"]


def test_gene_id_mismatch_unresolved_blocks_parameters() -> None:
    gene_set = _gene_set()
    gene_set["status"] = "blocked"
    gene_set["blockers"] = ["ora_gene_set_gene_id_mismatch:entrez!=symbol"]

    manifest = build_ora_parameter_manifest(_ora_input(), gene_set)

    assert "ora_gene_set_gene_id_mismatch:entrez!=symbol" in manifest["blockers"]


def _ora_input() -> dict[str, object]:
    return {
        "status": "passed",
        "ora_input_id": "ora-input-1",
        "source_result_id": "deg-1",
        "source_task_type": "deg",
        "source_result_semantics": "formal_computed_result",
        "gene_list_count": 12,
        "background_universe_count": 2000,
        "warnings": [],
        "blockers": [],
    }


def _gene_set() -> dict[str, object]:
    return {
        "status": "passed",
        "validation_status": "passed",
        "gene_set_resource_id": "sets",
        "warnings": [],
        "blockers": [],
    }
