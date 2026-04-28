import json
import tempfile
import unittest
from pathlib import Path

from literature_cli import (
    SearchConfig,
    SearchRecord,
    WorkflowSession,
    build_cache_path,
    contains_cjk,
    parse_max_results,
    parse_selection,
    save_search_results,
)


class LiteratureCliTests(unittest.TestCase):
    def test_parse_selection_multi_and_all(self):
        self.assertEqual(parse_selection("1,3-4", 5), [1, 3, 4])
        self.assertEqual(parse_selection("all", 3), [1, 2, 3])

    def test_save_search_results_json_and_csv(self):
        records = [
            SearchRecord(
                index=1,
                pmid="123",
                title="Example",
                year="2025",
                source="Journal",
                abstract="Abstract",
            )
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            save_search_results(records, Path(tmpdir), "both")
            self.assertTrue((Path(tmpdir) / "search_results.json").exists())
            self.assertTrue((Path(tmpdir) / "search_results.csv").exists())
            payload = json.loads((Path(tmpdir) / "search_results.json").read_text(encoding="utf-8"))
            self.assertEqual(payload[0]["pmid"], "123")

    def test_list_page_uses_configured_page_size(self):
        session = WorkflowSession(SearchConfig(page_size=3, max_results=9))
        session.query = "thyroid cancer"
        session.total_count = 12
        session.fetch_limit = 9
        session.results = [
            SearchRecord(
                index=i,
                pmid=str(i),
                title=f"Title {i}",
                year="2024",
                source="Journal",
                abstract="A" * 50,
            )
            for i in range(1, 8)
        ]
        page_text = session.list_page(2)
        self.assertIn("当前页: 2/3", page_text)
        self.assertIn("已抓取: 7", page_text)
        self.assertIn("是否抓完整: 否", page_text)
        self.assertIn("[4] Title 4", page_text)
        self.assertIn("[6] Title 6", page_text)
        self.assertNotIn("[7] Title 7", page_text)

    def test_parse_max_results_supports_all(self):
        self.assertIsNone(parse_max_results("all"))
        self.assertEqual(parse_max_results("1000"), 1000)

    def test_contains_cjk(self):
        self.assertTrue(contains_cjk("甲状腺癌"))
        self.assertFalse(contains_cjk("thyroid cancer"))

    def test_session_cache_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = WorkflowSession(SearchConfig(output_root=tmpdir, page_size=5))
            session.query = "thyroid cancer"
            session.total_count = 12
            session.fetch_limit = 10
            session.selected_indexes = [1, 2]
            session.results = [
                SearchRecord(
                    index=1,
                    pmid="123",
                    title="Example",
                    year="2025",
                    source="Journal",
                    abstract="Abstract",
                )
            ]
            session.save_cache()

            cache_path = build_cache_path(tmpdir, "thyroid cancer")
            self.assertTrue(cache_path.exists())

            restored = WorkflowSession(SearchConfig(output_root=tmpdir))
            restored.load_cache("thyroid cancer")
            self.assertEqual(restored.query, "thyroid cancer")
            self.assertEqual(restored.total_count, 12)
            self.assertEqual(restored.fetch_limit, 10)
            self.assertEqual(restored.selected_indexes, [1, 2])
            self.assertEqual(restored.results[0].pmid, "123")


if __name__ == "__main__":
    unittest.main()
