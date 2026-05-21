from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.meta_analysis.project_workspace import create_meta_analysis_project
from app.meta_analysis.search_config_draft import (
    build_meta_seed_search_config_draft,
    build_user_edited_search_plan,
    save_confirmed_search_plan,
    save_meta_seed_search_config_draft,
    save_rejected_search_config_draft,
)
from app.meta_analysis.search_execution_preflight import (
    build_pubmed_search_execution_plan,
    save_pubmed_search_execution_plan,
)
from app.shared.query_intelligence.meta_seed_terms import build_pubmed_query_blocks, match_chinese_question_to_pico


ROOT = Path(__file__).resolve().parents[2]
TERMS = ROOT / "data" / "medical_terms"
BIO = TERMS / "bioinformatics"
META = TERMS / "meta_analysis"
AUDIT_JSON = TERMS / "review_reports" / "medical_terms_integration_audit.json"


def test_shared_core_pollution_is_detected_and_bioinformatics_terms_stay_out() -> None:
    mini = json.loads((TERMS / "mini_medical_terms_index.json").read_text(encoding="utf-8"))
    zh_overrides = json.loads((TERMS / "zh_term_overrides.json").read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    shared_terms = _terms_from_shared_core(mini)
    override_terms = _terms_from_zh_overrides(zh_overrides)
    meta_scope_terms_found = {
        "overall survival",
        "progression-free survival",
        "hazard ratio",
        "odds ratio",
        "cohort study",
        "randomized controlled trial",
    }
    forbidden_bioinformatics_shared = {
        "gse",
        "gsm",
        "tpm",
        "fpkm",
        "series matrix",
        "sample metadata",
    }

    assert meta_scope_terms_found <= shared_terms
    assert audit["shared_core_pollution_detected"] is True
    assert any(issue["id"] == "shared_core_contains_meta_scope_terms" for issue in audit["issues"])
    assert forbidden_bioinformatics_shared.isdisjoint(shared_terms)
    assert {"gse", "gsm", "gpl", "series matrix", "sample metadata"}.isdisjoint(override_terms)
    assert "meta_exposure:obesity" not in {str(row.get("concept_id", "")) for row in mini}
    assert "meta_exposure:prediabetes" not in {str(row.get("concept_id", "")) for row in mini}
    assert (TERMS / "review_queue" / "shared" / "shared_promotion_candidates_from_meta.jsonl").exists()


def test_bioinformatics_scope_loads_expected_terms_and_excludes_meta_terms() -> None:
    species = _load_bio_terms("bioinformatics_species_terms.json")
    tissues = _load_bio_terms("bioinformatics_tissue_terms.json")
    data_types = _load_bio_terms("bioinformatics_data_type_terms.json")
    grouping = _load_bio_terms("bioinformatics_grouping_terms.json")
    registry = _load_bio_terms("bioinformatics_dataset_registry_terms.json")
    stop_terms = _load_bio_terms("bioinformatics_stop_terms.json")
    all_bio_terms = _flatten_terms([species, tissues, data_types, grouping, registry, stop_terms])

    assert {"homo sapiens", "mus musculus", "rattus norvegicus", "human", "mouse", "rat"} <= all_bio_terms
    assert {"skin", "heart", "artery", "muscle - skeletal", "nerve - tibial"} <= all_bio_terms
    assert {"tpm", "fpkm", "raw counts", "count matrix"} <= all_bio_terms
    assert {"adjacent normal", "knockdown", "overexpression", "platform annotation"} <= all_bio_terms
    assert {"overall survival", "progression-free survival", "hazard ratio", "cohort study", "risk factor", "rob2", "prisma"}.isdisjoint(all_bio_terms)

    mouse_terms = [row for row in species if "mouse" in _row_terms(row)]
    assert len(mouse_terms) == 1
    assert mouse_terms[0]["concept_id"] == "bio_species:mus_musculus"

    by_label = {str(row.get("preferred_label", "")).lower(): row for row in data_types}
    assert by_label["tpm"]["concept_type"] == "normalized_expression"
    assert by_label["tpm"].get("is_raw_counts") is False
    assert by_label["fpkm"]["concept_type"] == "normalized_expression"
    assert by_label["fpkm"].get("is_raw_counts") is False
    assert by_label["raw counts"].get("is_raw_counts") is True
    assert by_label["count matrix"]["concept_type"] == "expression_matrix"

    for row in stop_terms:
        assert row["term"] in {"dataset", "sample", "series"}
        assert row["term_type"] == "scoped_stop_term"
        assert row["global_stop_word"] is False
        assert "sample_metadata_detection" in row["does_not_block"]


def test_meta_scope_generates_seed_pico_query_and_excludes_bioinformatics_terms() -> None:
    cases = {
        "糖尿病前期与甲状腺癌风险的关系": {"meta_disease:thyroid_cancer", "meta_exposure:prediabetes"},
        "二甲双胍治疗2型糖尿病的疗效": {
            "meta_disease:type_2_diabetes_mellitus",
            "meta_intervention:metformin",
        },
        "放射性碘治疗甲状腺癌复发的影响": {
            "meta_disease:thyroid_cancer",
            "meta_intervention:radioactive_iodine_therapy",
            "meta_outcome:recurrence",
        },
        "肥胖与乳腺癌风险的Meta分析": {
            "meta_disease:breast_cancer",
            "meta_exposure:obesity",
            "meta_study_design:meta_analysis",
        },
    }

    for question, expected_ids in cases.items():
        draft = match_chinese_question_to_pico(question)
        concept_ids = set(draft.concept_ids())
        blocks = build_pubmed_query_blocks(draft.concept_ids())
        query = " ".join(blocks)

        assert expected_ids <= concept_ids
        assert blocks
        assert "hazard ratio" not in query.lower()
        assert "risk factor" not in query.lower()
        assert "meta-analysis" not in query.lower()

    guarded = build_meta_seed_search_config_draft("肥胖与乳腺癌风险的Meta分析，报告HR")
    guards = {guard.concept_id: guard for guard in guarded.detected_concepts}
    assert guards["meta_effect:hazard_ratio"].included_in_pubmed_topic_query is False
    assert guards["meta_study_design:meta_analysis"].filter_only is True

    bio_text = "GSE GSM GPL TPM FPKM raw counts probe ID series matrix sample metadata TCGA barcode GTEx tissue"
    assert match_chinese_question_to_pico(bio_text).concept_ids() == []


def test_meta_workflow_gate_and_pubmed_preflight_remain_non_executing(tmp_path) -> None:
    project = create_meta_analysis_project("Integration Audit", tmp_path)
    draft = build_meta_seed_search_config_draft("肥胖与乳腺癌风险的Meta分析，报告HR")

    draft_path = save_meta_seed_search_config_draft(project.project_root, draft)
    draft_payload = json.loads(draft_path.read_text(encoding="utf-8"))
    assert draft_payload["review_status"] == "draft_only"
    assert draft_payload["confirmed_search_plan"] is None
    with pytest.raises(FileNotFoundError):
        build_pubmed_search_execution_plan(project.project_root)

    rejected_path = save_rejected_search_config_draft(project.project_root, draft, user_notes="Rejected in audit.")
    rejected_payload = json.loads(rejected_path.read_text(encoding="utf-8"))
    assert rejected_payload["review_status"] == "rejected"
    assert rejected_payload["confirmed_search_plan"] is None
    with pytest.raises(FileNotFoundError):
        build_pubmed_search_execution_plan(project.project_root)

    edited = build_user_edited_search_plan(
        draft,
        guard_overrides=[
            {
                "concept_id": "meta_effect:hazard_ratio",
                "requested_action": "include_in_pubmed_topic_query",
                "reason": "Audit override check.",
            }
        ],
    )
    confirmed_path = save_confirmed_search_plan(project.project_root, draft, edited, user_confirmed=True)
    with pytest.raises(ValueError, match="Guard override warnings must be explicitly confirmed"):
        build_pubmed_search_execution_plan(confirmed_path)

    confirmed_edit = build_user_edited_search_plan(
        draft,
        guard_overrides=[
            {
                "concept_id": "meta_effect:hazard_ratio",
                "requested_action": "include_in_pubmed_topic_query",
                "reason": "Audit override warning explicitly confirmed.",
            }
        ],
        guard_override_confirmed=True,
    )
    save_confirmed_search_plan(project.project_root, draft, confirmed_edit, user_confirmed=True)
    plan_path = save_pubmed_search_execution_plan(project.project_root)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))

    assert plan["plan_status"] == "draft_execution_plan"
    assert plan["search_execution_status"] == "not_executed"
    assert plan["online_retrieval_executed"] is False
    assert plan["database"] == "PubMed"
    assert any("PubMed was not queried" in warning for warning in plan["warnings"])


