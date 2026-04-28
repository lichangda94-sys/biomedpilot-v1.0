import tempfile
import unittest
from pathlib import Path

from literature.dedup_service import NormalizationDedupService
from literature.merge_service import DedupMergeService
from literature.models import ImportFormatHint, ParsedLiteratureRecord
from literature.store import LiteratureStore


class NormalizationDedupTests(unittest.TestCase):
    def test_doi_duplicate_identification(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            store = LiteratureStore(root_dir)
            project_id = "proj-doi"
            store.replace_parsed_records(
                "batch-doi",
                [
                    self._record(
                        "r1",
                        project_id=project_id,
                        title="  Tea and Sleep:  A Study ",
                        authors=[" Alice  A. "],
                        doi=" DOI:10.1000/ABC.001 ",
                    ),
                    self._record(
                        "r2",
                        project_id=project_id,
                        title="Tea and Sleep Duplicate",
                        doi="https://doi.org/10.1000/abc.001",
                    ),
                ],
            )

            service = NormalizationDedupService(store)
            normalized_records, groups = service.prepare_project(project_id)

        self.assertEqual(normalized_records[0].title_normalized, "tea and sleep a study")
        self.assertEqual(normalized_records[0].doi_normalized, "10.1000/abc.001")
        self.assertEqual(normalized_records[0].authors_normalized, ["alice a"])
        self.assertEqual(len(groups), 1)
        self.assertIn("doi_exact", groups[0].match_reason)
        self.assertEqual(sorted(groups[0].candidate_record_ids), ["r1", "r2"])

    def test_pmid_duplicate_identification(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            store = LiteratureStore(root_dir)
            project_id = "proj-pmid"
            store.replace_parsed_records(
                "batch-pmid",
                [
                    self._record("r3", project_id=project_id, pmid="PMID: 123456"),
                    self._record("r4", project_id=project_id, pmid="123456"),
                ],
            )

            service = NormalizationDedupService(store)
            _, groups = service.prepare_project(project_id)

        self.assertEqual(len(groups), 1)
        self.assertIn("pmid_exact", groups[0].match_reason)

    def test_title_similar_duplicate_identification(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            store = LiteratureStore(root_dir)
            project_id = "proj-title"
            store.replace_parsed_records(
                "batch-title",
                [
                    self._record(
                        "r5",
                        project_id=project_id,
                        title="Effects of tea on sleep in adults",
                        authors=["Alice A."],
                        year=2024,
                    ),
                    self._record(
                        "r6",
                        project_id=project_id,
                        title="Effect of tea on sleep in adults",
                        authors=["Bob B."],
                        year=2025,
                    ),
                ],
            )

            service = NormalizationDedupService(store)
            normalized_records, groups = service.prepare_project(project_id)

        self.assertEqual(len(normalized_records), 2)
        self.assertEqual(len(groups), 1)
        self.assertIn("title_similar_year_close", groups[0].match_reason)

    def test_non_duplicate_records_are_not_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            store = LiteratureStore(root_dir)
            project_id = "proj-clean"
            store.replace_parsed_records(
                "batch-clean",
                [
                    self._record(
                        "r7",
                        project_id=project_id,
                        title="Tea and Sleep",
                        authors=["Alice A."],
                        year=2024,
                        doi="10.1000/tea.001",
                    ),
                    self._record(
                        "r8",
                        project_id=project_id,
                        title="Coffee and Memory",
                        authors=["Carol C."],
                        year=2020,
                        doi="10.1000/coffee.009",
                    ),
                ],
            )

            service = NormalizationDedupService(store)
            _, groups = service.prepare_project(project_id)

        self.assertEqual(groups, [])

    def test_merge_fills_missing_fields_and_tracks_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            store = LiteratureStore(root_dir)
            project_id = "proj-merge"
            store.replace_parsed_records(
                "batch-merge",
                [
                    self._record(
                        "r9",
                        project_id=project_id,
                        title="Tea and Sleep",
                        authors=["Alice A."],
                        journal="Journal A",
                        doi="10.1000/merge.001",
                    ),
                    self._record(
                        "r10",
                        project_id=project_id,
                        title="Tea and Sleep",
                        abstract="Helpful abstract",
                        authors=["Alice A."],
                        language="EN",
                        doi="10.1000/merge.001",
                    ),
                ],
            )

            prep_service = NormalizationDedupService(store)
            _, groups = prep_service.prepare_project(project_id)
            merge_result = DedupMergeService(store).merge_group(groups[0].duplicate_group_id)

        self.assertEqual(merge_result.merged_record.abstract, "Helpful abstract")
        self.assertEqual(merge_result.merged_record.journal, "Journal A")
        self.assertEqual(
            merge_result.field_sources["journal"],
            "r9",
        )
        self.assertEqual(
            sorted(merge_result.merged_record.source_trace),
            ["r10", "r9"],
        )

    def _record(
        self,
        record_id: str,
        *,
        project_id: str,
        title: str = "",
        abstract: str = "",
        authors: list[str] | None = None,
        journal: str = "",
        year: int | None = None,
        doi: str = "",
        pmid: str = "",
        language: str = "",
    ) -> ParsedLiteratureRecord:
        return ParsedLiteratureRecord(
            batch_id="batch-test",
            project_id=project_id,
            source=ImportFormatHint.RIS.value,
            record_id=record_id,
            source_record_id=record_id,
            title=title,
            abstract=abstract,
            authors=list(authors or []),
            journal=journal,
            year=year,
            doi=doi,
            pmid=pmid,
            language=language,
        )
