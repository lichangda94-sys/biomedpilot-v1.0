from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.bioinformatics.data_sources.tcga_clinical_builder import (
    latest_tcga_clinical_build_manifest_path,
    latest_tcga_expression_build_manifest_path,
)
from app.bioinformatics.data_sources.tcga_download_executor import latest_tcga_download_plan_path
from app.bioinformatics.data_sources.tcga_expression_builder import latest_tcga_raw_expression_record_path
from app.bioinformatics.project_workspace_binding import LATEST_RECORD


WORKFLOW_STEP_IDS = ("preview", "download", "expression_build", "clinical", "data_check")


@dataclass(frozen=True)
class TCGAWorkflowStep:
    step_id: str
    title: str
    status: str
    enabled: bool
    summary: str
    action_label: str | None = None
    blocking_reason: str | None = None
    warning: str | None = None
    developer_details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TCGAWorkflowState:
    project_id: str | None
    analysis_purpose: str | None
    sample_scope: str | None
    current_stage: str
    steps: list[TCGAWorkflowStep]
    next_action: str | None
    can_enter_data_check: bool
    warnings: list[str]
    developer_diagnostics: dict[str, Any]

    def step(self, step_id: str) -> TCGAWorkflowStep:
        for item in self.steps:
            if item.step_id == step_id:
                return item
        raise KeyError(step_id)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["steps"] = [step.to_dict() for step in self.steps]
        return payload


def build_tcga_workflow_state(
    project_root: str | Path | None,
    *,
    project_id: str | None = None,
    analysis_purpose: str | None = None,
    sample_scope: str | None = None,
) -> TCGAWorkflowState:
    root = Path(project_root).expanduser().resolve() if project_root is not None else None
    selected_project = str(project_id or "").strip().upper() or None
    records = _tcga_records(root, selected_project)
    request_record = _latest_record(records, {"registered_pending_tcga_build"})
    plan_path = _latest_plan_path(root, selected_project)
    plan = _read_json(plan_path) if plan_path is not None else {}
    raw_record = _latest_raw_record(records)
    expression_manifest_path = latest_tcga_expression_build_manifest_path(root) if root is not None else None
    expression_manifest = _read_json(expression_manifest_path) if expression_manifest_path is not None else {}
    clinical_manifest_path = latest_tcga_clinical_build_manifest_path(root) if root is not None else None
    clinical_manifest = _read_json(clinical_manifest_path) if clinical_manifest_path is not None else {}
    raw_record_path = latest_tcga_raw_expression_record_path(root) if root is not None else None

    raw_summary = _metadata_summary(raw_record, "tcga_download_summary")
    expression_summary = _metadata_summary(_record_for_manifest(records, expression_manifest_path), "tcga_expression_build_summary")
    clinical_summary = _metadata_summary(_record_for_manifest(records, clinical_manifest_path), "tcga_clinical_summary")
    if not clinical_summary and isinstance(clinical_manifest.get("summary"), dict):
        clinical_summary = clinical_manifest["summary"]

    warnings: list[str] = []
    warnings.extend(_plan_warnings(plan))
    warnings.extend(_raw_warnings(raw_record, raw_summary))
    warnings.extend(_expression_warnings(expression_manifest))
    warnings.extend(_clinical_warnings(clinical_manifest, clinical_summary))
    warnings.append("TCGA+GTEx 不自动合并；GTEx 不会作为 TCGA 正常对照。")

    preview_step = _preview_step(selected_project, plan_path, plan, request_record)
    download_step = _download_step(plan_path, plan, raw_record, raw_summary, expression_manifest_path, clinical_manifest_path)
    expression_step = _expression_step(raw_record_path, raw_record, expression_manifest_path, expression_manifest, expression_summary, clinical_manifest_path)
    clinical_step = _clinical_step(expression_manifest_path, clinical_manifest_path, clinical_manifest, clinical_summary, selected_project)
    data_check_step = _data_check_step(expression_manifest_path, expression_manifest, clinical_manifest_path, clinical_summary)
    steps = [preview_step, download_step, expression_step, clinical_step, data_check_step]
    current_stage = _current_stage(steps)
    next_step = next((step for step in steps if step.enabled and step.status in {"available", "failed"}), None)
    if next_step is None:
        next_step = next((step for step in steps if step.status == "blocked"), None)
    diagnostics = {
        "project_root": str(root or ""),
        "request_record_path": str(request_record.get("record_path") or "") if request_record else "",
        "download_plan_path": str(plan_path or ""),
        "download_receipt_path": _metadata_value(raw_record, "download_receipt_path"),
        "source_manifest_path": _metadata_value(raw_record, "source_manifest_path"),
        "download_manifest_path": _metadata_value(raw_record, "download_manifest_path"),
        "cache_path": _metadata_value(raw_record, "download_target_dir"),
        "expression_build_manifest_path": str(expression_manifest_path or ""),
        "clinical_build_manifest_path": str(clinical_manifest_path or ""),
        "raw_record_path": str(raw_record_path or ""),
        "highest_stage_record": _highest_stage_record(records),
    }
    return TCGAWorkflowState(
        project_id=selected_project,
        analysis_purpose=analysis_purpose,
        sample_scope=sample_scope,
        current_stage=current_stage,
        steps=steps,
        next_action=next_step.action_label if next_step and next_step.enabled else None,
        can_enter_data_check=bool(expression_manifest_path),
        warnings=list(dict.fromkeys(warnings)),
        developer_diagnostics=diagnostics,
    )


