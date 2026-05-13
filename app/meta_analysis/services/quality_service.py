from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.extraction.schema_registry import get_extraction_schema_profile
from app.meta_analysis.models.systematic_review import (
    QualityAssessment,
    new_quality_assessment_id,
    now_utc,
    quality_assessment_from_dict,
    quality_assessment_to_dict,
)
from app.meta_analysis.quality.tool_registry import get_quality_tool, list_quality_tools
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.project_contract_service import MetaProjectContractService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


QUALITY_TOOL_REGISTRY_V1_SCHEMA_VERSION = "meta_quality_tool_registry.v1"
QUALITY_ASSESSMENT_RECORD_V1_SCHEMA_VERSION = "meta_quality_assessment_record.v1"
QUALITY_ASSESSMENT_RECORDS_V1_SCHEMA_VERSION = "meta_quality_assessment_records.v1"
QUALITY_ASSESSMENT_SUMMARY_V1_SCHEMA_VERSION = "meta_quality_assessment_summary.v1"
GRADE_PLACEHOLDER_SCHEMA_VERSION = "meta_grade_summary_placeholder.v1"

QUALITY_ASSESSMENT_STATUSES = (
    "not_started",
    "draft",
    "suggested",
    "user_accepted",
    "user_edited",
    "confirmed",
    "rejected",
    "completed_by_user",
    "needs_review",
    "conflict_pending",
    "excluded_from_quality_assessment",
)
QUALITY_RATING_OPTIONS = ("low", "some_concerns", "high", "unclear", "not_applicable", "low_risk_or_good", "high_risk_or_poor", "not_assessed")
QUALITY_M6_GOVERNANCE_STATES = ("draft", "suggested", "user_accepted", "user_edited", "confirmed", "rejected")
NOS_TOOL_NAME = "NOS"
NOS_DOMAINS = ("selection", "comparability", "outcome_or_exposure")
NOS_DOMAIN_LABELS_ZH = {
    "selection": "选择",
    "comparability": "可比性",
    "outcome_or_exposure": "结局/暴露",
}
QUALITY_RATING_LABELS_ZH = {
    "low_risk_or_good": "低风险/较好",
    "unclear": "不明确",
    "high_risk_or_poor": "高风险/较差",
    "not_assessed": "未评价",
    "low": "低风险/较好",
    "some_concerns": "不明确",
    "high": "高风险/较差",
    "not_applicable": "未评价",
}
QUALITY_M6_STATE_LABELS_ZH = {
    "draft": "草稿",
    "suggested": "建议",
    "user_accepted": "用户接受",
    "user_edited": "用户编辑",
    "confirmed": "已确认",
    "rejected": "已拒绝",
}


@dataclass(frozen=True)
class QualityAssessmentV1Result:
    success: bool
    project_id: str
    assessment_id: str
    output_path: str
    summary_path: str
    message: str
    record: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)


