from __future__ import annotations

import csv
import html
import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.models.publication import (
    ArtifactLock,
    ProjectSnapshot,
    artifact_lock_from_dict,
    artifact_lock_to_dict,
    new_lock_id,
    new_snapshot_id,
    now_utc,
    project_snapshot_from_dict,
    project_snapshot_to_dict,
)
from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder
from app.meta_analysis.services.project_contract_service import MetaProjectContractService
from app.meta_analysis.version import META_INTERNAL_BETA_VERSION, META_SOFTWARE_STATUS
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


SOFTWARE_VERSION = f"BioMedPilot {META_INTERNAL_BETA_VERSION} / {META_SOFTWARE_STATUS}"


@dataclass(frozen=True)
class PublicationExportResult:
    success: bool
    output_path: str
    data_type: str
    message: str
    warnings: list[str] = field(default_factory=list)


class PublicationExportService:
    def __init__(
        self,
        *,
        formal_report_builder: FormalMarkdownReportBuilder | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
    ) -> None:
        self._formal_report_builder = formal_report_builder or FormalMarkdownReportBuilder(
            task_center=task_center,
            data_center=data_center,
        )
        self._task_center = task_center
        self._data_center = data_center
        self._contract_service = MetaProjectContractService(data_center=data_center, task_center=task_center)

    def export_html_report(self, project_dir: Path) -> PublicationExportResult:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(
            project_id=project_dir.name,
            task_type=TaskType.HTML_REPORT_EXPORT,
            title="HTML Report Export",
            summary="Exporting formal testing report as HTML.",
        )
        markdown_path = self._ensure_formal_markdown_report(project_dir)
        output_path, warnings = self._resolve_output_path(project_dir, project_dir / "reports" / "formal_meta_report.html", "formal_report")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_markdown_to_html(markdown_path.read_text(encoding="utf-8"), project_dir.name), encoding="utf-8")
        self._register_asset(
            project_id=project_dir.name,
            data_type="formal_html_report",
            source_path=str(markdown_path),
            output_path=str(output_path),
        )
        self._finish_task(task, success=True, summary=f"HTML report exported: {output_path}")
        return PublicationExportResult(
            success=True,
            output_path=str(output_path),
            data_type="formal_html_report",
            message="HTML testing report exported.",
            warnings=warnings,
        )

    def export_word_report(self, project_dir: Path) -> PublicationExportResult:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(
            project_id=project_dir.name,
            task_type=TaskType.WORD_REPORT_EXPORT,
            title="Word Report Export",
            summary="Exporting formal testing report as DOCX.",
        )
        markdown_path = self._ensure_formal_markdown_report(project_dir)
        output_path, warnings = self._resolve_output_path(project_dir, project_dir / "reports" / "formal_meta_report.docx", "formal_report")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _write_minimal_docx(output_path, markdown_path.read_text(encoding="utf-8"))
        self._register_asset(
            project_id=project_dir.name,
            data_type="formal_word_report",
            source_path=str(markdown_path),
            output_path=str(output_path),
        )
        self._finish_task(task, success=True, summary=f"Word report exported: {output_path}")
        return PublicationExportResult(
            success=True,
            output_path=str(output_path),
            data_type="formal_word_report",
            message="Word testing report exported.",
            warnings=warnings,
        )

    def export_pdf_report_placeholder(self, project_dir: Path) -> PublicationExportResult:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(
            project_id=project_dir.name,
            task_type=TaskType.PDF_REPORT_EXPORT,
            title="PDF Report Export",
            summary="Recording PDF export limitation.",
        )
        output_path = project_dir / "reports" / "formal_meta_report_pdf_placeholder.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "PDF export is not implemented in this testing build because no lightweight PDF renderer is configured.\n",
            encoding="utf-8",
        )
        self._finish_task(task, success=False, summary="PDF report export is not implemented in this testing build.")
        return PublicationExportResult(
            success=False,
            output_path=str(output_path),
            data_type="formal_pdf_report",
            message="PDF report export is not implemented in this testing build.",
            warnings=["pdf_export_not_implemented"],
        )

    def export_supplementary_exports(self, project_dir: Path) -> PublicationExportResult:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(
            project_id=project_dir.name,
            task_type=TaskType.SUPPLEMENTARY_EXPORT,
            title="Supplementary Export",
            summary="Exporting supplementary CSV tables.",
        )
        output_dir = project_dir / "exports" / "supplementary"
        output_dir.mkdir(parents=True, exist_ok=True)
        outputs = [
            _write_json_rows_csv(
                output_dir / "literature_records.csv",
                _find_rows(project_dir, name_patterns=("literature",), keys=("records", "literature_records", "imported_records")),
                default_headers=("record_id", "title"),
            ),
            _write_json_rows_csv(
                output_dir / "deduplicated_literature.csv",
                _find_rows(project_dir, name_patterns=("deduplicated_literature", "deduplicated"), keys=("deduplicated_records", "unique_records", "records")),
                default_headers=("record_id", "title"),
            ),
            _write_json_rows_csv(
                output_dir / "screening_decisions.csv",
                _find_rows(project_dir, name_patterns=("screening",), keys=("screening_records", "decisions", "screening_decisions")),
                default_headers=("record_id", "decision", "reviewer_id"),
            ),
            _copy_or_empty_csv(
                _first_existing(project_dir, ("reports/full_text_exclusion_report.csv", "exports/full_text_exclusion_report.csv")),
                output_dir / "full_text_exclusion_report.csv",
                "record_id,decision,exclusion_reason\n",
            ),
            _write_json_rows_csv(
                output_dir / "extraction_records.csv",
                _find_rows(project_dir, name_patterns=("extraction_records",), keys=("records", "extraction_records")),
                default_headers=("extraction_id", "record_id", "study_id", "profile_type"),
            ),
            _copy_or_empty_csv(
                _first_existing(project_dir, ("exports/quality_assessment_table.csv", "quality/quality_assessment_table.csv")),
                output_dir / "quality_assessment_table.csv",
                "assessment_id,study_id,record_id,tool_name,overall_judgement\n",
            ),
            _write_json_rows_csv(
                output_dir / "analysis_ready_dataset.csv",
                _analysis_dataset_rows(project_dir),
                default_headers=("dataset_id", "study_id", "record_id", "outcome_name", "analysis_status", "exclusion_reason"),
            ),
            _copy_or_empty_csv(
                _latest_matching(project_dir / "exports", "analysis_result_table_*.csv"),
                output_dir / "analysis_result_table.csv",
                "row_type,study_id,effect,ci_lower,ci_upper,standard_error,weight,model,effect_measure\n",
            ),
        ]
        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "project_id": project_dir.name,
                    "data_type": "supplementary_exports",
                    "created_at": now_utc(),
                    "files": [path.name for path in outputs],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self._register_asset(
            project_id=project_dir.name,
            data_type="supplementary_exports",
            source_path=str(project_dir),
            output_path=str(output_dir),
        )
        self._finish_task(task, success=True, summary=f"Supplementary exports generated: {output_dir}")
        return PublicationExportResult(
            success=True,
            output_path=str(output_dir),
            data_type="supplementary_exports",
            message="Supplementary exports generated.",
        )

    def export_figure_package(self, project_dir: Path) -> PublicationExportResult:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(
            project_id=project_dir.name,
            task_type=TaskType.FIGURE_PACKAGE_EXPORT,
            title="Figure Package Export",
            summary="Packaging figures and result tables.",
        )
        output_path, warnings = self._resolve_output_path(project_dir, project_dir / "exports" / "figures_package.zip", "figure_package")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        packaged = 0
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in _iter_existing_files(project_dir / "figures"):
                archive.write(path, path.relative_to(project_dir))
                packaged += 1
            for path in sorted((project_dir / "exports").glob("analysis_result_table_*.csv")):
                archive.write(path, path.relative_to(project_dir))
                packaged += 1
            if packaged == 0:
                archive.writestr("MANIFEST.txt", "No figure artifacts or result tables were available.\n")
        self._register_asset(
            project_id=project_dir.name,
            data_type="figure_package",
            source_path=str(project_dir / "figures"),
            output_path=str(output_path),
        )
        self._finish_task(task, success=True, summary=f"Figure package exported: {output_path}")
        return PublicationExportResult(
            success=True,
            output_path=str(output_path),
            data_type="figure_package",
            message="Figure package exported.",
            warnings=warnings,
        )

    def create_project_snapshot(self, project_dir: Path) -> ProjectSnapshot:
        project_dir = project_dir.expanduser().resolve()
        self._contract_service.write_project_manifests(project_dir)
        return ProjectSnapshot(
            snapshot_id=new_snapshot_id(),
            project_id=project_dir.name,
            created_at=now_utc(),
            software_version=SOFTWARE_VERSION,
            artifact_manifest=_artifact_manifest(project_dir),
            data_manifest=_data_manifest(self._data_center, project_dir.name),
            task_manifest=_task_manifest(self._task_center, project_dir.name),
            notes=[
                "Developer Preview snapshot for review and reproducibility testing.",
                "Snapshot manifest records file metadata only; raw files remain in the project directory.",
            ],
        )

    def save_project_snapshot(self, project_dir: Path, snapshot: ProjectSnapshot) -> Path:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(
            project_id=project_dir.name,
            task_type=TaskType.PROJECT_SNAPSHOT_CREATE,
            title="Project Snapshot Create",
            summary=f"Saving project snapshot {snapshot.snapshot_id}.",
        )
        output_path = project_dir / "snapshots" / f"snapshot_{snapshot.snapshot_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(project_snapshot_to_dict(snapshot), ensure_ascii=False, indent=2), encoding="utf-8")
        self._register_asset(
            project_id=project_dir.name,
            data_type="project_snapshot",
            source_path=str(project_dir),
            output_path=str(output_path),
        )
        self._finish_task(task, success=True, summary=f"Project snapshot saved: {output_path}")
        return output_path

    def list_project_snapshots(self, project_dir: Path) -> list[ProjectSnapshot]:
        snapshot_dir = project_dir.expanduser().resolve() / "snapshots"
        snapshots: list[ProjectSnapshot] = []
        for path in sorted(snapshot_dir.glob("snapshot_*.json")):
            try:
                snapshots.append(project_snapshot_from_dict(json.loads(path.read_text(encoding="utf-8"))))
            except Exception:
                continue
        return snapshots

    def export_reproducibility_package(self, project_dir: Path) -> PublicationExportResult:
        project_dir = project_dir.expanduser().resolve()
        self._ensure_formal_markdown_report(project_dir)
        self._contract_service.write_project_manifests(project_dir)
        task = self._start_task(
            project_id=project_dir.name,
            task_type=TaskType.REPRODUCIBILITY_PACKAGE_EXPORT,
            title="Reproducibility Package Export",
            summary="Exporting project reproducibility package.",
        )
        timestamp = now_utc().replace(":", "").replace("+", "Z")
        output_path = project_dir / "exports" / f"reproducibility_package_{timestamp}.zip"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            packaged = 0
            for path in _iter_existing_files(project_dir):
                if path == output_path or path.name.startswith("reproducibility_package_"):
                    continue
                archive.write(path, path.relative_to(project_dir))
                packaged += 1
            archive.writestr(
                "software_version.json",
                json.dumps(
                    {
                        "software_version": SOFTWARE_VERSION,
                        "created_at": now_utc(),
                        "packaged_file_count": packaged,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            archive.writestr(
                "PACKAGE_MANIFEST.txt",
                "BioMedPilot Meta Analysis reproducibility package generated from local project artifacts.\n",
            )
        self._register_asset(
            project_id=project_dir.name,
            data_type="reproducibility_package",
            source_path=str(project_dir),
            output_path=str(output_path),
        )
        self._finish_task(task, success=True, summary=f"Reproducibility package exported: {output_path}")
        return PublicationExportResult(
            success=True,
            output_path=str(output_path),
            data_type="reproducibility_package",
            message="Reproducibility package exported.",
        )

    def lock_analysis_result(self, project_dir: Path, result_id: str, notes: str = "") -> ArtifactLock:
        return self._lock_artifact(project_dir, "analysis_result", result_id, notes)

    def lock_figure_artifact(self, project_dir: Path, figure_id: str, notes: str = "") -> ArtifactLock:
        return self._lock_artifact(project_dir, "figure_artifact", figure_id, notes)

    def lock_formal_report(self, project_dir: Path, report_ref: str = "formal_report", notes: str = "") -> ArtifactLock:
        return self._lock_artifact(project_dir, "formal_report", report_ref, notes)

    def list_artifact_locks(self, project_dir: Path) -> list[ArtifactLock]:
        path = self._locks_path(project_dir.expanduser().resolve())
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [artifact_lock_from_dict(item) for item in payload.get("locks", [])]

    def _lock_artifact(self, project_dir: Path, artifact_type: str, artifact_ref: str, notes: str) -> ArtifactLock:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(
            project_id=project_dir.name,
            task_type=TaskType.ARTIFACT_LOCK,
            title="Artifact Lock",
            summary=f"Locking {artifact_type}: {artifact_ref}",
        )
        lock = ArtifactLock(
            lock_id=new_lock_id(),
            project_id=project_dir.name,
            artifact_type=artifact_type,
            artifact_ref=artifact_ref,
            locked_at=now_utc(),
            notes=notes,
        )
        path = self._locks_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        locks = [existing for existing in self.list_artifact_locks(project_dir) if existing.lock_id != lock.lock_id]
        locks.append(lock)
        path.write_text(json.dumps({"locks": [artifact_lock_to_dict(item) for item in locks]}, ensure_ascii=False, indent=2), encoding="utf-8")
        self._finish_task(task, success=True, summary=f"Artifact locked: {artifact_type} / {artifact_ref}")
        return lock

    def _ensure_formal_markdown_report(self, project_dir: Path) -> Path:
        markdown_path = project_dir / "reports" / "formal_meta_report.md"
        if markdown_path.exists():
            return markdown_path
        return self._formal_report_builder.build_formal_markdown_report(project_dir)

    def _resolve_output_path(self, project_dir: Path, preferred_path: Path, artifact_type: str) -> tuple[Path, list[str]]:
        if not self._is_locked(project_dir, preferred_path, artifact_type):
            return preferred_path, []
        timestamp = now_utc().replace(":", "").replace("+", "Z")
        versioned = preferred_path.with_name(f"{preferred_path.stem}_{timestamp}{preferred_path.suffix}")
        return versioned, [f"{artifact_type}_locked_new_version_created"]

    def _is_locked(self, project_dir: Path, preferred_path: Path, artifact_type: str) -> bool:
        rel = str(preferred_path.relative_to(project_dir)) if preferred_path.is_relative_to(project_dir) else str(preferred_path)
        lock_refs = {artifact_type, preferred_path.name, rel, str(preferred_path)}
        return any(lock.artifact_type == artifact_type and lock.artifact_ref in lock_refs for lock in self.list_artifact_locks(project_dir))

    def _locks_path(self, project_dir: Path) -> Path:
        return project_dir / "locks" / "artifact_locks.json"

    def _register_asset(self, *, project_id: str, data_type: str, source_path: str, output_path: str, status: str = "available") -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(
            project_id=project_id,
            module="meta_analysis",
            data_type=data_type,
            source_path=source_path,
            output_path=output_path,
            status=status,
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


def _markdown_to_html(markdown: str, project_name: str) -> str:
    body: list[str] = []
    in_list = False
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            if in_list:
                body.append("</ul>")
                in_list = False
            continue
        if line.startswith("# "):
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append(f"<h1>{html.escape(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append(f"<h2>{html.escape(line[3:].strip())}</h2>")
        elif line.startswith("- "):
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{html.escape(line[2:].strip())}</li>")
        else:
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append(f"<p>{html.escape(line)}</p>")
    if in_list:
        body.append("</ul>")
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            f"<title>{html.escape(project_name)} Formal Meta Report</title>",
            "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.55;max-width:980px;margin:40px auto;padding:0 24px;color:#172033}h1{font-size:28px}h2{font-size:20px;margin-top:28px;border-bottom:1px solid #d8dee9;padding-bottom:6px}li{margin:4px 0}.status{background:#fff7ed;border:1px solid #fed7aa;padding:12px;border-radius:6px}</style>",
            "</head>",
            "<body>",
            '<p class="status">Current software status: testing / developer preview. This export is not a production journal submission package.</p>',
            *body,
            "</body>",
            "</html>",
            "",
        ]
    )


def _write_minimal_docx(output_path: Path, markdown: str) -> None:
    paragraphs = _markdown_to_docx_paragraphs(markdown)
    document_xml = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">',
            "<w:body>",
            *[_docx_paragraph(text, style) for text, style in paragraphs],
            '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>',
            "</w:body>",
            "</w:document>",
        ]
    )
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
        )
        archive.writestr("word/document.xml", document_xml)


