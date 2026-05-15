from __future__ import annotations

import csv
import gzip
import re
from pathlib import Path
from typing import Any


PHENOTYPE_FIELD_TOKENS = (
    "treatment",
    "genotype",
    "tissue",
    "disease",
    "cell line",
    "cell_line",
    "cell type",
    "cell_type",
    "condition",
    "phenotype",
    "group",
    "source_name_ch1",
)
CLINICAL_FIELD_TOKENS = ("age", "sex", "gender", "stage", "grade", "survival", "status")
GENE_ID_TOKENS = ("id_ref", "gene", "gene symbol", "gene_symbol", "entrez", "ensembl", "probe", "transcript")


def parse_geo_family_soft(path: Path) -> dict[str, object]:
    """Parse a GEO family SOFT file into the current recognition evidence shape."""

    profile = _empty_profile(path)
    _scan_soft_text(path, profile)
    _merge_geoparse_profile(path, profile)
    _finalize_profile(profile)
    return profile


def _empty_profile(path: Path) -> dict[str, object]:
    return {
        "file_name": path.name,
        "file_format": "SOFT",
        "container_type": "geo_family_soft",
        "parser_engine": "GEOparse+soft_scan",
        "geoparse_status": "not_run",
        "parser_depth": "container_only",
        "series_accession": "",
        "series_title": "",
        "series_blocks": 0,
        "sample_block_count": 0,
        "platform_count": 0,
        "platform_block_presence": False,
        "platform_accessions": [],
        "platform_annotation_presence": False,
        "platform_table_presence": False,
        "platform_table_header": [],
        "platform_table_row_count": 0,
        "sample_count": 0,
        "sample_accessions": [],
        "sample_titles": {},
        "sample_metadata_fields": [],
        "phenotype_candidate_fields": [],
        "clinical_candidate_fields": [],
        "source_name_ch1": {},
        "characteristics_ch1": {},
        "expression_table_presence": False,
        "expression_table_sample_count": 0,
        "expression_table_row_count": 0,
        "expression_table_headers": [],
        "species_evidence": [],
        "gene_id_evidence": [],
        "requires_user_confirmation": False,
        "can_enter_standardization": False,
        "warnings": [],
        "_sample_blocks": {},
        "_platform_ids": set(),
        "_sample_table_headers_seen": [],
    }


def _scan_soft_text(path: Path, profile: dict[str, object]) -> None:
    current_sample = ""
    current_block = ""
    in_platform_table = False
    in_sample_table = False
    pending_platform_header = True
    pending_sample_header = True
    try:
        with _open_text(path) as handle:
            for raw_line in handle:
                stripped = raw_line.strip()
                if not stripped:
                    continue
                lower = stripped.lower()
                if stripped.startswith("^DATABASE") or "gene expression omnibus" in lower:
                    profile["has_geo_header"] = True
                elif stripped.startswith("^SERIES"):
                    profile["has_geo_header"] = True
                    profile["series_blocks"] = int(profile.get("series_blocks") or 0) + 1
                    current_block = "series"
                    accession = _assignment_value(stripped)
                    if accession:
                        profile["series_accession"] = accession
                elif stripped.startswith("^PLATFORM"):
                    profile["has_geo_header"] = True
                    current_block = "platform"
                    profile["platform_block_presence"] = True
                    accession = _assignment_value(stripped)
                    if accession:
                        _add_set(profile, "_platform_ids", accession)
                elif stripped.startswith("^SAMPLE"):
                    profile["has_geo_header"] = True
                    current_block = "sample"
                    profile["sample_block_count"] = int(profile.get("sample_block_count") or 0) + 1
                    current_sample = _assignment_value(stripped)
                    if current_sample:
                        _ensure_sample(profile, current_sample)
                elif stripped.startswith("!"):
                    _handle_bang_line(stripped, current_block, current_sample, profile)
                elif stripped.startswith("#"):
                    _handle_column_description(stripped, current_block, profile)

                if stripped.startswith("!platform_table_begin"):
                    in_platform_table = True
                    pending_platform_header = True
                    profile["platform_table_presence"] = True
                    profile["platform_annotation_presence"] = True
                    continue
                if stripped.startswith("!platform_table_end"):
                    in_platform_table = False
                    continue
                if stripped.startswith("!sample_table_begin"):
                    in_sample_table = True
                    pending_sample_header = True
                    continue
                if stripped.startswith("!sample_table_end"):
                    in_sample_table = False
                    continue
                if in_platform_table and not stripped.startswith("!"):
                    cells = _split_tab(stripped)
                    if pending_platform_header:
                        pending_platform_header = False
                        profile["platform_table_header"] = cells
                        _collect_gene_id_evidence(profile, cells, path.name, "platform table header")
                    else:
                        profile["platform_table_row_count"] = int(profile.get("platform_table_row_count") or 0) + 1
                elif in_sample_table and not stripped.startswith("!"):
                    cells = _split_tab(stripped)
                    if pending_sample_header:
                        pending_sample_header = False
                        profile["expression_table_headers"] = cells
                        profile["_sample_table_headers_seen"].append(cells)  # type: ignore[index]
                        _collect_gene_id_evidence(profile, cells, path.name, "sample table header")
                    elif len(cells) >= 2:
                        profile["expression_table_row_count"] = int(profile.get("expression_table_row_count") or 0) + 1
    except OSError as exc:
        _warning(profile, f"SOFT text scan failed: {exc}")


