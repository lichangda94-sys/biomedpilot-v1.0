from __future__ import annotations

import json
from pathlib import Path
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
            payloads.append((path, payload))
    return payloads


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
        counts[decision] = counts.get(decision, 0) + 1
    return counts


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
        "duplicate_candidate_groups": "duplicate_candidate",
        "deduplicated_literature": "deduplicated_literature",
        "screening_decisions": "screening",
        "extraction_records": "extraction_records.json",
        "analysis_ready_dataset": "analysis_ready_datasets.json",
        "analysis_result": "analysis_results.json",
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


def _formal_report_markdown(project_dir: Path, prisma: PRISMAFlowSummary, artifacts: dict[str, str]) -> str:
    missing = [key for key, value in artifacts.items() if value == "missing / not generated"]
    return "\n".join(
        [
            "# Formal Meta Analysis Report Draft",
            "",
            "## Project summary",
            f"- Project directory: {project_dir}",
            "- Current software status: Developer Preview / testing (testing / developer preview)",
            "",
            "## Research question",
            "- Missing / not generated.",
            "",
            "## Search and import summary",
            f"- Records identified: {prisma.records_identified}",
            f"- Literature records artifact: {artifacts['literature_records']}",
            "",
            "## Deduplication summary",
            f"- Records after deduplication: {prisma.records_after_deduplication}",
            f"- Duplicates removed: {prisma.duplicates_removed}",
            f"- Duplicate candidate artifact: {artifacts['duplicate_candidate_groups']}",
            f"- Deduplicated literature artifact: {artifacts['deduplicated_literature']}",
            "",
            "## Screening summary",
            f"- Records screened: {prisma.records_screened}",
            f"- Title/abstract exclusions: {prisma.records_excluded_title_abstract}",
            f"- Screening decisions artifact: {artifacts['screening_decisions']}",
            "",
            "## Full-text screening summary",
            "- Full-text workflow incomplete for production use; testing registry and exclusion export are available.",
            f"- Full-text reports sought estimate: {prisma.full_text_reports_sought}",
            f"- Full-text registry: {artifacts['fulltext_registry']}",
            f"- Full-text screening decisions: {artifacts['fulltext_screening_decisions']}",
            f"- Full-text exclusion report: {artifacts['full_text_exclusion_report']}",
            "",
            "## Included studies summary",
            f"- Studies included: {prisma.studies_included}",
            "",
            "## Extraction summary",
            f"- Extraction records artifact: {artifacts['extraction_records']}",
            "",
            "## Analysis summary",
            f"- Analysis-ready dataset artifact: {artifacts['analysis_ready_dataset']}",
            f"- Analysis result artifact: {artifacts['analysis_result']}",
            "",
            "## Advanced method summary",
            "- Testing support is available for prevalence / incidence, single-arm proportion, correlation, continuous biomarker difference, exposure-disease risk, and diagnostic basic result rows.",
            "- Diagnostic support is basic only; bivariate diagnostic models and HSROC are not implemented.",
            "- Network meta-analysis is listed as a placeholder only: Not implemented in current testing version.",
            "",
            "## Advanced analysis add-ons summary",
            f"- Subgroup analysis artifact: {artifacts['subgroup_analysis_result']}",
            f"- Leave-one-out sensitivity artifact: {artifacts['leave_one_out_result']}",
            f"- Publication bias artifact: {artifacts['publication_bias_result']}",
            f"- Funnel plot artifact: {artifacts['funnel_plot']}",
            "- Publication bias tests are marked unreliable when study count is small.",
            "",
            "## Forest plot artifact path",
            f"- {artifacts['forest_plot']}",
            "",
            "## Result table artifact path",
            f"- {artifacts['analysis_result_table']}",
            "",
            "## Quality assessment summary",
            f"- Quality assessments: {artifacts['quality_assessments']}",
            f"- Quality table path: {artifacts['quality_assessment_table']}",
            "",
            "## Reproducibility notes",
            "- Report generated from local project artifacts only.",
            "- Missing artifacts are listed explicitly.",
            "- HTML/DOCX testing exports, supplementary exports, figure packages, project snapshots, and reproducibility packages can be generated from this draft.",
            "",
            "## Known limitations",
            "- This is a Markdown report draft; HTML/DOCX outputs are testing exports, and PDF production output is not implemented.",
            "- PRISMA full-text counts are incomplete until full-text workflow is implemented.",
            "- Statistical limitations and applicability warnings must be reviewed before interpreting any testing pooled result.",
            "- Diagnostic basic outputs are not bivariate diagnostic models or HSROC.",
            "- Network meta-analysis is not implemented in this testing version.",
            "",
            "## Missing artifact warnings",
            *[f"- {item}: missing / not generated" for item in missing],
            "",
        ]
    )