def _preview_step(
    project_id: str | None,
    plan_path: Path | None,
    plan: dict[str, Any],
    request_record: dict[str, Any],
) -> TCGAWorkflowStep:
    if plan_path is not None:
        preview = plan.get("preview_summary") if isinstance(plan.get("preview_summary"), dict) else {}
        summary = (
            f"已完成预览：case {preview.get('case_count') or plan.get('case_count') or '-'}，"
            f"sample {preview.get('sample_count') or '-'}，file {plan.get('file_count') or 0}，"
            f"预计大小 {preview.get('estimated_size_bytes') or plan.get('estimated_size_bytes') or 0} bytes。"
        )
        return TCGAWorkflowStep("preview", "1. 预览可下载数据", "completed", False, summary, developer_details={"plan_path": str(plan_path)})
    if not project_id:
        return TCGAWorkflowStep("preview", "1. 预览可下载数据", "blocked", False, "请先选择 TCGA project。", "预览可下载数据", "未选择 project")
    if request_record:
        return TCGAWorkflowStep("preview", "1. 预览可下载数据", "available", True, "已有 TCGA request 草案；可重新预览并生成下载计划。", "预览可下载数据")
    return TCGAWorkflowStep("preview", "1. 预览可下载数据", "available", True, "选择癌种、分析目的和样本范围后可预览。", "预览可下载数据")


