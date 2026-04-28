from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from analysis.analysis_preflight import build_geo_series_matrix_preflight_summary  # noqa: E402
from analysis.group_detection import detect_geo_sample_groups  # noqa: E402
from geo_readiness.accession_parser import parse_geo_accession_metadata  # noqa: E402
from geo_readiness.platform_annotation_parser import (  # noqa: E402
    parse_platform_annotation_mapping_report,
)
from geo_readiness.real_dataset_report import (  # noqa: E402
    RealDatasetReadinessReport,
    build_real_dataset_readiness_report,
)
from geo_readiness.series_matrix_parser import (  # noqa: E402
    parse_series_matrix_expression_report,
    parse_series_matrix_metadata,
)
from geo_readiness.soft_parser import (  # noqa: E402
    parse_geo_soft_expression_report,
    parse_geo_soft_metadata,
    parse_geo_soft_platform_mapping_report,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a controlled local-file real GEO readiness test. "
            "This does not download data or execute DEG/enrichment/survival."
        )
    )
    parser.add_argument("--dataset-id", required=True, help="Dataset accession or test id.")
    parser.add_argument("--metadata-file", type=Path, help="Saved GEO accession HTML/text.")
    parser.add_argument("--series-matrix-file", type=Path, help="Local Series Matrix .txt/.txt.gz.")
    parser.add_argument("--soft-file", type=Path, help="Local GEO family SOFT .soft/.soft.gz.")
    parser.add_argument("--platform-annotation-file", type=Path, help="Local GPL/platform annotation.")
    parser.add_argument("--json", action="store_true", help="Emit JSON payload.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional directory for readiness_report.json and readiness_report.md.",
    )
    return parser.parse_args(argv)


def build_real_geo_readiness_report(
    *,
    dataset_id: str,
    metadata_file: Path | None = None,
    series_matrix_file: Path | None = None,
    soft_file: Path | None = None,
    platform_annotation_file: Path | None = None,
) -> RealDatasetReadinessReport:
    metadata_payload: dict[str, Any] = {}
    series_payload: dict[str, Any] = {}
    group_payload: dict[str, Any] = {}
    expression_payload: dict[str, Any] = {}
    platform_payload: dict[str, Any] = {}
    preflight_payload: dict[str, Any] = {}

    if metadata_file is not None:
        try:
            metadata_text = metadata_file.read_text(encoding="utf-8")
        except OSError as exc:
            metadata_payload = {
                "gse_id": dataset_id,
                "warnings": [str(exc)],
                "errors": ["metadata_file_read_failed"],
            }
        else:
            metadata_payload = parse_geo_accession_metadata(metadata_text).to_dict()

    metadata_report = None
    group_report = None
    expression_report = None
    platform_report = None
    if series_matrix_file is not None:
        metadata_report = parse_series_matrix_metadata(series_matrix_file)
        series_payload = metadata_report.to_dict()
        group_report = detect_geo_sample_groups(metadata_report.sample_metadata_rows)
        group_payload = group_report.to_dict()
        expression_report = parse_series_matrix_expression_report(
            series_matrix_file,
            metadata_sample_ids=metadata_report.sample_ids,
        )
        expression_payload = expression_report.to_dict()
    elif soft_file is not None:
        metadata_report = parse_geo_soft_metadata(soft_file)
        series_payload = metadata_report.to_dict()
        group_report = detect_geo_sample_groups(metadata_report.sample_metadata_rows)
        group_payload = group_report.to_dict()
        expression_report = parse_geo_soft_expression_report(
            soft_file,
            metadata_sample_ids=metadata_report.sample_ids,
        )
        expression_payload = expression_report.to_dict()

    if platform_annotation_file is not None:
        platform_report = parse_platform_annotation_mapping_report(platform_annotation_file)
        platform_payload = platform_report.to_dict()
    elif soft_file is not None:
        platform_id = metadata_report.platform_ids[0] if metadata_report and metadata_report.platform_ids else ""
        platform_report = parse_geo_soft_platform_mapping_report(
            soft_file,
            platform_id=platform_id,
        )
        platform_payload = platform_report.to_dict()

    if metadata_report is not None and group_report is not None:
        preflight = build_geo_series_matrix_preflight_summary(
            series_matrix_metadata=metadata_report,
            group_detection=group_report,
            expression_report=expression_report,
            platform_mapping_report=platform_report,
            profile_id="controlled_real_geo_readiness",
        )
        preflight_payload = preflight.to_dict()

    return build_real_dataset_readiness_report(
        dataset_id=dataset_id,
        metadata_parse=metadata_payload,
        series_matrix_metadata=series_payload,
        group_detection=group_payload,
        expression_report=expression_payload,
        platform_mapping=platform_payload,
        preflight=preflight_payload,
    )


