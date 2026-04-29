from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.meta_analysis.extraction.schema_registry import EXTRACTION_SCHEMA_REGISTRY
from app.meta_analysis.models.protocol import (
    DEFAULT_PLANNED_DATABASES,
    PROTOCOL_STATUS_COMPLETED,
    PROTOCOL_STATUS_IN_PROGRESS,
    PROTOCOL_STATUS_NEEDS_REVIEW,
    PROTOCOL_STATUS_READY,
    PICOFramework,
    ProjectProtocol,
    ProtocolArtifactPaths,
    ProtocolSaveResult,
    new_protocol_id,
    protocol_from_dict,
    utc_now,
)
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.project_contract_service import MetaProjectContractService
from app.shared.data_center.service import DataCenter


PROTOCOL_RELATIVE_PATHS = ProtocolArtifactPaths(
    review_protocol="protocol/review_protocol.json",
    search_terms_draft="protocol/search_terms_draft.json",
    search_strategy_preview="protocol/search_strategy_preview.md",
    protocol_summary="protocol/protocol_summary.md",
)

CORE_PROTOCOL_FIELDS = (
    "project_title",
    "review_question",
    "meta_analysis_type",
    "population",
    "outcomes",
    "primary_outcome",
)


class ProjectProtocolService:
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

    def protocol_paths(self, project_dir: Path) -> ProtocolArtifactPaths:
        project_dir = project_dir.expanduser().resolve()
        return ProtocolArtifactPaths(
            review_protocol=str(project_dir / PROTOCOL_RELATIVE_PATHS.review_protocol),
            search_terms_draft=str(project_dir / PROTOCOL_RELATIVE_PATHS.search_terms_draft),
            search_strategy_preview=str(project_dir / PROTOCOL_RELATIVE_PATHS.search_strategy_preview),
            protocol_summary=str(project_dir / PROTOCOL_RELATIVE_PATHS.protocol_summary),
        )

    def load_protocol(self, project_dir: Path) -> ProjectProtocol | None:
        path = project_dir.expanduser().resolve() / PROTOCOL_RELATIVE_PATHS.review_protocol
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        return protocol_from_dict(payload) if isinstance(payload, dict) else None

    def build_protocol(self, project_dir: Path, values: dict[str, Any], *, confirmed: bool = False) -> ProjectProtocol:
        project_dir = project_dir.expanduser().resolve()
        existing = self.load_protocol(project_dir)
        now = utc_now()
        protocol_id = str(values.get("protocol_id") or (existing.protocol_id if existing else new_protocol_id()))
        created_at = str(values.get("created_at") or (existing.created_at if existing else now))
        pico = PICOFramework(
            population=_string_value(values, "population", existing.pico.population if existing else ""),
            intervention_or_exposure=_string_value(values, "intervention_or_exposure", existing.pico.intervention_or_exposure if existing else ""),
            comparator=_string_value(values, "comparator", existing.pico.comparator if existing else ""),
            outcomes=tuple(_list_value(values.get("outcomes", existing.pico.outcomes if existing else ()))),
            study_design=_string_value(values, "study_design", existing.pico.study_design if existing else ""),
        )
        meta_analysis_type = _string_value(values, "meta_analysis_type", existing.meta_analysis_type if existing else "")
        method_profile_id = _string_value(values, "method_profile_id", existing.method_profile_id if existing else meta_analysis_type)
        warnings = tuple(self.validate_protocol_fields(values, pico=pico, meta_analysis_type=meta_analysis_type, method_profile_id=method_profile_id))
        is_confirmed = bool(confirmed or values.get("confirmed", False))
        readiness = _readiness_status(warnings, confirmed=is_confirmed)
        return ProjectProtocol(
            project_id=str(values.get("project_id") or project_dir.name),
            protocol_id=protocol_id,
            project_title=_string_value(values, "project_title", existing.project_title if existing else ""),
            review_question=_string_value(values, "review_question", existing.review_question if existing else ""),
            background=_string_value(values, "background", existing.background if existing else ""),
            rationale=_string_value(values, "rationale", existing.rationale if existing else ""),
            objective=_string_value(values, "objective", existing.objective if existing else ""),
            meta_analysis_type=meta_analysis_type,
            method_profile_id=method_profile_id,
            pico=pico,
            primary_outcome=_string_value(values, "primary_outcome", existing.primary_outcome if existing else ""),
            secondary_outcomes=tuple(_list_value(values.get("secondary_outcomes", existing.secondary_outcomes if existing else ()))),
            eligible_study_designs=tuple(_list_value(values.get("eligible_study_designs", existing.eligible_study_designs if existing else ()))),
            planned_databases=tuple(_list_value(values.get("planned_databases", existing.planned_databases if existing else DEFAULT_PLANNED_DATABASES))),
            custom_databases=tuple(_list_value(values.get("custom_databases", existing.custom_databases if existing else ()))),
            search_date=_string_value(values, "search_date", existing.search_date if existing else ""),
            language_restriction=_string_value(values, "language_restriction", existing.language_restriction if existing else ""),
            date_range_restriction=_string_value(values, "date_range_restriction", existing.date_range_restriction if existing else ""),
            notes=_string_value(values, "notes", existing.notes if existing else ""),
            developer_preview=True,
            readiness_status=readiness,
            confirmed=is_confirmed,
            warnings=warnings,
            created_at=created_at,
            updated_at=now,
            confirmed_at=now if is_confirmed else "",
        )

    def validate_protocol_fields(
        self,
        values: dict[str, Any],
        *,
        pico: PICOFramework | None = None,
        meta_analysis_type: str = "",
        method_profile_id: str = "",
    ) -> list[str]:
        pico = pico or PICOFramework()
        warnings: list[str] = []
        if not _string_value(values, "project_title"):
            warnings.append("missing_project_title")
        if not _string_value(values, "review_question"):
            warnings.append("missing_review_question")
        if not meta_analysis_type:
            warnings.append("missing_meta_analysis_type")
        if method_profile_id and method_profile_id not in EXTRACTION_SCHEMA_REGISTRY:
            warnings.append(f"unknown_method_profile:{method_profile_id}")
        if not pico.population:
            warnings.append("missing_population")
        if not pico.outcomes:
            warnings.append("missing_outcomes")
        if not _string_value(values, "primary_outcome"):
            warnings.append("missing_primary_outcome")
        if not _list_value(values.get("planned_databases", DEFAULT_PLANNED_DATABASES)):
            warnings.append("missing_planned_databases")
        if not _string_value(values, "search_date"):
            warnings.append("missing_search_date")
        return warnings

    def save_protocol(self, project_dir: Path, values: dict[str, Any], *, confirmed: bool = False) -> ProtocolSaveResult:
        project_dir = project_dir.expanduser().resolve()
        self._project_contract.ensure_project_structure(project_dir)
        protocol = self.build_protocol(project_dir, values, confirmed=confirmed)
        terms = self.build_search_terms(protocol)
        strategy_preview = self.build_search_strategy_preview(protocol, terms)
        summary = self.build_protocol_summary(protocol)

        paths = self.protocol_paths(project_dir)
        _write_json(Path(paths.review_protocol), protocol.to_dict())
        _write_json(Path(paths.search_terms_draft), terms)
        Path(paths.search_strategy_preview).parent.mkdir(parents=True, exist_ok=True)
        Path(paths.search_strategy_preview).write_text(strategy_preview, encoding="utf-8")
        Path(paths.protocol_summary).parent.mkdir(parents=True, exist_ok=True)
        Path(paths.protocol_summary).write_text(summary, encoding="utf-8")

        self._register_assets(protocol.project_id, project_dir, paths)
        self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=protocol.project_id,
            target_type="review_protocol",
            target_id=protocol.protocol_id,
            source_path="Protocol / Research Question page",
            output_path=PROTOCOL_RELATIVE_PATHS.review_protocol,
            summary="Protocol / PICO-PICOS draft saved",
            details={
                "readiness_status": protocol.readiness_status,
                "warnings": list(protocol.warnings),
                "developer_preview": protocol.developer_preview,
            },
        )
        self._project_contract.write_project_manifests(project_dir)
        message = "Protocol saved as Developer Preview / testing draft."
        if protocol.confirmed:
            message = "Protocol confirmed for Literature Import handoff in Developer Preview."
        return ProtocolSaveResult(
            success=True,
            protocol=protocol,
            artifact_paths=paths,
            warnings=protocol.warnings,
            message=message,
        )

    def build_search_terms(self, protocol: ProjectProtocol) -> dict[str, object]:
        groups = {
            "population": protocol.pico.population,
            "intervention_or_exposure": protocol.pico.intervention_or_exposure,
            "comparator": protocol.pico.comparator,
            "outcomes": "; ".join(protocol.pico.outcomes),
            "study_design": protocol.pico.study_design or "; ".join(protocol.eligible_study_designs),
        }
        structured_groups = {
            key: {
                "free_text_terms": _term_list(value),
                "synonyms": [],
                "mesh_placeholder": f"Add reviewed MeSH terms for {key}.",
                "chinese_terms_placeholder": f"Add reviewed Chinese terms for {key}.",
            }
            for key, value in groups.items()
        }
        return {
            "schema_version": "meta_protocol_search_terms.v1",
            "protocol_id": protocol.protocol_id,
            "project_id": protocol.project_id,
            "status": "draft_needs_review",
            "developer_preview": True,
            "term_groups": structured_groups,
            "planned_databases": list(protocol.planned_databases),
            "warnings": list(protocol.warnings),
        }

    def build_search_strategy_preview(self, protocol: ProjectProtocol, terms: dict[str, object]) -> str:
        term_groups = dict(terms.get("term_groups", {}))
        pubmed = _pubmed_query(term_groups)
        web_of_science = _web_of_science_query(term_groups)
        cnki = _chinese_query(term_groups, database="CNKI")
        wanfang = _chinese_query(term_groups, database="WanFang")
        lines = [
            "# Search Strategy Preview",
            "",
            "Status: draft / needs reviewer validation. This is not a final publication-grade strategy.",
            f"Protocol ID: {protocol.protocol_id}",
            f"Search date: {protocol.search_date or 'not recorded'}",
            "",
            "## PubMed draft",
            "```text",
            pubmed or "Add PICO terms before running PubMed search.",
            "```",
            "",
            "## Web of Science draft",
            "```text",
            web_of_science or "Add PICO terms before running Web of Science search.",
            "```",
            "",
            "## CNKI draft",
            "```text",
            cnki or "请补充中文关键词后在 CNKI 中人工测试。",
            "```",
            "",
            "## WanFang draft",
            "```text",
            wanfang or "请补充中文关键词后在万方中人工测试。",
            "```",
            "",
            "## Notes",
            "- MeSH, Chinese terms, syntax limits, and database-specific filters require manual review.",
            "- No live database search is executed in this Developer Preview stage.",
        ]
        return "\n".join(lines) + "\n"

    def build_protocol_summary(self, protocol: ProjectProtocol) -> str:
        return "\n".join(
            [
                "# Protocol Summary",
                "",
                f"Status: {protocol.readiness_status} / Developer Preview testing",
                f"Project title: {protocol.project_title or 'missing'}",
                f"Review question: {protocol.review_question or 'missing'}",
                f"Meta-analysis type: {protocol.meta_analysis_type or 'missing'}",
                f"Method profile: {protocol.method_profile_id or 'missing'}",
                "",
                "## PICO/PICOS",
                f"- Population: {protocol.pico.population or 'missing'}",
                f"- Intervention/exposure: {protocol.pico.intervention_or_exposure or 'missing'}",
                f"- Comparator: {protocol.pico.comparator or 'missing'}",
                f"- Outcomes: {', '.join(protocol.pico.outcomes) or 'missing'}",
                f"- Study design: {protocol.pico.study_design or 'missing'}",
                "",
                f"Primary outcome: {protocol.primary_outcome or 'missing'}",
                f"Secondary outcomes: {', '.join(protocol.secondary_outcomes) or 'none recorded'}",
                f"Planned databases: {', '.join(protocol.planned_databases) or 'missing'}",
                f"Search date: {protocol.search_date or 'missing'}",
                "",
                "## Warnings",
                "\n".join(f"- {warning}" for warning in protocol.warnings) if protocol.warnings else "- none",
                "",
                "## Testing limitation",
                "Search strategy drafts are copyable starting points only and require reviewer validation.",
                "",
            ]
        )

    def _register_assets(self, project_id: str, project_dir: Path, paths: ProtocolArtifactPaths) -> None:
        for data_type, path in (
            ("review_protocol", paths.review_protocol),
            ("search_terms_draft", paths.search_terms_draft),
            ("search_strategy_preview", paths.search_strategy_preview),
            ("protocol_summary", paths.protocol_summary),
        ):
            self._data_center.register_asset(
                project_id=project_id,
                module="meta_analysis",
                data_type=data_type,
                source_path=str(project_dir),
                output_path=path,
                status="testing",
            )


