from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.bioinformatics.data_sources.gtex_download_executor import latest_gtex_raw_expression_record_path
from app.bioinformatics.data_sources.gtex_expression_builder import latest_gtex_expression_build_manifest_path
from app.bioinformatics.data_sources.gtex_preview import latest_gtex_download_plan_path
from app.bioinformatics.project_workspace_binding import LATEST_RECORD


@dataclass(frozen=True)
class GTExWorkflowStep:
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
class GTExWorkflowState:
    tissue_id: str | None
    use_purpose: str | None
    current_stage: str
    steps: list[GTExWorkflowStep]
    next_action: str | None
    can_enter_data_check: bool
    warnings: list[str]
    developer_diagnostics: dict[str, Any]

    def step(self, step_id: str) -> GTExWorkflowStep:
        for step in self.steps:
            if step.step_id == step_id:
                return step
        raise KeyError(step_id)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["steps"] = [step.to_dict() for step in self.steps]
        return payload


def build_gtex_workflow_state(project_root: str | Path | None, *, tissue_id: str | None = None, use_purpose: str | None = None) -> GTExWorkflowState:
    root = Path(project_root).expanduser().resolve() if project_root is not None else None
    selected_tissue = str(tissue_id or "").strip() or None
    records = _gtex_records(root, selected_tissue)
    plan_path = _latest_plan_path(root, selected_tissue)
    plan = _read_json(plan_path) if plan_path is not None else {}
    raw_record = _latest_raw_record(records)
    raw_record_path = latest_gtex_raw_expression_record_path(root) if root is not None else None
    build_manifest_path = latest_gtex_expression_build_manifest_path(root) if root is not None else None
    build_manifest = _read_json(build_manifest_path) if build_manifest_path is not None else {}
    raw_summary = _metadata_summary(raw_record, "gtex_download_summary")
    build_record = _record_for_manifest(records, build_manifest_path)
    build_summary = _metadata_summary(build_record, "gtex_expression_build_summary")
    steps = [
        _preview_step(selected_tissue, plan_path, plan),
        _download_step(plan_path, plan, raw_record, raw_summary, build_manifest_path),
        _build_step(raw_record_path, raw_summary, build_manifest_path, build_manifest, build_summary),
        _data_check_step(build_manifest_path, build_manifest),
        _manual_config_step(build_manifest_path),
    ]
    warnings = [
        *_plan_warnings(plan),
        *_raw_warnings(raw_record, raw_summary),
        *_build_warnings(build_manifest),
        "GTEx 不自动作为 TCGA normal control；TCGA+GTEx 需要显式联合配置和批次校正。",
    ]
    next_step = next((step for step in steps if step.enabled and step.status in {"available", "failed"}), None)
    return GTExWorkflowState(
        tissue_id=selected_tissue,
        use_purpose=use_purpose,
        current_stage=_current_stage(steps),
        steps=steps,
        next_action=next_step.action_label if next_step else None,
        can_enter_data_check=bool(build_manifest_path),
        warnings=list(dict.fromkeys(warnings)),
        developer_diagnostics={
            "project_root": str(root or ""),
            "download_plan_path": str(plan_path or ""),
            "download_receipt_path": _metadata_value(raw_record, "download_receipt_path"),
            "source_manifest_path": _metadata_value(raw_record, "source_manifest_path"),
            "download_manifest_path": _metadata_value(raw_record, "download_manifest_path"),
            "cache_path": _metadata_value(raw_record, "download_target_dir"),
            "expression_build_manifest_path": str(build_manifest_path or ""),
            "highest_stage_record": _highest_stage_record(records),
        },
    )


def _preview_step(tissue_id: str | None, plan_path: Path | None, plan: dict[str, Any]) -> GTExWorkflowStep:
    if plan_path is not None:
        preview = plan.get("preview_summary") if isinstance(plan.get("preview_summary"), dict) else {}
        return GTExWorkflowStep("preview", "1. 预览 GTEx 可下载数据", "completed", False, f"已完成预览：sample {preview.get('sample_count') or '-'}，donor {preview.get('donor_count') or '-'}，file {plan.get('file_count') or 0}。", developer_details={"plan_path": str(plan_path)})
    if not tissue_id:
        return GTExWorkflowStep("preview", "1. 预览 GTEx 可下载数据", "blocked", False, "请先选择 GTEx tissue。", "预览 GTEx 可下载数据", "未选择 tissue")
    return GTExWorkflowStep("preview", "1. 预览 GTEx 可下载数据", "available", True, "选择组织和使用目的后可预览 GTEx metadata。", "预览 GTEx 可下载数据")


