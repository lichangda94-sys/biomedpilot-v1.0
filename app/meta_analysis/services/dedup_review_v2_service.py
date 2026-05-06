from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


DUPLICATE_REVIEW_QUEUE_SCHEMA_VERSION = "meta_duplicate_review_queue.v2"
DUPLICATE_GROUP_SCHEMA_VERSION = "meta_duplicate_group.v2"
DEDUP_DECISION_SCHEMA_VERSION = "meta_dedup_decision.v2"
DEDUP_DECISION_LOG_SCHEMA_VERSION = "meta_dedup_decision_log.v2"
DEDUPLICATED_SET_SCHEMA_VERSION = "meta_deduplicated_literature_set.v2"

RISK_RED = "red"
RISK_YELLOW = "yellow"
RISK_GRAY = "gray"
RISK_GREEN = "green"

RISK_LABELS = {
    RISK_RED: "高度重复",
    RISK_YELLOW: "疑似重复",
    RISK_GRAY: "轻度疑似",
    RISK_GREEN: "暂未发现重复",
}

DECISION_MERGE = "merge"
DECISION_KEEP_BOTH = "keep_both"
DECISION_MARK_NOT_DUPLICATE = "mark_not_duplicate"
DECISION_SET_MASTER_RECORD = "set_master_record"
DECISION_EXCLUDE_DUPLICATE = "exclude_duplicate"
DECISION_SKIP = "skip"
DECISION_UNDO = "undo"


@dataclass(frozen=True)
class DuplicateGroupV2:
    group_id: str
    record_ids: tuple[str, ...]
    records: tuple[dict[str, Any], ...]
    duplicate_rule: str
    match_reason: str
    risk_level: str
    risk_label: str
    confidence: float
    retain_candidate_id: str
    field_differences: tuple[dict[str, Any], ...]
    merge_preview: dict[str, Any]
    status: str = "pending_review"
    created_at: str = ""
    schema_version: str = DUPLICATE_GROUP_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "group_id": self.group_id,
            "record_ids": list(self.record_ids),
            "records": [dict(record) for record in self.records],
            "duplicate_rule": self.duplicate_rule,
            "match_reason": self.match_reason,
            "risk_level": self.risk_level,
            "risk_label": self.risk_label,
            "confidence": self.confidence,
            "retain_candidate_id": self.retain_candidate_id,
            "field_differences": [dict(item) for item in self.field_differences],
            "merge_preview": dict(self.merge_preview),
            "status": self.status,
            "created_at": self.created_at,
            "auto_merged": False,
            "auto_deleted": False,
        }


@dataclass(frozen=True)
class DedupReviewQueueV2:
    project_id: str
    groups: tuple[DuplicateGroupV2, ...]
    source_records_path: str
    created_at: str
    schema_version: str = DUPLICATE_REVIEW_QUEUE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        risk_counts: dict[str, int] = {}
        for group in self.groups:
            risk_counts[group.risk_level] = risk_counts.get(group.risk_level, 0) + 1
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "source_records_path": self.source_records_path,
            "created_at": self.created_at,
            "status": "pending_reviewer_decision",
            "group_count": len(self.groups),
            "risk_level_counts": risk_counts,
            "auto_merged": False,
            "auto_deleted": False,
            "screening_status": "not_started",
            "duplicate_groups": [group.to_dict() for group in self.groups],
        }


@dataclass(frozen=True)
class DedupDecisionV2:
    decision_id: str
    group_id: str
    decision: str
    actor: str
    selected_record_id: str = ""
    merged_record: dict[str, Any] = field(default_factory=dict)
    note: str = ""
    created_at: str = ""
    undone_decision_id: str = ""
    schema_version: str = DEDUP_DECISION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "group_id": self.group_id,
            "decision": self.decision,
            "actor": self.actor,
            "selected_record_id": self.selected_record_id,
            "merged_record": self.merged_record,
            "note": self.note,
            "created_at": self.created_at,
            "undone_decision_id": self.undone_decision_id,
            "auto_deleted": False,
            "auto_merged": False,
        }


