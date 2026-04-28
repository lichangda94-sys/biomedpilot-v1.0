from __future__ import annotations

import csv
from pathlib import Path

from analysis.models import AnalysisInput, AnalysisMetric, AnalysisModelType, MetaResult, StudyEffectResult
from analysis.store import AnalysisStore
from analysis_profiles.models import AnalysisProfile
from analysis_profiles.store import AnalysisProfileStore
from extraction.models import ExtractionRecord, OutcomeRecord
from extraction.store import ExtractionStore
from reporting.models import (
    AnalysisSummaryRow,
    AnalysisSummaryTable,
    ChineseAnalysisSummary,
    ExportArtifact,
    ForestPlotData,
    ForestPlotRow,
    FunnelPlotData,
    FunnelPlotPoint,
    StudyCharacteristicsRow,
    StudyCharacteristicsTable,
)


class ReportingService:
    def __init__(
        self,
        root_dir: Path,
        analysis_store: AnalysisStore,
        extraction_store: ExtractionStore,
        analysis_profile_store: AnalysisProfileStore | None = None,
    ) -> None:
        self._root_dir = root_dir
        self._analysis_store = analysis_store
        self._extraction_store = extraction_store
        self._analysis_profile_store = analysis_profile_store or AnalysisProfileStore(root_dir)

    @classmethod
    def from_root_dir(cls, root_dir: Path) -> "ReportingService":
        return cls(root_dir, AnalysisStore(root_dir), ExtractionStore(root_dir))

    def generate_forest_plot_data(self, analysis_id: str) -> ForestPlotData:
        analysis = self._require_analysis(analysis_id)
        meta = self._require_meta_result(analysis_id)
        study_effects = self._analysis_store.list_study_effects(analysis_id=analysis_id)
        rows = []
        for effect in study_effects:
            outcome = self._require_outcome(effect.outcome_record_id)
            extraction = self._require_extraction(outcome.extraction_record_id)
            rows.append(
                ForestPlotRow(
                    study_label=extraction.study_title or outcome.outcome_name,
                    effect_value=effect.effect_value,
                    ci_lower=effect.ci_lower,
                    ci_upper=effect.ci_upper,
                    weight=self._study_weight(effect, analysis.model_type),
                    outcome_record_id=effect.outcome_record_id,
                )
            )
        return ForestPlotData(
            analysis_id=analysis.analysis_id,
            metric=analysis.metric,
            model_type=analysis.model_type,
            rows=rows,
            pooled_effect=meta.pooled_effect,
            pooled_ci_lower=meta.ci_lower,
            pooled_ci_upper=meta.ci_upper,
            study_count=meta.study_count,
        )

    def generate_funnel_plot_data(self, analysis_id: str) -> FunnelPlotData:
        study_effects = self._analysis_store.list_study_effects(analysis_id=analysis_id)
        points = []
        for effect in study_effects:
            outcome = self._require_outcome(effect.outcome_record_id)
            extraction = self._require_extraction(outcome.extraction_record_id)
            points.append(
                FunnelPlotPoint(
                    study_label=extraction.study_title or outcome.outcome_name,
                    effect_value=effect.effect_value,
                    standard_error=effect.standard_error,
                    outcome_record_id=effect.outcome_record_id,
                )
            )
        analysis = self._require_analysis(analysis_id)
        return FunnelPlotData(
            analysis_id=analysis.analysis_id,
            metric=analysis.metric,
            points=points,
        )

    def generate_study_characteristics_table(self, analysis_id: str) -> StudyCharacteristicsTable:
        analysis = self._require_analysis(analysis_id)
        extractions = self._analysis_extractions(analysis)
        rows = [
            StudyCharacteristicsRow(
                extraction_record_id=extraction.extraction_record_id,
                study_title=extraction.study_title,
                study_design=extraction.study_design,
                population=extraction.population,
                condition=extraction.condition,
                intervention=extraction.intervention,
                comparator=extraction.comparator,
                sample_size_total=extraction.sample_size_total,
                follow_up=extraction.follow_up,
                country=extraction.country,
                notes=extraction.notes,
            )
            for extraction in extractions
        ]
        return StudyCharacteristicsTable(project_id=analysis.project_id, rows=rows)

    def generate_analysis_summary_table(self, analysis_id: str) -> AnalysisSummaryTable:
        analysis = self._require_analysis(analysis_id)
        meta = self._require_meta_result(analysis_id)
        profile = self._analysis_profile(analysis)
        return AnalysisSummaryTable(
            project_id=analysis.project_id,
            rows=[
                AnalysisSummaryRow(
                    analysis_id=analysis.analysis_id,
                    analysis_profile_id=analysis.analysis_profile_id,
                    analysis_profile_name=profile.name if profile else "",
                    metric=meta.metric,
                    model_type=meta.model_type,
                    pooled_effect=meta.pooled_effect,
                    ci_lower=meta.ci_lower,
                    ci_upper=meta.ci_upper,
                    p_value=meta.p_value,
                    tau2=meta.tau2,
                    q_statistic=meta.q_statistic,
                    i2=meta.i2,
                    study_count=meta.study_count,
                )
            ],
        )

    def generate_chinese_summary(self, analysis_id: str) -> ChineseAnalysisSummary:
        analysis = self._require_analysis(analysis_id)
        meta = self._require_meta_result(analysis_id)
        profile = self._analysis_profile(analysis)
        summary = (
            f"共纳入{meta.study_count}项研究，采用{self._model_label(meta.model_type)}"
            f"{meta.metric.value}模型分析，合并效应值为{meta.pooled_effect:.3f}"
            f"（95%CI {meta.ci_lower:.3f}–{meta.ci_upper:.3f}），"
            f"异质性I²={meta.i2:.1f}%。"
        )
        return ChineseAnalysisSummary(
            analysis_id=analysis.analysis_id,
            metric=analysis.metric,
            model_type=analysis.model_type,
            pooled_effect=meta.pooled_effect,
            ci_lower=meta.ci_lower,
            ci_upper=meta.ci_upper,
            study_count=meta.study_count,
            i2=meta.i2,
            short_cn_summary=summary,
            analysis_profile_id=analysis.analysis_profile_id,
            analysis_profile_name=profile.name if profile else "",
        )

    def export_forest_plot_csv(self, analysis_id: str) -> ExportArtifact:
        data = self.generate_forest_plot_data(analysis_id)
        analysis = self._require_analysis(analysis_id)
        file_path = self._artifact_path(analysis.project_id, f"{analysis_id}_forest_plot.csv")
        self._write_csv(file_path, [row.to_dict() for row in data.rows])
        return ExportArtifact(name="forest_plot_csv", path=file_path)

    def export_funnel_plot_csv(self, analysis_id: str) -> ExportArtifact:
        data = self.generate_funnel_plot_data(analysis_id)
        analysis = self._require_analysis(analysis_id)
        file_path = self._artifact_path(analysis.project_id, f"{analysis_id}_funnel_plot.csv")
        self._write_csv(file_path, [row.to_dict() for row in data.points])
        return ExportArtifact(name="funnel_plot_csv", path=file_path)

    def export_study_characteristics_csv(self, analysis_id: str) -> ExportArtifact:
        table = self.generate_study_characteristics_table(analysis_id)
        file_path = self._artifact_path(table.project_id, f"{analysis_id}_study_characteristics.csv")
        self._write_csv(file_path, [row.to_dict() for row in table.rows])
        return ExportArtifact(name="study_characteristics_csv", path=file_path)

    def export_analysis_summary_csv(self, analysis_id: str) -> ExportArtifact:
        table = self.generate_analysis_summary_table(analysis_id)
        file_path = self._artifact_path(table.project_id, f"{analysis_id}_analysis_summary.csv")
        self._write_csv(file_path, [row.to_dict() for row in table.rows])
        return ExportArtifact(name="analysis_summary_csv", path=file_path)

    def export_excel_placeholder(self, analysis_id: str) -> ExportArtifact:
        analysis = self._require_analysis(analysis_id)
        file_path = self._artifact_path(analysis.project_id, f"{analysis_id}_export_excel_placeholder.txt")
        file_path.write_text("Excel export is reserved for a later implementation.\n", encoding="utf-8")
        return ExportArtifact(name="excel_placeholder", path=file_path)

    def export_pdf_placeholder(self, analysis_id: str) -> ExportArtifact:
        analysis = self._require_analysis(analysis_id)
        file_path = self._artifact_path(analysis.project_id, f"{analysis_id}_export_pdf_placeholder.txt")
        file_path.write_text("PDF export is reserved for a later implementation.\n", encoding="utf-8")
        return ExportArtifact(name="pdf_placeholder", path=file_path)

    def _analysis_extractions(self, analysis: AnalysisInput) -> list[ExtractionRecord]:
        extractions: dict[str, ExtractionRecord] = {}
        for outcome_id in analysis.outcome_record_ids:
            outcome = self._require_outcome(outcome_id)
            extraction = self._require_extraction(outcome.extraction_record_id)
            extractions[extraction.extraction_record_id] = extraction
        return list(extractions.values())

    def _artifact_path(self, project_id: str, filename: str) -> Path:
        output_dir = self._root_dir / "output" / project_id / "reporting"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / filename

    def _write_csv(self, file_path: Path, rows: list[dict[str, object]]) -> None:
        if not rows:
            file_path.write_text("", encoding="utf-8")
            return
        with file_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    def _study_weight(self, effect: StudyEffectResult, model_type: AnalysisModelType) -> float:
        if model_type == AnalysisModelType.RANDOM_EFFECT and effect.weight_random is not None:
            return effect.weight_random
        return effect.weight_fixed

    def _model_label(self, model_type: AnalysisModelType) -> str:
        if model_type == AnalysisModelType.RANDOM_EFFECT:
            return "随机效应"
        return "固定效应"

    def _analysis_profile(self, analysis: AnalysisInput) -> AnalysisProfile | None:
        if analysis.analysis_profile_id is None:
            return None
        return self._analysis_profile_store.get_analysis_profile(analysis.analysis_profile_id)

    def _require_analysis(self, analysis_id: str) -> AnalysisInput:
        record = self._analysis_store.get_analysis_input(analysis_id)
        if record is None:
            raise ValueError(f"Analysis does not exist: {analysis_id}")
        return record

    def _require_meta_result(self, analysis_id: str) -> MetaResult:
        records = self._analysis_store.list_meta_results(analysis_id=analysis_id)
        if not records:
            raise ValueError(f"Meta result does not exist for analysis: {analysis_id}")
        return records[-1]

    def _require_outcome(self, outcome_record_id: str) -> OutcomeRecord:
        record = self._extraction_store.get_outcome_record(outcome_record_id)
        if record is None:
            raise ValueError(f"Outcome record does not exist: {outcome_record_id}")
        return record

    def _require_extraction(self, extraction_record_id: str) -> ExtractionRecord:
        record = self._extraction_store.get_extraction_record(extraction_record_id)
        if record is None:
            raise ValueError(f"Extraction record does not exist: {extraction_record_id}")
        return record
