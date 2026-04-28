from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.meta_analysis.version import META_INTERNAL_BETA_VERSION, META_SOFTWARE_STATUS
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter


MANIFEST_FILES = (
    "project.json",
    "data_manifest.json",
    "artifact_manifest.json",
    "task_manifest.json",
    "lineage_manifest.json",
)


CANONICAL_PROJECT_PATHS: dict[str, str] = {
    "literature_records": "literature/literature_records.json",
    "screening_ready_records": "screening/screening_ready_records.json",
    "duplicate_candidate_groups": "deduplication/duplicate_candidate_groups.json",
    "deduplicated_literature": "deduplication/deduplicated_literature.json",
    "screening_decisions": "screening/screening_decisions.json",
    "fulltext_registry": "fulltext/fulltext_registry.json",
    "fulltext_screening_decisions": "fulltext/fulltext_screening_decisions.json",
    "full_text_exclusion_report": "reports/full_text_exclusion_report.csv",
    "extraction_records": "extraction/extraction_records.json",
    "extraction_drafts": "extraction/drafts/",
    "quality_assessments": "quality/quality_assessments.json",
    "quality_assessment_table": "exports/quality_assessment_table.csv",
    "analysis_ready_dataset": "analysis/analysis_ready_datasets.json",
    "analysis_result": "analysis/analysis_results.json",
    "figure_artifacts": "figures/figure_artifacts.json",
    "formal_report": "reports/formal_meta_report.md",
    "report_manifest": "reports/report_manifest.json",
    "supplementary_exports": "exports/supplementary/",
    "figure_package": "exports/figures_package.zip",
    "artifact_locks": "locks/artifact_locks.json",
    "retrieval_history": "retrieval/pubmed_retrieval_history.json",
}


@dataclass(frozen=True)
class ProjectContractValidationResult:
    project_id: str
    valid: bool
    warnings: list[str]
    errors: list[str]