class QualityAssessmentService:
    def __init__(
        self,
        *,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        audit_log: MetaAuditLogService | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
        project_contract: MetaProjectContractService | None = None,
    ) -> None:
        self._task_center = task_center
        self._data_center = data_center
        self._audit_log = audit_log or MetaAuditLogService()
        self._governance = research_governance or MetaResearchGovernanceService(audit_log=self._audit_log)
        self._project_contract = project_contract

    def tool_registry_v1(self) -> dict[str, Any]:
        tools = []
        for tool in list_quality_tools():
            tools.append(
                {
                    "tool_name": tool.tool_name,
                    "domains": list(tool.domains),
                    "rating_options": list(tool.judgement_options),
                    "recommended_profiles": list(tool.recommended_profiles),
                    "output_summary_fields": list(tool.output_summary_fields),
                    "recommendation_status": "suggestion_only",
                    "auto_scores_final_quality": False,
                }
            )
        return {
            "schema_version": QUALITY_TOOL_REGISTRY_V1_SCHEMA_VERSION,
            "tool_count": len(tools),
            "tools": tools,
            "safety_note": "Quality tools are recommendation/form templates only; final ratings require reviewer action.",
        }

    def recommend_quality_tools(
        self,
        *,
        meta_type: str = "",
        study_design: str = "",
    ) -> list[dict[str, Any]]:
        normalized_meta = meta_type.strip()
        normalized_design = study_design.strip().lower()
        candidates: list[tuple[str, str]] = []
        profile = get_extraction_schema_profile(normalized_meta) if normalized_meta else None
        if profile is not None:
            candidates.extend((tool_name, "recommended_by_meta_type_profile") for tool_name in profile.recommended_quality_tools)
        candidates.extend((tool_name, "recommended_by_meta_type_registry") for tool_name in _tools_for_meta_type(normalized_meta))
        if "random" in normalized_design or "trial" in normalized_design or "rct" in normalized_design:
            candidates.append(("ROB2", "recommended_by_study_design"))
            candidates.append(("Cochrane RoB generic", "recommended_by_study_design"))
        if "non-random" in normalized_design or "observational" in normalized_design or "cohort" in normalized_design or "case-control" in normalized_design:
            candidates.append(("Newcastle-Ottawa Scale", "recommended_by_study_design"))
            candidates.append(("ROBINS-I", "recommended_by_study_design"))
        if "diagnostic" in normalized_design or "accuracy" in normalized_design:
            candidates.append(("QUADAS-2", "recommended_by_study_design"))
        if "cross-sectional" in normalized_design or "prevalence" in normalized_design:
            candidates.append(("JBI prevalence checklist", "recommended_by_study_design"))
            candidates.append(("AHRQ cross-sectional checklist", "recommended_by_study_design"))
        if not candidates:
            candidates.append(("Newcastle-Ottawa Scale", "fallback_suggestion"))
        suggestions: list[dict[str, Any]] = []
        seen: set[str] = set()
        for tool_name, reason in candidates:
            tool = get_quality_tool(tool_name)
            if tool is None or tool.tool_name in seen:
                continue
            seen.add(tool.tool_name)
            suggestions.append(
                {
                    "tool_name": tool.tool_name,
                    "reason": reason,
                    "status": "suggested",
                    "domains": list(tool.domains),
                    "rating_options": list(tool.judgement_options),
                    "requires_human_confirmation": True,
                    "auto_scores_final_quality": False,
                }
            )
        return suggestions

    def create_quality_assessment_draft(
        self,
        project_dir: Path,
        *,
        study_id: str,
        record_id: str,
        tool_name: str,
        domains: dict[str, str] | None = None,
        domain_notes: dict[str, str] | None = None,
        overall_rating: str = "",
        reviewer_id: str = "",
        notes: str = "",
        meta_type: str = "",
        study_design: str = "",
        actor: str = "reviewer",
        project_id: str | None = None,
        assessment_state: str = "draft",
    ) -> QualityAssessmentV1Result:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_id or project_dir.name
        tool = get_quality_tool(tool_name)
        if tool is None:
            raise ValueError("unsupported_quality_tool")
        assessment_state = _validate_quality_state(assessment_state)
        validation = self.validate_quality_assessment_model(
            tool_name=tool.tool_name,
            domains=dict(domains or {}),
            overall_rating=overall_rating,
            state=assessment_state,
        )
        now = now_utc()
        record = {
            "schema_version": QUALITY_ASSESSMENT_RECORD_V1_SCHEMA_VERSION,
            "assessment_id": new_quality_assessment_id(),
            "project_id": project_id,
            "study_id": study_id,
            "record_id": record_id,
            "tool_name": tool.tool_name,
            "meta_type": meta_type,
            "study_design": study_design,
            "domains": {str(key): _normalize_quality_rating(value) for key, value in dict(domains or {}).items()},
            "domain_notes": dict(domain_notes or {}),
            "overall_rating": _normalize_quality_rating(overall_rating) if overall_rating else "",
            "overall_judgement": _normalize_quality_rating(overall_rating) if overall_rating else "",
            "reviewer_id": reviewer_id,
            "notes": notes,
            "status": assessment_state,
            "confirmation_state": assessment_state,
            "grade_placeholder": self.grade_summary_placeholder(project_dir, outcome_id=study_id, actor=actor),
            "created_at": now,
            "updated_at": now,
            "governance_refs": [],
            "audit_refs": [],
            "analysis_ready_dataset_created": False,
            "statistics_run": False,
            "prisma_advanced": False,
            "safety_note": "Quality assessment draft requires reviewer completion; no automated final risk-of-bias or GRADE conclusion is generated.",
        }
        diagnostics = self._quality_record_diagnostics(record)
        diagnostics["m6_validation"] = validation
        record["diagnostics"] = diagnostics
        records = self.load_quality_assessment_records_v1(project_dir)
        records.append(record)
        output_path = self._records_v1_path(project_dir)
        _write_json(output_path, self._records_v1_payload(project_id, records))
        audit = self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=project_id,
            actor=actor,
            target_type="quality_assessment",
            target_id=record["assessment_id"],
            source_path=str(project_dir),
            output_path=str(output_path.relative_to(project_dir)),
            summary="Quality assessment draft saved.",
            details={"status": "draft", "tool_name": tool.tool_name, "auto_scores_final_quality": False},
        )
        if assessment_state == "suggested":
            governance = self._governance.record_suggestion_created(
                project_dir,
                project_id=project_id,
                actor=actor or "system",
                target_type="quality_assessment_score",
                target_id=record["assessment_id"],
                after=record,
                metadata={"tool_name": tool.tool_name, "status": assessment_state, "auto_grade": False},
            )
        else:
            governance = self._governance.record_draft_created(
                project_dir,
                project_id=project_id,
                actor=actor,
                target_type="quality_assessment_score",
                target_id=record["assessment_id"],
                after=record,
                metadata={"tool_name": tool.tool_name, "status": assessment_state, "auto_grade": False},
            )
        record["audit_refs"].append(audit.event_id)
        record["governance_refs"].append(governance.event_id)
        _write_json(output_path, self._records_v1_payload(project_id, records))
        summary_path = self.write_quality_summary_v1(project_dir)
        return QualityAssessmentV1Result(True, project_id, record["assessment_id"], str(output_path), str(summary_path), "Quality assessment draft saved.", record, diagnostics)

    def create_nos_assessment_draft(
        self,
        project_dir: Path,
        *,
        study_id: str,
        record_id: str,
        domains: dict[str, str] | None = None,
        domain_notes: dict[str, str] | None = None,
        overall_rating: str = "",
        reviewer_id: str = "",
        notes: str = "",
        actor: str = "reviewer",
        assessment_state: str = "draft",
    ) -> QualityAssessmentV1Result:
        domains = {domain: dict(domains or {}).get(domain, "not_assessed") for domain in NOS_DOMAINS}
        return self.create_quality_assessment_draft(
            project_dir,
            study_id=study_id,
            record_id=record_id,
            tool_name=NOS_TOOL_NAME,
            domains=domains,
            domain_notes=domain_notes,
            overall_rating=overall_rating or self.suggest_overall_judgement(NOS_TOOL_NAME, domains),
            reviewer_id=reviewer_id,
            notes=notes,
            actor=actor,
            assessment_state=assessment_state,
        )

    def update_quality_assessment_draft(
        self,
        project_dir: Path,
        *,
        assessment_id: str,
        updates: dict[str, Any],
        actor: str = "reviewer",
    ) -> QualityAssessmentV1Result:
        return self._update_quality_assessment_record(
            project_dir,
            assessment_id=assessment_id,
            updates=updates,
            status="draft",
            governance_action="edit",
            actor=actor,
            summary="Quality assessment draft edited.",
        )

    def complete_quality_assessment_by_user(
        self,
        project_dir: Path,
        *,
        assessment_id: str,
        actor: str = "reviewer",
    ) -> QualityAssessmentV1Result:
        return self._update_quality_assessment_record(
            project_dir,
            assessment_id=assessment_id,
            updates={"completed_by_user": True},
            status="completed_by_user",
            governance_action="confirm",
            actor=actor,
            summary="Quality assessment completed by user.",
        )

    def confirm_quality_assessment_by_user(
        self,
        project_dir: Path,
        *,
        assessment_id: str,
        actor: str = "reviewer",
    ) -> QualityAssessmentV1Result:
        return self._update_quality_assessment_record(
            project_dir,
            assessment_id=assessment_id,
            updates={"completed_by_user": True, "confirmation_state": "confirmed"},
            status="confirmed",
            governance_action="confirm",
            actor=actor,
            summary="Quality assessment confirmed by user.",
        )

    def change_quality_assessment_state(
        self,
        project_dir: Path,
        *,
        assessment_id: str,
        state: str,
        actor: str = "reviewer",
    ) -> QualityAssessmentV1Result:
        state = _validate_quality_state(state)
        action = "reject" if state == "rejected" else "accept" if state == "user_accepted" else "edit"
        return self._update_quality_assessment_record(
            project_dir,
            assessment_id=assessment_id,
            updates={"confirmation_state": state},
            status=state,
            governance_action=action,
            actor=actor,
            summary=f"Quality assessment state changed to {state}.",
        )

    def load_quality_assessment_records_v1(self, project_dir: Path) -> list[dict[str, Any]]:
        payload = _load_json(self._records_v1_path(project_dir.expanduser().resolve()))
        rows = payload.get("quality_assessment_records", []) if isinstance(payload, dict) else []
        return [dict(item) for item in rows if isinstance(item, dict)] if isinstance(rows, list) else []

    def write_quality_summary_v1(self, project_dir: Path) -> Path:
        project_dir = project_dir.expanduser().resolve()
        records = self.load_quality_assessment_records_v1(project_dir)
        by_tool: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_rating: dict[str, int] = {}
        for record in records:
            tool = str(record.get("tool_name", ""))
            status = str(record.get("status", ""))
            rating = str(record.get("overall_rating", ""))
            by_tool[tool] = by_tool.get(tool, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
            if rating:
                by_rating[rating] = by_rating.get(rating, 0) + 1
        summary = {
            "schema_version": QUALITY_ASSESSMENT_SUMMARY_V1_SCHEMA_VERSION,
            "project_id": project_dir.name,
            "assessment_count": len(records),
            "completed_by_user_count": by_status.get("completed_by_user", 0),
            "by_tool": by_tool,
            "by_status": by_status,
            "by_overall_rating": by_rating,
            "grade_status": "placeholder_only_no_auto_grade",
            "analysis_ready_dataset_created": False,
            "statistics_run": False,
            "prisma_advanced": False,
            "report_note": "Quality ratings are reviewer-entered or reviewer-confirmed. GRADE is placeholder only.",
            "m6_summary": self.quality_m6_summary(project_dir),
        }
        path = project_dir / "quality" / "quality_assessment_summary_v1.json"
        _write_json(path, summary)
        return path

    def quality_m6_summary(self, project_dir: Path, *, expected_study_ids: list[str] | None = None) -> dict[str, int]:
        records = self.load_quality_assessment_records_v1(project_dir)
        expected = set(expected_study_ids or _quality_expected_study_ids(project_dir))
        assessed_studies = {str(record.get("study_id", "")) for record in records if str(record.get("study_id", "")).strip()}
        draft_studies = {
            str(record.get("study_id", ""))
            for record in records
            if str(record.get("status", "")) in {"draft", "suggested", "user_accepted", "user_edited", "rejected", "needs_review", "conflict_pending"}
        }
        confirmed_studies = {
            str(record.get("study_id", ""))
            for record in records
            if str(record.get("status", "")) in {"confirmed", "completed_by_user"}
        }
        ratings = [_quality_summary_bucket(str(record.get("overall_rating") or record.get("overall_judgement") or "")) for record in records if str(record.get("status", "")) in {"confirmed", "completed_by_user"}]
        return {
            "studies_pending_quality": len(expected - assessed_studies) if expected else 0,
            "studies_with_draft_quality": len({item for item in draft_studies if item}),
            "studies_with_confirmed_quality": len({item for item in confirmed_studies if item}),
            "low_risk_or_good": ratings.count("low_risk_or_good"),
            "unclear": ratings.count("unclear"),
            "high_risk_or_poor": ratings.count("high_risk_or_poor"),
        }

    def validate_quality_assessment_model(
        self,
        *,
        tool_name: str,
        domains: dict[str, str],
        overall_rating: str = "",
        state: str = "draft",
    ) -> dict[str, Any]:
        tool = get_quality_tool(tool_name)
        errors: list[str] = []
        warnings: list[str] = []
        if tool is None:
            errors.append("unsupported_quality_tool")
            domains_expected: tuple[str, ...] = ()
        else:
            domains_expected = tuple(tool.domains)
        state = _validate_quality_state(state)
        normalized_domains = {str(key): _normalize_quality_rating(value) for key, value in dict(domains or {}).items()}
        unknown_domains = sorted(set(normalized_domains) - set(domains_expected))
        if unknown_domains:
            errors.append(f"unsupported_quality_domain:{','.join(unknown_domains)}")
        invalid_ratings = [key for key, value in normalized_domains.items() if value not in QUALITY_RATING_OPTIONS]
        if invalid_ratings:
            errors.append(f"unsupported_quality_rating:{','.join(invalid_ratings)}")
        if tool_name == NOS_TOOL_NAME:
            missing_nos = [domain for domain in NOS_DOMAINS if domain not in normalized_domains]
            if missing_nos and state == "confirmed":
                errors.append(f"missing_nos_domain:{','.join(missing_nos)}")
            if missing_nos and state != "confirmed":
                warnings.append(f"missing_nos_domain:{','.join(missing_nos)}")
        normalized_overall = _normalize_quality_rating(overall_rating) if overall_rating else ""
        if normalized_overall and normalized_overall not in QUALITY_RATING_OPTIONS:
            errors.append("unsupported_overall_rating")
        if state == "confirmed" and not normalized_overall:
            errors.append("confirmed_quality_requires_overall_judgement")
        return {
            "validation_status": "invalid" if errors else "valid_with_warnings" if warnings else "valid",
            "errors": errors,
            "warnings": warnings,
            "state": state,
            "auto_quality_scoring": False,
            "official_scoring_claimed": False,
        }

    def quality_summary_for_report(self, project_dir: Path) -> dict[str, Any]:
        path = self.write_quality_summary_v1(project_dir)
        summary = _load_json(path)
        legacy = self.summarize_quality_assessments(project_dir)
        return {
            **summary,
            "legacy_assessment_count": legacy["assessment_count"],
            "legacy_by_tool": legacy["by_tool"],
            "reporting_status": "draft_testing",
        }

    def export_quality_assessments_v1_json(self, project_dir: Path) -> Path:
        project_dir = project_dir.expanduser().resolve()
        source = self._records_v1_path(project_dir)
        target = project_dir / "quality" / "quality_assessment_v1_export.json"
        if source.exists():
            shutil.copyfile(source, target)
        else:
            _write_json(target, self._records_v1_payload(project_dir.name, []))
        self._audit_log.record_event(
            project_dir,
            event_type="report_exported",
            project_id=project_dir.name,
            target_type="quality_assessment_export",
            target_id=target.name,
            source_path=str(source),
            output_path=str(target.relative_to(project_dir)),
            summary="Quality assessment v1 JSON exported.",
            details={"auto_grade": False, "statistics_run": False},
        )
        return target

    def export_quality_assessments_v1_csv(self, project_dir: Path) -> Path:
        project_dir = project_dir.expanduser().resolve()
        records = self.load_quality_assessment_records_v1(project_dir)
        path = project_dir / "exports" / "quality_assessment_v1.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        domain_names = sorted({domain for record in records for domain in dict(record.get("domains", {})).keys()})
        fieldnames = ["assessment_id", "study_id", "record_id", "tool_name", "status", "overall_rating", "reviewer_id", *domain_names, "notes"]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                row = {key: record.get(key, "") for key in ("assessment_id", "study_id", "record_id", "tool_name", "status", "overall_rating", "reviewer_id", "notes")}
                row.update(dict(record.get("domains", {})))
                writer.writerow(row)
        self._audit_log.record_event(
            project_dir,
            event_type="report_exported",
            project_id=project_dir.name,
            target_type="quality_assessment_table",
            target_id=path.name,
            source_path=str(self._records_v1_path(project_dir)),
            output_path=str(path.relative_to(project_dir)),
            summary="Quality assessment v1 CSV exported.",
            details={"assessment_count": len(records), "auto_grade": False},
        )
        return path

    def grade_summary_placeholder(self, project_dir: Path, *, outcome_id: str = "", actor: str = "system") -> dict[str, Any]:
        return {
            "schema_version": GRADE_PLACEHOLDER_SCHEMA_VERSION,
            "project_id": project_dir.expanduser().resolve().name,
            "outcome_id": outcome_id,
            "status": "placeholder_only",
            "certainty": "not_assessed",
            "domains": {
                "risk_of_bias": "not_assessed",
                "inconsistency": "not_assessed",
                "indirectness": "not_assessed",
                "imprecision": "not_assessed",
                "publication_bias": "not_assessed",
            },
            "created_by": actor,
            "auto_grade_generated": False,
            "safety_note": "GRADE summary is a placeholder draft; certainty must be judged by the reviewer.",
        }

    def create_quality_assessment(
        self,
        *,
        project_id: str,
        study_id: str,
        record_id: str,
        tool_name: str,
        domains: dict[str, str],
        overall_judgement: str,
        reviewer_id: str,
        notes: str = "",
        domain_notes: dict[str, str] | None = None,
    ) -> QualityAssessment:
        if get_quality_tool(tool_name) is None:
            raise ValueError("unsupported_quality_tool")
        return QualityAssessment(
            assessment_id=new_quality_assessment_id(),
            project_id=project_id,
            study_id=study_id,
            record_id=record_id,
            tool_name=tool_name,
            domains=dict(domains),
            overall_judgement=overall_judgement,
            reviewer_id=reviewer_id,
            notes=notes,
            created_at=now_utc(),
            domain_notes=dict(domain_notes or {}),
        )

    def save_quality_assessment(self, project_dir: Path, assessment: QualityAssessment) -> Path:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(project_id=assessment.project_id, task_type=TaskType.QUALITY_ASSESSMENT_SAVE, title="Quality Assessment Save")
        assessments = [existing for existing in self.load_quality_assessments(project_dir) if existing.assessment_id != assessment.assessment_id]
        assessments.append(assessment)
        output_path = self._assessments_path(project_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"project_id": assessment.project_id, "quality_assessments": [quality_assessment_to_dict(item) for item in assessments]}
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._register_asset(project_id=assessment.project_id, data_type="quality_assessments", source_path=str(project_dir), output_path=str(output_path))
        self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=assessment.project_id,
            target_type="quality_assessment",
            target_id=assessment.assessment_id,
            source_path=str(project_dir),
            output_path=str(output_path),
            summary=f"Quality assessment saved with {assessment.tool_name}.",
            details={"study_id": assessment.study_id, "record_id": assessment.record_id, "overall_judgement": assessment.overall_judgement},
        )
        if self._project_contract is not None:
            self._project_contract.write_project_manifests(project_dir)
        self._finish_task(task, success=True, summary=f"Quality assessment saved: {assessment.assessment_id}")
        return output_path

    def load_quality_assessments(self, project_dir: Path) -> list[QualityAssessment]:
        path = self._assessments_path(project_dir.expanduser().resolve())
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [quality_assessment_from_dict(item) for item in payload.get("quality_assessments", [])]

    def summarize_quality_assessments(self, project_dir: Path) -> dict[str, object]:
        assessments = self.load_quality_assessments(project_dir)
        by_tool: dict[str, int] = {}
        by_overall: dict[str, int] = {}
        for assessment in assessments:
            by_tool[assessment.tool_name] = by_tool.get(assessment.tool_name, 0) + 1
            by_overall[assessment.overall_judgement] = by_overall.get(assessment.overall_judgement, 0) + 1
        return {"assessment_count": len(assessments), "by_tool": by_tool, "by_overall_judgement": by_overall}

    def quality_form_metadata(self, tool_name: str) -> dict[str, object]:
        tool = get_quality_tool(tool_name)
        if tool is None:
            raise ValueError("unsupported_quality_tool")
        return {
            "tool_name": tool.tool_name,
            "domains": list(tool.domains),
            "judgement_options": list(tool.judgement_options),
            "domain_note_fields": [f"{domain}_note" for domain in tool.domains],
            "recommended_profiles": list(tool.recommended_profiles),
            "output_summary_fields": list(tool.output_summary_fields),
        }

    def suggest_overall_judgement(self, tool_name: str, domains: dict[str, str]) -> str:
        if get_quality_tool(tool_name) is None:
            raise ValueError("unsupported_quality_tool")
        values = {str(value).lower() for value in domains.values()}
        if any(value in {"high", "high risk", "very serious", "no"} for value in values):
            return "high risk"
        if any(value in {"moderate risk", "some concerns", "some_concerns", "unclear", "serious"} for value in values):
            return "some concerns"
        if values and all(value in {"low", "low risk", "yes", "not serious"} for value in values):
            return "low risk"
        return "unclear"

    def quality_completeness_summary(self, project_dir: Path, *, expected_study_ids: list[str] | None = None) -> dict[str, object]:
        assessments = self.load_quality_assessments(project_dir)
        expected = set(expected_study_ids or [assessment.study_id for assessment in assessments])
        assessed = {assessment.study_id for assessment in assessments}
        missing = sorted(expected - assessed)
        return {
            "expected_study_count": len(expected),
            "assessed_study_count": len(assessed),
            "missing_study_ids": missing,
            "completeness_score": 1.0 if not expected else len(assessed & expected) / len(expected),
        }

    def recommended_tool_for_study(self, *, study_design: str = "", profile_type: str = "") -> str:
        profile = get_extraction_schema_profile(profile_type) if profile_type else None
        if profile is not None and profile.recommended_quality_tools:
            return profile.recommended_quality_tools[0]
        normalized = study_design.strip().lower()
        if "random" in normalized or "trial" in normalized:
            return "RoB2 simplified"
        if "diagnostic" in normalized or "accuracy" in normalized:
            return "QUADAS-2"
        if "cohort" in normalized or "case-control" in normalized or "observational" in normalized:
            return "NOS"
        suggestions = self.recommend_quality_tools(meta_type=profile_type, study_design=study_design)
        if suggestions:
            return str(suggestions[0]["tool_name"])
        return "NOS"

    def export_quality_table_csv(self, project_dir: Path) -> Path:
        project_dir = project_dir.expanduser().resolve()
        assessments = self.load_quality_assessments(project_dir)
        task = self._start_task(project_id=project_dir.name, task_type=TaskType.QUALITY_ASSESSMENT_EXPORT, title="Quality Assessment Export")
        output_path = project_dir / "exports" / "quality_assessment_table.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        domain_names = sorted({domain for assessment in assessments for domain in assessment.domains})
        fieldnames = ["assessment_id", "study_id", "record_id", "tool_name", "overall_judgement", "reviewer_id", *domain_names, "notes", "created_at"]
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for assessment in assessments:
                row = {
                    "assessment_id": assessment.assessment_id,
                    "study_id": assessment.study_id,
                    "record_id": assessment.record_id,
                    "tool_name": assessment.tool_name,
                    "overall_judgement": assessment.overall_judgement,
                    "reviewer_id": assessment.reviewer_id,
                    "notes": assessment.notes,
                    "created_at": assessment.created_at,
                }
                row.update(assessment.domains)
                writer.writerow(row)
        self._register_asset(project_id=project_dir.name, data_type="quality_assessment_table", source_path=str(self._assessments_path(project_dir)), output_path=str(output_path))
        self._audit_log.record_event(
            project_dir,
            event_type="report_exported",
            project_id=project_dir.name,
            target_type="quality_assessment_table",
            target_id=output_path.name,
            source_path=str(self._assessments_path(project_dir)),
            output_path=str(output_path),
            summary="Quality assessment table exported.",
            details={"assessment_count": len(assessments)},
        )
        if self._project_contract is not None:
            self._project_contract.write_project_manifests(project_dir)
        self._finish_task(task, success=True, summary=f"Quality assessment table exported: {output_path}")
        return output_path

    def export_quality_summary_markdown(self, project_dir: Path, *, expected_study_ids: list[str] | None = None) -> Path:
        project_dir = project_dir.expanduser().resolve()
        summary = self.summarize_quality_assessments(project_dir)
        completeness = self.quality_completeness_summary(project_dir, expected_study_ids=expected_study_ids)
        output_path = project_dir / "quality" / "quality_summary.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Quality Assessment Summary",
            "",
            "Status: Developer Preview / testing",
            f"Assessments: {summary['assessment_count']}",
            f"By tool: {summary['by_tool']}",
            f"By overall judgement: {summary['by_overall_judgement']}",
            "",
            "## Completeness",
            f"- Expected studies: {completeness['expected_study_count']}",
            f"- Assessed studies: {completeness['assessed_study_count']}",
            f"- Missing study IDs: {', '.join(completeness['missing_study_ids']) if completeness['missing_study_ids'] else 'none'}",
            f"- Completeness score: {completeness['completeness_score']}",
            "",
            "## Testing limitation",
            "Quality tools are testing form templates and do not replace reviewer judgement.",
            "",
        ]
        output_path.write_text("\n".join(lines), encoding="utf-8")
        self._register_asset(project_id=project_dir.name, data_type="quality_summary", source_path=str(self._assessments_path(project_dir)), output_path=str(output_path))
        self._audit_log.record_event(
            project_dir,
            event_type="report_exported",
            project_id=project_dir.name,
            target_type="quality_summary",
            target_id=output_path.name,
            source_path=str(self._assessments_path(project_dir)),
            output_path=str(output_path),
            summary="Quality summary markdown exported.",
            details={"completeness_score": completeness["completeness_score"]},
        )
        if self._project_contract is not None:
            self._project_contract.write_project_manifests(project_dir)
        return output_path

    def export_quality_beta_outputs(self, project_dir: Path, *, expected_study_ids: list[str] | None = None) -> dict[str, str]:
        project_dir = project_dir.expanduser().resolve()
        assessments_path = self._assessments_path(project_dir)
        alias_assessment_path = project_dir / "quality" / "quality_assessment.json"
        alias_assessment_path.parent.mkdir(parents=True, exist_ok=True)
        if assessments_path.exists():
            shutil.copyfile(assessments_path, alias_assessment_path)
        else:
            alias_assessment_path.write_text(json.dumps({"project_id": project_dir.name, "quality_assessments": []}, ensure_ascii=False, indent=2), encoding="utf-8")
        table_path = self.export_quality_table_csv(project_dir)
        alias_table_path = project_dir / "quality" / "quality_table.csv"
        alias_table_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(table_path, alias_table_path)
        summary_path = self.export_quality_summary_markdown(project_dir, expected_study_ids=expected_study_ids)
        self._register_asset(project_id=project_dir.name, data_type="quality_assessment", source_path=str(assessments_path), output_path=str(alias_assessment_path))
        self._register_asset(project_id=project_dir.name, data_type="quality_table", source_path=str(table_path), output_path=str(alias_table_path))
        if self._project_contract is not None:
            self._project_contract.write_project_manifests(project_dir)
        return {
            "quality_assessment": str(alias_assessment_path),
            "quality_assessments": str(assessments_path),
            "quality_table": str(alias_table_path),
            "quality_assessment_table": str(table_path),
            "quality_summary": str(summary_path),
        }

    def list_quality_tools(self) -> list[str]:
        return [tool.tool_name for tool in list_quality_tools()]

    def _assessments_path(self, project_dir: Path) -> Path:
        return project_dir / "quality" / "quality_assessments.json"

    def _records_v1_path(self, project_dir: Path) -> Path:
        return project_dir / "quality" / "quality_assessment_records_v1.json"

    def _records_v1_payload(self, project_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "schema_version": QUALITY_ASSESSMENT_RECORDS_V1_SCHEMA_VERSION,
            "record_schema_version": QUALITY_ASSESSMENT_RECORD_V1_SCHEMA_VERSION,
            "project_id": project_id,
            "quality_assessment_records": records,
            "record_count": len(records),
            "analysis_ready_dataset_created": False,
            "statistics_run": False,
            "prisma_advanced": False,
        }

    def _quality_record_diagnostics(self, record: dict[str, Any]) -> dict[str, Any]:
        missing = []
        if not str(record.get("study_id", "")).strip():
            missing.append("study_id")
        if not str(record.get("record_id", "")).strip():
            missing.append("record_id")
        if not str(record.get("tool_name", "")).strip():
            missing.append("tool_name")
        invalid_domains = [
            key
            for key, value in dict(record.get("domains", {})).items()
            if value not in QUALITY_RATING_OPTIONS and value not in {"low risk", "moderate risk", "high risk", "yes", "no", "not assessed", "not_assessed", "draft_note_only"}
        ]
        return {
            "missing_required_fields": missing,
            "invalid_domain_ratings": invalid_domains,
            "grade_auto_judgement": False,
            "analysis_ready_dataset_created": False,
        }

    def _update_quality_assessment_record(
        self,
        project_dir: Path,
        *,
        assessment_id: str,
        updates: dict[str, Any],
        status: str,
        governance_action: str,
        actor: str,
        summary: str,
    ) -> QualityAssessmentV1Result:
        project_dir = project_dir.expanduser().resolve()
        records = self.load_quality_assessment_records_v1(project_dir)
        index = next((idx for idx, item in enumerate(records) if str(item.get("assessment_id", "")) == assessment_id), -1)
        if index < 0:
            raise ValueError(f"quality_assessment_record_not_found:{assessment_id}")
        before = dict(records[index])
        after = {**before, **updates, "status": status, "updated_at": now_utc(), "analysis_ready_dataset_created": False, "statistics_run": False, "prisma_advanced": False}
        if "overall_rating" in after:
            after["overall_rating"] = _normalize_quality_rating(str(after.get("overall_rating", ""))) if after.get("overall_rating") else ""
            after["overall_judgement"] = after["overall_rating"]
        state_candidate = str(after.get("confirmation_state") or status)
        after["confirmation_state"] = _validate_quality_state(state_candidate) if state_candidate in QUALITY_M6_GOVERNANCE_STATES else "confirmed" if status == "completed_by_user" else "draft"
        after["domains"] = {str(key): _normalize_quality_rating(value) for key, value in dict(after.get("domains", {})).items()}
        after["diagnostics"] = self._quality_record_diagnostics(after)
        after["diagnostics"]["m6_validation"] = self.validate_quality_assessment_model(
            tool_name=str(after.get("tool_name", "")),
            domains=dict(after.get("domains", {})),
            overall_rating=str(after.get("overall_rating", "")),
            state=str(after.get("confirmation_state") or "draft"),
        )
        records[index] = after
        output_path = self._records_v1_path(project_dir)
        _write_json(output_path, self._records_v1_payload(str(after.get("project_id") or project_dir.name), records))
        audit = self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=str(after.get("project_id") or project_dir.name),
            actor=actor,
            target_type="quality_assessment",
            target_id=assessment_id,
            source_path=str(output_path.relative_to(project_dir)),
            output_path=str(output_path.relative_to(project_dir)),
            summary=summary,
            details={"status": status, "analysis_ready_dataset_created": False, "statistics_run": False, "prisma_advanced": False},
        )
        governance = self._governance.record_user_confirmation(
            project_dir,
            project_id=str(after.get("project_id") or project_dir.name),
            action=governance_action,
            actor=actor,
            target_type="quality_assessment_score",
            target_id=assessment_id,
            before=before,
            after=after,
            metadata={"status": status, "auto_grade": False, "statistics_run": False, "prisma_advanced": False},
        )
        after.setdefault("audit_refs", []).append(audit.event_id)
        after.setdefault("governance_refs", []).append(governance.event_id)
        records[index] = after
        _write_json(output_path, self._records_v1_payload(str(after.get("project_id") or project_dir.name), records))
        summary_path = self.write_quality_summary_v1(project_dir)
        return QualityAssessmentV1Result(True, str(after.get("project_id") or project_dir.name), assessment_id, str(output_path), str(summary_path), summary, after, after["diagnostics"])

    def _register_asset(self, *, project_id: str, data_type: str, source_path: str, output_path: str) -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(project_id=project_id, module="meta_analysis", data_type=data_type, source_path=source_path, output_path=output_path, status="available")

    def _start_task(self, *, project_id: str, task_type: TaskType, title: str) -> TaskRecord:
        now = now_utc()
        if self._task_center is None:
            return TaskRecord(task_id=f"task-{uuid4().hex[:12]}", task_type=task_type, status=TaskStatus.RUNNING, module="meta_analysis", title=title, created_at=now, updated_at=now, project_id=project_id, started_at=now)
        return self._task_center.register_task(task_id=f"task-{uuid4().hex[:12]}", task_type=task_type, module="meta_analysis", title=title, project_id=project_id, status=TaskStatus.RUNNING, started_at=now)

    def _finish_task(self, task: TaskRecord, *, success: bool, summary: str) -> None:
        if self._task_center is None:
            return
        now = now_utc()
        self._task_center.save_task(TaskRecord(task_id=task.task_id, task_type=task.task_type, status=TaskStatus.COMPLETED if success else TaskStatus.FAILED, module=task.module, title=task.title, created_at=task.created_at, updated_at=now, project_id=task.project_id, started_at=task.started_at, finished_at=now, summary=summary, error_message="" if success else summary))


