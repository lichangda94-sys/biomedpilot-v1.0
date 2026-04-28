from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from geo_readiness.accession_parser import parse_geo_accession_metadata  # noqa: E402
from geo_readiness.live_fetch import (  # noqa: E402
    GeoMetadataFetchError,
    fetch_geo_accession_metadata,
)
from geo_readiness.models import GeoAccessionInventory  # noqa: E402


def get_recommended_action(inventory: GeoAccessionInventory) -> str:
    error_codes = set(inventory.errors)
    if "ssl_error" in error_codes:
        return (
            "Check the local certificate/Python SSL environment, use "
            "--metadata-file as the controlled fallback, and do not disable "
            "SSL verification by default."
        )
    if "network_unavailable" in error_codes:
        return "Check network access or use --metadata-file as the controlled fallback."
    if "fetch_timeout" in error_codes:
        return "Retry with a longer --timeout or use --metadata-file as the controlled fallback."
    if "http_error" in error_codes:
        return "Check the GEO accession page manually or use --metadata-file with saved metadata."
    if "accession_not_found" in error_codes:
        return "Check the GSE accession id and retry with a valid accession."
    if "metadata_file_required" in error_codes:
        return "Provide --metadata-file or explicitly opt into --live."
    if "metadata_file_read_failed" in error_codes:
        return "Check that the metadata file exists and is readable."
    if "metadata_parse_failed" in error_codes:
        return "Inspect the saved metadata text and update the parser only in a scoped parser task."
    if inventory.warnings:
        return "Review warnings before continuing controlled readiness inspection."
    return "ready_for_candidate_inventory_review"


def build_geo_accession_readiness_payload(
    inventory: GeoAccessionInventory,
) -> dict[str, Any]:
    return {
        "gse_id": inventory.gse_id,
        "title": inventory.title,
        "organism": inventory.organism,
        "sample_count": inventory.sample_count,
        "platform_ids": list(inventory.platform_ids),
        "series_matrix_candidates": len(inventory.series_matrix_candidates),
        "supplementary_candidates": len(inventory.supplementary_candidates),
        "sample_metadata_candidates": len(inventory.sample_metadata_candidates),
        "expression_candidates": len(inventory.expression_candidates),
        "warnings": list(inventory.warnings),
        "errors": list(inventory.errors),
        "recommended_action": get_recommended_action(inventory),
        "inventory": inventory.to_dict(),
    }


def build_geo_accession_readiness_text(
    inventory: GeoAccessionInventory,
) -> list[str]:
    return [
        "GEO accession readiness:",
        f"- gse id: {inventory.gse_id or 'unknown'}",
        f"- sample count: {inventory.sample_count}",
        f"- platform ids: {', '.join(inventory.platform_ids) or 'none'}",
        f"- series matrix candidates: {len(inventory.series_matrix_candidates)}",
        f"- supplementary candidates: {len(inventory.supplementary_candidates)}",
        f"- sample metadata candidates: {len(inventory.sample_metadata_candidates)}",
        f"- expression candidates: {len(inventory.expression_candidates)}",
        f"- warnings: {len(inventory.warnings)}",
        f"- errors: {len(inventory.errors)}",
        f"- recommended action: {get_recommended_action(inventory)}",
    ]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a local GEO accession metadata fixture. "
            "This does not access the network, download GEO data, or execute analysis."
        )
    )
    parser.add_argument(
        "--metadata-file",
        type=Path,
        help="Path to a saved/fake GEO-like metadata text file.",
    )
    parser.add_argument(
        "--gse",
        help="Optional expected GSE accession id for reporting checks.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch the NCBI GEO accession metadata page. Does not download data files.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Timeout in seconds for --live metadata fetch.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.live:
        try:
            metadata_text = fetch_geo_accession_metadata(args.gse or "", timeout=args.timeout)
        except GeoMetadataFetchError as exc:
            inventory = GeoAccessionInventory(
                gse_id=(args.gse or "").strip().upper(),
                errors=[exc.error_code],
                warnings=[str(exc)],
            )
        else:
            inventory = parse_geo_accession_metadata(metadata_text)
            if args.gse and inventory.gse_id and inventory.gse_id != args.gse.upper():
                inventory.warnings.append("gse_argument_mismatch")
    elif not args.metadata_file:
        inventory = GeoAccessionInventory(
            gse_id=args.gse or "",
            errors=["metadata_file_required"],
        )
    else:
        try:
            metadata_text = args.metadata_file.read_text(encoding="utf-8")
        except OSError as exc:
            inventory = GeoAccessionInventory(
                gse_id=args.gse or "",
                errors=["metadata_file_read_failed"],
                warnings=[str(exc)],
            )
        else:
            inventory = parse_geo_accession_metadata(metadata_text)
            if args.gse and inventory.gse_id and inventory.gse_id != args.gse.upper():
                inventory.warnings.append("gse_argument_mismatch")

    if args.json:
        print(json.dumps(build_geo_accession_readiness_payload(inventory), sort_keys=True))
    else:
        for line in build_geo_accession_readiness_text(inventory):
            print(line)
    return 1 if inventory.errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
