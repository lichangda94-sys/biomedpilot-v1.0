from __future__ import annotations

import csv
import gzip
import re
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree


GROUP_PREVIEW_REPORT = Path("logs") / "recognition" / "group_preview_report.json"

GROUP_FIELD_PRIORITY = (
    "group",
    "condition",
    "treatment",
    "response",
    "disease_state",
    "phenotype",
    "benign_malignant",
    "malignancy",
    "histology",
    "disease",
    "diagnosis",
    "tumor_status",
    "genotype",
    "tissue",
    "sample_type",
    "source_name_ch1",
    "title_pattern",
    "characteristics_ch1",
)
EXCLUDED_GROUP_FIELDS = {
    "sample",
    "sample_id",
    "sampleid",
    "geo_accession",
    "accession",
    "gsm",
    "batch",
    "platform",
    "barcode",
    "file",
    "filename",
    "replicate",
    "replicate_id",
    "run",
    "run_accession",
    "library_strategy",
    "cell_line",
    "time_point",
    "extract_protocol_ch1",
    "growth_protocol_ch1",
    "data_processing",
    "sex",
    "gender",
    "age",
}
SAMPLE_ID_FIELDS = ("sample_id", "sample", "geo_accession", "sample_geo_accession", "gsm")
CELL_LINE_PATTERNS = (
    "a375",
    "cal-62",
    "cal62",
    "tpc-1",
    "tpc1",
    "bcpap",
    "8505c",
    "k1",
    "sw1736",
    "ftc-133",
    "ftc133",
    "mda-mb-231",
    "mdamb231",
    "mcf-7",
    "mcf7",
    "a549",
    "h1299",
    "hct116",
    "ht29",
    "hela",
    "hek293",
    "jurkat",
    "u87",
    "u251",
    "ln229",
    "t47d",
)
SEMANTIC_GROUP_LABELS = {
    "normal",
    "control",
    "treated",
    "tumor",
    "case",
    "resistant",
    "sensitive",
    "mutant",
    "wild_type",
    "knockout",
    "metastatic",
    "primary",
    "benign",
    "malignant",
}


def build_group_preview_report(project_root: str | Path, recognition_records: list[dict[str, object]]) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    file_previews = []
    for record in recognition_records:
        path = Path(str(record.get("original_path") or "")).expanduser()
        if not path.is_absolute():
            path = root / path
        if not path.exists() or not path.is_file():
            continue
        roles = {str(role) for role in record.get("recognized_roles", []) or []}
        primary = str(record.get("recognized_type") or "")
        if primary == "geo_soft_container":
            preview = _preview_geo_family_soft(path)
        elif primary == "geo_series_matrix_container":
            preview = _preview_geo_series_matrix(path)
        elif roles & {"sample_metadata", "clinical_metadata", "phenotype_metadata"} or primary in {"sample_metadata", "clinical_metadata"}:
            preview = _preview_metadata_table(path)
        elif roles & {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix"} or primary in {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix"}:
            preview = _preview_expression_matrix(path)
        else:
            continue
        if preview:
            preview["source_file"] = str(path)
            file_previews.append(preview)

    top = _select_top_preview(file_previews)
    if any(_record_has_comparison_config(record) for record in recognition_records):
        top["status"] = "confirmed_comparison_exists"
        top["missing_group_reason"] = ""
        top["warnings"] = list(dict.fromkeys([*top.get("warnings", []), "已存在正式比较组设置。"]))
    top["file_previews"] = file_previews
    return top


def _record_has_comparison_config(record: dict[str, object]) -> bool:
    roles = {str(role) for role in record.get("recognized_roles", []) or []}
    return str(record.get("recognized_type") or "") == "comparison_config" or "comparison_config" in roles


def _empty_preview(reason: str = "未在样本信息中识别到明确分组字段") -> dict[str, object]:
    return {
        "sample_count": 0,
        "expression_sample_count": 0,
        "metadata_sample_count": 0,
        "sample_id_match_status": "not_available",
        "candidate_group_fields": [],
        "selected_preview_field": "",
        "group_count": 0,
        "group_sizes": {},
        "sample_group_assignments": {},
        "confidence": "low",
        "status": "no_group_detected",
        "warnings": [],
        "source_file": "",
        "missing_group_reason": reason,
    }


