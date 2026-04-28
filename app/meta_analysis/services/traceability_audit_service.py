from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.meta_analysis.services.project_contract_service import MetaProjectContractService


@dataclass(frozen=True)
class TraceabilityAuditResult:
    project_dir: str
    artifact_manifest: list[dict[str, object]]
    lineage_checks: dict[str, object]
    reproducibility_checks: dict[str, object]
    report_checks: dict[str, object]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors


class TraceabilityAuditService:
    def __init__(self, *, contract_service: MetaProjectContractService | None = None) -> None:
        self._contract_service = contract_service or MetaProjectContractService()

    def build_artifact_manifest(self, project_dir: Path) -> list[dict[str, object]]:
        project_dir = project_dir.expanduser().resolve()
        manifest: list[dict[str, object]] = []
        for path in _iter_files(project_dir):
            manifest.append(
                {
                    "relative_path": str(path.relative_to(project_dir)),
                    "artifact_type": _artifact_type_for_path(path),
                    "size_bytes": path.stat().st_size,
                    "source_reference": _source_reference_for_path(project_dir, path),
                }
            )
        return manifest

    def check_data_lineage(self, project_dir: Path) -> tuple[dict[str, object], list[str], list[str]]:
        project_dir = project_dir.expanduser().resolve()
        warnings: list[str] = []
        errors: list[str] = []
        extraction_records = _load_json(project_dir / "extraction" / "extraction_records.json").get("records", [])
        datasets = _load_json(project_dir / "analysis" / "analysis_ready_datasets.json").get("datasets", [])
        analysis_results = _load_json(project_dir / "analysis" / "analysis_results.json").get("results", [])
        figure_artifacts = _load_json(project_dir / "figures" / "figure_artifacts.json").get("artifacts", [])
        prisma = _load_json(project_dir / "reports" / "prisma_flow_summary.json")

        extraction_ids = {str(item.get("extraction_id")) for item in extraction_records if isinstance(item, dict)}
        dataset_ids = {str(item.get("dataset_id")) for item in datasets if isinstance(item, dict)}
        analysis_result_ids = {str(item.get("result_id")) for item in analysis_results if isinstance(item, dict)}
        included_literature_ids = _included_literature_ids(project_dir)

        dataset_to_extraction = True
        for dataset in [item for item in datasets if isinstance(item, dict)]:
            for extraction_id in dataset.get("included_extraction_ids", []):
                if str(extraction_id) not in extraction_ids:
                    dataset_to_extraction = False
                    warnings.append(f"analysis_ready_dataset_source_missing:{dataset.get('dataset_id')}:{extraction_id}")

        analysis_to_dataset = True
        for result in [item for item in analysis_results if isinstance(item, dict)]:
            if str(result.get("dataset_id")) not in dataset_ids:
                analysis_to_dataset = False
                warnings.append(f"analysis_result_dataset_missing:{result.get('result_id')}:{result.get('dataset_id')}")

        extraction_to_literature = True
        for record in [item for item in extraction_records if isinstance(item, dict)]:
            record_id = str(record.get("record_id", ""))
            if included_literature_ids and record_id not in included_literature_ids:
                extraction_to_literature = False
                warnings.append(f"extraction_record_literature_source_missing:{record.get('extraction_id')}:{record_id}")

        figure_to_analysis = True
        for artifact in [item for item in figure_artifacts if isinstance(item, dict)]:
            if str(artifact.get("analysis_result_id")) not in analysis_result_ids:
                figure_to_analysis = False
                warnings.append(f"figure_analysis_result_missing:{artifact.get('figure_id')}:{artifact.get('analysis_result_id')}")
            file_path = Path(str(artifact.get("file_path", "")))
            if not file_path.exists():
                figure_to_analysis = False
                warnings.append(f"figure_file_missing:{artifact.get('figure_id')}:{artifact.get('file_path')}")

        prisma_sources_available = bool(prisma) and bool(prisma.get("data_sources"))
        if not prisma_sources_available:
            warnings.append("prisma_source_references_missing")

        lineage = {
            "analysis_result_to_dataset": analysis_to_dataset,
            "analysis_ready_dataset_to_extraction_records": dataset_to_extraction,
            "extraction_records_to_included_literature": extraction_to_literature,
            "figures_to_analysis_result": figure_to_analysis,
            "prisma_to_source_artifacts": prisma_sources_available,
            "analysis_result_count": len(analysis_results) if isinstance(analysis_results, list) else 0,
            "dataset_count": len(datasets) if isinstance(datasets, list) else 0,
            "extraction_record_count": len(extraction_records) if isinstance(extraction_records, list) else 0,
        }
        return lineage, _dedupe(warnings), errors

    def check_reproducibility_package(self, project_dir: Path, package_path: Path | None = None) -> tuple[dict[str, object], list[str]]:
        project_dir = project_dir.expanduser().resolve()
        package = package_path or _latest_reproducibility_package(project_dir)
        warnings: list[str] = []
        if package is None or not package.exists():
            return {"package_path": "", "complete": False, "missing_entries": ["reproducibility_package"]}, ["reproducibility_package_missing"]
        required_entries = [
            "project.json",
            "reports/formal_meta_report.md",
            "reports/prisma_flow_summary.json",
            "extraction/extraction_records.json",
            "quality/quality_assessments.json",
            "analysis/analysis_ready_datasets.json",
            "analysis/analysis_results.json",
            "software_version.json",
        ]
        with zipfile.ZipFile(package) as archive:
            names = set(archive.namelist())
        missing = [entry for entry in required_entries if entry not in names]
        if missing:
            warnings.extend(f"reproducibility_package_entry_missing:{entry}" for entry in missing)
        return {
            "package_path": str(package),
            "complete": not missing,
            "required_entries": required_entries,
            "missing_entries": missing,
            "entry_count": len(names),
        }, warnings

    def check_report_artifacts(self, project_dir: Path) -> tuple[dict[str, object], list[str]]:
        project_dir = project_dir.expanduser().resolve()
        report_path = project_dir / "reports" / "formal_meta_report.md"
        if not report_path.exists():
            return {"formal_report_path": str(report_path), "exists": False}, ["formal_report_missing"]
        text = report_path.read_text(encoding="utf-8")
        checks = {
            "exists": True,
            "references_forest_plot": "forest_plot_" in text,
            "references_result_table": "analysis_result_table_" in text,
            "references_extraction": "extraction_records" in text,
            "references_analysis": "analysis_results" in text or "Analysis result artifact" in text,
            "declares_testing_status": "testing / developer preview" in text,
            "missing_artifact_lines": [line for line in text.splitlines() if "missing / not generated" in line],
        }
        warnings = [f"formal_report_missing_artifact:{line}" for line in checks["missing_artifact_lines"]]
        for key in ("references_forest_plot", "references_result_table", "references_extraction", "references_analysis", "declares_testing_status"):
            if not checks[key]:
                warnings.append(f"formal_report_check_failed:{key}")
        return {"formal_report_path": str(report_path), **checks}, warnings

    def run_traceability_audit(self, project_dir: Path, package_path: Path | None = None) -> TraceabilityAuditResult:
        project_dir = project_dir.expanduser().resolve()
        manifest = self.build_artifact_manifest(project_dir)
        lineage, lineage_warnings, lineage_errors = self.check_data_lineage(project_dir)
        reproducibility, reproducibility_warnings = self.check_reproducibility_package(project_dir, package_path)
        report, report_warnings = self.check_report_artifacts(project_dir)
        return TraceabilityAuditResult(
            project_dir=str(project_dir),
            artifact_manifest=manifest,
            lineage_checks=lineage,
            reproducibility_checks=reproducibility,
            report_checks=report,
            warnings=_dedupe([*lineage_warnings, *reproducibility_warnings, *report_warnings]),
            errors=lineage_errors,
        )

    def save_project_manifests(self, project_dir: Path) -> dict[str, Path]:
        return self._contract_service.write_project_manifests(project_dir)


