#!/usr/bin/env python3
"""Controlled random GEO recognition audit for BioMedPilot developers."""

from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import ssl
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urljoin
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.bioinformatics.project_readiness import run_project_readiness
from app.bioinformatics.project_recognition import run_project_recognition_for_paths
from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.retrieval.geo_search_service import GeoDatasetResult, GeoSearchService
from app.bioinformatics.services.geo_metadata_profile_service import GeoMetadataProfile, GeoMetadataProfileService


DOWNLOAD_PROFILE_ONLY = "profile_only"
DOWNLOAD_METADATA_ONLY = "metadata_only"
DOWNLOAD_METADATA_PLUS_SMALL = "metadata_plus_small_supplementary"
DOWNLOAD_MODES = (DOWNLOAD_PROFILE_ONLY, DOWNLOAD_METADATA_ONLY, DOWNLOAD_METADATA_PLUS_SMALL)
JSONL_OUTPUT = Path("logs") / "validation" / "geo_random_recognition_audit.jsonl"
DEFAULT_QUERIES = "thyroid cancer,breast cancer,lung cancer,colorectal cancer,melanoma"
RAW_FILE_PATTERNS = (
    ".fastq",
    ".fq",
    ".bam",
    ".cram",
    ".sra",
    ".cel",
    "_raw.tar",
    ".tar",
    ".tar.gz",
    ".tgz",
)
SMALL_SUPPLEMENT_TYPES = {
    "expression_matrix",
    "normalized_expression",
    "raw_count_matrix",
    "sample_metadata",
    "clinical_metadata",
    "platform_annotation",
    "gene_annotation",
}


@dataclass(frozen=True)
class AuditConfig:
    queries: tuple[str, ...]
    per_query: int = 3
    max_total: int = 10
    seed: int = 202605
    download_mode: str = DOWNLOAD_METADATA_ONLY
    max_file_mb: int = 50
    max_total_mb: int = 500
    skip_raw: bool = True
    workdir: Path = field(default_factory=lambda: _default_workdir())
    keep_files: bool = False
    output: Path = Path("docs") / "stage_bio_geo_random_recognition_audit.md"
    timeout: int = 30

    @property
    def max_file_bytes(self) -> int:
        return int(self.max_file_mb) * 1024 * 1024

    @property
    def max_total_bytes(self) -> int:
        return int(self.max_total_mb) * 1024 * 1024

    def to_report_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["workdir"] = str(self.workdir)
        payload["output"] = str(self.output)
        return payload


@dataclass(frozen=True)
class GeoAuditCandidate:
    query: str
    accession: str
    title: str
    summary: str
    query_used: str
    rank_score: float = 0.0
    duplicate_queries: tuple[str, ...] = ()
    search_error: str = ""


@dataclass(frozen=True)
class DownloadDecision:
    file_name: str
    remote_url: str
    asset_type: str
    predicted_type: str
    decision: str
    reason: str
    file_size: int | None = None
    local_path: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class GseAuditResult:
    accession: str
    query: str
    seed: int
    selected: bool = False
    selection_reason: str = ""
    skipped_reason: str = ""
    analysis_potential_level: str = ""
    profile: dict[str, object] = field(default_factory=dict)
    downloaded_files: list[str] = field(default_factory=list)
    download_decisions: list[DownloadDecision] = field(default_factory=list)
    recognition_report: dict[str, object] = field(default_factory=dict)
    readiness_report: dict[str, object] = field(default_factory=dict)
    capability_matrix: dict[str, object] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)
    project_root: str = ""

    def to_jsonl_dict(self, *, run_id: str, config: AuditConfig) -> dict[str, object]:
        metrics = _result_metrics(self)
        return {
            "run_id": run_id,
            "config": config.to_report_dict(),
            "accession": self.accession,
            "query": self.query,
            "seed": self.seed,
            "selected": self.selected,
            "selection_reason": self.selection_reason,
            "skipped_reason": self.skipped_reason,
            "analysis_potential_level": self.analysis_potential_level,
            "download_mode": config.download_mode,
            "downloaded_files": self.downloaded_files,
            "skipped_downloads": [item.to_dict() for item in self.download_decisions if item.decision == "skipped"],
            "download_decisions": [item.to_dict() for item in self.download_decisions],
            "warnings": self.warnings,
            "improvement_suggestions": self.improvement_suggestions,
            **metrics,
        }