def _select_top_preview(previews: list[dict[str, object]]) -> dict[str, object]:
    if not previews:
        return _empty_preview()
    ranked = sorted(previews, key=_preview_rank, reverse=True)
    top = dict(ranked[0])
    top["status"] = "preview_only" if top.get("group_count", 0) else "no_group_detected"
    if top["status"] == "no_group_detected" and not top.get("missing_group_reason"):
        top["missing_group_reason"] = "未在样本信息中识别到明确分组字段"
    return top


def _preview_rank(preview: dict[str, object]) -> tuple[int, int, int]:
    confidence = {"high": 3, "medium": 2, "low": 1}.get(str(preview.get("confidence") or ""), 0)
    group_count = int(preview.get("group_count") or 0)
    usable_groups = 1 if 2 <= group_count <= 8 else 0
    sample_count = int(preview.get("sample_count") or 0)
    return usable_groups, confidence, sample_count


def _preview_geo_series_matrix(path: Path) -> dict[str, object]:
    sample_ids: list[str] = []
    titles: list[str] = []
    metadata_fields: dict[str, list[str]] = {}
    expression_samples: list[str] = []
    try:
        with _open_text(path) as handle:
            in_table = False
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("!series_matrix_table_begin"):
                    in_table = True
                    continue
                if stripped.startswith("!series_matrix_table_end"):
                    break
                if in_table and not expression_samples:
                    cells = _clean_cells(_split_line(stripped, "\t"))
                    if cells and _normalize(cells[0]) == "id_ref":
                        expression_samples = [cell for cell in cells[1:] if _looks_like_sample_id(cell)]
                    continue
                key, values = _series_metadata_values(stripped)
                normalized = _normalize(key)
                if normalized == "sample_geo_accession":
                    sample_ids.extend(values)
                elif normalized == "sample_title":
                    titles.extend(values)
                elif normalized in {"sample_source_name_ch1", "sample_treatment_protocol_ch1"}:
                    field = normalized.replace("sample_", "")
                    metadata_fields.setdefault(field, []).extend(values)
                elif normalized == "sample_extract_protocol_ch1":
                    continue
                elif normalized == "sample_characteristics_ch1":
                    _collect_characteristics(metadata_fields, values)
    except OSError:
        return _empty_preview("无法读取文件内容")
    sample_ids = list(dict.fromkeys(sample_ids))
    metadata_sample_count = max(len(sample_ids), len(titles), len(expression_samples), 0)
    preview = _preview_from_fields(
        metadata_fields,
        metadata_sample_count=metadata_sample_count,
        expression_samples=expression_samples,
        metadata_sample_ids=sample_ids,
        default_confidence="medium",
        reason="未在 GEO Series Matrix 样本信息中识别到明确分组字段",
    )
    if not preview.get("sample_count"):
        preview["sample_count"] = max(metadata_sample_count, len(expression_samples))
    return preview


def _preview_geo_family_soft(path: Path) -> dict[str, object]:
    sample_ids: list[str] = []
    titles: list[str] = []
    metadata_fields: dict[str, list[str]] = {}
    expression_samples: list[str] = []
    current_sample = ""
    current_has_table = False
    try:
        with _open_text(path) as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("^SAMPLE"):
                    if current_sample and current_has_table:
                        expression_samples.append(current_sample)
                    current_sample = _clean_cell(stripped.partition("=")[2]) or current_sample
                    current_has_table = False
                    if current_sample:
                        sample_ids.append(current_sample)
                    continue
                if stripped.startswith("!sample_table_begin"):
                    current_has_table = True
                    continue
                key, _, raw_value = stripped.partition("=")
                if not raw_value:
                    continue
                normalized = _normalize(key.lstrip("!"))
                value = _clean_cell(raw_value)
                if normalized == "sample_geo_accession":
                    if value:
                        sample_ids.append(value)
                        current_sample = value
                elif normalized == "sample_title":
                    titles.append(value)
                    title_group = _coarse_group_from_text(value)
                    if title_group:
                        metadata_fields.setdefault("title_pattern", []).append(title_group)
                elif normalized in {"sample_source_name_ch1", "sample_treatment_protocol_ch1"}:
                    field = normalized.replace("sample_", "")
                    group = _clean_group_value(value)
                    if group:
                        metadata_fields.setdefault(field, []).append(group)
                    coarse = _coarse_group_from_text(value)
                    if coarse:
                        metadata_fields.setdefault("title_pattern", []).append(coarse)
                elif normalized == "sample_extract_protocol_ch1":
                    continue
                elif normalized == "sample_characteristics_ch1":
                    _collect_characteristics(metadata_fields, [value])
                    coarse = _coarse_group_from_text(value)
                    if coarse:
                        metadata_fields.setdefault("title_pattern", []).append(coarse)
            if current_sample and current_has_table:
                expression_samples.append(current_sample)
    except OSError:
        return _empty_preview("无法读取文件内容")
    sample_ids = list(dict.fromkeys(sample_ids))
    metadata_sample_count = max(len(sample_ids), len(titles), len(expression_samples), 0)
    preview = _preview_from_fields(
        metadata_fields,
        metadata_sample_count=metadata_sample_count,
        expression_samples=expression_samples,
        metadata_sample_ids=sample_ids,
        default_confidence="medium",
        reason="未在 GEO family SOFT 样本信息中识别到明确分组字段",
    )
    if not preview.get("sample_count"):
        preview["sample_count"] = max(metadata_sample_count, len(expression_samples))
    return preview