def _download_step(
    plan_path: Path | None,
    plan: dict[str, Any],
    raw_record: dict[str, Any],
    raw_summary: dict[str, Any],
    expression_manifest_path: Path | None,
    clinical_manifest_path: Path | None,
) -> TCGAWorkflowStep:
    if expression_manifest_path is not None or clinical_manifest_path is not None:
        return TCGAWorkflowStep("download", "2. 下载 TCGA 原始文件", "completed", False, "原始文件已获取，并已推进到后续构建阶段。")
    raw_status = _download_status(raw_record)
    acquired = int(raw_summary.get("acquired_count") or 0)
    if acquired > 0:
        failed = int(raw_summary.get("failed_count") or 0)
        blocked = int(raw_summary.get("blocked_count") or 0)
        warning = "存在失败或阻断文件。" if failed or blocked else None
        return TCGAWorkflowStep(
            "download",
            "2. 下载 TCGA 原始文件",
            "completed",
            False,
            f"已获取 {acquired} 个原始文件；失败 {failed}，阻断 {blocked}，累计 {raw_summary.get('total_size_display') or raw_summary.get('total_size_bytes') or 0}。",
            warning=warning,
            developer_details={"receipt_path": _metadata_value(raw_record, "download_receipt_path")},
        )
    if raw_status in {"tcga_gdc_raw_file_download_failed", "tcga_gdc_download_plan_empty"}:
        return TCGAWorkflowStep("download", "2. 下载 TCGA 原始文件", "failed", bool(plan_path), "下载未获取可用原始文件。", "下载 TCGA 原始文件", "无成功下载或缓存文件")
    if plan_path is None:
        return TCGAWorkflowStep("download", "2. 下载 TCGA 原始文件", "blocked", False, "需要先完成预览并生成下载计划。", "下载 TCGA 原始文件", "没有 download plan")
    file_count = int(plan.get("file_count") or 0)
    if file_count <= 0:
        return TCGAWorkflowStep("download", "2. 下载 TCGA 原始文件", "blocked", False, "下载计划为空，没有可下载表达文件。", "下载 TCGA 原始文件", "download plan 为空")
    return TCGAWorkflowStep("download", "2. 下载 TCGA 原始文件", "available", True, f"下载计划已就绪：{file_count} 个候选文件。", "下载 TCGA 原始文件", developer_details={"plan_path": str(plan_path)})


def _expression_step(
    raw_record_path: Path | None,
    raw_record: dict[str, Any],
    expression_manifest_path: Path | None,
    expression_manifest: dict[str, Any],
    expression_summary: dict[str, Any],
    clinical_manifest_path: Path | None,
) -> TCGAWorkflowStep:
    if expression_manifest_path is not None:
        sample_count = expression_manifest.get("sample_count") or expression_summary.get("sample_count") or 0
        gene_count = expression_manifest.get("gene_count") or expression_summary.get("gene_count") or 0
        summary = f"表达矩阵已构建：{sample_count} 个样本，{gene_count} 个基因；raw counts 用于 DEG preflight 候选。"
        return TCGAWorkflowStep("expression_build", "3. 构建 TCGA 表达矩阵", "completed", False, summary, developer_details={"expression_build_manifest_path": str(expression_manifest_path)})
    if clinical_manifest_path is not None:
        return TCGAWorkflowStep("expression_build", "3. 构建 TCGA 表达矩阵", "completed", False, "表达构建已完成，并已推进到 clinical 阶段。")
    if raw_record_path is not None or int(_metadata_summary(raw_record, "tcga_download_summary").get("acquired_count") or 0) > 0:
        return TCGAWorkflowStep("expression_build", "3. 构建 TCGA 表达矩阵", "available", True, "已获取原始表达文件，可构建 raw counts/TPM/FPKM/FPKM-UQ 矩阵。", "构建 TCGA 表达矩阵")
    return TCGAWorkflowStep("expression_build", "3. 构建 TCGA 表达矩阵", "blocked", False, "需要先成功下载或缓存 TCGA expression quantification 文件。", "构建 TCGA 表达矩阵", "没有成功下载的 expression 文件")


def _clinical_step(
    expression_manifest_path: Path | None,
    clinical_manifest_path: Path | None,
    clinical_manifest: dict[str, Any],
    clinical_summary: dict[str, Any],
    project_id: str | None,
) -> TCGAWorkflowStep:
    if clinical_manifest_path is not None:
        mode = str(clinical_manifest.get("mode") or "")
        matched = int(clinical_summary.get("matched_case_count") or 0)
        cases = int(clinical_summary.get("case_count") or 0)
        survival = int(clinical_summary.get("survival_case_count") or 0)
        deaths = int(clinical_summary.get("death_event_count") or 0)
        status = "completed" if mode != "project_clinical_preview_only" else "skipped"
        warning = "仅为项目 clinical 概况，尚未完成表达-临床映射。" if status == "skipped" else None
        return TCGAWorkflowStep("clinical", "4. 获取 TCGA 临床信息", status, False, f"clinical 已获取：{cases} case，匹配 {matched} case，基础 OS {survival} case，死亡事件 {deaths}。", warning=warning, developer_details={"clinical_manifest_path": str(clinical_manifest_path)})
    if expression_manifest_path is not None:
        return TCGAWorkflowStep("clinical", "4. 获取 TCGA 临床信息", "available", True, "表达矩阵已构建，可获取 clinical metadata 并建立表达-临床映射。", "获取 TCGA 临床信息")
    if project_id:
        return TCGAWorkflowStep("clinical", "4. 获取 TCGA 临床信息", "blocked", False, "需要先构建表达矩阵；项目 clinical 概况可在后续作为预览补充，但不能完成表达-临床映射。", "获取 TCGA 临床信息", "没有 expression build")
    return TCGAWorkflowStep("clinical", "4. 获取 TCGA 临床信息", "blocked", False, "需要先选择 TCGA project 并完成表达矩阵构建。", "获取 TCGA 临床信息", "未选择 project")


