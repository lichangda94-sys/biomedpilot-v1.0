from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


EXPERIMENT_TEMPLATE_SCHEMA_VERSION = "labtools_experiment_template_draft.v1"
EXPERIMENT_TEMPLATE_REVIEW_NOTICE = (
    "实验模板仅为本地结构化草稿，使用前需结合实验室 SOP、伦理/安全要求、试剂说明书和人工复核；"
    "不构成完整 ELN、临床建议或正式操作规程。"
)
TEMPLATE_STATUS = "draft_manual_review_required"


class ExperimentTemplateError(ValueError):
    """User-facing experiment template validation error."""


@dataclass(frozen=True)
class ExperimentTemplate:
    template_id: str
    name: str
    category: str
    description: str
    purpose_prompt: str
    sample_group_fields: tuple[str, ...]
    reagent_fields: tuple[str, ...]
    key_parameter_fields: tuple[str, ...]
    output_file_fields: tuple[str, ...]
    note_fields: tuple[str, ...]
    safety_notes: tuple[str, ...]
    version: str = "2026.05-local-draft"
    review_notice: str = EXPERIMENT_TEMPLATE_REVIEW_NOTICE

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "purpose_prompt": self.purpose_prompt,
            "sample_group_fields": list(self.sample_group_fields),
            "reagent_fields": list(self.reagent_fields),
            "key_parameter_fields": list(self.key_parameter_fields),
            "output_file_fields": list(self.output_file_fields),
            "note_fields": list(self.note_fields),
            "safety_notes": list(self.safety_notes),
            "version": self.version,
            "review_notice": self.review_notice,
        }


@dataclass(frozen=True)
class ExperimentRecordDraft:
    template_id: str
    template_name: str
    purpose: str
    sample_groups: tuple[str, ...]
    reagents: tuple[str, ...]
    key_parameters: tuple[str, ...]
    output_files: tuple[str, ...]
    notes: tuple[str, ...] = ()
    status: str = TEMPLATE_STATUS
    schema_version: str = EXPERIMENT_TEMPLATE_SCHEMA_VERSION
    review_notice: str = EXPERIMENT_TEMPLATE_REVIEW_NOTICE
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat())
    draft_id: str = field(default_factory=lambda: f"experiment_draft_{uuid4().hex[:12]}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "draft_id": self.draft_id,
            "template_id": self.template_id,
            "template_name": self.template_name,
            "created_at": self.created_at,
            "status": self.status,
            "purpose": self.purpose,
            "sample_groups": list(self.sample_groups),
            "reagents": list(self.reagents),
            "key_parameters": list(self.key_parameters),
            "output_files": list(self.output_files),
            "notes": list(self.notes),
            "review_notice": self.review_notice,
        }
