from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "data" / "medical_terms" / "review_reports"
DOCS = ROOT / "docs" / "medical_terms"


REQUIRED_JSON_FILES = {
    "consumer_adoption": REPORTS / "vocabulary_consumer_adoption_audit.json",
    "strategy_a_plan": REPORTS / "shared_core_strategy_a_execution_plan.json",
    "gene_expression_decision": REPORTS / "gene_expression_profiling_routing_decision.json",
    "source_of_truth": REPORTS / "medical_terms_document_status_index.json",
    "meta_seed_governance": REPORTS / "meta_seed_expansion_governance.json",
    "emtree_review_plan": REPORTS / "emtree_mapping_review_plan.json",
    "geo_long_tail_policy": REPORTS / "bioinformatics_geo_long_tail_intake_policy.json",
    "candidate_archive_policy": REPORTS / "medical_terms_candidate_archive_policy.json",
    "remediation_summary": REPORTS / "medical_terms_handoff_gap_remediation.json",
}


REQUIRED_DOC_FILES = {
    DOCS / "vocabulary_consumer_adoption_audit_20260520.md",
    DOCS / "shared_core_strategy_a_execution_plan_20260520.md",
    DOCS / "gene_expression_profiling_routing_decision_20260520.md",
    DOCS / "medical_terms_source_of_truth_index_20260520.md",
    DOCS / "meta_seed_expansion_governance_20260520.md",
    DOCS / "emtree_mapping_review_plan_20260520.md",
    DOCS / "bioinformatics_geo_long_tail_intake_policy_20260520.md",
    DOCS / "medical_terms_candidate_archive_policy_20260520.md",
    DOCS / "medical_terms_handoff_gap_remediation_20260520.md",
}


def test_handoff_gap_remediation_json_outputs_are_loadable() -> None:
    loaded = {name: _load_json(path) for name, path in REQUIRED_JSON_FILES.items()}

    assert loaded["consumer_adoption"]["audit_name"] == "vocabulary_consumer_adoption_audit"
    assert loaded["strategy_a_plan"]["plan_name"] == "shared_core_strategy_a_execution_plan"
    assert loaded["gene_expression_decision"]["decision_name"] == "gene_expression_profiling_routing_decision"
    assert loaded["source_of_truth"]["index_name"] == "medical_terms_source_of_truth_index"
    assert loaded["meta_seed_governance"]["policy_name"] == "meta_seed_expansion_governance"
    assert loaded["emtree_review_plan"]["plan_name"] == "emtree_mapping_review_plan"
    assert loaded["geo_long_tail_policy"]["policy_name"] == "bioinformatics_geo_long_tail_intake_policy"
    assert loaded["candidate_archive_policy"]["policy_name"] == "medical_terms_candidate_archive_policy"
    assert loaded["remediation_summary"]["report_name"] == "medical_terms_handoff_gap_remediation"


def test_handoff_gap_remediation_docs_exist() -> None:
    missing = [path for path in REQUIRED_DOC_FILES if not path.exists()]
    assert missing == []


def test_consumer_adoption_audit_records_direct_read_findings_without_refactor() -> None:
    audit = _load_json(REQUIRED_JSON_FILES["consumer_adoption"])

    assert audit["runtime_refactor_executed"] is False
    assert audit["loader_behavior_modified"] is False
    assert audit["summary"]["finding_count"] > 0
    assert audit["summary"]["manual_review_required_count"] > 0
    assert "approved_loader_internal" in audit["summary"]["classification_counts"]
    assert "safe_test_fixture" in audit["summary"]["classification_counts"]
    assert any(finding["matched_path"] == "mini_medical_terms_index.json" for finding in audit["findings"])
    assert any(finding["classification"] == "manual_review_required" for finding in audit["findings"])