def test_machine_readable_integration_audit_report_matches_current_boundaries() -> None:
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))

    assert audit["audit_name"] == "medical_terms_integration_audit"
    assert audit["audit_date"] == "2026-05-20"
    assert audit["shared_core_modified"] is False
    assert audit["shared_core_pollution_detected"] is True
    assert audit["bioinformatics_scope_isolation_passed"] is True
    assert audit["meta_scope_isolation_passed"] is True
    assert audit["meta_search_draft_available"] is True
    assert audit["meta_review_gate_available"] is True
    assert audit["meta_pubmed_preflight_available"] is True
    assert audit["pubmed_online_search_enabled"] is False
    assert audit["chinese_database_search_enabled"] is False
    assert audit["chinese_pdf_extraction_enabled"] is False
    assert audit["english_pdf_extraction_ui_enabled"] is False
    assert any(issue["id"] == "shared_core_contains_meta_scope_terms" for issue in audit["issues"])
    assert any(fix["id"] == "meta_matcher_short_latin_token_boundary_fix" for fix in audit["fixes"])


def _load_bio_terms(filename: str) -> list[dict[str, object]]:
    payload = json.loads((BIO / filename).read_text(encoding="utf-8"))
    return list(payload["terms"])


def _terms_from_shared_core(rows: list[dict[str, object]]) -> set[str]:
    keys = (
        "concept_id",
        "preferred_label_en",
        "concept_type",
        "zh_terms",
        "synonyms_en",
        "exact_synonyms_en",
        "related_synonyms_en",
        "abbreviations",
        "mesh_terms",
        "normalized_terms",
    )
    return {term.lower() for row in rows for term in _values(row, keys)}


def _terms_from_zh_overrides(rows: list[dict[str, object]]) -> set[str]:
    keys = ("zh_term", "zh_terms", "preferred_label_en", "mapped_concept_ids", "synonyms_en", "disease_terms_en")
    return {term.lower() for row in rows for term in _values(row, keys)}


def _flatten_terms(groups: list[list[dict[str, object]]]) -> set[str]:
    keys = (
        "term",
        "preferred_label",
        "preferred_zh",
        "synonyms",
        "zh_entry_terms",
        "gtex_subtype_mappings",
        "concept_type",
        "term_type",
    )
    return {term.lower() for group in groups for row in group for term in _values(row, keys)}


def _row_terms(row: dict[str, object]) -> set[str]:
    return {term.lower() for term in _values(row, ("term", "preferred_label", "synonyms"))}


def _values(row: dict[str, object], keys: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for key in keys:
        value = row.get(key)
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    values.append(item)
                elif isinstance(item, dict):
                    values.extend(str(v) for v in item.values() if isinstance(v, str))
        elif isinstance(value, dict):
            values.extend(str(v) for v in value.values() if isinstance(v, str))
    return values