def _download_step(plan_path: Path | None, plan: dict[str, Any], raw_record: dict[str, Any], raw_summary: dict[str, Any], build_manifest_path: Path | None) -> GTExWorkflowStep:
    if build_manifest_path is not None:
        return GTExWorkflowStep("download", "2. 下载 GTEx 原始文件", "completed", False, "原始文件已获取，并已推进到表达矩阵构建。")
    acquired = int(raw_summary.get("acquired_count") or 0)
    if acquired:
        failed = int(raw_summary.get("failed_count") or 0)
        return GTExWorkflowStep("download", "2. 下载 GTEx 原始文件", "completed", False, f"已获取 {acquired} 个 GTEx 原始文件；失败 {failed} 个。", warning="存在下载失败文件。" if failed else None)
    if _download_status(raw_record) in {"gtex_raw_file_download_failed", "gtex_download_plan_empty"}:
        return GTExWorkflowStep("download", "2. 下载 GTEx 原始文件", "failed", bool(plan_path), "未获取可用 GTEx 原始文件。", "下载 GTEx 原始文件")
    if plan_path is None:
        return GTExWorkflowStep("download", "2. 下载 GTEx 原始文件", "blocked", False, "需要先生成 GTEx 下载计划。", "下载 GTEx 原始文件", "没有 download plan")
    if int(plan.get("file_count") or 0) <= 0:
        return GTExWorkflowStep("download", "2. 下载 GTEx 原始文件", "blocked", False, "下载计划未包含公共表达文件 URL。", "下载 GTEx 原始文件", "download plan 为空")
    return GTExWorkflowStep("download", "2. 下载 GTEx 原始文件", "available", True, f"下载计划已就绪：{plan.get('file_count') or 0} 个候选文件。", "下载 GTEx 原始文件")


def _build_step(raw_record_path: Path | None, raw_summary: dict[str, Any], build_manifest_path: Path | None, manifest: dict[str, Any], build_summary: dict[str, Any]) -> GTExWorkflowStep:
    if build_manifest_path is not None:
        samples = manifest.get("sample_count") or build_summary.get("sample_count") or 0
        genes = manifest.get("gene_count") or build_summary.get("gene_count") or 0
        return GTExWorkflowStep("expression_build", "3. 构建 GTEx 表达矩阵", "completed", False, f"表达矩阵已构建：{samples} 个样本，{genes} 个基因；仅作为独立正常组织表达资源。")
    if raw_record_path is not None or int(raw_summary.get("acquired_count") or 0) > 0:
        return GTExWorkflowStep("expression_build", "3. 构建 GTEx 表达矩阵", "available", True, "已获取 GTEx 表达文件，可构建 expression/sample/donor/tissue metadata。", "构建 GTEx 表达矩阵")
    return GTExWorkflowStep("expression_build", "3. 构建 GTEx 表达矩阵", "blocked", False, "需要先成功下载 GTEx 表达文件。", "构建 GTEx 表达矩阵", "没有成功下载的 GTEx 表达文件")


def _data_check_step(build_manifest_path: Path | None, manifest: dict[str, Any]) -> GTExWorkflowStep:
    if build_manifest_path is None:
        return GTExWorkflowStep("data_check", "4. 进入数据检查与准备", "blocked", False, "需要先构建 GTEx 表达矩阵。", "进入数据检查与准备")
    return GTExWorkflowStep("data_check", "4. 进入数据检查与准备", "available", True, f"GTEx 构建产物可进入数据检查：{manifest.get('sample_count') or 0} 样本 / {manifest.get('gene_count') or 0} 基因。", "进入数据检查与准备")