@dataclass(frozen=True)
class DedupReviewResultV2:
    success: bool
    project_id: str
    group_count: int
    output_path: str
    message: str
    risk_level_counts: dict[str, int] = field(default_factory=dict)
    groups: tuple[DuplicateGroupV2, ...] = ()
    error_count: int = 0


class DedupReviewV2Service:
    def __init__(
        self,
        *,
        literature_library: LiteratureLibraryService | None = None,
        audit_log: MetaAuditLogService | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
    ) -> None:
        self._library = literature_library or LiteratureLibraryService()
        self._audit_log = audit_log or MetaAuditLogService()
        self._research_governance = research_governance or MetaResearchGovernanceService(audit_log=self._audit_log)

    def review_queue_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "deduplication" / "duplicate_groups_v2.json"

    def decisions_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "deduplication" / "dedup_decisions_v2.json"

    def deduplicated_set_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "deduplication" / "deduplicated_literature_v2.json"

    def build_review_queue(self, project_dir: Path, *, project_id: str | None = None) -> DedupReviewResultV2:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_id or project_dir.name
        records = self._library.list_records(project_dir)
        groups = tuple(self._identify_groups(records))
        queue = DedupReviewQueueV2(
            project_id=project_id,
            groups=groups,
            source_records_path=str(self._library.records_path(project_dir).relative_to(project_dir)),
            created_at=_now(),
        )
        output_path = self.review_queue_path(project_dir)
        _write_json(output_path, queue.to_dict())
        for group in groups:
            self._audit_log.record_event(
                project_dir,
                event_type="duplicate_detected",
                project_id=project_id,
                target_type="duplicate_group_v2",
                target_id=group.group_id,
                source_path=str(self._library.records_path(project_dir).relative_to(project_dir)),
                output_path=str(output_path.relative_to(project_dir)),
                summary=f"Duplicate group v2 detected: {group.duplicate_rule}",
                details={
                    "record_ids": list(group.record_ids),
                    "risk_level": group.risk_level,
                    "risk_label": group.risk_label,
                    "confidence": group.confidence,
                    "auto_merged": False,
                    "auto_deleted": False,
                },
            )
        return DedupReviewResultV2(
            success=True,
            project_id=project_id,
            group_count=len(groups),
            output_path=str(output_path),
            message=f"Duplicate Review v2 generated {len(groups)} duplicate groups.",
            risk_level_counts=queue.to_dict()["risk_level_counts"],
            groups=groups,
        )

    def load_queue(self, project_dir: Path) -> DedupReviewQueueV2:
        path = self.review_queue_path(project_dir)
        payload = _load_json(path)
        if not payload:
            return DedupReviewQueueV2(project_id=project_dir.expanduser().resolve().name, groups=(), source_records_path="", created_at="")
        groups = tuple(_group_from_payload(item) for item in payload.get("duplicate_groups", []) if isinstance(item, dict))
        return DedupReviewQueueV2(
            project_id=str(payload.get("project_id", project_dir.expanduser().resolve().name)),
            groups=groups,
            source_records_path=str(payload.get("source_records_path", "")),
            created_at=str(payload.get("created_at", "")),
            schema_version=str(payload.get("schema_version", DUPLICATE_REVIEW_QUEUE_SCHEMA_VERSION)),
        )

    def preview_merge(self, project_dir: Path, *, group_id: str, selected_record_id: str = "") -> dict[str, Any]:
        group = self._require_group(project_dir, group_id)
        records = list(group.records)
        if selected_record_id:
            records = sorted(records, key=lambda record: 0 if str(record.get("record_id", "")) == selected_record_id else 1)
        return _merge_preview(group_id, records, risk_level=group.risk_level, duplicate_rule=group.duplicate_rule)

    def save_decision(
        self,
        project_dir: Path,
        *,
        group_id: str,
        decision: str,
        actor: str,
        selected_record_id: str = "",
        note: str = "",
        merged_record: dict[str, Any] | None = None,
        undone_decision_id: str = "",
    ) -> DedupDecisionV2:
        project_dir = project_dir.expanduser().resolve()
        normalized = _normalize_decision(decision)
        group = self._require_group(project_dir, group_id)
        if normalized in {DECISION_MERGE, DECISION_SET_MASTER_RECORD}:
            merged_record = dict(merged_record or self.preview_merge(project_dir, group_id=group_id, selected_record_id=selected_record_id))
            if not merged_record.get("merged_from_record_ids"):
                raise ValueError("merge decision requires a merge preview.")
        decision_payload = DedupDecisionV2(
            decision_id=f"dedupv2-{uuid4().hex[:12]}",
            group_id=group_id,
            decision=normalized,
            actor=actor,
            selected_record_id=selected_record_id or group.retain_candidate_id,
            merged_record=dict(merged_record or {}),
            note=note.strip(),
            created_at=_now(),
            undone_decision_id=undone_decision_id,
        )
        decisions = self._load_decisions(project_dir)
        decisions = [item for item in decisions if item.group_id != group_id or normalized == DECISION_UNDO]
        decisions.append(decision_payload)
        _write_json(
            self.decisions_path(project_dir),
            {
                "schema_version": DEDUP_DECISION_LOG_SCHEMA_VERSION,
                "project_id": project_dir.name,
                "updated_at": _now(),
                "decisions": [item.to_dict() for item in decisions],
                "auto_deleted": False,
                "auto_merged": False,
            },
        )
        self._audit_log.record_event(
            project_dir,
            event_type="duplicate_decision",
            project_id=project_dir.name,
            actor=actor,
            target_type="duplicate_group_v2",
            target_id=group_id,
            source_path=str(self.review_queue_path(project_dir).relative_to(project_dir)),
            output_path=str(self.decisions_path(project_dir).relative_to(project_dir)),
            summary=f"Duplicate Review v2 decision saved: {normalized}",
            details={
                "decision_id": decision_payload.decision_id,
                "decision": normalized,
                "selected_record_id": decision_payload.selected_record_id,
                "risk_level": group.risk_level,
                "auto_deleted": False,
                "auto_merged": False,
            },
        )
        self._research_governance.record_user_confirmation(
            project_dir,
            project_id=project_dir.name,
            action="confirm",
            actor=actor,
            target_type="dedup_merge",
            target_id=group_id,
            before={"status": group.status, "record_ids": list(group.record_ids)},
            after=decision_payload.to_dict(),
            metadata={"risk_level": group.risk_level, "duplicate_rule": group.duplicate_rule},
        )
        return decision_payload

    def generate_deduplicated_set(self, project_dir: Path, *, project_id: str | None = None) -> dict[str, Any]:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_id or project_dir.name
        records = self._library.list_records(project_dir)
        groups = {group.group_id: group for group in self.load_queue(project_dir).groups}
        decisions = {decision.group_id: decision for decision in self._load_decisions(project_dir) if decision.decision != DECISION_UNDO}
        removed_ids: set[str] = set()
        replacements: list[dict[str, Any]] = []
        unresolved: list[str] = []
        for group_id, group in groups.items():
            decision = decisions.get(group_id)
            if decision is None or decision.decision == DECISION_SKIP:
                unresolved.append(group_id)
                continue
            if decision.decision in {DECISION_KEEP_BOTH, DECISION_MARK_NOT_DUPLICATE}:
                continue
            if decision.decision in {DECISION_MERGE, DECISION_SET_MASTER_RECORD}:
                removed_ids.update(group.record_ids)
                replacement = dict(decision.merged_record or self.preview_merge(project_dir, group_id=group_id, selected_record_id=decision.selected_record_id))
                replacement["dedup_status"] = "deduplicated_merged"
                replacement["record_status"] = "deduplicated_set_member"
                replacements.append(replacement)
                continue
            if decision.decision == DECISION_EXCLUDE_DUPLICATE:
                removed_ids.update(record_id for record_id in group.record_ids if record_id != decision.selected_record_id)
        deduplicated = [
            {**record, "dedup_status": "deduplicated_set_member"}
            for record in records
            if str(record.get("record_id", "")) not in removed_ids
        ]
        deduplicated.extend(replacements)
        payload = {
            "schema_version": DEDUPLICATED_SET_SCHEMA_VERSION,
            "project_id": project_id,
            "created_at": _now(),
            "source_records_path": str(self._library.records_path(project_dir).relative_to(project_dir)),
            "decisions_path": str(self.decisions_path(project_dir).relative_to(project_dir)),
            "original_count": len(records),
            "deduplicated_count": len(deduplicated),
            "unresolved_group_ids": unresolved,
            "records": deduplicated,
            "auto_deleted": False,
            "auto_merged": False,
            "screening_status": "not_started",
        }
        _write_json(self.deduplicated_set_path(project_dir), payload)
        return payload

    def _identify_groups(self, records: list[dict[str, Any]]) -> list[DuplicateGroupV2]:
        pairs: dict[tuple[str, str], tuple[str, float]] = {}
        for left_index, left in enumerate(records):
            for right in records[left_index + 1 :]:
                rule, confidence = _match_rule(left, right)
                if not rule:
                    continue
                key = tuple(sorted((str(left.get("record_id", "")), str(right.get("record_id", "")))))
                if key not in pairs or confidence > pairs[key][1]:
                    pairs[key] = (rule, confidence)
        parent = {str(record.get("record_id", "")): str(record.get("record_id", "")) for record in records}
        for left_id, right_id in pairs:
            _union(parent, left_id, right_id)
        clusters: dict[str, list[str]] = {}
        for record_id in parent:
            clusters.setdefault(_find(parent, record_id), []).append(record_id)
        records_by_id = {str(record.get("record_id", "")): record for record in records}
        groups: list[DuplicateGroupV2] = []
        for ids in clusters.values():
            if len(ids) < 2:
                continue
            cluster_records = [records_by_id[record_id] for record_id in sorted(ids)]
            rules = [pairs[key] for key in pairs if key[0] in ids and key[1] in ids]
            duplicate_rule, confidence = max(rules, key=lambda item: item[1])
            risk = _risk_level(duplicate_rule, confidence)
            group_id = f"dupv2-{_slug('-'.join(sorted(ids)))}"
            groups.append(
                DuplicateGroupV2(
                    group_id=group_id,
                    record_ids=tuple(sorted(ids)),
                    records=tuple(cluster_records),
                    duplicate_rule=duplicate_rule,
                    match_reason=_match_reason(duplicate_rule),
                    risk_level=risk,
                    risk_label=RISK_LABELS[risk],
                    confidence=confidence,
                    retain_candidate_id=_retain_candidate_id(cluster_records),
                    field_differences=tuple(_field_differences(cluster_records)),
                    merge_preview=_merge_preview(group_id, cluster_records, risk_level=risk, duplicate_rule=duplicate_rule),
                    created_at=_now(),
                )
            )
        return groups

    def _require_group(self, project_dir: Path, group_id: str) -> DuplicateGroupV2:
        for group in self.load_queue(project_dir).groups:
            if group.group_id == group_id:
                return group
        raise ValueError(f"duplicate_group_not_found:{group_id}")

    def _load_decisions(self, project_dir: Path) -> list[DedupDecisionV2]:
        payload = _load_json(self.decisions_path(project_dir))
        decisions = payload.get("decisions", []) if isinstance(payload, dict) else []
        return [_decision_from_payload(item) for item in decisions if isinstance(item, dict)]


