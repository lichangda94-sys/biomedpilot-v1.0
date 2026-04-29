from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.meta_analysis.version import META_SOFTWARE_STATUS


@dataclass(frozen=True)
class ReportSectionManifest:
    section_id: str
    title: str
    status: str
    source_artifacts: list[str]
    generated_outputs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ReportManifestService:
    def build_report_manifest(self, project_dir: Path) -> dict[str, object]:
        project_dir = project_dir.expanduser().resolve()
        sections = [
            self._section(project_dir, "project_summary", "Project summary", ["project.json"]),
            self._section(project_dir, "protocol", "Protocol and research question", ["protocol/review_protocol.json", "protocol/search_strategy_preview.md", "criteria/criteria_summary.md"]),
            self._section(project_dir, "search_import", "Search and import summary", ["literature/literature_records.json"]),
            self._section(project_dir, "deduplication", "Deduplication summary", ["deduplication/duplicate_candidate_groups.json", "deduplication/deduplicated_literature.json"]),
            self._section(project_dir, "screening", "Screening summary", ["screening/screening_decisions.json"]),
            self._section(
                project_dir,
                "fulltext",
                "Full-text screening summary",
                [
                    "fulltext/fulltext_registry.json",
                    "fulltext/fulltext_screening_decisions.json",
                    "fulltext/fulltext_eligibility_decisions.json",
                    "fulltext/fulltext_exclusion_report.csv",
                    "fulltext/final_included_studies.json",
                    "reports/full_text_exclusion_report.csv",
                ],
            ),
            self._section(project_dir, "extraction", "Extraction summary", ["extraction/extraction_records.json", "extraction/manual_edits_log.jsonl"]),
            self._section(
                project_dir,
                "quality",
                "Quality assessment summary",
                [
                    "quality/quality_assessments.json",
                    "quality/quality_assessment.json",
                    "exports/quality_assessment_table.csv",
                    "quality/quality_table.csv",
                    "quality/quality_summary.md",
                ],
            ),
            self._analysis_section(project_dir),
            self._section(project_dir, "applicability", "Applicability warnings", ["analysis/applicability_warnings.json"]),
            self._section(project_dir, "figures", "Figures and result tables", ["figures/figure_artifacts.json"], generated_outputs=_matching_outputs(project_dir, ("figures/forest_plot_*.png", "figures/funnel_plot_*.png", "exports/analysis_result_table_*.csv"))),
            self._prisma_section(project_dir),
            self._section(project_dir, "exports", "Publication exports", ["reports/formal_meta_report.md", "reports/formal_meta_report.html", "reports/formal_meta_report.docx", "exports/supplementary/manifest.json"]),
            ReportSectionManifest(
                section_id="pdf_strategy",
                title="PDF strategy",
                status="placeholder",
                source_artifacts=[],
                generated_outputs=["reports/formal_meta_report_pdf_placeholder.txt"] if (project_dir / "reports" / "formal_meta_report_pdf_placeholder.txt").exists() else [],
                warnings=["pdf_export_not_implemented"],
            ),
        ]
        return {
            "project_id": project_dir.name,
            "schema_version": "meta_report_manifest.v1",
            "software_status": META_SOFTWARE_STATUS,
            "sections": [section.__dict__ for section in sections],
            "warnings": [warning for section in sections for warning in section.warnings],
        }

    def save_report_manifest(self, project_dir: Path) -> Path:
        project_dir = project_dir.expanduser().resolve()
        output_path = project_dir / "reports" / "report_manifest.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.build_report_manifest(project_dir), ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def _section(
        self,
        project_dir: Path,
        section_id: str,
        title: str,
        source_artifacts: list[str],
        *,
        generated_outputs: list[str] | None = None,
    ) -> ReportSectionManifest:
        missing = [artifact for artifact in source_artifacts if not _artifact_exists(project_dir / artifact)]
        status = "available" if not missing else "missing"
        warnings = [f"report_section_source_missing:{section_id}:{artifact}" for artifact in missing]
        return ReportSectionManifest(
            section_id=section_id,
            title=title,
            status=status,
            source_artifacts=source_artifacts,
            generated_outputs=generated_outputs or [],
            warnings=warnings,
        )

    def _analysis_section(self, project_dir: Path) -> ReportSectionManifest:
        required = ["analysis/analysis_ready_datasets.json", "analysis/analysis_results.json"]
        optional = [
            "analysis/analysis_plan.json",
            "analysis/analysis_ready_dataset.json",
            "analysis/analysis_result.json",
            "analysis/applicability_warnings.json",
        ]
        missing_required = [artifact for artifact in required if not _artifact_exists(project_dir / artifact)]
        missing_optional = [artifact for artifact in optional if not _artifact_exists(project_dir / artifact)]
        warnings = [f"report_section_source_missing:analysis:{artifact}" for artifact in missing_required]
        warnings.extend(f"report_section_optional_source_missing:analysis:{artifact}" for artifact in missing_optional)
        return ReportSectionManifest(
            section_id="analysis",
            title="Analysis summary",
            status="available" if not missing_required else "missing",
            source_artifacts=[*required, *optional],
            warnings=warnings,
        )

    def _prisma_section(self, project_dir: Path) -> ReportSectionManifest:
        required = ["reports/prisma_flow_summary.json", "reports/prisma_flow_summary.md"]
        optional = ["reports/prisma_summary.json", "reports/prisma_flow.md", "reports/prisma_flow.svg"]
        missing_required = [artifact for artifact in required if not _artifact_exists(project_dir / artifact)]
        missing_optional = [artifact for artifact in optional if not _artifact_exists(project_dir / artifact)]
        warnings = [f"report_section_source_missing:prisma:{artifact}" for artifact in missing_required]
        warnings.extend(f"report_section_optional_source_missing:prisma:{artifact}" for artifact in missing_optional)
        return ReportSectionManifest(
            section_id="prisma",
            title="PRISMA summary",
            status="available" if not missing_required else "missing",
            source_artifacts=[*required, *optional],
            warnings=warnings,
        )


def _artifact_exists(path: Path) -> bool:
    if str(path).endswith("/"):
        return path.exists() and path.is_dir()
    return path.exists()


def _matching_outputs(project_dir: Path, patterns: tuple[str, ...]) -> list[str]:
    outputs: list[str] = []
    for pattern in patterns:
        outputs.extend(str(path.relative_to(project_dir)) for path in sorted(project_dir.glob(pattern)))
    return outputs
