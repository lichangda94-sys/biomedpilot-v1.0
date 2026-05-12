from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.bioinformatics.group_comparison_design import (
    group_comparison_design_path,
    has_confirmed_group_comparison_design,
    load_group_design_context,
    save_group_comparison_design,
    validate_group_comparison_design,
)
from app.bioinformatics.project_analysis_tasks import load_analysis_task_center
from app.bioinformatics.project_recognition import run_project_recognition
from app.bioinformatics.project_standardization import generate_standardized_assets
from app.bioinformatics.project_workspace import create_bioinformatics_project


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return create_bioinformatics_project("Group Design Project", tmp_path).project_root


def _write_integrated_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "gene_id,A1_count,A2_count,B1_count,B2_count,A1_fpkm,A2_fpkm,B1_fpkm,B2_fpkm,"
        "PFFvsPBS_log2FoldChange,PFFvsPBS_pvalue,PFFvsPBS_padj,gene_name,gene_biotype,gene_description\n"
        "ENSMUSG00000026193,10,12,30,32,1.1,1.2,3.0,3.2,1.5,0.01,0.04,Sox17,protein_coding,SRY-box transcription factor 17\n"
        "ENSMUSG00000064351,20,18,6,5,2.1,2.2,0.6,0.5,-1.7,0.02,0.03,mt-Nd1,protein_coding,mitochondrially encoded NADH\n",
        encoding="utf-8",
    )


def _prepare_integrated_project(project_root: Path) -> None:
    _write_integrated_csv(project_root / "raw_data" / "local_import" / "integrated_rnaseq.csv")
    run_project_recognition(project_root)
    generate_standardized_assets(project_root)


def test_group_design_context_uses_count_matrix_sample_ids(project_root: Path) -> None:
    _prepare_integrated_project(project_root)

    context = load_group_design_context(project_root)
    groups = {str(item["inferred_group_id"]): item for item in context["sample_groups"]}  # type: ignore[index]

    assert context["has_count_matrix"] is True
    assert context["count_fpkm_sample_match"] is True
    assert groups["A"]["sample_ids"] == ["A1", "A2"]
    assert groups["B"]["sample_ids"] == ["B1", "B2"]
    assert "A1_count" in groups["A"]["source_columns"]
    assert not any("log2FoldChange" in column for group in groups.values() for column in group["source_columns"])  # type: ignore[index]
    assert context["imported_deg_references"][0]["comparison_name"] == "PFFvsPBS"  # type: ignore[index]


def test_imported_deg_references_do_not_become_confirmed_design(project_root: Path) -> None:
    _prepare_integrated_project(project_root)

    context = load_group_design_context(project_root)

    assert context["imported_deg_count"] == 1
    assert context["has_confirmed_design"] is False
    assert has_confirmed_group_comparison_design(project_root) is False
    assert not group_comparison_design_path(project_root).exists()


def test_save_group_mapping_writes_manifest_and_updates_task_center(project_root: Path) -> None:
    _prepare_integrated_project(project_root)
    before_current = (project_root / "recognized_data" / "current.json").read_text(encoding="utf-8")
    context = load_group_design_context(project_root)
    groups = []
    for item in context["sample_groups"]:  # type: ignore[index]
        row = dict(item)
        if row["inferred_group_id"] == "A":
            row["user_group_name"] = "PBS"
            row["group_role"] = "control"
        elif row["inferred_group_id"] == "B":
            row["user_group_name"] = "PFF"
            row["group_role"] = "treatment"
        groups.append(row)
    comparisons = [
        {
            "comparison_name": "PFF_vs_PBS",
            "case_group": "PFF",
            "control_group": "PBS",
            "case_inferred_group_id": "B",
            "control_inferred_group_id": "A",
            "status": "confirmed",
            "source": "user_confirmed",
        }
    ]

    payload = save_group_comparison_design(project_root, groups, comparisons)
    center = load_analysis_task_center(project_root)
    capabilities = {str(item["task_id"]): item for item in center["capabilities"]}  # type: ignore[index]

    assert payload["schema_version"] == "bioinformatics_group_comparison_design.v1"
    assert payload["source_recognition_run_id"]
    assert payload["sample_groups"][0]["sample_ids"]  # type: ignore[index]
    assert payload["comparisons"][0]["status"] == "confirmed"  # type: ignore[index]
    assert has_confirmed_group_comparison_design(project_root) is True
    assert capabilities["differential_expression_recompute"]["status"] == "available"
    assert "已确认分组" in capabilities["differential_expression_recompute"]["reason"]
    assert (project_root / "recognized_data" / "current.json").read_text(encoding="utf-8") == before_current


def test_comparison_validation_rejects_empty_or_same_groups() -> None:
    groups = [
        {"inferred_group_id": "A", "user_group_name": "PBS", "group_role": "control", "sample_count": 3},
        {"inferred_group_id": "B", "user_group_name": "PFF", "group_role": "treatment", "sample_count": 3},
    ]

    warnings = validate_group_comparison_design(
        groups,
        [
            {"comparison_name": "", "case_group": "", "control_group": "PBS"},
            {"comparison_name": "PBS_vs_PBS", "case_group": "PBS", "control_group": "PBS"},
        ],
    )

    assert any("不能为空" in warning for warning in warnings)
    assert any("不能相同" in warning for warning in warnings)


def test_mismatched_count_and_fpkm_samples_warns(project_root: Path) -> None:
    registry_path = project_root / "manifests" / "standardized_assets_registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(
            {
                "assets": [
                    {"asset_id": "count_matrix_001", "asset_type": "count_matrix", "sample_columns": ["A1_count", "A2_count"], "inferred_sample_ids": ["A1", "A2"]},
                    {"asset_id": "fpkm_matrix_001", "asset_type": "normalized_expression_matrix", "value_type": "fpkm", "sample_columns": ["A1_fpkm", "B1_fpkm"], "inferred_sample_ids": ["A1", "B1"]},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    context = load_group_design_context(project_root)

    assert context["count_fpkm_sample_match"] is False
    assert any("不完全一致" in warning for warning in context["warnings"])  # type: ignore[operator]


def test_fpkm_only_does_not_make_recompute_deg_ready(project_root: Path) -> None:
    registry_path = project_root / "manifests" / "standardized_assets_registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(
            {
                "assets": [
                    {"asset_id": "fpkm_matrix_001", "asset_type": "normalized_expression_matrix", "value_type": "fpkm", "sample_columns": ["A1_fpkm", "B1_fpkm"], "inferred_sample_ids": ["A1", "B1"]}
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    context = load_group_design_context(project_root)
    center = load_analysis_task_center(project_root)
    task_ids = {str(item["task_id"]): item for item in center["capabilities"]}  # type: ignore[index]

    assert context["has_count_matrix"] is False
    assert any("不建议作为 DESeq2/edgeR" in warning for warning in context["warnings"])  # type: ignore[operator]
    assert "differential_expression_recompute" not in task_ids
