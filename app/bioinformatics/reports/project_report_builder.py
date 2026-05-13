from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.deg_task_plan import load_deg_preflight_manifest
from app.bioinformatics.imported_deg_results import list_imported_deg_results
from app.bioinformatics.project_analysis_tasks import load_task_records
from app.bioinformatics.project_readiness import load_readiness_artifacts
from app.bioinformatics.project_recognition import load_recognition_report
from app.bioinformatics.project_standardization import load_standardization_artifacts
from app.bioinformatics.project_workspace_binding import load_latest_acquisition_summary
from app.bioinformatics.results.project_results import load_result_index


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
    preflight = load_deg_preflight_manifest(root)
    imported_deg_results = list_imported_deg_results(root)
    warnings: list[str] = []
    if acquisition is None:
        warnings.append("尚未生成数据获取记录。")
    warnings.extend(str(item) for item in recognition.get("warnings", []) or [] if isinstance(recognition, dict))
    warnings.extend(str(item) for item in readiness.get("warnings", []) or [] if isinstance(readiness, dict))
    warnings.extend(str(item) for item in standardization.get("warnings", []) or [] if isinstance(standardization, dict))
    warnings.extend(_safe_user_text(str(item), root) for item in result_index.get("warnings", []) or [])
    markdown_path = root / PROJECT_REPORT_MD
    markdown = _render_draft_markdown(
        root=root,
        acquisition=acquisition,
        recognition=recognition,
        readiness=readiness,
        standardization=standardization,
        result_index=result_index,
        task_records=task_records,
        preflight=preflight,
        imported_deg_results=imported_deg_results,
        warnings=warnings,
    )
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown, encoding="utf-8")
    entries = [item for item in result_index.get("entries", []) or [] if isinstance(item, dict)]
    included_result_ids = [str(item.get("result_id") or "") for item in entries if item.get("report_candidate") and item.get("result_id")]
    manifest = {
        "schema_version": "biomedpilot.project_report_manifest.v1",
        "generated_at": _now(),
        "markdown_path": str(markdown_path),
        "semantic_policy": _semantic_policy(),
        "section_statuses": _section_statuses(acquisition, recognition, readiness, standardization, task_records, preflight, imported_deg_results),
        "included_result_ids": included_result_ids,
        "warning_count": len(warnings),
        "warnings": warnings,
        "exports": {"Markdown": str(markdown_path), "PDF": "本阶段不支持", "DOCX": "本阶段不支持"},
    }
    builder_report = {
        "schema_version": "biomedpilot.project_report_builder_report.v1",
        "generated_at": manifest["generated_at"],
        "status": "generated",
        "warnings": manifest["warnings"],
    }
    _write_json(root / PROJECT_REPORT_MANIFEST, manifest)
    _write_json(root / PROJECT_REPORT_BUILDER_REPORT, builder_report)
    return {"markdown": markdown, "markdown_path": str(markdown_path), "manifest": manifest, "builder_report": builder_report}


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


def _render_draft_markdown(
    *,
    root: Path,
    acquisition: object,
    recognition: dict[str, object],
    readiness: dict[str, object],
    standardization: dict[str, object],
    result_index: dict[str, object],
    task_records: list[dict[str, object]],
    preflight: dict[str, object] | None,
    imported_deg_results: list[object],
    warnings: list[str],
) -> str:
    manifest = _read_json(root / "project_manifest.json") if (root / "project_manifest.json").exists() else {}
    project_name = str(manifest.get("project_name") or root.name)
    entries = [item for item in result_index.get("entries", []) or [] if isinstance(item, dict)]
    recognition_files = len(recognition.get("files", []) or []) if isinstance(recognition, dict) else 0
    lines = [
        "# BioMedPilot 生信项目报告草稿",
        "",
        "本报告为草稿级报告，用于项目内部检查和人工核对，不是正式发表级、临床级或投稿级报告。",
        "",
        "## 项目基本信息",
        "",
        f"- 项目名称：{project_name}",
        f"- 报告生成时间：{_now()}",
        "- 报告阶段：Markdown 草稿",
        "",
        "## 数据来源",
        "",
        f"- 数据来源：{_safe_user_text(getattr(acquisition, 'source_label', '尚未记录'), root) if acquisition else '尚未记录'}",
        f"- 来源类型：{_safe_user_text(getattr(acquisition, 'source_type', '尚未记录'), root) if acquisition else '尚未记录'}",
        "",
        "## 识别状态",
        "",
        f"- 已识别文件数量：{recognition_files}",
        f"- 识别状态：{'已生成识别记录' if recognition_files else '尚未生成识别记录'}",
        "",
        "## 标准化状态",
        "",
        f"- 标准化状态：{_standardization_text(standardization)}",
        "",
        "## 分析任务状态",
        "",
        f"- 任务记录数量：{len(task_records)}",
        f"- 任务语义：{'任务已配置但尚未执行' if task_records else '尚未配置分析任务'}",
        "",
        "## Preflight 检查结果",
        "",
        _preflight_text(preflight),
        "",
        "## 导入的 DEG 结果",
        "",
    ]
    lines.extend(_imported_deg_lines(imported_deg_results))
    lines.extend(
        [
            "",
            "## 结果语义声明",
            "",
            "- preflight-only：输入检查已完成 / 尚未运行真实分析。",
            "- imported result：用户导入的外部分析结果显示。",
            "- testing-level result：测试级分析输出，不应用于正式科研结论。",
            "- dry-run / configured-not-run：任务已配置但尚未执行。",
            "- real computed result：本阶段未开放真实 DEG 计算结果。",
            "",
            "## 下一步建议",
            "",
        ]
    )
    lines.extend(_next_step_lines(entries, task_records, preflight, imported_deg_results))
    if warnings:
        lines.extend(["", "## 注意事项", ""])
        lines.extend(f"- {_safe_user_text(warning, root)}" for warning in warnings)
    return "\n".join(lines).rstrip() + "\n"


