from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.meta_analysis.models.attachments import ATTACHMENT_MODES
from app.meta_analysis.models.systematic_review import FULLTEXT_EXCLUSION_REASONS, now_utc
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.fulltext_service import FullTextService
from app.meta_analysis.services.project_contract_service import MetaProjectContractService
from app.shared.data_center.service import DataCenter


FULLTEXT_ELIGIBILITY_STATUSES = (
    "not_checked",
    "available_online",
    "local_pdf_linked",
    "local_pdf_copied",
    "missing_full_text",
    "failed_to_access",
    "manual_review_required",
    "excluded_after_full_text_review",
    "included_for_extraction",
)

INCLUDE_LIKE_STATUSES = (
    "available_online",
    "local_pdf_linked",
    "local_pdf_copied",
    "included_for_extraction",
)


@dataclass(frozen=True)
class FullTextEligibilityCandidate:
    record_id: str
    screening_record_id: str
    title: str
    authors: str
    journal: str
    year: str
    doi: str
    pmid: str
    screening_decision: str
    fulltext_status: str
    pdf_status: str
    recommended_action: str
    exclusion_reason: str = ""
    notes: str = ""


@dataclass(frozen=True)
class FullTextEligibilityDecision:
    record_id: str
    eligibility_status: str
    reviewer_id: str = ""
    exclusion_reason: str = ""
    notes: str = ""
    source_screening_decision: str = ""
    pdf_path: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True)
class FullTextEligibilitySaveResult:
    success: bool
    decision: FullTextEligibilityDecision | None
    output_path: str
    compatible_decisions_path: str
    message: str
    warnings: tuple[str, ...] = ()