def _data_check_step(
    expression_manifest_path: Path | None,
    expression_manifest: dict[str, Any],
    clinical_manifest_path: Path | None,
    clinical_summary: dict[str, Any],
) -> TCGAWorkflowStep:
    if expression_manifest_path is None:
        return TCGAWorkflowStep("data_check", "5. 进入数据检查与准备", "blocked", False, "需要先完成 TCGA 表达矩阵构建。", "进入数据检查与准备", "没有 expression build")
    clinical_text = "clinical readiness 将在数据检查中显示。" if clinical_manifest_path is not None else "clinical 可稍后补充；表达数据已可进入数据检查。"
    sample_count = expression_manifest.get("sample_count") or 0
    gene_count = expression_manifest.get("gene_count") or 0
    if clinical_summary:
        clinical_text = f"clinical {clinical_summary.get('clinical_gate_status') or 'unknown'}；basic OS {clinical_summary.get('survival_gate_status') or 'unknown'}。"
    return TCGAWorkflowStep("data_check", "5. 进入数据检查与准备", "available", True, f"表达构建产物可进入数据检查：{sample_count} 样本 / {gene_count} 基因；{clinical_text}", "进入数据检查与准备")


def _tcga_records(root: Path | None, project_id: str | None) -> list[dict[str, Any]]:
    if root is None:
        return []
    records_dir = root / "acquisition" / "records"
    if not records_dir.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(records_dir.glob("*.json"), key=lambda item: item.stat().st_mtime):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if not isinstance(metadata, dict):
            metadata = {}
        if str(metadata.get("source") or "") != "tcga_gdc" and "tcga" not in str(payload.get("source_type") or ""):
            continue
        record_project = str(metadata.get("project_id") or payload.get("source_label") or "").strip().upper()
        if project_id and record_project and record_project != project_id:
            continue
        records.append({"record_path": str(path), "payload": payload, "metadata": metadata, "mtime": path.stat().st_mtime})
    return records


def _latest_record(records: list[dict[str, Any]], statuses: set[str]) -> dict[str, Any]:
    matches = [record for record in records if _download_status(record) in statuses]
    return matches[-1] if matches else {}


