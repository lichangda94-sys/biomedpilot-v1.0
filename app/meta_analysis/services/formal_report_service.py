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
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


class PRISMAService:
    def __init__(
        self,
        *,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
    ) -> None:
        self._task_center = task_center
        self._data_center = data_center

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
        records_after_deduplication = _max_count(payloads, ("deduplicated_records", "unique_records"))
        screening_records = _screening_records(payloads)
        decision_counts = _decision_counts(screening_records)
        records_screened = len(screening_records)
        included_or_maybe = decision_counts.get("included", 0) + decision_counts.get("maybe", 0)
        studies_included = decision_counts.get("included", 0)
        if records_after_deduplication == 0:
            records_after_deduplication = records_screened or records_identified
        if studies_included == 0:
            studies_included = _max_count(payloads, ("records",), path_contains="extraction_records")
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
            data_sources=[str(path.relative_to(project_dir)) for path, _payload in payloads],
            notes=["full-text workflow incomplete; full-text PRISMA counts are testing estimates."],
            created_at=now_utc(),
        )
        self._finish_task(task, success=True, summary="PRISMA flow summary collected.")
        return summary

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
    ) -> None:
        self._prisma_service = prisma_service or PRISMAService(task_center=task_center, data_center=data_center)
        self._task_center = task_center
        self._data_center = data_center

    def build_formal_markdown_report(self, project_dir: Path) -> Path:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(project_id=project_dir.name)
        summary = self._prisma_service.load_prisma_flow_summary(project_dir)
        if summary is None:
            summary = self._prisma_service.collect_prisma_numbers(project_dir)
            self._prisma_service.save_prisma_flow_summary(project_dir, summary)
            self._prisma_service.export_prisma_flow_markdown(project_dir, summary)
        artifact_summary = _artifact_summary(project_dir)
        output_path = project_dir / "reports" / "formal_meta_report.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_formal_report_markdown(project_dir, summary, artifact_summary), encoding="utf-8")
        self._register_asset(
            project_id=project_dir.name,
            data_type="formal_meta_report",
            source_path=str(project_dir),
            output_path=str(output_path),
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


def _prisma_markdown(summary: PRISMAFlowSummary) -> str:
    return "\n".join(
        [
            "# PRISMA Flow Summary",
            "",
            f"- Records identified: {summary.records_identified}",
            f"- Records after deduplication: {summary.records_after_deduplication}",
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
        ]
    )


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
        "fulltext_registry": "fulltext_registry.json",
        "fulltext_screening_decisions": "fulltext_screening_decisions.json",
        "full_text_exclusion_report": "full_text_exclusion_report.csv",
        "quality_assessments": "quality_assessments.json",
        "quality_assessment_table": "quality_assessment_table.csv",
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
            "- Current software status: testing / developer preview",
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
            "",
            "## Missing artifact warnings",
            *[f"- {item}: missing / not generated" for item in missing],
            "",
        ]
    )
