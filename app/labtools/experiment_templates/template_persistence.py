from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.labtools.experiment_templates.template_models import (
    EXPERIMENT_TEMPLATE_REVIEW_NOTICE,
    EXPERIMENT_TEMPLATE_SCHEMA_VERSION,
    TEMPLATE_STATUS,
    ExperimentRecordDraft,
    ExperimentTemplateError,
)


LABTOOLS_EXPERIMENT_RECORD_DRAFT_STORE_SCHEMA_VERSION = "labtools_experiment_record_draft_store.v1"
EXPERIMENT_RECORD_DRAFT_EXPORT_TYPE = "labtools_experiment_record_draft_store"
SOFTWARE_CHANNEL = "Developer Preview / testing"
EXPERIMENT_RECORD_DRAFT_REVIEW_STATUS = "manual_review_required"
EXPERIMENT_RECORD_DRAFT_PERSISTENCE_NOTE = (
    "本地 JSON 仅保存用户生成的实验记录草稿；仅在用户明确选择路径后写盘，"
    "不自动保存、不写数据库、不联网、不调用 AI，不构成完整 ELN。"
)
EXPERIMENT_RECORD_DRAFT_SAFETY_NOTE = (
    "实验记录草稿仅用于常规科研实验整理。使用前需人工核对实验室 SOP、"
    "伦理/安全要求、试剂说明书和实验设计；不构成完整 ELN、临床、诊断、安全操作建议或正式实验记录。"
)
BLOCKED_TEMPLATE_SCOPE_TERMS = (
    "人体实验",
    "human subject",
    "动物实验",
    "animal protocol",
    "病毒包装",
    "viral packaging",
    "临床诊断",
    "clinical diagnosis",
    "治疗建议",
    "treatment recommendation",
    "高风险合成",
)


@dataclass(frozen=True)
class ExperimentDraftReview:
    status: str
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    review_notice: str = EXPERIMENT_RECORD_DRAFT_SAFETY_NOTE

    @property
    def allowed(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "review_notice": self.review_notice,
        }


@dataclass(frozen=True)
class ExperimentDraftStoreSaveResult:
    success: bool
    path: str
    schema_version: str
    draft_count: int
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    review_notice: str = EXPERIMENT_RECORD_DRAFT_SAFETY_NOTE

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "path": self.path,
            "schema_version": self.schema_version,
            "draft_count": self.draft_count,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "review_notice": self.review_notice,
        }


@dataclass(frozen=True)
class ExperimentDraftStoreLoadResult:
    success: bool
    path: str
    schema_version: str
    drafts: tuple[ExperimentRecordDraft, ...]
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    review_notice: str = EXPERIMENT_RECORD_DRAFT_SAFETY_NOTE

    @property
    def draft_count(self) -> int:
        return len(self.drafts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "path": self.path,
            "schema_version": self.schema_version,
            "draft_count": self.draft_count,
            "drafts": [draft.to_dict() for draft in self.drafts],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "review_notice": self.review_notice,
        }


def evaluate_experiment_record_draft(draft: ExperimentRecordDraft) -> ExperimentDraftReview:
    _validate_draft(draft)
    haystack = _draft_text(draft).lower()
    matches = tuple(term for term in BLOCKED_TEMPLATE_SCOPE_TERMS if term.lower() in haystack)
    if matches:
        return ExperimentDraftReview(
            status="blocked_high_risk_scope",
            warnings=matches,
            errors=(
                "实验记录草稿包含人体/动物实验、病毒包装、临床诊断、治疗建议或高风险合成相关关键词；"
                "LabTools 不保存此类操作草稿。",
            ),
        )
    return ExperimentDraftReview(
        status=EXPERIMENT_RECORD_DRAFT_REVIEW_STATUS,
        warnings=("本地草稿保存前已完成基础范围检查；仍需人工核对 SOP、伦理/安全要求和实验设计。",),
    )


