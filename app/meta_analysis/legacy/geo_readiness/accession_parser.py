from __future__ import annotations

import re
from html import unescape

from geo_readiness.models import GeoAccessionInventory, GeoRemoteAssetCandidate


def parse_geo_accession_metadata(text: str) -> GeoAccessionInventory:
    content = text or ""
    errors: list[str] = []
    warnings: list[str] = []
    if not content.strip():
        return GeoAccessionInventory(
            gse_id="",
            errors=["metadata_parse_failed"],
        )

    normalized_text = _normalize_metadata_text(content)
    gse_id = _first_match(r"\b(GSE\d+)\b", normalized_text)
    if not gse_id:
        errors.append("metadata_parse_failed")

    title = _field_value(normalized_text, ["Title", "title"])
    summary = _field_value(normalized_text, ["Summary", "summary"])
    organism = _field_value(normalized_text, ["Organism", "organism"])
    sample_count = _sample_count(normalized_text)
    platform_ids = sorted(set(re.findall(r"\bGPL\d+\b", normalized_text)))

    if not title:
        warnings.append("title_missing")
    if not summary:
        warnings.append("summary_missing")
    if not organism:
        warnings.append("organism_missing")
    if not sample_count:
        warnings.append("sample_count_missing")

    series_candidates = _series_matrix_candidates(normalized_text, gse_id)
    supplementary_candidates = _supplementary_candidates(normalized_text)
    sample_metadata_candidates = _sample_metadata_candidates(normalized_text)
    expression_candidates = _expression_candidates(
        normalized_text,
        series_candidates=series_candidates,
        supplementary_candidates=supplementary_candidates,
    )

    return GeoAccessionInventory(
        gse_id=gse_id,
        title=title,
        summary=summary,
        organism=organism,
        sample_count=sample_count,
        platform_ids=platform_ids,
        series_matrix_candidates=series_candidates,
        supplementary_candidates=supplementary_candidates,
        sample_metadata_candidates=sample_metadata_candidates,
        expression_candidates=expression_candidates,
        warnings=warnings,
        errors=errors,
    )


def _field_value(text: str, labels: list[str]) -> str:
    for label in labels:
        pattern = rf"^\s*(?:!Series_)?{re.escape(label)}\s*[:=]\s*(.+?)\s*$"
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ""


def _first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).upper() if match else ""


