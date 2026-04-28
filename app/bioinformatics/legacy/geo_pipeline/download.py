"""Module 1: remote discovery, scoring, planning, and download execution for GEO datasets."""

from __future__ import annotations

import argparse
import gzip
import os
import json
import logging
import re
import shutil
import ssl
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import GEOparse

from .common import build_gse_summary, configure_logging, is_gse_like, normalize_accession, save_json
from geo_processing.module1_contracts import (
    build_download_plan_payload,
    build_download_receipt_payload,
    derive_module1_state,
)


LOGGER = logging.getLogger("geo_download")
MODULE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = MODULE_ROOT.parent

GEO_FTP_ROOT = "https://ftp.ncbi.nlm.nih.gov/geo"
TEXT_PRIORITY_EXTENSIONS = {".txt", ".tsv", ".csv", ".xlsx", ".xls", ".txt.gz", ".tsv.gz", ".csv.gz"}
ARCHIVE_EXTENSIONS = {".zip", ".tar", ".tar.gz", ".tgz"}
PLATFORM_HINTS = ("gpl", "platform", "annotation", "annot", "probe", "mapping")
EXPRESSION_HINTS = ("matrix", "expression", "expr", "count", "counts", "normalized", "tpm", "fpkm", "rpkm")
SAMPLE_HINTS = ("sample", "phenotype", "metadata", "design", "group", "annotation")
CLINICAL_HINTS = ("clinical", "patient", "survival", "stage", "grade", "response", "pathology")
SUPPORTING_HINTS = ("readme", "protocol", "note", "summary", "pdf", "doc")
SRA_HINTS = ("sra", "srx", "srp", "biosample")
URL_RE = __import__("re").compile(r"https?://\S+")
SERIES_SUPP_RE = re.compile(r"^!Series_supplementary_file\s*=\s*(.+)$", re.IGNORECASE)


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


@dataclass
class RemoteCandidate:
    accession: str
    source_level: str
    source_accession: str
    remote_url: str
    file_name: str
    file_ext: str
    guessed_role: str
    priority_score: float = 0.0
    required: bool = False
    should_download: bool = False
    reasons: list[str] = field(default_factory=list)
    decision_trace: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    size_hint: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _stat_file_state(path: Path) -> dict[str, Any]:
    exists = path.exists()
    size = 0
    if exists:
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
    return {
        "final_saved_path": str(path),
        "file_exists_after_save": exists,
        "file_size_on_disk": size,
    }


def _append_transaction(
    log_entries: list[dict[str, Any]],
    *,
    candidate: RemoteCandidate | None,
    started_at: float,
    ended_at: float,
    response_status: str,
    bytes_received: int | None,
    final_path: Path,
    error_message: str | None = None,
) -> None:
    file_state = _stat_file_state(final_path)
    entry = {
        "accession": candidate.accession if candidate else None,
        "source_level": candidate.source_level if candidate else None,
        "source_accession": candidate.source_accession if candidate else None,
        "guessed_role": candidate.guessed_role if candidate else None,
        "file_type": candidate.guessed_role if candidate else None,
        "remote_url": candidate.remote_url if candidate else None,
        "request_started_at": started_at,
        "request_finished_at": ended_at,
        "response_status": response_status,
        "bytes_received": bytes_received,
        **file_state,
        "final_size_on_disk": file_state["file_size_on_disk"],
        "error_message": error_message,
    }
    log_entries.append(entry)


def _series_prefix(accession: str) -> str:
    digits = accession[3:]
    prefix = digits[:-3] if len(digits) > 3 else "0"
    return f"GSE{prefix}nnn"


def _platform_prefix(accession: str) -> str:
    digits = accession[3:]
    prefix = digits[:-3] if len(digits) > 3 else "0"
    return f"GPL{prefix}nnn"


def _normalize_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _extract_urls(values: Iterable[Any]) -> list[str]:
    urls: list[str] = []
    for value in values:
        for match in URL_RE.findall(str(value)):
            urls.append(match.rstrip(";,"))
    return sorted(dict.fromkeys(urls))


def _normalize_file_ext(file_name: str) -> str:
    suffixes = [suffix.lower() for suffix in Path(file_name).suffixes]
    if len(suffixes) >= 2 and suffixes[-1] == ".gz":
        return "".join(suffixes[-2:])
    return suffixes[-1] if suffixes else ""


def _normalize_remote_url(url: str) -> str:
    cleaned = str(url).strip().strip('"')
    if cleaned.lower().startswith("ftp://ftp.ncbi.nlm.nih.gov/"):
        return "https://" + cleaned[len("ftp://") :]
    return cleaned


def _discover_series_supplementary_urls_from_quick_text(accession: str) -> list[str]:
    quick_txt = REPO_ROOT / f"{accession}.txt"
    if not quick_txt.exists():
        return []
    urls: list[str] = []
    try:
        for line in quick_txt.read_text(encoding="utf-8", errors="replace").splitlines():
            match = SERIES_SUPP_RE.match(line.strip())
            if not match:
                continue
            raw_value = _normalize_remote_url(match.group(1))
            if raw_value and raw_value.upper() != "NONE":
                urls.append(raw_value)
    except Exception:
        return []
    return sorted(dict.fromkeys(urls))


