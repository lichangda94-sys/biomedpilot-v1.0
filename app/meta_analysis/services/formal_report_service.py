from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.models.prisma import (
    PRISMAFlowSummary,
    now_utc,
    prisma_flow_summary_from_dict,
    prisma_flow_summary_to_dict,
)
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.report_manifest_service import ReportManifestService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType
from app.meta_analysis.models.statistical_result_state import (
    STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN,
    STATISTICAL_RESULT_STATE_FAILED_VALIDATION,
    STATISTICAL_RESULT_STATE_NOT_RUN,
    blocks_formal_report_claim,
    statistical_result_state_label_zh,
)


DRAFT_REPORT_M8_SCHEMA_VERSION = "meta_draft_report.m8"


class PRISMAService:
    def __init__(
        self,
        *,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        audit_log: MetaAuditLogService | None = None,
    ) -> None:
        self._task_center = task_center
        self._data_center = data_center
        self._audit_log = audit_log or MetaAuditLogService()

    def collect_prisma_numbers(self, project_dir: Path) -> PRISMAFlowSummary:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_dir.name
        task = self._start_task(
            project_id=project_id,
            task_type=TaskType.PRISMA_COLLECT,
            title="PRISMA Collect",
            summary=f"Collecting PRISMA numbers from {project_dir}",
        )
        payloads = _load_project_json_payloads(project_dir)
        records_identified = _max_count(payloads, ("records", "literature_records", "imported_records"))
        duplicates_removed = _duplicates_removed_from_decisions(payloads)
        records_after_deduplication = _max_count(payloads, ("deduplicated_records", "unique_records"))
        screening_records = _screening_records(payloads)
        decision_counts = _decision_counts(screening_records)
        records_screened = len(screening_records)
        included_or_maybe = decision_counts.get("included", 0) + decision_counts.get("maybe", 0)
        studies_included = decision_counts.get("included", 0)
        if records_after_deduplication == 0:
            records_after_deduplication = max(records_identified - duplicates_removed, 0) if duplicates_removed else records_screened or records_identified
        if studies_included == 0:
            studies_included = _max_count(payloads, ("records",), path_contains="extraction_records")
        audit_sources = self._audit_source_refs(project_dir)
        data_sources = [str(path.relative_to(project_dir)) for path, _payload in payloads]
        for source in audit_sources:
            if source not in data_sources:
                data_sources.append(source)
        source_references = _prisma_source_references(project_dir, payloads, audit_sources)
        summary = PRISMAFlowSummary(
            records_identified=records_identified,
            records_after_deduplication=records_after_deduplication,
            records_screened=records_screened,
            records_excluded_title_abstract=decision_counts.get("excluded", 0),
            full_text_reports_sought=included_or_maybe,
            full_text_reports_assessed=included_or_maybe,
            full_text_reports_excluded=0,
            full_text_exclusion_reasons={},
            studies_included=studies_included,
            reports_included=studies_included,
            data_sources=data_sources,
            notes=["full-text workflow incomplete; full-text PRISMA counts are testing estimates.", "PRISMA sources include ImportBatch, DuplicateReviewDecision, ScreeningRecord, FulltextStatus, ExtractionRecord, and AnalysisInput when available."],
            created_at=now_utc(),
            source_references=source_references,
            duplicates_removed=duplicates_removed,
        )
        self._finish_task(task, success=True, summary="PRISMA flow summary collected.")
        return summary

    def collect_literature_acquisition_summary(self, project_dir: Path) -> dict[str, object]:
        project_dir = project_dir.expanduser().resolve()
        from app.meta_analysis.services.literature_library_service import LiteratureLibraryService

        records = LiteratureLibraryService().list_records(project_dir)
        dedup_payload = _load_json(project_dir / "deduplication" / "deduplicated_literature_v2.json")
        queue_payload = _load_json(project_dir / "screening" / "title_abstract_queue_v2.json")
        flow = self.collect_prisma_numbers(project_dir)
        pubmed_count = sum(1 for record in records if _is_pubmed_source(record))
        total = len(records)
        has_dedup = bool(dedup_payload)
        unresolved = list(dedup_payload.get("unresolved_group_ids", [])) if isinstance(dedup_payload, dict) else []
        after_dedup = int(dedup_payload.get("deduplicated_count", 0) or flow.records_after_deduplication) if has_dedup else flow.records_after_deduplication
        ready = int(queue_payload.get("record_count", 0) or after_dedup or total) if has_dedup or queue_payload else 0
        return {
            "records_identified_from_pubmed": pubmed_count,
            "records_identified_from_local_imports": max(total - pubmed_count, 0),
            "total_records_before_deduplication": total,
            "duplicate_records_removed": int(dedup_payload.get("duplicate_records_removed", flow.duplicates_removed) if has_dedup else flow.duplicates_removed),
            "records_after_deduplication": after_dedup,
            "records_ready_for_title_abstract_screening": ready,
            "deduplication_status": "completed" if has_dedup and not unresolved else "preliminary",
            "unresolved_duplicate_group_count": len(unresolved),
            "screening_queue_record_count": int(queue_payload.get("record_count", 0) or 0) if isinstance(queue_payload, dict) else 0,
            "notes": ["去重完成后数字会更新"] if not has_dedup or unresolved else [],
        }

    def _audit_source_refs(self, project_dir: Path) -> list[str]:
        refs: list[str] = []
        for event in self._audit_log.list_events(project_dir):
            source_type = {
                "import_batch_created": "ImportBatch",
                "duplicate_decision": "DuplicateReviewDecision",
                "screening_decision": "ScreeningRecord",
                "fulltext_status_changed": "FulltextStatus",
                "extraction_updated": "ExtractionRecord",
                "analysis_run_completed": "AnalysisInput",
            }.get(event.event_type)
            if source_type:
                refs.append(f"audit:{source_type}:{event.target_id}")
        return refs

    def save_prisma_flow_summary(self, project_dir: Path, summary: PRISMAFlowSummary) -> Path:
        project_dir = project_dir.expanduser().resolve()
        output_path = project_dir / "reports" / "prisma_flow_summary.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(prisma_flow_summary_to_dict(summary), ensure_ascii=False, indent=2), encoding="utf-8")
        self._register_asset(
            project_id=project_dir.name,
            data_type="prisma_flow_summary",
            source_path=str(project_dir),
            output_path=str(output_path),
        )
        return output_path

    def load_prisma_flow_summary(self, project_dir: Path) -> PRISMAFlowSummary | None:
        path = project_dir.expanduser().resolve() / "reports" / "prisma_flow_summary.json"
        if not path.exists():
            return None
        return prisma_flow_summary_from_dict(json.loads(path.read_text(encoding="utf-8")))

    def export_prisma_flow_markdown(self, project_dir: Path, summary: PRISMAFlowSummary) -> Path:
        project_dir = project_dir.expanduser().resolve()
        output_path = project_dir / "reports" / "prisma_flow_summary.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_prisma_markdown(summary), encoding="utf-8")
        return output_path

    def export_simplified_prisma_flow(self, project_dir: Path, summary: PRISMAFlowSummary) -> dict[str, Path]:
        project_dir = project_dir.expanduser().resolve()
        reports_dir = project_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        summary_json = reports_dir / "prisma_summary.json"
        flow_markdown = reports_dir / "prisma_flow.md"
        flow_svg = reports_dir / "prisma_flow.svg"
        summary_json.write_text(json.dumps(prisma_flow_summary_to_dict(summary), ensure_ascii=False, indent=2), encoding="utf-8")
        flow_markdown.write_text(_simplified_prisma_flow_markdown(summary), encoding="utf-8")
        flow_svg.write_text(_simplified_prisma_flow_svg(summary), encoding="utf-8")
        self._register_asset(
            project_id=project_dir.name,
            data_type="prisma_summary",
            source_path=str(project_dir),
            output_path=str(summary_json),
        )
        self._register_asset(
            project_id=project_dir.name,
            data_type="simplified_prisma_flow",
            source_path=str(summary_json),
            output_path=str(flow_svg),
        )
        return {"summary_json": summary_json, "flow_markdown": flow_markdown, "flow_svg": flow_svg}

    def _register_asset(self, *, project_id: str, data_type: str, source_path: str, output_path: str) -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(
            project_id=project_id,
            module="meta_analysis",
            data_type=data_type,
            source_path=source_path,
            output_path=output_path,
            status="available",
        )

    def _start_task(self, *, project_id: str, task_type: TaskType, title: str, summary: str) -> TaskRecord:
        now = now_utc()
        if self._task_center is None:
            return TaskRecord(
                task_id=f"task-{uuid4().hex[:12]}",
                task_type=task_type,
                status=TaskStatus.RUNNING,
                module="meta_analysis",
                title=title,
                created_at=now,
                updated_at=now,
                project_id=project_id,
                started_at=now,
                summary=summary,
            )
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=task_type,
            module="meta_analysis",
            title=title,
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=summary,
        )

    def _finish_task(self, task: TaskRecord, *, success: bool, summary: str) -> None:
        if self._task_center is None:
            return
        now = now_utc()
        self._task_center.save_task(
            TaskRecord(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED if success else TaskStatus.FAILED,
                module=task.module,
                title=task.title,
                created_at=task.created_at,
                updated_at=now,
                project_id=task.project_id,
                started_at=task.started_at,
                finished_at=now,
                summary=summary,
                error_message="" if success else summary,
            )
        )


