import os
import unittest

from analysis.models import AnalysisMetric, AnalysisModelType
from reporting.models import AnalysisSummaryRow, AnalysisSummaryTable


class ReportingSummaryWidgetTests(unittest.TestCase):
    def test_displays_profile_source_from_analysis_summary(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.reporting_summary_widget import ReportingSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = ReportingSummaryWidget()
        table = AnalysisSummaryTable(
            project_id="proj-ui",
            rows=[
                AnalysisSummaryRow(
                    analysis_id="analysis-1",
                    analysis_profile_id="aprof-1",
                    analysis_profile_name="Primary OR profile",
                    metric=AnalysisMetric.OR,
                    model_type=AnalysisModelType.FIXED_EFFECT,
                    pooled_effect=0.75,
                    ci_lower=0.50,
                    ci_upper=0.95,
                    p_value=0.01,
                    tau2=0.0,
                    q_statistic=1.0,
                    i2=0.0,
                    study_count=2,
                )
            ],
        )

        widget.set_analysis_summary(table)

        self.assertEqual(widget.profile_source_text(), "Profile: Primary OR profile (aprof-1)")
        self.assertEqual(widget.summary_cell_text(0, 1), "aprof-1")
        self.assertEqual(widget.summary_cell_text(0, 2), "Primary OR profile")
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
