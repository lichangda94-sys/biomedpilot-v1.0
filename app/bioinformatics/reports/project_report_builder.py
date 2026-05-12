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
PROJECT_REPORT_DRAFT_MD = Path("reports") / "project_report_draft.md"
PROJECT_REPORT_MANIFEST = Path("reports") / "project_report_manifest.json"
PROJECT_REPORT_BUILDER_REPORT = Path("logs") / "reports" / "project_report_builder_report.json"


def generate_project_report(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    acquisition = load_latest_acquisition_summary(root)
    recognition = load_recognition_report(root) or {}
    readiness = load_readiness_artifacts(root).get("readiness_report") or {}
    standardization_artifacts = load_standardization_artifacts(root)
    standardization = standardization_artifacts.get("analysis_ready_manifest") or {}
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
    draft_sections = _draft_sections(root, acquisition, recognition, standardization_artifacts, result_items, report_sections, task_records, warnings)
    draft_markdown = _format_project_report_draft(draft_sections)

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
        "differential_expression_results": _draft_differential_expression_section(result_items),
        "sample_annotation_and_grouping": _draft_group_design_section(root),
        "parameter_summary": _draft_parameter_section(result_items),
        "warnings": warnings,
        "requested_output_formats": ["markdown"],
    }
    result = generate_standard_report(analysis_result, output_dir=root)
    markdown_path = root / PROJECT_REPORT_MD
    draft_path = root / PROJECT_REPORT_DRAFT_MD
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(draft_markdown, encoding="utf-8")
    markdown_path.write_text(draft_markdown, encoding="utf-8")
    manifest = {
        "schema_version": "bioinformatics_report_manifest.v1",
        "generated_at": _now(),
        "project_root": str(root),
        "markdown_path": str(markdown_path),
        "draft_path": str(draft_path),
        "source_markdown_path": str(result.markdown_path),
        "config_snapshot_path": str(result.config_snapshot_path),
        "sections": report_sections,
        "draft_sections": [{"section_id": section["section_id"], "title": section["title"], "status": section["status"]} for section in draft_sections],
        "result_items": result_items,
        "warning_count": len(warnings) + len(result.warnings),
        "warnings": warnings + list(result.warnings),
        "exports": {"PDF": "未正式支持", "DOCX": "testing placeholder", "HTML": "testing placeholder"},
    }
    builder_report = {
        "schema_version": "biomedpilot.project_report_builder_report.v1",
        "generated_at": manifest["generated_at"],
        "status": "generated",
        "draft_status": "generated",
        "warnings": manifest["warnings"],
    }
    _write_json(root / PROJECT_REPORT_MANIFEST, manifest)
    _write_json(root / PROJECT_REPORT_BUILDER_REPORT, builder_report)
    return {"markdown": draft_markdown, "markdown_path": str(markdown_path), "draft_path": str(draft_path), "manifest": manifest, "builder_report": builder_report}