def parse_args(argv: list[str] | None = None) -> AuditConfig:
    parser = argparse.ArgumentParser(description="Controlled random GEO recognition audit for BioMedPilot developers.")
    parser.add_argument("--queries", default=DEFAULT_QUERIES, help="Comma-separated disease or tumor search queries.")
    parser.add_argument("--per-query", type=int, default=3)
    parser.add_argument("--max-total", type=int, default=10)
    parser.add_argument("--seed", type=int, default=202605)
    parser.add_argument("--download-mode", choices=DOWNLOAD_MODES, default=DOWNLOAD_METADATA_ONLY)
    parser.add_argument("--max-file-mb", type=int, default=50)
    parser.add_argument("--max-total-mb", type=int, default=500)
    parser.add_argument("--skip-raw", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--workdir", default="")
    parser.add_argument("--keep-files", action="store_true", default=False)
    parser.add_argument("--output", default=str(Path("docs") / "stage_bio_geo_random_recognition_audit.md"))
    parser.add_argument("--timeout", type=int, default=15)
    args = parser.parse_args(argv)
    queries = tuple(query.strip() for query in str(args.queries).split(",") if query.strip())
    if not queries:
        parser.error("--queries must contain at least one query")
    return AuditConfig(
        queries=queries,
        per_query=max(1, int(args.per_query)),
        max_total=max(1, int(args.max_total)),
        seed=int(args.seed),
        download_mode=str(args.download_mode),
        max_file_mb=max(1, int(args.max_file_mb)),
        max_total_mb=max(1, int(args.max_total_mb)),
        skip_raw=bool(args.skip_raw),
        workdir=Path(args.workdir).expanduser().resolve() if args.workdir else _default_workdir(),
        keep_files=bool(args.keep_files),
        output=Path(args.output),
        timeout=max(1, int(args.timeout)),
    )


def collect_geo_candidates(
    config: AuditConfig,
    *,
    search_service: GeoSearchService | None = None,
) -> tuple[list[GeoAuditCandidate], list[GseAuditResult]]:
    service = search_service or GeoSearchService()
    by_accession: dict[str, GeoAuditCandidate] = {}
    skipped: list[GseAuditResult] = []
    pool_size = max(20, config.per_query * 6)
    for query in config.queries:
        try:
            response = service.search(query, max_results=pool_size, include_supplemental=True)
        except Exception as exc:
            skipped.append(_skipped_result(query=query, accession="", seed=config.seed, reason=f"search_exception:{exc}"))
            continue
        if response.error_message:
            skipped.append(_skipped_result(query=query, accession="", seed=config.seed, reason=f"search_error:{response.error_message}"))
        if not response.results:
            skipped.append(_skipped_result(query=query, accession="", seed=config.seed, reason="search_returned_no_results"))
            continue
        for item in response.results:
            candidate = _candidate_from_result(query, item)
            existing = by_accession.get(candidate.accession)
            if existing is None:
                by_accession[candidate.accession] = candidate
            else:
                merged = tuple(dict.fromkeys([*existing.duplicate_queries, query]))
                by_accession[candidate.accession] = GeoAuditCandidate(
                    query=existing.query,
                    accession=existing.accession,
                    title=existing.title,
                    summary=existing.summary,
                    query_used=existing.query_used,
                    rank_score=max(existing.rank_score, candidate.rank_score),
                    duplicate_queries=merged,
                )
    return list(by_accession.values()), skipped


def build_preselection_profiles(
    candidates: list[GeoAuditCandidate],
    config: AuditConfig,
    *,
    fetcher: Callable[[str, int], bytes] | None = None,
    directory_lister: Callable[[str, int], list[dict[str, object]]] | None = None,
    include_remote_assets: bool = False,
) -> tuple[dict[str, GeoMetadataProfile], dict[str, list[DownloadDecision]], list[GseAuditResult]]:
    service = GeoMetadataProfileService()
    profiles: dict[str, GeoMetadataProfile] = {}
    decisions: dict[str, list[DownloadDecision]] = {}
    skipped: list[GseAuditResult] = []
    for candidate in candidates:
        try:
            quick_metadata, quick_assets = fetch_geo_quick_metadata(candidate.accession, config, fetcher=fetcher)
            remote_assets = discover_remote_assets(candidate.accession, config, directory_lister=directory_lister) if include_remote_assets else []
            assets = _asset_entries_from_quick_and_remote(quick_assets, remote_assets)
            metadata = {
                "title_en": candidate.title,
                "summary_en": candidate.summary,
                "query_used": candidate.query_used,
                **quick_metadata,
            }
            profile = service.build_profile(
                accession=candidate.accession,
                candidate_metadata=metadata,
                asset_manifest={"assets": assets},
            )
            profiles[candidate.accession] = profile
            decisions[candidate.accession] = plan_downloads(profile, config)
        except Exception as exc:
            skipped.append(_skipped_result(query=candidate.query, accession=candidate.accession, seed=config.seed, reason=f"profile_failed:{exc}"))
    return profiles, decisions, skipped


def build_download_profile(
    candidate: GeoAuditCandidate,
    config: AuditConfig,
    *,
    fetcher: Callable[[str, int], bytes] | None = None,
    directory_lister: Callable[[str, int], list[dict[str, object]]] | None = None,
) -> tuple[GeoMetadataProfile, list[DownloadDecision]]:
    profiles, decisions, skipped = build_preselection_profiles(
        [candidate],
        config,
        fetcher=fetcher,
        directory_lister=directory_lister,
        include_remote_assets=True,
    )
    profile = profiles.get(candidate.accession)
    if profile is None:
        reason = skipped[0].skipped_reason if skipped else "download_profile_failed"
        raise RuntimeError(reason)
    return profile, decisions.get(candidate.accession, [])


def limit_candidates_for_profile(candidates: list[GeoAuditCandidate], config: AuditConfig) -> tuple[list[GeoAuditCandidate], list[GseAuditResult]]:
    rng = random.Random(config.seed)
    by_query: dict[str, list[GeoAuditCandidate]] = defaultdict(list)
    for candidate in candidates:
        by_query[candidate.query].append(candidate)
    profile_budget = max(config.per_query * 3, 5)
    selected: list[GeoAuditCandidate] = []
    skipped: list[GseAuditResult] = []
    selected_keys: set[str] = set()
    for query in config.queries:
        values = by_query.get(query, [])
        pinned = values[: min(len(values), config.per_query * 2)]
        remainder = [item for item in values if item not in pinned]
        rng.shuffle(remainder)
        query_profiled = [*pinned, *remainder[: max(0, profile_budget - len(pinned))]]
        for item in query_profiled:
            if item.accession not in selected_keys:
                selected.append(item)
                selected_keys.add(item.accession)
        for item in values:
            if item.accession not in selected_keys:
                skipped.append(_skipped_result(query=item.query, accession=item.accession, seed=config.seed, reason="not_profiled_by_seed_budget"))
    return selected, skipped


def stratified_sample_candidates(
    candidates: list[GeoAuditCandidate],
    profiles: dict[str, GeoMetadataProfile],
    config: AuditConfig,
) -> tuple[list[GeoAuditCandidate], list[GseAuditResult]]:
    rng = random.Random(config.seed)
    by_query: dict[str, list[GeoAuditCandidate]] = defaultdict(list)
    for candidate in candidates:
        if candidate.accession in profiles:
            by_query[candidate.query].append(candidate)
    selected: list[GeoAuditCandidate] = []
    skipped: list[GseAuditResult] = []
    selected_keys: set[str] = set()
    for query in config.queries:
        query_candidates = by_query.get(query, [])
        strata = {
            "high": [item for item in query_candidates if profiles[item.accession].analysis_potential_level == "高"],
            "medium": [item for item in query_candidates if profiles[item.accession].analysis_potential_level == "中"],
            "low": [item for item in query_candidates if profiles[item.accession].analysis_potential_level in {"低", "不建议"}],
        }
        for values in strata.values():
            rng.shuffle(values)
        per_query_selected: list[GeoAuditCandidate] = []
        for label in ("high", "medium", "low"):
            if len(per_query_selected) >= config.per_query:
                break
            while strata[label]:
                item = strata[label].pop(0)
                if item.accession not in selected_keys:
                    per_query_selected.append(item)
                    selected_keys.add(item.accession)
                    break
        remainder = [item for item in query_candidates if item.accession not in selected_keys]
        rng.shuffle(remainder)
        for item in remainder:
            if len(per_query_selected) >= config.per_query:
                break
            per_query_selected.append(item)
            selected_keys.add(item.accession)
        for item in per_query_selected:
            if len(selected) < config.max_total:
                selected.append(item)
            else:
                skipped.append(_skipped_result(query=item.query, accession=item.accession, seed=config.seed, reason="max_total_reached"))
        for item in query_candidates:
            if item.accession not in selected_keys:
                skipped.append(_skipped_result(query=item.query, accession=item.accession, seed=config.seed, reason="not_selected_by_seed_or_strata"))
    return selected[: config.max_total], skipped


def download_selected_assets(
    candidate: GeoAuditCandidate,
    profile: GeoMetadataProfile,
    planned: list[DownloadDecision],
    project_root: Path,
    config: AuditConfig,
    *,
    fetcher: Callable[[str, int], bytes] | None = None,
    total_bytes_used: int = 0,
) -> tuple[list[str], list[DownloadDecision], int, list[str]]:
    if config.download_mode == DOWNLOAD_PROFILE_ONLY:
        return [], [DownloadDecision("profile_only", "", "none", "none", "skipped", "profile_only does not download files")], total_bytes_used, []
    target = project_root / "raw_data" / "geo" / candidate.accession
    target.mkdir(parents=True, exist_ok=True)
    downloaded: list[str] = []
    resolved: list[DownloadDecision] = []
    warnings: list[str] = []
    for decision in planned:
        if decision.decision != "download":
            resolved.append(decision)
            continue
        if total_bytes_used >= config.max_total_bytes:
            resolved.append(_replace_decision(decision, decision="skipped", reason="max_total_mb exceeded"))
            continue
        if decision.file_size is not None and total_bytes_used + decision.file_size > config.max_total_bytes:
            resolved.append(_replace_decision(decision, decision="skipped", reason="max_total_mb would be exceeded"))
            continue
        try:
            local_path, bytes_downloaded = safe_download_file(decision.remote_url, target / decision.asset_type, config, fetcher=fetcher)
        except Exception as exc:
            warnings.append(f"{decision.file_name}: {exc}")
            resolved.append(_replace_decision(decision, decision="skipped", reason=f"download_failed:{exc}"))
            continue
        total_bytes_used += bytes_downloaded
        downloaded.append(str(local_path))
        resolved.append(_replace_decision(decision, decision="downloaded", reason="downloaded", local_path=str(local_path), file_size=bytes_downloaded))
    return downloaded, resolved, total_bytes_used, warnings


def run_recognition_audit(
    candidate: GeoAuditCandidate,
    profile: GeoMetadataProfile,
    downloaded_files: list[str],
    project_parent: Path,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], str]:
    summary = create_bioinformatics_project(f"geo-audit-{candidate.accession}", project_parent)
    project_root = summary.project_root
    recognition = run_project_recognition_for_paths(project_root, [Path(path) for path in downloaded_files], skipped_unselected_count=0)
    readiness = run_project_readiness(project_root)
    readiness_report = readiness.get("readiness_report") if isinstance(readiness, dict) else {}
    capability_matrix = readiness.get("capability_matrix") if isinstance(readiness, dict) else {}
    return recognition, readiness_report if isinstance(readiness_report, dict) else {}, capability_matrix if isinstance(capability_matrix, dict) else {}, str(project_root)


