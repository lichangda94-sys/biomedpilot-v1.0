from __future__ import annotations

import csv
import gzip
import re
from pathlib import Path


SAMPLE_METADATA_KEYS = {
    "sample_geo_accession",
    "sample_title",
    "sample_source_name_ch1",
    "sample_organism_ch1",
    "sample_characteristics_ch1",
    "sample_treatment_protocol_ch1",
    "sample_growth_protocol_ch1",
    "sample_extract_protocol_ch1",
    "sample_data_processing",
    "sample_platform_id",
    "sample_relation",
}
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
    "title_pattern",
)
CLINICAL_FIELD_TOKENS = ("age", "sex", "gender", "stage", "grade", "survival", "status")


def parse_geo_series_matrix(path: Path, *, preview_rows: int = 100) -> dict[str, object]:
    profile = _empty_profile(path)
    try:
        _scan_series_matrix(path, profile, encoding="utf-8", errors="strict", preview_rows=preview_rows)
    except UnicodeDecodeError:
        profile = _empty_profile(path)
        _warning(profile, "UTF-8 decode failed; retried with latin-1 replacement decoding.")
        _scan_series_matrix(path, profile, encoding="latin-1", errors="replace", preview_rows=preview_rows)
    except OSError as exc:
        _warning(profile, f"Series Matrix read failed: {exc}")
    _finalize_profile(profile)
    return profile


def _empty_profile(path: Path) -> dict[str, object]:
    return {
        "file_name": path.name,
        "file_format": "TXT.GZ" if path.name.lower().endswith(".gz") else "TXT",
        "container_type": "geo_series_matrix",
        "parser_depth": "container_only",
        "series_accession": "",
        "series_title": "",
        "series_summary": "",
        "overall_design": "",
        "platform_accessions": [],
        "sample_count": 0,
        "sample_accessions": [],
        "sample_titles": {},
        "sample_source_name_ch1": {},
        "sample_characteristics_ch1": {},
        "sample_metadata_fields": [],
        "phenotype_candidate_fields": [],
        "phenotype_candidate_values_preview": {},
        "clinical_candidate_fields": [],
        "expression_matrix_presence": False,
        "expression_matrix_dimensions": {"rows": 0, "columns": 0, "sample_columns": 0},
        "table_data_row_count": 0,
        "gsm_column_count": 0,
        "matrix_column_count": 0,
        "id_column": "",
        "sample_columns": [],
        "expression_value_type_candidate": "unknown",
        "gene_id_type_candidate": "unknown",
        "species_evidence": [],
        "warnings": [],
        "requires_user_confirmation": False,
        "can_enter_standardization": False,
        "table_begin_line": None,
        "table_end_line": None,
        "table_header_line": None,
        "matrix_row_count_approximate": True,
        "_sample_rows": {},
        "_platform_accessions": [],
        "_id_preview": [],
        "_value_preview": [],
        "_sample_organisms": [],
        "_series_species_values": [],
        "_platform_species_values": [],
        "_saw_series_or_sample_metadata": False,
        "_saw_matrix_end": False,
    }


def _scan_series_matrix(path: Path, profile: dict[str, object], *, encoding: str, errors: str, preview_rows: int) -> None:
    in_matrix = False
    header_seen = False
    try:
        with _open_text(path, encoding=encoding, errors=errors) as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                lower = stripped.lower()
                if stripped.startswith("!series_matrix_table_begin"):
                    profile["table_begin_line"] = line_number
                    in_matrix = True
                    profile["_saw_series_or_sample_metadata"] = True
                    continue
                if stripped.startswith("!series_matrix_table_end"):
                    profile["table_end_line"] = line_number
                    profile["_saw_matrix_end"] = True
                    break
                if in_matrix:
                    if not header_seen and not stripped.startswith("!"):
                        _handle_matrix_header(stripped, line_number, profile)
                        header_seen = True
                    elif header_seen and not stripped.startswith("!"):
                        _handle_matrix_data_row(stripped, profile, preview_rows=preview_rows)
                    continue
                if stripped.startswith("!"):
                    _handle_metadata_line(stripped, profile)
                elif lower.startswith(("series_", "sample_", "platform_")):
                    _handle_metadata_line("!" + stripped, profile)
    except UnicodeDecodeError:
        raise