def load_project_report(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    markdown_path = root / PROJECT_REPORT_MD
    manifest_path = root / PROJECT_REPORT_MANIFEST
    return {
        "markdown": markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else "",
        "manifest": _read_json(manifest_path) if manifest_path.exists() else None,
        "markdown_path": str(markdown_path),
        "draft_path": str(root / PROJECT_REPORT_DRAFT_MD),
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


def _draft_sections(
    root: Path,
    acquisition: object,
    recognition: dict[str, object],
    standardization_artifacts: dict[str, object],
    result_items: list[dict[str, object]],
    report_sections: list[dict[str, object]],
    task_records: list[dict[str, object]],
    warnings: list[str],
) -> list[dict[str, object]]:
    registry = standardization_artifacts.get("registry") if isinstance(standardization_artifacts.get("registry"), dict) else {}
    assets = [item for item in registry.get("assets", []) or registry.get("standardized_assets", []) or [] if isinstance(item, dict)]
    imported = [item for item in result_items if item.get("item_type") == "imported_deg_result"]
    task_runs = [item for item in result_items if item.get("item_type") == "analysis_task_run"]
    completed = [item for item in result_items if item.get("item_type") == "completed_result"]
    return [
        {
            "section_id": "project_overview",
            "title": "项目概览",
            "status": "available",
            "body": _project_overview_lines(root, acquisition, recognition, assets, imported, task_runs, completed),
        },
        {
            "section_id": "data_recognition",
            "title": "数据识别摘要",
            "status": _status_for_source(report_sections, "data_recognition"),
            "body": _recognition_lines(recognition),
        },
        {
            "section_id": "standardized_assets",
            "title": "标准化资产与默认选择",
            "status": _status_for_source(report_sections, "standardized_assets"),
            "body": _standardized_asset_lines(assets),
        },
        {
            "section_id": "group_design",
            "title": "分组与比较设计",
            "status": _status_for_source(report_sections, "group_design"),
            "body": _group_design_lines(root),
        },
        {
            "section_id": "imported_deg_results",
            "title": "导入 DEG 结果",
            "status": "available" if imported else "not_available",
            "body": _imported_result_lines(imported),
        },
        {
            "section_id": "analysis_task_runs",
            "title": "分析任务记录",
            "status": "available" if task_runs or task_records else "not_available",
            "body": _task_run_lines(task_runs, task_records),
        },
        {
            "section_id": "completed_results",
            "title": "已完成分析结果",
            "status": "available" if completed else "not_available",
            "body": _completed_result_lines(completed),
        },
        {
            "section_id": "warnings_and_limitations",
            "title": "限制与待确认事项",
            "status": "available",
            "body": _warning_lines(warnings, task_runs),
        },
    ]


def _format_project_report_draft(sections: list[dict[str, object]]) -> str:
    lines = [
        "# BioMedPilot 生信项目报告草稿",
        "",
        "> 自动组装草稿。本文只汇总已登记的数据识别、标准化资产、导入结果和任务记录；不会生成或伪造差异基因表、火山图或富集结果。",
        "",
    ]
    for section in sections:
        lines.extend([f"## {section['title']}", "", f"状态：{section['status']}", ""])
        body = [str(item) for item in section.get("body", []) or [] if str(item)]
        lines.extend(body or ["- 暂无可写入内容。"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _project_overview_lines(
    root: Path,
    acquisition: object,
    recognition: dict[str, object],
    assets: list[dict[str, object]],
    imported: list[dict[str, object]],
    task_runs: list[dict[str, object]],
    completed: list[dict[str, object]],
) -> list[str]:
    return [
        f"- 项目目录：{root}",
        f"- 数据来源：{getattr(acquisition, 'source_label', '未记录') if acquisition is not None else '未记录'}",
        f"- 识别文件数：{len(recognition.get('files', []) or []) if isinstance(recognition, dict) else 0}",
        f"- 标准化资产数：{len(assets)}",
        f"- 导入 DEG 结果：{len(imported)} 项",
        f"- 分析任务记录：{len(task_runs)} 项",
        f"- 已完成分析结果：{len(completed)} 项",
    ]


def _recognition_lines(recognition: dict[str, object]) -> list[str]:
    files = [item for item in recognition.get("files", []) or [] if isinstance(item, dict)] if isinstance(recognition, dict) else []
    if not files:
        return ["- 尚未检测到当前 recognition run。"]
    lines = []
    for item in files[:8]:
        label = item.get("semantic_type_zh") or item.get("recognized_type_zh") or item.get("recognized_type") or "未知文件"
        species = item.get("species") or "物种未检测"
        lines.append(f"- {item.get('file_name', '未命名文件')}：{label}；物种：{species}")
    if len(files) > 8:
        lines.append(f"- 另有 {len(files) - 8} 个文件。")
    return lines


def _standardized_asset_lines(assets: list[dict[str, object]]) -> list[str]:
    if not assets:
        return ["- 尚未生成标准化资产索引。"]
    lines = []
    for asset in assets[:12]:
        uses = ", ".join(str(item) for item in asset.get("recommended_for", []) or []) or "用途待确认"
        restriction = "；限制：当前为资产注册和轻量校验，非正式 normalization 输出"
        lines.append(f"- {asset.get('asset_id', 'asset')}：{asset.get('asset_type', 'unknown')}；样本数：{asset.get('sample_count', '未记录')}；用途：{uses}{restriction}")
    if len(assets) > 12:
        lines.append(f"- 另有 {len(assets) - 12} 个资产。")
    return lines


def _group_design_lines(root: Path) -> list[str]:
    path = root / GROUP_COMPARISON_DESIGN
    if not path.exists():
        return ["- 尚未确认分组与比较设计。"]
    design = _read_json(path)
    groups = [item for item in design.get("sample_groups", []) or [] if isinstance(item, dict)]
    comparisons = [item for item in design.get("comparisons", []) or [] if isinstance(item, dict)]
    controls = [str(item.get("user_group_name") or "") for item in groups if item.get("group_role") == "control"]
    lines = [f"- 样本组数：{len(groups)}", f"- 比较数：{len(comparisons)}", f"- 对照组：{', '.join(controls) if controls else '未设置'}"]
    lines.extend(f"- 比较：{item.get('comparison_name')} ({item.get('case_group')} vs {item.get('control_group')})" for item in comparisons[:8])
    return lines


def _imported_result_lines(imported: list[dict[str, object]]) -> list[str]:
    if not imported:
        return ["- 未检测到导入表格中的已有 DEG 结果。"]
    return [
        f"- {item.get('item_id')}：{item.get('description') or '导入表格中的已有差异分析结果'}；比较数：{item.get('comparison_count', 0)}；状态：{item.get('status')}"
        for item in imported
    ]


def _task_run_lines(task_runs: list[dict[str, object]], task_records: list[dict[str, object]]) -> list[str]:
    lines = []
    for item in task_runs:
        lines.append(
            f"- {item.get('item_id')}：{item.get('task_type')}；状态：{item.get('status')}；比较数：{item.get('comparison_count', 0)}；说明：任务记录不代表真实 DEG 已完成。"
        )
    for item in task_records:
        lines.append(f"- legacy task record {item.get('task_id', '')}：{item.get('task_type', '')}；状态：{item.get('status', '')}")
    return lines or ["- 暂无分析任务记录。"]


def _completed_result_lines(completed: list[dict[str, object]]) -> list[str]:
    if not completed:
        return ["- 尚无已完成分析结果。dry-run 任务不会列为完成结果。"]
    return [f"- {item.get('item_id')}：{item.get('result_name') or item.get('analysis_type')}；状态：{item.get('status')}" for item in completed]


def _warning_lines(warnings: list[str], task_runs: list[dict[str, object]]) -> list[str]:
    lines = [f"- {warning}" for warning in warnings if warning]
    if any(item.get("status") == "skipped_dry_run" for item in task_runs):
        lines.append("- 检测到 dry-run 任务记录：当前版本尚未执行真实 DEG，不能解读为 DEG 已完成。")
    lines.append("- 报告草稿不会生成假差异基因表、假火山图或假富集结果。")
    return list(dict.fromkeys(lines))


def _draft_differential_expression_section(result_items: list[dict[str, object]]) -> str:
    imported = [item for item in result_items if item.get("item_type") == "imported_deg_result"]
    task_runs = [item for item in result_items if item.get("item_type") == "analysis_task_run"]
    lines = []
    lines.extend(f"- 导入 DEG：{item.get('item_id')}；比较数：{item.get('comparison_count', 0)}；来源：导入表格中的已有差异分析结果" for item in imported)
    lines.extend(f"- 重新 DEG 任务记录：{item.get('item_id')}；状态：{item.get('status')}；尚未执行真实 DEG" for item in task_runs)
    return "\n".join(lines) if lines else "Not available in this run."


def _draft_group_design_section(root: Path) -> str:
    return "\n".join(_group_design_lines(root))


def _draft_parameter_section(result_items: list[dict[str, object]]) -> dict[str, object]:
    task_runs = [item for item in result_items if item.get("item_type") == "analysis_task_run"]
    return {
        "analysis_task_runs": [
            {
                "run_id": item.get("item_id", ""),
                "task_type": item.get("task_type", ""),
                "status": item.get("status", ""),
                "parameters": item.get("parameters", {}),
            }
            for item in task_runs
        ],
        "note": "dry-run parameters are planning metadata only.",
    }


def _status_for_source(sections: list[dict[str, object]], section_id: str) -> str:
    return str(next((section.get("status") for section in sections if section.get("section_id") == section_id), "not_available"))


def _read_json(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