def _standardization_text(standardization: dict[str, object]) -> str:
    if isinstance(standardization, dict) and standardization.get("exists"):
        return "已生成标准化资产记录；当前描述资产状态，不代表真实 DEG 已执行。"
    return "尚未生成标准化资产记录。"


def _preflight_text(preflight: dict[str, object] | None) -> str:
    if not isinstance(preflight, dict):
        return "- 尚未运行 DEG preflight；尚未运行真实分析。"
    status = str(preflight.get("status") or "unknown")
    return f"- DEG preflight 状态：{status}；输入检查已完成 / 尚未运行真实分析。"


def _imported_deg_lines(imported_deg_results: list[object]) -> list[str]:
    if not imported_deg_results:
        return ["- 当前没有已识别的导入 DEG 结果。"]
    lines: list[str] = []
    for result in imported_deg_results:
        name = str(getattr(result, "name", "导入 DEG 结果"))
        counts = getattr(result, "regulation_counts", {}) or {}
        if counts.get("status") == "computed":
            count_text = f"上调 {counts.get('up')}，下调 {counts.get('down')}，不显著 {counts.get('not_significant')}"
        else:
            count_text = "上调 / 下调 / 不显著数量待确认"
        top_up = "、".join(str(item.get("gene") or "未命名") for item in list(getattr(result, "top_up_genes", ()) or ())[:5]) or "暂无"
        top_down = "、".join(str(item.get("gene") or "未命名") for item in list(getattr(result, "top_down_genes", ()) or ())[:5]) or "暂无"
        lines.append(f"- {name}：用户导入的外部分析结果显示，{count_text}。Top up genes：{top_up}；Top down genes：{top_down}。")
    return lines


def _next_step_lines(entries: list[dict[str, object]], task_records: list[dict[str, object]], preflight: dict[str, object] | None, imported_deg_results: list[object]) -> list[str]:
    lines = ["- 人工核对导入结果的列映射、阈值和来源说明。"]
    if not imported_deg_results:
        lines.append("- 如需形成 DEG 结果浏览闭环，请先导入外部差异分析表。")
    if preflight is not None:
        lines.append("- preflight 只说明输入检查状态；真实 DEG 执行器需要后续单独审计。")
    if task_records and not entries:
        lines.append("- 当前任务已配置但尚未执行，不应写成分析发现。")
    return lines


def _semantic_policy() -> dict[str, str]:
    return {
        "preflight-only": "输入检查已完成 / 尚未运行真实分析",
        "imported result": "用户导入的外部分析结果显示",
        "testing-level result": "测试级分析输出，不应用于正式科研结论",
        "dry-run / configured-not-run": "任务已配置但尚未执行",
        "real computed result": "当前未开放；本阶段不生成真实计算结论",
    }


def _section_statuses(
    acquisition: object,
    recognition: dict[str, object],
    readiness: dict[str, object],
    standardization: dict[str, object],
    task_records: list[dict[str, object]],
    preflight: dict[str, object] | None,
    imported_deg_results: list[object],
) -> dict[str, str]:
    recognition_files = len(recognition.get("files", []) or []) if isinstance(recognition, dict) else 0
    return {
        "project_info": "available",
        "data_source": "available" if acquisition else "missing",
        "recognition": "available" if recognition_files else "missing",
        "standardization": "available" if isinstance(standardization, dict) and standardization.get("exists") else "missing",
        "analysis_task_status": "available" if task_records else "not_configured",
        "preflight": "available" if preflight else "not_run",
        "imported_deg_results": "available" if imported_deg_results else "missing",
        "result_semantics": "enforced",
        "next_steps": "available",
    }


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_user_text(value: object, root: Path) -> str:
    text = str(value)
    if not text:
        return ""
    root_text = str(root)
    if root_text in text:
        text = text.replace(root_text, "[项目目录]")
    if "结果文件缺失：" in text:
        return "结果文件缺失，请在开发者诊断中查看路径。"
    path = Path(text).expanduser()
    if path.is_absolute():
        return path.name
    return text