def _match_rule(left: dict[str, Any], right: dict[str, Any]) -> tuple[str, float]:
    left_pmid = _norm_id(left.get("pmid"))
    right_pmid = _norm_id(right.get("pmid"))
    if left_pmid and left_pmid == right_pmid:
        return "pmid_exact", 1.0
    left_doi = _norm_doi(left.get("doi"))
    right_doi = _norm_doi(right.get("doi"))
    if left_doi and left_doi == right_doi:
        return "doi_exact_or_variant", 0.99
    left_pmcid = _norm_id(left.get("pmcid"))
    right_pmcid = _norm_id(right.get("pmcid"))
    if left_pmcid and left_pmcid == right_pmcid:
        return "pmcid_exact_cross_check", 0.98
    if set(_clinical_trials(left)) & set(_clinical_trials(right)):
        return "clinical_trial_id_exact", 0.98
    left_title = _norm_title(left.get("title"))
    right_title = _norm_title(right.get("title"))
    if left_title and left_title == right_title:
        return "title_normalized_exact", 0.95
    if left_title and right_title:
        first_author_match = _norm_name(left.get("first_author") or _first_author(left)) == _norm_name(right.get("first_author") or _first_author(right))
        year_match = _year(left) and _year(left) == _year(right)
        journal_match = _norm_title(left.get("journal") or left.get("publication_title")) == _norm_title(right.get("journal") or right.get("publication_title"))
        similarity = SequenceMatcher(None, left_title, right_title).ratio()
        if first_author_match and year_match and similarity >= 0.92:
            return "title_first_author_year", 0.9
        if first_author_match and journal_match and similarity >= 0.86:
            return "title_fuzzy_journal_author", 0.82
    return "", 0.0


