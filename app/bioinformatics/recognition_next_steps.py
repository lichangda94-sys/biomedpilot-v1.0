from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.bioinformatics.comparison_config import load_confirmed_comparison_config
from app.bioinformatics.group_comparison_design import has_confirmed_group_comparison_design
from app.bioinformatics.project_recognition import CURRENT_RECOGNITION_RUN
from app.bioinformatics.project_standardization import load_standardization_artifacts


def build_recognition_next_steps(
    project_root: str | Path,
    run: dict[str, object] | None,
    files: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    run = dict(run or {})
    files = [item for item in files or _files_from_run(root, run) if isinstance(item, dict)]
    run_id = str(run.get("run_id") or "")
    current_status = recognition_run_current_status(root, run)
    block_types = _block_types(files)
    species_group = _species_group(files)
    standardized = _standardized_state(root)
    has_assets = bool(standardized["asset_types"])
    has_imported_deg = "deg_result_table" in standardized["asset_types"] or "deg_comparisons" in block_types
    has_standardizable = bool(
        block_types
        & {
            "count_expression_matrix",
            "fpkm_expression_matrix",
            "tpm_expression_matrix",
            "deg_comparisons",
            "gene_annotation",
            "gene_identifier",
        }
    ) or any(str(item.get("recognized_type") or "") in {"expression_matrix", "raw_count_matrix", "normalized_expression_matrix"} for item in files)
    is_unknown = not has_standardizable
    has_group_config = load_confirmed_comparison_config(root) is not None or has_confirmed_group_comparison_design(root)

    if is_unknown:
        primary = {"label": "返回数据导入", "target": "data_source"}
        secondary = [
            {"label": "查看识别详情", "target": "detail"},
            {"label": "导出数据识别报告", "target": "export_recognition_report"},
        ]
    elif current_status["status"] != "current":
        primary = {"label": "设为当前标准化输入", "target": "set_current_recognition_run", "run_id": run_id}
        secondary = [
            {"label": "查看详情", "target": "detail"},
            {"label": "导出数据识别报告", "target": "export_recognition_report"},
        ]
    elif has_assets:
        primary = {"label": "进入分析任务中心", "target": "analysis_tasks"}
        secondary = [
            {"label": "查看已有 DEG 结果", "target": "result_browser"},
            {"label": "查看标准化资产", "target": "standardization"},
            {"label": "导出数据识别报告", "target": "export_recognition_report"},
        ]
    else:
        primary = {"label": "继续数据标准化", "target": "standardization"}
        secondary = [
            {"label": "查看识别详情", "target": "detail"},
            {"label": "进入分析任务中心", "target": "analysis_tasks"},
            {"label": "导出数据识别报告", "target": "export_recognition_report"},
        ]
        if has_imported_deg:
            secondary.insert(1, {"label": "查看已有 DEG 结果", "target": "result_browser"})

    direct = []
    if has_standardizable:
        direct.append("进入数据标准化")
    if has_imported_deg:
        direct.extend(["查看已有 DEG 结果", "DEG 筛选", "富集分析输入"])
    if "fpkm_expression_matrix" in block_types or "tpm_expression_matrix" in block_types or "normalized_expression_matrix" in standardized["asset_types"]:
        direct.extend(["表达热图", "样本相关性"])
    if has_assets:
        direct.append("进入分析任务中心")
    direct.append("导出数据识别报告")

    needs_confirmation = []
    if "count_expression_matrix" in block_types or "count_matrix" in standardized["asset_types"]:
        if not has_group_config:
            needs_confirmation.append("重新差异表达分析需要确认分组")
            needs_confirmation.append("样本 QC 需要确认样本分组和批次信息")
            secondary.insert(1, {"label": "确认分组与比较设计", "target": "group_design"})
        else:
            direct.append("分组设计已确认，可进入分析任务中心配置差异分析")

    not_recommended = []
    if species_group == "mouse":
        not_recommended.extend(["直接作为人类临床队列解释", "小鼠数据不建议默认接入 TCGA/GTEx 人类队列"])
    if is_unknown:
        not_recommended.append("未检测到明确表达矩阵、差异分析结果或样本注释结构，请检查文件格式或重新导入")

    return {
        "run_id": run_id,
        "current_status": current_status,
        "primary_action": primary,
        "secondary_actions": _dedupe_actions(secondary),
        "direct_available": _unique(direct),
        "needs_confirmation": _unique(needs_confirmation),
        "not_recommended": _unique(not_recommended),
        "has_imported_deg": has_imported_deg,
        "has_standardized_assets": has_assets,
        "asset_types": sorted(standardized["asset_types"]),
        "content_block_types": sorted(block_types),
        "species_group": species_group,
        "summary_text": format_next_steps_text(
            {
                "current_status": current_status,
                "primary_action": primary,
                "direct_available": _unique(direct),
                "needs_confirmation": _unique(needs_confirmation),
                "not_recommended": _unique(not_recommended),
            }
        ),
    }


def recognition_run_current_status(project_root: str | Path, run: dict[str, object] | None = None) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    run = dict(run or {})
    run_id = str(run.get("run_id") or "")
    current = _read_json(root / CURRENT_RECOGNITION_RUN)
    current_run_id = str(current.get("run_id") or "")
    current_run_dir = Path(str(current.get("run_dir") or ""))
    if current_run_dir and not current_run_dir.is_absolute():
        current_run_dir = root / current_run_dir
    if run.get("legacy"):
        return {"status": "legacy", "label": "旧版识别记录", "note": "由旧版项目结构导入。"}
    if run_id and current_run_id == run_id:
        note = "该识别记录将作为数据标准化的输入。"
        if current_run_dir and not current_run_dir.exists():
            return {"status": "stale_current", "label": "当前识别输入已失效", "note": "请重新识别或选择历史识别记录。"}
        return {"status": "current", "label": "当前使用中", "note": note}
    if run.get("recognition_report") and not run.get("recognition_report_path"):
        return {"status": "transient", "label": "本次识别结果，尚未设为当前输入", "note": "该识别记录当前不会被标准化模块使用。"}
    return {"status": "history", "label": "历史记录", "note": "该识别记录仅供查看，不会修改本次识别结果或标准化输入。"}


def standardization_current_input_summary(project_root: str | Path) -> str:
    root = Path(project_root).expanduser().resolve()
    current_path = root / CURRENT_RECOGNITION_RUN
    if not current_path.exists():
        return "尚未选择当前识别结果。\n请先完成数据识别，或从历史识别记录中选择一条作为当前标准化输入。"
    current = _read_json(current_path)
    run_dir = Path(str(current.get("run_dir") or ""))
    if run_dir and not run_dir.is_absolute():
        run_dir = root / run_dir
    if run_dir and not run_dir.exists():
        return "当前识别输入已失效。\n请重新识别或选择历史识别记录。"
    report_path = Path(str(current.get("recognition_report_path") or ""))
    if report_path and not report_path.is_absolute():
        report_path = root / report_path
    report = _read_json(report_path)
    files = [item for item in report.get("files", []) or [] if isinstance(item, dict)]
    return "\n".join(
        [
            "当前标准化输入：",
            f"recognition run id：{current.get('run_id') or '未记录'}",
            f"输入文件数：{len(files)}",
            f"内容摘要：{_content_summary(files)}",
            f"生成时间：{current.get('generated_at') or report.get('generated_at') or '未记录'}",
            "当前状态：已选择为标准化输入",
        ]
    )


def format_next_steps_text(next_steps: dict[str, object]) -> str:
    status = next_steps.get("current_status") if isinstance(next_steps.get("current_status"), dict) else {}
    primary = next_steps.get("primary_action") if isinstance(next_steps.get("primary_action"), dict) else {}
    direct = [str(item) for item in next_steps.get("direct_available", []) or [] if str(item)]
    confirm = [str(item) for item in next_steps.get("needs_confirmation", []) or [] if str(item)]
    blocked = [str(item) for item in next_steps.get("not_recommended", []) or [] if str(item)]
    lines = [
        "下一步建议",
        f"当前状态：{status.get('label') or '未识别'}",
        str(status.get("note") or ""),
        f"主操作：{primary.get('label') or '未设置'}",
    ]
    if direct:
        lines.append("可直接进行：" + "、".join(direct))
    if confirm:
        lines.append("需要确认后进行：" + "、".join(confirm))
    if blocked:
        lines.append("不建议：" + "、".join(blocked))
    return "\n".join(line for line in lines if line)


def _files_from_run(root: Path, run: dict[str, object]) -> list[dict[str, object]]:
    report = run.get("recognition_report")
    if not isinstance(report, dict):
        path = Path(str(run.get("recognition_report_path") or ""))
        if path and not path.is_absolute():
            path = root / path
        report = _read_json(path)
    return [item for item in report.get("files", []) or [] if isinstance(item, dict)] if isinstance(report, dict) else []


def _standardized_state(root: Path) -> dict[str, set[str]]:
    artifacts = load_standardization_artifacts(root)
    registry = artifacts.get("registry")
    assets = registry.get("assets", []) if isinstance(registry, dict) else []
    return {"asset_types": {str(asset.get("asset_type") or "") for asset in assets if isinstance(asset, dict)}}


def _block_types(files: list[dict[str, object]]) -> set[str]:
    result: set[str] = set()
    for item in files:
        for block in _content_blocks(item):
            result.add(str(block.get("block_type") or ""))
    return {value for value in result if value}


def _content_blocks(item: dict[str, object]) -> list[dict[str, object]]:
    blocks = item.get("content_blocks")
    if not isinstance(blocks, list):
        profile = item.get("content_profile")
        blocks = profile.get("content_blocks") if isinstance(profile, dict) else []
    return [block for block in blocks or [] if isinstance(block, dict)]


def _species_group(files: list[dict[str, object]]) -> str:
    for item in files:
        group = str(item.get("species_group") or "")
        if group:
            return group
        profile = item.get("content_profile")
        if isinstance(profile, dict) and profile.get("species_group"):
            return str(profile.get("species_group"))
        for block in _content_blocks(item):
            if block.get("species_group"):
                return str(block.get("species_group"))
    return ""


def _content_summary(files: list[dict[str, object]]) -> str:
    block_types = _block_types(files)
    labels = []
    if "count_expression_matrix" in block_types:
        labels.append("count 矩阵")
    if "fpkm_expression_matrix" in block_types:
        labels.append("FPKM 矩阵")
    if "tpm_expression_matrix" in block_types:
        labels.append("TPM 矩阵")
    if "deg_comparisons" in block_types:
        labels.append("已有 DEG 结果")
    if "gene_annotation" in block_types:
        labels.append("基因注释")
    if "gene_identifier" in block_types:
        labels.append("基因标识")
    if labels:
        return "、".join(labels)
    file_types = [str(item.get("semantic_type_zh") or item.get("recognized_type_zh") or item.get("recognized_type") or "") for item in files]
    return "、".join(_unique(file_types)) if file_types else "无有效识别文件"


def _dedupe_actions(actions: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[str] = set()
    result = []
    for action in actions:
        key = str(action.get("target") or "") + ":" + str(action.get("label") or "")
        if action.get("target") and key not in seen:
            seen.add(key)
            result.append(action)
    return result


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for value in values:
        text = str(value).strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}