def _handle_metadata_line(line: str, profile: dict[str, object]) -> None:
    key, values = _metadata_values(line)
    normalized = _normalize_key(key)
    if not normalized:
        return
    if normalized.startswith(("series_", "sample_", "platform_")):
        profile["_saw_series_or_sample_metadata"] = True
    if normalized == "series_geo_accession":
        profile["series_accession"] = _first(values)
    elif normalized == "series_title":
        profile["series_title"] = _first(values)
    elif normalized == "series_summary":
        profile["series_summary"] = _first(values)
    elif normalized == "series_overall_design":
        profile["overall_design"] = _first(values)
    elif normalized in {"series_platform_id", "sample_platform_id", "platform_geo_accession"}:
        for value in values:
            if value:
                _add_unique(profile, "_platform_accessions", value)
    elif normalized in {"series_organism", "series_taxon", "series_species"}:
        for value in values:
            if value:
                _add_species_evidence(profile, value, key, "medium")
                _add_unique(profile, "_series_species_values", value)
    elif normalized in {"platform_organism", "platform_taxon", "platform_species"}:
        for value in values:
            if value:
                _add_species_evidence(profile, value, key, "medium")
                _add_unique(profile, "_platform_species_values", value)
    if normalized in SAMPLE_METADATA_KEYS:
        profile["_sample_rows"].setdefault(normalized, []).append(values)  # type: ignore[union-attr]
        _add_unique(profile, "sample_metadata_fields", normalized.removeprefix("sample_"))
        if normalized == "sample_organism_ch1":
            for value in values:
                if value:
                    _add_species_evidence(profile, value, key, "high")
                    _add_unique(profile, "_sample_organisms", value)
        if normalized in {
            "sample_characteristics_ch1",
            "sample_source_name_ch1",
            "sample_title",
            "sample_treatment_protocol_ch1",
        }:
            _collect_phenotype_candidates(profile, normalized, values)
        if any(token in normalized for token in CLINICAL_FIELD_TOKENS):
            _add_unique(profile, "clinical_candidate_fields", normalized.removeprefix("sample_"))


def _handle_matrix_header(line: str, line_number: int, profile: dict[str, object]) -> None:
    columns = _split_tab(line)
    if not columns:
        return
    id_column = columns[0]
    sample_columns = [column for column in columns[1:] if column]
    profile["table_header_line"] = line_number
    profile["id_column"] = id_column
    profile["sample_columns"] = sample_columns
    profile["expression_matrix_dimensions"] = {
        "rows": 0,
        "columns": len(columns),
        "sample_columns": len(sample_columns),
    }
    for column in sample_columns:
        if _looks_like_sample_accession(column):
            _add_unique(profile, "sample_accessions", column)


def _handle_matrix_data_row(line: str, profile: dict[str, object], *, preview_rows: int) -> None:
    cells = _split_tab(line)
    if len(cells) < 2:
        return
    dimensions = profile.get("expression_matrix_dimensions")
    if isinstance(dimensions, dict):
        dimensions["rows"] = int(dimensions.get("rows") or 0) + 1
    id_preview = profile.get("_id_preview")
    if isinstance(id_preview, list) and len(id_preview) < preview_rows:
        id_preview.append(cells[0])
    value_preview = profile.get("_value_preview")
    if isinstance(value_preview, list) and len(value_preview) < preview_rows * 10:
        value_preview.extend(cells[1 : min(len(cells), 11)])