def _readiness_status(warnings: tuple[str, ...], *, confirmed: bool) -> str:
    if confirmed and not warnings:
        return PROTOCOL_STATUS_COMPLETED
    if warnings:
        return PROTOCOL_STATUS_NEEDS_REVIEW
    return PROTOCOL_STATUS_READY


def _string_value(values: dict[str, Any], key: str, fallback: str = "") -> str:
    value = values.get(key, fallback)
    return str(value).strip() if value is not None else ""


def _list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[;,]\s*|\n+", value) if item.strip()]
    return [str(value).strip()] if str(value).strip() else []


def _term_list(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"\s+OR\s+|[;,]\s*|\n+", value, flags=re.IGNORECASE) if item.strip()]


def _group_terms(term_groups: dict[str, object], key: str) -> list[str]:
    group = term_groups.get(key, {})
    if not isinstance(group, dict):
        return []
    terms = group.get("free_text_terms", [])
    return [str(item).strip() for item in terms if str(item).strip()] if isinstance(terms, list) else []


def _pubmed_query(term_groups: dict[str, object]) -> str:
    groups = []
    for key in ("population", "intervention_or_exposure", "comparator", "outcomes", "study_design"):
        terms = _group_terms(term_groups, key)
        if terms:
            groups.append("(" + " OR ".join(f'"{term}"[Title/Abstract]' for term in terms) + ")")
    return " AND\n".join(groups)


def _web_of_science_query(term_groups: dict[str, object]) -> str:
    groups = []
    for key in ("population", "intervention_or_exposure", "comparator", "outcomes", "study_design"):
        terms = _group_terms(term_groups, key)
        if terms:
            groups.append("TS=(" + " OR ".join(f'"{term}"' for term in terms) + ")")
    return " AND\n".join(groups)


def _chinese_query(term_groups: dict[str, object], *, database: str) -> str:
    groups = []
    for key in ("population", "intervention_or_exposure", "comparator", "outcomes", "study_design"):
        terms = _group_terms(term_groups, key)
        if terms:
            prefix = "主题" if database == "CNKI" else "主题"
            groups.append(prefix + "=(" + " OR ".join(terms) + ")")
    return " AND\n".join(groups)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
