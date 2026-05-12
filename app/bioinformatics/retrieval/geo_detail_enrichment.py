from __future__ import annotations

import html
import json
import re
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Any
from urllib.parse import urljoin

import requests

from app.bioinformatics.services.organism_display import get_organism_display_name, get_organism_zh


GEO_QUERY_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"


@dataclass(frozen=True)
class GeoPlatformDetail:
    accession: str
    title: str = ""


@dataclass(frozen=True)
class GeoSamplePreview:
    accession: str
    title: str = ""
    characteristics: tuple[str, ...] = ()


@dataclass(frozen=True)
class GeoSupplementaryDetail:
    file_name: str
    file_size: str = ""
    url: str = ""
    file_type: str = ""


@dataclass(frozen=True)
class GeoDownloadLink:
    label: str
    url: str


@dataclass(frozen=True)
class GeoDetailMetadata:
    accession: str
    title: str = ""
    organism: str = ""
    organism_zh: str = ""
    organism_display_name: str = ""
    experiment_type: str = ""
    summary: str = ""
    overall_design: str = ""
    status: str = ""
    public_date: str = ""
    submit_date: str = ""
    last_update_date: str = ""
    contributors: tuple[str, ...] = ()
    citation: str = ""
    pmid: str = ""
    platforms: tuple[GeoPlatformDetail, ...] = ()
    sample_count: int = 0
    sample_preview: tuple[GeoSamplePreview, ...] = ()
    supplementary_files: tuple[GeoSupplementaryDetail, ...] = ()
    download_links: tuple[GeoDownloadLink, ...] = ()
    superseries: str = ""
    bioproject: str = ""
    geo_url: str = ""
    fetched_at: str = ""
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_candidate_metadata(self) -> dict[str, object]:
        platform_accessions = [platform.accession for platform in self.platforms if platform.accession]
        platform_titles = [platform.title for platform in self.platforms if platform.title]
        sample_preview = [asdict(item) for item in self.sample_preview]
        supplementary_files = [asdict(item) for item in self.supplementary_files]
        download_links = [asdict(item) for item in self.download_links]
        return {
            "accession": self.accession,
            "gse_id": self.accession,
            "geo_detail_enriched": True,
            "geo_detail_enriched_at": self.fetched_at,
            "geo_detail_cache_schema": "bioinformatics.geo_detail.v1",
            "geo_url": self.geo_url,
            "title_en": self.title,
            "summary_en": self.summary,
            "overall_design_en": self.overall_design,
            "organism": self.organism,
            "organism_zh": self.organism_zh,
            "organism_display_name": self.organism_display_name,
            "experiment_type": self.experiment_type,
            "status": self.status,
            "public_date": self.public_date,
            "submit_date": self.submit_date,
            "last_update_date": self.last_update_date,
            "contributors": list(self.contributors),
            "citation": self.citation,
            "pmid": self.pmid,
            "platform_accessions": platform_accessions,
            "platform_titles": platform_titles,
            "platforms": [asdict(item) for item in self.platforms],
            "sample_count": self.sample_count,
            "sample_preview": sample_preview,
            "sample_summary": _sample_overview_text(sample_preview),
            "supplementary_files": supplementary_files,
            "download_links": download_links,
            "superseries": self.superseries,
            "bioproject": self.bioproject,
            "geo_detail_warnings": list(self.warnings),
        }


FetchText = Callable[[str, dict[str, str]], str]