def format_real_dataset_readiness_markdown(report: RealDatasetReadinessReport) -> str:
    payload = report.to_dict()
    lines = [
        f"# Real Dataset Readiness Report: {report.dataset_id}",
        "",
        "## Summary",
        "",
        f"- recommended_action: `{report.recommended_action}`",
        f"- gaps: {len(report.gaps)}",
        f"- warnings: {len(report.warnings)}",
        f"- errors: {len(report.errors)}",
        "",
        "## Metadata Parse",
        "",
        f"- gse_id: `{payload['metadata_parse'].get('gse_id', '')}`",
        f"- title: {payload['metadata_parse'].get('title', '')}",
        f"- organism: {payload['metadata_parse'].get('organism', '')}",
        f"- sample_count: {payload['metadata_parse'].get('sample_count', 0)}",
        f"- platform_ids: {payload['metadata_parse'].get('platform_ids', [])}",
        "",
        "## Series Matrix Metadata",
        "",
        f"- sample_count: {payload['series_matrix_metadata'].get('sample_count', 0)}",
        f"- sample_metadata_rows: {len(payload['series_matrix_metadata'].get('sample_metadata_rows', []))}",
        "",
        "## Group Detection",
        "",
        f"- detected_groups: {payload['group_detection'].get('detected_groups', [])}",
        f"- excluded_groups: {payload['group_detection'].get('excluded_group_candidates', [])}",
        f"- ambiguous_samples: {payload['group_detection'].get('ambiguous_samples', [])}",
        f"- confidence: {payload['group_detection'].get('confidence', 0)}",
        "",
        "## Expression Report",
        "",
        f"- feature_count: {payload['expression_report'].get('feature_count', 0)}",
        f"- sample_count: {payload['expression_report'].get('sample_count', 0)}",
        f"- numeric_value_status: {payload['expression_report'].get('numeric_value_status', '')}",
        f"- missing_value_count: {payload['expression_report'].get('missing_value_count', 0)}",
        f"- sample_id_match_status: {payload['expression_report'].get('sample_id_match_status', '')}",
        "",
        "## Platform Mapping",
        "",
        f"- probe_count: {payload['platform_mapping'].get('probe_count', 0)}",
        f"- mapped_probe_count: {payload['platform_mapping'].get('mapped_probe_count', 0)}",
        f"- mapping_success_rate: {payload['platform_mapping'].get('mapping_success_rate', 0)}",
        f"- duplicated_symbol_count: {payload['platform_mapping'].get('duplicated_symbol_count', 0)}",
        f"- acceptable: {payload['platform_mapping'].get('acceptable', False)}",
        "",
        "## Preflight",
        "",
        f"- runnable: {payload['preflight'].get('runnable', False)}",
        f"- blocking_errors: {payload['preflight'].get('blocking_errors', [])}",
        f"- warnings: {payload['preflight'].get('warnings', [])}",
        f"- recommended_action: {payload['preflight'].get('recommended_action', '')}",
        "",
        "## Gaps",
        "",
    ]
    for gap in report.gaps:
        lines.append(f"- `{gap.category}`: `{gap.code}` ({gap.source})")
    if not report.gaps:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_report_files(report: RealDatasetReadinessReport, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "readiness_report.json").write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "readiness_report.md").write_text(
        format_real_dataset_readiness_markdown(report),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_real_geo_readiness_report(
        dataset_id=args.dataset_id,
        metadata_file=args.metadata_file,
        series_matrix_file=args.series_matrix_file,
        soft_file=args.soft_file,
        platform_annotation_file=args.platform_annotation_file,
    )
    if args.output_dir:
        write_report_files(report, args.output_dir)
    if args.json:
        print(json.dumps(report.to_dict(), sort_keys=True))
    else:
        print(format_real_dataset_readiness_markdown(report))
    return 1 if report.gaps else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