class FormalMarkdownReportBuilder:
    def __init__(
        self,
        *,
        prisma_service: PRISMAService | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        audit_log: MetaAuditLogService | None = None,
    ) -> None:
        self._audit_log = audit_log or MetaAuditLogService()
        self._prisma_service = prisma_service or PRISMAService(task_center=task_center, data_center=data_center, audit_log=self._audit_log)
        self._task_center = task_center
        self._data_center = data_center
        self._report_manifest_service = ReportManifestService()

    def build_formal_markdown_report(self, project_dir: Path) -> Path:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(project_id=project_dir.name)
        summary = self._prisma_service.load_prisma_flow_summary(project_dir)
        if summary is None:
            summary = self._prisma_service.collect_prisma_numbers(project_dir)
            self._prisma_service.save_prisma_flow_summary(project_dir, summary)
            self._prisma_service.export_prisma_flow_markdown(project_dir, summary)
        if not (project_dir / "reports" / "prisma_flow.svg").exists():
            self._prisma_service.export_simplified_prisma_flow(project_dir, summary)
        artifact_summary = _artifact_summary(project_dir)
        output_path = project_dir / "reports" / "formal_meta_report.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_formal_report_markdown(project_dir, summary, artifact_summary), encoding="utf-8")
        self._report_manifest_service.save_report_manifest(project_dir)
        self._register_asset(
            project_id=project_dir.name,
            data_type="formal_meta_report",
            source_path=str(project_dir),
            output_path=str(output_path),
        )
        self._audit_log.record_event(
            project_dir,
            event_type="report_exported",
            project_id=project_dir.name,
            target_type="formal_meta_report",
            target_id="formal_meta_report.md",
            source_path=str(project_dir),
            output_path=str(output_path),
            summary="Formal markdown report exported.",
        )
        self._finish_task(task, success=True, summary=f"Formal markdown report exported: {output_path}")
        return output_path

    def build_draft_markdown_report(self, project_dir: Path) -> Path:
        return self.build_formal_markdown_report(project_dir)

    def _start_task(self, *, project_id: str) -> TaskRecord:
        now = now_utc()
        if self._task_center is None:
            return TaskRecord(
                task_id=f"task-{uuid4().hex[:12]}",
                task_type=TaskType.FORMAL_REPORT_EXPORT,
                status=TaskStatus.RUNNING,
                module="meta_analysis",
                title="Formal Markdown Report Export",
                created_at=now,
                updated_at=now,
                project_id=project_id,
                started_at=now,
                summary="Exporting formal markdown report",
            )
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.FORMAL_REPORT_EXPORT,
            module="meta_analysis",
            title="Formal Markdown Report Export",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary="Exporting formal markdown report",
        )

    def _finish_task(self, task: TaskRecord, *, success: bool, summary: str) -> None:
        if self._task_center is None:
            return
        now = now_utc()
        self._task_center.save_task(
            TaskRecord(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED if success else TaskStatus.FAILED,
                module=task.module,
                title=task.title,
                created_at=task.created_at,
                updated_at=now,
                project_id=task.project_id,
                started_at=task.started_at,
                finished_at=now,
                summary=summary,
                error_message="" if success else summary,
            )
        )

    def _register_asset(self, *, project_id: str, data_type: str, source_path: str, output_path: str) -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(
            project_id=project_id,
            module="meta_analysis",
            data_type=data_type,
            source_path=source_path,
            output_path=output_path,
            status="available",
        )


