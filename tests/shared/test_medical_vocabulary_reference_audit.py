from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_medical_vocabulary_coverage import build_coverage_audit_report


ROOT = Path(__file__).resolve().parents[2]
CHECKLIST_DIR = ROOT / "data" / "medical_terms" / "reference_checklists"
REPORT_PATH = ROOT / "data" / "medical_terms" / "coverage_audit_report.json"
STAGE_REPORT_PATH = ROOT / "docs" / "stage_2_3_medical_vocabulary_reference_audit.md"


def test_reference_checklists_exist() -> None:
    expected = {
        "tcga_projects_checklist.json",
        "common_cancers_checklist.json",
        "common_diseases_checklist.json",
        "gtex_tissues_checklist.json",
        "meta_terms_checklist.json",
        "oncology_core_checklist.json",
        "endocrine_metabolic_core_checklist.json",
        "anatomy_tissue_core_checklist.json",
    }

    assert expected <= {path.name for path in CHECKLIST_DIR.glob("*.json")}
    for path in CHECKLIST_DIR.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["schema_version"] == "medical_vocabulary_reference_checklist.v1"
        assert payload["items"]


def test_audit_script_runs() -> None:
    report = build_coverage_audit_report()

    assert report["schema_version"] == "medical_vocabulary_coverage_audit.v1"
    assert report["overall"]["total_checklist_items"] >= 80
    assert {
        "tcga_projects",
        "common_cancers",
        "common_diseases",
        "gtex_tissues",
        "meta_terms",
        "oncology_core",
        "endocrine_metabolic_core",
        "anatomy_tissue_core",
    } <= set(report["sections"])


def test_tcga_checklist_has_core_projects() -> None:
    payload = json.loads((CHECKLIST_DIR / "tcga_projects_checklist.json").read_text(encoding="utf-8"))
    projects = {project for item in payload["items"] for project in item["expected_tcga_projects"]}

    assert {
        "TCGA-GBM",
        "TCGA-LGG",
        "TCGA-THCA",
        "TCGA-LUAD",
        "TCGA-LUSC",
        "TCGA-BRCA",
        "TCGA-PRAD",
        "TCGA-PAAD",
        "TCGA-SKCM",
    } <= projects


def test_audit_report_contains_coverage_sections() -> None:
    assert REPORT_PATH.exists()
    assert STAGE_REPORT_PATH.exists()

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    markdown = STAGE_REPORT_PATH.read_text(encoding="utf-8")

    assert report["sections"]["tcga_projects"]["covered"] >= 30
    assert report["sections"]["meta_terms"]["coverage_rate"] >= 0.8
    for heading in (
        "Overall Coverage",
        "TCGA Projects Covered/Missing",
        "Common Cancers Covered/Missing",
        "Common Diseases Covered/Missing",
        "GTEx Tissues Exact/Approximate/Missing",
        "Meta Terms Covered/Missing",
        "Oncology Core Covered/Missing",
        "Oncology Core Summary",
        "Endocrine And Metabolic Core Covered/Missing",
        "Endocrine And Metabolic Core Summary",
        "Anatomy Tissue Core Covered/Missing",
        "Anatomy Tissue Core Summary",
        "P0 Gaps",
        "P1 Gaps",
        "P2 Gaps",
        "External Resource Sources And Version Notes",
    ):
        assert heading in markdown


def test_no_cross_context_pollution_in_audit() -> None:
    report = build_coverage_audit_report()
    meta_details = report["sections"]["meta_terms"]["details"]
    tcga_details = report["sections"]["tcga_projects"]["details"]

    assert all("matched_tcga_projects" not in item for item in meta_details)
    assert all("matched_gtex_tissues" not in item for item in meta_details)
    assert all(item["expected_tcga_projects"] for item in tcga_details)
    assert report["prioritized_gaps"]["P0"] == []


def test_stage_2_5_partial_and_approximate_gaps_are_closed() -> None:
    report = build_coverage_audit_report()
    common_diseases = {item["id"]: item for item in report["sections"]["common_diseases"]["details"]}
    gtex_tissues = {item["id"]: item for item in report["sections"]["gtex_tissues"]["details"]}

    assert common_diseases["cardiovascular_diseases"]["status"] == "covered"
    assert common_diseases["neurodegenerative_disease"]["status"] == "covered"
    assert common_diseases["autoimmune_disease"]["status"] == "covered"
    assert gtex_tissues["Kidney"]["status"] == "covered"
    assert gtex_tissues["Kidney"]["mapping_status"] == "exact"
    assert gtex_tissues["Bladder"]["status"] == "covered"
    assert gtex_tissues["Bladder"]["mapping_status"] == "exact"
    assert report["prioritized_gaps"] == {"P0": [], "P1": [], "P2": []}


def test_stage_v7_quality_gates_pass() -> None:
    report = build_coverage_audit_report()
    gates = {gate["gate_id"]: gate for gate in report["quality_gates"]["gates"]}

    assert report["quality_gates"]["status"] == "pass"
    assert gates["core_cancers_coverage"]["observed"] >= 0.95
    assert gates["tcga_project_mapping"]["observed"] >= 0.90
    assert gates["gtex_tissue_mapping"]["observed"] >= 0.95
    assert gates["meta_retrieval_terms"]["observed"] >= 0.90
    assert gates["oncology_core_coverage"]["observed"] >= 0.95
    assert gates["oncology_core_missing_tcga_projects"]["observed"] == 0
    assert gates["endocrine_metabolic_core_coverage"]["observed"] >= 0.95
    assert gates["endocrine_metabolic_missing_terms"]["observed"] == 0
    assert gates["anatomy_tissue_core_coverage"]["observed"] >= 0.95
    assert gates["anatomy_tissue_missing_gtex_tissues"]["observed"] == 0
    assert gates["anatomy_tissue_missing_tcga_primary_sites"]["observed"] == 0
    assert gates["missing_items"]["observed"] == 0
    assert gates["p0_gaps"]["observed"] == 0
    assert gates["audit_cross_context_pollution"]["observed"] == 0
