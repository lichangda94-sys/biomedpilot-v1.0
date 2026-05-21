from __future__ import annotations

from app.bioinformatics.gsea import build_gsea_parameter_manifest


def test_valid_gsea_parameter_manifest_passes() -> None:
    manifest = build_gsea_parameter_manifest(_gsea_input(), _gene_set())

    assert manifest["status"] == "passed"
    assert manifest["permutation_type"] == "gene_set"
    assert manifest["random_seed"] == 1
    assert manifest["multiple_testing_policy"] == "BH"


def test_missing_random_seed_and_invalid_size_bounds_block() -> None:
    manifest = build_gsea_parameter_manifest(_gsea_input(), _gene_set(), random_seed=None, min_gene_set_size=500, max_gene_set_size=10)

    assert "gsea_parameter_random_seed_missing" in manifest["blockers"]
    assert "gsea_parameter_gene_set_size_bounds_invalid" in manifest["blockers"]


def test_missing_source_and_invalid_rank_metric_block() -> None:
    gsea_input = _gsea_input()
    gsea_input["source_result_id"] = ""
    gsea_input["rank_metric"] = "bad_metric"
    manifest = build_gsea_parameter_manifest(gsea_input, _gene_set())

    assert "gsea_parameter_missing_source_result" in manifest["blockers"]
    assert "gsea_parameter_invalid_rank_metric" in manifest["blockers"]


def test_msigdb_license_warning_must_be_acknowledged() -> None:
    gene_set = _gene_set()
    gene_set["warnings"] = ["gsea_msigdb_resource_requires_manual_license_acknowledgement"]

    blocked = build_gsea_parameter_manifest(_gsea_input(), gene_set, msigdb_license_acknowledged=False)
    passed = build_gsea_parameter_manifest(_gsea_input(), gene_set, msigdb_license_acknowledged=True)

    assert "gsea_msigdb_license_or_source_unacknowledged" in blocked["blockers"]
    assert passed["status"] == "passed"


def test_gsea_parameter_blocks_when_input_or_gene_set_gate_blocked() -> None:
    gsea_input = _gsea_input()
    gsea_input["status"] = "blocked"
    gsea_input["blockers"] = ["gsea_rank_metric_all_zero"]
    gene_set = _gene_set()
    gene_set["status"] = "blocked"
    gene_set["blockers"] = ["gsea_gene_set_no_overlap_with_ranked_genes"]

    manifest = build_gsea_parameter_manifest(gsea_input, gene_set)

    assert "gsea_rank_metric_all_zero" in manifest["blockers"]
    assert "gsea_gene_set_no_overlap_with_ranked_genes" in manifest["blockers"]


def _gsea_input() -> dict[str, object]:
    return {
        "status": "passed",
        "gsea_input_id": "gsea-input-1",
        "source_result_id": "deg-1",
        "source_result_semantics": "formal_computed_result",
        "source_task_type": "deg",
        "rank_metric": "signed_log10_fdr_by_log2fc",
        "rank_metric_policy": "gsea_preranked_metric_gate_only_no_execution",
        "ranked_gene_count": 12,
        "warnings": [],
        "blockers": [],
    }


def _gene_set() -> dict[str, object]:
    return {
        "status": "passed",
        "gene_set_resource_id": "sets",
        "warnings": [],
        "blockers": [],
    }