class GeoDetailEnrichmentService:
    def __init__(
        self,
        *,
        timeout: int = 30,
        session: requests.Session | None = None,
        fetch_text: FetchText | None = None,
    ) -> None:
        self.timeout = timeout
        self.session = session or requests.Session()
        self._fetch_text = fetch_text
        self.session.headers.update(
            {
                "User-Agent": "BioMedPilot/1.0 GEO detail enrichment",
                "Accept": "text/html,text/plain,*/*",
            }
        )

    def enrich(
        self,
        accession: str,
        *,
        project_root: Path | None = None,
        existing_metadata: dict[str, object] | None = None,
        force_refresh: bool = False,
    ) -> GeoDetailMetadata:
        normalized = _normalize_accession(accession)
        existing = dict(existing_metadata or {})
        cache_path = geo_detail_cache_path(project_root, normalized) if project_root is not None else None
        if not force_refresh and cache_path is not None:
            cached = _read_cached_detail(cache_path)
            if cached is not None and _detail_cache_sufficient(cached):
                return _metadata_from_dict({**existing, **cached, "accession": normalized})

        warnings: list[str] = []
        try:
            self_text = self._get_text({"acc": normalized, "targ": "self", "form": "text", "view": "quick"})
        except Exception as exc:
            warnings.append(f"GEO Series SOFT 抓取失败：{exc}")
            self_text = ""
        try:
            gsm_text = self._get_text({"acc": normalized, "targ": "gsm", "form": "text", "view": "quick"})
        except Exception as exc:
            warnings.append(f"GEO GSM SOFT 抓取失败：{exc}")
            gsm_text = ""
        try:
            html_text = self._get_text({"acc": normalized})
        except Exception as exc:
            warnings.append(f"GEO HTML 详情抓取失败：{exc}")
            html_text = ""

        detail = build_geo_detail_metadata(
            normalized,
            self_text=self_text,
            gsm_text=gsm_text,
            html_text=html_text,
            existing_metadata=existing,
            warnings=tuple(warnings),
        )
        if cache_path is not None and (detail.summary or detail.overall_design or detail.sample_preview or detail.supplementary_files):
            _write_json_atomic(cache_path, detail.to_dict())
        return detail

    def _get_text(self, params: dict[str, str]) -> str:
        if self._fetch_text is not None:
            return self._fetch_text(GEO_QUERY_URL, params)
        response = self.session.get(GEO_QUERY_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.text


def geo_detail_cache_path(project_root: Path | None, accession: str) -> Path:
    root = Path(project_root) if project_root is not None else Path(".")
    return root / "acquisition" / "geo_detail_cache" / f"{_normalize_accession(accession)}_detail.json"


def build_geo_detail_metadata(
    accession: str,
    *,
    self_text: str = "",
    gsm_text: str = "",
    html_text: str = "",
    existing_metadata: dict[str, object] | None = None,
    warnings: tuple[str, ...] = (),
) -> GeoDetailMetadata:
    normalized = _normalize_accession(accession)
    existing = dict(existing_metadata or {})
    html_detail = _parse_geo_html_detail(html_text)
    sample_preview = tuple(_parse_gsm_soft_samples(gsm_text) or html_detail.get("sample_preview") or ())
    platforms = tuple(_merge_platforms(_parse_platforms_from_soft(self_text), html_detail.get("platforms") or [], existing))
    supplementary = tuple(html_detail.get("supplementary_files") or _parse_supplementary_from_soft(self_text))
    download_links = tuple(_download_links_from_html(normalized, html_text))
    relations = _parse_relations(self_text)
    organism = _first_text(
        _unique_soft_values(self_text, "!Series_sample_organism"),
        _unique_soft_values(self_text, "!Series_organism"),
        [str(existing.get("organism") or "")],
    )
    title = _first_text(_soft_values(self_text, "!Series_title"), [str(existing.get("title_en") or existing.get("display_title") or "")])
    summary = " ".join(_soft_values(self_text, "!Series_summary")).strip() or str(existing.get("summary_en") or "")
    overall_design = " ".join(_soft_values(self_text, "!Series_overall_design")).strip() or str(existing.get("overall_design_en") or "")
    experiment_type = _first_text(_unique_soft_values(self_text, "!Series_type"), [str(existing.get("experiment_type") or existing.get("data_type") or existing.get("data_modality") or "")])
    status = _first_text(_soft_values(self_text, "!Series_status"), [str(existing.get("status") or "")])
    sample_count = _sample_count_from_sources(self_text, html_text, sample_preview, existing)
    pmid = _first_text(_soft_values(self_text, "!Series_pubmed_id"), [str(existing.get("pmid") or existing.get("pubmed_id") or "")])
    organism_display = get_organism_display_name(organism)
    return GeoDetailMetadata(
        accession=normalized,
        title=title,
        organism=organism,
        organism_zh=get_organism_zh(organism),
        organism_display_name=organism_display,
        experiment_type=experiment_type,
        summary=summary,
        overall_design=overall_design,
        status=status,
        public_date=_public_date_from_status(status),
        submit_date=_first_text(_soft_values(self_text, "!Series_submission_date"), [str(existing.get("submit_date") or "")]),
        last_update_date=_first_text(_soft_values(self_text, "!Series_last_update_date"), [str(existing.get("last_update_date") or "")]),
        contributors=tuple(_format_contributor(value) for value in _soft_values(self_text, "!Series_contributor") if value.strip()),
        citation=_clean_text(str(html_detail.get("citation") or existing.get("citation") or "")),
        pmid=pmid,
        platforms=platforms,
        sample_count=sample_count,
        sample_preview=sample_preview,
        supplementary_files=supplementary,
        download_links=download_links,
        superseries=str(relations.get("superseries") or existing.get("superseries") or ""),
        bioproject=str(relations.get("bioproject") or existing.get("bioproject") or ""),
        geo_url=f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={normalized}",
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        warnings=tuple(warning for warning in warnings if warning),
    )


def _metadata_from_dict(payload: dict[str, object]) -> GeoDetailMetadata:
    platforms = tuple(
        GeoPlatformDetail(accession=str(item.get("accession") or ""), title=str(item.get("title") or ""))
        for item in payload.get("platforms", []) or []
        if isinstance(item, dict)
    )
    samples = tuple(
        GeoSamplePreview(
            accession=str(item.get("accession") or ""),
            title=str(item.get("title") or ""),
            characteristics=tuple(str(value) for value in item.get("characteristics", []) or []),
        )
        for item in payload.get("sample_preview", []) or []
        if isinstance(item, dict)
    )
    supplementary = tuple(
        GeoSupplementaryDetail(
            file_name=str(item.get("file_name") or ""),
            file_size=str(item.get("file_size") or ""),
            url=str(item.get("url") or ""),
            file_type=str(item.get("file_type") or ""),
        )
        for item in payload.get("supplementary_files", []) or []
        if isinstance(item, dict)
    )
    links = tuple(
        GeoDownloadLink(label=str(item.get("label") or ""), url=str(item.get("url") or ""))
        for item in payload.get("download_links", []) or []
        if isinstance(item, dict)
    )
    organism = str(payload.get("organism") or "")
    return GeoDetailMetadata(
        accession=_normalize_accession(str(payload.get("accession") or "")),
        title=str(payload.get("title") or payload.get("title_en") or ""),
        organism=organism,
        organism_zh=str(payload.get("organism_zh") or get_organism_zh(organism)),
        organism_display_name=str(payload.get("organism_display_name") or get_organism_display_name(organism)),
        experiment_type=str(payload.get("experiment_type") or ""),
        summary=str(payload.get("summary") or payload.get("summary_en") or ""),
        overall_design=str(payload.get("overall_design") or payload.get("overall_design_en") or ""),
        status=str(payload.get("status") or ""),
        public_date=str(payload.get("public_date") or ""),
        submit_date=str(payload.get("submit_date") or ""),
        last_update_date=str(payload.get("last_update_date") or ""),
        contributors=tuple(str(item) for item in payload.get("contributors", []) or []),
        citation=str(payload.get("citation") or ""),
        pmid=str(payload.get("pmid") or ""),
        platforms=platforms,
        sample_count=_safe_int(payload.get("sample_count")),
        sample_preview=samples,
        supplementary_files=supplementary,
        download_links=links,
        superseries=str(payload.get("superseries") or ""),
        bioproject=str(payload.get("bioproject") or ""),
        geo_url=str(payload.get("geo_url") or ""),
        fetched_at=str(payload.get("fetched_at") or payload.get("geo_detail_enriched_at") or ""),
        warnings=tuple(str(item) for item in payload.get("warnings", []) or payload.get("geo_detail_warnings", []) or []),
    )


def _read_cached_detail(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _detail_cache_sufficient(payload: dict[str, object]) -> bool:
    return bool(
        str(payload.get("summary") or payload.get("summary_en") or "").strip()
        and str(payload.get("overall_design") or payload.get("overall_design_en") or "").strip()
        and payload.get("sample_preview")
        and payload.get("supplementary_files")
    )


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temp_path = Path(handle.name)
    temp_path.replace(path)


def _soft_values(text: str, key: str) -> list[str]:
    pattern = re.compile(rf"^{re.escape(key)}\s*=\s*(.+)$", flags=re.MULTILINE)
    return [_clean_text(match) for match in pattern.findall(text or "") if _clean_text(match)]


def _unique_soft_values(text: str, key: str) -> list[str]:
    return list(dict.fromkeys(_soft_values(text, key)))


def _parse_gsm_soft_samples(text: str) -> list[GeoSamplePreview]:
    samples: list[GeoSamplePreview] = []
    current: dict[str, Any] | None = None
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if line.startswith("^SAMPLE"):
            if current:
                samples.append(_sample_from_record(current))
            current = {"accession": _clean_text(line.split("=", 1)[1] if "=" in line else ""), "characteristics": []}
            continue
        if current is None or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        if key == "!Sample_title":
            current["title"] = _clean_text(value)
        elif key == "!Sample_geo_accession":
            current["accession"] = _clean_text(value)
        elif key == "!Sample_characteristics_ch1":
            current.setdefault("characteristics", []).append(_clean_text(value))
    if current:
        samples.append(_sample_from_record(current))
    return samples


def _sample_from_record(record: dict[str, Any]) -> GeoSamplePreview:
    return GeoSamplePreview(
        accession=str(record.get("accession") or ""),
        title=str(record.get("title") or ""),
        characteristics=tuple(str(item) for item in record.get("characteristics", []) if str(item).strip()),
    )


def _parse_platforms_from_soft(text: str) -> list[GeoPlatformDetail]:
    return [GeoPlatformDetail(accession=value, title="") for value in _unique_soft_values(text, "!Series_platform_id")]


def _merge_platforms(
    soft_platforms: list[GeoPlatformDetail],
    html_platforms: list[GeoPlatformDetail],
    existing: dict[str, object],
) -> list[GeoPlatformDetail]:
    by_accession: dict[str, GeoPlatformDetail] = {}
    for item in [*soft_platforms, *html_platforms]:
        if not item.accession:
            continue
        prior = by_accession.get(item.accession)
        by_accession[item.accession] = GeoPlatformDetail(accession=item.accession, title=item.title or (prior.title if prior else ""))
    accessions = existing.get("platform_accessions")
    titles = existing.get("platform_titles")
    if isinstance(accessions, list):
        for index, accession in enumerate(accessions):
            key = str(accession or "").strip()
            if not key:
                continue
            title = ""
            if isinstance(titles, list) and index < len(titles):
                title = str(titles[index] or "")
            prior = by_accession.get(key)
            by_accession[key] = GeoPlatformDetail(accession=key, title=(prior.title if prior and prior.title else title))
    return list(by_accession.values())


def _parse_supplementary_from_soft(text: str) -> list[GeoSupplementaryDetail]:
    details: list[GeoSupplementaryDetail] = []
    for url in _soft_values(text, "!Series_supplementary_file"):
        details.append(GeoSupplementaryDetail(file_name=url.rsplit("/", 1)[-1], url=url))
    return details


def _parse_relations(text: str) -> dict[str, str]:
    relations: dict[str, str] = {}
    for value in _soft_values(text, "!Series_relation"):
        if "SubSeries of:" in value:
            match = re.search(r"(GSE\d+)", value)
            if match:
                relations["superseries"] = match.group(1)
        if "BioProject:" in value:
            match = re.search(r"(PRJNA\d+)", value)
            if match:
                relations["bioproject"] = match.group(1)
            else:
                relations["bioproject"] = value.split("BioProject:", 1)[1].strip()
    return relations


class _GeoTableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[tuple[str, str]]] = []
        self._row: list[tuple[str, str]] | None = None
        self._cell_text: list[str] | None = None
        self._cell_href = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell_text = []
            self._cell_href = ""
        elif tag == "a" and self._cell_text is not None:
            attrs_dict = {key: value or "" for key, value in attrs}
            if attrs_dict.get("href") and not self._cell_href:
                self._cell_href = attrs_dict["href"]

    def handle_data(self, data: str) -> None:
        if self._cell_text is not None:
            self._cell_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._row is not None and self._cell_text is not None:
            self._row.append((_clean_text(" ".join(self._cell_text)), self._cell_href))
            self._cell_text = None
            self._cell_href = ""
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None


def _parse_geo_html_detail(text: str) -> dict[str, object]:
    parser = _GeoTableHTMLParser()
    try:
        parser.feed(text or "")
    except Exception:
        return {}
    platforms: list[GeoPlatformDetail] = []
    samples: list[GeoSamplePreview] = []
    supplements: list[GeoSupplementaryDetail] = []
    citation = ""
    for row in parser.rows:
        values = [cell[0] for cell in row]
        joined = " ".join(values)
        for value in values:
            if value.startswith("GPL") and len(row) >= 2:
                accession = value.split()[0]
                if re.fullmatch(r"GPL\d+", accession):
                    title = values[1] if values[1] != value else ""
                    platforms.append(GeoPlatformDetail(accession=accession, title=title))
            if value.startswith("GSM") and len(row) >= 2:
                accession = value.split()[0]
                if re.fullmatch(r"GSM\d+", accession):
                    samples.append(GeoSamplePreview(accession=accession, title=values[1] if values[1] != value else ""))
        if values and re.match(r"GSE\d+_.+\.(?:tar|gz|zip|txt|csv|xlsx?|soft)", values[0], re.I):
            supplements.append(
                GeoSupplementaryDetail(
                    file_name=values[0],
                    file_size=values[1] if len(values) > 1 else "",
                    url=urljoin("https://www.ncbi.nlm.nih.gov", row[2][1]) if len(row) > 2 and row[2][1] else "",
                    file_type=values[3] if len(values) > 3 else "",
                )
            )
        if not citation and ("Citation" in joined or "Science" in joined) and "PMID" in joined:
            citation = joined
    return {
        "platforms": _dedupe_platforms(platforms),
        "sample_preview": _dedupe_samples(samples),
        "supplementary_files": supplements,
        "citation": citation,
    }


def _download_links_from_html(accession: str, text: str) -> list[GeoDownloadLink]:
    links = [
        GeoDownloadLink("GEO HTML", f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}"),
        GeoDownloadLink("SOFT", f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}&targ=self&form=text&view=quick"),
        GeoDownloadLink("MINiML", f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}&targ=self&form=xml&view=quick"),
        GeoDownloadLink("Series Matrix", f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}&targ=self&form=text&view=quick"),
    ]
    if "format=file" in (text or ""):
        links.append(GeoDownloadLink("Supplementary files", f"https://www.ncbi.nlm.nih.gov/geo/download/?acc={accession}&format=file"))
    return links


def _sample_count_from_sources(
    self_text: str,
    html_text: str,
    samples: tuple[GeoSamplePreview, ...] | list[GeoSamplePreview],
    existing: dict[str, object],
) -> int:
    count = len(_unique_soft_values(self_text, "!Series_sample_id")) or len(samples)
    match = re.search(r"Samples\s*\((\d+)\)", html.unescape(html_text or ""))
    if match:
        count = max(count, _safe_int(match.group(1)))
    return count or _safe_int(existing.get("sample_count"))


def _first_text(*groups: list[str]) -> str:
    for group in groups:
        for value in group:
            text = _clean_text(value)
            if text and text not in {"未记录", "待确认"}:
                return text
    return ""


def _public_date_from_status(status: str) -> str:
    match = re.search(r"Public on\s+(.+)$", status or "", flags=re.I)
    return match.group(1).strip() if match else ""


def _format_contributor(value: str) -> str:
    parts = [part for part in value.replace(",,", ",").split(",") if part]
    return " ".join(parts).strip() or value


def _clean_text(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _safe_int(value: object) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def _normalize_accession(accession: str) -> str:
    return str(accession or "").strip().upper()


def _dedupe_platforms(items: list[GeoPlatformDetail]) -> list[GeoPlatformDetail]:
    seen: dict[str, GeoPlatformDetail] = {}
    for item in items:
        if item.accession and item.accession not in seen:
            seen[item.accession] = item
    return list(seen.values())


def _dedupe_samples(items: list[GeoSamplePreview]) -> list[GeoSamplePreview]:
    seen: dict[str, GeoSamplePreview] = {}
    for item in items:
        if item.accession and item.accession not in seen:
            seen[item.accession] = item
    return list(seen.values())


def _sample_overview_text(items: list[dict[str, object]]) -> str:
    lines: list[str] = []
    for item in items[:20]:
        accession = str(item.get("accession") or "")
        title = str(item.get("title") or "")
        if accession or title:
            lines.append(f"{accession}: {title}".strip(": "))
    return "\n".join(lines)