def _finalize_profile(profile: dict[str, object]) -> None:
    sample_rows = profile.get("_sample_rows")
    if isinstance(sample_rows, dict):
        metadata_accessions = _flatten_sample_rows(sample_rows.get("sample_geo_accession", []))
        for accession in metadata_accessions:
            _add_unique(profile, "sample_accessions", accession)
        accessions = [str(item) for item in profile.get("sample_accessions", []) or []]
        if not accessions and profile.get("sample_columns"):
            accessions = [str(item) for item in profile.get("sample_columns", []) or [] if _looks_like_sample_accession(str(item))]
            profile["sample_accessions"] = accessions
        profile["sample_count"] = max(len(accessions), len(profile.get("sample_columns", []) or []))
        _map_sample_values(profile, "sample_title", "sample_titles", accessions)
        _map_sample_values(profile, "sample_source_name_ch1", "sample_source_name_ch1", accessions)
        _map_sample_values(profile, "sample_characteristics_ch1", "sample_characteristics_ch1", accessions, multi=True)
    platforms = [str(item) for item in profile.get("_platform_accessions", []) if str(item)]
    if not platforms:
        platforms = _platforms_from_name(str(profile.get("file_name") or ""))
    profile["platform_accessions"] = list(dict.fromkeys(platforms))
    dimensions = profile.get("expression_matrix_dimensions")
    row_count = int(dimensions.get("rows") or 0) if isinstance(dimensions, dict) else 0
    sample_columns = [str(item) for item in profile.get("sample_columns", []) or []]
    id_column = str(profile.get("id_column") or "")
    profile["table_data_row_count"] = row_count
    profile["gsm_column_count"] = len(sample_columns)
    profile["matrix_column_count"] = int(dimensions.get("columns") or 0) if isinstance(dimensions, dict) else 0
    has_matrix_markers = profile.get("table_begin_line") is not None and profile.get("table_header_line") is not None
    id_is_matrix_like = _is_matrix_id_column(id_column)
    profile["expression_matrix_presence"] = bool(has_matrix_markers and id_is_matrix_like and sample_columns and row_count > 0)
    profile["expression_value_type_candidate"] = _expression_value_type(profile.get("_value_preview", []))
    profile["gene_id_type_candidate"] = _gene_id_type(id_column, profile.get("_id_preview", []))
    _add_gene_pattern_species_evidence(profile)
    _add_gene_id_mapping_warnings(profile)
    if profile.get("_sample_organisms"):
        unique_organisms = {str(item).strip().lower() for item in profile.get("_sample_organisms", []) if str(item).strip()}
        if len(unique_organisms) > 1:
            _warning(profile, "Conflicting Sample_organism_ch1 values detected; species requires user review.")
    if profile.get("expression_matrix_presence"):
        profile["requires_user_confirmation"] = True
        profile["can_enter_standardization"] = True
    elif profile.get("sample_metadata_fields") or profile.get("sample_count"):
        profile["requires_user_confirmation"] = True
        profile["can_enter_standardization"] = False
    if not profile.get("_saw_series_or_sample_metadata"):
        _warning(profile, "No Series Matrix metadata markers were parsed.")
    if has_matrix_markers and not profile.get("_saw_matrix_end"):
        _warning(profile, "Series Matrix table end marker was not found; matrix row count may be incomplete.")
    if has_matrix_markers and not profile.get("expression_matrix_presence"):
        _warning(profile, "Series Matrix table markers were found, but no data rows or sample columns confirmed an expression matrix.")
    profile["parser_depth"] = _parser_depth(profile, has_matrix_markers=bool(has_matrix_markers), row_count=row_count)
    for private_key in (
        "_sample_rows",
        "_platform_accessions",
        "_id_preview",
        "_value_preview",
        "_sample_organisms",
        "_series_species_values",
        "_platform_species_values",
        "_saw_series_or_sample_metadata",
        "_saw_matrix_end",
    ):
        profile.pop(private_key, None)


def _parser_depth(profile: dict[str, object], *, has_matrix_markers: bool, row_count: int) -> str:
    if profile.get("expression_matrix_presence") and row_count > 0:
        return "matrix_previewed"
    if has_matrix_markers:
        return "matrix_detected"
    if profile.get("sample_metadata_fields") or profile.get("series_accession") or profile.get("platform_accessions"):
        return "metadata_parsed"
    return "container_only"


def _metadata_values(line: str) -> tuple[str, list[str]]:
    raw = line.strip().lstrip("!")
    if "\t" in raw:
        cells = _split_tab(raw)
        key = cells[0]
        values = [_clean_cell(cell) for cell in cells[1:] if _clean_cell(cell)]
        if not values and "=" in key:
            key, _, value = key.partition("=")
            values = [_clean_cell(value)]
        return key.strip(), values
    key, _, value = raw.partition("=")
    return key.strip(), [_clean_cell(value)] if value.strip() else []


def _map_sample_values(profile: dict[str, object], source_key: str, target_key: str, accessions: list[str], *, multi: bool = False) -> None:
    sample_rows = profile.get("_sample_rows")
    if not isinstance(sample_rows, dict):
        return
    rows = sample_rows.get(source_key, [])
    if not isinstance(rows, list) or not rows:
        return
    mapped = profile.get(target_key)
    if not isinstance(mapped, dict):
        return
    if len(rows) == 1 and isinstance(rows[0], list) and len(rows[0]) >= len(accessions):
        for accession, value in zip(accessions, rows[0], strict=False):
            _assign_sample_value(mapped, accession, str(value), multi=multi)
        return
    if len(rows) >= len(accessions) and all(isinstance(row, list) and len(row) == 1 for row in rows):
        for accession, row in zip(accessions, rows, strict=False):
            _assign_sample_value(mapped, accession, str(row[0]), multi=multi)
        return
    for row in rows:
        if isinstance(row, list) and len(row) == len(accessions):
            for accession, value in zip(accessions, row, strict=False):
                _assign_sample_value(mapped, accession, str(value), multi=multi)