def test_strategy_a_plan_is_not_executed_and_matches_mirror_count() -> None:
    plan = _load_json(REQUIRED_JSON_FILES["strategy_a_plan"])

    assert plan["strategy"] == "A_deprecate_in_shared"
    assert plan["execution_status"] == "not_executed"
    assert plan["user_confirmation_required"] is True
    assert plan["mini_medical_terms_index_modified"] is False
    assert plan["zh_term_overrides_modified"] is False
    assert plan["terms_to_mark_count"] == 48
    assert plan["has_compatibility_map_count"] == 48
    assert all(item["execution_status"] == "not_executed_requires_user_confirmation" for item in plan["items"])
    assert any(item["redirect_to"] == "meta_outcome:overall_survival" for item in plan["items"])


def test_gene_expression_profiling_decision_routes_to_bioinformatics_only() -> None:
    decision = _load_json(REQUIRED_JSON_FILES["gene_expression_decision"])

    assert decision["term"] == "gene expression profiling"
    assert decision["recommended_target"] == "Bioinformatics scoped vocabulary"
    assert decision["suggested_concept_type"] == "expression_profiling_assay"
    assert decision["meta_analysis_allowed"] is False
    assert decision["shared_core_allowed"] is False
    assert decision["runtime_files_modified"] is False
    assert decision["manual_review_required_before_runtime_change"] is True


def test_governance_policies_keep_runtime_boundaries_closed() -> None:
    meta_governance = _load_json(REQUIRED_JSON_FILES["meta_seed_governance"])
    emtree_plan = _load_json(REQUIRED_JSON_FILES["emtree_review_plan"])
    geo_policy = _load_json(REQUIRED_JSON_FILES["geo_long_tail_policy"])
    archive_policy = _load_json(REQUIRED_JSON_FILES["candidate_archive_policy"])
    remediation = _load_json(REQUIRED_JSON_FILES["remediation_summary"])

    assert meta_governance["automatic_external_chinese_candidate_promotion_allowed"] is False
    assert meta_governance["manual_curated_required"] is True
    assert emtree_plan["automatic_emtree_guessing_allowed"] is False
    assert emtree_plan["embase_search_enabled"] is False
    assert geo_policy["shared_core_allowed"] is False
    assert geo_policy["meta_scope_allowed"] is False
    assert archive_policy["runtime_build_may_read_archive"] is False
    assert remediation["boundaries"]["mini_medical_terms_index_modified"] is False
    assert remediation["boundaries"]["zh_term_overrides_modified"] is False
    assert remediation["boundaries"]["meta_seed_expanded"] is False
    assert remediation["boundaries"]["online_search_enabled"] is False


def test_source_of_truth_index_marks_known_prefix_docs_as_historical() -> None:
    index = _load_json(REQUIRED_JSON_FILES["source_of_truth"])
    current = index["current_source_of_truth"]
    docs_by_name = {Path(row["document"]).name: row for row in index["document_status"]}

    assert current["GEO current audit"] == "data/medical_terms/bioinformatics/audits/geo_core_terms_coverage_audit.json"
    assert current["GTEx current audit"] == "data/medical_terms/bioinformatics/audits/gtex_terms_coverage_audit.json"
    assert docs_by_name["geo_core_terms_coverage_audit.md"]["status"] == "superseded_or_historical"
    assert docs_by_name["gtex_terms_coverage_audit.md"]["status"] == "superseded_or_historical"
    assert index["old_documents_deleted"] is False


def test_protected_runtime_files_are_not_modified_by_this_stage() -> None:
    changed = set(_git_changed_files())

    assert "data/medical_terms/mini_medical_terms_index.json" not in changed
    assert "data/medical_terms/zh_term_overrides.json" not in changed
    assert "data/medical_terms/meta_analysis/meta_seed_terms.json" not in changed
    assert not any(path.startswith("data/medical_terms/bioinformatics/bioinformatics_") for path in changed)
    assert not any(path.startswith("app/shared/query_intelligence/medical_terms/") for path in changed)


def _load_json(path: Path) -> dict[str, object]:
    assert path.exists(), path
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _git_changed_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return sorted({line for output in (result.stdout, staged.stdout) for line in output.splitlines() if line})