def _iter_files(project_dir: Path) -> list[Path]:
    if not project_dir.exists():
        return []
    return [path for path in sorted(project_dir.rglob("*")) if path.is_file()]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _artifact_type_for_path(path: Path) -> str:
    name = path.name
    if name == "extraction_records.json":
        return "extraction_records"
    if name == "analysis_ready_datasets.json":
        return "analysis_ready_dataset"
    if name == "analysis_results.json":
        return "analysis_result"
    if name.startswith("forest_plot_"):
        return "forest_plot"
    if name.startswith("funnel_plot_"):
        return "funnel_plot"
    if name.startswith("analysis_result_table_"):
        return "analysis_result_table"
    if name.startswith("reproducibility_package_"):
        return "reproducibility_package"
    if name == "formal_meta_report.md":
        return "formal_meta_report"
    if name == "prisma_flow_summary.json":
        return "prisma_flow_summary"
    if name == "artifact_locks.json":
        return "artifact_locks"
    return path.parent.name


def _source_reference_for_path(project_dir: Path, path: Path) -> str:
    relative = path.relative_to(project_dir)
    if str(relative).startswith("analysis/analysis_results"):
        return "analysis/analysis_ready_datasets.json"
    if str(relative).startswith("analysis/analysis_ready_datasets"):
        return "extraction/extraction_records.json"
    if str(relative).startswith("figures/"):
        return "analysis/analysis_results.json"
    if str(relative).startswith("reports/formal_meta_report"):
        return "project artifact summary"
    if str(relative).startswith("exports/reproducibility_package"):
        return "project directory artifacts"
    return ""


def _included_literature_ids(project_dir: Path) -> set[str]:
    ids: set[str] = set()
    for path in sorted((project_dir / "screening").glob("*.json")):
        payload = _load_json(path)
        for record in payload.get("screening_records", []) if isinstance(payload.get("screening_records"), list) else []:
            if not isinstance(record, dict):
                continue
            if str(record.get("decision", "")).lower() != "included":
                continue
            for key in ("record_id", "normalized_record_id", "source_record_id", "screening_record_id"):
                value = record.get(key)
                if value:
                    ids.add(str(value))
    if ids:
        return ids
    for path in sorted((project_dir / "literature").glob("*.json")):
        payload = _load_json(path)
        for record in payload.get("records", []) if isinstance(payload.get("records"), list) else []:
            if isinstance(record, dict):
                for key in ("record_id", "normalized_record_id", "source_record_id"):
                    value = record.get(key)
                    if value:
                        ids.add(str(value))
    return ids


def _latest_reproducibility_package(project_dir: Path) -> Path | None:
    matches = sorted((project_dir / "exports").glob("reproducibility_package_*.zip"))
    return matches[-1] if matches else None


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