def _series_metadata_values(line: str) -> tuple[str, list[str]]:
    if "\t" in line:
        cells = _clean_cells(_split_line(line, "\t"))
        return cells[0].lstrip("!") if cells else "", [cell for cell in cells[1:] if cell]
    key, _, value = line.partition("=")
    return key.strip().lstrip("!"), [_clean_cell(value)] if value.strip() else []


def _collect_characteristics(fields: dict[str, list[str]], values: list[str]) -> None:
    for value in values:
        raw = _clean_cell(value)
        parts = [part.strip() for part in re.split(r";\s*", raw) if part.strip()] or [raw]
        parsed_any = False
        for part in parts:
            label, sep, content = part.partition(":")
            if sep:
                parsed_any = True
                field = _normalize(label)
                if _is_group_candidate_field(field):
                    group = _clean_group_value(content)
                    if group:
                        fields.setdefault(field, []).append(group)
                group = _clean_group_value(part)
                if group:
                    fields.setdefault("characteristics_ch1", []).append(group)
        if not parsed_any:
            group = _clean_group_value(raw)
            if group:
                fields.setdefault("characteristics_ch1", []).append(group)


def _preview_metadata_table(path: Path) -> dict[str, object]:
    rows = _read_table_rows(path)
    if len(rows) < 2:
        return _empty_preview("样本信息表为空或表头不足")
    header = [_normalize(cell) for cell in rows[0]]
    data = [row for row in rows[1:] if any(_clean_cell(cell) for cell in row)]
    fields: dict[str, list[str]] = {}
    sample_ids: list[str] = []
    for row in data:
        padded = row + [""] * max(0, len(header) - len(row))
        for index, field in enumerate(header):
            value = _clean_cell(padded[index]) if index < len(padded) else ""
            if not value:
                continue
            if field in SAMPLE_ID_FIELDS:
                sample_ids.append(value)
            if _is_group_candidate_field(field):
                group = _clean_group_value(value)
                if group:
                    fields.setdefault(field, []).append(group)
            elif field == "characteristics_ch1":
                _collect_characteristics(fields, [value])
    return _preview_from_fields(
        fields,
        metadata_sample_count=len(data),
        expression_samples=[],
        metadata_sample_ids=sample_ids,
        default_confidence="high",
        reason="未在样本信息表中识别到明确分组字段",
    )


def _preview_expression_matrix(path: Path) -> dict[str, object]:
    rows = _read_table_rows(path, max_rows=1)
    if not rows:
        return _empty_preview("表达矩阵表头为空")
    header = [_clean_cell(cell) for cell in rows[0]]
    if len(header) < 3:
        return _empty_preview("表达矩阵样本列不足")
    sample_columns = [column for column in header[1:] if _looks_like_expression_sample_column(column)]
    groups = [_group_from_sample_column(column) for column in sample_columns]
    clean_groups = [group for group in groups if group]
    group_sizes = _valid_group_sizes(clean_groups)
    status = "preview_only" if group_sizes else "no_group_detected"
    return {
        "sample_count": len(sample_columns),
        "expression_sample_count": len(sample_columns),
        "metadata_sample_count": 0,
        "sample_id_match_status": "not_available",
        "candidate_group_fields": ["expression_column_pattern"] if group_sizes else [],
        "selected_preview_field": "expression_column_pattern" if group_sizes else "",
        "group_count": len(group_sizes),
        "group_sizes": group_sizes,
        "sample_group_assignments": {
            sample: group for sample, group in zip(sample_columns, groups, strict=False) if sample and group
        },
        "confidence": "low",
        "status": status,
        "warnings": ["仅根据表达矩阵列名推断，不能作为正式比较组。"] if group_sizes else [],
        "source_file": str(path),
        "missing_group_reason": "" if group_sizes else "表达矩阵列名中没有稳定的分组模式",
    }