def _risk_level(rule: str, confidence: float) -> str:
    if rule in {"pmid_exact", "doi_exact_or_variant", "pmcid_exact_cross_check", "clinical_trial_id_exact", "title_normalized_exact"} or confidence >= 0.95:
        return RISK_RED
    if rule in {"title_first_author_year"} or confidence >= 0.86:
        return RISK_YELLOW
    if rule in {"title_fuzzy_journal_author"} or confidence >= 0.75:
        return RISK_GRAY
    return RISK_GREEN


def _match_reason(rule: str) -> str:
    return {
        "pmid_exact": "PMID exact match",
        "doi_exact_or_variant": "DOI exact or string variant match",
        "pmcid_exact_cross_check": "PMCID cross-check match",
        "clinical_trial_id_exact": "ClinicalTrials ID exact match",
        "title_normalized_exact": "Normalized title exact match",
        "title_first_author_year": "Title plus first author plus year match",
        "title_fuzzy_journal_author": "Title fuzzy plus journal plus author match",
    }.get(rule, rule)


def _merge_preview(group_id: str, records: list[dict[str, Any]], *, risk_level: str, duplicate_rule: str) -> dict[str, Any]:
    merged: dict[str, Any] = {
        "schema_version": "meta_dedup_merge_preview.v2",
        "record_id": f"merged-{group_id}",
        "merged_from_record_ids": [str(record.get("record_id", "")) for record in records],
        "field_sources": {},
        "provenance_sources": [],
        "risk_level": risk_level,
        "duplicate_rule": duplicate_rule,
        "warnings": [],
        "auto_merged": False,
    }
    for key in ("pmid", "doi", "pmcid", "title", "abstract", "authors", "authors_text", "first_author", "journal", "year", "publication_date", "database_source", "source_type"):
        value, source = _best_value(records, key)
        if value not in ("", None, []):
            merged[key] = value
            merged["field_sources"][key] = source
    provenance_sources: list[str] = []
    for record in records:
        provenance = record.get("provenance")
        if isinstance(provenance, dict):
            for key in ("source_file", "source_query", "candidate_preview_id", "import_batch_id"):
                if provenance.get(key):
                    provenance_sources.append(str(provenance[key]))
        for key in ("source_file", "source_query", "import_batch_id"):
            if record.get(key):
                provenance_sources.append(str(record[key]))
    merged["provenance_sources"] = sorted(set(provenance_sources))
    if len(records) < 2:
        merged["warnings"].append("merge_preview_requires_multiple_records")
    if _field_differences(records):
        merged["warnings"].append("field_differences_require_reviewer_confirmation")
    return merged