def _load_project_json_payloads(project_dir: Path) -> list[tuple[Path, dict[str, object]]]:
    payloads: list[tuple[Path, dict[str, object]]] = []
    if not project_dir.exists():
        return payloads
    for path in sorted(project_dir.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(payload, dict):
            if payload.get("schema_version") == "meta_pubmed_search_execution.v1":
                continue
            payloads.append((path, payload))
    return payloads


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _max_count(payloads: list[tuple[Path, dict[str, object]]], keys: tuple[str, ...], path_contains: str = "") -> int:
    counts: list[int] = []
    for path, payload in payloads:
        if path_contains and path_contains not in path.name:
            continue
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                counts.append(len(value))
    return max(counts, default=0)


def _screening_records(payloads: list[tuple[Path, dict[str, object]]]) -> list[dict[str, object]]:
    best: list[dict[str, object]] = []
    for _path, payload in payloads:
        records = payload.get("screening_records")
        if isinstance(records, list) and len(records) > len(best):
            best = [dict(item) for item in records if isinstance(item, dict)]
    return best


def _decision_counts(records: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        decision = str(record.get("decision", "pending")).lower()
        if decision not in {"included", "excluded", "maybe", "pending"}:
            decision = str(record.get("legacy_decision") or decision).lower()
        if decision == "need_full_text":
            decision = "maybe"
        counts[decision] = counts.get(decision, 0) + 1
    return counts


def _is_pubmed_source(record: dict[str, object]) -> bool:
    source = f"{record.get('source_type', '')} {record.get('database_source', '')} {record.get('source_database', '')}".lower()
    return "pubmed" in source or bool(str(record.get("pmid", "")).strip() and not source.strip())


def _duplicates_removed_from_decisions(payloads: list[tuple[Path, dict[str, object]]]) -> int:
    group_sizes: dict[str, int] = {}
    for _path, payload in payloads:
        for group in list(payload.get("duplicate_groups", [])):
            if not isinstance(group, dict):
                continue
            group_id = str(group.get("group_id") or group.get("duplicate_group_id", ""))
            record_ids = list(group.get("record_ids") or group.get("candidate_record_ids") or [])
            if group_id:
                group_sizes[group_id] = len(record_ids)

    removed = 0
    for _path, payload in payloads:
        for decision in list(payload.get("decisions", [])):
            if not isinstance(decision, dict):
                continue
            decision_type = str(decision.get("decision", "")).lower()
            group_size = group_sizes.get(str(decision.get("group_id", "")), 0)
            if group_size < 1:
                continue
            if decision_type in {"keep_first", "keep_second", "merge", "set_master_record"}:
                removed += max(group_size - 1, 0)
            elif decision_type == "exclude_duplicate":
                removed += group_size
    return removed


def _prisma_source_references(project_dir: Path, payloads: list[tuple[Path, dict[str, object]]], audit_sources: list[str]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    source_map = {
        "ImportBatch": ("batch_id", "literature"),
        "DuplicateReviewDecision": ("decisions", "dedup"),
        "ScreeningRecord": ("screening_records", "screening"),
        "FulltextStatus": ("fulltext_files", "fulltext"),
        "ExtractionRecord": ("records", "extraction_records"),
        "AnalysisInput": ("datasets", "analysis_ready"),
    }
    for source_type, (_key, name_hint) in source_map.items():
        match = next((path for path, _payload in payloads if name_hint in path.name or name_hint in str(path.relative_to(project_dir))), None)
        if match is not None:
            refs.append({"source_type": source_type, "path": str(match.relative_to(project_dir)), "status": "available"})
        else:
            refs.append({"source_type": source_type, "path": "", "status": "missing"})
    refs.extend({"source_type": source.split(":")[1], "path": source, "status": "audit"} for source in audit_sources if source.startswith("audit:"))
    return refs


def _prisma_markdown(summary: PRISMAFlowSummary) -> str:
    return "\n".join(
        [
            "# PRISMA Flow Summary",
            "",
            f"- Records identified: {summary.records_identified}",
            f"- Records after deduplication: {summary.records_after_deduplication}",
            f"- Duplicates removed: {summary.duplicates_removed}",
            f"- Records screened: {summary.records_screened}",
            f"- Records excluded title/abstract: {summary.records_excluded_title_abstract}",
            f"- Full-text reports sought: {summary.full_text_reports_sought}",
            f"- Full-text reports assessed: {summary.full_text_reports_assessed}",
            f"- Full-text reports excluded: {summary.full_text_reports_excluded}",
            f"- Studies included: {summary.studies_included}",
            f"- Reports included: {summary.reports_included}",
            "",
            "## Notes",
            *[f"- {note}" for note in summary.notes],
            "",
            "## Source References",
            *[
                f"- {ref.get('source_type', '')}: {ref.get('status', '')} {ref.get('path', '')}".rstrip()
                for ref in summary.source_references
            ],
            "",
        ]
    )


def _simplified_prisma_flow_markdown(summary: PRISMAFlowSummary) -> str:
    return "\n".join(
        [
            "# Simplified PRISMA Flow (Testing)",
            "",
            "> Developer Preview: this is a simplified testing diagram, not a formal PRISMA 2020 figure.",
            "",
            f"- Records identified: {summary.records_identified}",
            f"- Duplicates removed: {summary.duplicates_removed}",
            f"- Records after deduplication: {summary.records_after_deduplication}",
            f"- Records screened: {summary.records_screened}",
            f"- Title/abstract exclusions: {summary.records_excluded_title_abstract}",
            f"- Full-text reports sought: {summary.full_text_reports_sought}",
            f"- Full-text reports assessed: {summary.full_text_reports_assessed}",
            f"- Full-text reports excluded: {summary.full_text_reports_excluded}",
            f"- Studies included: {summary.studies_included}",
            "",
            "## Source References",
            *[f"- {item.get('source_type', '')}: {item.get('path', '')} ({item.get('status', '')})" for item in summary.source_references],
            "",
            "## Notes",
            *[f"- {note}" for note in summary.notes],
            "",
        ]
    )


def _simplified_prisma_flow_svg(summary: PRISMAFlowSummary) -> str:
    boxes = [
        ("Records identified", summary.records_identified, 30, 30),
        ("Duplicates removed", summary.duplicates_removed, 360, 30),
        ("Records after deduplication", summary.records_after_deduplication, 30, 145),
        ("Records screened", summary.records_screened, 30, 260),
        ("Title/abstract excluded", summary.records_excluded_title_abstract, 360, 260),
        ("Full-text sought", summary.full_text_reports_sought, 30, 375),
        ("Full-text excluded", summary.full_text_reports_excluded, 360, 375),
        ("Studies included", summary.studies_included, 30, 490),
    ]
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="700" height="650" viewBox="0 0 700 650" role="img" aria-label="Simplified testing PRISMA flow">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="7" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L8,3 z" fill="#475569"/></marker></defs>',
        '<rect width="700" height="650" fill="#ffffff"/>',
        '<text x="30" y="625" font-family="Arial, sans-serif" font-size="13" fill="#7a4a00">Developer Preview: simplified testing flow, not formal PRISMA 2020.</text>',
    ]
    for label, value, x, y in boxes:
        lines.append(f'<rect x="{x}" y="{y}" width="270" height="70" rx="6" fill="#f8fafc" stroke="#64748b" stroke-width="1.5"/>')
        lines.append(f'<text x="{x + 18}" y="{y + 30}" font-family="Arial, sans-serif" font-size="15" fill="#0f172a">{_svg_escape(label)}</text>')
        lines.append(f'<text x="{x + 18}" y="{y + 55}" font-family="Arial, sans-serif" font-size="22" font-weight="700" fill="#0f172a">{value}</text>')
    for x1, y1, x2, y2 in (
        (165, 100, 165, 145),
        (165, 215, 165, 260),
        (165, 330, 165, 375),
        (165, 445, 165, 490),
        (300, 65, 360, 65),
        (300, 295, 360, 295),
        (300, 410, 360, 410),
    ):
        lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)"/>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _svg_escape(value: object) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _artifact_summary(project_dir: Path) -> dict[str, str]:
    checks = {
        "literature_records": "literature",
        "review_protocol": "review_protocol.json",
        "search_strategy_preview": "search_strategy_preview.md",
        "criteria_summary": "criteria_summary.md",
        "duplicate_candidate_groups": "duplicate_candidate",
        "deduplicated_literature": "deduplicated_literature",
        "screening_decisions": "screening",
        "extraction_records": "extraction_records.json",
        "analysis_plan": "analysis_plan.json",
        "analysis_ready_dataset": "analysis_ready_datasets.json",
        "analysis_result": "analysis_results.json",
        "applicability_warnings": "applicability_warnings.json",
        "forest_plot": "forest_plot_",
        "analysis_result_table": "analysis_result_table_",
        "subgroup_analysis_result": "subgroup_analysis_results.json",
        "leave_one_out_result": "leave_one_out_results.json",
        "publication_bias_result": "publication_bias_results.json",
        "funnel_plot": "funnel_plot_",
        "fulltext_registry": "fulltext_registry.json",
        "fulltext_screening_decisions": "fulltext_screening_decisions.json",
        "full_text_exclusion_report": "full_text_exclusion_report.csv",
        "quality_assessments": "quality_assessments.json",
        "quality_assessment_table": "quality_assessment_table.csv",
        "prisma_flow_svg": "prisma_flow.svg",
    }
    paths = [path for path in project_dir.rglob("*") if path.is_file()] if project_dir.exists() else []
    summary: dict[str, str] = {}
    for key, pattern in checks.items():
        match = next((path for path in paths if pattern in path.name), None)
        summary[key] = str(match) if match is not None else "missing / not generated"
    return summary


def _m8_report_state(project_dir: Path, prisma: PRISMAFlowSummary, artifacts: dict[str, str]) -> dict[str, Any]:
    screening = _safe_screening_summary(project_dir)
    fulltext = _safe_fulltext_summary(project_dir)
    extraction_rows = _safe_extraction_rows(project_dir)
    quality = _safe_quality_summary(project_dir, expected_study_ids=[str(row.get("study_id", "")) for row in extraction_rows if str(row.get("study_id", "")).strip()])
    plan = _safe_analysis_plan_summary(project_dir)
    statistical_result = _safe_statistical_result_state_summary(project_dir, plan_complete=bool(plan.get("complete")))
    literature_records = _load_literature_records(project_dir)
    source_counts: dict[str, int] = {}
    for record in literature_records:
        source = str(record.get("source_database") or record.get("database_source") or record.get("source") or "未标注").strip() or "未标注"
        source_counts[source] = source_counts.get(source, 0) + 1
    final_count = len([row for row in extraction_rows if str(row.get("confirmation_status", "")) in {"已确认", "用户完成"}])
    if final_count == 0:
        final_count = _analysis_ready_count(project_dir)
    missing_sections = _m8_missing_sections(artifacts, screening, fulltext, extraction_rows, quality, plan)
    return {
        "research_question_lines": _research_question_lines(project_dir),
        "source_summary": _format_counts(source_counts) if source_counts else "缺失",
        "dedup_status": _dedup_status(project_dir, prisma),
        "prisma_counts": {
            "imported_total": max(int(screening.get("imported_total", 0) or 0), prisma.records_identified),
            "after_dedup_total": max(int(screening.get("after_dedup_total", 0) or 0), prisma.records_after_deduplication),
            "title_abstract_included": int(screening.get("title_abstract_included", 0) or 0),
            "title_abstract_excluded": int(screening.get("title_abstract_excluded", 0) or prisma.records_excluded_title_abstract),
            "title_abstract_uncertain": int(screening.get("title_abstract_uncertain", 0) or 0),
            "full_text_needed": max(int(screening.get("full_text_needed", 0) or 0), int(fulltext.get("full_text_needed", 0) or 0), prisma.full_text_reports_sought),
            "full_text_confirmed": int(fulltext.get("full_text_confirmed", 0) or int(screening.get("full_text_included", 0) or 0)),
            "full_text_excluded": int(fulltext.get("full_text_excluded", 0) or int(screening.get("full_text_excluded", 0) or prisma.full_text_reports_excluded)),
            "full_text_unavailable": int(fulltext.get("full_text_unavailable", 0) or 0),
            "final_included_for_extraction": final_count,
        },
        "extraction_rows": extraction_rows,
        "quality_summary": quality,
        "analysis_plan": plan,
        "statistical_result": statistical_result,
        "missing_sections": missing_sections,
    }


def _safe_statistical_result_state_summary(project_dir: Path, *, plan_complete: bool) -> dict[str, Any]:
    result_payload = _load_json(project_dir / "analysis" / "analysis_result.json")
    result = result_payload.get("result") if isinstance(result_payload.get("result"), dict) else {}
    if not result:
        collection = _load_json(project_dir / "analysis" / "analysis_results.json")
        results = collection.get("results")
        if isinstance(results, list) and results and isinstance(results[-1], dict):
            result = dict(results[-1])
    warnings_payload = _load_json(project_dir / "analysis" / "applicability_warnings.json")
    errors = [str(item) for item in warnings_payload.get("errors", [])] if isinstance(warnings_payload.get("errors"), list) else []
    warnings = [str(item) for item in warnings_payload.get("warnings", [])] if isinstance(warnings_payload.get("warnings"), list) else []
    if errors:
        state = STATISTICAL_RESULT_STATE_FAILED_VALIDATION
    elif result:
        state = str(result.get("result_state") or "testing_level")
    elif plan_complete:
        state = STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN
    else:
        state = STATISTICAL_RESULT_STATE_NOT_RUN
    payload = dict(result) if result else {"result_state": state, "testing_level": False}
    return {
        "state": state,
        "label_zh": statistical_result_state_label_zh(state),
        "blocks_formal_report_claim": blocks_formal_report_claim(payload),
        "warnings": "；".join(warnings) if warnings else "无",
        "errors": "；".join(errors) if errors else "无",
        "report_ready": not blocks_formal_report_claim(payload),
    }


def _safe_screening_summary(project_dir: Path) -> dict[str, int]:
    try:
        from app.meta_analysis.services.title_abstract_screening_v2_service import TitleAbstractScreeningV2Service

        return {key: int(value) for key, value in TitleAbstractScreeningV2Service().screening_summary(project_dir).to_dict().items() if isinstance(value, int)}
    except Exception:
        payload = _load_json(project_dir / "screening" / "title_abstract_screening_summary_v1.json")
        return {key: int(value) for key, value in payload.items() if isinstance(value, int)}


def _safe_fulltext_summary(project_dir: Path) -> dict[str, int]:
    try:
        from app.meta_analysis.services.fulltext_management_service import FullTextManagementService

        return FullTextManagementService().summary_counts(project_dir)
    except Exception:
        return {}


def _safe_extraction_rows(project_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    effect_payload = _load_json(project_dir / "extraction" / "extraction_effect_rows.json")
    for item in effect_payload.get("effect_rows", []):
        if not isinstance(item, dict):
            continue
        structured = item.get("m5_structured_fields", {}) if isinstance(item.get("m5_structured_fields"), dict) else {}
        if not structured and str(item.get("study_unit_label", "")).strip():
            structured = {
                "first_author": str(item.get("study_unit_label", "")),
                "outcome": str(item.get("outcome_name", "")),
                "effect_measure_type": str(item.get("effect_measure", "")),
            }
        rows.append(
            {
                "study_id": str(structured.get("study_id") or item.get("study_unit_label") or ""),
                "author_year": _author_year(structured),
                "study_design": _safe_text(structured.get("study_design")),
                "population": _safe_text(structured.get("population")),
                "outcome": _safe_text(structured.get("outcome") or item.get("outcome_name")),
                "effect_measure_type": _safe_text(structured.get("effect_measure_type") or item.get("effect_measure")),
                "confirmation_status": _confirmation_status_label(str(item.get("evidence_state") or item.get("extraction_status") or "draft")),
            }
        )
    if rows:
        return rows
    legacy = _load_json(project_dir / "extraction" / "extraction_records.json")
    for item in legacy.get("records", []):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "study_id": "",
                "author_year": _safe_text(item.get("author_year") or item.get("first_author") or "未填写"),
                "study_design": _safe_text(item.get("study_design")),
                "population": _safe_text(item.get("population")),
                "outcome": _safe_text(item.get("outcome") or item.get("outcome_name")),
                "effect_measure_type": _safe_text(item.get("effect_measure_type") or item.get("effect_measure")),
                "confirmation_status": _confirmation_status_label(str(item.get("evidence_state") or item.get("status") or "draft")),
            }
        )
    return rows