def build_experiment_draft_store_payload(drafts: tuple[ExperimentRecordDraft, ...]) -> dict[str, Any]:
    reviews = [evaluate_experiment_record_draft(draft).to_dict() for draft in drafts]
    return {
        "schema_version": LABTOOLS_EXPERIMENT_RECORD_DRAFT_STORE_SCHEMA_VERSION,
        "export_type": EXPERIMENT_RECORD_DRAFT_EXPORT_TYPE,
        "created_at": _utc_now(),
        "software_channel": SOFTWARE_CHANNEL,
        "review_status": EXPERIMENT_RECORD_DRAFT_REVIEW_STATUS,
        "draft_count": len(drafts),
        "drafts": [draft.to_dict() for draft in drafts],
        "draft_reviews": reviews,
        "source_schema_version": EXPERIMENT_TEMPLATE_SCHEMA_VERSION,
        "safety_note": EXPERIMENT_RECORD_DRAFT_SAFETY_NOTE,
        "persistence_note": EXPERIMENT_RECORD_DRAFT_PERSISTENCE_NOTE,
    }


def save_experiment_draft_store(
    drafts: tuple[ExperimentRecordDraft, ...],
    output_path: str | Path | None,
) -> ExperimentDraftStoreSaveResult:
    if not drafts:
        raise ExperimentTemplateError("尚未生成实验记录草稿，未写入任何文件。")
    path = _resolve_output_file(output_path)
    payload = build_experiment_draft_store_payload(drafts)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    except FileExistsError as exc:
        raise ExperimentTemplateError("保存目标文件已存在，已停止以避免覆盖。") from exc
    except OSError as exc:
        raise ExperimentTemplateError("无法写入实验记录草稿 JSON，请检查路径权限。") from exc
    return ExperimentDraftStoreSaveResult(
        success=True,
        path=str(path),
        schema_version=LABTOOLS_EXPERIMENT_RECORD_DRAFT_STORE_SCHEMA_VERSION,
        draft_count=len(drafts),
        warnings=("仅保存用户生成的记录草稿；未生成完整 ELN、正式 SOP、数据库记录或跨模块项目文件。",),
    )