def _discover_series_supplementary_urls_from_family_soft(family_soft_path: Path) -> list[str]:
    if not family_soft_path.exists():
        return []
    urls: list[str] = []
    try:
        opener = gzip.open if family_soft_path.suffix == ".gz" else Path.open
        with opener(family_soft_path, "rt", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                match = SERIES_SUPP_RE.match(line.strip())
                if not match:
                    continue
                raw_value = _normalize_remote_url(match.group(1))
                if raw_value and raw_value.upper() != "NONE":
                    urls.append(raw_value)
    except Exception:
        return []
    return sorted(dict.fromkeys(urls))


def _infer_role(file_name: str, remote_url: str = "") -> str:
    haystack = f"{file_name} {remote_url}".lower()
    if "family.soft" in haystack:
        return "family_soft"
    if "readme" in haystack or haystack.endswith(".pdf"):
        return "supporting_doc"
    if any(haystack.endswith(ext) for ext in ARCHIVE_EXTENSIONS) or "raw.tar" in haystack:
        return "archive"
    if "series_matrix" in haystack or "matrix" in haystack and any(token in haystack for token in EXPRESSION_HINTS):
        return "expression_payload"
    if any(token in haystack for token in CLINICAL_HINTS):
        return "clinical_annotation"
    if any(token in haystack for token in SAMPLE_HINTS):
        return "sample_annotation"
    if any(token in haystack for token in PLATFORM_HINTS):
        return "platform_annotation"
    if any(token in haystack for token in SRA_HINTS):
        return "external_raw_source"
    if any(token in haystack for token in SUPPORTING_HINTS):
        return "supporting_doc"
    return "unknown"


def _candidate(
    *,
    accession: str,
    source_level: str,
    source_accession: str,
    remote_url: str,
    file_name: str,
    guessed_role: str | None = None,
    required: bool = False,
    size_hint: int | None = None,
    extra: dict[str, Any] | None = None,
) -> RemoteCandidate:
    remote_url = _normalize_remote_url(remote_url)
    role = guessed_role or _infer_role(file_name, remote_url)
    return RemoteCandidate(
        accession=accession,
        source_level=source_level,
        source_accession=source_accession,
        remote_url=remote_url,
        file_name=file_name,
        file_ext=_normalize_file_ext(file_name),
        guessed_role=role,
        required=required,
        size_hint=size_hint,
        extra=extra or {},
    )


def _trace_candidate(candidate: RemoteCandidate, message: str) -> None:
    if message not in candidate.decision_trace:
        candidate.decision_trace.append(message)


def _should_export_debug_snapshots(dataset_root: Path) -> bool:
    if os.environ.get("GEO_DEBUG_SNAPSHOTS", "").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    if (dataset_root / "expected.json").exists():
        return True
    lowered = str(dataset_root).lower()
    return any(token in lowered for token in ("test", "debug", "sandbox"))


def _write_debug_snapshot(dataset_root: Path, name: str, payload: Any) -> str:
    snapshot_dir = dataset_root / "organized" / "reports" / "debug_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    path = snapshot_dir / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def _dedupe_candidates(candidates: Iterable[RemoteCandidate]) -> list[RemoteCandidate]:
    merged: dict[tuple[str, str], RemoteCandidate] = {}
    for candidate in candidates:
        key = (candidate.remote_url, candidate.file_name)
        if key not in merged:
            merged[key] = candidate
            continue
        current = merged[key]
        current.required = current.required or candidate.required
        current.reasons.extend(reason for reason in candidate.reasons if reason not in current.reasons)
        current.warnings.extend(warning for warning in candidate.warnings if warning not in current.warnings)
        current.extra.update({k: v for k, v in candidate.extra.items() if k not in current.extra})
        current.priority_score = max(current.priority_score, candidate.priority_score)
    return list(merged.values())


def _probe_remote_candidate_metadata(remote_url: str) -> dict[str, Any]:
    """Best-effort remote metadata probe without downloading the full file."""
    remote_url = _normalize_remote_url(remote_url)
    metadata: dict[str, Any] = {"remote_url": remote_url}
    try:
        request = Request(remote_url, method="HEAD", headers={"User-Agent": "codex-geo-downloader"})
        open_kwargs = {"timeout": 30}
        if remote_url.startswith("https://ftp.ncbi.nlm.nih.gov/"):
            open_kwargs["context"] = ssl._create_unverified_context()
        with urlopen(request, **open_kwargs) as response:
            headers = response.headers
            metadata["size_hint"] = int(headers.get("Content-Length", "0") or 0) or None
            metadata["content_type"] = headers.get("Content-Type")
            metadata["content_disposition"] = headers.get("Content-Disposition")
            metadata["final_url"] = response.geturl()
    except Exception as exc:
        metadata["probe_error"] = str(exc)
    return metadata


def _resolve_remote_file_name(remote_url: str, probe_info: dict[str, Any] | None = None) -> str:
    probe_info = probe_info or {}
    disposition = str(probe_info.get("content_disposition") or "")
    match = None
    if disposition:
        match = next(
            (
                part.split("=", 1)[1].strip().strip('"')
                for part in disposition.split(";")
                if "filename=" in part.lower()
            ),
            None,
        )
    if match:
        return match
    final_url = str(probe_info.get("final_url") or remote_url)
    return Path(urlparse(final_url).path).name or Path(urlparse(remote_url).path).name


def _classify_supplementary_role(file_name: str, remote_url: str, probe_info: dict[str, Any] | None = None) -> str:
    probe_info = probe_info or {}
    file_haystack = f"{file_name} {remote_url}".lower()
    content_type = str(probe_info.get("content_type", "")).lower()
    haystack = f"{file_haystack} {content_type}"
    if any(token in file_haystack for token in ("readme", ".pdf", "protocol", "manual")) or "application/pdf" in content_type:
        return "supporting_doc"
    if "raw.tar" in haystack or any(file_name.lower().endswith(ext) for ext in ARCHIVE_EXTENSIONS):
        return "archive"
    if any(token in haystack for token in EXPRESSION_HINTS) or file_name.lower().endswith((".xlsx", ".xls", ".txt", ".tsv", ".csv", ".txt.gz", ".tsv.gz", ".csv.gz")):
        if not any(token in haystack for token in ("readme", "protocol", "manual", "logfc", "padj")):
            return "expression_payload"
    if any(token in haystack for token in CLINICAL_HINTS):
        return "clinical_annotation"
    if any(token in haystack for token in SAMPLE_HINTS):
        return "sample_annotation"
    if any(token in haystack for token in PLATFORM_HINTS):
        return "platform_annotation"
    if any(token in haystack for token in SUPPORTING_HINTS):
        return "supporting_doc"
    return "unknown"


def try_get_geo(accession: str, geo_dir: Path, how: str, annotate_gpl: bool) -> Any:
    LOGGER.info("Calling GEOparse.get_GEO(accession=%s, how=%s)", accession, how)
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


def _load_quick_gse(accession: str) -> Any:
    temp_dir = REPO_ROOT
    gse = try_get_geo(accession=accession, geo_dir=temp_dir, how="quick", annotate_gpl=False)
    if not is_gse_like(gse):
        raise GeoDownloadError(f"Quick GEO object is not GSE-like: {type(gse)!r}")
    return gse


def discover_series_level_candidates(gse_id: str) -> list[RemoteCandidate]:
    accession = normalize_accession(gse_id)
    prefix = _series_prefix(accession)
    base = f"{GEO_FTP_ROOT}/series/{prefix}/{accession}"
    candidates = [
        _candidate(
            accession=accession,
            source_level="series",
            source_accession=accession,
            remote_url=f"{base}/soft/{accession}_family.soft.gz",
            file_name=f"{accession}_family.soft.gz",
            guessed_role="family_soft",
            required=True,
            extra={"core_record": True},
        ),
        _candidate(
            accession=accession,
            source_level="series",
            source_accession=accession,
            remote_url=f"{base}/matrix/{accession}_series_matrix.txt.gz",
            file_name=f"{accession}_series_matrix.txt.gz",
            guessed_role="expression_payload",
            required=True,
            extra={"core_record": True, "container": "series_matrix"},
        ),
        _candidate(
            accession=accession,
            source_level="series",
            source_accession=accession,
            remote_url=f"{base}/miniml/{accession}_family.xml.tgz",
            file_name=f"{accession}_family.xml.tgz",
            guessed_role="miniml",
            required=True,
            extra={"core_record": True},
        ),
    ]
    try:
        gse = _load_quick_gse(accession)
    except Exception as exc:
        for candidate in candidates:
            candidate.warnings.append(f"quick discovery unavailable: {exc}")
        return candidates

    supplementary_candidates = discover_series_supplementary_candidates(accession)
    for candidate in supplementary_candidates:
        if "series-level supplementary candidate" not in " ".join(candidate.reasons):
            candidate.reasons.append("discovered from series supplementary enumeration")
        _trace_candidate(candidate, "discovered from series supplementary")
        candidates.append(candidate)

    candidates.append(
        _candidate(
            accession=accession,
            source_level="series",
            source_accession=accession,
            remote_url=f"geo://{accession}/series_supplementary_index",
            file_name=f"{accession}_series_supplementary_index.json",
            guessed_role="supplementary_index",
            required=True,
            extra={"generated_from_discovery": True},
        )
    )
    return _dedupe_candidates(candidates)


def discover_series_supplementary_candidates(gse_id: str) -> list[RemoteCandidate]:
    accession = normalize_accession(gse_id)
    try:
        gse = _load_quick_gse(accession)
    except Exception:
        return []
    metadata = getattr(gse, "metadata", {}) or {}
    fallback_urls = _discover_series_supplementary_urls_from_quick_text(accession)
    supplementary_values = _normalize_values(metadata.get("supplementary_file"))
    if not supplementary_values:
        supplementary_values = fallback_urls
    candidates: list[RemoteCandidate] = []
    for raw_url in supplementary_values:
        probe_info = _probe_remote_candidate_metadata(raw_url)
        file_name = _resolve_remote_file_name(raw_url, probe_info) or f"{accession}_supplementary"
        guessed_role = _classify_supplementary_role(file_name, raw_url, probe_info)
        candidate = _candidate(
            accession=accession,
            source_level="series",
            source_accession=accession,
            remote_url=raw_url,
            file_name=file_name,
            guessed_role=guessed_role,
            size_hint=probe_info.get("size_hint"),
            extra={
                "metadata_field": "supplementary_file",
                "series_level": True,
                "content_type": probe_info.get("content_type"),
                "content_disposition": probe_info.get("content_disposition"),
                "probe_error": probe_info.get("probe_error"),
                "final_url": probe_info.get("final_url"),
            },
        )
        candidate.reasons.append("series-level supplementary candidate discovered from GSE metadata")
        candidate.reasons.append("real supplementary URL enumerated from series metadata")
        _trace_candidate(candidate, "discovered from series supplementary metadata")
        if raw_url in fallback_urls:
            candidate.reasons.append("series supplementary was recovered from quick text fallback")
            _trace_candidate(candidate, "discovered from series supplementary quick-text fallback")
        if probe_info.get("size_hint"):
            candidate.reasons.append("remote probe returned content length")
            _trace_candidate(candidate, "remote probe returned content length")
        if probe_info.get("content_type"):
            _trace_candidate(candidate, f"remote probe indicates {probe_info['content_type']}")
        if probe_info.get("probe_error"):
            candidate.warnings.append(f"remote probe failed: {probe_info['probe_error']}")
            _trace_candidate(candidate, "remote probe failed during supplementary discovery")
        candidates.append(candidate)
    return _dedupe_candidates(candidates)


def discover_series_supplementary_candidates_from_family_soft(gse_id: str, family_soft_path: str) -> list[RemoteCandidate]:
    accession = normalize_accession(gse_id)
    urls = _discover_series_supplementary_urls_from_family_soft(Path(family_soft_path).expanduser().resolve())
    candidates: list[RemoteCandidate] = []
    for raw_url in urls:
        probe_info = _probe_remote_candidate_metadata(raw_url)
        file_name = _resolve_remote_file_name(raw_url, probe_info) or f"{accession}_supplementary"
        guessed_role = _classify_supplementary_role(file_name, raw_url, probe_info)
        candidate = _candidate(
            accession=accession,
            source_level="series_supplementary",
            source_accession=accession,
            remote_url=raw_url,
            file_name=file_name,
            guessed_role=guessed_role,
            size_hint=probe_info.get("size_hint"),
            extra={
                "discovered_from": "family_soft",
                "content_type": probe_info.get("content_type"),
                "probe_error": probe_info.get("probe_error"),
            },
        )
        candidate.reasons.append("series supplementary candidate discovered from downloaded family.soft")
        _trace_candidate(candidate, "discovered from downloaded family.soft supplementary metadata")
        if probe_info.get("content_type"):
            _trace_candidate(candidate, f"remote probe indicates {probe_info['content_type']}")
        if probe_info.get("probe_error"):
            candidate.warnings.append(f"remote probe failed: {probe_info['probe_error']}")
        candidates.append(candidate)
    return _dedupe_candidates(candidates)


def discover_sample_level_candidates(gse_id: str) -> list[RemoteCandidate]:
    accession = normalize_accession(gse_id)
    try:
        gse = _load_quick_gse(accession)
    except Exception:
        return []
    candidates: list[RemoteCandidate] = []
    for gsm_name, gsm in (getattr(gse, "gsms", {}) or {}).items():
        metadata = getattr(gsm, "metadata", {}) or {}
        for key, values in metadata.items():
            if "supplementary_file" not in key.lower():
                continue
            for raw_url in _normalize_values(values):
                if raw_url.upper() == "NONE":
                    continue
                if any(token in raw_url.lower() for token in SRA_HINTS):
                    continue
                probe_info = _probe_remote_candidate_metadata(raw_url)
                file_name = _resolve_remote_file_name(raw_url, probe_info) or f"{gsm_name}_supplementary"
                guessed_role = _classify_supplementary_role(file_name, raw_url, probe_info)
                candidate = _candidate(
                    accession=accession,
                    source_level="sample",
                    source_accession=str(gsm_name),
                    remote_url=raw_url,
                    file_name=file_name,
                    guessed_role=guessed_role,
                    size_hint=probe_info.get("size_hint"),
                    extra={
                        "metadata_field": key,
                        "gsm": str(gsm_name),
                        "content_type": probe_info.get("content_type"),
                        "probe_error": probe_info.get("probe_error"),
                    },
                )
                candidate.reasons.append("sample-level supplementary candidate discovered from GSM metadata")
                _trace_candidate(candidate, "discovered from sample supplementary metadata")
                if probe_info.get("probe_error"):
                    candidate.warnings.append(f"remote probe failed: {probe_info['probe_error']}")
                    _trace_candidate(candidate, "remote probe failed during sample supplementary discovery")
                candidates.append(candidate)
    return _dedupe_candidates(candidates)


def discover_platform_candidates(gse_id: str) -> list[RemoteCandidate]:
    accession = normalize_accession(gse_id)
    try:
        gse = _load_quick_gse(accession)
    except Exception:
        return []

    metadata = getattr(gse, "metadata", {}) or {}
    gpls = getattr(gse, "gpls", {}) or {}
    platform_ids: set[str] = set(str(key) for key in gpls.keys())
    for gsm in (getattr(gse, "gsms", {}) or {}).values():
        metadata = getattr(gsm, "metadata", {}) or {}
        platform_ids.update(_normalize_values(metadata.get("platform_id")))

    haystack = " ".join(
        [
            *[str(item) for item in _normalize_values(getattr(gse, "metadata", {}).get("type"))],
            *[candidate.remote_url for candidate in discover_series_supplementary_candidates(accession)],
        ]
    ).lower()
    microarray_suspected = any(token in haystack for token in ("microarray", "array", "cel", "id_ref", "_at"))

    candidates: list[RemoteCandidate] = []
    for platform_id in sorted(platform_ids):
        normalized = platform_id.strip().upper()
        if not normalized.startswith("GPL"):
            continue
        prefix = _platform_prefix(normalized)
        base = f"{GEO_FTP_ROOT}/platforms/{prefix}/{normalized}"
        platform_object = gpls.get(normalized)
        candidate = _candidate(
            accession=accession,
            source_level="platform",
            source_accession=normalized,
            remote_url=f"{base}/soft/{normalized}_family.soft.gz",
            file_name=f"{normalized}_family.soft.gz",
            guessed_role="platform_annotation",
            extra={"platform_id": normalized, "microarray_suspected": microarray_suspected},
        )
        candidate.reasons.append("platform candidate derived from GPL/platform_id metadata")
        _trace_candidate(candidate, "discovered from GPL/platform_id metadata")
        if microarray_suspected:
            candidate.reasons.append("microarray/probe-level signals suggest GPL annotation is useful")
            _trace_candidate(candidate, "dataset context suggests probe-level microarray support")
        candidates.append(candidate)
        platform_metadata = getattr(platform_object, "metadata", {}) or {}
        for raw_url in _normalize_values(platform_metadata.get("supplementary_file")):
            probe_info = _probe_remote_candidate_metadata(raw_url)
            file_name = _resolve_remote_file_name(raw_url, probe_info) or f"{normalized}_annotation"
            discovered = _candidate(
                accession=accession,
                source_level="platform",
                source_accession=normalized,
                remote_url=raw_url,
                file_name=file_name,
                guessed_role="platform_annotation",
                size_hint=probe_info.get("size_hint"),
                extra={
                    "platform_id": normalized,
                    "content_type": probe_info.get("content_type"),
                    "probe_error": probe_info.get("probe_error"),
                },
            )
            discovered.reasons.append("platform supplementary candidate discovered from GPL metadata")
            _trace_candidate(discovered, "discovered from GPL supplementary metadata")
            candidates.append(discovered)
    return _dedupe_candidates(candidates)


def discover_external_sources(gse_id: str) -> list[RemoteCandidate]:
    accession = normalize_accession(gse_id)
    try:
        gse = _load_quick_gse(accession)
    except Exception:
        return []

    candidates: list[RemoteCandidate] = []
    relations = getattr(gse, "relations", {}) or {}
    for relation_type, values in relations.items():
        for raw_url in _normalize_values(values):
            file_name = Path(urlparse(raw_url).path).name or f"{accession}_{relation_type.lower()}"
            candidate = _candidate(
                accession=accession,
                source_level="external",
                source_accession=accession,
                remote_url=raw_url,
                file_name=file_name,
                guessed_role="external_raw_source",
                extra={"relation_type": relation_type},
            )
            candidate.reasons.append("external source discovered from series relations")
            _trace_candidate(candidate, "discovered from series relation")
            candidates.append(candidate)

    series_metadata = getattr(gse, "metadata", {}) or {}
    for key, values in series_metadata.items():
        if "relation" not in key.lower() and "supplementary_file" not in key.lower():
            continue
        for raw_url in _extract_urls(_normalize_values(values)):
            if not any(token in raw_url.lower() for token in SRA_HINTS):
                continue
            file_name = Path(urlparse(raw_url).path).name or f"{accession}_{key.lower()}"
            candidate = _candidate(
                accession=accession,
                source_level="external",
                source_accession=accession,
                remote_url=raw_url,
                file_name=file_name,
                guessed_role="external_raw_source",
                extra={"metadata_field": key},
            )
            candidate.reasons.append("external source discovered from series metadata relation")
            _trace_candidate(candidate, "discovered from series metadata relation")
            candidates.append(candidate)

    for gsm_name, gsm in (getattr(gse, "gsms", {}) or {}).items():
        gsm_relations = getattr(gsm, "relations", {}) or {}
        for relation_type, values in gsm_relations.items():
            for raw_url in _normalize_values(values):
                file_name = Path(urlparse(raw_url).path).name or f"{gsm_name}_{relation_type.lower()}"
                candidate = _candidate(
                    accession=accession,
                    source_level="external",
                    source_accession=str(gsm_name),
                    remote_url=raw_url,
                    file_name=file_name,
                    guessed_role="external_raw_source",
                    extra={"relation_type": relation_type, "gsm": str(gsm_name)},
                )
                candidate.reasons.append("external source discovered from GSM relations")
                _trace_candidate(candidate, "discovered from GSM relation")
                candidates.append(candidate)
        gsm_metadata = getattr(gsm, "metadata", {}) or {}
        for key, values in gsm_metadata.items():
            if "relation" not in key.lower() and "supplementary_file" not in key.lower():
                continue
            for raw_url in _extract_urls(_normalize_values(values)):
                if not any(token in raw_url.lower() for token in SRA_HINTS):
                    continue
                file_name = Path(urlparse(raw_url).path).name or f"{gsm_name}_{key.lower()}"
                candidate = _candidate(
                    accession=accession,
                    source_level="external",
                    source_accession=str(gsm_name),
                    remote_url=raw_url,
                    file_name=file_name,
                    guessed_role="external_raw_source",
                    extra={"metadata_field": key, "gsm": str(gsm_name)},
                )
                candidate.reasons.append("external source discovered from GSM metadata relation")
                _trace_candidate(candidate, "discovered from GSM metadata relation")
                candidates.append(candidate)
    return _dedupe_candidates(candidates)


def score_remote_candidate(candidate: RemoteCandidate) -> RemoteCandidate:
    score = 0.0
    name = candidate.file_name.lower()
    url = candidate.remote_url.lower()
    _trace_candidate(candidate, "entered remote_scoring")

    if candidate.required:
        score += 1.0
        candidate.reasons.append("required core record")
        _trace_candidate(candidate, "required core GEO record")

    if candidate.guessed_role in {"family_soft", "miniml", "supplementary_index"}:
        score += 0.95
    elif candidate.guessed_role == "expression_payload":
        score += 0.82
    elif candidate.guessed_role in {"sample_annotation", "clinical_annotation"}:
        score += 0.62
    elif candidate.guessed_role == "platform_annotation":
        score += 0.56
    elif candidate.guessed_role == "archive":
        score += 0.5
    elif candidate.guessed_role == "supporting_doc":
        score += 0.22
    elif candidate.guessed_role == "external_raw_source":
        score += 0.15
        candidate.warnings.append("external source is recorded for downstream handling, not primary direct download")
        _trace_candidate(candidate, "external source retained as reference only")

    if any(token in name or token in url for token in EXPRESSION_HINTS):
        score += 0.26
        candidate.reasons.append("name/url suggests expression payload")
        _trace_candidate(candidate, "name/url suggests expression payload")
    if any(token in name or token in url for token in SAMPLE_HINTS):
        score += 0.12
        candidate.reasons.append("name/url suggests sample annotation")
        _trace_candidate(candidate, "name/url suggests sample annotation")
    if any(token in name or token in url for token in CLINICAL_HINTS):
        score += 0.1
        candidate.reasons.append("name/url suggests clinical annotation")
        _trace_candidate(candidate, "name/url suggests clinical annotation")
    if any(token in name or token in url for token in PLATFORM_HINTS):
        score += 0.1
        candidate.reasons.append("name/url suggests platform annotation")
        _trace_candidate(candidate, "name/url suggests platform annotation")
    if candidate.file_ext in TEXT_PRIORITY_EXTENSIONS:
        score += 0.08
        _trace_candidate(candidate, f"remote probe indicates text-like payload {candidate.file_ext}")
    if candidate.file_ext in ARCHIVE_EXTENSIONS:
        score += 0.06
        candidate.reasons.append("archive retained for later inspection")
        _trace_candidate(candidate, "remote probe indicates archive payload")
    if candidate.size_hint and candidate.size_hint > 1_000_000:
        score += 0.04
        _trace_candidate(candidate, "size hint suggests non-trivial payload")

    candidate.priority_score = round(max(0.0, min(1.5, score)), 3)
    _trace_candidate(candidate, f"remote score={candidate.priority_score}")
    return candidate


def score_remote_candidates(candidates: list[RemoteCandidate]) -> list[RemoteCandidate]:
    return sorted(
        [score_remote_candidate(candidate) for candidate in candidates],
        key=lambda item: (item.required, item.priority_score, item.file_name),
        reverse=True,
    )


def should_probe_sample_level(series_candidates: list[RemoteCandidate], local_validation: dict | None = None) -> bool:
    if local_validation and local_validation.get("has_expression_payload"):
        return False
    if local_validation and local_validation.get("payload_type") not in {None, "none", "metadata_only", "annotation_only", "diff_result_only", "sample_id_only"}:
        return False
    for candidate in series_candidates:
        if candidate.guessed_role == "expression_payload" and candidate.priority_score >= 0.75:
            return False
    return True


def select_remote_download_plan(candidates: list[RemoteCandidate]) -> list[RemoteCandidate]:
    scored = score_remote_candidates(candidates)
    selected: list[RemoteCandidate] = []
    for candidate in scored:
        if candidate.guessed_role == "external_raw_source":
            candidate.should_download = False
            _trace_candidate(candidate, "excluded from download plan because external source is reference-only")
        elif candidate.required:
            candidate.should_download = True
            _trace_candidate(candidate, "accepted into download plan because required core record")
        elif candidate.priority_score >= 0.72:
            candidate.should_download = True
            _trace_candidate(candidate, "accepted into download plan because remote score passed threshold")
        elif candidate.guessed_role in {"sample_annotation", "clinical_annotation", "platform_annotation", "archive"} and candidate.priority_score >= 0.5:
            candidate.should_download = True
            _trace_candidate(candidate, "accepted into download plan as secondary high-value asset")
        elif candidate.guessed_role == "supporting_doc":
            candidate.should_download = False
            _trace_candidate(candidate, "excluded from download plan because supporting document is low priority")
        elif candidate.guessed_role == "supplementary_index":
            candidate.should_download = True
            _trace_candidate(candidate, "accepted into download plan to preserve remote discovery manifest")
        else:
            candidate.should_download = False
            _trace_candidate(candidate, "excluded from download plan because remote score did not justify download")
        selected.append(candidate)
    return selected


def _resolve_destination(output_dir: str, candidate: RemoteCandidate) -> Path:
    root = Path(output_dir).expanduser().resolve()
    if candidate.guessed_role in {"family_soft", "expression_payload", "miniml"} and candidate.source_level == "series":
        target_dir = root / "raw_downloads" / "geo_downloads"
    elif candidate.guessed_role == "platform_annotation" or candidate.source_level == "platform":
        target_dir = root / "raw_downloads" / "metadata_records"
    elif candidate.guessed_role in {"supplementary_index", "external_raw_source"}:
        target_dir = root / "raw_downloads" / "metadata_records"
    else:
        target_dir = root / "raw_downloads" / "supplementary"
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / candidate.file_name


def _download_url_to_path(remote_url: str, destination: Path) -> int:
    remote_url = _normalize_remote_url(remote_url)
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(remote_url, headers={"User-Agent": "codex-geo-downloader"})
    open_kwargs = {"timeout": 60}
    if remote_url.startswith("https://ftp.ncbi.nlm.nih.gov/"):
        open_kwargs["context"] = ssl._create_unverified_context()
    with urlopen(request, **open_kwargs) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)
        return int(response.headers.get("Content-Length", "0")) if response.headers.get("Content-Length") else destination.stat().st_size