def _handle_bang_line(line: str, current_block: str, current_sample: str, profile: dict[str, object]) -> None:
    key, value = _metadata_pair(line)
    normalized = _normalize_key(key)
    if not normalized:
        return
    if normalized == "series_title":
        profile["series_title"] = value
    elif normalized == "series_geo_accession" and value:
        profile["series_accession"] = value
    elif normalized == "series_sample_id" and value:
        _ensure_sample(profile, value)
    elif normalized in {"series_platform_id", "platform_geo_accession"} and value:
        _add_set(profile, "_platform_ids", value)
    elif normalized in {"series_organism", "sample_organism_ch1", "platform_organism"} and value:
        _add_unique(profile, "species_evidence", f"{profile['file_name']}: {key}={value}")
    elif normalized == "platform_title":
        profile["platform_annotation_presence"] = True
    elif normalized == "sample_title" and current_sample:
        _ensure_sample(profile, current_sample)
        profile["sample_titles"][current_sample] = value  # type: ignore[index]
        _add_unique(profile, "sample_metadata_fields", "title")
    elif normalized == "sample_source_name_ch1" and current_sample:
        _ensure_sample(profile, current_sample)
        profile["source_name_ch1"][current_sample] = value  # type: ignore[index]
        _add_unique(profile, "sample_metadata_fields", "source_name_ch1")
        _add_unique(profile, "phenotype_candidate_fields", "source_name_ch1")
    elif normalized == "sample_characteristics_ch1" and current_sample:
        _ensure_sample(profile, current_sample)
        profile["characteristics_ch1"].setdefault(current_sample, []).append(value)  # type: ignore[union-attr]
        _add_unique(profile, "sample_metadata_fields", "characteristics_ch1")
        for field in _characteristic_fields(value):
            _add_unique(profile, "sample_metadata_fields", field)
            lowered = field.lower().replace("_", " ")
            if any(token in lowered for token in PHENOTYPE_FIELD_TOKENS):
                _add_unique(profile, "phenotype_candidate_fields", field)
            if any(token in lowered for token in CLINICAL_FIELD_TOKENS):
                _add_unique(profile, "clinical_candidate_fields", field)
            if "organism" in lowered or "species" in lowered:
                _add_unique(profile, "species_evidence", f"{profile['file_name']}: {key}={value}")
    elif current_block == "sample" and normalized.startswith("sample_"):
        _add_unique(profile, "sample_metadata_fields", normalized.removeprefix("sample_"))


def _handle_column_description(line: str, current_block: str, profile: dict[str, object]) -> None:
    key, value = _metadata_pair(line)
    normalized = _normalize_key(key)
    if current_block == "platform":
        profile["platform_annotation_presence"] = True
        if _is_gene_id_key(normalized) or _is_gene_id_key(value):
            _add_unique(profile, "gene_id_evidence", f"{profile['file_name']}: platform column {key}")
    elif current_block == "sample":
        if normalized in {"id_ref", "value"}:
            _add_unique(profile, "gene_id_evidence", f"{profile['file_name']}: sample column {key}")


