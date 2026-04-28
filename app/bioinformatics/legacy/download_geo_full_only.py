#!/usr/bin/env python3
"""Compatibility-only legacy download entrypoint; not part of the frozen GEO mainline.

Download GEO GSE full family SOFT only.

Quick mode is allowed only as an accessibility check after full download fails.
Quick results must never be used as formal downstream processing input.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

import GEOparse


LOGGER = logging.getLogger("download_geo_full_only")


class DownloadModuleError(Exception):
    """Base exception for download module failures."""


class GeoDownloadError(DownloadModuleError):
    """Raised when GEO full family SOFT download or parsing fails."""


@dataclass
class DownloadConfig:
    accession: str
    geo_dir: str
    full_mode: str = "full"
    check_with_quick_if_full_fails: bool = True
    annotate_gpl: bool = False
    remove_corrupted_cache: bool = True
    max_full_retries: int = 2


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def normalize_accession(accession: str) -> str:
    accession = accession.strip().upper()
    if not accession.startswith("GSE"):
        raise DownloadModuleError(f"Only GSE accessions are supported, got: {accession}")
    return accession


def is_gse_like(obj: Any) -> bool:
    return (
        obj is not None
        and getattr(obj, "__class__", type(None)).__name__ == "GSE"
        and hasattr(obj, "gsms")
    )


class GeoObjectView:
    """Thin BaseGEO-like interface for GEOparse objects."""

    def __init__(self, geo_object: Any):
        self.geo_object = geo_object
        self.name = getattr(geo_object, "name", None)
        self.metadata = getattr(geo_object, "metadata", {}) or {}
        self.relations = getattr(geo_object, "relations", {}) or {}

    def get_accession(self) -> Optional[str]:
        if hasattr(self.geo_object, "get_accession"):
            return self.geo_object.get_accession()
        value = self.metadata.get("geo_accession")
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def get_type(self) -> Optional[str]:
        if hasattr(self.geo_object, "get_type"):
            return self.geo_object.get_type()
        value = self.metadata.get("type")
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def get_metadata_attribute(self, metaname: str) -> Any:
        value = self.metadata.get(metaname)
        if value is None:
            return None
        if isinstance(value, list):
            return value if len(value) > 1 else value[0]
        return value


def save_json(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def build_family_soft_path(accession: str, geo_dir: Path) -> Path:
    return geo_dir / f"{accession}_family.soft.gz"


def build_quick_path(accession: str, geo_dir: Path) -> Path:
    return geo_dir / f"{accession}.txt"


def build_summary_payload(
    accession: str,
    geo_dir: Path,
    family_soft_path: Path,
    quick_check_path: Path,
    config: DownloadConfig,
) -> dict[str, Any]:
    return {
        "status": "failed",
        "accession": accession,
        "geo_dir": str(geo_dir),
        "family_soft_path": str(family_soft_path),
        "quick_check_path": str(quick_check_path),
        "full_download_success": False,
        "quick_check_success": False,
        "quick_check_used": False,
        "annotate_gpl": config.annotate_gpl,
        "max_full_retries": config.max_full_retries,
        "summary": None,
        "error": None,
        "note": None,
    }


def build_gse_summary(gse: Any) -> dict[str, Any]:
    geo = GeoObjectView(gse)
    metadata = geo.metadata
    title = geo.get_metadata_attribute("title") or geo.name
    return {
        "geo_type": geo.get_type() or getattr(gse, "__class__", type(None)).__name__,
        "name": title,
        "n_samples": len(getattr(gse, "gsms", {}) or {}),
        "n_platforms": len(getattr(gse, "gpls", {}) or {}),
        "metadata_keys": sorted(metadata.keys()),
    }


def remove_cached_file(path: Path) -> None:
    if path.exists():
        LOGGER.warning("Removing cached file: %s", path)
        path.unlink()


def remove_corrupted_download_artifacts(accession: str, geo_dir: Path) -> None:
    patterns = [
        f"{accession}_family.soft.gz",
        f"{accession}.txt",
        f"{accession}*part",
        f"{accession}*tmp",
        f"{accession}*download",
    ]
    for pattern in patterns:
        for path in geo_dir.glob(pattern):
            if path.is_file():
                remove_cached_file(path)


def parse_full_family_soft(filepath: Path, annotate_gpl: bool = False) -> Any:
    if not filepath.exists():
        raise GeoDownloadError(f"Full family SOFT file does not exist: {filepath}")
    if filepath.name.endswith(".txt"):
        raise GeoDownloadError(
            f"Quick text file is not allowed as formal processing input: {filepath}"
        )

    LOGGER.info("Parsing local full family SOFT: %s", filepath)
    try:
        gse = GEOparse.get_GEO(
            filepath=str(filepath),
            annotate_gpl=annotate_gpl,
            silent=False,
        )
    except Exception as exc:
        raise GeoDownloadError(f"Failed to parse local family SOFT: {filepath}") from exc

    if not is_gse_like(gse):
        raise GeoDownloadError(
            f"Parsed object is not a GSE-like object: {type(gse)!r}"
        )
    return gse


def load_existing_full_family_soft(accession: str, geo_dir: str) -> dict[str, Any]:
    accession = normalize_accession(accession)
    geo_dir_path = Path(geo_dir).expanduser().resolve()
    family_soft_path = build_family_soft_path(accession, geo_dir_path)
    quick_check_path = build_quick_path(accession, geo_dir_path)
    config = DownloadConfig(accession=accession, geo_dir=str(geo_dir_path))
    result = build_summary_payload(
        accession=accession,
        geo_dir=geo_dir_path,
        family_soft_path=family_soft_path,
        quick_check_path=quick_check_path,
        config=config,
    )
    gse = parse_full_family_soft(family_soft_path, annotate_gpl=False)
    result.update(
        {
            "status": "success",
            "full_download_success": True,
            "summary": build_gse_summary(gse),
            "error": None,
            "note": "Loaded existing local full family SOFT successfully.",
        }
    )
    save_json(result, geo_dir_path / "download_summary.json")
    return result


def call_get_geo(
    accession: str,
    geo_dir: Path,
    how: str,
    annotate_gpl: bool,
) -> Any:
    LOGGER.info(
        "Calling GEOparse.get_GEO(geo=%s, destdir=%s, how=%s, annotate_gpl=%s)",
        accession,
        geo_dir,
        how,
        annotate_gpl,
    )
    try:
        return GEOparse.get_GEO(
            geo=accession,
            destdir=str(geo_dir),
            how=how,
            annotate_gpl=annotate_gpl,
            silent=False,
        )
    except Exception as exc:
        raise GeoDownloadError(
            f"GEOparse.get_GEO failed for accession={accession}, how={how}"
        ) from exc


def download_full_family_soft(config: DownloadConfig) -> dict[str, Any]:
    accession = normalize_accession(config.accession)
    geo_dir = Path(config.geo_dir).expanduser().resolve()
    geo_dir.mkdir(parents=True, exist_ok=True)
    family_soft_path = build_family_soft_path(accession, geo_dir)
    quick_check_path = build_quick_path(accession, geo_dir)
    summary_path = geo_dir / "download_summary.json"
    result = build_summary_payload(
        accession=accession,
        geo_dir=geo_dir,
        family_soft_path=family_soft_path,
        quick_check_path=quick_check_path,
        config=config,
    )

    LOGGER.info("Starting full family SOFT download for %s", accession)
    total_attempts = max(0, config.max_full_retries) + 1
    last_full_error: Optional[Exception] = None

    for attempt in range(1, total_attempts + 1):
        LOGGER.info("Full download attempt %s/%s", attempt, total_attempts)
        try:
            gse = call_get_geo(
                accession=accession,
                geo_dir=geo_dir,
                how=config.full_mode,
                annotate_gpl=config.annotate_gpl,
            )
            if not is_gse_like(gse):
                raise GeoDownloadError(
                    f"Full mode returned a non-GSE object: {type(gse)!r}"
                )
            result.update(
                {
                    "status": "success",
                    "full_download_success": True,
                    "summary": build_gse_summary(gse),
                    "error": None,
                    "note": "Full family SOFT downloaded and parsed successfully.",
                }
            )
            save_json(result, summary_path)
            LOGGER.info("Full family SOFT download succeeded for %s", accession)
            return result
        except Exception as exc:
            last_full_error = exc
            LOGGER.exception("Full family SOFT attempt failed for %s", accession)
            if config.remove_corrupted_cache:
                LOGGER.warning(
                    "Removing potentially corrupted full-download cache before retry"
                )
                remove_corrupted_download_artifacts(accession, geo_dir)

    result["error"] = str(last_full_error) if last_full_error else "Unknown full download error"

    if config.check_with_quick_if_full_fails:
        result["quick_check_used"] = True
        LOGGER.warning(
            "Full family SOFT download failed. Falling back to quick mode for accessibility check only."
        )
        try:
            quick_obj = call_get_geo(
                accession=accession,
                geo_dir=geo_dir,
                how="quick",
                annotate_gpl=False,
            )
            if not is_gse_like(quick_obj):
                raise GeoDownloadError(
                    f"Quick mode returned a non-GSE object: {type(quick_obj)!r}"
                )
            result.update(
                {
                    "status": "failed_full_but_quick_accessible",
                    "quick_check_success": True,
                    "summary": build_gse_summary(quick_obj),
                    "note": (
                        "Full family SOFT failed, but quick mode confirms the accession is accessible. "
                        "Quick output is for accessibility checking only and must not enter formal processing."
                    ),
                }
            )
        except Exception as exc:
            LOGGER.exception("Quick accessibility check failed for %s", accession)
            if config.remove_corrupted_cache:
                remove_cached_file(quick_check_path)
            result.update(
                {
                    "status": "failed",
                    "quick_check_success": False,
                    "note": "Full family SOFT failed and quick accessibility check also failed.",
                    "error": (
                        f"{result['error']}; quick_check_error={exc}"
                        if result["error"]
                        else f"quick_check_error={exc}"
                    ),
                }
            )
    else:
        result["note"] = "Full family SOFT failed. Quick accessibility check was disabled."

    save_json(result, summary_path)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download GEO GSE full family SOFT. Quick mode is only used as an accessibility check."
    )
    parser.add_argument("accession", help="GSE accession, for example GSE12345")
    parser.add_argument(
        "--geo-dir",
        default="geo_downloads",
        help="Directory for GEOparse cache and downloaded files",
    )
    parser.add_argument(
        "--annotate-gpl",
        action="store_true",
        help="Pass annotate_gpl=True into GEOparse.get_GEO",
    )
    parser.add_argument(
        "--disable-quick-check",
        action="store_true",
        help="Do not run quick accessibility check when full mode fails",
    )
    parser.add_argument(
        "--keep-corrupted-cache",
        action="store_true",
        help="Do not delete corrupted cache files after failed attempts",
    )
    parser.add_argument(
        "--max-full-retries",
        type=int,
        default=2,
        help="Number of retries after the first full download attempt",
    )
    parser.add_argument(
        "--load-existing-only",
        action="store_true",
        help="Parse an existing local full family SOFT only, without any download",
    )
    return parser.parse_args()


def main() -> int:
    configure_logging()
    args = parse_args()

    try:
        if args.load_existing_only:
            result = load_existing_full_family_soft(args.accession, args.geo_dir)
        else:
            config = DownloadConfig(
                accession=args.accession,
                geo_dir=args.geo_dir,
                annotate_gpl=args.annotate_gpl,
                check_with_quick_if_full_fails=not args.disable_quick_check,
                remove_corrupted_cache=not args.keep_corrupted_cache,
                max_full_retries=args.max_full_retries,
            )
            LOGGER.info("Download config: %s", json.dumps(asdict(config), ensure_ascii=False))
            result = download_full_family_soft(config)
    except DownloadModuleError as exc:
        LOGGER.error("Download module failed: %s", exc, exc_info=True)
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2, ensure_ascii=False))
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
