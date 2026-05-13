from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.meta_analysis.models.criteria import (
    DEFAULT_EXCLUSION_CRITERIA,
    DEFAULT_INCLUSION_CRITERIA,
    CriteriaSet,
    Criterion,
    criteria_set_from_dict,
    criterion_from_label,
    new_criteria_id,
    utc_now,
)
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.project_contract_service import MetaProjectContractService
from app.shared.data_center.service import DataCenter


CRITERIA_PATHS = {
    "inclusion_criteria": "criteria/inclusion_criteria.json",
    "exclusion_criteria": "criteria/exclusion_criteria.json",
    "criteria_summary": "criteria/criteria_summary.md",
}


class CriteriaBuilderService:
    def __init__(
        self,
        *,
        data_center: DataCenter | None = None,
        audit_log: MetaAuditLogService | None = None,
        project_contract: MetaProjectContractService | None = None,
    ) -> None:
        self._data_center = data_center or DataCenter.default()
        self._audit_log = audit_log or MetaAuditLogService()
        self._project_contract = project_contract or MetaProjectContractService(data_center=self._data_center)

    def default_inclusion_criteria(self) -> tuple[Criterion, ...]:
        return tuple(criterion_from_label(label, category="inclusion", index=index, required=index < 3) for index, label in enumerate(DEFAULT_INCLUSION_CRITERIA))

    def default_exclusion_criteria(self) -> tuple[Criterion, ...]:
        return tuple(criterion_from_label(label, category="exclusion", index=index) for index, label in enumerate(DEFAULT_EXCLUSION_CRITERIA))

    def load_criteria(self, project_dir: Path) -> CriteriaSet | None:
        project_dir = project_dir.expanduser().resolve()
        inclusion_path = project_dir / CRITERIA_PATHS["inclusion_criteria"]
        exclusion_path = project_dir / CRITERIA_PATHS["exclusion_criteria"]
        if not inclusion_path.exists() and not exclusion_path.exists():
            return None
        inclusion_payload = _load_json(inclusion_path)
        exclusion_payload = _load_json(exclusion_path)
        combined = {
            "project_id": project_dir.name,
            "criteria_id": str(inclusion_payload.get("criteria_id") or exclusion_payload.get("criteria_id") or new_criteria_id()),
            "inclusion_criteria": inclusion_payload.get("inclusion_criteria", []),
            "exclusion_criteria": exclusion_payload.get("exclusion_criteria", []),
            "source_protocol_path": str(inclusion_payload.get("source_protocol_path") or exclusion_payload.get("source_protocol_path") or ""),
            "readiness_status": str(inclusion_payload.get("readiness_status") or exclusion_payload.get("readiness_status") or "needs_review"),
            "warnings": list(inclusion_payload.get("warnings", [])) + list(exclusion_payload.get("warnings", [])),
            "created_at": str(inclusion_payload.get("created_at") or exclusion_payload.get("created_at") or ""),
            "updated_at": str(inclusion_payload.get("updated_at") or exclusion_payload.get("updated_at") or ""),
        }
        return criteria_set_from_dict(combined)

    def build_criteria(
        self,
        project_dir: Path,
        *,
        inclusion_labels: list[str] | tuple[str, ...] | None = None,
        exclusion_labels: list[str] | tuple[str, ...] | None = None,
    ) -> CriteriaSet:
        project_dir = project_dir.expanduser().resolve()
        existing = self.load_criteria(project_dir)
        now = utc_now()
        inclusion = tuple(
            criterion_from_label(label, category="inclusion", index=index, required=index < 3)
            for index, label in enumerate(_labels_or_default(inclusion_labels, DEFAULT_INCLUSION_CRITERIA))
        )
        exclusion = tuple(
            criterion_from_label(label, category="exclusion", index=index)
            for index, label in enumerate(_labels_or_default(exclusion_labels, DEFAULT_EXCLUSION_CRITERIA))
        )
        warnings = tuple(self.validate_criteria(project_dir, inclusion, exclusion))
        return CriteriaSet(
            project_id=project_dir.name,
            criteria_id=existing.criteria_id if existing else new_criteria_id(),
            inclusion_criteria=inclusion,
            exclusion_criteria=exclusion,
            source_protocol_path="protocol/review_protocol.json" if (project_dir / "protocol" / "review_protocol.json").exists() else "",
            developer_preview=True,
            readiness_status="needs_review" if warnings else "ready",
            warnings=warnings,
            created_at=existing.created_at if existing and existing.created_at else now,
            updated_at=now,
        )

    def validate_criteria(self, project_dir: Path, inclusion: tuple[Criterion, ...], exclusion: tuple[Criterion, ...]) -> list[str]:
        warnings: list[str] = []
        if not (project_dir / "protocol" / "review_protocol.json").exists():
            warnings.append("missing_protocol_reference")
        if not inclusion:
            warnings.append("missing_inclusion_criteria")
        if not exclusion:
            warnings.append("missing_exclusion_criteria")
        labels = {criterion.label.strip().lower() for criterion in inclusion if criterion.label.strip()}
        overlap = [criterion.label for criterion in exclusion if criterion.label.strip().lower() in labels]
        if overlap:
            warnings.append("criteria_overlap:" + ",".join(overlap))
        return warnings

    def save_criteria(
        self,
        project_dir: Path,
        *,
        inclusion_labels: list[str] | tuple[str, ...] | None = None,
        exclusion_labels: list[str] | tuple[str, ...] | None = None,
    ) -> CriteriaSet:
        project_dir = project_dir.expanduser().resolve()
        self._project_contract.ensure_project_structure(project_dir)
        criteria = self.build_criteria(project_dir, inclusion_labels=inclusion_labels, exclusion_labels=exclusion_labels)
        inclusion_path = project_dir / CRITERIA_PATHS["inclusion_criteria"]
        exclusion_path = project_dir / CRITERIA_PATHS["exclusion_criteria"]
        summary_path = project_dir / CRITERIA_PATHS["criteria_summary"]
        _write_json(inclusion_path, {**_criteria_header(criteria), "inclusion_criteria": [item.to_dict() for item in criteria.inclusion_criteria]})
        _write_json(exclusion_path, {**_criteria_header(criteria), "exclusion_criteria": [item.to_dict() for item in criteria.exclusion_criteria]})
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(self.build_summary_markdown(criteria), encoding="utf-8")
        self._register_assets(project_dir, criteria)
        self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=criteria.project_id,
            target_type="criteria_builder",
            target_id=criteria.criteria_id,
            source_path=criteria.source_protocol_path,
            output_path=CRITERIA_PATHS["criteria_summary"],
            summary="Inclusion / exclusion criteria saved.",
            details={"warnings": list(criteria.warnings), "readiness_status": criteria.readiness_status},
        )
        self._project_contract.write_project_manifests(project_dir)
        return criteria

    def build_summary_markdown(self, criteria: CriteriaSet) -> str:
        return "\n".join(
            [
                "# Inclusion / Exclusion Criteria Summary",
                "",
                f"Status: {criteria.readiness_status} / Developer Preview testing",
                f"Criteria ID: {criteria.criteria_id}",
                f"Protocol source: {criteria.source_protocol_path or 'missing'}",
                "",
                "## Inclusion criteria",
                *[f"- {item.label}" for item in criteria.inclusion_criteria],
                "",
                "## Exclusion criteria",
                *[f"- {item.label}" for item in criteria.exclusion_criteria],
                "",
                "## Warnings",
                *([f"- {warning}" for warning in criteria.warnings] if criteria.warnings else ["- none"]),
                "",
                "## Testing limitation",
                "Criteria guide reviewer decisions; they do not automatically change screening or full-text decisions.",
                "",
            ]
        )

    def criteria_hints(self, project_dir: Path, *, stage: str = "title_abstract") -> tuple[str, ...]:
        criteria = self.load_criteria(project_dir)
        if criteria is None:
            return ()
        inclusion = [f"Include if: {item.label}" for item in criteria.inclusion_criteria if stage in item.applies_to_stage]
        exclusion = [f"Exclude if: {item.label}" for item in criteria.exclusion_criteria if stage in item.applies_to_stage]
        return tuple(inclusion + exclusion)

    def _register_assets(self, project_dir: Path, criteria: CriteriaSet) -> None:
        for data_type, relative in CRITERIA_PATHS.items():
            self._data_center.register_asset(
                project_id=criteria.project_id,
                module="meta_analysis",
                data_type=data_type,
                source_path=criteria.source_protocol_path or str(project_dir),
                output_path=str(project_dir / relative),
                status="testing",
            )


def _criteria_header(criteria: CriteriaSet) -> dict[str, Any]:
    return {
        "project_id": criteria.project_id,
        "criteria_id": criteria.criteria_id,
        "source_protocol_path": criteria.source_protocol_path,
        "developer_preview": criteria.developer_preview,
        "readiness_status": criteria.readiness_status,
        "warnings": list(criteria.warnings),
        "created_at": criteria.created_at,
        "updated_at": criteria.updated_at,
    }


def _labels_or_default(values: list[str] | tuple[str, ...] | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if values is None:
        return default
    return tuple(str(item).strip() for item in values if str(item).strip())


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
