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
    "disease_state",
    "phenotype",
    "source_name_ch1",
    "disease",
    "genotype",
    "tissue",
    "cell_line",
    "time_point",
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
    "sex",
    "gender",
    "age",
}
SAMPLE_ID_FIELDS = ("sample_id", "sample", "geo_accession", "sample_geo_accession", "gsm")


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
        if primary == "geo_series_matrix_container":
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
                elif normalized in {"sample_source_name_ch1", "sample_treatment_protocol_ch1", "sample_extract_protocol_ch1"}:
                    field = normalized.replace("sample_", "")
                    metadata_fields.setdefault(field, []).extend(values)
                elif normalized == "sample_characteristics_ch1":
                    _collect_characteristics(metadata_fields, values)
    except OSError:
        return _empty_preview("无法读取文件内容")
    metadata_sample_count = max(len(sample_ids), *(len(values) for values in metadata_fields.values()), len(titles), 0)
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


def _series_metadata_values(line: str) -> tuple[str, list[str]]:
    if "\t" in line:
        cells = _clean_cells(_split_line(line, "\t"))
        return cells[0].lstrip("!") if cells else "", [cell for cell in cells[1:] if cell]
    key, _, value = line.partition("=")
    return key.strip().lstrip("!"), [_clean_cell(value)] if value.strip() else []


def _collect_characteristics(fields: dict[str, list[str]], values: list[str]) -> None:
    for value in values:
        raw = _clean_cell(value)
        label, sep, content = raw.partition(":")
        if sep:
            field = _normalize(label)
            if _is_group_candidate_field(field):
                fields.setdefault(field, []).append(_clean_group_value(content))
            fields.setdefault("characteristics_ch1", []).append(raw)
        else:
            fields.setdefault("characteristics_ch1", []).append(raw)


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
                fields.setdefault(field, []).append(_clean_group_value(value))
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
    candidates: list[tuple[str, dict[str, int]]] = []
    for field in _ordered_fields(fields):
        group_sizes = _valid_group_sizes(fields.get(field, []))
        if group_sizes:
            candidates.append((field, group_sizes))
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
    selected_field, group_sizes = candidates[0]
    return {
        "sample_count": sample_count,
        "expression_sample_count": expression_sample_count,
        "metadata_sample_count": metadata_sample_count,
        "sample_id_match_status": _sample_id_match_status(expression_samples, metadata_sample_ids),
        "candidate_group_fields": [field for field, _sizes in candidates],
        "selected_preview_field": selected_field,
        "group_count": len(group_sizes),
        "group_sizes": group_sizes,
        "confidence": default_confidence,
        "status": "preview_only",
        "warnings": ["检测到多个可能分组字段，请选择用于分析的比较组。"] if len(candidates) > 1 else [],
        "source_file": "",
        "missing_group_reason": "",
    }


def _ordered_fields(fields: dict[str, list[str]]) -> list[str]:
    return [field for field in GROUP_FIELD_PRIORITY if field in fields] + sorted(field for field in fields if field not in GROUP_FIELD_PRIORITY)


def _valid_group_sizes(values: list[str]) -> dict[str, int]:
    clean_values = [_clean_group_value(value) for value in values if _clean_group_value(value)]
    if not clean_values:
        return {}
    counts = Counter(clean_values)
    if len(counts) < 2 or len(counts) > 8:
        return {}
    if len(counts) == len(clean_values) and len(counts) > 2:
        return {}
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


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
    return any(token in field for token in ("group", "condition", "treatment", "disease_state", "phenotype", "source_name", "characteristics"))


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
    return text.strip().lower()


def _normalize(value: object) -> str:
    return re.sub(r"_+", "_", "".join(character.lower() if character.isalnum() else "_" for character in str(value))).strip("_")


def _normalize_sample_id(value: object) -> str:
    return _clean_cell(value).strip().strip('"').upper()


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