class FullTextEligibilityService:
    def __init__(
        self,
        *,
        fulltext_service: FullTextService | None = None,
        data_center: DataCenter | None = None,
        audit_log: MetaAuditLogService | None = None,
        project_contract: MetaProjectContractService | None = None,
    ) -> None:
        self._data_center = data_center or DataCenter.default()
        self._audit_log = audit_log or MetaAuditLogService()
        self._fulltext_service = fulltext_service or FullTextService(data_center=self._data_center, audit_log=self._audit_log)
        self._project_contract = project_contract or MetaProjectContractService(data_center=self._data_center)

    def build_candidates_from_screening(self, project_dir: Path) -> tuple[FullTextEligibilityCandidate, ...]:
        project_dir = project_dir.expanduser().resolve()
        screening_records = self._load_screening_records(project_dir)
        fulltext_by_record = {record.record_id: record for record in self._fulltext_service.list_fulltext_files(project_dir)}
        decisions_by_record = {decision.record_id: decision for decision in self.load_eligibility_decisions(project_dir)}
        candidates: list[FullTextEligibilityCandidate] = []
        for item in screening_records:
            decision = _screening_decision(item)
            if decision not in {"included", "include", "maybe", "needs_review"}:
                continue
            record_id = _record_id(item)
            if not record_id:
                continue
            fulltext_record = fulltext_by_record.get(record_id)
            eligibility = decisions_by_record.get(record_id)
            fulltext_status = eligibility.eligibility_status if eligibility else (fulltext_record.availability_status if fulltext_record else "not_checked")
            pdf_status = "local_pdf_available" if fulltext_record and fulltext_record.pdf_path else "no_local_pdf"
            candidates.append(
                FullTextEligibilityCandidate(
                    record_id=record_id,
                    screening_record_id=str(item.get("screening_record_id", "")),
                    title=str(item.get("title", "")),
                    authors=_join_text(item.get("authors") or item.get("authors_text") or item.get("creators")),
                    journal=str(item.get("journal") or item.get("publication_title") or ""),
                    year=str(item.get("year") or item.get("date") or ""),
                    doi=str(item.get("doi") or ""),
                    pmid=str(item.get("pmid") or ""),
                    screening_decision=decision,
                    fulltext_status=fulltext_status,
                    pdf_status=pdf_status,
                    recommended_action=_recommended_action(decision, fulltext_status, pdf_status),
                    exclusion_reason=eligibility.exclusion_reason if eligibility else "",
                    notes=eligibility.notes if eligibility else "",
                )
            )
        return tuple(candidates)

    def load_eligibility_decisions(self, project_dir: Path) -> tuple[FullTextEligibilityDecision, ...]:
        path = self._eligibility_path(project_dir.expanduser().resolve())
        if not path.exists():
            return ()
        payload = _load_json(path)
        decisions = payload.get("decisions", [])
        return tuple(_decision_from_dict(item) for item in decisions if isinstance(item, dict))

    def save_eligibility_decision(
        self,
        project_dir: Path,
        *,
        record_id: str,
        eligibility_status: str,
        reviewer_id: str = "",
        exclusion_reason: str = "",
        notes: str = "",
        source_screening_decision: str = "",
    ) -> FullTextEligibilitySaveResult:
        project_dir = project_dir.expanduser().resolve()
        validation_warnings = self._validate_decision(record_id=record_id, eligibility_status=eligibility_status, exclusion_reason=exclusion_reason)
        if any(warning.startswith("error:") for warning in validation_warnings):
            return FullTextEligibilitySaveResult(
                success=False,
                decision=None,
                output_path=str(self._eligibility_path(project_dir)),
                compatible_decisions_path=str(project_dir / "fulltext" / "fulltext_screening_decisions.json"),
                message="Full-text eligibility decision was not saved. Please fix the highlighted fields.",
                warnings=tuple(validation_warnings),
            )
        existing = {decision.record_id: decision for decision in self.load_eligibility_decisions(project_dir)}
        now = now_utc()
        previous = existing.get(record_id)
        pdf_path = self._pdf_path(project_dir, record_id)
        decision = FullTextEligibilityDecision(
            record_id=record_id,
            eligibility_status=eligibility_status,
            reviewer_id=reviewer_id,
            exclusion_reason=exclusion_reason if _is_excluded_status(eligibility_status) else "",
            notes=notes,
            source_screening_decision=source_screening_decision,
            pdf_path=pdf_path,
            created_at=previous.created_at if previous else now,
            updated_at=now,
        )
        existing[record_id] = decision
        output_path = self._write_eligibility_decisions(project_dir, tuple(existing.values()))
        compatible = self._save_compatible_fulltext_decision(project_dir, decision)
        self._register_asset(project_dir.name, "fulltext_eligibility_decisions", str(project_dir / "screening"), str(output_path))
        self._audit_log.record_event(
            project_dir,
            event_type="fulltext_status_changed",
            project_id=project_dir.name,
            target_type="fulltext_eligibility_decision",
            target_id=record_id,
            source_path=str(project_dir / "screening"),
            output_path=str(output_path),
            summary=f"Full-text eligibility decision saved: {eligibility_status}",
            details={"reviewer_id": reviewer_id, "exclusion_reason": decision.exclusion_reason, "developer_preview": True},
        )
        self._project_contract.write_project_manifests(project_dir)
        return FullTextEligibilitySaveResult(
            success=True,
            decision=decision,
            output_path=str(output_path),
            compatible_decisions_path=str(compatible),
            message=f"Full-text eligibility decision saved for {record_id}.",
            warnings=tuple(validation_warnings),
        )

    def attach_pdf_for_candidate(
        self,
        project_dir: Path,
        *,
        record_id: str,
        source_file_path: str,
        mode: str,
        reviewer_id: str = "",
        notes: str = "",
    ) -> FullTextEligibilitySaveResult:
        if mode not in ATTACHMENT_MODES:
            return FullTextEligibilitySaveResult(
                success=False,
                decision=None,
                output_path=str(self._eligibility_path(project_dir)),
                compatible_decisions_path=str(project_dir / "fulltext" / "fulltext_screening_decisions.json"),
                message="Unsupported attachment mode. Use link_existing_files, copy_to_project_library, or ignore_attachments.",
                warnings=("error:unsupported_attachment_mode",),
            )
        if mode == "ignore_attachments":
            self._fulltext_service.update_fulltext_availability(project_dir, record_id, "not_required")
            return self.save_eligibility_decision(
                project_dir,
                record_id=record_id,
                eligibility_status="manual_review_required",
                reviewer_id=reviewer_id,
                notes=notes or "Attachment handling ignored by reviewer.",
            )
        self._fulltext_service.attach_pdf(project_dir, record_id, source_file_path, mode=mode, notes=notes)
        return self.save_eligibility_decision(
            project_dir,
            record_id=record_id,
            eligibility_status="local_pdf_copied" if mode == "copy_to_project_library" else "local_pdf_linked",
            reviewer_id=reviewer_id,
            notes=notes,
        )

    def export_final_included_studies(self, project_dir: Path) -> Path:
        project_dir = project_dir.expanduser().resolve()
        candidates_by_record = {candidate.record_id: candidate for candidate in self.build_candidates_from_screening(project_dir)}
        rows = []
        for decision in self.load_eligibility_decisions(project_dir):
            if decision.eligibility_status not in INCLUDE_LIKE_STATUSES:
                continue
            candidate = candidates_by_record.get(decision.record_id)
            rows.append(
                {
                    "record_id": decision.record_id,
                    "title": candidate.title if candidate else "",
                    "authors": candidate.authors if candidate else "",
                    "journal": candidate.journal if candidate else "",
                    "year": candidate.year if candidate else "",
                    "eligibility_status": decision.eligibility_status,
                    "pdf_path": decision.pdf_path,
                    "notes": decision.notes,
                }
            )
        output_path = project_dir / "fulltext" / "final_included_studies.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps({"project_id": project_dir.name, "developer_preview": True, "included_studies": rows}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._register_asset(project_dir.name, "final_included_studies", str(self._eligibility_path(project_dir)), str(output_path))
        self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=project_dir.name,
            target_type="final_included_studies",
            target_id="final_included_studies",
            source_path=str(self._eligibility_path(project_dir)),
            output_path=str(output_path),
            summary=f"Final included studies exported: {len(rows)} records.",
            details={"included_count": len(rows), "developer_preview": True},
        )
        self._project_contract.write_project_manifests(project_dir)
        return output_path

    def export_fulltext_exclusion_report(self, project_dir: Path) -> Path:
        project_dir = project_dir.expanduser().resolve()
        compatibility_report = self._fulltext_service.export_full_text_exclusion_report(project_dir)
        output_path = project_dir / "fulltext" / "fulltext_exclusion_report.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["record_id", "eligibility_status", "exclusion_reason", "reviewer_id", "notes", "updated_at"])
            writer.writeheader()
            for decision in self.load_eligibility_decisions(project_dir):
                if _is_excluded_status(decision.eligibility_status):
                    writer.writerow(
                        {
                            "record_id": decision.record_id,
                            "eligibility_status": decision.eligibility_status,
                            "exclusion_reason": decision.exclusion_reason,
                            "reviewer_id": decision.reviewer_id,
                            "notes": decision.notes,
                            "updated_at": decision.updated_at,
                        }
                    )
        self._register_asset(project_dir.name, "fulltext_eligibility_exclusion_report", str(self._eligibility_path(project_dir)), str(output_path))
        self._audit_log.record_event(
            project_dir,
            event_type="report_exported",
            project_id=project_dir.name,
            target_type="fulltext_eligibility_exclusion_report",
            target_id=output_path.name,
            source_path=str(self._eligibility_path(project_dir)),
            output_path=str(output_path),
            summary="Full-text eligibility exclusion report exported.",
            details={"compatibility_report": str(compatibility_report), "developer_preview": True},
        )
        self._project_contract.write_project_manifests(project_dir)
        return output_path

    def _load_screening_records(self, project_dir: Path) -> list[dict[str, object]]:
        paths = (
            project_dir / "screening" / "title_abstract_decisions.json",
            project_dir / "screening" / "screening_decisions.json",
        )
        for path in paths:
            records = _records_from_json(path)
            if records:
                return records
        for path in sorted((project_dir / "screening").glob("*screening_queue.json")):
            records = _records_from_json(path)
            if records:
                return records
        return []

    def _eligibility_path(self, project_dir: Path) -> Path:
        return project_dir / "fulltext" / "fulltext_eligibility_decisions.json"

    def _write_eligibility_decisions(self, project_dir: Path, decisions: tuple[FullTextEligibilityDecision, ...]) -> Path:
        output_path = self._eligibility_path(project_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "project_id": project_dir.name,
            "schema_version": "meta_fulltext_eligibility.v1",
            "developer_preview": True,
            "decisions": [asdict(decision) for decision in sorted(decisions, key=lambda item: item.record_id)],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def _save_compatible_fulltext_decision(self, project_dir: Path, decision: FullTextEligibilityDecision) -> Path:
        compatible_decision = _compatible_decision(decision)
        compatible_reason = decision.exclusion_reason
        if compatible_decision == "exclude" and not compatible_reason:
            compatible_reason = "no full text" if decision.eligibility_status == "missing_full_text" else "other"
        self._fulltext_service.save_fulltext_decision(
            project_dir,
            record_id=decision.record_id,
            reviewer_id=decision.reviewer_id,
            decision=compatible_decision,
            exclusion_reason=compatible_reason,
            notes=decision.notes,
        )
        return project_dir / "fulltext" / "fulltext_screening_decisions.json"

    def _validate_decision(self, *, record_id: str, eligibility_status: str, exclusion_reason: str) -> list[str]:
        warnings: list[str] = []
        if not record_id.strip():
            warnings.append("error:missing_record_id")
        if eligibility_status not in FULLTEXT_ELIGIBILITY_STATUSES:
            warnings.append("error:unsupported_fulltext_eligibility_status")
        if _is_excluded_status(eligibility_status):
            if not exclusion_reason:
                warnings.append("error:missing_fulltext_exclusion_reason")
            elif exclusion_reason not in FULLTEXT_EXCLUSION_REASONS:
                warnings.append("error:unsupported_fulltext_exclusion_reason")
        if eligibility_status in {"available_online", "manual_review_required"}:
            warnings.append("needs_reviewer_follow_up")
        return warnings

    def _pdf_path(self, project_dir: Path, record_id: str) -> str:
        record = self._fulltext_service.get_fulltext_by_record_id(project_dir, record_id)
        return record.pdf_path if record is not None else ""

    def _register_asset(self, project_id: str, data_type: str, source_path: str, output_path: str) -> None:
        self._data_center.register_asset(project_id=project_id, module="meta_analysis", data_type=data_type, source_path=source_path, output_path=output_path, status="testing")


def _records_from_json(path: Path) -> list[dict[str, object]]:
    payload = _load_json(path)
    for key in ("screening_records", "records", "decisions", "screening_decisions"):
        records = payload.get(key)
        if isinstance(records, list):
            return [dict(item) for item in records if isinstance(item, dict)]
    return []


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _decision_from_dict(payload: dict[str, object]) -> FullTextEligibilityDecision:
    return FullTextEligibilityDecision(
        record_id=str(payload.get("record_id", "")),
        eligibility_status=str(payload.get("eligibility_status", "not_checked")),
        reviewer_id=str(payload.get("reviewer_id", "")),
        exclusion_reason=str(payload.get("exclusion_reason", "")),
        notes=str(payload.get("notes", "")),
        source_screening_decision=str(payload.get("source_screening_decision", "")),
        pdf_path=str(payload.get("pdf_path", "")),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
    )


def _record_id(item: dict[str, object]) -> str:
    return str(item.get("record_id") or item.get("normalized_record_id") or item.get("source_record_id") or "")


def _screening_decision(item: dict[str, object]) -> str:
    value = str(item.get("decision") or item.get("screening_decision") or item.get("status") or "pending").strip().lower()
    if value == "include":
        return "included"
    if value == "exclude":
        return "excluded"
    return value


def _join_text(value: object) -> str:
    if isinstance(value, list):
        names: list[str] = []
        for item in value:
            if isinstance(item, dict):
                names.append(str(item.get("full_name") or item.get("raw") or item.get("last_name") or ""))
            else:
                names.append(str(item))
        return "; ".join(name for name in names if name)
    return str(value or "")


def _recommended_action(screening_decision: str, fulltext_status: str, pdf_status: str) -> str:
    if fulltext_status in INCLUDE_LIKE_STATUSES:
        return "ready_for_extraction"
    if fulltext_status in {"excluded_after_full_text_review", "missing_full_text", "failed_to_access"}:
        return "review_exclusion_reason"
    if pdf_status == "local_pdf_available":
        return "complete_full_text_review"
    if screening_decision == "maybe":
        return "manual_full_text_review"
    return "link_or_copy_pdf"


def _is_excluded_status(status: str) -> bool:
    return status in {"excluded_after_full_text_review", "missing_full_text", "failed_to_access"}


def _compatible_decision(decision: FullTextEligibilityDecision) -> str:
    if decision.eligibility_status in INCLUDE_LIKE_STATUSES:
        return "include"
    if _is_excluded_status(decision.eligibility_status):
        return "exclude"
    return "maybe"
