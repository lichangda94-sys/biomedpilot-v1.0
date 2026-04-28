from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tcga_gtex import build_tcga_gtex_bundle, download_tcga_gtex_dataset, get_tcga_gtex_summary
from tcga_gtex.mainline_bridge import (
    build_mainline_summary,
    build_runtime_message,
    build_runtime_action_state,
    first_runtime_candidate,
    locator_kind,
    locator_summary,
    records_by_study,
    run_minimal_runtime,
)
from tcga_gtex.models import FileRecord


class Module4MainlineBridgeTests(unittest.TestCase):
    def test_summary_marks_missing_locator_and_groups_runtime_candidates(self) -> None:
        search_result = {
            "status": "success",
            "message": "Resolved 1 study record.",
            "data": {
                "results": [{"source": "tcga_gdc", "study_id": "TCGA-BRCA"}],
                "results_by_source": {"tcga_gdc": [{"study_id": "TCGA-BRCA"}], "gtex": []},
            },
        }
        resolve_result = {
            "status": "success",
            "message": "Resolved 1 file candidate.",
            "data": {
                "results": [
                    FileRecord(
                        source="tcga_gdc",
                        study_id="TCGA-BRCA",
                        file_id="TCGA-BRCA:expression",
                        file_name="tcga_brca_expression.tsv.gz",
                        guessed_role="expression",
                    ).to_dict()
                ]
            },
        }

        text = build_mainline_summary(search_result, resolve_result)
        grouped = records_by_study(resolve_result["data"]["results"])

        self.assertIn("TCGA/GTEx 查询分流结果（可选路径，不进入 GEO workflow）", text)
        self.assertIn("locator readiness: local_path=0, download_url=0, missing_locator=1", text)
        self.assertIn("locator=missing_locator (cannot download until a local_path/download_url is available)", text)
        self.assertEqual(list(grouped), ["TCGA-BRCA"])
        self.assertEqual(first_runtime_candidate(grouped)[0], "TCGA-BRCA")
        self.assertEqual(locator_kind(resolve_result["data"]["results"][0]), "missing_locator")

    def test_runtime_action_state_explains_ready_and_missing_locator_records(self) -> None:
        records = [
            FileRecord(
                source="tcga_gdc",
                study_id="TCGA-BRCA",
                file_id="TCGA-BRCA:expression",
                file_name="tcga_brca_expression.tsv.gz",
                guessed_role="expression",
                local_path="/tmp/tcga_brca_expression.tsv.gz",
            ).to_dict(),
            FileRecord(
                source="tcga_gdc",
                study_id="TCGA-BRCA",
                file_id="TCGA-BRCA:clinical",
                file_name="tcga_brca_clinical.json",
                guessed_role="clinical",
            ).to_dict(),
        ]
        grouped = records_by_study(records)

        state = build_runtime_action_state(grouped)
        summary = locator_summary(records)

        self.assertTrue(state["enabled"])
        self.assertEqual(state["study_id"], "TCGA-BRCA")
        self.assertEqual(state["runnable_count"], 1)
        self.assertEqual(state["missing_locator_count"], 1)
        self.assertIn("运行 TCGA-BRCA 最小 runtime", state["button_text"])
        self.assertIn("1 个候选带 locator", state["help_text"])
        self.assertEqual(summary["counts_by_locator"]["local_path"], 1)
        self.assertEqual(summary["counts_by_locator"]["missing_locator"], 1)

    def test_runtime_action_state_warns_when_every_candidate_lacks_locator(self) -> None:
        grouped = records_by_study(
            [
                FileRecord(
                    source="tcga_gdc",
                    study_id="TCGA-BRCA",
                    file_id="TCGA-BRCA:expression",
                    file_name="tcga_brca_expression.tsv.gz",
                    guessed_role="expression",
                ).to_dict()
            ]
        )

        state = build_runtime_action_state(grouped)

        self.assertTrue(state["enabled"])
        self.assertIn("缺 locator", state["button_text"])
        self.assertIn("运行会明确 failed", state["help_text"])

    def test_minimal_runtime_fails_clearly_without_locator(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_minimal_runtime(
                "TCGA-BRCA",
                tmpdir,
                [
                    FileRecord(
                        source="tcga_gdc",
                        study_id="TCGA-BRCA",
                        file_id="TCGA-BRCA:expression",
                        file_name="tcga_brca_expression.tsv.gz",
                        guessed_role="expression",
                    ).to_dict()
                ],
                download_fn=download_tcga_gtex_dataset,
                build_fn=build_tcga_gtex_bundle,
                summary_fn=get_tcga_gtex_summary,
            )

        message = build_runtime_message(result)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["stage"], "download")
        self.assertIn("missing_locator", message)
        self.assertIn("Missing downloadable locator", message)
        self.assertIn("what to check", message)

    def test_minimal_runtime_downloads_local_fixture_and_reads_bundle_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = Path(tmpdir) / "fixtures"
            fixture_dir.mkdir()
            fixture_path = fixture_dir / "tcga_brca_expression.tsv.gz"
            fixture_path.write_text("gene\tsample\nTP53\t8\n", encoding="utf-8")
            out_dir = Path(tmpdir) / "runtime"

            result = run_minimal_runtime(
                "TCGA-BRCA",
                out_dir,
                [
                    FileRecord(
                        source="tcga_gdc",
                        study_id="TCGA-BRCA",
                        file_id="TCGA-BRCA:expression",
                        file_name="tcga_brca_expression.tsv.gz",
                        guessed_role="expression",
                        local_path=str(fixture_path),
                    ).to_dict()
                ],
                download_fn=download_tcga_gtex_dataset,
                build_fn=build_tcga_gtex_bundle,
                summary_fn=get_tcga_gtex_summary,
            )

            downloaded_record = result["download_result"]["data"]["records"][0]
            downloaded_path = out_dir / downloaded_record["relative_path"]
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["stage"], "summary")
            self.assertTrue(downloaded_path.exists())
            self.assertEqual(result["summary_result"]["status"], "success")
            self.assertEqual(result["summary_result"]["data"]["summary"]["study_ids"], ["TCGA-BRCA"])


if __name__ == "__main__":
    unittest.main()