def _safe_quality_summary(project_dir: Path, *, expected_study_ids: list[str]) -> dict[str, Any]:
    try:
        from app.meta_analysis.services.quality_service import QualityAssessmentService

        service = QualityAssessmentService()
        records = service.load_quality_assessment_records_v1(project_dir)
        m6 = service.quality_m6_summary(project_dir, expected_study_ids=expected_study_ids)
        tools = sorted({str(record.get("tool_name", "")) for record in records if str(record.get("tool_name", "")).strip()})
        return {
            "tools_used": "、".join(tools) if tools else "缺失",
            "studies_assessed": int(m6.get("studies_with_confirmed_quality", 0) or 0),
            "risk_distribution": f"低风险/较好 {m6.get('low_risk_or_good', 0)}；不明确 {m6.get('unclear', 0)}；高风险/较差 {m6.get('high_risk_or_poor', 0)}",
            "warning": "质量评价尚未全部确认" if int(m6.get("studies_pending_quality", 0) or 0) > 0 else "无",
            "complete": int(m6.get("studies_pending_quality", 0) or 0) == 0 and bool(records),
        }
    except Exception:
        payload = _load_json(project_dir / "quality" / "quality_assessment_records_v1.json") or _load_json(project_dir / "quality" / "quality_assessments.json")
        records = payload.get("records") or payload.get("quality_assessments") or payload.get("assessments") or []
        records = [dict(item) for item in records if isinstance(item, dict)] if isinstance(records, list) else []
        tools = sorted({str(record.get("tool_name", "")) for record in records if str(record.get("tool_name", "")).strip()})
        return {
            "tools_used": "、".join(tools) if tools else "缺失",
            "studies_assessed": len(records),
            "risk_distribution": "缺失",
            "warning": "质量评价尚未全部确认" if not records else "无",
            "complete": bool(records),
        }