def _latest_raw_record(records: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = {
        "tcga_gdc_raw_files_acquired",
        "tcga_gdc_raw_files_acquired_with_warnings",
        "tcga_gdc_raw_file_download_failed",
        "tcga_gdc_download_plan_empty",
        "tcga_gdc_files_downloaded",
        "tcga_gdc_files_downloaded_with_warnings",
    }
    return _latest_record(records, statuses)


def _record_for_manifest(records: list[dict[str, Any]], manifest_path: Path | None) -> dict[str, Any]:
    if manifest_path is None:
        return {}
    target = str(manifest_path)
    for record in reversed(records):
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        if target in {
            str(metadata.get("tcga_expression_build_manifest_path") or ""),
            str(metadata.get("tcga_clinical_build_manifest_path") or ""),
        }:
            return record
    return {}


def _latest_plan_path(root: Path | None, project_id: str | None) -> Path | None:
    if root is None:
        return None
    plans_dir = root / "acquisition" / "tcga_download_plans"
    if not plans_dir.exists():
        return None
    candidates: list[Path] = []
    for path in plans_dir.glob("*.json"):
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        plan_project = str(payload.get("project_id") or "").strip().upper()
        if project_id and plan_project and plan_project != project_id:
            continue
        candidates.append(path)
    if candidates:
        return max(candidates, key=lambda item: item.stat().st_mtime)
    return latest_tcga_download_plan_path(root)


def _current_stage(steps: list[TCGAWorkflowStep]) -> str:
    completed = [step.step_id for step in steps if step.status in {"completed", "skipped"}]
    if completed:
        return completed[-1]
    available = next((step.step_id for step in steps if step.status == "available"), "preview")
    return available


def _highest_stage_record(records: list[dict[str, Any]]) -> dict[str, object]:
    order = {
        "tcga_clinical_metadata_built": 5,
        "tcga_expression_matrix_built": 4,
        "tcga_gdc_raw_files_acquired": 3,
        "tcga_gdc_raw_files_acquired_with_warnings": 3,
        "tcga_gdc_download_plan_draft_created": 2,
        "registered_pending_tcga_build": 1,
    }
    best = max(records, key=lambda record: (order.get(_download_status(record), 0), float(record.get("mtime") or 0)), default={})
    metadata = best.get("metadata") if isinstance(best.get("metadata"), dict) else {}
    return {
        "record_path": str(best.get("record_path") or ""),
        "download_status": str(metadata.get("download_status") or ""),
        "project_id": str(metadata.get("project_id") or ""),
    }


def _metadata_summary(record: dict[str, Any], key: str) -> dict[str, Any]:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    value = metadata.get(key) if isinstance(metadata, dict) else {}
    return value if isinstance(value, dict) else {}


def _metadata_value(record: dict[str, Any], key: str) -> str:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    return str(metadata.get(key) or "") if isinstance(metadata, dict) else ""


def _download_status(record: dict[str, Any]) -> str:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    return str(metadata.get("download_status") or "") if isinstance(metadata, dict) else ""


def _plan_warnings(plan: dict[str, Any]) -> list[str]:
    warnings = [str(item) for item in plan.get("warnings", []) or [] if str(item)] if isinstance(plan, dict) else []
    if int(plan.get("file_count") or 0) <= 0 and plan:
        warnings.append("当前 TCGA 下载计划没有匹配文件。")
    size = int(plan.get("estimated_size_bytes") or 0) if isinstance(plan, dict) else 0
    if size >= 5 * 1024 * 1024 * 1024:
        warnings.append("预计下载体积较大。")
    return warnings


def _raw_warnings(raw_record: dict[str, Any], raw_summary: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    failed = int(raw_summary.get("failed_count") or 0)
    blocked = int(raw_summary.get("blocked_count") or 0)
    if failed:
        warnings.append(f"TCGA 下载部分失败：{failed} 个文件。")
    if blocked:
        warnings.append(f"RAW/controlled-access 文件已阻断：{blocked} 个。")
    if _download_status(raw_record) == "tcga_gdc_raw_file_download_failed":
        warnings.append("TCGA 原始文件下载失败，不能构建表达矩阵。")
    return warnings


def _expression_warnings(manifest: dict[str, Any]) -> list[str]:
    return [str(item) for item in manifest.get("warnings", []) or [] if str(item)] if isinstance(manifest, dict) else []


def _clinical_warnings(manifest: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    warnings = [str(item) for item in manifest.get("warnings", []) or [] if str(item)] if isinstance(manifest, dict) else []
    if str(summary.get("clinical_gate_status") or "") == "clinical_partial":
        warnings.append("clinical 与表达 case 匹配比例不足或字段不完整。")
    if int(summary.get("death_event_count") or 0) and int(summary.get("death_event_count") or 0) < 5:
        warnings.append("basic OS 死亡事件数偏少，仅作为 preflight warning。")
    return warnings


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


__all__ = [
    "TCGAWorkflowState",
    "TCGAWorkflowStep",
    "WORKFLOW_STEP_IDS",
    "build_tcga_workflow_state",
]
