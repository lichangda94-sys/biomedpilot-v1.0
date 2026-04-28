from __future__ import annotations

import gzip
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from geo_pipeline.download import (
    RemoteCandidate,
    check_download_path_consistency,
    discover_external_sources,
    discover_platform_candidates,
    discover_sample_level_candidates,
    discover_series_level_candidates,
    discover_series_supplementary_candidates,
    discover_series_supplementary_candidates_from_family_soft,
    download_core_geo_records,
    execute_download_plan,
    score_remote_candidates,
    select_remote_download_plan,
    should_probe_sample_level,
)


class GSM:
    def __init__(self, metadata=None, relations=None):
        self.metadata = metadata or {}
        self.relations = relations or {}


class GSE:
    def __init__(self):
        self.metadata = {
            "title": ["demo"],
            "supplementary_file": [
                "https://example.org/GSE5000_counts.tsv.gz",
                "https://example.org/GSE5000_README.pdf",
            ],
        }
        self.relations = {"SRA": ["https://www.ncbi.nlm.nih.gov/sra?term=SRP000001"]}
        self.gsms = {
            "GSM1": GSM(
                metadata={
                    "platform_id": ["GPL570"],
                    "supplementary_file_1": ["https://example.org/GSM1_counts.tsv.gz"],
                },
                relations={"SRA": ["https://www.ncbi.nlm.nih.gov/sra?term=SRX000001"]},
            ),
            "GSM2": GSM(
                metadata={
                    "platform_id": ["GPL570"],
                    "supplementary_file_1": ["NONE"],
                },
                relations={},
            ),
        }
        self.gpls = {"GPL570": object()}


class Platform:
    def __init__(self, metadata=None):
        self.metadata = metadata or {}


