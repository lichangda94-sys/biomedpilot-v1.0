from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.deg_task_plan import build_deg_preflight
from app.bioinformatics.imported_deg_results import mark_imported_deg_report_candidates
from app.bioinformatics.project_recognition import run_project_recognition
from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.reports.project_report_builder import generate_project_report
from app.bioinformatics.results.project_results import write_result_index


def test_project_report_builder_enforces_imported_deg_semantics(tmp_path: Path) -> None:
    project_root = create_bioinformatics_project("Draft Report Semantics", tmp_path).project_root
    source = project_root / "raw_data" / "local_import" / "deg_results.csv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "gene,logFC,P.Value,adj.P.Val\n"
        "TP53,1.3,0.01,0.02\n"
        "EGFR,-1.5,0.02,0.03\n",
        encoding="utf-8",
    )
    run_project_recognition(project_root)
    entries = mark_imported_deg_report_candidates(project_root)
    preflight = build_deg_preflight(project_root)

    payload = generate_project_report(project_root)
    markdown = Path(str(payload["markdown_path"])).read_text(encoding="utf-8")
    manifest = payload["manifest"]

    assert preflight.status == "blocked"
    assert "输入检查已完成 / 尚未运行真实分析" in markdown
    assert "用户导入的外部分析结果显示" in markdown
    assert "测试级分析输出，不应用于正式科研结论" in markdown
    assert "任务已配置但尚未执行" in markdown
    assert "本软件计算发现" not in markdown
    assert manifest["semantic_policy"]["imported result"] == "用户导入的外部分析结果显示"  # type: ignore[index]
    assert entries[0]["result_id"] in manifest["included_result_ids"]  # type: ignore[index]
    assert manifest["section_statuses"]["imported_deg_results"] == "available"  # type: ignore[index]
    assert (project_root / "reports" / "project_report_manifest.json").is_file()
    saved_manifest = json.loads((project_root / "reports" / "project_report_manifest.json").read_text(encoding="utf-8"))
    assert saved_manifest["schema_version"] == "biomedpilot.project_report_manifest.v1"


def test_project_report_builder_handles_missing_empty_and_old_result_index(tmp_path: Path) -> None:
    for label, index_payload in (
        ("missing-index", None),
        ("empty-index", []),
        (
            "old-index",
            [
                {
                    "name": "Old Imported DEG",
                    "analysis_type": "differential_expression",
                    "file_path": str(tmp_path / "old_missing.csv"),
                    "status": "imported",
                    "result_semantics": "imported result",
                }
            ],
        ),
    ):
        project_root = create_bioinformatics_project(f"Report {label}", tmp_path).project_root
        if index_payload is not None:
            write_result_index(project_root, index_payload)

        payload = generate_project_report(project_root)
        markdown = Path(str(payload["markdown_path"])).read_text(encoding="utf-8")
        manifest = payload["manifest"]

        assert "BioMedPilot 生信项目报告草稿" in markdown
        assert "本软件计算发现" not in markdown
        assert "BioMedPilot 计算得到" not in markdown
        assert str(tmp_path) not in markdown
        assert manifest["semantic_policy"]["real computed result"] == "当前未开放；本阶段不生成真实计算结论"  # type: ignore[index]


def test_project_report_builder_sanitizes_missing_result_paths(tmp_path: Path) -> None:
    project_root = create_bioinformatics_project("Report Missing Result Path", tmp_path).project_root
    missing_path = project_root / "results" / "tables" / "missing.csv"
    write_result_index(
        project_root,
        [
            {
                "result_name": "Missing imported result",
                "analysis_type": "differential_expression",
                "path": str(missing_path),
                "status": "imported",
                "result_semantics": "imported result",
            }
        ],
    )

    payload = generate_project_report(project_root)
    markdown = Path(str(payload["markdown_path"])).read_text(encoding="utf-8")

    assert str(missing_path) not in markdown
    assert "结果文件缺失，请在开发者诊断中查看路径" in markdown
