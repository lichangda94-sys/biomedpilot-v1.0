from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("BIOINF_LIGHT_VALIDATION_MODE", "1")
os.environ.setdefault("BIOINF_TCGA_DOWNLOAD_LIMIT_FILES", "1")
os.environ.setdefault("BIOINF_GTEX_DOWNLOAD_LIMIT_FILES", "1")
os.environ.setdefault("BIOINF_GTEX_LIMIT_SAMPLES", "3")
os.environ.setdefault("BIOINF_GTEX_LIMIT_GENES", "10")

import ui_route_contract_bio_batch11_tcga_gtex_adapters as base


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH12_TCGA_GTEX_LIGHT_VALIDATION.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH12_TCGA_GTEX_LIGHT_VALIDATION.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_bio_batch12_tcga_gtex_light_validation"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    code = base.main(
        [
            "--json-out",
            str(args.json_out),
            "--markdown-out",
            str(args.markdown_out),
            "--screenshot-dir",
            str(args.screenshot_dir),
        ]
    )
    if args.json_out.exists():
        payload = json.loads(args.json_out.read_text(encoding="utf-8"))
        _rewrite_payload(payload)
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        args.markdown_out.write_text(base._render_markdown(payload), encoding="utf-8")
    return code


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Bio C1 TCGA/GTEx light-validation download/build adapters.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _rewrite_payload(payload: dict[str, object]) -> None:
    payload["schema_version"] = "ui_route_contract_bio_batch12_tcga_gtex_light_validation.v1"
    payload["scope"] = (
        "Bioinformatics TCGA/GTEx light-validation Data Source adapter: "
        "visible source request, metadata preview, download-plan, limited download receipt, and expression build manifest."
    )
    payload["batch"] = "Batch 12: Bioinformatics TCGA/GTEx light-validation download/build"
    payload["gate_policy"] = {
        "light_validation_mode": os.environ.get("BIOINF_LIGHT_VALIDATION_MODE", ""),
        "BIOINF_TCGA_DOWNLOAD_LIMIT_FILES": os.environ.get("BIOINF_TCGA_DOWNLOAD_LIMIT_FILES", ""),
        "BIOINF_GTEX_DOWNLOAD_LIMIT_FILES": os.environ.get("BIOINF_GTEX_DOWNLOAD_LIMIT_FILES", ""),
        "BIOINF_GTEX_LIMIT_SAMPLES": os.environ.get("BIOINF_GTEX_LIMIT_SAMPLES", ""),
        "BIOINF_GTEX_LIMIT_GENES": os.environ.get("BIOINF_GTEX_LIMIT_GENES", ""),
        "formal_analysis": "not opened by this batch",
        "production_use": "light validation artifacts are not report-ready production analysis inputs",
    }
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        row["contract_id"] = str(row.get("contract_id", "")).replace("BIO-B11-", "BIO-B12-LIGHT-")
        row["batch"] = "Batch 12: Bioinformatics TCGA/GTEx light-validation download/build"
        if "LIGHT-DOWNLOAD" in str(row.get("contract_id", "")) or "EXPRESSION-BUILD" in str(row.get("contract_id", "")):
            row["runtime_effect"] = f"{row.get('runtime_effect', '')}; light validation only, not formal analysis"


if __name__ == "__main__":
    raise SystemExit(main())
