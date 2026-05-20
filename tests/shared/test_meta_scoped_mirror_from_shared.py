from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TERMS = ROOT / "data" / "medical_terms"
META = TERMS / "meta_analysis"
REPORTS = TERMS / "review_reports"


def test_meta_scoped_mirror_and_compatibility_files_exist_without_shared_cleanup() -> None:
    mirror = json.loads((META / "meta_migrated_from_shared_terms.json").read_text(encoding="utf-8"))
    compatibility = json.loads((META / "legacy_meta_compatibility_map.json").read_text(encoding="utf-8"))

    assert mirror["stage"] == "S3_meta_scoped_mirror"
    assert mirror["shared_core_runtime_modified"] is False
    assert mirror["terms_count"] == len(mirror["terms"]) == 48
    assert compatibility["stage"] == "S3_meta_scoped_mirror"
    assert compatibility["routing_active"] is False
    assert compatibility["shared_core_runtime_modified"] is False
    assert compatibility["mappings_count"] == len(compatibility["mappings"]) == 48
    assert (TERMS / "mini_medical_terms_index.json").exists()
    assert (TERMS / "zh_term_overrides.json").exists()


def test_overall_survival_is_single_mirrored_concept_with_two_legacy_ids() -> None:
    terms = _mirror_terms()
    mappings = _compatibility_mappings()
    overall_terms = [term for term in terms if term["preferred_label_en"] == "overall survival"]
    overall_mapping = mappings["meta_outcome:overall_survival"]

    assert len(overall_terms) == 1
    assert overall_terms[0]["concept_id"] == "meta_outcome:overall_survival"
    assert overall_terms[0]["legacy_concept_ids"] == [
        "mini:meta_outcomes_core",
        "mini:meta_analysis_overall_survival",
    ]
    assert "risk" not in {term.lower() for term in overall_terms[0]["synonyms_en"]}
    assert overall_mapping["legacy_concept_ids"] == [
        "mini:meta_outcomes_core",
        "mini:meta_analysis_overall_survival",
    ]
    assert overall_mapping["shared_core_active"] is True
    assert overall_mapping["planned_shared_status"] == "deprecated_in_shared_after_loader_routing"


def test_gene_expression_profiling_is_not_mirrored_to_meta_scope() -> None:
    terms = _mirror_terms()
    conflicts = [
        json.loads(line)
        for line in (REPORTS / "meta_scoped_mirror_conflicts.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert all(term["preferred_label_en"] != "gene expression profiling" for term in terms)
    assert conflicts == [
        {
            "term": "gene expression profiling",
            "concept_id": "mini:data_modality_core",
            "phase": "S3_meta_scoped_mirror",
            "issue_type": "bioinformatics_candidate_migration_required",
            "details": "Gene expression profiling is omics/data-modality vocabulary and must not be mirrored into Meta scoped vocabulary as a PICO term.",
            "recommended_action": "route_to_bioinformatics_scoped_vocabulary_or_keep_manual_routing_item",
            "auto_fix_applied": False,
        }
    ]


def test_survival_data_is_context_only_not_overall_survival_synonym() -> None:
    terms = {term["concept_id"]: term for term in _mirror_terms()}
    survival_data = terms["meta_data_context:survival_data"]
    overall = terms["meta_outcome:overall_survival"]

    assert survival_data["category"] == "meta_data_context_or_extraction_context"
    assert survival_data["usage"]["query_expansion_allowed"] is False
    assert survival_data["usage"]["standalone_search_allowed"] is False
    assert survival_data["requires_context"]["requires_qualified_term"] is True
    assert "survival data" not in {term.lower() for term in overall["synonyms_en"]}
    assert "overall survival data" not in {term.lower() for term in overall["synonyms_en"]}


def test_mirrored_terms_have_meta_only_scope_and_schema_blocks() -> None:
    generic_non_expanding = {
        "meta_research_intent:risk",
        "meta_pico:control",
        "meta_pico:patient",
        "meta_pico:population",
        "meta_study_design:review",
        "meta_context:setting",
    }

    for term in _mirror_terms():
        assert term["scope"] == {
            "shared_core_allowed": False,
            "bioinformatics_allowed": False,
            "meta_analysis_allowed": True,
        }
        assert {"query_expansion_allowed", "standalone_search_allowed", "filter_only"} <= set(term["usage"])
        assert {"requires_population_or_disease", "requires_intervention_or_exposure", "requires_qualified_term"} <= set(
            term["requires_context"]
        )
        assert term["migration"]["migration_status"] == "mirrored_to_meta_scoped"
        assert term["migration"]["compatibility_alias"] is True
        assert term["migration"]["active_in_shared"] is True
        assert term["usage"]["standalone_search_allowed"] is False
        if term["concept_id"] in generic_non_expanding:
            assert term["usage"]["query_expansion_allowed"] is False


def test_compatibility_map_is_data_only_and_meta_scoped() -> None:
    for mapping in _compatibility_mappings().values():
        assert mapping["scope"] == "meta_analysis"
        assert mapping["status"] == "mirrored_to_meta_scoped"
        assert mapping["bioinformatics_allowed"] is False
        assert mapping["shared_core_active"] is True
        assert mapping["planned_shared_status"] == "deprecated_in_shared_after_loader_routing"
        assert mapping["legacy_concept_ids"]


def _mirror_terms() -> list[dict[str, object]]:
    return json.loads((META / "meta_migrated_from_shared_terms.json").read_text(encoding="utf-8"))["terms"]


def _compatibility_mappings() -> dict[str, dict[str, object]]:
    rows = json.loads((META / "legacy_meta_compatibility_map.json").read_text(encoding="utf-8"))["mappings"]
    return {row["new_concept_id"]: row for row in rows}