def _merge_geoparse_profile(path: Path, profile: dict[str, object]) -> None:
    try:
        import GEOparse  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - depends on local optional package
        profile["geoparse_status"] = "unavailable"
        _warning(profile, f"GEOparse unavailable: {type(exc).__name__}: {exc}")
        return
    try:
        gse = GEOparse.get_GEO(filepath=str(path), silent=True)
    except Exception as exc:
        profile["geoparse_status"] = "failed"
        _warning(profile, f"GEOparse parse failed; soft_scan evidence retained: {type(exc).__name__}: {exc}")
        return
    profile["geoparse_status"] = "parsed"
    metadata = getattr(gse, "metadata", {}) or {}
    if not profile.get("series_title"):
        profile["series_title"] = _first(metadata.get("title"))
    if not profile.get("series_accession"):
        profile["series_accession"] = str(getattr(gse, "name", "") or _first(metadata.get("geo_accession")))
    for key in ("organism", "sample_organism", "platform_organism"):
        value = _first(metadata.get(key))
        if value:
            _add_unique(profile, "species_evidence", f"{path.name}: GEOparse series {key}={value}")
    gsms = getattr(gse, "gsms", {}) or {}
    for accession, gsm in gsms.items():
        sample_id = str(accession)
        _ensure_sample(profile, sample_id)
        gsm_metadata = getattr(gsm, "metadata", {}) or {}
        title = _first(gsm_metadata.get("title"))
        if title and sample_id not in profile["sample_titles"]:  # type: ignore[operator]
            profile["sample_titles"][sample_id] = title  # type: ignore[index]
        source = _first(gsm_metadata.get("source_name_ch1"))
        if source:
            profile["source_name_ch1"][sample_id] = source  # type: ignore[index]
            _add_unique(profile, "sample_metadata_fields", "source_name_ch1")
            _add_unique(profile, "phenotype_candidate_fields", "source_name_ch1")
        for characteristic in _as_list(gsm_metadata.get("characteristics_ch1")):
            if characteristic:
                profile["characteristics_ch1"].setdefault(sample_id, []).append(characteristic)  # type: ignore[union-attr]
                _add_unique(profile, "sample_metadata_fields", "characteristics_ch1")
                for field in _characteristic_fields(characteristic):
                    _add_unique(profile, "sample_metadata_fields", field)
                    lowered = field.lower().replace("_", " ")
                    if any(token in lowered for token in PHENOTYPE_FIELD_TOKENS):
                        _add_unique(profile, "phenotype_candidate_fields", field)
                    if any(token in lowered for token in CLINICAL_FIELD_TOKENS):
                        _add_unique(profile, "clinical_candidate_fields", field)
        table = getattr(gsm, "table", None)
        columns = [str(column) for column in getattr(table, "columns", [])] if table is not None else []
        if columns:
            profile["expression_table_headers"] = columns
            _collect_gene_id_evidence(profile, columns, path.name, "GEOparse sample table")
        try:
            row_count = len(table.index) if table is not None else 0
        except Exception:
            row_count = 0
        if {"ID_REF", "VALUE"} <= {column.upper() for column in columns} and row_count > 0:
            profile["expression_table_row_count"] = max(int(profile.get("expression_table_row_count") or 0), int(row_count))
    gpls = getattr(gse, "gpls", {}) or {}
    for accession, gpl in gpls.items():
        _add_set(profile, "_platform_ids", str(accession))
        profile["platform_block_presence"] = True
        table = getattr(gpl, "table", None)
        columns = [str(column) for column in getattr(table, "columns", [])] if table is not None else []
        if columns:
            profile["platform_table_header"] = columns
            profile["platform_annotation_presence"] = True
            profile["platform_table_presence"] = True
            _collect_gene_id_evidence(profile, columns, path.name, "GEOparse platform table")
        try:
            row_count = len(table.index) if table is not None else 0
        except Exception:
            row_count = 0
        profile["platform_table_row_count"] = max(int(profile.get("platform_table_row_count") or 0), int(row_count))


