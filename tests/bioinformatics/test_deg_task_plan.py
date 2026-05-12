from __future__ import annotations

from pathlib import Path

import pytest

from app.bioinformatics.deg_task_plan import DEG_TASK_PLAN, build_deg_task_plan_context, load_deg_task_plan, save_deg_task_plan
from app.bioinformatics.group_comparison_design import load_group_design_context, save_group_comparison_design
from app.bioinformatics.project_analysis_tasks import load_analysis_task_center
from app.bioinformatics.project_recognition import run_project_recognition
from app.bioinformatics.project_standardization import generate_standardized_assets
from app.bioinformatics.project_workspace import create_bioinformatics_project


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return create_bioinformatics_project("DEG Task Plan Project", tmp_path).project_root


def _write_integrated_csv(path: Path, *, comparison: str, groups: tuple[str, str] = ("A", "B")) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    left, right = groups
    path.write_text(
        "\n".join(
            [
                f"gene_id,{left}1_count,{left}2_count,{right}1_count,{right}2_count,"
                f"{left}1_fpkm,{left}2_fpkm,{right}1_fpkm,{right}2_fpkm,"
                f"{comparison}_log2FoldChange,{comparison}_pvalue,{comparison}_padj,"
                "gene_name,gene_biotype,gene_description",
                "ENSMUSG00000026193,10,11,20,21,1.1,1.2,2.1,2.2,1.5,0.01,0.04,Sox17,protein_coding,SRY-box transcription factor 17",
                "ENSMUSG00000064351,30,31,18,17,3.1,3.2,1.8,1.7,-1.6,0.02,0.03,mt-Nd1,protein_coding,mitochondrially encoded NADH",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _prepare_project(project_root: Path, *, multiple_count_assets: bool = False) -> None:
    _write_integrated_csv(project_root / "raw_data" / "local_import" / "integrated_a.csv", comparison="PFFvsPBS", groups=("A", "B"))
    if multiple_count_assets:
        _write_integrated_csv(project_root / "raw_data" / "local_import" / "integrated_b.csv", comparison="MMP3vsPBS", groups=("X", "Y"))
    run_project_recognition(project_root)
    generate_standardized_assets(project_root)


def _save_confirmed_design(project_root: Path) -> None:
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
    save_group_comparison_design(
        project_root,
        groups,
        [
            {
                "comparison_name": "PFF_vs_PBS",
                "case_group": "PFF",
                "control_group": "PBS",
                "case_inferred_group_id": "B",
                "control_inferred_group_id": "A",
                "status": "confirmed",
                "source": "user_confirmed",
            }
        ],
    )


def test_deg_task_plan_requires_default_count_asset(project_root: Path) -> None:
    _prepare_project(project_root, multiple_count_assets=True)

    context = build_deg_task_plan_context(project_root)

    assert "default_count_matrix" in context["missing"]
    with pytest.raises(ValueError, match="默认 count matrix"):
        save_deg_task_plan(project_root)


def test_deg_task_plan_requires_confirmed_group_design(project_root: Path) -> None:
    _prepare_project(project_root)

    context = build_deg_task_plan_context(project_root)

    assert "confirmed_group_design" in context["missing"]
    with pytest.raises(ValueError, match="confirmed group design"):
        save_deg_task_plan(project_root)


def test_save_deg_task_plan_uses_default_count_and_confirmed_comparisons(project_root: Path) -> None:
    _prepare_project(project_root)
    _save_confirmed_design(project_root)

    payload = save_deg_task_plan(project_root)
    center = load_analysis_task_center(project_root)
    capabilities = {str(item["task_id"]): item for item in center["capabilities"]}  # type: ignore[index]

    assert payload["schema_version"] == "bioinformatics_deg_task_plan.v1"
    assert payload["status"] == "configured_not_run"
    assert payload["source_count_asset_id"] == "count_matrix_001"
    assert payload["source_group_design_path"] == "manifests/group_comparison_design.json"
    assert payload["comparisons"] == [{"comparison_name": "PFF_vs_PBS", "case_group": "PFF", "control_group": "PBS", "status": "selected"}]
    assert payload["method"] == {"name": "DESeq2", "status": "planned_placeholder"}
    assert payload["thresholds"] == {"padj": 0.05, "abs_log2fc": 1.0}
    assert (project_root / DEG_TASK_PLAN).exists()
    assert load_deg_task_plan(project_root) is not None
    assert capabilities["differential_expression_recompute"]["status"] == "configured_not_run"
    assert capabilities["deg_result_browse"]["source_asset_type"] == "deg_result_table"
    assert capabilities["deg_result_browse"]["status"] == "available"