def _preview_from_fields(
    fields: dict[str, list[str]],
    *,
    metadata_sample_count: int,
    expression_samples: list[str],
    metadata_sample_ids: list[str],
    default_confidence: str,
    reason: str,
) -> dict[str, object]:
    candidates: list[tuple[str, dict[str, int], str, list[str]]] = []
    for field in _ordered_fields(fields):
        values = fields.get(field, [])
        if metadata_sample_count and len(values) != metadata_sample_count:
            continue
        group_sizes = _valid_group_sizes(values)
        if group_sizes:
            confidence, warnings = _preview_confidence_for_field(field, group_sizes, default_confidence)
            candidates.append((field, group_sizes, confidence, warnings))
    expression_sample_count = len(expression_samples)
    sample_count = max(metadata_sample_count, expression_sample_count, len(metadata_sample_ids))
    if not candidates:
        preview = _empty_preview(reason)
        preview.update(
            {
                "sample_count": sample_count,
                "expression_sample_count": expression_sample_count,
                "metadata_sample_count": metadata_sample_count,
                "sample_id_match_status": _sample_id_match_status(expression_samples, metadata_sample_ids),
            }
        )
        return preview
    selected_field, group_sizes, confidence, confidence_warnings = candidates[0]
    selected_values = [_clean_group_value(value) for value in fields.get(selected_field, [])]
    sample_group_assignments = (
        {
            sample_id: group
            for sample_id, group in zip(metadata_sample_ids, selected_values, strict=False)
            if sample_id and group and group in group_sizes
        }
        if metadata_sample_ids and len(metadata_sample_ids) == len(selected_values)
        else {}
    )
    return {
        "sample_count": sample_count,
        "expression_sample_count": expression_sample_count,
        "metadata_sample_count": metadata_sample_count,
        "sample_id_match_status": _sample_id_match_status(expression_samples, metadata_sample_ids),
        "candidate_group_fields": [field for field, _sizes, _confidence, _warnings in candidates],
        "selected_preview_field": selected_field,
        "group_count": len(group_sizes),
        "group_sizes": group_sizes,
        "sample_group_assignments": sample_group_assignments,
        "confidence": confidence,
        "status": "preview_only",
        "warnings": [*(["检测到多个可能分组字段，请选择用于分析的比较组。"] if len(candidates) > 1 else []), *confidence_warnings],
        "source_file": "",
        "missing_group_reason": "",
    }


def _ordered_fields(fields: dict[str, list[str]]) -> list[str]:
    return [field for field in GROUP_FIELD_PRIORITY if field in fields] + sorted(field for field in fields if field not in GROUP_FIELD_PRIORITY)