class MetaProjectContractService:
    def __init__(self, *, data_center: DataCenter | None = None, task_center: TaskCenter | None = None) -> None:
        self._data_center = data_center
        self._task_center = task_center

    def ensure_project_structure(self, project_dir: Path) -> list[Path]:
        project_dir = project_dir.expanduser().resolve()
        directories = [
            project_dir / "literature",
            project_dir / "deduplication",
            project_dir / "screening",
            project_dir / "fulltext",
            project_dir / "extraction" / "drafts",
            project_dir / "quality",
            project_dir / "analysis",
            project_dir / "figures",
            project_dir / "reports",
            project_dir / "exports" / "supplementary",
            project_dir / "snapshots",
            project_dir / "locks",
            project_dir / "retrieval",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        return directories

    def write_project_manifests(self, project_dir: Path) -> dict[str, Path]:
        project_dir = project_dir.expanduser().resolve()
        self.ensure_project_structure(project_dir)
        project_manifest = self._project_manifest(project_dir)
        artifact_manifest = self._artifact_manifest(project_dir)
        lineage_manifest = self._lineage_manifest(project_dir, artifact_manifest)
        data_manifest = self._data_manifest(project_dir)
        task_manifest = self._task_manifest(project_dir)
        outputs = {
            "project": project_dir / "project.json",
            "data": project_dir / "data_manifest.json",
            "artifact": project_dir / "artifact_manifest.json",
            "task": project_dir / "task_manifest.json",
            "lineage": project_dir / "lineage_manifest.json",
        }
        _write_json(outputs["project"], project_manifest)
        _write_json(outputs["data"], data_manifest)
        _write_json(outputs["artifact"], artifact_manifest)
        _write_json(outputs["task"], task_manifest)
        _write_json(outputs["lineage"], lineage_manifest)
        return outputs

    def validate_project_contract(self, project_dir: Path) -> ProjectContractValidationResult:
        project_dir = project_dir.expanduser().resolve()
        warnings: list[str] = []
        errors: list[str] = []
        for filename in MANIFEST_FILES:
            if not (project_dir / filename).exists():
                warnings.append(f"manifest_missing:{filename}")
        for data_type, relative in CANONICAL_PROJECT_PATHS.items():
            path = project_dir / relative
            if relative.endswith("/"):
                if not path.exists():
                    warnings.append(f"canonical_directory_missing:{data_type}:{relative}")
            elif not path.exists():
                warnings.append(f"canonical_artifact_missing:{data_type}:{relative}")
        return ProjectContractValidationResult(project_id=project_dir.name, valid=not errors, warnings=warnings, errors=errors)

    def _project_manifest(self, project_dir: Path) -> dict[str, object]:
        existing = _load_json(project_dir / "project.json")
        return {
            "project_id": str(existing.get("project_id") or project_dir.name),
            "project_dir": str(project_dir),
            "module": "meta_analysis",
            "software_status": META_SOFTWARE_STATUS,
            "software_version": META_INTERNAL_BETA_VERSION,
            "schema_version": "meta_project_contract.v1",
            "canonical_paths": CANONICAL_PROJECT_PATHS,
        }

    def _data_manifest(self, project_dir: Path) -> dict[str, object]:
        assets = []
        if self._data_center is not None:
            assets = [asdict(asset) for asset in self._data_center.list_assets(project_dir.name)]
        return {
            "project_id": project_dir.name,
            "schema_version": "meta_data_manifest.v1",
            "data_assets": assets,
            "known_data_types": sorted(CANONICAL_PROJECT_PATHS),
        }

    def _task_manifest(self, project_dir: Path) -> dict[str, object]:
        tasks = []
        if self._task_center is not None:
            tasks = [asdict(task) for task in self._task_center.list_tasks(limit=None) if task.project_id == project_dir.name]
        return {"project_id": project_dir.name, "schema_version": "meta_task_manifest.v1", "tasks": tasks}

    def _artifact_manifest(self, project_dir: Path) -> dict[str, object]:
        artifacts = []
        for path in sorted(project_dir.rglob("*")) if project_dir.exists() else []:
            if not path.is_file():
                continue
            artifacts.append(
                {
                    "relative_path": str(path.relative_to(project_dir)),
                    "artifact_type": _artifact_type(path),
                    "size_bytes": path.stat().st_size,
                    "source_reference": _source_reference(path.relative_to(project_dir)),
                    "status": "available",
                }
            )
        return {
            "project_id": project_dir.name,
            "schema_version": "meta_artifact_manifest.v1",
            "artifacts": artifacts,
        }

    def _lineage_manifest(self, project_dir: Path, artifact_manifest: dict[str, object]) -> dict[str, object]:
        artifacts = artifact_manifest.get("artifacts", [])
        available = {str(item.get("relative_path")) for item in artifacts if isinstance(item, dict)}
        lineage = [
            _lineage_item("analysis_result_to_dataset", "analysis/analysis_results.json", "analysis/analysis_ready_datasets.json", available),
            _lineage_item("analysis_ready_dataset_to_extraction_records", "analysis/analysis_ready_datasets.json", "extraction/extraction_records.json", available),
            _lineage_item("extraction_records_to_literature", "extraction/extraction_records.json", "screening/screening_decisions.json", available),
            _lineage_item("figure_to_analysis_result", "figures/figure_artifacts.json", "analysis/analysis_results.json", available),
            _lineage_item("report_to_artifacts", "reports/formal_meta_report.md", "reports/report_manifest.json", available),
            _lineage_item("prisma_to_sources", "reports/prisma_flow_summary.json", "screening/screening_decisions.json", available),
        ]
        return {
            "project_id": project_dir.name,
            "schema_version": "meta_lineage_manifest.v1",
            "lineage": lineage,
            "warnings": [item["warning"] for item in lineage if item.get("warning")],
        }


def _lineage_item(name: str, artifact: str, source: str, available: set[str]) -> dict[str, object]:
    status = "available" if artifact in available and source in available else "missing_source"
    warning = "" if status == "available" else f"lineage_source_missing:{name}:{artifact}->{source}"
    return {"name": name, "artifact": artifact, "source": source, "status": status, "warning": warning}


def _artifact_type(path: Path) -> str:
    name = path.name
    if name in MANIFEST_FILES:
        return name.removesuffix(".json")
    if name == "report_manifest.json":
        return "report_manifest"
    if name.startswith("forest_plot_"):
        return "forest_plot"
    if name.startswith("funnel_plot_"):
        return "funnel_plot"
    if name.startswith("analysis_result_table_"):
        return "analysis_result_table"
    if name.startswith("reproducibility_package_"):
        return "reproducibility_package"
    if name.endswith("_records.json"):
        return name.removesuffix(".json")
    return path.parent.name


def _source_reference(relative_path: Path) -> str:
    text = str(relative_path)
    if text.startswith("analysis/analysis_results"):
        return "analysis/analysis_ready_datasets.json"
    if text.startswith("analysis/analysis_ready_datasets"):
        return "extraction/extraction_records.json"
    if text.startswith("figures/"):
        return "analysis/analysis_results.json"
    if text.startswith("reports/formal_meta_report"):
        return "reports/report_manifest.json"
    if text.startswith("exports/reproducibility_package"):
        return "project manifest set"
    return ""


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

