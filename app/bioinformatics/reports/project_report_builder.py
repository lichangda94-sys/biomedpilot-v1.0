from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.group_comparison_design import GROUP_COMPARISON_DESIGN
from app.bioinformatics.project_analysis_tasks import load_task_records
from app.bioinformatics.project_readiness import load_readiness_artifacts
from app.bioinformatics.project_recognition import CURRENT_RECOGNITION_RUN, load_recognition_report
from app.bioinformatics.project_standardization import STANDARDIZED_REGISTRY, load_standardization_artifacts
from app.bioinformatics.project_workspace_binding import load_latest_acquisition_summary
from app.bioinformatics.results.project_results import load_result_index
from app.bioinformatics.standardized_asset_selection import STANDARDIZED_ASSET_SELECTION
from reporting.bioinformatics_standard_report import generate_standard_report


PROJECT_REPORT_MD = Path("reports") / "project_analysis_report.md"
PROJECT_REPORT_MANIFEST = Path("reports") / "project_report_manifest.json"
PROJECT_REPORT_BUILDER_REPORT = Path("logs") / "reports" / "project_report_builder_report.json"


def generate_project_report(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    acquisition = load_latest_acquisition_summary(root)
    recognition = load_recognition_report(root) or {}
    readiness = load_readiness_artifacts(root).get("readiness_report") or {}
    standardization = load_standardization_artifacts(root).get("analysis_ready_manifest") or {}
    result_index = load_result_index(root)
    task_records = load_task_records(root)
    result_items = [item for item in result_index.get("items", []) or [] if isinstance(item, dict)]
    report_sections = _report_sections(root, result_items)
    warnings: list[str] = []
    if acquisition is None:
        warnings.append("尚未生成数据获取记录。")
    warnings.extend(str(item) for item in recognition.get("warnings", []) or [] if isinstance(recognition, dict))
    warnings.extend(str(item) for item in readiness.get("warnings", []) or [] if isinstance(readiness, dict))
    warnings.extend(str(item) for item in standardization.get("warnings", []) or [] if isinstance(standardization, dict))
    warnings.extend(str(item) for item in result_index.get("warnings", []) or [])

    analysis_result = {
        "title": "BioMedPilot 生信项目报告",
        "report_filename": "project_analysis_report.md",
        "project_summary": {"project_root": str(root), "developer_preview": "Developer Preview / 本地测试版"},
        "dataset_summary": {
            "source_type": acquisition.source_type if acquisition else "未记录",
            "source_label": acquisition.source_label if acquisition else "未记录",
            "strategy": acquisition.strategy if acquisition else "未记录",
        },
        "analysis_workflow": {
            "recognition_files": len(recognition.get("files", []) or []) if isinstance(recognition, dict) else 0,
            "ready_status": readiness.get("overall_status", "尚未生成") if isinstance(readiness, dict) else "尚未生成",
            "standardized_assets": standardization.get("exists", False) if isinstance(standardization, dict) else False,
            "task_records": len(task_records),
            "result_count": len(result_index.get("entries", []) or []),
            "result_item_count": len(result_items),
        },
        "input_files": recognition.get("files", []) if isinstance(recognition, dict) else [],
        "tables": result_index.get("entries", []) or [],
        "reportable_items": result_items,
        "warnings": warnings,
        "requested_output_formats": ["markdown"],
    }
    result = generate_standard_report(analysis_result, output_dir=root)
    markdown_path = root / PROJECT_REPORT_MD
    if result.markdown_path != markdown_path:
        markdown_path.write_text(result.markdown, encoding="utf-8")
    manifest = {
        "schema_version": "bioinformatics_report_manifest.v1",
        "generated_at": _now(),
        "project_root": str(root),
        "markdown_path": str(markdown_path),
        "source_markdown_path": str(result.markdown_path),
        "config_snapshot_path": str(result.config_snapshot_path),
        "sections": report_sections,
        "result_items": result_items,
        "warning_count": len(warnings) + len(result.warnings),
        "warnings": warnings + list(result.warnings),
        "exports": {"PDF": "未正式支持", "DOCX": "testing placeholder", "HTML": "testing placeholder"},
    }
    builder_report = {
        "schema_version": "biomedpilot.project_report_builder_report.v1",
        "generated_at": manifest["generated_at"],
        "status": "generated",
        "warnings": manifest["warnings"],
    }
    _write_json(root / PROJECT_REPORT_MANIFEST, manifest)
    _write_json(root / PROJECT_REPORT_BUILDER_REPORT, builder_report)
    return {"markdown": result.markdown, "markdown_path": str(markdown_path), "manifest": manifest, "builder_report": builder_report}


def load_project_report(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    markdown_path = root / PROJECT_REPORT_MD
    manifest_path = root / PROJECT_REPORT_MANIFEST
    return {
        "markdown": markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else "",
        "manifest": _read_json(manifest_path) if manifest_path.exists() else None,
        "markdown_path": str(markdown_path),
        "manifest_path": str(manifest_path),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _report_sections(root: Path, result_items: list[dict[str, object]]) -> list[dict[str, object]]:
    imported_deg = [item for item in result_items if item.get("item_type") == "imported_deg_result"]
    task_runs = [item for item in result_items if item.get("item_type") == "analysis_task_run"]
    return [
        _section(root, "data_recognition", CURRENT_RECOGNITION_RUN, "recognized_data/current.json"),
        _section(root, "standardized_assets", STANDARDIZED_REGISTRY, "manifests/standardized_assets_registry.json"),
        _section(root, "asset_selection", STANDARDIZED_ASSET_SELECTION, "manifests/standardized_asset_selection.json"),
        _section(root, "group_design", GROUP_COMPARISON_DESIGN, "manifests/group_comparison_design.json"),
        {
            "section_id": "imported_deg_results",
            "status": "available" if imported_deg else "available_if_present",
            "source": "manifests/standardized_asset_selection.json",
            "item_count": len(imported_deg),
            "description": "导入表格中的已有差异分析结果",
        },
        {
            "section_id": "analysis_task_runs",
            "status": "available" if task_runs else "not_available",
            "source": "analysis_runs/",
            "item_count": len(task_runs),
            "description": "分析任务运行记录；dry-run 不代表真实分析完成。",
        },
    ]


def _section(root: Path, section_id: str, source: Path, display_source: str) -> dict[str, object]:
    return {
        "section_id": section_id,
        "status": "available" if (root / source).exists() else "not_available",
        "source": display_source,
    }


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
