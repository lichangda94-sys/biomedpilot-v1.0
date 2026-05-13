from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


EXCLUSION_CRITERIA_LIBRARY_SCHEMA_VERSION = "meta_exclusion_criteria_library.v1"
EXCLUSION_REASON_SCHEMA_VERSION = "meta_exclusion_reason.v1"
PRISMA_REASON_MAP_SCHEMA_VERSION = "meta_prisma_reason_map.v1"

TITLE_ABSTRACT_STAGE = "title_abstract"
FULL_TEXT_STAGE = "full_text"


@dataclass(frozen=True)
class ExclusionReason:
    reason_id: str
    code: str
    english_label: str
    chinese_label: str
    applies_to_stage: tuple[str, ...]
    prisma_reason: str
    enabled: bool = True
    built_in: bool = True
    custom: bool = False
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    schema_version: str = EXCLUSION_REASON_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["applies_to_stage"] = list(self.applies_to_stage)
        return payload


@dataclass(frozen=True)
class ExclusionCriteriaLibrary:
    project_id: str
    reasons: tuple[ExclusionReason, ...]
    status: str
    created_at: str
    updated_at: str
    selected_reason_codes: tuple[str, ...] = ()
    governance_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    schema_version: str = EXCLUSION_CRITERIA_LIBRARY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        enabled = [reason for reason in self.reasons if reason.enabled]
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "selected_reason_codes": list(self.selected_reason_codes),
            "governance_refs": list(self.governance_refs),
            "audit_refs": list(self.audit_refs),
            "reason_count": len(self.reasons),
            "enabled_reason_count": len(enabled),
            "reasons": [reason.to_dict() for reason in self.reasons],
            "prisma_reason_map": {
                "schema_version": PRISMA_REASON_MAP_SCHEMA_VERSION,
                "mappings": {reason.code: reason.prisma_reason for reason in enabled},
            },
            "testing_note": "Exclusion criteria guide reviewer decisions; they do not automatically exclude records.",
        }


