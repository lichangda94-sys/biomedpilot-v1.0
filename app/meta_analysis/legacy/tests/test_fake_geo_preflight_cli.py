import io
import json
import unittest
from contextlib import redirect_stdout

from scripts.run_fake_geo_preflight import (
    build_fake_geo_preflight_payload,
    build_fake_geo_preflight_summary,
    build_fake_geo_preflight_text,
    main,
)


class FakeGeoPreflightCliTests(unittest.TestCase):
    def test_help_runs(self) -> None:
        with self.assertRaises(SystemExit) as context:
            main(["--help"])

        self.assertEqual(context.exception.code, 0)

    def test_default_run_prints_stable_summary(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main([])

        output = buffer.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("Fake GEO preflight:", output)
        self.assertIn("- total checks: 2", output)
        self.assertIn("- runnable checks: 1", output)
        self.assertIn("- blocked checks: 1", output)

    def test_json_output_contains_readiness_fields(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["summary"]["total_checks"], 2)
        self.assertEqual(payload["summary"]["runnable_checks"], 1)
        self.assertEqual(payload["summary"]["blocked_checks"], 1)
        self.assertIn("dataset_id", payload["datasets"][0])
        self.assertIn("runnable", payload["datasets"][0])
        self.assertIn("warnings", payload["datasets"][0])
        self.assertIn("blocking_errors", payload["datasets"][0])

    def test_helpers_do_not_create_results_artifacts_or_logs(self) -> None:
        summaries = build_fake_geo_preflight_summary()
        payload = build_fake_geo_preflight_payload(summaries)
        lines = build_fake_geo_preflight_text(summaries)

        self.assertEqual(len(summaries), 2)
        self.assertNotIn("result_id", payload["datasets"][0])
        self.assertNotIn("artifact_path", payload["datasets"][0])
        self.assertTrue(lines)


if __name__ == "__main__":
    unittest.main()