def _normalize_quality_rating(value: str) -> str:
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "low_risk": "low",
        "low_risk_or_good": "low_risk_or_good",
        "低风险/较好": "low_risk_or_good",
        "moderate_risk": "some_concerns",
        "some_concern": "some_concerns",
        "high_risk": "high",
        "high_risk_or_poor": "high_risk_or_poor",
        "高风险/较差": "high_risk_or_poor",
        "不明确": "unclear",
        "未评价": "not_assessed",
        "not_applicable": "not_applicable",
        "not_assessed": "not_assessed",
        "not_assessed_": "not_assessed",
        "yes": "low",
        "no": "high",
    }
    return aliases.get(normalized, normalized if normalized in QUALITY_RATING_OPTIONS else value.strip())


def _validate_quality_state(value: str) -> str:
    state = str(value or "").strip()
    if state not in QUALITY_M6_GOVERNANCE_STATES:
        raise ValueError(f"unsupported_quality_governance_state:{value}")
    return state


def _quality_summary_bucket(value: str) -> str:
    normalized = _normalize_quality_rating(value)
    if normalized in {"low", "low_risk_or_good"}:
        return "low_risk_or_good"
    if normalized in {"high", "high_risk_or_poor"}:
        return "high_risk_or_poor"
    return "unclear"


