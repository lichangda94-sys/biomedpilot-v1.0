import tempfile
import unittest
from pathlib import Path

from analysis.models import AnalysisMetric, AnalysisModelType
from analysis.profile_adapter import build_profile_analysis_input
from analysis.service import AnalysisService
from analysis.store import AnalysisStore
from analysis_profiles.models import KeywordMatchMode
from analysis_profiles.service import AnalysisProfileService
from extraction.models import ExtractionRecord, OutcomeRecord, OutcomeType
from extraction.store import ExtractionStore


class AnalysisProfileConsumptionTests(unittest.TestCase):
    def test_create_analysis_from_profile_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            outcome_ids = [
                self._seed_outcome(
                    root_dir,
                    "profile-or-1",
                    OutcomeType.BINARY,
                    group_a_n=100,
                    group_b_n=100,
                    events_a=12,
                    events_b=25,
                ),
                self._seed_outcome(
                    root_dir,
                    "profile-or-2",
                    OutcomeType.BINARY,
                    group_a_n=120,
                    group_b_n=120,
                    events_a=18,
                    events_b=30,
                ),
            ]
            profile_service = AnalysisProfileService.from_root_dir(root_dir)
            profile = self._seed_profile(profile_service)
            profile_service.mark_ready(profile.analysis_profile_id)
            config = profile_service.export_engine_config(profile.analysis_profile_id)

            analysis_service = AnalysisService.from_root_dir(root_dir)
            analysis = analysis_service.create_analysis_from_profile_config(config, outcome_ids)
            meta = analysis_service.run_analysis(analysis.analysis_id)
            reloaded = AnalysisStore(root_dir).get_analysis_input(analysis.analysis_id)

        self.assertEqual(analysis.analysis_profile_id, profile.analysis_profile_id)
        self.assertEqual(analysis.project_id, "proj-profile")
        self.assertEqual(analysis.metric, AnalysisMetric.OR)
        self.assertEqual(analysis.model_type, AnalysisModelType.RANDOM_EFFECT)
        self.assertLess(meta.pooled_effect, 1.0)
        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded.analysis_profile_id, profile.analysis_profile_id)

    def test_profile_adapter_maps_engine_config_without_running_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            profile_service = AnalysisProfileService.from_root_dir(root_dir)
            profile = self._seed_profile(profile_service)
            config = profile_service.export_engine_config(profile.analysis_profile_id)

            adapted = build_profile_analysis_input(config, ["outcome-a", "outcome-b"])

        self.assertEqual(adapted.analysis_profile_id, profile.analysis_profile_id)
        self.assertEqual(adapted.project_id, "proj-profile")
        self.assertEqual(adapted.outcome_record_ids, ["outcome-a", "outcome-b"])
        self.assertEqual(adapted.outcome_type, OutcomeType.BINARY)
        self.assertEqual(adapted.metric, AnalysisMetric.OR)
        self.assertEqual(adapted.model_type, AnalysisModelType.RANDOM_EFFECT)

    def test_profile_consumption_keeps_existing_outcome_type_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            outcome_id = self._seed_outcome(
                root_dir,
                "profile-md-mismatch",
                OutcomeType.CONTINUOUS,
                group_a_n=40,
                group_b_n=40,
                mean_a=5.0,
                mean_b=4.0,
                sd_a=1.2,
                sd_b=1.1,
            )
            profile_service = AnalysisProfileService.from_root_dir(root_dir)
            profile = self._seed_profile(profile_service)
            config = profile_service.export_engine_config(profile.analysis_profile_id)

            analysis_service = AnalysisService.from_root_dir(root_dir)
            with self.assertRaisesRegex(ValueError, "type mismatch"):
                analysis_service.create_analysis_from_profile_config(config, [outcome_id])

    def _seed_profile(self, service: AnalysisProfileService):
        gene_panel = service.create_gene_panel(
            "proj-profile",
            "Profile panel",
            ["EGFR", "ALK"],
        )
        comparison = service.create_comparison_rule(
            "proj-profile",
            "Treatment versus control",
            "Treatment",
            "Control",
        )
        keyword_set = service.create_keyword_rule_set(
            "proj-profile",
            "Profile keywords",
            ["metastatic", "advanced"],
            match_mode=KeywordMatchMode.ANY,
        )
        thresholds = service.create_threshold_profile(
            "proj-profile",
            "Profile thresholds",
            min_study_count=2,
            max_i2=75.0,
            alpha=0.05,
        )
        return service.create_analysis_profile(
            "proj-profile",
            "Profile OR random",
            outcome_type=OutcomeType.BINARY,
            metric=AnalysisMetric.OR,
            model_type=AnalysisModelType.RANDOM_EFFECT,
            comparison_rule_id=comparison.comparison_rule_id,
            threshold_profile_id=thresholds.threshold_profile_id,
            gene_panel_id=gene_panel.gene_panel_id,
            keyword_rule_set_id=keyword_set.keyword_rule_set_id,
        )

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
                project_id="proj-profile",
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


if __name__ == "__main__":
    unittest.main()