def _markdown_to_docx_paragraphs(markdown: str) -> list[tuple[str, str]]:
    paragraphs: list[tuple[str, str]] = [
        ("Current software status: testing / developer preview. This DOCX is a testing export, not a production journal report.", "Normal")
    ]
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("# "):
            paragraphs.append((line[2:].strip(), "Title"))
        elif line.startswith("## "):
            paragraphs.append((line[3:].strip(), "Heading"))
        elif line.startswith("- "):
            paragraphs.append((f"- {line[2:].strip()}", "Normal"))
        else:
            paragraphs.append((line, "Normal"))
    return paragraphs


def _docx_paragraph(text: str, style: str) -> str:
    escaped = html.escape(text)
    if style == "Title":
        props = '<w:pPr><w:pStyle w:val="Title"/></w:pPr>'
    elif style == "Heading":
        props = '<w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
    else:
        props = ""
    return f"<w:p>{props}<w:r><w:t xml:space=\"preserve\">{escaped}</w:t></w:r></w:p>"


def _find_rows(project_dir: Path, *, name_patterns: tuple[str, ...], keys: tuple[str, ...]) -> list[dict[str, object]]:
    best: list[dict[str, object]] = []
    for path in sorted(project_dir.rglob("*.json")):
        if not any(pattern in path.name for pattern in name_patterns):
            continue
        payload = _load_json_dict(path)
        if not payload:
            continue
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list) and len(value) >= len(best):
                best = [dict(item) for item in value if isinstance(item, dict)]
    return best