def _valid_group_sizes(values: list[str]) -> dict[str, int]:
    clean_values = [_clean_group_value(value) for value in values if _clean_group_value(value)]
    clean_values = [value for value in clean_values if not _is_invalid_group_value(value)]
    if not clean_values:
        return {}
    counts = Counter(clean_values)
    if len(counts) < 2 or len(counts) > 8:
        return {}
    if len(counts) == len(clean_values) and len(counts) > 2:
        return {}
    if not _has_semantic_group(counts):
        return {}
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _preview_confidence_for_field(field: str, group_sizes: dict[str, int], default_confidence: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    confidence = default_confidence
    if field in {"title_pattern", "source_name_ch1", "description"} and confidence == "high":
        confidence = "medium"
    if field in {"expression_column_pattern"}:
        confidence = "low"
    total = sum(group_sizes.values())
    if any(size < 2 for size in group_sizes.values()) and total > 4:
        confidence = "low"
        warnings.append("部分候选组样本数过少，只能作为可能分组。")
    if any(_is_low_confidence_group_value(value) for value in group_sizes):
        confidence = "low"
        warnings.append("候选组包含细胞系、剂量、时间点或技术标签，只能作为可能分组。")
    if not _has_clear_experimental_pair(set(group_sizes)):
        confidence = "low" if confidence != "high" else "medium"
        warnings.append("候选组标签不是明确医学或实验设计分组，正式分析前需人工确认。")
    return confidence, list(dict.fromkeys(warnings))


def _has_semantic_group(values: Counter[str] | dict[str, int]) -> bool:
    labels = set(values.keys())
    return bool(labels & SEMANTIC_GROUP_LABELS) or _has_clear_experimental_pair(labels)


def _has_clear_experimental_pair(labels: set[str]) -> bool:
    pairs = (
        {"tumor", "normal"},
        {"treated", "control"},
        {"resistant", "sensitive"},
        {"mutant", "wild_type"},
        {"malignant", "benign"},
        {"tumor", "benign"},
        {"metastatic", "primary"},
    )
    return any(pair <= labels for pair in pairs)


def _is_invalid_group_value(value: str) -> bool:
    lowered = str(value or "").strip().lower()
    if not lowered:
        return True
    return _is_accession_or_technical_label(lowered) or _is_cell_line_label(lowered) or _is_numeric_dose_or_time_label(lowered) or _is_replicate_or_batch_label(lowered)


def _is_low_confidence_group_value(value: str) -> bool:
    lowered = str(value or "").strip().lower()
    return _is_invalid_group_value(lowered) or _contains_cell_line(lowered) or _is_numeric_dose_or_time_label(lowered) or _is_replicate_or_batch_label(lowered)


def _sample_id_match_status(expression_samples: list[str], metadata_sample_ids: list[str]) -> str:
    expression = {_normalize_sample_id(value) for value in expression_samples if value}
    metadata = {_normalize_sample_id(value) for value in metadata_sample_ids if value}
    if not expression or not metadata:
        return "not_available"
    if expression == metadata:
        return "matched"
    overlap = expression & metadata
    return "partial" if overlap else "mismatch"


def _is_group_candidate_field(field: str) -> bool:
    if not field or field in EXCLUDED_GROUP_FIELDS:
        return False
    if field in GROUP_FIELD_PRIORITY:
        return True
    return any(
        token in field
        for token in (
            "group",
            "condition",
            "treatment",
            "disease_state",
            "phenotype",
            "source_name",
            "characteristics",
            "disease",
            "diagnosis",
            "tumor",
            "benign",
            "malignant",
            "malignancy",
            "histology",
            "genotype",
            "tissue",
            "sample_type",
            "cell_line",
        )
    )


def _read_table_rows(path: Path, *, max_rows: int = 250) -> list[list[str]]:
    if path.suffix.lower() == ".xlsx":
        return _xlsx_rows(path, max_rows=max_rows)
    try:
        with _open_text(path) as handle:
            lines = [line.rstrip("\n") for _, line in zip(range(max_rows), handle) if line.strip()]
    except OSError:
        return []
    if not lines:
        return []
    delimiter = _detect_delimiter(path, lines[:20])
    return [_clean_cells(_split_line(line.lstrip("#"), delimiter)) for line in lines if not line.startswith("!") and not line.startswith("^")]


def _open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8", errors="ignore") if path.name.lower().endswith(".gz") else path.open("r", encoding="utf-8", errors="ignore")


def _detect_delimiter(path: Path, lines: list[str]) -> str:
    suffixes = [suffix.lower() for suffix in path.suffixes]
    if suffixes and suffixes[-1] == ".gz":
        suffixes = suffixes[:-1]
    if suffixes and suffixes[-1] == ".csv":
        return ","
    return "\t" if sum(line.count("\t") for line in lines) >= sum(line.count(",") for line in lines) else ","


def _split_line(line: str, delimiter: str) -> list[str]:
    try:
        return next(csv.reader([line], delimiter=delimiter))
    except csv.Error:
        return line.split(delimiter)


def _clean_cells(values: list[str]) -> list[str]:
    return [_clean_cell(value) for value in values]


def _clean_cell(value: object) -> str:
    return str(value).strip().strip('"').strip("'")


def _clean_group_value(value: object) -> str:
    text = _clean_cell(value)
    text = re.sub(r"\s+", " ", text)
    cleaned = text.strip().lower().replace("μ", "u")
    if not cleaned:
        return ""
    canonical = _canonical_semantic_group(cleaned)
    if canonical:
        return canonical
    cleaned = _strip_cell_line_tokens(cleaned)
    cleaned = re.sub(r"\b(rep|replicate|biological replicate|technical replicate)[ _.-]?\d+\b", " ", cleaned)
    cleaned = re.sub(r"\b\d+(?:\.\d+)?\s*(nm|um|mm|ug/ml|mg/ml|mg/kg|h|hr|hrs|hour|hours|day|days|week|weeks)\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" _.-")
    if _is_invalid_group_value(cleaned):
        return ""
    return cleaned


def _normalize(value: object) -> str:
    return re.sub(r"_+", "_", "".join(character.lower() if character.isalnum() else "_" for character in str(value))).strip("_")


def _normalize_sample_id(value: object) -> str:
    return _clean_cell(value).strip().strip('"').upper()


def _canonical_semantic_group(text: str) -> str:
    normalized = _normalize_group_text(text)
    phrase_map = (
        ("adjacent normal", "normal"),
        ("para cancer", "normal"),
        ("para-cancer", "normal"),
        ("wild type", "wild_type"),
        ("knockout", "knockout"),
        ("resistant", "resistant"),
        ("sensitive", "sensitive"),
        ("metastatic", "metastatic"),
        ("recurrent", "recurrent"),
        ("primary", "primary"),
        ("malignant", "malignant"),
        ("benign", "benign"),
        ("normal", "normal"),
        ("healthy", "normal"),
        ("vehicle", "control"),
        ("dmso", "control"),
        ("mock", "control"),
        ("untreated", "control"),
        ("control", "control"),
        ("treated", "treated"),
        ("treatment", "treated"),
        ("mutant", "mutant"),
        ("mutated", "mutant"),
        ("tumour", "tumor"),
        ("tumor", "tumor"),
        ("cancer", "tumor"),
        ("carcinoma", "tumor"),
        ("case", "case"),
        ("disease", "case"),
    )
    for phrase, label in phrase_map:
        if _token_in_text(phrase, normalized):
            return label
    return ""


def _normalize_group_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower().replace("_", " ").strip())


def _token_in_text(token: str, text: str) -> bool:
    return re.search(rf"(^|[^a-z0-9]){re.escape(token.lower())}([^a-z0-9]|$)", text.lower()) is not None


def _is_accession_or_technical_label(text: str) -> bool:
    value = text.strip()
    if re.fullmatch(r"(gsm|gse|gpl|srr|srx|srs|err|drx)\w+", value, flags=re.IGNORECASE):
        return True
    return any(_token_in_text(token, value) for token in ("batch", "lane", "run", "library", "barcode", "platform"))


def _contains_cell_line(text: str) -> bool:
    normalized = _normalize_group_text(text)
    compact = normalized.replace("-", "").replace("_", "").replace(" ", "")
    for pattern in CELL_LINE_PATTERNS:
        compact_pattern = pattern.replace("-", "").replace("_", "").replace(" ", "")
        if re.search(rf"(^|[^a-z0-9]){re.escape(pattern)}([^a-z0-9]|$)", normalized) or compact_pattern in compact:
            return True
    return False


def _strip_cell_line_tokens(text: str) -> str:
    cleaned = _normalize_group_text(text)
    for pattern in CELL_LINE_PATTERNS:
        cleaned = re.sub(rf"(^|[^a-z0-9]){re.escape(pattern)}([^a-z0-9]|$)", " ", cleaned)
        cleaned = cleaned.replace(pattern.replace("-", ""), " ")
    cleaned = re.sub(r"\b(cell|cells|cell line|line)\b", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _is_cell_line_label(text: str) -> bool:
    if not _contains_cell_line(text):
        return False
    stripped = _strip_cell_line_tokens(text)
    return not stripped


def _is_numeric_dose_or_time_label(text: str) -> bool:
    value = _normalize_group_text(text).replace("μ", "u")
    if re.fullmatch(r"\d+(?:\.\d+)?", value):
        return True
    if re.fullmatch(r"\d+(?:\.\d+)?\s*(nm|um|mm|ug/ml|mg/ml|mg/kg|h|hr|hrs|hour|hours|day|days|week|weeks)", value):
        return True
    if re.search(r"\b\d+(?:\.\d+)?\s*(nm|um|mm|mg/kg|h|hr|hrs|hours|day|week)\b", value):
        return _canonical_semantic_group(value) == ""
    return False


def _is_replicate_or_batch_label(text: str) -> bool:
    value = _normalize_group_text(text)
    if re.fullmatch(r"(rep|replicate|biological replicate)[ _.-]?\d+", value):
        return True
    return any(_token_in_text(token, value) for token in ("replicate", "biological replicate", "technical replicate", "batch", "lane", "barcode"))


def _looks_like_sample_id(value: str) -> bool:
    return bool(re.match(r"^(GSM|SRR|ERR|DRR|TCGA)[A-Z0-9_.-]+$", _clean_cell(value), flags=re.IGNORECASE))


def _looks_like_expression_sample_column(value: str) -> bool:
    normalized = _normalize(value)
    if not normalized:
        return False
    if normalized in {"gene", "gene_id", "symbol", "id_ref", "probe", "ensembl"}:
        return False
    return True


def _group_from_sample_column(value: str) -> str:
    normalized = _normalize(value)
    for token in ("control", "treated", "treatment", "case", "tumor", "normal", "disease", "vehicle", "untreated"):
        if normalized == token or normalized.startswith(f"{token}_") or normalized.endswith(f"_{token}"):
            return {"untreated": "control", "vehicle": "control", "treatment": "treated"}.get(token, token)
    match = re.match(r"([a-z]+)[_.-]?\d+$", normalized)
    if match and match.group(1) in {"control", "treated", "case", "tumor", "normal"}:
        return match.group(1)
    return ""


def _coarse_group_from_text(value: str) -> str:
    normalized = _normalize_group_text(value)
    if not normalized:
        return ""
    token_map = (
        ("normal", "normal"),
        ("control", "control"),
        ("healthy", "normal"),
        ("dmso", "control"),
        ("mock", "control"),
        ("vehicle", "control"),
        ("untreated", "control"),
        ("treated", "treated"),
        ("treatment", "treated"),
        ("tumor", "tumor"),
        ("tumour", "tumor"),
        ("cancer", "tumor"),
        ("carcinoma", "tumor"),
        ("case", "case"),
        ("disease", "case"),
    )
    if _contains_cell_line(normalized) and not any(_token_in_text(token, normalized) for token, _label in token_map):
        return ""
    matches = [label for token, label in token_map if _token_in_text(token, normalized)]
    unique = list(dict.fromkeys(matches))
    if len(unique) == 1:
        return unique[0]
    if "normal" in unique and "tumor" in unique:
        return ""
    return unique[0] if unique else ""


def _xlsx_rows(path: Path, *, max_rows: int = 250) -> list[list[str]]:
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if "xl/worksheets/sheet1.xml" not in names:
                return []
            shared = _xlsx_shared_strings(archive, names)
            root = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
            rows: list[list[str]] = []
            for row in root.findall(".//{*}sheetData/{*}row")[:max_rows]:
                values_by_col: dict[int, str] = {}
                for cell in row.findall("{*}c"):
                    values_by_col[_xlsx_column_index(str(cell.attrib.get("r", "")))] = _xlsx_cell_value(cell, shared)
                if values_by_col:
                    rows.append([values_by_col.get(index, "") for index in range(max(values_by_col) + 1)])
            return rows
    except Exception:
        return []


def _xlsx_shared_strings(archive: zipfile.ZipFile, names: set[str]) -> list[str]:
    if "xl/sharedStrings.xml" not in names:
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    return ["".join(node.text or "" for node in item.findall(".//{*}t")) for item in root.findall("{*}si")]


def _xlsx_cell_value(cell: ElementTree.Element, shared: list[str]) -> str:
    value_node = cell.find("{*}v")
    if value_node is None or value_node.text is None:
        return "".join(node.text or "" for node in cell.findall(".//{*}t")).strip()
    raw = value_node.text
    if cell.attrib.get("t") == "s":
        try:
            return shared[int(raw)].strip()
        except (ValueError, IndexError):
            return ""
    return raw.strip()


def _xlsx_column_index(reference: str) -> int:
    letters = "".join(character for character in reference if character.isalpha())
    index = 0
    for character in letters.upper():
        index = index * 26 + ord(character) - ord("A") + 1
    return max(index - 1, 0)