class GeoDownloaderTests(unittest.TestCase):
    def test_discovery_collects_multi_source_candidates(self) -> None:
        with patch("geo_pipeline.download._load_quick_gse", return_value=GSE()):
            series = discover_series_level_candidates("GSE5000")
            samples = discover_sample_level_candidates("GSE5000")
            platforms = discover_platform_candidates("GSE5000")
            external = discover_external_sources("GSE5000")

        self.assertTrue(any(item.guessed_role == "family_soft" for item in series))
        self.assertTrue(any(item.guessed_role == "expression_payload" for item in series))
        self.assertTrue(any(item.source_level == "sample" for item in samples))
        self.assertTrue(any(item.source_level == "platform" for item in platforms))
        self.assertTrue(any(item.guessed_role == "external_raw_source" for item in external))

    def test_series_supplementary_enumeration_uses_real_urls_and_probe_hints(self) -> None:
        gse = GSE()
        with (
            patch("geo_pipeline.download._load_quick_gse", return_value=gse),
            patch(
                "geo_pipeline.download._probe_remote_candidate_metadata",
                side_effect=[
                    {
                        "size_hint": 2048,
                        "content_type": "text/tab-separated-values",
                        "content_disposition": None,
                        "final_url": "https://example.org/GSE5000_counts.tsv.gz",
                    },
                    {
                        "size_hint": 512,
                        "content_type": "application/pdf",
                        "content_disposition": None,
                        "final_url": "https://example.org/GSE5000_README.pdf",
                    },
                ],
            ),
        ):
            candidates = discover_series_supplementary_candidates("GSE5000")

        by_name = {item.file_name: item for item in candidates}
        self.assertIn("GSE5000_counts.tsv.gz", by_name)
        self.assertIn("GSE5000_README.pdf", by_name)
        self.assertEqual(by_name["GSE5000_counts.tsv.gz"].guessed_role, "expression_payload")
        self.assertEqual(by_name["GSE5000_README.pdf"].guessed_role, "supporting_doc")
        self.assertEqual(by_name["GSE5000_counts.tsv.gz"].size_hint, 2048)
        self.assertEqual(by_name["GSE5000_README.pdf"].extra["content_type"], "application/pdf")
        self.assertIn("discovered from series supplementary metadata", by_name["GSE5000_counts.tsv.gz"].decision_trace)

    def test_series_supplementary_enumerates_archive_and_xlsx(self) -> None:
        gse = GSE()
        gse.metadata["supplementary_file"] = [
            "https://example.org/GSE5006_RAW.tar",
            "https://example.org/GSE5006_counts.xlsx",
            "https://example.org/GSE5006_notes.txt.gz",
        ]
        with (
            patch("geo_pipeline.download._load_quick_gse", return_value=gse),
            patch(
                "geo_pipeline.download._probe_remote_candidate_metadata",
                side_effect=[
                    {"size_hint": 100000, "content_type": "application/x-tar"},
                    {"size_hint": 50000, "content_type": "application/vnd.ms-excel"},
                    {"size_hint": 2000, "content_type": "application/gzip"},
                ],
            ),
        ):
            candidates = discover_series_supplementary_candidates("GSE5006")
        roles = {item.file_name: item.guessed_role for item in candidates}
        self.assertEqual(roles["GSE5006_RAW.tar"], "archive")
        self.assertEqual(roles["GSE5006_counts.xlsx"], "expression_payload")
        self.assertIn(roles["GSE5006_notes.txt.gz"], {"expression_payload", "unknown"})

    def test_series_supplementary_candidates_flow_into_plan(self) -> None:
        gse = GSE()
        gse.metadata["supplementary_file"] = [
            "https://example.org/GSE5007_counts.tsv",
            "https://example.org/GSE5007_README.pdf",
        ]
        with (
            patch("geo_pipeline.download._load_quick_gse", return_value=gse),
            patch(
                "geo_pipeline.download._probe_remote_candidate_metadata",
                side_effect=[
                    {"size_hint": 4096, "content_type": "text/tab-separated-values"},
                    {"size_hint": 256, "content_type": "application/pdf"},
                ],
            ),
        ):
            candidates = discover_series_supplementary_candidates("GSE5007")
        planned = select_remote_download_plan(score_remote_candidates(candidates))
        plan_by_name = {item.file_name: item.should_download for item in planned}
        self.assertTrue(plan_by_name["GSE5007_counts.tsv"])
        self.assertFalse(plan_by_name["GSE5007_README.pdf"])
        trace_by_name = {item.file_name: item.decision_trace for item in planned}
        self.assertTrue(any("download plan" in step for step in trace_by_name["GSE5007_counts.tsv"]))

    def test_series_supplementary_can_be_recovered_from_family_soft(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            family_soft = Path(tmpdir) / "GSE236866_family.soft.gz"
            with gzip.open(family_soft, "wt", encoding="utf-8") as handle:
                handle.write(
                    "^SERIES = GSE236866\n"
                    "!Series_supplementary_file = ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE236nnn/GSE236866/suppl/GSE236866_Processed_data_tau_with_inhibitors.xlsx\n"
                )
            with patch(
                "geo_pipeline.download._probe_remote_candidate_metadata",
                return_value={"size_hint": 4096, "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
            ):
                candidates = discover_series_supplementary_candidates_from_family_soft("GSE236866", str(family_soft))
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].source_level, "series_supplementary")
        self.assertEqual(candidates[0].guessed_role, "expression_payload")
        self.assertTrue(candidates[0].remote_url.startswith("https://"))

    def test_sample_level_probe_only_when_series_lacks_expression(self) -> None:
        weak_series = [
            RemoteCandidate(
                accession="GSE5001",
                source_level="series",
                source_accession="GSE5001",
                remote_url="https://example.org/GSE5001_README.pdf",
                file_name="GSE5001_README.pdf",
                file_ext=".pdf",
                guessed_role="supporting_doc",
                priority_score=0.2,
            )
        ]
        strong_series = [
            RemoteCandidate(
                accession="GSE5001",
                source_level="series",
                source_accession="GSE5001",
                remote_url="https://example.org/GSE5001_series_matrix.txt.gz",
                file_name="GSE5001_series_matrix.txt.gz",
                file_ext=".txt.gz",
                guessed_role="expression_payload",
                priority_score=0.92,
            )
        ]
        self.assertTrue(should_probe_sample_level(weak_series))
        self.assertFalse(should_probe_sample_level(strong_series))
        self.assertTrue(should_probe_sample_level(weak_series, {"payload_type": "metadata_only", "has_expression_payload": False}))
        self.assertFalse(should_probe_sample_level(weak_series, {"payload_type": "expression_matrix", "has_expression_payload": True}))

    def test_sample_level_candidates_are_enumerated_but_not_blindly_downloaded(self) -> None:
        gse = GSE()
        gse.gsms["GSM1"].metadata["supplementary_file_2"] = ["https://example.org/GSM1_README.pdf"]
        with (
            patch("geo_pipeline.download._load_quick_gse", return_value=gse),
            patch(
                "geo_pipeline.download._probe_remote_candidate_metadata",
                side_effect=[
                    {"size_hint": 4096, "content_type": "text/tab-separated-values"},
                    {"size_hint": 256, "content_type": "application/pdf"},
                ],
            ),
        ):
            candidates = discover_sample_level_candidates("GSE5000")
        planned = select_remote_download_plan(score_remote_candidates(candidates))
        plan_by_name = {item.file_name: item.should_download for item in planned}
        self.assertTrue(plan_by_name["GSM1_counts.tsv.gz"])
        self.assertFalse(plan_by_name["GSM1_README.pdf"])

    def test_platform_discovery_marks_microarray_probe_level_context(self) -> None:
        gse = GSE()
        gse.metadata["type"] = ["microarray"]
        gse.gpls = {
            "GPL570": Platform(metadata={"supplementary_file": ["https://example.org/GPL570.annot.txt.gz"]}),
        }
        with (
            patch("geo_pipeline.download._load_quick_gse", return_value=gse),
            patch(
                "geo_pipeline.download._probe_remote_candidate_metadata",
                return_value={"size_hint": 5000, "content_type": "application/gzip"},
            ),
        ):
            candidates = discover_platform_candidates("GSE5010")
        self.assertTrue(any(item.source_accession == "GPL570" for item in candidates))
        self.assertTrue(any(item.extra.get("microarray_suspected") for item in candidates))
        self.assertTrue(any("GPL annotation" in " ".join(item.reasons) for item in candidates))

    def test_external_source_discovery_uses_metadata_relations(self) -> None:
        gse = GSE()
        gse.metadata["relation"] = [
            "BioProject: https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1",
            "SRA: https://www.ncbi.nlm.nih.gov/sra?term=SRP123456",
        ]
        gse.gsms["GSM1"].metadata["relation"] = [
            "SRA: https://www.ncbi.nlm.nih.gov/sra?term=SRX123456",
        ]
        with patch("geo_pipeline.download._load_quick_gse", return_value=gse):
            candidates = discover_external_sources("GSE5011")
        urls = {item.remote_url for item in candidates}
        self.assertIn("https://www.ncbi.nlm.nih.gov/sra?term=SRP123456", urls)
        self.assertIn("https://www.ncbi.nlm.nih.gov/sra?term=SRX123456", urls)

    def test_plan_scores_and_skips_external_direct_download(self) -> None:
        candidates = [
            RemoteCandidate(
                accession="GSE5002",
                source_level="series",
                source_accession="GSE5002",
                remote_url="https://example.org/GSE5002_family.soft.gz",
                file_name="GSE5002_family.soft.gz",
                file_ext=".soft.gz",
                guessed_role="family_soft",
                required=True,
            ),
            RemoteCandidate(
                accession="GSE5002",
                source_level="external",
                source_accession="GSE5002",
                remote_url="https://www.ncbi.nlm.nih.gov/sra?term=SRP1",
                file_name="SRP1",
                file_ext="",
                guessed_role="external_raw_source",
            ),
        ]
        planned = select_remote_download_plan(score_remote_candidates(candidates))
        direct = {item.guessed_role: item.should_download for item in planned}
        self.assertTrue(direct["family_soft"])
        self.assertFalse(direct["external_raw_source"])

    def test_execute_download_plan_saves_real_files_and_records_external(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_file = root / "source" / "GSE5003_family.soft.gz"
            source_file.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(source_file, "wt", encoding="utf-8") as handle:
                handle.write("^SERIES = GSE5003\n")
            plan = [
                RemoteCandidate(
                    accession="GSE5003",
                    source_level="series",
                    source_accession="GSE5003",
                    remote_url=source_file.resolve().as_uri(),
                    file_name="GSE5003_family.soft.gz",
                    file_ext=".soft.gz",
                    guessed_role="family_soft",
                    required=True,
                    should_download=True,
                ),
                RemoteCandidate(
                    accession="GSE5003",
                    source_level="external",
                    source_accession="GSE5003",
                    remote_url="https://www.ncbi.nlm.nih.gov/sra?term=SRP2",
                    file_name="SRP2",
                    file_ext="",
                    guessed_role="external_raw_source",
                    should_download=False,
                ),
            ]
            result = execute_download_plan(plan, str(root / "dataset"))

            self.assertEqual(result["status"], "success")
            self.assertTrue(result["nonempty_saved_files"])
            self.assertTrue(result["external_sources"])
            self.assertTrue(any(item["response_status"] == "success" for item in result["download_transaction_log"]))
            self.assertTrue(result["download_success"])

    def test_download_core_geo_records_writes_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_file = root / "remote" / "GSE5004_family.soft.gz"
            source_file.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(source_file, "wt", encoding="utf-8") as handle:
                handle.write("^SERIES = GSE5004\n^SAMPLE = GSM1\n")

            series_candidates = [
                RemoteCandidate(
                    accession="GSE5004",
                    source_level="series",
                    source_accession="GSE5004",
                    remote_url=source_file.resolve().as_uri(),
                    file_name="GSE5004_family.soft.gz",
                    file_ext=".soft.gz",
                    guessed_role="family_soft",
                    required=True,
                ),
                RemoteCandidate(
                    accession="GSE5004",
                    source_level="series",
                    source_accession="GSE5004",
                    remote_url="geo://GSE5004/series_supplementary_index",
                    file_name="GSE5004_series_supplementary_index.json",
                    file_ext=".json",
                    guessed_role="supplementary_index",
                    required=True,
                ),
            ]

            with (
                patch("geo_pipeline.download.discover_series_level_candidates", return_value=series_candidates),
                patch("geo_pipeline.download.discover_series_supplementary_candidates", return_value=[]),
                patch("geo_pipeline.download.discover_sample_level_candidates", return_value=[]),
                patch("geo_pipeline.download.discover_platform_candidates", return_value=[]),
                patch("geo_pipeline.download.discover_external_sources", return_value=[]),
            ):
                result = download_core_geo_records("GSE5004", str(root / "dataset"))

            self.assertEqual(result["status"], "success")
            organized_reports = Path(root / "dataset" / "organized" / "reports")
            self.assertTrue((organized_reports / "remote_candidates.json").exists())
            self.assertTrue((organized_reports / "download_plan.json").exists())
            self.assertTrue((organized_reports / "download_receipt.json").exists())
            self.assertTrue((organized_reports / "download_transaction_log.json").exists())
            payload = json.loads((organized_reports / "download_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "module1.download_plan.v1")
            self.assertTrue(any(item["file_name"] == "GSE5004_family.soft.gz" for item in payload["plan"]))
            receipt = json.loads((organized_reports / "download_receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["schema_version"], "module1.download_receipt.v1")
            self.assertTrue(any(item["file_name"] == "GSE5004_family.soft.gz" for item in receipt["files"]))

    def test_network_request_failure_is_logged(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = [
                RemoteCandidate(
                    accession="GSE6001",
                    source_level="series",
                    source_accession="GSE6001",
                    remote_url="https://example.org/missing.soft.gz",
                    file_name="GSE6001_family.soft.gz",
                    file_ext=".soft.gz",
                    guessed_role="family_soft",
                    should_download=True,
                )
            ]
            with patch("geo_pipeline.download._download_url_to_path", side_effect=OSError("timed out")):
                result = execute_download_plan(plan, tmpdir)
            self.assertEqual(result["status"], "failed")
            self.assertTrue(result["errors"])
            self.assertIn("timeout", result["errors"][0])

    def test_file_write_failure_is_logged(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = [
                RemoteCandidate(
                    accession="GSE6002",
                    source_level="series",
                    source_accession="GSE6002",
                    remote_url="file:///tmp/fake.soft.gz",
                    file_name="GSE6002_family.soft.gz",
                    file_ext=".soft.gz",
                    guessed_role="family_soft",
                    should_download=True,
                )
            ]
            with patch("geo_pipeline.download._download_url_to_path", side_effect=PermissionError("permission denied")):
                result = execute_download_plan(plan, tmpdir)
            self.assertEqual(result["status"], "failed")
            self.assertIn("permission denied", "\n".join(result["errors"]))

    def test_wrong_destination_path_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            real_source = root / "real" / "GSE6003_family.soft.gz"
            real_source.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(real_source, "wt", encoding="utf-8") as handle:
                handle.write("^SERIES = GSE6003\n")
            plan = [
                RemoteCandidate(
                    accession="GSE6003",
                    source_level="series",
                    source_accession="GSE6003",
                    remote_url=real_source.resolve().as_uri(),
                    file_name="GSE6003_family.soft.gz",
                    file_ext=".soft.gz",
                    guessed_role="family_soft",
                    should_download=True,
                )
            ]
            wrong_path = root / "outside" / "GSE6003_family.soft.gz"
            with patch("geo_pipeline.download._resolve_destination", return_value=wrong_path):
                result = execute_download_plan(plan, str(root / "dataset"))
            self.assertFalse(result["path_consistency"]["paths_consistent"])
            self.assertIn("destination path mismatch", "\n".join(result["errors"]))

    def test_no_candidates_produces_specific_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = execute_download_plan([], tmpdir)
            self.assertEqual(result["status"], "failed")
            self.assertIn("no candidate URLs found", result["errors"])

    def test_path_consistency_reports_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            raw_target = root / "dataset" / "raw_downloads" / "geo_downloads" / "GSE6004_family.soft.gz"
            raw_target.parent.mkdir(parents=True, exist_ok=True)
            raw_target.write_text("x", encoding="utf-8")
            payload = check_download_path_consistency(
                str(root / "dataset"),
                [{"final_saved_path": str(raw_target)}],
            )
            self.assertTrue(payload["paths_consistent"])

    def test_successful_supplementary_xlsx_download_counts_as_real_download(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_file = root / "src" / "GSE6005_counts.xlsx"
            source_file.parent.mkdir(parents=True, exist_ok=True)
            source_file.write_text("fake-xlsx-content", encoding="utf-8")
            plan = [
                RemoteCandidate(
                    accession="GSE6005",
                    source_level="series",
                    source_accession="GSE6005",
                    remote_url=source_file.resolve().as_uri(),
                    file_name="GSE6005_counts.xlsx",
                    file_ext=".xlsx",
                    guessed_role="expression_payload",
                    should_download=True,
                )
            ]
            result = execute_download_plan(plan, str(root / "dataset"))
            self.assertTrue(result["download_success"])
            self.assertEqual(result["scan_range_file_count"], 1)


if __name__ == "__main__":
    unittest.main()
