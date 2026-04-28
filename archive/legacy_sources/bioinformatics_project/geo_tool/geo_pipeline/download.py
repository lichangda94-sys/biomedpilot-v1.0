"""Module 1: download GEO full family SOFT with GEOparse."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import GEOparse

from .common import build_gse_summary, is_gse_like, normalize_accession, save_json


LOGGER = logging.getLogger("geo_download")


class DownloadModuleError(Exception):
    """Base exception for the download module."""


class GeoDownloadError(DownloadModuleError):
    """Raised when GEO download or parsing fails."""


@dataclass
class DownloadConfig:
    accession: str
    geo_dir: str
    full_mode: str = "full"
    check_with_quick_if_full_fails: bool = True
    annotate_gpl: bool = False
    remove_corrupted_cache: bool = True
    max_full_retries: int = 2


def build_full_family_soft_path(accession: str, geo_dir: Path) -> Path:
    return geo_dir / f"{accession}_family.soft.gz"


def build_quick_txt_path(accession: str, geo_dir: Path) -> Path:
    return geo_dir / f"{accession}.txt"


def remove_file_if_exists(path: Path) -> None:
    if path.exists():
        LOGGER.warning("Removing cached file: %s", path)
        path.unlink()


def parse_existing_full_family_soft(filepath: Path, annotate_gpl: bool = False) -> Any:
    if not filepath.exists():
        raise GeoDownloadError(f"Full family SOFT file does not exist: {filepath}")
    if filepath.name.endswith(".txt"):
        raise GeoDownloadError(
            f"Quick text file is not allowed as formal analysis input: {filepath}"
        )

    try:
        gse = GEOparse.get_GEO(filepath=str(filepath), annotate_gpl=annotate_gpl, silent=False)
    except Exception as exc:
        raise GeoDownloadError(f"Failed to parse existing family SOFT: {filepath}") from exc

    if not is_gse_like(gse):
        raise GeoDownloadError(f"Parsed object is not a GSE-like object: {type(gse)!r}")

    return gse


def load_existing_full_family_soft(accession: str, geo_dir: str) -> dict[str, Any]:
    try:
        accession = normalize_accession(accession)
    except ValueError as exc:
        raise DownloadModuleError(str(exc)) from exc

    geo_dir_path = Path(geo_dir).expanduser().resolve()
    family_soft_path = build_full_family_soft_path(accession, geo_dir_path)

    gse = parse_existing_full_family_soft(family_soft_path, annotate_gpl=False)
    result = {
        "status": "success",
        "accession": accession,
        "geo_dir": str(geo_dir_path),
        "family_soft_path": str(family_soft_path),
        "quick_check_path": None,
        "full_download_success": True,
        "quick_check_success": False,
        "quick_check_used": False,
        "annotate_gpl": False,
        "max_full_retries": 0,
        "summary": build_gse_summary(gse),
        "error": None,
        "note": "Loaded existing full family SOFT from local cache.",
    }
    save_json(result, geo_dir_path / f"{accession}_download_summary.json")
    return result


def try_get_geo(accession: str, geo_dir: Path, how: str, annotate_gpl: bool) -> Any:
    try:
        return GEOparse.get_GEO(
            geo=accession,
            destdir=str(geo_dir),
            how=how,
            annotate_gpl=annotate_gpl,
            silent=False,
        )
    except Exception as exc:
        raise GeoDownloadError(f"GEOparse.get_GEO failed for {accession} with how={how}") from exc


def download_full_family_soft(config: DownloadConfig) -> dict[str, Any]:
    try:
        accession = normalize_accession(config.accession)
    except ValueError as exc:
        raise DownloadModuleError(str(exc)) from exc

    geo_dir = Path(config.geo_dir).expanduser().resolve()
    geo_dir.mkdir(parents=True, exist_ok=True)
    LOGGER.info("[DOWNLOAD] accession=%s start download", accession)

    family_soft_path = build_full_family_soft_path(accession, geo_dir)
    quick_check_path = build_quick_txt_path(accession, geo_dir)
    summary_path = geo_dir / f"{accession}_download_summary.json"

    result: dict[str, Any] = {
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

    last_full_error: Optional[Exception] = None
    total_attempts = max(config.max_full_retries, 0) + 1

    for _attempt in range(1, total_attempts + 1):
        try:
            gse = try_get_geo(
                accession=accession,
                geo_dir=geo_dir,
                how=config.full_mode,
                annotate_gpl=config.annotate_gpl,
            )
            if not is_gse_like(gse):
                raise GeoDownloadError(
                    f"Expected a GSE-like object from full download, got {type(gse)!r}"
                )

            result["status"] = "success"
            result["full_download_success"] = True
            result["summary"] = build_gse_summary(gse)
            result["note"] = "Full family SOFT downloaded and parsed successfully."
            result["error"] = None
            LOGGER.info("[DOWNLOAD] accession=%s download success summary=%s", accession, result["summary"])
            save_json(result, summary_path)
            return result
        except Exception as exc:
            last_full_error = exc
            LOGGER.warning("[DOWNLOAD] accession=%s attempt failed: %s", accession, exc)
            if config.remove_corrupted_cache:
                remove_file_if_exists(family_soft_path)

    result["error"] = str(last_full_error) if last_full_error else "Unknown full download error"

    if config.check_with_quick_if_full_fails:
        result["quick_check_used"] = True
        try:
            quick_obj = try_get_geo(
                accession=accession,
                geo_dir=geo_dir,
                how="quick",
                annotate_gpl=False,
            )
            if not is_gse_like(quick_obj):
                raise GeoDownloadError(
                    f"Quick check did not return a GSE-like object: {type(quick_obj)!r}"
                )
            result["quick_check_success"] = True
            result["status"] = "failed_full_but_quick_accessible"
            result["summary"] = build_gse_summary(quick_obj)
            result["note"] = (
                "Full family SOFT failed, but quick accessibility check succeeded. "
                "Quick result is for connectivity/accession validation only and must not "
                "be passed to the processing module."
            )
        except Exception as exc:
            if config.remove_corrupted_cache:
                remove_file_if_exists(quick_check_path)
            result["status"] = "failed"
            result["quick_check_success"] = False
            result["note"] = (
                "Full family SOFT failed and quick accessibility check also failed."
            )
            result["error"] = (
                f"{result['error']}; quick_check_error={exc}"
                if result["error"]
                else f"quick_check_error={exc}"
            )
    else:
        result["note"] = "Full family SOFT failed. Quick accessibility check disabled."

    save_json(result, summary_path)
    return result