def _finalize_profile(profile: dict[str, object]) -> None:
    sample_blocks = profile.get("_sample_blocks")
    samples = list(sample_blocks.keys()) if isinstance(sample_blocks, dict) else []
    profile["sample_accessions"] = samples
    profile["sample_count"] = len(samples)
    platforms = sorted(str(item) for item in profile.get("_platform_ids", set()) if str(item))
    profile["platform_accessions"] = platforms
    profile["platform_count"] = len(platforms)
    headers_seen = profile.get("_sample_table_headers_seen")
    expression_headers = [str(item) for item in profile.get("expression_table_headers", []) or []]
    has_expression_header = _has_expression_header(expression_headers)
    if isinstance(headers_seen, list):
        has_expression_header = has_expression_header or any(_has_expression_header([str(cell) for cell in header]) for header in headers_seen if isinstance(header, list))
    expression_rows = int(profile.get("expression_table_row_count") or 0)
    profile["expression_table_presence"] = bool(has_expression_header and expression_rows > 0)
    profile["expression_table_sample_count"] = int(profile.get("sample_count") or 0) if profile["expression_table_presence"] else 0
    profile["platform_annotation_presence"] = bool(
        profile.get("platform_annotation_presence")
        or profile.get("platform_table_presence")
        or profile.get("platform_count")
    )
    profile["requires_user_confirmation"] = bool(profile["expression_table_presence"])
    profile["can_enter_standardization"] = bool(profile["expression_table_presence"])
    if not profile.get("has_geo_header"):
        _warning(profile, "No GEO SOFT header was found.")
    if not profile.get("sample_count"):
        _warning(profile, "No SAMPLE blocks were parsed.")
    if profile.get("sample_count") and not profile.get("expression_table_presence"):
        _warning(profile, "Parsed sample/platform metadata, but no clear ID_REF/VALUE expression table was confirmed.")
    profile["parser_depth"] = _parser_depth(profile)
    for private_key in ("_sample_blocks", "_platform_ids", "_sample_table_headers_seen", "has_geo_header"):
        profile.pop(private_key, None)


def _parser_depth(profile: dict[str, object]) -> str:
    table_markers = bool(profile.get("platform_table_presence") or profile.get("expression_table_headers"))
    table_parsed = bool(
        (profile.get("platform_table_presence") and profile.get("platform_table_header"))
        or profile.get("expression_table_presence")
    )
    if table_parsed:
        return "table_parsed"
    if table_markers:
        return "table_detected"
    if profile.get("sample_count") or profile.get("platform_count") or profile.get("sample_metadata_fields"):
        return "metadata_parsed"
    return "container_only"


def _ensure_sample(profile: dict[str, object], accession: str) -> None:
    if not accession:
        return
    blocks = profile.get("_sample_blocks")
    if isinstance(blocks, dict):
        blocks.setdefault(accession, {})
    _add_unique(profile, "sample_metadata_fields", "geo_accession")


def _add_set(profile: dict[str, object], key: str, value: str) -> None:
    values = profile.get(key)
    if isinstance(values, set) and value:
        values.add(value)


def _add_unique(profile: dict[str, object], key: str, value: str) -> None:
    if not value:
        return
    values = profile.setdefault(key, [])
    if isinstance(values, list) and value not in values:
        values.append(value)


def _warning(profile: dict[str, object], value: str) -> None:
    _add_unique(profile, "warnings", value)


def _open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8", errors="ignore") if path.name.lower().endswith(".gz") else path.open("r", encoding="utf-8", errors="ignore")


def _assignment_value(line: str) -> str:
    return line.partition("=")[2].strip()


def _metadata_pair(line: str) -> tuple[str, str]:
    key, _, value = line.partition("=")
    return key.strip().lstrip("!#"), value.strip()


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _split_tab(line: str) -> list[str]:
    try:
        return [cell.strip().strip('"') for cell in next(csv.reader([line], delimiter="\t"))]
    except csv.Error:
        return [cell.strip().strip('"') for cell in line.split("\t")]


def _characteristic_fields(value: str) -> list[str]:
    fields: list[str] = []
    for part in re.split(r";\s*", value):
        key, sep, _ = part.partition(":")
        if sep:
            normalized = _normalize_key(key)
            if normalized:
                fields.append(normalized)
    return fields


def _collect_gene_id_evidence(profile: dict[str, object], columns: list[str], file_name: str, source: str) -> None:
    for column in columns:
        if _is_gene_id_key(column):
            _add_unique(profile, "gene_id_evidence", f"{file_name}: {source} column {column}")


def _is_gene_id_key(value: object) -> bool:
    normalized = str(value).strip().lower().replace("_", " ")
    return any(token in normalized for token in GENE_ID_TOKENS)


def _has_expression_header(columns: list[str]) -> bool:
    normalized = {_normalize_key(column) for column in columns}
    return "id_ref" in normalized and "value" in normalized


def _first(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return str(value[0]) if value else ""
    return str(value) if value is not None else ""


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]