def _quality_expected_study_ids(project_dir: Path) -> list[str]:
    project_dir = project_dir.expanduser().resolve()
    rows: list[str] = []
    effect_payload = _load_json(project_dir / "extraction" / "extraction_effect_rows.json")
    for item in effect_payload.get("effect_rows", []):
        if not isinstance(item, dict):
            continue
        if str(item.get("evidence_state", "")) not in {"confirmed"} and str(item.get("extraction_status", "")) != "completed_by_user":
            continue
        structured = item.get("m5_structured_fields", {}) if isinstance(item.get("m5_structured_fields"), dict) else {}
        study_id = str(structured.get("study_id") or item.get("study_unit_label") or item.get("study_unit_id") or "").strip()
        if study_id:
            rows.append(study_id)
    if rows:
        return sorted(set(rows))
    final = _load_json(project_dir / "fulltext" / "final_included_studies.json")
    for item in final.get("included_studies", []):
        if isinstance(item, dict):
            study_id = str(item.get("study_id") or item.get("record_id") or "").strip()
            if study_id:
                rows.append(study_id)
    return sorted(set(rows))


def _tools_for_meta_type(meta_type: str) -> tuple[str, ...]:
    mapping = {
        "binary_outcome_meta": ("ROB2", "Cochrane RoB generic", "GRADE summary placeholder"),
        "continuous_outcome_meta": ("ROB2", "Cochrane RoB generic", "GRADE summary placeholder"),
        "treatment_comparative_meta": ("ROB2", "Cochrane RoB generic", "GRADE summary placeholder"),
        "exposure_disease_risk_meta": ("Newcastle-Ottawa Scale", "ROBINS-I", "GRADE summary placeholder"),
        "diagnostic_accuracy_meta": ("QUADAS-2", "GRADE summary placeholder"),
        "prognostic_factor_meta": ("Newcastle-Ottawa Scale", "ROBINS-I", "GRADE summary placeholder"),
        "prevalence_incidence_meta": ("JBI prevalence checklist", "AHRQ cross-sectional checklist", "GRADE summary placeholder"),
        "biomarker_expression_difference_meta": ("Newcastle-Ottawa Scale", "AHRQ cross-sectional checklist"),
        "correlation_meta": ("Newcastle-Ottawa Scale", "JBI prevalence checklist"),
        "survival_outcome_meta": ("Newcastle-Ottawa Scale", "ROBINS-I", "GRADE summary placeholder"),
        "dose_response_meta": ("Newcastle-Ottawa Scale", "ROBINS-I"),
        "TREATMENT_EFFECT_META": ("ROB2", "Cochrane RoB generic", "GRADE summary placeholder"),
        "DIAGNOSTIC_ACCURACY_META": ("QUADAS-2", "GRADE summary placeholder"),
        "PROGNOSTIC_FACTOR_META": ("Newcastle-Ottawa Scale", "ROBINS-I", "GRADE summary placeholder"),
        "PREVALENCE_INCIDENCE_META": ("JBI prevalence checklist", "AHRQ cross-sectional checklist", "GRADE summary placeholder"),
    }
    return mapping.get(meta_type, ())


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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