def _sample_count(text: str) -> int:
    patterns = [
        r"Samples?\s*[:=]\s*(\d+)",
        r"Sample count\s*[:=]\s*(\d+)",
        r"Samples?\s*\(\s*(\d+)\s*\)",
        r"(\d+)\s+samples?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 0


def _normalize_metadata_text(text: str) -> str:
    normalized = unescape(text)
    normalized = re.sub(r"(?i)<br\s*/?>", "\n", normalized)
    normalized = re.sub(r"(?i)</(?:tr|p|div|li|h\d|td|th)>", "\n", normalized)
    normalized = re.sub(r"(?is)<script.*?</script>", " ", normalized)
    normalized = re.sub(r"(?is)<style.*?</style>", " ", normalized)
    normalized = re.sub(r"<[^>]+>", " ", normalized)
    normalized = normalized.replace("\xa0", " ")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = _normalize_labeled_field(normalized, "Title")
    normalized = _normalize_labeled_field(normalized, "Summary")
    normalized = _normalize_labeled_field(normalized, "Organism")
    normalized = re.sub(
        r"(?i)(\b\d+\s+samples?)",
        r"\n\1",
        normalized,
    )
    return "\n".join(line.strip() for line in normalized.splitlines() if line.strip())


def _normalize_labeled_field(text: str, label: str) -> str:
    return re.sub(
        rf"(?i)\b{label}\b\s*[:=]?\s*",
        f"\n{label}: ",
        text,
        count=1,
    )


def _series_matrix_candidates(
    text: str,
    gse_id: str,
) -> list[GeoRemoteAssetCandidate]:
    candidates: list[GeoRemoteAssetCandidate] = []
    for name in _candidate_names(text, r"\b\S*series_matrix\S*\.txt(?:\.gz)?\b"):
        candidates.append(
            GeoRemoteAssetCandidate(
                candidate_type="series_matrix",
                name=name,
                confidence=0.9,
                reasons=["series_matrix_hint"],
            )
        )
    if not candidates and re.search(r"Series Matrix", text, flags=re.IGNORECASE):
        candidates.append(
            GeoRemoteAssetCandidate(
                candidate_type="series_matrix",
                name=f"{gse_id or 'GSE'}_series_matrix.txt.gz",
                confidence=0.6,
                reasons=["series_matrix_label"],
            )
        )
    return candidates


def _supplementary_candidates(text: str) -> list[GeoRemoteAssetCandidate]:
    candidates: list[GeoRemoteAssetCandidate] = []
    patterns = [
        r"\bGSE\d+_[\w.\-]+(?:\.txt|\.csv|\.tsv|\.gz|\.tar)\b",
        (
            r"\b[\w.\-]+(?:annotation|clinical|matrix|counts|tpm|fpkm)"
            r"[\w.\-]*(?:\.txt|\.csv|\.tsv|\.gz)\b"
        ),
    ]
    seen: set[str] = set()
    for pattern in patterns:
        for name in _candidate_names(text, pattern):
            if name in seen:
                continue
            seen.add(name)
            candidates.append(
                GeoRemoteAssetCandidate(
                    candidate_type="supplementary_file",
                    name=name,
                    size_hint=_size_hint_for_line(text, name),
                    confidence=0.7,
                    reasons=["supplementary_file_hint"],
                )
            )
    return candidates


def _sample_metadata_candidates(text: str) -> list[GeoRemoteAssetCandidate]:
    candidates: list[GeoRemoteAssetCandidate] = []
    if re.search(r"sample table|sample metadata|Series Matrix", text, flags=re.IGNORECASE):
        candidates.append(
            GeoRemoteAssetCandidate(
                candidate_type="sample_metadata",
                name="GEO sample metadata",
                confidence=0.7,
                reasons=["sample_metadata_hint"],
            )
        )
    for candidate in _supplementary_candidates(text):
        if re.search(r"clinical|annotation|metadata", candidate.name, flags=re.IGNORECASE):
            candidates.append(
                GeoRemoteAssetCandidate(
                    candidate_type="sample_metadata",
                    name=candidate.name,
                    size_hint=candidate.size_hint,
                    confidence=0.75,
                    reasons=["supplementary_metadata_name"],
                )
            )
    return candidates


def _expression_candidates(
    text: str,
    *,
    series_candidates: list[GeoRemoteAssetCandidate],
    supplementary_candidates: list[GeoRemoteAssetCandidate],
) -> list[GeoRemoteAssetCandidate]:
    candidates: list[GeoRemoteAssetCandidate] = []
    if re.search(r"processed data.*sample table|expression matrix", text, flags=re.IGNORECASE):
        candidates.append(
            GeoRemoteAssetCandidate(
                candidate_type="expression_matrix",
                name="GEO processed sample table",
                confidence=0.55,
                reasons=["processed_data_sample_table_hint"],
            )
        )
    for candidate in series_candidates:
        candidates.append(
            GeoRemoteAssetCandidate(
                candidate_type="expression_matrix",
                name=candidate.name,
                confidence=0.6,
                reasons=["series_matrix_may_include_processed_values"],
            )
        )
    for candidate in supplementary_candidates:
        if re.search(r"matrix|counts|tpm|fpkm|expression", candidate.name, flags=re.IGNORECASE):
            candidates.append(
                GeoRemoteAssetCandidate(
                    candidate_type="expression_matrix",
                    name=candidate.name,
                    size_hint=candidate.size_hint,
                    confidence=0.7,
                    reasons=["supplementary_expression_name"],
                )
            )
    return candidates


def _candidate_names(text: str, pattern: str) -> list[str]:
    return sorted(
        set(
            match.group(0).strip(".,;()[]")
            for match in re.finditer(pattern, text, flags=re.IGNORECASE)
        )
    )


def _size_hint_for_line(text: str, name: str) -> str:
    for line in text.splitlines():
        if name in line:
            match = re.search(r"(\d+(?:\.\d+)?\s*(?:Kb|Mb|Gb|B))", line, flags=re.IGNORECASE)
            if match:
                return match.group(1)
    return ""