def rebuild_profile_with_downloaded_metadata(
    candidate: GeoAuditCandidate,
    profile: GeoMetadataProfile,
    downloaded_files: list[str],
) -> GeoMetadataProfile:
    family_path = _first_existing_path(downloaded_files, ("family.soft", "family.soft.gz"))
    matrix_path = _first_existing_path(downloaded_files, ("series_matrix",))
    if family_path is None and matrix_path is None:
        return profile
    metadata = {
        "title_en": profile.title or candidate.title,
        "summary_en": profile.summary or candidate.summary,
        "overall_design_en": profile.overall_design,
        "organism": profile.organism,
        "platform_accessions": list(profile.platform_ids),
        "query_used": candidate.query_used,
    }
    asset_manifest = {"assets": [item.to_dict() for item in profile.supplementary_file_preview]}
    return GeoMetadataProfileService().build_profile(
        accession=candidate.accession,
        candidate_metadata=metadata,
        asset_manifest=asset_manifest,
        family_soft_path=family_path,
        series_matrix_path=matrix_path,
    )


def run_audit(
    config: AuditConfig,
    *,
    search_service: GeoSearchService | None = None,
    fetcher: Callable[[str, int], bytes] | None = None,
    directory_lister: Callable[[str, int], list[dict[str, object]]] | None = None,
) -> list[GseAuditResult]:
    config.workdir.mkdir(parents=True, exist_ok=True)
    run_results: list[GseAuditResult] = []
    total_downloaded = 0
    try:
        candidates, skipped_search = collect_geo_candidates(config, search_service=search_service)
        profile_candidates, skipped_budget = limit_candidates_for_profile(candidates, config)
        profiles, planned_decisions, skipped_profiles = build_preselection_profiles(profile_candidates, config, fetcher=fetcher, directory_lister=directory_lister)
        selected, skipped_sampling = stratified_sample_candidates(profile_candidates, profiles, config)
        run_results.extend(skipped_search)
        run_results.extend(skipped_budget)
        run_results.extend(skipped_profiles)
        run_results.extend(skipped_sampling)
        for candidate in selected:
            profile = profiles[candidate.accession]
            planned = planned_decisions.get(candidate.accession, [])
            result = GseAuditResult(
                accession=candidate.accession,
                query=candidate.query,
                seed=config.seed,
                selected=True,
                selection_reason=_selection_reason(profile),
                analysis_potential_level=profile.analysis_potential_level,
                profile=profile.to_dict(),
            )
            try:
                profile, planned = build_download_profile(candidate, config, fetcher=fetcher, directory_lister=directory_lister)
                result.analysis_potential_level = profile.analysis_potential_level
                result.profile = profile.to_dict()
            except Exception as exc:
                result.warnings.append(f"download_profile_failed:{exc}")
            downloaded, decisions, total_downloaded, download_warnings = download_selected_assets(
                candidate,
                profile,
                planned,
                config.workdir,
                config,
                fetcher=fetcher,
                total_bytes_used=total_downloaded,
            )
            result.downloaded_files = downloaded
            result.download_decisions = decisions
            result.warnings.extend(download_warnings)
            try:
                profile = rebuild_profile_with_downloaded_metadata(candidate, profile, downloaded)
                result.analysis_potential_level = profile.analysis_potential_level
                result.profile = profile.to_dict()
            except Exception as exc:
                result.warnings.append(f"downloaded_metadata_profile_failed:{exc}")
            try:
                recognition, readiness, matrix, project_root = run_recognition_audit(candidate, profile, downloaded, config.workdir / "projects")
                result.recognition_report = recognition
                result.readiness_report = readiness
                result.capability_matrix = matrix
                result.project_root = project_root
            except Exception as exc:
                result.warnings.append(f"recognition_failed:{exc}")
            result.improvement_suggestions = improvement_suggestions(result)
            run_results.append(result)
        return run_results
    finally:
        if not config.keep_files:
            shutil.rmtree(config.workdir, ignore_errors=True)