def _write_candidate_manifest(candidate: RemoteCandidate, destination: Path) -> int:
    payload = candidate.to_dict()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination.stat().st_size


def check_download_path_consistency(dataset_root: str, transaction_log: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    root = Path(dataset_root).expanduser().resolve()
    raw_download_root = root / "raw_downloads"
    validation_scan_root = root
    organized_root = root / "organized"
    report_root = raw_download_root / "reports"
    transaction_log = transaction_log or []
    download_targets = [str(Path(item.get("final_saved_path", "")).resolve()) for item in transaction_log if item.get("final_saved_path")]
    outside_raw_root = [
        path
        for path in download_targets
        if path and Path(path).exists() and raw_download_root not in Path(path).parents and Path(path) != raw_download_root
    ]
    return {
        "dataset_root": str(root),
        "downloader_writes_to": str(raw_download_root),
        "validation_scans": str(validation_scan_root),
        "organized_reports_to": str(organized_root / "reports"),
        "raw_report_dir": str(report_root),
        "download_targets": sorted(dict.fromkeys(download_targets)),
        "paths_consistent": not outside_raw_root,
        "outside_raw_download_root": sorted(dict.fromkeys(outside_raw_root)),
    }


def _is_raw_download_file(path: Path, dataset_root: Path) -> bool:
    raw_root = dataset_root / "raw_downloads"
    return raw_root in path.parents


def _classify_failed_download(error: Exception) -> str:
    lowered = str(error).lower()
    if "timed out" in lowered or "timeout" in lowered:
        return "timeout"
    if "permission denied" in lowered:
        return "permission denied"
    if "no such file or directory" in lowered:
        return "write failed"
    return "request failed"


def execute_download_plan(plan: list[RemoteCandidate], output_dir: str) -> dict:
    root = Path(output_dir).expanduser().resolve()
    transaction_log: list[dict[str, Any]] = []
    saved_files: list[str] = []
    downloaded_candidates: list[dict[str, Any]] = []
    external_sources: list[str] = []
    errors: list[str] = []
    request_count = 0
    response_success_count = 0
    write_success_count = 0
    scan_range_file_count = 0

    for candidate in plan:
        if not candidate.should_download and candidate.guessed_role != "external_raw_source":
            continue
        destination = _resolve_destination(str(root), candidate)
        started_at = time.time()
        request_count += 1
        try:
            if candidate.guessed_role == "supplementary_index" or candidate.remote_url.startswith("geo://"):
                bytes_received = _write_candidate_manifest(candidate, destination)
                ended_at = time.time()
                response_success_count += 1
                write_success_count += 1
                if destination.exists() and destination.stat().st_size > 0 and _is_raw_download_file(destination, root):
                    scan_range_file_count += 1
                _append_transaction(
                    transaction_log,
                    candidate=candidate,
                    started_at=started_at,
                    ended_at=ended_at,
                    response_status="success",
                    bytes_received=bytes_received,
                    final_path=destination,
                )
                saved_files.append(str(destination))
                _trace_candidate(candidate, "download execution wrote discovery manifest locally")
            elif candidate.guessed_role == "external_raw_source":
                external_sources.append(candidate.remote_url)
                ended_at = time.time()
                _trace_candidate(candidate, "download execution recorded external source without fetching")
                _append_transaction(
                    transaction_log,
                    candidate=candidate,
                    started_at=started_at,
                    ended_at=ended_at,
                    response_status="recorded_only",
                    bytes_received=None,
                    final_path=destination,
                )
            else:
                bytes_received = _download_url_to_path(candidate.remote_url, destination)
                ended_at = time.time()
                response_success_count += 1
                if not destination.exists():
                    errors.append(f"{candidate.file_name}: destination path mismatch")
                    _trace_candidate(candidate, "download execution failed because destination path mismatch")
                    _append_transaction(
                        transaction_log,
                        candidate=candidate,
                        started_at=started_at,
                        ended_at=ended_at,
                        response_status="failed",
                        bytes_received=bytes_received,
                        final_path=destination,
                        error_message="destination path mismatch",
                    )
                    downloaded_candidates.append({**candidate.to_dict(), "final_saved_path": str(destination), "error": "destination path mismatch"})
                    continue
                if destination.stat().st_size <= 0:
                    errors.append(f"{candidate.file_name}: zero-byte file saved")
                    _trace_candidate(candidate, "download execution failed because zero-byte file was saved")
                    _append_transaction(
                        transaction_log,
                        candidate=candidate,
                        started_at=started_at,
                        ended_at=ended_at,
                        response_status="failed",
                        bytes_received=bytes_received,
                        final_path=destination,
                        error_message="zero-byte file saved",
                    )
                    downloaded_candidates.append({**candidate.to_dict(), "final_saved_path": str(destination), "error": "zero-byte file saved"})
                    continue
                write_success_count += 1
                if _is_raw_download_file(destination, root):
                    scan_range_file_count += 1
                _append_transaction(
                    transaction_log,
                    candidate=candidate,
                    started_at=started_at,
                    ended_at=ended_at,
                    response_status="success",
                    bytes_received=bytes_received,
                    final_path=destination,
                )
                if destination.exists() and destination.stat().st_size > 0:
                    saved_files.append(str(destination))
                    _trace_candidate(candidate, "download execution saved non-empty file")
            downloaded_candidates.append({**candidate.to_dict(), "final_saved_path": str(destination)})
        except (HTTPError, URLError, OSError) as exc:
            ended_at = time.time()
            classified_error = _classify_failed_download(exc)
            errors.append(f"{candidate.file_name}: {classified_error}: {exc}")
            _trace_candidate(candidate, f"download execution failed: {classified_error}")
            _append_transaction(
                transaction_log,
                candidate=candidate,
                started_at=started_at,
                ended_at=ended_at,
                response_status="failed",
                bytes_received=None,
                final_path=destination,
                error_message=f"{classified_error}: {exc}",
            )
            downloaded_candidates.append({**candidate.to_dict(), "final_saved_path": str(destination), "error": f"{classified_error}: {exc}"})

    nonempty_saved = [
        path
        for path in saved_files
        if Path(path).exists() and Path(path).stat().st_size > 0 and _is_raw_download_file(Path(path), root)
    ]
    if request_count == 0:
        errors.append("no candidate URLs found")
    if request_count > 0 and not nonempty_saved and not errors:
        errors.append("download finished with no saved files")
    path_consistency = check_download_path_consistency(str(root), transaction_log)
    if not path_consistency["paths_consistent"]:
        errors.append("destination path mismatch")
    return {
        "status": "success" if nonempty_saved else "failed",
        "saved_files": sorted(dict.fromkeys(saved_files)),
        "nonempty_saved_files": sorted(dict.fromkeys(nonempty_saved)),
        "downloaded_candidates": downloaded_candidates,
        "download_transaction_log": transaction_log,
        "external_sources": sorted(dict.fromkeys(external_sources)),
        "errors": sorted(dict.fromkeys(errors)),
        "request_count": request_count,
        "response_success_count": response_success_count,
        "write_success_count": write_success_count,
        "scan_range_file_count": scan_range_file_count,
        "path_consistency": path_consistency,
        "download_success": bool(write_success_count and scan_range_file_count and nonempty_saved),
        "module1_state": derive_module1_state(
            has_candidates=bool(plan),
            has_plan=bool(plan),
            has_downloaded_files=bool(nonempty_saved),
            failed=not bool(nonempty_saved),
            legacy_status="downloaded" if nonempty_saved else "failed",
        ),
    }


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
        raise GeoDownloadError(f"Quick text file is not allowed as formal analysis input: {filepath}")
    LOGGER.info("Loading existing full family SOFT: %s", filepath)
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


def download_full_family_soft(config: DownloadConfig) -> dict[str, Any]:
    """Compatibility wrapper preserved for existing callers."""
    try:
        accession = normalize_accession(config.accession)
    except ValueError as exc:
        raise DownloadModuleError(str(exc)) from exc

    geo_dir = Path(config.geo_dir).expanduser().resolve()
    geo_dir.mkdir(parents=True, exist_ok=True)
    dataset_root = geo_dir.parent.parent if geo_dir.name == "geo_downloads" else geo_dir
    result = download_core_geo_records(accession, str(dataset_root))
    result["family_soft_path"] = str(build_full_family_soft_path(accession, geo_dir))
    return result


def _write_reports(report_root: Path, name: str, payload: Any) -> str:
    report_root.mkdir(parents=True, exist_ok=True)
    path = report_root / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def download_core_geo_records(gse_id: str, output_dir: str) -> dict[str, Any]:
    accession = normalize_accession(gse_id)
    dataset_root = Path(output_dir).expanduser().resolve()
    raw_download_root = dataset_root / "raw_downloads"
    geo_dir = raw_download_root / "geo_downloads"
    metadata_dir = raw_download_root / "metadata_records"
    supplementary_dir = raw_download_root / "supplementary"
    raw_report_dir = raw_download_root / "reports"
    organized_report_dir = dataset_root / "organized" / "reports"
    for path in (geo_dir, metadata_dir, supplementary_dir, raw_report_dir):
        path.mkdir(parents=True, exist_ok=True)

    series_candidates = discover_series_level_candidates(accession)
    series_supplementary = discover_series_supplementary_candidates(accession)
    combined_series = _dedupe_candidates([*series_candidates, *series_supplementary])
    scored_series = score_remote_candidates([candidate for candidate in combined_series])
    sample_candidates = discover_sample_level_candidates(accession) if should_probe_sample_level(scored_series) else []
    platform_candidates = discover_platform_candidates(accession)
    external_candidates = discover_external_sources(accession)

    all_candidates = _dedupe_candidates([*combined_series, *sample_candidates, *platform_candidates, *external_candidates])
    scored_candidates = score_remote_candidates(all_candidates)
    download_plan = select_remote_download_plan(scored_candidates)
    execution = execute_download_plan(download_plan, str(dataset_root))
    family_soft_path = build_full_family_soft_path(accession, geo_dir)
    if family_soft_path.exists():
        post_core_supplementary = discover_series_supplementary_candidates_from_family_soft(accession, str(family_soft_path))
        existing_urls = {item.remote_url for item in download_plan}
        followup_candidates = [item for item in post_core_supplementary if item.remote_url not in existing_urls]
        if followup_candidates:
            followup_scored = score_remote_candidates(followup_candidates)
            followup_plan = select_remote_download_plan(followup_scored)
            followup_execution = execute_download_plan(followup_plan, str(dataset_root))
            execution["saved_files"] = sorted(dict.fromkeys([*execution["saved_files"], *followup_execution["saved_files"]]))
            execution["nonempty_saved_files"] = sorted(dict.fromkeys([*execution["nonempty_saved_files"], *followup_execution["nonempty_saved_files"]]))
            execution["downloaded_candidates"].extend(followup_execution["downloaded_candidates"])
            execution["download_transaction_log"].extend(followup_execution["download_transaction_log"])
            execution["external_sources"] = sorted(dict.fromkeys([*execution["external_sources"], *followup_execution["external_sources"]]))
            execution["errors"] = sorted(dict.fromkeys([*execution["errors"], *followup_execution["errors"]]))
            execution["request_count"] += followup_execution["request_count"]
            execution["response_success_count"] += followup_execution["response_success_count"]
            execution["write_success_count"] += followup_execution["write_success_count"]
            execution["scan_range_file_count"] += followup_execution["scan_range_file_count"]
            execution["download_success"] = execution["download_success"] or followup_execution["download_success"]
            all_candidates = _dedupe_candidates([*all_candidates, *followup_candidates])
            scored_candidates = score_remote_candidates(all_candidates)
            download_plan = select_remote_download_plan(scored_candidates)
            execution["path_consistency"] = check_download_path_consistency(str(dataset_root), execution["download_transaction_log"])

    download_plan_payload = build_download_plan_payload(
        accession,
        str(dataset_root),
        [item.to_dict() for item in download_plan],
    )
    download_receipt_payload = build_download_receipt_payload(
        accession,
        str(dataset_root),
        execution["download_transaction_log"],
        legacy_status="downloaded" if execution["download_success"] else "failed",
    )

    save_json(execution["download_transaction_log"], raw_report_dir / "download_transaction_log.json")
    remote_candidates_path = str(raw_report_dir / "remote_candidates.json")
    scored_candidates_path = str(raw_report_dir / "scored_candidates.json")
    download_plan_path = str(raw_report_dir / "download_plan.json")
    download_receipt_path = str(raw_report_dir / "download_receipt.json")
    save_json({"candidates": [item.to_dict() for item in all_candidates]}, Path(remote_candidates_path))
    save_json({"candidates": [item.to_dict() for item in scored_candidates]}, Path(scored_candidates_path))
    save_json(download_plan_payload, Path(download_plan_path))
    save_json(download_receipt_payload, Path(download_receipt_path))
    transaction_log_path = str(raw_report_dir / "download_transaction_log.json")

    summary = None
    if family_soft_path.exists() and family_soft_path.stat().st_size > 0:
        try:
            gse = parse_existing_full_family_soft(family_soft_path, annotate_gpl=False)
            summary = build_gse_summary(gse)
        except Exception as exc:
            LOGGER.warning("Failed to parse downloaded family.soft for summary: %s", exc)

    core_records = {
        "family_soft": str(family_soft_path) if family_soft_path.exists() else None,
        "series_matrix": next((path for path in execution["saved_files"] if "series_matrix" in Path(path).name.lower()), None),
        "miniml": next((path for path in execution["saved_files"] if Path(path).name.lower().endswith(".xml.tgz")), None),
        "supplementary_index": next((path for path in execution["saved_files"] if Path(path).name.lower().endswith("_series_supplementary_index.json")), None),
        "accession_summary": summary,
    }

    result = {
        "status": "success" if execution["download_success"] else "failed",
        "accession": accession,
        "geo_dir": str(geo_dir),
        "dataset_root": str(dataset_root),
        "raw_download_root": str(raw_download_root),
        "metadata_records_dir": str(metadata_dir),
        "supplementary_dir": str(supplementary_dir),
        "report_dir": str(raw_report_dir),
        "family_soft_path": core_records["family_soft"],
        "summary": summary,
        "error": None if execution["download_success"] else "; ".join(execution["errors"]) if execution["errors"] else "download finished with no saved files",
        "note": "remote discovery, scoring, planning, and execution completed",
        "transaction_log": execution["download_transaction_log"],
        "transaction_log_path": transaction_log_path,
        "saved_raw_files": execution["nonempty_saved_files"],
        "download_success": execution["download_success"],
        "remote_candidates_path": remote_candidates_path,
        "scored_candidates_path": scored_candidates_path,
        "download_plan_path": download_plan_path,
        "download_receipt_path": download_receipt_path,
        "organized_transaction_log_path": None,
        "external_sources": execution["external_sources"],
        "errors": execution["errors"],
        "core_records": core_records,
        "request_count": execution["request_count"],
        "response_success_count": execution["response_success_count"],
        "write_success_count": execution["write_success_count"],
        "scan_range_file_count": execution["scan_range_file_count"],
        "path_consistency": execution["path_consistency"],
        "module1_state": derive_module1_state(
            has_candidates=bool(all_candidates),
            has_plan=bool(download_plan),
            has_downloaded_files=execution["download_success"],
            legacy_status="downloaded" if execution["download_success"] else "failed",
            failed=not execution["download_success"],
        ),
    }
    if execution["download_success"]:
        organized_report_dir.mkdir(parents=True, exist_ok=True)
        result["remote_candidates_path"] = _write_reports(organized_report_dir, "remote_candidates.json", [item.to_dict() for item in all_candidates])
        result["scored_candidates_path"] = _write_reports(organized_report_dir, "scored_candidates.json", [item.to_dict() for item in scored_candidates])
        result["download_plan_path"] = _write_reports(organized_report_dir, "download_plan.json", download_plan_payload)
        result["download_receipt_path"] = _write_reports(organized_report_dir, "download_receipt.json", download_receipt_payload)
        result["organized_transaction_log_path"] = _write_reports(organized_report_dir, "download_transaction_log.json", execution["download_transaction_log"])
    if _should_export_debug_snapshots(dataset_root):
        snapshots = {
            "remote_candidates": [item.to_dict() for item in all_candidates],
            "scored_candidates": [item.to_dict() for item in scored_candidates],
            "download_plan": [item.to_dict() for item in download_plan],
            "transaction_log": execution["download_transaction_log"],
        }
        debug_snapshot_paths = {
            name: _write_debug_snapshot(dataset_root, name, payload) for name, payload in snapshots.items()
        }
        result["debug_snapshot_paths"] = debug_snapshot_paths
    save_json(result, raw_report_dir / "core_download_summary.json")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download GEO datasets via remote discovery and layered planning.")
    parser.add_argument("accession", help="GEO accession, for example GSE12345")
    parser.add_argument("--geo-dir", default="geo_downloads", help="Directory used by GEOparse for cached downloads")
    parser.add_argument("--annotate-gpl", action="store_true", help="Pass annotate_gpl=True into GEOparse.get_GEO during download")
    parser.add_argument("--disable-quick-check", action="store_true", help="Unused compatibility flag retained for CLI stability")
    parser.add_argument("--keep-corrupted-cache", action="store_true", help="Unused compatibility flag retained for CLI stability")
    parser.add_argument("--max-full-retries", type=int, default=2, help="Unused compatibility flag retained for CLI stability")
    parser.add_argument("--load-existing-only", action="store_true", help="Only load a local full family SOFT if it already exists")
    return parser.parse_args()


def main() -> int:
    configure_logging()
    args = parse_args()

    try:
        if args.load_existing_only:
            result = load_existing_full_family_soft(args.accession, args.geo_dir)
        else:
            result = download_core_geo_records(args.accession, args.geo_dir)
    except DownloadModuleError as exc:
        LOGGER.exception("Download module failed")
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2, ensure_ascii=False))
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