def _assign_sample_value(mapped: dict[object, object], accession: str, value: str, *, multi: bool) -> None:
    if not accession or not value:
        return
    if multi:
        mapped.setdefault(accession, [])
        existing = mapped.get(accession)
        if isinstance(existing, list) and value not in existing:
            existing.append(value)
    else:
        mapped.setdefault(accession, value)


def _collect_phenotype_candidates(profile: dict[str, object], field: str, values: list[str]) -> None:
    normalized_field = field.removeprefix("sample_")
    if field in {"sample_source_name_ch1", "sample_treatment_protocol_ch1"}:
        _add_unique(profile, "phenotype_candidate_fields", normalized_field)
        _add_preview_values(profile, normalized_field, values)
    if field == "sample_title":
        title_hits = [value for value in values if _has_phenotype_token(value)]
        if title_hits:
            _add_unique(profile, "phenotype_candidate_fields", "title_pattern")
            _add_preview_values(profile, "title_pattern", title_hits)
    if field == "sample_characteristics_ch1":
        for value in values:
            key, sep, raw_value = value.partition(":")
            if sep:
                candidate = _normalize_key(key)
                if candidate:
                    _add_unique(profile, "sample_metadata_fields", candidate)
                    if any(token in candidate.replace("_", " ") for token in PHENOTYPE_FIELD_TOKENS):
                        _add_unique(profile, "phenotype_candidate_fields", candidate)
                        _add_preview_values(profile, candidate, [raw_value.strip()])
                    if any(token in candidate for token in CLINICAL_FIELD_TOKENS):
                        _add_unique(profile, "clinical_candidate_fields", candidate)


def _add_preview_values(profile: dict[str, object], field: str, values: list[str]) -> None:
    preview = profile.get("phenotype_candidate_values_preview")
    if not isinstance(preview, dict):
        return
    bucket = preview.setdefault(field, [])
    if not isinstance(bucket, list):
        return
    for value in values:
        cleaned = _clean_cell(value)
        if cleaned and cleaned not in bucket and len(bucket) < 5:
            bucket.append(cleaned)


def _flatten_sample_rows(rows: object) -> list[str]:
    flattened: list[str] = []
    if not isinstance(rows, list):
        return flattened
    for row in rows:
        if isinstance(row, list):
            for value in row:
                cleaned = _clean_cell(value)
                if cleaned:
                    flattened.append(cleaned)
    return flattened


def _expression_value_type(values: object) -> str:
    numeric: list[tuple[str, float]] = []
    if not isinstance(values, list):
        return "unknown"
    for value in values:
        cleaned = _clean_cell(value)
        if not cleaned or cleaned.upper() in {"NA", "N/A", "NAN", "NULL"}:
            continue
        try:
            numeric.append((cleaned, float(cleaned)))
        except ValueError:
            continue
    if not numeric:
        return "unknown"
    if len(numeric) < max(3, min(10, len([item for item in values if _clean_cell(item)]))):
        return "unknown"
    has_decimal = any("." in raw or "e" in raw.lower() for raw, _ in numeric)
    has_negative = any(value < 0 for _, value in numeric)
    all_non_negative_integer = all(value >= 0 and value.is_integer() and re.fullmatch(r"\d+(?:\.0+)?", raw) for raw, value in numeric)
    if all_non_negative_integer and not has_decimal and not has_negative:
        return "count_like_candidate"
    if has_decimal or has_negative:
        return "normalized_or_log_expression"
    return "unknown"


def _gene_id_type(id_column: str, values: object) -> str:
    normalized_id = _normalize_key(id_column)
    preview = [_clean_cell(value) for value in values] if isinstance(values, list) else []
    if "ensembl" in normalized_id or _ratio(preview, lambda value: re.match(r"ENS[A-Z]*G\d+", value, flags=re.IGNORECASE) is not None) >= 0.6:
        return "ensembl_id"
    if "entrez" in normalized_id or _ratio(preview, lambda value: re.fullmatch(r"\d{3,12}", value) is not None) >= 0.6:
        return "entrez_id"
    if normalized_id in {"id_ref", "ref", "probe", "probe_id"}:
        if _ratio(preview, _looks_like_probe_id) >= 0.4 or normalized_id == "id_ref":
            return "probe_id"
        return "unknown"
    if "gene_symbol" in normalized_id or normalized_id == "symbol":
        return "gene_symbol"
    if "gene" in normalized_id and _ratio(preview, _looks_like_gene_symbol) >= 0.6:
        return "gene_symbol"
    return "unknown"