def fetch_geo_quick_metadata(
    accession: str,
    config: AuditConfig,
    *,
    fetcher: Callable[[str, int], bytes] | None = None,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}&targ=self&form=text&view=quick"
    text = _fetch_text(url, config.timeout, fetcher=fetcher)
    def values(key: str) -> list[str]:
        return [item.strip().strip('"') for item in re.findall(rf"^!{re.escape(key)} = (.*)", text, flags=re.MULTILINE)]
    metadata = {
        "title_en": _first(values("Series_title")),
        "summary_en": " ".join(values("Series_summary")),
        "overall_design_en": " ".join(values("Series_overall_design")),
        "platform_accessions": values("Series_platform_id"),
        "organism": _first(values("Series_sample_organism")) or _first(values("Series_organism")),
    }
    assets = [
        {
            "asset_type": "supplementary_file",
            "file_name": Path(url).name or url.rstrip("/").rsplit("/", 1)[-1],
            "remote_url": url,
            "status": "remote_discovered",
            "size_bytes": None,
        }
        for url in values("Series_supplementary_file")
    ]
    return metadata, assets


def discover_remote_assets(
    accession: str,
    config: AuditConfig,
    *,
    directory_lister: Callable[[str, int], list[dict[str, object]]] | None = None,
) -> list[dict[str, object]]:
    assets: list[dict[str, object]] = [
        {
            "asset_type": "family_soft",
            "file_name": f"{accession}_family.soft.gz",
            "remote_url": _geo_family_soft_url(accession),
            "status": "remote_discovered",
            "size_bytes": remote_file_size(_geo_family_soft_url(accession), config.timeout),
        }
    ]
    for url, asset_type in ((_geo_matrix_dir_url(accession), "series_matrix"), (_geo_supp_dir_url(accession), "supplementary_file")):
        try:
            entries = directory_lister(url, config.timeout) if directory_lister is not None else list_remote_directory(url, config.timeout)
        except Exception:
            continue
        for entry in entries:
            file_name = str(entry.get("file_name") or "")
            if asset_type == "series_matrix" and "series_matrix" not in file_name.lower():
                continue
            assets.append(
                {
                    "asset_type": asset_type,
                    "file_name": file_name,
                    "remote_url": str(entry.get("remote_url") or ""),
                    "status": "remote_discovered",
                    "size_bytes": _int_or_none(entry.get("size_bytes")),
                }
            )
    return assets