def _field_differences(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    for field_name in ("title", "abstract", "authors_text", "year", "journal", "doi", "pmid", "pmcid"):
        values = [(str(record.get("record_id", "")), _stable(record.get(field_name))) for record in records if _stable(record.get(field_name))]
        unique_values = {value for _record_id, value in values}
        if len(unique_values) > 1:
            differences.append({"field_name": field_name, "values_by_record_id": values})
    return differences


def _best_value(records: list[dict[str, Any]], key: str) -> tuple[Any, str]:
    values = [(record.get(key), str(record.get("record_id", ""))) for record in records if record.get(key) not in ("", None, [])]
    if not values:
        return "", ""
    if key in {"title", "abstract", "authors_text"}:
        return max(values, key=lambda item: len(_stable(item[0])))
    return values[0]


def _retain_candidate_id(records: list[dict[str, Any]]) -> str:
    scored = sorted(records, key=lambda record: (_completeness_score(record), len(str(record.get("abstract", "")))), reverse=True)
    return str(scored[0].get("record_id", "")) if scored else ""


def _completeness_score(record: dict[str, Any]) -> int:
    fields = ("title", "abstract", "authors", "journal", "year", "doi", "pmid")
    return sum(1 for field in fields if record.get(field) not in ("", None, []))


def _clinical_trials(record: dict[str, Any]) -> list[str]:
    value = record.get("clinical_trial_id") or record.get("clinical_trials_ids") or []
    if isinstance(value, str):
        values = re.split(r";|,", value)
    elif isinstance(value, list):
        values = [str(item) for item in value]
    else:
        values = []
    return [_norm_id(item) for item in values if _norm_id(item)]


def _first_author(record: dict[str, Any]) -> str:
    authors = record.get("authors")
    if isinstance(authors, list) and authors:
        return str(authors[0])
    return str(record.get("authors_text", "")).split(";")[0].strip()


def _year(record: dict[str, Any]) -> str:
    value = str(record.get("year") or record.get("publication_date") or record.get("date") or "")
    match = re.search(r"\b(19|20)\d{2}\b", value)
    return match.group(0) if match else ""


def _norm_id(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _norm_doi(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"^https?://(dx\.)?doi\.org/", "", text)
    text = re.sub(r"^doi:\s*", "", text)
    return text.rstrip(".")


def _norm_title(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _norm_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _stable(value: Any) -> str:
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    return str(value or "").strip()


def _union(parent: dict[str, str], left: str, right: str) -> None:
    parent[_find(parent, right)] = _find(parent, left)


def _find(parent: dict[str, str], value: str) -> str:
    while parent[value] != value:
        parent[value] = parent[parent[value]]
        value = parent[value]
    return value


def _normalize_decision(decision: str) -> str:
    normalized = decision.strip().lower()
    allowed = {DECISION_MERGE, DECISION_KEEP_BOTH, DECISION_MARK_NOT_DUPLICATE, DECISION_SET_MASTER_RECORD, DECISION_EXCLUDE_DUPLICATE, DECISION_SKIP, DECISION_UNDO}
    if normalized not in allowed:
        raise ValueError("unsupported_dedup_decision")
    return normalized


def _group_from_payload(payload: dict[str, Any]) -> DuplicateGroupV2:
    return DuplicateGroupV2(
        group_id=str(payload.get("group_id", "")),
        record_ids=tuple(str(item) for item in payload.get("record_ids", [])),
        records=tuple(dict(item) for item in payload.get("records", []) if isinstance(item, dict)),
        duplicate_rule=str(payload.get("duplicate_rule", "")),
        match_reason=str(payload.get("match_reason", "")),
        risk_level=str(payload.get("risk_level", RISK_GRAY)),
        risk_label=str(payload.get("risk_label", RISK_LABELS.get(str(payload.get("risk_level", RISK_GRAY)), ""))),
        confidence=float(payload.get("confidence", 0.0) or 0.0),
        retain_candidate_id=str(payload.get("retain_candidate_id", "")),
        field_differences=tuple(dict(item) for item in payload.get("field_differences", []) if isinstance(item, dict)),
        merge_preview=dict(payload.get("merge_preview", {})),
        status=str(payload.get("status", "pending_review")),
        created_at=str(payload.get("created_at", "")),
        schema_version=str(payload.get("schema_version", DUPLICATE_GROUP_SCHEMA_VERSION)),
    )


def _decision_from_payload(payload: dict[str, Any]) -> DedupDecisionV2:
    return DedupDecisionV2(
        decision_id=str(payload.get("decision_id", "")),
        group_id=str(payload.get("group_id", "")),
        decision=str(payload.get("decision", "")),
        actor=str(payload.get("actor", "")),
        selected_record_id=str(payload.get("selected_record_id", "")),
        merged_record=dict(payload.get("merged_record", {})),
        note=str(payload.get("note", "")),
        created_at=str(payload.get("created_at", "")),
        undone_decision_id=str(payload.get("undone_decision_id", "")),
        schema_version=str(payload.get("schema_version", DEDUP_DECISION_SCHEMA_VERSION)),
    )


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


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or uuid4().hex[:12]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