def _analysis_dataset_rows(project_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    payload = _load_json_dict(project_dir / "analysis" / "analysis_ready_datasets.json")
    for dataset in payload.get("datasets", []) if isinstance(payload.get("datasets"), list) else []:
        if not isinstance(dataset, dict):
            continue
        dataset_id = str(dataset.get("dataset_id", ""))
        for row in dataset.get("study_rows", []) if isinstance(dataset.get("study_rows"), list) else []:
            if isinstance(row, dict):
                rows.append({"dataset_id": dataset_id, **row})
        if not dataset.get("study_rows"):
            rows.append({key: value for key, value in dataset.items() if key != "study_rows"})
    return rows


def _write_json_rows_csv(path: Path, rows: list[dict[str, object]], *, default_headers: tuple[str, ...]) -> Path:
    fieldnames = _fieldnames(rows, default_headers)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(value) for key, value in row.items()})
    return path


def _copy_or_empty_csv(source: Path | None, destination: Path, header: str) -> Path:
    if source is not None and source.exists():
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        destination.write_text(header, encoding="utf-8")
    return destination


def _first_existing(project_dir: Path, relatives: tuple[str, ...]) -> Path | None:
    for relative in relatives:
        path = project_dir / relative
        if path.exists():
            return path
    return None


def _latest_matching(directory: Path, pattern: str) -> Path | None:
    matches = sorted(directory.glob(pattern), key=lambda path: path.stat().st_mtime if path.exists() else 0)
    return matches[-1] if matches else None