def _add_gene_pattern_species_evidence(profile: dict[str, object]) -> None:
    gene_type = str(profile.get("gene_id_type_candidate") or "")
    if gene_type != "ensembl_id":
        return
    id_preview = [str(value) for value in profile.get("_id_preview", []) if str(value)]
    if not id_preview:
        return
    if sum(1 for value in id_preview if value.upper().startswith("ENSMUSG")) >= max(1, len(id_preview) // 2):
        _add_species_evidence(profile, "Mus musculus", "gene_id_pattern", "low")
    elif sum(1 for value in id_preview if value.upper().startswith("ENSG")) >= max(1, len(id_preview) // 2):
        _add_species_evidence(profile, "Homo sapiens", "gene_id_pattern", "low")


def _add_gene_id_mapping_warnings(profile: dict[str, object]) -> None:
    gene_type = str(profile.get("gene_id_type_candidate") or "unknown")
    if gene_type in {"probe_id", "unknown"} and profile.get("expression_matrix_presence"):
        _warning(profile, "ID_REF may be a platform probe ID; platform annotation or ID mapping must be confirmed before gene-level analysis.")
    value_type = str(profile.get("expression_value_type_candidate") or "unknown")
    if value_type == "unknown" and profile.get("expression_matrix_presence"):
        _warning(profile, "Expression value type is unknown and must be confirmed during standardization.")
    elif value_type == "count_like_candidate":
        _warning(profile, "Expression values look count-like, but raw count status requires user confirmation.")


def _add_species_evidence(profile: dict[str, object], species: str, source_field: str, confidence: str) -> None:
    cleaned = _clean_cell(species)
    if not cleaned:
        return
    evidence = profile.get("species_evidence")
    if not isinstance(evidence, list):
        return
    payload = {
        "species": cleaned,
        "source_field": source_field,
        "source_file": str(profile.get("file_name") or ""),
        "confidence": confidence,
    }
    if payload not in evidence:
        evidence.append(payload)


def _is_matrix_id_column(value: str) -> bool:
    normalized = _normalize_key(value)
    return normalized in {"id_ref", "id", "gene", "gene_id", "gene_symbol", "symbol", "probe", "probe_id", "feature_id"} or any(
        token in normalized for token in ("ensembl", "entrez", "transcript")
    )


def _looks_like_sample_accession(value: str) -> bool:
    normalized = _clean_cell(value).lower()
    return normalized.startswith(("gsm", "srr", "err", "drr")) or re.fullmatch(r"[a-z]{0,3}\d+[a-z]?(?:_\d+)?", normalized) is not None


def _looks_like_probe_id(value: str) -> bool:
    cleaned = _clean_cell(value)
    return re.match(r"\d+_[a-z]+_at$", cleaned, flags=re.IGNORECASE) is not None or re.match(r"[A-Z]{2,}\d+", cleaned) is not None


def _looks_like_gene_symbol(value: str) -> bool:
    return re.fullmatch(r"[A-Za-z][A-Za-z0-9.-]{1,12}", _clean_cell(value)) is not None


def _has_phenotype_token(value: str) -> bool:
    lowered = value.lower()
    return any(token.replace("_", " ") in lowered for token in PHENOTYPE_FIELD_TOKENS)


def _ratio(values: list[str], predicate) -> float:
    sample = [value for value in values if value]
    if not sample:
        return 0.0
    return sum(1 for value in sample if predicate(value)) / len(sample)


def _platforms_from_name(name: str) -> list[str]:
    return list(dict.fromkeys(match.upper() for match in re.findall(r"GPL\d+", name, flags=re.IGNORECASE)))


def _open_text(path: Path, *, encoding: str, errors: str):
    if path.name.lower().endswith(".gz"):
        return gzip.open(path, "rt", encoding=encoding, errors=errors)
    return path.open("r", encoding=encoding, errors=errors)


def _split_tab(line: str) -> list[str]:
    try:
        return [_clean_cell(cell) for cell in next(csv.reader([line], delimiter="\t"))]
    except csv.Error:
        return [_clean_cell(cell) for cell in line.split("\t")]


def _clean_cell(value: object) -> str:
    return str(value).strip().strip('"').strip("'")


def _normalize_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _first(values: list[str]) -> str:
    return values[0] if values else ""


def _add_unique(profile: dict[str, object], key: str, value: str) -> None:
    if not value:
        return
    values = profile.setdefault(key, [])
    if isinstance(values, list) and value not in values:
        values.append(value)


def _warning(profile: dict[str, object], value: str) -> None:
    _add_unique(profile, "warnings", value)