def load_experiment_draft_store(input_path: str | Path | None) -> ExperimentDraftStoreLoadResult:
    path = _input_file(input_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExperimentTemplateError("实验记录草稿文件不是有效 JSON。") from exc
    except OSError as exc:
        raise ExperimentTemplateError("无法读取实验记录草稿 JSON。") from exc
    if payload.get("schema_version") != LABTOOLS_EXPERIMENT_RECORD_DRAFT_STORE_SCHEMA_VERSION:
        raise ExperimentTemplateError("实验记录草稿文件 schema 不匹配。")
    raw_drafts = payload.get("drafts")
    if not isinstance(raw_drafts, list):
        raise ExperimentTemplateError("实验记录草稿文件缺少 drafts 列表。")
    drafts = tuple(_draft_from_dict(item) for item in raw_drafts)
    for draft in drafts:
        review = evaluate_experiment_record_draft(draft)
        if not review.allowed:
            raise ExperimentTemplateError(review.errors[0])
    return ExperimentDraftStoreLoadResult(
        success=True,
        path=str(path),
        schema_version=LABTOOLS_EXPERIMENT_RECORD_DRAFT_STORE_SCHEMA_VERSION,
        drafts=drafts,
        warnings=("载入结果仍为本地结构化草稿；使用前需人工核对 SOP、伦理/安全要求和实验设计。",),
    )


def _draft_from_dict(payload: Any) -> ExperimentRecordDraft:
    if not isinstance(payload, dict):
        raise ExperimentTemplateError("drafts 列表包含无效记录。")
    draft = ExperimentRecordDraft(
        template_id=_required_text(payload, "template_id"),
        template_name=_required_text(payload, "template_name"),
        purpose=_required_text(payload, "purpose"),
        sample_groups=_required_text_tuple(payload, "sample_groups"),
        reagents=_required_text_tuple(payload, "reagents"),
        key_parameters=_required_text_tuple(payload, "key_parameters"),
        output_files=_required_text_tuple(payload, "output_files"),
        notes=_optional_text_tuple(payload, "notes"),
        status=str(payload.get("status") or TEMPLATE_STATUS),
        schema_version=str(payload.get("schema_version") or EXPERIMENT_TEMPLATE_SCHEMA_VERSION),
        review_notice=str(payload.get("review_notice") or EXPERIMENT_TEMPLATE_REVIEW_NOTICE),
        created_at=str(payload.get("created_at") or _utc_now()),
        draft_id=str(payload.get("draft_id") or ""),
    )
    _validate_draft(draft)
    return draft


def _validate_draft(draft: ExperimentRecordDraft) -> None:
    if draft.schema_version != EXPERIMENT_TEMPLATE_SCHEMA_VERSION:
        raise ExperimentTemplateError("实验记录草稿 schema 不匹配。")
    if draft.status != TEMPLATE_STATUS:
        raise ExperimentTemplateError("实验记录草稿状态必须为 draft_manual_review_required。")
    required_text_fields = (draft.template_id, draft.template_name, draft.purpose, draft.created_at, draft.draft_id)
    if any(not str(value).strip() for value in required_text_fields):
        raise ExperimentTemplateError("实验记录草稿缺少必要文本字段。")
    if not draft.sample_groups:
        raise ExperimentTemplateError("实验记录草稿缺少样本分组。")
    if not draft.reagents:
        raise ExperimentTemplateError("实验记录草稿缺少试剂/材料。")
    if not draft.key_parameters:
        raise ExperimentTemplateError("实验记录草稿缺少关键参数。")
    if not draft.output_files:
        raise ExperimentTemplateError("实验记录草稿缺少输出文件/记录。")
    if "人工复核" not in draft.review_notice:
        raise ExperimentTemplateError("实验记录草稿缺少人工复核提示。")


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise ExperimentTemplateError(f"实验记录草稿缺少 {key}。")
    return value


def _required_text_tuple(payload: dict[str, Any], key: str) -> tuple[str, ...]:
    values = _optional_text_tuple(payload, key)
    if not values:
        raise ExperimentTemplateError(f"实验记录草稿缺少 {key}。")
    return values


def _optional_text_tuple(payload: dict[str, Any], key: str) -> tuple[str, ...]:
    raw_values = payload.get(key) or ()
    if not isinstance(raw_values, list | tuple):
        raise ExperimentTemplateError(f"实验记录草稿字段 {key} 格式无效。")
    return tuple(str(value).strip() for value in raw_values if str(value).strip())


def _draft_text(draft: ExperimentRecordDraft) -> str:
    fields: list[str] = [
        draft.template_id,
        draft.template_name,
        draft.purpose,
        draft.review_notice,
    ]
    fields.extend(draft.sample_groups)
    fields.extend(draft.reagents)
    fields.extend(draft.key_parameters)
    fields.extend(draft.output_files)
    fields.extend(draft.notes)
    return "\n".join(fields)


def _resolve_output_file(output_path: str | Path | None) -> Path:
    if output_path is None or str(output_path).strip() == "":
        raise ExperimentTemplateError("请选择实验记录草稿保存路径。")
    requested = Path(output_path).expanduser()
    if requested.exists() and requested.is_dir():
        requested = requested / "labtools_experiment_record_drafts.json"
    if requested.suffix.lower() != ".json":
        requested = requested.with_suffix(".json")
    parent = requested.parent
    if not parent.exists() or not parent.is_dir():
        raise ExperimentTemplateError("保存路径所在文件夹不存在。")
    return _non_overwriting_path(requested)


def _input_file(input_path: str | Path | None) -> Path:
    if input_path is None or str(input_path).strip() == "":
        raise ExperimentTemplateError("请选择实验记录草稿 JSON 文件。")
    path = Path(input_path).expanduser()
    if not path.exists() or not path.is_file():
        raise ExperimentTemplateError("实验记录草稿 JSON 文件不存在。")
    return path


def _non_overwriting_path(path: Path) -> Path:
    safe_name = _sanitize_filename(path.stem)
    candidate = path.with_name(f"{safe_name}{path.suffix}")
    for index in range(1000):
        numbered = candidate if index == 0 else candidate.with_name(f"{safe_name}_{index:03d}{path.suffix}")
        if not numbered.exists():
            return numbered
    raise ExperimentTemplateError("保存目录中同名文件过多，请选择新的保存路径。")


def _sanitize_filename(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("._-")
    return sanitized[:96] or "labtools_experiment_record_drafts"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