def _safe_analysis_plan_summary(project_dir: Path) -> dict[str, str]:
    confirmed = _load_json(project_dir / "analysis" / "analysis_plan_confirmed_v1.json")
    draft = _load_json(project_dir / "analysis" / "analysis_plan_draft_v1.json")
    legacy = _load_json(project_dir / "analysis" / "analysis_plan.json")
    legacy_plan = dict(legacy.get("plan", {})) if isinstance(legacy.get("plan", {}), dict) else legacy
    plan = confirmed or draft or legacy_plan
    status = "已确认" if confirmed else "草稿" if draft or legacy else "缺失"
    warnings = plan.get("m7_warning_labels_zh", {}) if isinstance(plan.get("m7_warning_labels_zh"), dict) else {}
    return {
        "status_label": status,
        "effect_measure_type": _safe_text(plan.get("effect_measure_type") or plan.get("confirmed_effect_measure") or plan.get("effect_measure")),
        "model_preference": _model_label(str(plan.get("model_preference") or plan.get("confirmed_model") or plan.get("model_default") or "")),
        "heterogeneity_plan": _safe_text(plan.get("heterogeneity_metrics") or "I2 / tau2 / Q"),
        "subgroup_plan": _safe_plan(plan.get("subgroup_plan") or plan.get("confirmed_subgroup_plan")),
        "sensitivity_plan": _safe_plan(plan.get("sensitivity_plan") or plan.get("confirmed_sensitivity_plan")),
        "warnings": "；".join(str(value) for value in warnings.values()) if warnings else "无",
        "complete": bool(confirmed),
    }


