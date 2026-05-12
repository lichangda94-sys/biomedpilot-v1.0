from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.analysis_task_runs import create_deg_task_run
from app.bioinformatics.deg_task_plan import save_deg_task_plan
from app.bioinformatics.group_comparison_design import load_group_design_context, save_group_comparison_design
from app.bioinformatics.project_recognition import run_project_recognition
from app.bioinformatics.project_standardization import generate_standardized_assets
from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.reports.project_report_builder import generate_project_report
from app.bioinformatics.results.project_results import load_result_index


def _write_integrated_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "gene_id,A1_count,A2_count,B1_count,B2_count,A1_fpkm,A2_fpkm,B1_fpkm,B2_fpkm,"
                "PFFvsPBS_log2FoldChange,PFFvsPBS_pvalue,PFFvsPBS_padj,gene_name,gene_biotype,gene_description",
                "ENSMUSG00000026193,10,11,20,21,1.1,1.2,2.1,2.2,1.5,0.01,0.04,Sox17,protein_coding,SRY-box transcription factor 17",
                "ENSMUSG00000064351,30,31,18,17,3.1,3.2,1.8,1.7,-1.6,0.02,0.03,mt-Nd1,protein_coding,mitochondrially encoded NADH",
            ]
        ),
        encoding="utf-8",
    )


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


def test_result_index_registers_imported_deg_and_dry_run_task_record(tmp_path: Path) -> None:
    project_root = create_bioinformatics_project("Result Manifest Project", tmp_path).project_root
    _write_integrated_csv(project_root / "raw_data" / "local_import" / "integrated.csv")
    run_project_recognition(project_root)
    generate_standardized_assets(project_root)
    _save_confirmed_design(project_root)
    save_deg_task_plan(project_root)
    run = create_deg_task_run(project_root)

    result_index = load_result_index(project_root)
    items = {str(item["item_type"]): item for item in result_index["items"]}  # type: ignore[index]
    index_path = project_root / "results" / "summaries" / "result_index.json"
    saved_index = json.loads(index_path.read_text(encoding="utf-8"))

    assert saved_index["schema_version"] == "bioinformatics_result_index.v1"
    assert "items" in saved_index
    assert items["imported_deg_result"]["source"] == "imported_table"
    assert items["imported_deg_result"]["description"] == "导入表格中的已有差异分析结果"
    assert items["analysis_task_run"]["item_id"] == run["run_id"]
    assert items["analysis_task_run"]["status"] == "skipped_dry_run"
    assert items["analysis_task_run"]["source_run_path"].endswith("task_run.json")
    assert items["analysis_task_run"]["item_type"] != "completed_result"
    assert not any("volcano" in str(item.get("path") or "").lower() for item in result_index["items"])  # type: ignore[index]


def test_project_report_manifest_links_upstream_bioinformatics_manifests(tmp_path: Path) -> None:
    project_root = create_bioinformatics_project("Report Manifest Project", tmp_path).project_root
    _write_integrated_csv(project_root / "raw_data" / "local_import" / "integrated.csv")
    run_project_recognition(project_root)
    generate_standardized_assets(project_root)
    _save_confirmed_design(project_root)
    save_deg_task_plan(project_root)
    create_deg_task_run(project_root)

    payload = generate_project_report(project_root)
    manifest = payload["manifest"]  # type: ignore[index]
    sections = {str(section["section_id"]): section for section in manifest["sections"]}  # type: ignore[index]
    result_items = {str(item["item_type"]): item for item in manifest["result_items"]}  # type: ignore[index]

    assert manifest["schema_version"] == "bioinformatics_report_manifest.v1"
    assert sections["data_recognition"]["source"] == "recognized_data/current.json"
    assert sections["standardized_assets"]["source"] == "manifests/standardized_assets_registry.json"
    assert sections["asset_selection"]["source"] == "manifests/standardized_asset_selection.json"
    assert sections["group_design"]["status"] == "available"
    assert sections["imported_deg_results"]["status"] == "available"
    assert sections["analysis_task_runs"]["status"] == "available"
    assert result_items["imported_deg_result"]["description"] == "导入表格中的已有差异分析结果"
    assert result_items["analysis_task_run"]["status"] == "skipped_dry_run"
    assert result_items["analysis_task_run"]["item_type"] != "completed_result"
