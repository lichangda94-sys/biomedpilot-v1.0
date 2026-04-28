import tempfile
import unittest
from pathlib import Path

from analysis.models import AnalysisMetric, AnalysisModelType
from analysis.service import AnalysisService
from analysis_profiles.models import KeywordMatchMode
from analysis_profiles.service import AnalysisProfileService
from extraction.models import ExtractionRecord, OutcomeRecord, OutcomeType
from extraction.store import ExtractionStore
from reporting.service import ReportingService


class ReportingServiceTests(unittest.TestCase):
    def test_forest_plot_data_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            analysis_id = self._seed_analysis(root_dir)
            service = ReportingService.from_root_dir(root_dir)

            data = service.generate_forest_plot_data(analysis_id)

        self.assertEqual(data.analysis_id, analysis_id)
        self.assertEqual(len(data.rows), 2)
        self.assertGreater(data.pooled_effect, 0.0)

    def test_funnel_plot_data_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            analysis_id = self._seed_analysis(root_dir)
            service = ReportingService.from_root_dir(root_dir)

            data = service.generate_funnel_plot_data(analysis_id)

        self.assertEqual(len(data.points), 2)
        self.assertEqual(data.points[0].outcome_record_id[:4], "out-")

    def test_study_characteristics_table_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            analysis_id = self._seed_analysis(root_dir)
            service = ReportingService.from_root_dir(root_dir)

            table = service.generate_study_characteristics_table(analysis_id)

        self.assertEqual(table.project_id, "proj-report")
        self.assertEqual(len(table.rows), 2)
        self.assertEqual(table.rows[0].study_title[:5], "Study")

    def test_analysis_summary_table_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            analysis_id = self._seed_analysis(root_dir)
            service = ReportingService.from_root_dir(root_dir)

            table = service.generate_analysis_summary_table(analysis_id)

        self.assertEqual(len(table.rows), 1)
        self.assertEqual(table.rows[0].analysis_id, analysis_id)
        self.assertEqual(table.rows[0].metric, AnalysisMetric.OR)

    def test_analysis_summary_includes_profile_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            analysis_id, profile_id = self._seed_profile_analysis(root_dir)
            service = ReportingService.from_root_dir(root_dir)

            table = service.generate_analysis_summary_table(analysis_id)
            summary = service.generate_chinese_summary(analysis_id)

        self.assertEqual(table.rows[0].analysis_profile_id, profile_id)
        self.assertEqual(table.rows[0].analysis_profile_name, "Reporting profile")
        self.assertEqual(summary.analysis_profile_id, profile_id)
        self.assertEqual(summary.analysis_profile_name, "Reporting profile")

    def test_csv_export_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            analysis_id = self._seed_analysis(root_dir)
            service = ReportingService.from_root_dir(root_dir)

            artifact = service.export_forest_plot_csv(analysis_id)
            self.assertTrue(artifact.path.exists())
            self.assertIn("study_label", artifact.path.read_text(encoding="utf-8"))
            self.assertIn("/output/proj-report/reporting/", str(artifact.path))

    def test_analysis_summary_csv_exports_profile_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            analysis_id, profile_id = self._seed_profile_analysis(root_dir)
            service = ReportingService.from_root_dir(root_dir)

            artifact = service.export_analysis_summary_csv(analysis_id)
            content = artifact.path.read_text(encoding="utf-8")

        self.assertIn("analysis_profile_id", content)
        self.assertIn("analysis_profile_name", content)
        self.assertIn(profile_id, content)
        self.assertIn("Reporting profile", content)

    def test_chinese_summary_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            analysis_id = self._seed_analysis(root_dir)
            service = ReportingService.from_root_dir(root_dir)

            summary = service.generate_chinese_summary(analysis_id)

        self.assertEqual(summary.analysis_id, analysis_id)
        self.assertIn("共纳入", summary.short_cn_summary)
        self.assertIn("95%CI", summary.short_cn_summary)

    def _seed_analysis(self, root_dir: Path) -> str:
        extraction_store = ExtractionStore(root_dir)
        outcomes = []
        for index, events in enumerate((12, 18), start=1):
            extraction_id = f"extr-{index}"
            extraction_store.save_extraction_record(
                ExtractionRecord(
                    extraction_record_id=extraction_id,
                    project_id="proj-report",
                    screening_record_id=f"screen-{index}",
                    normalized_record_id=f"norm-{index}",
                    study_title=f"Study {index}",
                    study_design="RCT",
                    population="Adults",
                    condition="Condition X",
                    intervention="Intervention A",
                    comparator="Comparator B",
                    sample_size_total=100 + index,
                    follow_up="12 weeks",
                    country="China",
                )
            )
            outcome_id = f"out-{index}"
            extraction_store.save_outcome_record(
                OutcomeRecord(
                    outcome_record_id=outcome_id,
                    extraction_record_id=extraction_id,
                    outcome_name="Response",
                    outcome_type=OutcomeType.BINARY,
                    group_a_n=100,
                    group_b_n=100,
                    events_a=events,
                    events_b=25,
                )
            )
            outcomes.append(outcome_id)

        analysis_service = AnalysisService.from_root_dir(root_dir)
        analysis = analysis_service.create_analysis(
            "proj-report",
            outcomes,
            outcome_type=OutcomeType.BINARY,
            metric=AnalysisMetric.OR,
            model_type=AnalysisModelType.FIXED_EFFECT,
        )
        analysis_service.run_analysis(analysis.analysis_id)
        return analysis.analysis_id

    def _seed_profile_analysis(self, root_dir: Path) -> tuple[str, str]:
        outcome_ids = self._seed_reporting_outcomes(root_dir)
        profile_service = AnalysisProfileService.from_root_dir(root_dir)
        gene_panel = profile_service.create_gene_panel(
            "proj-report",
            "Reporting panel",
            ["EGFR", "ALK"],
        )
        comparison = profile_service.create_comparison_rule(
            "proj-report",
            "Treatment versus control",
            "Treatment",
            "Control",
        )
        keyword_set = profile_service.create_keyword_rule_set(
            "proj-report",
            "Reporting keywords",
            ["metastatic", "advanced"],
            match_mode=KeywordMatchMode.ANY,
        )
        thresholds = profile_service.create_threshold_profile(
            "proj-report",
            "Reporting thresholds",
            min_study_count=2,
            max_i2=75.0,
            alpha=0.05,
        )
        profile = profile_service.create_analysis_profile(
            "proj-report",
            "Reporting profile",
            outcome_type=OutcomeType.BINARY,
            metric=AnalysisMetric.OR,
            model_type=AnalysisModelType.FIXED_EFFECT,
            comparison_rule_id=comparison.comparison_rule_id,
            threshold_profile_id=thresholds.threshold_profile_id,
            gene_panel_id=gene_panel.gene_panel_id,
            keyword_rule_set_id=keyword_set.keyword_rule_set_id,
        )
        config = profile_service.export_engine_config(profile.analysis_profile_id)
        analysis_service = AnalysisService.from_root_dir(root_dir)
        analysis = analysis_service.create_analysis_from_profile_config(config, outcome_ids)
        analysis_service.run_analysis(analysis.analysis_id)
        return analysis.analysis_id, profile.analysis_profile_id

    def _seed_reporting_outcomes(self, root_dir: Path) -> list[str]:
        extraction_store = ExtractionStore(root_dir)
        outcomes = []
        for index, events in enumerate((12, 18), start=1):
            extraction_id = f"extr-profile-{index}"
            extraction_store.save_extraction_record(
                ExtractionRecord(
                    extraction_record_id=extraction_id,
                    project_id="proj-report",
                    screening_record_id=f"screen-profile-{index}",
                    normalized_record_id=f"norm-profile-{index}",
                    study_title=f"Profile study {index}",
                )
            )
            outcome_id = f"out-profile-{index}"
            extraction_store.save_outcome_record(
                OutcomeRecord(
                    outcome_record_id=outcome_id,
                    extraction_record_id=extraction_id,
                    outcome_name="Response",
                    outcome_type=OutcomeType.BINARY,
                    group_a_n=100,
                    group_b_n=100,
                    events_a=events,
                    events_b=25,
                )
            )
            outcomes.append(outcome_id)
        return outcomes