def _research_question_lines(project_dir: Path) -> list[str]:
    confirmed = _load_json(project_dir / "protocol" / "pico_workspace_confirmed.json")
    draft = _load_json(project_dir / "protocol" / "pico_workspace_draft.json")
    legacy = _load_json(project_dir / "protocol" / "review_protocol.json")
    lines: list[str] = []
    if confirmed:
        lines.extend(
            [
                f"- 用户确认内容：研究对象：{_safe_text(confirmed.get('confirmed_population'))}",
                f"- 用户确认内容：干预/暴露：{_safe_text(confirmed.get('confirmed_intervention_or_exposure'))}",
                f"- 用户确认内容：对照：{_safe_text(confirmed.get('confirmed_comparator'))}",
                f"- 用户确认内容：结局：{_safe_text(confirmed.get('confirmed_outcomes'))}",
                f"- 用户确认内容：研究类型：{_safe_text(confirmed.get('confirmed_study_design'))}",
            ]
        )
    elif draft:
        lines.extend(
            [
                f"- 草稿内容：研究问题：{_safe_text(draft.get('research_question_original'))}",
                f"- 草稿内容：研究对象：{_safe_text(draft.get('population'))}",
                f"- 草稿内容：结局：{_safe_text(draft.get('outcome'))}",
            ]
        )
    elif legacy:
        title = legacy.get("project_title") or legacy.get("research_question") or legacy.get("title")
        lines.append(f"- 草稿内容：{_safe_text(title)}")
    return lines or ["- 缺失内容：尚未找到研究问题或 PICO/PICOS/PECO 确认记录。"]


def _load_literature_records(project_dir: Path) -> list[dict[str, Any]]:
    for path in (
        project_dir / "literature" / "literature_records.json",
        project_dir / "literature" / "batch_literature_records.json",
    ):
        payload = _load_json(path)
        records = payload.get("records") or payload.get("literature_records")
        if isinstance(records, list):
            return [dict(item) for item in records if isinstance(item, dict)]
    return []


def _dedup_status(project_dir: Path, prisma: PRISMAFlowSummary) -> str:
    payload = _load_json(project_dir / "deduplication" / "deduplicated_literature_v2.json") or _load_json(project_dir / "deduplication" / "deduplicated_literature.json")
    if payload:
        unresolved = payload.get("unresolved_group_ids", [])
        pending = int(payload.get("pending_duplicate_group_count", 0) or (len(unresolved) if isinstance(unresolved, list) else 0))
        return "已生成去重结果" if pending == 0 else f"存在待处理重复组 {pending}"
    return "缺失" if prisma.records_after_deduplication == 0 else "testing-level PRISMA fallback"


def _analysis_ready_count(project_dir: Path) -> int:
    payload = _load_json(project_dir / "analysis" / "analysis_ready_datasets.json")
    datasets = payload.get("datasets")
    if isinstance(datasets, list):
        total = 0
        for dataset in datasets:
            if isinstance(dataset, dict):
                included = dataset.get("included_study_count")
                total += int(included) if isinstance(included, int) else 1
        return total
    return 0


