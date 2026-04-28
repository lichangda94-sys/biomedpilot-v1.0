import tempfile
import unittest
from pathlib import Path

from analysis.models import AnalysisMetric, AnalysisModelType
from analysis.service import AnalysisService
from extraction.models import ExtractionRecord, OutcomeRecord, OutcomeType
from extraction.store import ExtractionStore


class AnalysisServiceTests(unittest.TestCase):
    def test_or_calculation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            outcome_id = self._seed_outcome(
                root_dir,
                "binary-or",
                OutcomeType.BINARY,
                group_a_n=100,
                group_b_n=100,
                events_a=10,
                events_b=20,
            )
            service = AnalysisService.from_root_dir(root_dir)
            analysis = service.create_analysis(
                "proj-1",
                [outcome_id],
                outcome_type=OutcomeType.BINARY,
                metric=AnalysisMetric.OR,
                model_type=AnalysisModelType.FIXED_EFFECT,
            )
            study_effect = service.calculate_study_effects(analysis.analysis_id)[0]

        self.assertAlmostEqual(study_effect.effect_value, 0.4444, places=3)

    def test_rr_calculation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            outcome_id = self._seed_outcome(
                root_dir,
                "binary-rr",
                OutcomeType.BINARY,
                group_a_n=100,
                group_b_n=100,
                events_a=10,
                events_b=20,
            )
            service = AnalysisService.from_root_dir(root_dir)
            analysis = service.create_analysis(
                "proj-1",
                [outcome_id],
                outcome_type=OutcomeType.BINARY,
                metric=AnalysisMetric.RR,
                model_type=AnalysisModelType.FIXED_EFFECT,
            )
            study_effect = service.calculate_study_effects(analysis.analysis_id)[0]

        self.assertAlmostEqual(study_effect.effect_value, 0.5, places=3)

    def test_md_calculation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            outcome_id = self._seed_outcome(
                root_dir,
                "cont-md",
                OutcomeType.CONTINUOUS,
                group_a_n=50,
                group_b_n=48,
                mean_a=5.0,
                mean_b=4.0,
                sd_a=1.5,
                sd_b=1.4,
            )
            service = AnalysisService.from_root_dir(root_dir)
            analysis = service.create_analysis(
                "proj-2",
                [outcome_id],
                outcome_type=OutcomeType.CONTINUOUS,
                metric=AnalysisMetric.MD,
                model_type=AnalysisModelType.FIXED_EFFECT,
            )
            study_effect = service.calculate_study_effects(analysis.analysis_id)[0]

        self.assertAlmostEqual(study_effect.effect_value, 1.0, places=6)

    def test_smd_calculation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            outcome_id = self._seed_outcome(
                root_dir,
                "cont-smd",
                OutcomeType.CONTINUOUS,
                group_a_n=40,
                group_b_n=38,
                mean_a=3.0,
                mean_b=2.0,
                sd_a=1.2,
                sd_b=1.1,
            )
            service = AnalysisService.from_root_dir(root_dir)
            analysis = service.create_analysis(
                "proj-2",
                [outcome_id],
                outcome_type=OutcomeType.CONTINUOUS,
                metric=AnalysisMetric.SMD,
                model_type=AnalysisModelType.FIXED_EFFECT,
            )
            study_effect = service.calculate_study_effects(analysis.analysis_id)[0]

        self.assertGreater(study_effect.effect_value, 0.8)
        self.assertLess(study_effect.effect_value, 1.0)

    def test_hr_aggregation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            outcome_ids = [
                self._seed_outcome(
                    root_dir,
                    "tte-1",
                    OutcomeType.TIME_TO_EVENT,
                    hr=0.8,
                    ci_lower=0.6,
                    ci_upper=1.0,
                ),
                self._seed_outcome(
                    root_dir,
                    "tte-2",
                    OutcomeType.TIME_TO_EVENT,
                    hr=0.7,
                    ci_lower=0.5,
                    ci_upper=0.98,
                ),
            ]
            service = AnalysisService.from_root_dir(root_dir)
            analysis = service.create_analysis(
                "proj-3",
                outcome_ids,
                outcome_type=OutcomeType.TIME_TO_EVENT,
                metric=AnalysisMetric.HR,
                model_type=AnalysisModelType.FIXED_EFFECT,
            )
            meta = service.run_analysis(analysis.analysis_id)

        self.assertLess(meta.pooled_effect, 0.8)
        self.assertGreater(meta.pooled_effect, 0.6)
        self.assertEqual(meta.study_count, 2)

    def test_fixed_effect_aggregation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            outcome_ids = [
                self._seed_outcome(
                    root_dir,
                    "or-1",
                    OutcomeType.BINARY,
                    group_a_n=120,
                    group_b_n=120,
                    events_a=12,
                    events_b=20,
                ),
                self._seed_outcome(
                    root_dir,
                    "or-2",
                    OutcomeType.BINARY,
                    group_a_n=90,
                    group_b_n=90,
                    events_a=9,
                    events_b=15,
                ),
            ]
            service = AnalysisService.from_root_dir(root_dir)
            analysis = service.create_analysis(
                "proj-4",
                outcome_ids,
                outcome_type=OutcomeType.BINARY,
                metric=AnalysisMetric.OR,
                model_type=AnalysisModelType.FIXED_EFFECT,
            )
            meta = service.run_analysis(analysis.analysis_id)

        self.assertLess(meta.pooled_effect, 1.0)
        self.assertGreater(meta.ci_upper, meta.pooled_effect)

    def test_random_effect_minimal_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            outcome_ids = [
                self._seed_outcome(
                    root_dir,
                    "md-1",
                    OutcomeType.CONTINUOUS,
                    group_a_n=50,
                    group_b_n=50,
                    mean_a=6.0,
                    mean_b=4.0,
                    sd_a=1.2,
                    sd_b=1.1,
                ),
                self._seed_outcome(
                    root_dir,
                    "md-2",
                    OutcomeType.CONTINUOUS,
                    group_a_n=40,
                    group_b_n=40,
                    mean_a=3.0,
                    mean_b=4.5,
                    sd_a=1.0,
                    sd_b=1.1,
                ),
            ]
            service = AnalysisService.from_root_dir(root_dir)
            analysis = service.create_analysis(
                "proj-5",
                outcome_ids,
                outcome_type=OutcomeType.CONTINUOUS,
                metric=AnalysisMetric.MD,
                model_type=AnalysisModelType.RANDOM_EFFECT,
            )
            meta = service.run_analysis(analysis.analysis_id)
            study_effects = service.list_study_effects(analysis.analysis_id)

        self.assertGreaterEqual(meta.tau2, 0.0)
        self.assertTrue(any(effect.weight_random is not None for effect in study_effects))

    def test_i2_and_q_statistics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            outcome_ids = [
                self._seed_outcome(
                    root_dir,
                    "hr-1",
                    OutcomeType.TIME_TO_EVENT,
                    hr=0.65,
                    ci_lower=0.45,
                    ci_upper=0.95,
                ),
                self._seed_outcome(
                    root_dir,
                    "hr-2",
                    OutcomeType.TIME_TO_EVENT,
                    hr=1.10,
                    ci_lower=0.80,
                    ci_upper=1.50,
                ),
            ]
            service = AnalysisService.from_root_dir(root_dir)
            analysis = service.create_analysis(
                "proj-6",
                outcome_ids,
                outcome_type=OutcomeType.TIME_TO_EVENT,
                metric=AnalysisMetric.HR,
                model_type=AnalysisModelType.RANDOM_EFFECT,
            )
            meta = service.run_analysis(analysis.analysis_id)

        self.assertGreaterEqual(meta.q_statistic, 0.0)
        self.assertGreaterEqual(meta.i2, 0.0)

    def test_invalid_input_raises_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            outcome_id = self._seed_outcome(
                root_dir,
                "bad-binary",
                OutcomeType.BINARY,
                group_a_n=100,
                group_b_n=100,
                events_a=None,
                events_b=20,
            )
            service = AnalysisService.from_root_dir(root_dir)
            analysis = service.create_analysis(
                "proj-7",
                [outcome_id],
                outcome_type=OutcomeType.BINARY,
                metric=AnalysisMetric.OR,
                model_type=AnalysisModelType.FIXED_EFFECT,
            )

            with self.assertRaisesRegex(
                ValueError,
                "requires 2x2 data for binary analysis",
            ):
                service.calculate_study_effects(analysis.analysis_id)

    def _seed_outcome(
        self,
        root_dir: Path,
        suffix: str,
        outcome_type: OutcomeType,
        **fields: object,
    ) -> str:
        store = ExtractionStore(root_dir)
        extraction_id = f"extr-{suffix}"
        store.save_extraction_record(
            ExtractionRecord(
                extraction_record_id=extraction_id,
                project_id="proj-seed",
                screening_record_id=f"screen-{suffix}",
                normalized_record_id=f"norm-{suffix}",
                study_title=f"Study {suffix}",
            )
        )
        outcome_id = f"out-{suffix}"
        store.save_outcome_record(
            OutcomeRecord(
                outcome_record_id=outcome_id,
                extraction_record_id=extraction_id,
                outcome_name=f"Outcome {suffix}",
                outcome_type=outcome_type,
                **fields,
            )
        )
        return outcome_id
