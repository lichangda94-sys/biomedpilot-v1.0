from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from analysis.analysis_preflight import (  # noqa: E402
    AnalysisPreflightSummary,
    build_fake_analysis_preflight_smoke_fixture,
    summarize_analysis_preflight_summaries,
)


def build_fake_geo_preflight_summary() -> list[AnalysisPreflightSummary]:
    return build_fake_analysis_preflight_smoke_fixture()


def build_fake_geo_preflight_text(
    summaries: list[AnalysisPreflightSummary],
) -> list[str]:
    aggregate = summarize_analysis_preflight_summaries(summaries)
    lines = [
        "Fake GEO preflight:",
        f"- total checks: {aggregate['total_checks']}",
        f"- runnable checks: {aggregate['runnable_checks']}",
        f"- blocked checks: {aggregate['blocked_checks']}",
        f"- warning count: {aggregate['warning_count']}",
        f"- blocking error count: {aggregate['blocking_error_count']}",
        "Datasets:",
    ]
    for summary in summaries:
        lines.extend(
            [
                f"- dataset id: {summary.dataset_id}",
                f"  profile id: {summary.profile_id}",
                f"  runnable: {'yes' if summary.runnable else 'no'}",
                f"  warnings: {len(summary.warnings)}",
                f"  blocking errors: {len(summary.blocking_errors)}",
                f"  recommended action: {summary.recommended_action}",
            ]
        )
    return lines


def build_fake_geo_preflight_payload(
    summaries: list[AnalysisPreflightSummary],
) -> dict[str, Any]:
    return {
        "summary": summarize_analysis_preflight_summaries(summaries),
        "datasets": [
            {
                "dataset_id": item.dataset_id,
                "profile_id": item.profile_id,
                "runnable": item.runnable,
                "warnings": list(item.warnings),
                "blocking_errors": list(item.blocking_errors),
                "recommended_action": item.recommended_action,
            }
            for item in summaries
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run an in-memory fake GEO readiness preflight. "
            "This does not download GEO data or execute analysis."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summaries = build_fake_geo_preflight_summary()
    if args.json:
        print(json.dumps(build_fake_geo_preflight_payload(summaries), sort_keys=True))
    else:
        for line in build_fake_geo_preflight_text(summaries):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
