from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.bioinformatics.group_comparison_design import load_group_design_context
from app.bioinformatics.project_analysis_tasks import load_analysis_task_center
from app.bioinformatics.project_recognition import run_project_recognition
from app.bioinformatics.project_standardization import generate_standardized_assets
from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.results.project_results import build_imported_deg_view, load_imported_deg_comparisons
from app.bioinformatics.standardized_asset_selection import (
    STANDARDIZED_ASSET_SELECTION,
    build_asset_selection_context,
    load_standardized_asset_selection,
    save_standardized_asset_selection,
)


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return create_bioinformatics_project("Asset Selection Project", tmp_path).project_root


def _write_integrated_csv(path: Path, *, comparison: str, groups: tuple[str, str] = ("A", "B")) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    left, right = groups
    path.write_text(
        "\n".join(
            [
                f"gene_id,{left}1_count,{left}2_count,{right}1_count,{right}2_count,"
                f"{left}1_fpkm,{left}2_fpkm,{right}1_fpkm,{right}2_fpkm,"
                f"{comparison}_log2FoldChange,{comparison}_pvalue,{comparison}_padj,"
                "gene_name,gene_start,gene_end,gene_biotype,gene_description",
                "ENSMUSG00000026193,10,11,20,21,1.1,1.2,2.1,2.2,1.5,0.01,0.04,"
                "Sox17,4490931,4497354,protein_coding,SRY-box transcription factor 17",
                "ENSMUSG00000064351,30,31,18,17,3.1,3.2,1.8,1.7,-1.6,0.02,0.03,"
                "mt-Nd1,2751,3707,protein_coding,mitochondrially encoded NADH",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _prepare_assets(project_root: Path, *, multiple: bool = False) -> list[dict[str, object]]:
    _write_integrated_csv(project_root / "raw_data" / "local_import" / "integrated_a.csv", comparison="PFFvsPBS", groups=("A", "B"))
    if multiple:
        _write_integrated_csv(project_root / "raw_data" / "local_import" / "integrated_b.csv", comparison="MMP3vsPBS", groups=("X", "Y"))
    run_project_recognition(project_root)
    standardization = generate_standardized_assets(project_root)
    return [asset for asset in standardization["registry"]["assets"] if isinstance(asset, dict)]  # type: ignore[index]


def test_single_candidate_assets_are_recommended_defaults(project_root: Path) -> None:
    _prepare_assets(project_root)

    context = build_asset_selection_context(project_root)
    states = {group["asset_type"]: group for group in context["groups"]}  # type: ignore[index]

    for asset_type in ("count_matrix", "normalized_expression_matrix", "deg_result_table", "gene_annotation"):
        assert states[asset_type]["selection_state"] == "recommended_default"
        assert states[asset_type]["candidate_count"] == 1
        assert states[asset_type]["selected_asset_id"]

    center = load_analysis_task_center(project_root)
    capabilities = {item["task_id"]: item for item in center["capabilities"]}  # type: ignore[index]
    assert capabilities["deg_result_browse"]["status"] == "available"
    assert capabilities["differential_expression_recompute"]["status"] == "ready_with_group_confirmation"


def test_multiple_same_type_assets_require_selection(project_root: Path) -> None:
    _prepare_assets(project_root, multiple=True)

    context = build_asset_selection_context(project_root)
    states = {group["asset_type"]: group for group in context["groups"]}  # type: ignore[index]

    assert states["count_matrix"]["selection_state"] == "needs_selection"
    assert states["count_matrix"]["candidate_count"] == 2
    assert states["deg_result_table"]["selection_state"] == "needs_selection"

    center = load_analysis_task_center(project_root)
    capabilities = {item["task_id"]: item for item in center["capabilities"]}  # type: ignore[index]
    assert capabilities["differential_expression_recompute"]["status"] == "needs_asset_selection"
    assert capabilities["deg_result_browse"]["status"] == "needs_asset_selection"
    tasks = {item["task_type"]: item for item in center["tasks"]}  # type: ignore[index]
    assert tasks["deg_result_browse"]["can_run"] is False
    assert "default_standardized_asset_selection" in tasks["deg_result_browse"]["missing_inputs"]


def test_save_selection_manifest_and_use_selected_count_asset(project_root: Path) -> None:
    assets = _prepare_assets(project_root, multiple=True)
    count_assets = [asset for asset in assets if asset.get("asset_type") == "count_matrix"]

    payload = save_standardized_asset_selection(project_root, {"count_matrix": str(count_assets[1]["asset_id"])})
    context = build_asset_selection_context(project_root)
    group_context = load_group_design_context(project_root)

    assert payload["schema_version"] == "bioinformatics.standardized_asset_selection.v1"
    assert load_standardized_asset_selection(project_root) is not None
    assert (project_root / STANDARDIZED_ASSET_SELECTION).exists()
    count_group = next(group for group in context["groups"] if group["asset_type"] == "count_matrix")  # type: ignore[index]
    assert count_group["selection_state"] == "confirmed"
    assert count_group["selected_asset_id"] == count_assets[1]["asset_id"]
    inferred_groups = {item["inferred_group_id"] for item in group_context["sample_groups"]}  # type: ignore[index]
    assert inferred_groups == {"X", "Y"}


def test_selected_deg_asset_drives_imported_result_browser(project_root: Path) -> None:
    assets = _prepare_assets(project_root, multiple=True)
    deg_assets = [asset for asset in assets if asset.get("asset_type") == "deg_result_table"]

    assert load_imported_deg_comparisons(project_root) == []
    blocked_view = build_imported_deg_view(project_root)
    assert any("选择默认资产" in warning for warning in blocked_view["warnings"])  # type: ignore[index]

    save_standardized_asset_selection(project_root, {"deg_result_table": str(deg_assets[1]["asset_id"])})
    comparisons = load_imported_deg_comparisons(project_root)
    view = build_imported_deg_view(project_root)

    assert {comparison["comparison_name"] for comparison in comparisons} == {"MMP3vsPBS"}
    assert view["source_asset_id"] == deg_assets[1]["asset_id"]
    assert view["comparison_name"] == "MMP3vsPBS"


def test_invalid_saved_selection_is_reported(project_root: Path) -> None:
    _prepare_assets(project_root)
    path = project_root / STANDARDIZED_ASSET_SELECTION
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "bioinformatics.standardized_asset_selection.v1",
                "asset_selections": [{"asset_type": "count_matrix", "selected_asset_id": "missing_asset"}],
                "warnings": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    context = build_asset_selection_context(project_root)
    count_group = next(group for group in context["groups"] if group["asset_type"] == "count_matrix")  # type: ignore[index]

    assert count_group["selection_state"] == "invalid"
    assert any("默认资产失效" in warning for warning in context["warnings"])  # type: ignore[index]
