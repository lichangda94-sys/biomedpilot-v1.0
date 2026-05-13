from __future__ import annotations

from pathlib import Path

from app.bioinformatics.deg_task_plan import build_deg_preflight
from app.bioinformatics.imported_deg_results import list_imported_deg_results, mark_imported_deg_report_candidates
from app.bioinformatics.project_recognition import run_project_recognition
from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.results.project_results import load_result_index


def test_imported_deg_result_browser_profiles_columns_and_counts(tmp_path: Path) -> None:
    project_root = create_bioinformatics_project("Imported DEG Project", tmp_path).project_root
    source = project_root / "raw_data" / "local_import" / "deg_results.csv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "gene,logFC,P.Value,adj.P.Val\n"
        "TP53,1.2,0.01,0.02\n"
        "EGFR,-1.4,0.02,0.03\n"
        "ACTB,0.2,0.5,0.8\n",
        encoding="utf-8",
    )
    run_project_recognition(project_root)

    results = list_imported_deg_results(project_root)

    assert len(results) == 1
    result = results[0]
    assert result.status == "ready"
    assert result.source_label == "用户导入 / 外部分析结果"
    assert result.column_mapping["gene"] == "gene"
    assert result.column_mapping["logfc"] == "logFC"
    assert result.column_mapping["fdr"] == "adj.P.Val"
    assert result.regulation_counts["status"] == "computed"
    assert result.regulation_counts["up"] == 1
    assert result.regulation_counts["down"] == 1
    assert result.regulation_counts["not_significant"] == 1
    assert "not_biomedpilot_computed" in result.to_dict()["semantic_boundary"]


def test_imported_deg_can_be_report_candidate_but_not_preflight_input(tmp_path: Path) -> None:
    project_root = create_bioinformatics_project("Imported DEG Boundary", tmp_path).project_root
    source = project_root / "raw_data" / "local_import" / "deg_results.csv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene,logFC,P.Value,adj.P.Val\nTP53,1.2,0.01,0.02\n", encoding="utf-8")
    run_project_recognition(project_root)

    entries = mark_imported_deg_report_candidates(project_root)
    preflight = build_deg_preflight(project_root)

    assert entries
    assert entries[0]["result_semantics"] == "imported result"
    assert entries[0]["report_candidate"] is True
    assert "重新计算" in entries[0]["warning"]
    assert preflight.status == "blocked"
    assert preflight.manifest["input_summary"]["imported_deg_detected"] is True  # type: ignore[index]
    assert any("导入差异结果不能作为重新计算 DEG" in item for item in preflight.manifest["warnings"])  # type: ignore[index]
    result_index = load_result_index(project_root)
    assert result_index["entries"][0]["result_semantics"] == "imported result"  # type: ignore[index]
    assert not (project_root / "results" / "tables").exists()
    assert not (project_root / "results" / "figures").exists()
