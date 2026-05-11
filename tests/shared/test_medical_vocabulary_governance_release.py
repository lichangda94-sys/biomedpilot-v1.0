from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from scripts.audit_medical_vocabulary_coverage import build_coverage_audit_report


ROOT = Path(__file__).resolve().parents[2]
MEDICAL_TERMS = ROOT / "data" / "medical_terms"
SOURCE_METADATA = MEDICAL_TERMS / "source_metadata.json"
MINI_INDEX = MEDICAL_TERMS / "mini_medical_terms_index.json"
ZH_OVERRIDES = MEDICAL_TERMS / "zh_term_overrides.json"


REQUIRED_SHORT_TOKEN_RISK_TERMS = {
    "PTC",
    "SCC",
    "RCC",
    "CRC",
    "HCC",
    "GBM",
    "LGG",
    "RA",
    "SLE",
    "IBD",
    "MS",
    "CRP",
    "IL-6",
    "TNF",
    "IFN",
    "ANA",
    "RF",
    "ANCA",
    "T3",
    "T4",
    "TSH",
    "PTH",
    "BMI",
    "HDL",
    "LDL",
    "OS",
    "HR",
    "OR",
    "RR",
    "CI",
    "MD",
    "SMD",
    "PR",
    "SD",
    "PD",
    "WGS",
    "WES",
    "RNA",
    "DNA",
    "CNV",
    "SNP",
}


def _mini() -> list[dict[str, object]]:
    return json.loads(MINI_INDEX.read_text(encoding="utf-8"))


def _zh_overrides() -> list[dict[str, object]]:
    return json.loads(ZH_OVERRIDES.read_text(encoding="utf-8"))


def test_release_summary_is_present_and_matches_runtime_counts() -> None:
    report = build_coverage_audit_report()
    release = report["release_summary"]

    assert release["release_name"] == "shared_medical_vocabulary_core_v1"
    assert release["version"] == "core_v1.0.0"
    assert release["runtime_vocabulary_total_concepts"] == len(_mini())
    assert release["zh_overrides_total_mappings"] == len(_zh_overrides())
    assert release["coverage_summary"]["total_checklist_terms"] == report["overall"]["total_checklist_items"]
    assert release["coverage_summary"]["total_covered"] == report["overall"]["covered"]
    assert release["coverage_summary"]["overall_coverage"] == 1.0
    assert release["quality_gate_overall_status"] == "pass"
    assert len(release["included_core_packages"]) == 7
    assert all(item["quality_gate_status"] == "pass" for item in release["included_core_packages"])


def test_source_metadata_records_governance_release() -> None:
    metadata = json.loads(SOURCE_METADATA.read_text(encoding="utf-8"))
    release = metadata["shared_vocabulary_release"]

    assert release["release_name"] == "shared_medical_vocabulary_core_v1"
    assert release["version"] == "core_v1.0.0"
    assert release["total_runtime_concepts"] == len(_mini())
    assert release["total_zh_overrides"] == len(_zh_overrides())
    assert release["quality_gate_status"] == "pass"
    assert release["governance_conflict_audit_status"] == "pass"
    assert REQUIRED_SHORT_TOKEN_RISK_TERMS <= set(release["short_token_risk_terms"])


def test_release_short_token_risk_terms_are_complete() -> None:
    report = build_coverage_audit_report()
    release_terms = set(report["release_summary"]["short_token_risk_terms"])

    assert REQUIRED_SHORT_TOKEN_RISK_TERMS <= release_terms


def test_release_governance_conflict_audit_passes() -> None:
    report = build_coverage_audit_report()
    conflict_audit = report["release_summary"]["governance_conflict_audit"]

    assert conflict_audit["status"] == "pass"
    assert conflict_audit["duplicate_concept_ids"] == []
    assert all(item["status"] == "pass" for item in conflict_audit["watched_terms"])


def test_cross_core_watched_terms_have_single_primary_concept() -> None:
    mini = _mini()
    concept_ids = [str(item.get("concept_id") or "") for item in mini]
    by_id = {str(item["concept_id"]): item for item in mini}

    assert not [concept_id for concept_id, count in Counter(concept_ids).items() if count > 1]
    assert "mini:adipose_tissue" not in by_id
    assert "mini:blood_tissue" not in by_id
    assert "mini:heart_tissue" not in by_id
    assert by_id["mini:anatomy_adipose_tissue"]["deprecated_alias_concept_ids"] == ["mini:adipose_tissue"]
    assert by_id["mini:anatomy_whole_blood"]["deprecated_alias_concept_ids"] == ["mini:blood_tissue"]
    assert by_id["mini:anatomy_heart"]["deprecated_alias_concept_ids"] == ["mini:heart_tissue"]
    assert by_id["mini:cardiovascular_c_reactive_protein"]["concept_type"] == "biomarker"
    assert by_id["mini:hashimoto_thyroiditis"]["category"] == "endocrine_metabolic"
    assert by_id["mini:graves_disease"]["category"] == "endocrine_metabolic"
    assert by_id["mini:dyslipidemia"]["category"] == "endocrine_metabolic"
    assert "dyslipidemia" not in [term.lower() for term in by_id["mini:hyperlipidemia"].get("synonyms_en", [])]