def list_remote_directory(url: str, timeout: int) -> list[dict[str, object]]:
    html = _fetch_text(url, timeout)
    entries: list[dict[str, object]] = []
    for href in re.findall(r'href="([^"]+)"', html):
        if href.startswith("?") or href.startswith("/") or href in {"../", "./"}:
            continue
        file_name = unquote(href.rstrip("/").rsplit("/", 1)[-1])
        if not file_name:
            continue
        remote_url = urljoin(url if url.endswith("/") else url + "/", href)
        entries.append({"file_name": file_name, "remote_url": remote_url, "size_bytes": remote_file_size(remote_url, timeout)})
    return entries


def plan_downloads(profile: GeoMetadataProfile, config: AuditConfig) -> list[DownloadDecision]:
    if config.download_mode == DOWNLOAD_PROFILE_ONLY:
        return [DownloadDecision("profile_only", "", "none", "none", "skipped", "profile_only does not download files")]
    decisions: list[DownloadDecision] = []
    for item in profile.supplementary_file_preview:
        file_name = item.file_name
        remote_url = item.remote_url
        asset_type = item.asset_type or "supplementary_file"
        predicted_type = item.predicted_type
        if asset_type == "family_soft" or asset_type == "series_matrix":
            decisions.append(_decision_for_asset(file_name, remote_url, asset_type, predicted_type, item.file_size, config, force_metadata=True))
            continue
        if config.download_mode != DOWNLOAD_METADATA_PLUS_SMALL:
            decisions.append(DownloadDecision(file_name, remote_url, asset_type, predicted_type, "skipped", "metadata_only skips supplementary files", item.file_size))
            continue
        decisions.append(_decision_for_asset(file_name, remote_url, asset_type, predicted_type, item.file_size, config, force_metadata=False))
    return _dedupe_download_decisions(decisions)


def safe_download_file(
    remote_url: str,
    target_dir: Path,
    config: AuditConfig,
    *,
    fetcher: Callable[[str, int], bytes] | None = None,
) -> tuple[Path, int]:
    if not _safe_geo_url(remote_url):
        raise ValueError("unsafe_non_geo_url")
    target_dir.mkdir(parents=True, exist_ok=True)
    file_name = Path(unquote(remote_url.rstrip("/").rsplit("/", 1)[-1])).name
    if not file_name:
        raise ValueError("missing_remote_file_name")
    size = remote_file_size(remote_url, config.timeout)
    if size is not None and size > config.max_file_bytes:
        raise ValueError("max_file_mb exceeded")
    target = target_dir / file_name
    if fetcher is not None:
        payload = fetcher(remote_url, config.timeout)
        if len(payload) > config.max_file_bytes:
            raise ValueError("max_file_mb exceeded")
        target.write_bytes(payload)
        return target.resolve(), len(payload)
    bytes_downloaded = 0
    partial = target.with_suffix(target.suffix + ".part")
    try:
        with urlopen(Request(remote_url, headers={"User-Agent": "BioMedPilot GEO audit"}), timeout=config.timeout, context=_ssl_context()) as response:  # nosec B310 - guarded GEO URL.
            with partial.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    bytes_downloaded += len(chunk)
                    if bytes_downloaded > config.max_file_bytes:
                        raise ValueError("max_file_mb exceeded while downloading")
                    handle.write(chunk)
        partial.replace(target)
    except Exception:
        try:
            partial.unlink()
        except OSError:
            pass
        raise
    return target.resolve(), bytes_downloaded