def _manual_config_step(build_manifest_path: Path | None) -> GTExWorkflowStep:
    if build_manifest_path is None:
        return GTExWorkflowStep("manual_config", "5. 后续手动配置用途", "blocked", False, "完成数据检查后再配置展示或显式联合分析。")
    return GTExWorkflowStep("manual_config", "5. 后续手动配置用途", "available", False, "可用于表达展示、组织背景参考，或后续显式 TCGA+GTEx 联合配置；不会自动合并。")


def _gtex_records(root: Path | None, tissue_id: str | None) -> list[dict[str, Any]]:
    if root is None:
        return []
    records_dir = root / "acquisition" / "records"
    if not records_dir.exists():
        return []
    records = []
    for path in sorted(records_dir.glob("*.json"), key=lambda item: item.stat().st_mtime):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if not isinstance(metadata, dict) or str(metadata.get("source") or "") != "gtex":
            continue
        record_tissue = str(metadata.get("tissue_id") or payload.get("source_label") or "")
        if tissue_id and record_tissue and record_tissue != tissue_id:
            continue
        records.append({"record_path": str(path), "payload": payload, "metadata": metadata, "mtime": path.stat().st_mtime})
    return records


def _latest_raw_record(records: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = {"gtex_raw_files_acquired", "gtex_raw_files_acquired_with_warnings", "gtex_raw_file_download_failed", "gtex_download_plan_empty"}
    matches = [record for record in records if _download_status(record) in statuses]
    return matches[-1] if matches else {}


def _record_for_manifest(records: list[dict[str, Any]], manifest_path: Path | None) -> dict[str, Any]:
    if manifest_path is None:
        return {}
    target = str(manifest_path)
    for record in reversed(records):
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        if str(metadata.get("gtex_expression_build_manifest_path") or "") == target:
            return record
    return {}


def _latest_plan_path(root: Path | None, tissue_id: str | None) -> Path | None:
    if root is None:
        return None
    plans_dir = root / "acquisition" / "gtex_download_plans"
    if not plans_dir.exists():
        return None
    candidates = []
    for path in plans_dir.glob("*.json"):
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        plan_tissue = str(payload.get("tissue_id") or "")
        if tissue_id and plan_tissue and plan_tissue != tissue_id:
            continue
        candidates.append(path)
    return max(candidates, key=lambda item: item.stat().st_mtime) if candidates else latest_gtex_download_plan_path(root)


def _current_stage(steps: list[GTExWorkflowStep]) -> str:
    completed = [step.step_id for step in steps if step.status == "completed"]
    return completed[-1] if completed else next((step.step_id for step in steps if step.status == "available"), "preview")


def _highest_stage_record(records: list[dict[str, Any]]) -> dict[str, object]:
    order = {"gtex_expression_matrix_built": 4, "gtex_raw_files_acquired": 3, "gtex_raw_files_acquired_with_warnings": 3, "gtex_download_plan_draft_created": 2, "registered_pending_gtex_build": 1}
    best = max(records, key=lambda record: (order.get(_download_status(record), 0), float(record.get("mtime") or 0)), default={})
    metadata = best.get("metadata") if isinstance(best.get("metadata"), dict) else {}
    return {"record_path": str(best.get("record_path") or ""), "download_status": str(metadata.get("download_status") or ""), "tissue_id": str(metadata.get("tissue_id") or "")}


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
    if not plan:
        return []
    warnings = [str(item) for item in plan.get("warnings", []) or [] if str(item)]
    if int(plan.get("file_count") or 0) <= 0:
        warnings.append("当前 GTEx 下载计划没有公共表达文件 URL。")
    return warnings


def _raw_warnings(raw_record: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    warnings = []
    if int(summary.get("failed_count") or 0):
        warnings.append(f"GTEx 下载部分失败：{summary.get('failed_count')} 个文件。")
    if _download_status(raw_record) == "gtex_raw_file_download_failed":
        warnings.append("GTEx 原始文件下载失败，不能构建表达矩阵。")
    return warnings


def _build_warnings(manifest: dict[str, Any]) -> list[str]:
    return [str(item) for item in manifest.get("warnings", []) or [] if str(item)] if isinstance(manifest, dict) else []


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


__all__ = ["GTExWorkflowState", "GTExWorkflowStep", "build_gtex_workflow_state"]