def _m8_missing_sections(
    artifacts: dict[str, str],
    screening: dict[str, int],
    fulltext: dict[str, int],
    extraction_rows: list[dict[str, str]],
    quality: dict[str, Any],
    plan: dict[str, str],
) -> list[str]:
    missing = [key for key, value in artifacts.items() if value == "missing / not generated" and key in {"literature_records", "deduplicated_literature", "screening_decisions", "analysis_plan"}]
    if not screening:
        missing.append("title_abstract_screening_summary")
    if not fulltext:
        missing.append("full_text_management")
    if not extraction_rows:
        missing.append("structured_extraction_rows")
    if not quality.get("complete"):
        missing.append("confirmed_quality_assessment")
    if not plan.get("complete"):
        missing.append("confirmed_analysis_plan")
    return _dedupe_strings(missing)


def _section_lines(lines: list[str]) -> list[str]:
    return lines if lines else ["- 缺失内容：暂无。"]


def _study_feature_lines(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return ["- 缺失内容：尚无可展示的纳入研究基本特征。"]
    return [
        f"- {row.get('author_year') or '未填写'}；设计：{row.get('study_design') or '未填写'}；人群：{row.get('population') or '未填写'}"
        for row in rows[:20]
    ]


def _extraction_summary_lines(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return ["- 缺失内容：尚无结构化数据提取表。"]
    return [
        f"- {row.get('author_year') or '未填写'}；结局：{row.get('outcome') or '未填写'}；效应量：{row.get('effect_measure_type') or '未填写'}；状态：{row.get('confirmation_status') or '未填写'}"
        for row in rows[:20]
    ]


def _author_year(fields: dict[str, Any]) -> str:
    author = _safe_text(fields.get("first_author") or fields.get("author") or fields.get("title") or "未填写")
    year = _safe_text(fields.get("year"))
    return f"{author} {year}".strip()


def _confirmation_status_label(value: str) -> str:
    labels = {
        "confirmed": "已确认",
        "completed_by_user": "用户完成",
        "user_accepted": "用户接受",
        "user_edited": "用户编辑",
        "suggested": "建议",
        "draft": "草稿",
        "rejected": "已拒绝",
    }
    return labels.get(value, value or "草稿")


def _model_label(value: str) -> str:
    labels = {
        "fixed": "固定效应",
        "fixed_effect": "固定效应",
        "fixed_effects": "固定效应",
        "random": "随机效应",
        "random_effect": "随机效应",
        "random_effects": "随机效应",
        "both": "固定效应 + 随机效应",
        "undecided": "暂不决定",
    }
    return labels.get(value.strip(), _safe_text(value))


def _safe_plan(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("user_plan", "status", "description"):
            if str(value.get(key, "")).strip():
                return _safe_text(value.get(key))
        return "；".join(f"{key}: {_safe_text(item)}" for key, item in value.items() if _safe_text(item) != "缺失") or "缺失"
    return _safe_text(value)


def _safe_text(value: Any) -> str:
    if isinstance(value, (list, tuple, set)):
        return "、".join(_safe_text(item) for item in value if _safe_text(item) != "缺失") or "缺失"
    if isinstance(value, dict):
        return "；".join(f"{key}: {_safe_text(item)}" for key, item in value.items() if _safe_text(item) != "缺失") or "缺失"
    text = str(value or "").strip()
    if not text:
        return "缺失"
    if "/" in text or "\\" in text:
        return Path(text).name if Path(text).name else "已登记"
    return text


def _format_counts(values: dict[str, int]) -> str:
    return "；".join(f"{key} {value}" for key, value in sorted(values.items())) if values else "缺失"


def _dedupe_strings(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


def _formal_report_markdown(project_dir: Path, prisma: PRISMAFlowSummary, artifacts: dict[str, str]) -> str:
    state = _m8_report_state(project_dir, prisma, artifacts)
    missing = list(state["missing_sections"])
    extraction_rows = list(state["extraction_rows"])
    quality = dict(state["quality_summary"])
    plan = dict(state["analysis_plan"])
    statistical_result = dict(state["statistical_result"])
    prisma_counts = dict(state["prisma_counts"])
    return "\n".join(
        [
            "# 报告标题",
            "",
            f"医研智析 Meta 分析报告草稿（{DRAFT_REPORT_M8_SCHEMA_VERSION}）",
            "",
            "> 当前报告为 Developer Preview / testing 阶段草稿，不是生产、临床、监管、投稿或正式可发表统计结论；not a production journal submission.",
            "",
            "## 内容状态图例",
            "- 用户确认内容：来自用户确认的研究问题、筛选、全文、提取、质量评价或分析计划。",
            "- 草稿内容：已保存但尚未确认，需用户继续编辑。",
            "- 建议内容：AI、规则或系统建议，不能当作已接受证据。",
            "- testing-level output：测试阶段辅助输出，不代表正式结果。",
            "- testing / developer preview：所有报告内容均保持测试阶段标签。",
            "- 缺失内容：当前项目尚未生成或尚未确认的部分。",
            "- 未来正式统计结果占位：只说明后续需要真实统计执行器与结果审计，不填充 pooled effect、p value、forest plot 或 funnel plot 结论。",
            "",
            "## 研究问题 / Protocol summary",
            *_section_lines(state["research_question_lines"]),
            "",
            "## 检索与导入概况",
            f"- imported_total：{prisma_counts['imported_total']}",
            f"- PubMed / 本地导入等来源统计：{state['source_summary']}",
            "- WOS / Embase / CNKI 等非 PubMed 在线检索若未由当前代码证明，保持 draft/network-dependent 或未完整实现。",
            "",
            "## 去重结果 / Study selection",
            f"- after_dedup_total：{prisma_counts['after_dedup_total']}",
            f"- duplicates_removed：{prisma.duplicates_removed}",
            f"- 去重状态：{state['dedup_status']}",
            "",
            "## PRISMA 流程摘要 / PRISMA summary",
            f"- imported_total：{prisma_counts['imported_total']}",
            f"- after_dedup_total：{prisma_counts['after_dedup_total']}",
            f"- title_abstract_included：{prisma_counts['title_abstract_included']}",
            f"- title_abstract_excluded：{prisma_counts['title_abstract_excluded']}",
            f"- full_text_needed：{prisma_counts['full_text_needed']}",
            f"- full_text_confirmed：{prisma_counts['full_text_confirmed']}",
            f"- full_text_excluded：{prisma_counts['full_text_excluded']}",
            f"- final_included_for_extraction：{prisma_counts['final_included_for_extraction']}",
            "",
            "## 标题摘要筛选结果",
            f"- 纳入：{prisma_counts['title_abstract_included']}",
            f"- 排除：{prisma_counts['title_abstract_excluded']}",
            f"- 不确定 / 需要全文：{prisma_counts['title_abstract_uncertain'] + prisma_counts['full_text_needed']}",
            "- 筛选结论只来自用户操作或用户确认；suggested 状态不写入正式纳入/排除结论。",
            "",
            "## 全文筛选结果 / Full-text registry",
            f"- 需要全文：{prisma_counts['full_text_needed']}",
            f"- 全文已确认：{prisma_counts['full_text_confirmed']}",
            f"- 全文已排除：{prisma_counts['full_text_excluded']}",
            f"- 全文不可获取：{prisma_counts['full_text_unavailable']}",
            "- PDF 或解析提示不会自动成为 confirmed evidence。",
            "",
            "## 纳入研究基本特征",
            *_study_feature_lines(extraction_rows),
            "",
            "## 数据提取表摘要",
            f"- 提取行数量：{len(extraction_rows)}",
            *_extraction_summary_lines(extraction_rows),
            "",
            "## 质量评价摘要 / Quality assessment summary",
            f"- 评价工具：{quality.get('tools_used', '缺失')}",
            f"- 已评价研究数：{quality.get('studies_assessed', 0)}",
            f"- 总体风险分布：{quality.get('risk_distribution', '缺失')}",
            f"- 质量评价提示：{quality.get('warning', '无')}",
            "",
            "## 分析计划 / Statistical methods",
            f"- 状态：{plan.get('status_label', '缺失')}",
            f"- 效应量类型：{plan.get('effect_measure_type', '缺失')}",
            f"- 模型偏好：{plan.get('model_preference', '缺失')}",
            f"- 异质性计划：{plan.get('heterogeneity_plan', '缺失')}",
            f"- 亚组分析：{plan.get('subgroup_plan', '缺失')}",
            f"- 敏感性分析：{plan.get('sensitivity_plan', '缺失')}",
            f"- 警告：{plan.get('warnings', '无')}",
            "",
            "## 统计分析状态",
            f"- 结果状态：{statistical_result.get('label_zh', '尚未运行正式统计分析')}（{statistical_result.get('state', 'not_run')}）。",
            f"- report_ready：{'是' if statistical_result.get('report_ready') else '否'}。",
            f"- formal claim blocked：{'是' if statistical_result.get('blocks_formal_report_claim', True) else '否'}。",
            f"- 校验错误：{statistical_result.get('errors', '无')}",
            f"- 校验提示：{statistical_result.get('warnings', '无')}",
            "- 当前报告为 Developer Preview / testing 阶段草稿。",
            "- not_run / configured_not_run：尚未运行正式统计分析。",
            "- failed_validation：只展示校验失败摘要，不生成正式统计结论。",
            "- testing_level：测试级结果不能作为正式 computed 结果或 formal report claim。",
            "- 统计分析结果尚未作为正式可发表结论生成。",
            "- 只有未来真实执行器返回 report_ready 后，正式报告段落才可纳入统计结论。",
            "- 本报告不生成 pooled effect、p value、forest plot、funnel plot 或医学结论。",
            "",
            "## Advanced method summary",
            "- Network meta-analysis：未来正式统计执行器审计前不生成正式结果。",
            "- Diagnostic bivariate / HSROC：当前报告只保留缺失或占位状态。",
            "",
            "## Advanced analysis add-ons summary",
            "- Subgroup、leave-one-out、publication bias 和 funnel plot 仅作为未来审计后的结果占位；本报告不填充正式图表结论。",
            "",
            "## Analysis summary",
            "- Analysis plan confirmation is summarized above; formal statistical execution is not part of M8.",
            "",
            "## Figures",
            "- 图表状态：未来正式统计结果占位；本报告不展示 forest/funnel artifact path。",
            "",
            "## Tables",
            "- 表格状态：仅展示用户可读摘要；不展示内部导出文件路径。",
            "",
            "## Applicability warnings",
            "- 任何 testing-level 输出都需要人工复核，不能被报告为正式统计证据。",
            "",
            "## Reproducibility notes",
            "- 报告从当前 Meta 项目内的结构化状态生成。",
            "- 报告正文不展示原始清单路径、本地文件路径、原始结构化负载或内部对象 ID。",
            "- Report manifest 可记录开发者级 source artifacts，但报告正文保持用户可读。",
            "",
            "## 局限性",
            "- 本报告是 Markdown 草稿；HTML/DOCX 转换仍属于 testing export。",
            "- 检索、筛选、全文、提取、质量评价和分析计划均依赖用户确认状态。",
            "- 统计分析部分是未来正式执行器占位，不支持发表级结论。",
            "- AI/rule/model 输出如存在，均只能作为建议，不能替代用户确认。",
            "",
            "## 下一步建议",
            "- 补全缺失的筛选、全文、提取、质量评价或分析计划部分。",
            "- 在 M9 对真实统计执行器输入、方法、验证基线和输出标签进行审计。",
            "- 审计通过前，不将任何统计输出用于投稿、临床或监管用途。",
            "",
            "## 开发者预览声明",
            "- BioMedPilot / 医研智析 Meta 当前为 Developer Preview / testing。",
            "- 本报告用于工作流对齐和人工复核，不是 publication-ready、clinical-ready、regulatory-ready 或 submission-ready 文档。",
            "",
            "## Missing artifact warnings",
            *[f"- {item}: missing / not generated" for item in missing],
            "",
        ]
    )