def write_markdown_report(results: list[GseAuditResult], config: AuditConfig, output: Path) -> Path:
    output = output if output.is_absolute() else REPO_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    selected = [item for item in results if item.selected]
    stats = _overall_stats(selected)
    failures = _failure_counts(selected)
    lines = [
        "# Stage Bio GEO Random Recognition Audit",
        "",
        "## 测试配置",
        "",
        f"- seed: `{config.seed}`",
        f"- queries: `{', '.join(config.queries)}`",
        f"- per-query: `{config.per_query}`",
        f"- max-total: `{config.max_total}`",
        f"- download-mode: `{config.download_mode}`",
        f"- max-file-mb: `{config.max_file_mb}`",
        f"- max-total-mb: `{config.max_total_mb}`",
        f"- keep-files: `{config.keep_files}`",
        f"- workdir: `{config.workdir}`" if config.keep_files else "- workdir: cleaned after run",
        "",
        "## 总体统计",
        "",
        *[f"- {key}: {value}" for key, value in stats.items()],
        "",
        "## 每个 GSE 结果表",
        "",
        "| GSE | query | 推荐等级 | 样本数 | 候选分组 | 表达矩阵 | 样本注释 | 基因/平台注释 | 是否可继续 | 主要失败原因 |",
        "|---|---|---|---:|---|---|---|---|---|---|",
    ]
    for item in selected:
        metrics = _result_metrics(item)
        lines.append(
            "| "
            + " | ".join(
                [
                    item.accession,
                    item.query,
                    item.analysis_potential_level or "-",
                    str(metrics["metadata_sample_count"] or metrics["geo_sample_count"] or 0),
                    _compact_group(metrics),
                    _yes_no(metrics["expression_matrix_detected"]),
                    _yes_no(metrics["sample_metadata_detected"]),
                    _yes_no(metrics["gene_or_platform_annotation_detected"]),
                    _yes_no(_readiness_can_continue(item)),
                    _first_failure(item),
                ]
            )
            + " |"
        )
    lines.extend(["", "## 错误类型归纳", ""])
    if failures:
        lines.extend(f"- {key}: {value}" for key, value in failures.most_common())
    else:
        lines.append("- 未发现阻断性错误。")
    lines.extend(["", "## 人工复核摘要", ""])
    for item in selected:
        lines.extend(_manual_review_lines(item))
    lines.extend(["", "## 下一步改进建议", ""])
    suggestions = Counter(suggestion for item in selected for suggestion in item.improvement_suggestions)
    if suggestions:
        lines.extend(f"- {text}: {count}" for text, count in suggestions.most_common())
    else:
        lines.append("- 当前小规模样本未产生明确改进建议。")
    skipped = [item for item in results if not item.selected]
    if skipped:
        lines.extend(["", "## Skipped GSE", ""])
        for item in skipped[:80]:
            lines.append(f"- {item.accession or '(query)'} / {item.query}: {item.skipped_reason}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def write_jsonl_results(results: list[GseAuditResult], config: AuditConfig, *, run_id: str) -> Path:
    path = REPO_ROOT / JSONL_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in results:
            handle.write(json.dumps(item.to_jsonl_dict(run_id=run_id, config=config), ensure_ascii=False, default=str) + "\n")
    return path


def improvement_suggestions(result: GseAuditResult) -> list[str]:
    metrics = _result_metrics(result)
    suggestions: list[str] = []
    if not metrics["expression_matrix_detected"]:
        suggestions.append("project_recognition: improve expression matrix detection or supplementary prioritization")
    if not metrics["sample_metadata_detected"]:
        suggestions.append("geo_metadata_profile/group_preview: improve sample metadata parsing")
    if not metrics["candidate_comparison_count"]:
        suggestions.append("geo_metadata_profile: improve sample-level group evidence extraction")
    if metrics["blocked_by_sample_id_mismatch"]:
        suggestions.append("comparison_config/readiness: improve sample ID matching diagnostics")
    if any("raw" in decision.reason.lower() for decision in result.download_decisions if decision.decision == "skipped"):
        suggestions.append("geo_download: keep raw files opt-in and show safer processed alternatives")
    return suggestions


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    run_id = datetime.now(timezone.utc).strftime("geo-audit-%Y%m%dT%H%M%SZ")
    results = run_audit(config)
    if not any(item.selected for item in results):
        write_markdown_report(results, config, config.output)
        write_jsonl_results(results, config, run_id=run_id)
        print("No GSE datasets were selected; see audit report for search/profile failures.", file=sys.stderr)
        return 1
    md_path = write_markdown_report(results, config, config.output)
    jsonl_path = write_jsonl_results(results, config, run_id=run_id)
    print(f"markdown_report={md_path}")
    print(f"jsonl_results={jsonl_path}")
    print(f"selected_gse={sum(1 for item in results if item.selected)}")
    return 0


def remote_file_size(url: str, timeout: int) -> int | None:
    if not _safe_geo_url(url):
        return None
    try:
        with urlopen(Request(url, method="HEAD", headers={"User-Agent": "BioMedPilot GEO audit"}), timeout=timeout, context=_ssl_context()) as response:  # nosec B310
            value = response.headers.get("Content-Length")
            return int(value) if value and value.isdigit() else None
    except Exception:
        return None


def _fetch_text(url: str, timeout: int, *, fetcher: Callable[[str, int], bytes] | None = None) -> str:
    data = fetcher(url, timeout) if fetcher is not None else urlopen(Request(url, headers={"User-Agent": "BioMedPilot GEO audit"}), timeout=timeout, context=_ssl_context()).read()  # nosec B310
    return data.decode("utf-8", "ignore")


def _candidate_from_result(query: str, item: GeoDatasetResult) -> GeoAuditCandidate:
    return GeoAuditCandidate(query=query, accession=item.accession.upper(), title=item.title, summary=item.summary, query_used=item.query_used, rank_score=item.rank_score)


def _asset_entries_from_quick_and_remote(quick_assets: list[dict[str, object]], remote_assets: list[dict[str, object]]) -> list[dict[str, object]]:
    by_key: dict[tuple[str, str], dict[str, object]] = {}
    for item in [*quick_assets, *remote_assets]:
        key = (str(item.get("asset_type") or ""), str(item.get("file_name") or item.get("remote_url") or ""))
        if key[1]:
            by_key[key] = {**by_key.get(key, {}), **item}
    return list(by_key.values())


def _decision_for_asset(file_name: str, remote_url: str, asset_type: str, predicted_type: str, file_size: int | None, config: AuditConfig, *, force_metadata: bool) -> DownloadDecision:
    if not remote_url or not _safe_geo_url(remote_url):
        return DownloadDecision(file_name, remote_url, asset_type, predicted_type, "skipped", "unsafe or missing GEO URL", file_size)
    if config.skip_raw and _is_raw_file(file_name, predicted_type):
        return DownloadDecision(file_name, remote_url, asset_type, predicted_type, "skipped", "raw sequencing/CEL/archive files are skipped", file_size)
    if file_size is not None and file_size > config.max_file_bytes:
        return DownloadDecision(file_name, remote_url, asset_type, predicted_type, "skipped", "max_file_mb exceeded", file_size)
    if force_metadata:
        return DownloadDecision(file_name, remote_url, asset_type, predicted_type, "download", "metadata download mode", file_size)
    if predicted_type not in SMALL_SUPPLEMENT_TYPES:
        return DownloadDecision(file_name, remote_url, asset_type, predicted_type, "skipped", "supplementary type not in small candidate allowlist", file_size)
    return DownloadDecision(file_name, remote_url, asset_type, predicted_type, "download", "small supplementary candidate", file_size)


def _dedupe_download_decisions(decisions: list[DownloadDecision]) -> list[DownloadDecision]:
    seen: set[tuple[str, str]] = set()
    deduped: list[DownloadDecision] = []
    for item in decisions:
        key = (item.remote_url, item.file_name)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _replace_decision(item: DownloadDecision, **updates: object) -> DownloadDecision:
    payload = item.to_dict()
    payload.update(updates)
    return DownloadDecision(**payload)  # type: ignore[arg-type]


def _result_metrics(result: GseAuditResult) -> dict[str, object]:
    profile = result.profile or {}
    recognition = result.recognition_report or {}
    readiness = result.readiness_report or {}
    files = [item for item in recognition.get("files", []) or [] if isinstance(item, dict)]
    roles = {
        str(role)
        for record in files
        for role in [record.get("recognized_type"), *(record.get("recognized_roles", []) or [])]
        if role
    }
    group_preview = recognition.get("group_preview") if isinstance(recognition.get("group_preview"), dict) else {}
    comparisons = profile.get("candidate_comparisons") if isinstance(profile.get("candidate_comparisons"), list) else []
    first_comparison = comparisons[0] if comparisons and isinstance(comparisons[0], dict) else {}
    return {
        "title_found": bool(profile.get("title")),
        "summary_found": bool(profile.get("summary")),
        "overall_design_found": bool(profile.get("overall_design")),
        "geo_sample_count": profile.get("geo_sample_count") or 0,
        "metadata_sample_count": profile.get("metadata_sample_count") or 0,
        "expression_sample_count": profile.get("expression_sample_count") or _group_value(group_preview, "expression_sample_count"),
        "matched_sample_count": profile.get("matched_sample_count") or _group_value(group_preview, "matched_sample_count"),
        "sample_metadata_detected": "sample_metadata" in roles,
        "expression_matrix_detected": bool(roles & {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix"}),
        "gene_or_platform_annotation_detected": bool(roles & {"gene_annotation", "platform_annotation", "platform_reference_hint"}),
        "clinical_annotation_detected": bool(roles & {"clinical_metadata", "survival_metadata"}),
        "candidate_comparison_count": len(comparisons),
        "group_count": int(group_preview.get("group_count") or len(first_comparison.get("group_sizes", {}) or {}) or 0) if isinstance(group_preview, dict) else 0,
        "group_sizes": group_preview.get("group_sizes") if isinstance(group_preview, dict) and group_preview.get("group_sizes") else first_comparison.get("group_sizes", {}),
        "confidence": group_preview.get("confidence") if isinstance(group_preview, dict) and group_preview.get("confidence") else first_comparison.get("confidence", ""),
        "requires_user_confirmation": bool(first_comparison.get("requires_user_confirmation", True)) if first_comparison else False,
        "readiness_status": readiness.get("overall_status", ""),
        "blocked_by_missing_expression": "expression_matrix" in _missing_inputs(result) or not bool(roles & {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix"}),
        "blocked_by_sample_id_mismatch": readiness.get("comparison_group_status") == "confirmed_sample_mismatch",
        "blocked_by_unsupported_modality": profile.get("analysis_potential_level") == "不建议",
        "possible_misclassification": _possible_misclassification(result, roles),
    }


def _missing_inputs(result: GseAuditResult) -> set[str]:
    values: set[str] = set()
    for row in (result.capability_matrix or {}).get("rows", []) or []:
        if isinstance(row, dict):
            values.update(str(item) for item in row.get("missing_inputs", []) or [])
    return values


def _possible_misclassification(result: GseAuditResult, roles: set[str]) -> bool:
    if result.downloaded_files and not roles:
        return True
    if any(path.lower().endswith((".txt", ".tsv", ".csv", ".gz")) for path in result.downloaded_files) and "unknown" in roles:
        return True
    return False


def _overall_stats(results: list[GseAuditResult]) -> dict[str, int]:
    return {
        "测试 GSE 数": len(results),
        "profile 成功数": sum(1 for item in results if item.profile),
        "下载成功数": sum(1 for item in results if item.downloaded_files),
        "expression matrix 识别成功数": sum(1 for item in results if _result_metrics(item)["expression_matrix_detected"]),
        "sample metadata 识别成功数": sum(1 for item in results if _result_metrics(item)["sample_metadata_detected"]),
        "candidate comparisons 成功数": sum(1 for item in results if _result_metrics(item)["candidate_comparison_count"]),
        "group preview 成功数": sum(1 for item in results if _result_metrics(item)["group_count"]),
        "readiness 可继续数": sum(1 for item in results if _readiness_can_continue(item)),
    }


def _failure_counts(results: list[GseAuditResult]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for item in results:
        metrics = _result_metrics(item)
        if not metrics["expression_matrix_detected"]:
            counter["缺表达矩阵或表达矩阵未识别"] += 1
        if not metrics["sample_metadata_detected"]:
            counter["样本注释缺失或未识别"] += 1
        if not metrics["candidate_comparison_count"]:
            counter["未生成候选分组"] += 1
        if metrics["blocked_by_sample_id_mismatch"]:
            counter["表达矩阵列名与 GSM 不匹配"] += 1
        if metrics["blocked_by_unsupported_modality"]:
            counter["数据类型不支持或不建议"] += 1
        for decision in item.download_decisions:
            if decision.decision == "skipped" and "raw" in decision.reason.lower():
                counter["raw 数据不可直接分析"] += 1
            elif decision.decision == "skipped" and "max_file" in decision.reason:
                counter["supplementary 文件过大"] += 1
    return counter


def _manual_review_lines(item: GseAuditResult) -> list[str]:
    profile = item.profile or {}
    samples = profile.get("sample_records") if isinstance(profile.get("sample_records"), list) else []
    comparisons = profile.get("candidate_comparisons") if isinstance(profile.get("candidate_comparisons"), list) else []
    files = [record for record in (item.recognition_report or {}).get("files", []) or [] if isinstance(record, dict)]
    return [
        f"### {item.accession}",
        "",
        f"- query: {item.query}",
        f"- title: {profile.get('title') or '未记录'}",
        f"- overall design: {_short_text(profile.get('overall_design'))}",
        f"- sample title examples: {_sample_field_examples(samples, 'sample_title')}",
        f"- characteristics examples: {_characteristics_examples(samples)}",
        f"- software candidate groups: {_comparison_examples(comparisons)}",
        f"- downloaded files: {', '.join(Path(path).name for path in item.downloaded_files) or '无'}",
        f"- recognized file types: {', '.join(str(record.get('recognized_type')) for record in files) or '无'}",
        f"- warnings: {'; '.join(item.warnings) or '无'}",
        f"- improvement suggestions: {'; '.join(item.improvement_suggestions) or '无'}",
        "",
    ]


def _sample_field_examples(samples: list[object], field_name: str) -> str:
    values = []
    for item in samples[:5]:
        if isinstance(item, dict) and item.get(field_name):
            values.append(str(item[field_name]))
    return "；".join(values) or "无"


def _characteristics_examples(samples: list[object]) -> str:
    values = []
    for item in samples[:5]:
        if isinstance(item, dict):
            characteristics = item.get("characteristics_ch1")
            if isinstance(characteristics, list) and characteristics:
                values.append("; ".join(str(value) for value in characteristics[:2]))
    return "；".join(values) or "无"


def _comparison_examples(comparisons: list[object]) -> str:
    values = []
    for item in comparisons[:3]:
        if isinstance(item, dict):
            values.append(f"{item.get('label')} {item.get('group_sizes')}")
    return "；".join(values) or "无"


def _compact_group(metrics: dict[str, object]) -> str:
    groups = metrics.get("group_sizes")
    if isinstance(groups, dict) and groups:
        return ", ".join(f"{key}:{value}" for key, value in groups.items())
    return "无"


def _first_failure(item: GseAuditResult) -> str:
    metrics = _result_metrics(item)
    if item.warnings:
        return item.warnings[0].replace("|", "/")[:80]
    if not metrics["expression_matrix_detected"]:
        return "缺表达矩阵"
    if not metrics["candidate_comparison_count"]:
        return "未识别候选分组"
    return "无"


def _readiness_can_continue(item: GseAuditResult) -> bool:
    return str((item.readiness_report or {}).get("overall_status") or "") in {"partially_ready", "ready", "ready_with_warnings"}


def _selection_reason(profile: GeoMetadataProfile) -> str:
    comparisons = len(profile.candidate_comparisons)
    return f"stratified_by_analysis_potential:{profile.analysis_potential_level};candidate_comparisons={comparisons}"


def _skipped_result(*, query: str, accession: str, seed: int, reason: str) -> GseAuditResult:
    return GseAuditResult(accession=accession, query=query, seed=seed, selected=False, skipped_reason=reason)


def _safe_geo_url(url: str) -> bool:
    return url.startswith("https://ftp.ncbi.nlm.nih.gov/geo/") or url.startswith("https://www.ncbi.nlm.nih.gov/geo/")


def _is_raw_file(file_name: str, predicted_type: str) -> bool:
    lowered = file_name.lower()
    return predicted_type == "raw_data" or any(pattern in lowered for pattern in RAW_FILE_PATTERNS)


def _geo_prefix(accession: str) -> str:
    match = re.search(r"GSE(\d+)", accession.upper())
    if not match:
        return "GSE0nnn"
    return f"GSE{int(match.group(1)) // 1000}nnn"


def _geo_family_soft_url(accession: str) -> str:
    acc = accession.upper()
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{_geo_prefix(acc)}/{acc}/soft/{acc}_family.soft.gz"


def _geo_matrix_dir_url(accession: str) -> str:
    acc = accession.upper()
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{_geo_prefix(acc)}/{acc}/matrix/"


def _geo_supp_dir_url(accession: str) -> str:
    acc = accession.upper()
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{_geo_prefix(acc)}/{acc}/suppl/"


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _int_or_none(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _group_value(group_preview: object, key: str) -> object:
    return group_preview.get(key, 0) if isinstance(group_preview, dict) else 0


def _first_existing_path(paths: list[str], needles: tuple[str, ...]) -> Path | None:
    for value in paths:
        path = Path(value)
        lowered = path.name.lower()
        if path.exists() and any(needle in lowered for needle in needles):
            return path
    return None


def _first(values: list[str]) -> str:
    return values[0] if values else ""


def _short_text(value: object, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit] + ("..." if len(text) > limit else "") if text else "未记录"


def _yes_no(value: object) -> str:
    return "是" if bool(value) else "否"


def _default_workdir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(tempfile.gettempdir()) / f"biomedpilot_geo_random_audit_{stamp}"


if __name__ == "__main__":
    raise SystemExit(main())