class ExclusionCriteriaLibraryService:
    def __init__(
        self,
        *,
        audit_log: MetaAuditLogService | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
    ) -> None:
        self._audit_log = audit_log or MetaAuditLogService()
        self._governance = research_governance or MetaResearchGovernanceService(audit_log=self._audit_log)

    def library_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "criteria" / "exclusion_criteria_library_v1.json"

    def prisma_reason_map_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "criteria" / "prisma_reason_map_v1.json"

    def load_library(self, project_dir: Path) -> ExclusionCriteriaLibrary | None:
        payload = _load_json(self.library_path(project_dir))
        if not payload:
            return None
        return _library_from_payload(payload)

    def build_default_library(
        self,
        project_dir: Path,
        *,
        selected_reason_codes: tuple[str, ...] | list[str] | None = None,
        custom_reasons: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (),
        status: str = "draft",
    ) -> ExclusionCriteriaLibrary:
        project_dir = project_dir.expanduser().resolve()
        now = _now()
        selected = tuple(selected_reason_codes or tuple(reason.code for reason in DEFAULT_EXCLUSION_REASONS))
        custom = tuple(_custom_reason(item, index=index, now=now) for index, item in enumerate(custom_reasons))
        reasons = tuple(
            _set_enabled(reason, reason.code in selected)
            for reason in (*DEFAULT_EXCLUSION_REASONS, *custom)
        )
        return ExclusionCriteriaLibrary(
            project_id=project_dir.name,
            reasons=reasons,
            status=status,
            created_at=now,
            updated_at=now,
            selected_reason_codes=selected,
        )

    def save_library(
        self,
        project_dir: Path,
        *,
        selected_reason_codes: tuple[str, ...] | list[str] | None = None,
        custom_reasons: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (),
        actor: str = "system",
        confirm: bool = False,
    ) -> ExclusionCriteriaLibrary:
        project_dir = project_dir.expanduser().resolve()
        previous = self.load_library(project_dir)
        status = "confirmed" if confirm else "draft_needs_review"
        library = self.build_default_library(
            project_dir,
            selected_reason_codes=selected_reason_codes,
            custom_reasons=custom_reasons,
            status=status,
        )
        self._write_library(project_dir, library)
        self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=library.project_id,
            actor=actor,
            target_type="exclusion_criteria_library",
            target_id="exclusion_criteria_library_v1",
            source_path="criteria/default_exclusion_criteria",
            output_path=str(self.library_path(project_dir).relative_to(project_dir)),
            summary="Exclusion criteria library saved.",
            details={"status": status, "enabled_reason_count": len([reason for reason in library.reasons if reason.enabled])},
        )
        if confirm:
            self._governance.record_user_confirmation(
                project_dir,
                project_id=library.project_id,
                action="confirm",
                actor=actor,
                target_type="exclusion_criteria_library",
                target_id="exclusion_criteria_library_v1",
                before=previous.to_dict() if previous else {},
                after=library.to_dict(),
                metadata={"reason_count": len(library.reasons)},
            )
        else:
            self._governance.record_draft_created(
                project_dir,
                project_id=library.project_id,
                actor=actor,
                target_type="exclusion_criteria_library",
                target_id="exclusion_criteria_library_v1",
                after=library.to_dict(),
                metadata={"reason_count": len(library.reasons)},
            )
        return library

    def add_custom_reason(
        self,
        project_dir: Path,
        *,
        english_label: str,
        chinese_label: str,
        prisma_reason: str,
        applies_to_stage: tuple[str, ...] | list[str] = (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE),
        actor: str = "reviewer",
        confirm: bool = False,
    ) -> ExclusionCriteriaLibrary:
        existing = self.load_library(project_dir)
        selected = [reason.code for reason in existing.reasons if reason.enabled] if existing else [reason.code for reason in DEFAULT_EXCLUSION_REASONS]
        custom_payloads = [
            {
                "english_label": reason.english_label,
                "chinese_label": reason.chinese_label,
                "prisma_reason": reason.prisma_reason,
                "applies_to_stage": list(reason.applies_to_stage),
                "code": reason.code,
            }
            for reason in (existing.reasons if existing else ())
            if reason.custom
        ]
        code = _code(english_label)
        selected.append(code)
        custom_payloads.append(
            {
                "code": code,
                "english_label": english_label,
                "chinese_label": chinese_label,
                "prisma_reason": prisma_reason,
                "applies_to_stage": list(applies_to_stage),
            }
        )
        return self.save_library(project_dir, selected_reason_codes=tuple(dict.fromkeys(selected)), custom_reasons=tuple(custom_payloads), actor=actor, confirm=confirm)

    def list_reasons(self, project_dir: Path, *, stage: str = "", enabled_only: bool = True) -> tuple[ExclusionReason, ...]:
        library = self.load_library(project_dir)
        reasons = library.reasons if library else DEFAULT_EXCLUSION_REASONS
        if enabled_only:
            reasons = tuple(reason for reason in reasons if reason.enabled)
        if stage:
            reasons = tuple(reason for reason in reasons if stage in reason.applies_to_stage)
        return tuple(reasons)

    def validate_reason(self, project_dir: Path, *, reason_code: str, stage: str) -> tuple[bool, str]:
        normalized = _code(reason_code)
        for reason in self.list_reasons(project_dir, enabled_only=True):
            if normalized in {reason.code, _code(reason.english_label), _code(reason.chinese_label)}:
                if stage not in reason.applies_to_stage:
                    return False, "exclusion_reason_not_available_for_stage"
                return True, ""
        return False, "unsupported_exclusion_reason"

    def prisma_reason_for_code(self, project_dir: Path, reason_code: str) -> str:
        normalized = _code(reason_code)
        for reason in self.list_reasons(project_dir, enabled_only=True):
            if normalized in {reason.code, _code(reason.english_label), _code(reason.chinese_label)}:
                return reason.prisma_reason
        return reason_code.strip()

    def count_prisma_reasons(self, project_dir: Path, decision_records: list[dict[str, Any]] | tuple[dict[str, Any], ...], *, stage: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in decision_records:
            decision = str(record.get("decision") or record.get("v2_decision") or "").lower()
            if decision not in {"exclude", "excluded", "missing_full_text", "ineligible"}:
                continue
            reason_code = str(record.get("exclusion_reason_code") or record.get("exclusion_reason") or record.get("exclusion_reason_text") or "").strip()
            ok, _message = self.validate_reason(project_dir, reason_code=reason_code, stage=stage)
            reason = self.prisma_reason_for_code(project_dir, reason_code) if ok else (reason_code or "unspecified")
            counts[reason] = counts.get(reason, 0) + 1
        return counts

    def _write_library(self, project_dir: Path, library: ExclusionCriteriaLibrary) -> None:
        _write_json(self.library_path(project_dir), library.to_dict())
        _write_json(self.prisma_reason_map_path(project_dir), library.to_dict()["prisma_reason_map"])


DEFAULT_EXCLUSION_REASONS = (
    ExclusionReason("exreason-review", "review", "Review", "综述", (TITLE_ABSTRACT_STAGE,), "not_original_research"),
    ExclusionReason("exreason-meta-analysis", "meta_analysis", "Meta-analysis", "Meta 分析", (TITLE_ABSTRACT_STAGE,), "not_original_research"),
    ExclusionReason("exreason-conference-abstract", "conference_abstract", "Conference abstract", "会议摘要", (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE), "conference_abstract"),
    ExclusionReason("exreason-editorial", "editorial", "Editorial", "社论", (TITLE_ABSTRACT_STAGE,), "not_original_research"),
    ExclusionReason("exreason-letter", "letter", "Letter", "来信", (TITLE_ABSTRACT_STAGE,), "not_original_research"),
    ExclusionReason("exreason-comment", "comment", "Comment", "评论", (TITLE_ABSTRACT_STAGE,), "not_original_research"),
    ExclusionReason("exreason-case-report", "case_report", "Case report", "病例报告", (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE), "case_report"),
    ExclusionReason("exreason-animal-study", "animal_study", "Animal study", "动物研究", (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE), "animal_or_cell_study"),
    ExclusionReason("exreason-cell-study", "cell_study", "Cell study", "细胞研究", (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE), "animal_or_cell_study"),
    ExclusionReason("exreason-non-original", "non_original_article", "Non-original article", "非原始研究", (TITLE_ABSTRACT_STAGE,), "not_original_research"),
    ExclusionReason("exreason-wrong-population", "wrong_population", "Wrong population", "研究对象不符", (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE), "wrong_population"),
    ExclusionReason("exreason-wrong-intervention", "wrong_intervention_exposure", "Wrong intervention / exposure", "干预或暴露不符", (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE), "wrong_intervention_or_exposure"),
    ExclusionReason("exreason-wrong-comparator", "wrong_comparator", "Wrong comparator", "对照不符", (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE), "wrong_comparator"),
    ExclusionReason("exreason-wrong-outcome", "wrong_outcome", "Wrong outcome", "结局不符", (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE), "wrong_outcome"),
    ExclusionReason("exreason-insufficient-data", "insufficient_data", "Insufficient data", "数据不足", (FULL_TEXT_STAGE,), "insufficient_data"),
    ExclusionReason("exreason-fulltext-unavailable", "full_text_unavailable", "Full text unavailable", "全文不可得", (FULL_TEXT_STAGE,), "full_text_unavailable"),
    ExclusionReason("exreason-duplicate-publication", "duplicate_publication", "Duplicate publication", "重复发表", (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE), "duplicate_publication"),
    ExclusionReason("exreason-non-target-language", "non_target_language", "Non-English / 非目标语言", "非目标语言", (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE), "language"),
    ExclusionReason("exreason-protocol-only", "protocol_only", "Protocol only", "仅方案", (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE), "protocol_only"),
    ExclusionReason("exreason-preprint-only", "preprint_only", "Preprint only", "仅预印本", (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE), "preprint_only"),
)


def _set_enabled(reason: ExclusionReason, enabled: bool) -> ExclusionReason:
    return ExclusionReason(**{**reason.to_dict(), "enabled": enabled, "applies_to_stage": tuple(reason.applies_to_stage)})


def _custom_reason(payload: dict[str, Any], *, index: int, now: str) -> ExclusionReason:
    english = str(payload.get("english_label") or payload.get("label") or "").strip()
    if not english:
        raise ValueError("custom_exclusion_reason_english_label_required")
    chinese = str(payload.get("chinese_label") or english).strip()
    prisma_reason = str(payload.get("prisma_reason") or _code(english)).strip()
    code = _code(str(payload.get("code") or english))
    stages = tuple(str(item) for item in payload.get("applies_to_stage", (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE)) if str(item).strip())
    return ExclusionReason(
        reason_id=f"exreason-custom-{index + 1:02d}-{code[:40]}",
        code=code,
        english_label=english,
        chinese_label=chinese,
        applies_to_stage=stages or (TITLE_ABSTRACT_STAGE, FULL_TEXT_STAGE),
        prisma_reason=prisma_reason,
        built_in=False,
        custom=True,
        created_at=now,
        updated_at=now,
    )


def _library_from_payload(payload: dict[str, Any]) -> ExclusionCriteriaLibrary:
    return ExclusionCriteriaLibrary(
        project_id=str(payload.get("project_id", "")),
        reasons=tuple(_reason_from_payload(item) for item in payload.get("reasons", []) if isinstance(item, dict)),
        status=str(payload.get("status", "draft_needs_review")),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
        selected_reason_codes=tuple(str(item) for item in payload.get("selected_reason_codes", []) if str(item).strip()),
        governance_refs=tuple(str(item) for item in payload.get("governance_refs", []) if str(item).strip()),
        audit_refs=tuple(str(item) for item in payload.get("audit_refs", []) if str(item).strip()),
        schema_version=str(payload.get("schema_version", EXCLUSION_CRITERIA_LIBRARY_SCHEMA_VERSION)),
    )


def _reason_from_payload(payload: dict[str, Any]) -> ExclusionReason:
    return ExclusionReason(
        reason_id=str(payload.get("reason_id", "")),
        code=str(payload.get("code", "")),
        english_label=str(payload.get("english_label", "")),
        chinese_label=str(payload.get("chinese_label", "")),
        applies_to_stage=tuple(str(item) for item in payload.get("applies_to_stage", []) if str(item).strip()),
        prisma_reason=str(payload.get("prisma_reason", "")),
        enabled=bool(payload.get("enabled", True)),
        built_in=bool(payload.get("built_in", True)),
        custom=bool(payload.get("custom", False)),
        notes=str(payload.get("notes", "")),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
        schema_version=str(payload.get("schema_version", EXCLUSION_REASON_SCHEMA_VERSION)),
    )


def _code(value: str) -> str:
    return "_".join(value.lower().replace("/", " ").replace("-", " ").split())


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
