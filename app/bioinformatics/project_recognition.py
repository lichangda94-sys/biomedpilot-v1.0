from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

from app.bioinformatics.legacy.geo_processing.detector.dataset_detector import detect_dataset


RECOGNITION_REPORT = Path("logs") / "recognition" / "recognition_report.json"

TYPE_LABELS = {
    "expression_matrix": "表达矩阵",
    "normalized_expression_matrix": "标准化表达矩阵",
    "raw_count_matrix": "原始计数矩阵",
    "sample_metadata": "样本注释",
    "clinical_metadata": "临床信息",
    "gene_annotation": "基因注释",
    "platform_annotation": "平台注释",
    "comparison_config": "分组比较配置",
    "gmt_gene_set": "GMT 基因集",
    "unknown": "未知文件",
}


def run_project_recognition(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    files = _candidate_files(root)
    warnings: list[str] = []
    records: list[dict[str, object]] = []
    if not files:
        warnings.append("未找到可识别的数据文件，请返回数据来源页补充数据。")
    for path in files:
        kind, reason, confidence = classify_file(path)
        records.append(
            {
                "file_name": path.name,
                "original_path": str(path),
                "recognized_type": kind,
                "recognized_type_zh": TYPE_LABELS.get(kind, "未知文件"),
                "confidence": confidence,
                "file_size": path.stat().st_size if path.exists() else 0,
                "reason": reason,
                "warning": "低置信度，需要人工确认。" if confidence < 0.5 else "",
                "route_path": str(root / "recognized_data" / kind / path.name),
            }
        )
    try:
        geo_root = root / "raw_data" / "geo"
        if geo_root.exists() and any(geo_root.rglob("*")):
            detection = detect_dataset("GSE_LOCAL", str(geo_root))
            warnings.extend(str(item) for item in detection.warnings)
    except Exception as exc:
        warnings.append(f"legacy GEO 检测未完成：{exc.__class__.__name__}")
    report = {
        "schema_version": "biomedpilot.recognition_report.v1",
        "generated_at": _now(),
        "project_root": str(root),
        "files": records,
        "type_counts": _type_counts(records),
        "warnings": warnings,
    }
    _write_json(root / RECOGNITION_REPORT, report)
    return report


def load_recognition_report(project_root: str | Path) -> dict[str, object] | None:
    path = Path(project_root).expanduser().resolve() / RECOGNITION_REPORT
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def classify_file(path: Path) -> tuple[str, str, float]:
    name = path.name.lower()
    if name.endswith((".gmt", ".gmx")):
        return "gmt_gene_set", "文件扩展名提示为基因集。", 0.85
    if any(token in name for token in ("clinical", "survival", "patient")):
        return "clinical_metadata", "文件名包含临床/生存信息提示。", 0.72
    if any(token in name for token in ("sample", "metadata", "phenotype", "pheno")):
        return "sample_metadata", "文件名包含样本注释提示。", 0.72
    if any(token in name for token in ("gene_annotation", "platform", "gpl", "probe", "annotation")):
        return "platform_annotation", "文件名包含平台或注释提示。", 0.68
    if any(token in name for token in ("comparison", "contrast", "group")):
        return "comparison_config", "文件名包含分组比较提示。", 0.64
    if any(token in name for token in ("count", "counts", "raw")):
        return "raw_count_matrix", "文件名包含 raw/counts 提示。", 0.66
    if any(token in name for token in ("expression", "expr", "matrix", "tpm", "fpkm", "series_matrix")):
        return "expression_matrix", "文件名包含表达矩阵提示。", 0.7
    if path.suffix.lower() == ".xlsx":
        workbook_kind = _classify_xlsx_table(path)
        if workbook_kind is not None:
            return workbook_kind
    return "unknown", "未匹配到稳定识别规则。", 0.2


def _classify_xlsx_table(path: Path) -> tuple[str, str, float] | None:
    try:
        headers = _xlsx_first_row(path)
    except Exception:
        return None
    if len(headers) < 3:
        return None
    normalized = [_normalize_header(header) for header in headers]
    first_header = normalized[0]
    has_gene_column = any(token in first_header for token in ("gene", "ensembl", "probe", "symbol", "id"))
    numeric_sample_like = sum(
        1
        for header in normalized[1:]
        if header and any(token in header for token in ("count", "counts", "sample", "gsm", "srr", "tcga", "tpm", "fpkm"))
    )
    if has_gene_column and numeric_sample_like >= 2:
        if any("count" in header for header in normalized[1:]):
            return "raw_count_matrix", "XLSX 首行包含 gene/probe/id 列和多个 count 样本列。", 0.82
        return "expression_matrix", "XLSX 首行包含 gene/probe/id 列和多个样本表达列。", 0.78
    return None


def _xlsx_first_row(path: Path, *, max_cells: int = 200) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        worksheet_name = "xl/worksheets/sheet1.xml"
        if worksheet_name not in names:
            return []
        shared_strings = _xlsx_shared_strings(archive, names)
        worksheet = ElementTree.fromstring(archive.read(worksheet_name))
        first_row = worksheet.find(".//{*}sheetData/{*}row")
        if first_row is None:
            return []
        values_by_column: dict[int, str] = {}
        for cell in list(first_row.findall("{*}c"))[:max_cells]:
            column_index = _xlsx_column_index(str(cell.attrib.get("r", "")))
            values_by_column[column_index] = _xlsx_cell_value(cell, shared_strings)
        if not values_by_column:
            return []
        return [values_by_column.get(index, "") for index in range(max(values_by_column) + 1)]


def _xlsx_shared_strings(archive: zipfile.ZipFile, names: set[str]) -> list[str]:
    if "xl/sharedStrings.xml" not in names:
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for item in root.findall("{*}si"):
        strings.append("".join(node.text or "" for node in item.findall(".//{*}t")))
    return strings


def _xlsx_cell_value(cell: ElementTree.Element, shared_strings: list[str]) -> str:
    if cell.attrib.get("t") == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//{*}t")).strip()
    value_node = cell.find("{*}v")
    if value_node is None or value_node.text is None:
        return ""
    raw_value = value_node.text
    if cell.attrib.get("t") == "s":
        try:
            return shared_strings[int(raw_value)].strip()
        except (ValueError, IndexError):
            return ""
    return raw_value.strip()


def _xlsx_column_index(reference: str) -> int:
    letters = "".join(character for character in reference if character.isalpha())
    index = 0
    for character in letters.upper():
        index = index * 26 + ord(character) - ord("A") + 1
    return max(index - 1, 0)


def _normalize_header(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "_" for character in str(value)).strip("_")


def _candidate_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for base in (root / "raw_data", root / "acquisition"):
        if base.exists():
            paths.extend(path for path in base.rglob("*") if path.is_file() and path.suffix.lower() not in {".json"})
    return sorted(set(paths))


def _type_counts(records: list[dict[str, object]]) -> dict[str, int]:
    counts = {key: 0 for key in TYPE_LABELS}
    for record in records:
        key = str(record.get("recognized_type") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