def _fieldnames(rows: list[dict[str, object]], default_headers: tuple[str, ...]) -> list[str]:
    fieldnames: list[str] = list(default_headers)
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(str(key))
    return fieldnames


def _csv_value(value: object) -> object:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def _artifact_manifest(project_dir: Path) -> list[dict[str, object]]:
    manifest: list[dict[str, object]] = []
    for path in _iter_existing_files(project_dir):
        manifest.append(
            {
                "path": str(path.relative_to(project_dir)),
                "size_bytes": path.stat().st_size,
                "modified_at": path.stat().st_mtime,
            }
        )
    return manifest


def _data_manifest(data_center: DataCenter | None, project_id: str) -> list[dict[str, object]]:
    if data_center is None:
        return []
    return [
        {
            "data_id": asset.data_id,
            "data_type": asset.data_type,
            "source_path": asset.source_path,
            "output_path": asset.output_path,
            "status": asset.status,
        }
        for asset in data_center.list_assets(project_id)
    ]


def _task_manifest(task_center: TaskCenter | None, project_id: str) -> list[dict[str, object]]:
    if task_center is None:
        return []
    return [
        {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "status": task.status.value,
            "summary": task.summary,
            "finished_at": task.finished_at,
        }
        for task in task_center.list_tasks(limit=None)
        if task.project_id == project_id
    ]


def _iter_existing_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [path for path in sorted(root.rglob("*")) if path.is_file()]


def _load_json_dict(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}
