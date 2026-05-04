from __future__ import annotations

import json
import gzip
import zipfile
from dataclasses import dataclass
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
    "geo_soft_container": "GEO SOFT 容器",
    "unknown": "未知文件",
}


@dataclass(frozen=True)
class RecognitionClassification:
    primary_type: str
    reason: str
    confidence: float
    roles: tuple[str, ...]
    detected_assets: tuple[dict[str, object], ...] = ()
    container_format: str = ""


def run_project_recognition(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    files = _candidate_files(root)
    warnings: list[str] = []
    records: list[dict[str, object]] = []
    if not files:
        warnings.append("未找到可识别的数据文件，请返回数据来源页补充数据。")
    for path in files:
        classification = classify_file_details(path)
        kind = classification.primary_type
        reason = classification.reason
        confidence = classification.confidence
        records.append(
            {
                "file_name": path.name,
                "original_path": str(path),
                "recognized_type": kind,
                "recognized_type_zh": TYPE_LABELS.get(kind, "未知文件"),
                "recognized_roles": list(classification.roles),
                "recognized_roles_zh": [TYPE_LABELS.get(role, role) for role in classification.roles],
                "detected_assets": list(classification.detected_assets),
                "container_format": classification.container_format,
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
    classification = classify_file_details(path)
    return classification.primary_type, classification.reason, classification.confidence


def classify_file_details(path: Path) -> RecognitionClassification:
    name = path.name.lower()
    if name.endswith((".gmt", ".gmx")):
        return _classification("gmt_gene_set", "文件扩展名提示为基因集。", 0.85)
    if _is_geo_soft_path(path):
        geo_soft = _classify_geo_soft(path)
        if geo_soft is not None:
            return geo_soft
    if any(token in name for token in ("clinical", "survival", "patient")):
        return _classification("clinical_metadata", "文件名包含临床/生存信息提示。", 0.72)
    if any(token in name for token in ("sample", "metadata", "phenotype", "pheno")):
        return _classification("sample_metadata", "文件名包含样本注释提示。", 0.72)
    if any(token in name for token in ("gene_annotation", "platform", "gpl", "probe", "annotation")):
        return _classification("platform_annotation", "文件名包含平台或注释提示。", 0.68)
    if any(token in name for token in ("comparison", "contrast", "group")):
        return _classification("comparison_config", "文件名包含分组比较提示。", 0.64)
    if any(token in name for token in ("count", "counts", "raw")):
        return _classification("raw_count_matrix", "文件名包含 raw/counts 提示。", 0.66)
    if any(token in name for token in ("expression", "expr", "matrix", "tpm", "fpkm", "series_matrix")):
        return _classification("expression_matrix", "文件名包含表达矩阵提示。", 0.7)
    if path.suffix.lower() == ".xlsx":
        workbook_kind = _classify_xlsx_table(path)
        if workbook_kind is not None:
            return workbook_kind
    return _classification("unknown", "未匹配到稳定识别规则。", 0.2, roles=())


def _classification(
    primary_type: str,
    reason: str,
    confidence: float,
    *,
    roles: tuple[str, ...] | None = None,
    detected_assets: tuple[dict[str, object], ...] = (),
    container_format: str = "",
) -> RecognitionClassification:
    normalized_roles = tuple(dict.fromkeys(roles if roles is not None else (() if primary_type == "unknown" else (primary_type,))))
    return RecognitionClassification(
        primary_type=primary_type,
        reason=reason,
        confidence=confidence,
        roles=normalized_roles,
        detected_assets=detected_assets or tuple(_detected_asset(role, confidence=confidence, reason=reason) for role in normalized_roles),
        container_format=container_format,
    )


def _classify_xlsx_table(path: Path) -> RecognitionClassification | None:
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
            return _classification("raw_count_matrix", "XLSX 首行包含 gene/probe/id 列和多个 count 样本列。", 0.82)
        return _classification("expression_matrix", "XLSX 首行包含 gene/probe/id 列和多个样本表达列。", 0.78)
    return None


def _classify_geo_soft(path: Path) -> RecognitionClassification | None:
    scan = _scan_geo_soft(path)
    if not scan["has_geo_header"]:
        return None
    roles: list[str] = []
    assets: list[dict[str, object]] = []
    if scan["has_expression_table"]:
        roles.append("expression_matrix")
        assets.append(
            _detected_asset(
                "expression_matrix",
                confidence=0.86,
                reason="SOFT sample table 包含 ID_REF / VALUE 表达值。",
                source_section="sample_table",
                source_format="geo_family_soft",
                extra={"sample_count": scan["sample_count"], "value_description": scan["value_description"]},
            )
        )
    if scan["has_sample_metadata"]:
        roles.append("sample_metadata")
        assets.append(
            _detected_asset(
                "sample_metadata",
                confidence=0.84,
                reason="SOFT 包含 SAMPLE 块、样本标题或样本 characteristics。",
                source_section="sample_metadata",
                source_format="geo_family_soft",
                extra={"sample_count": scan["sample_count"]},
            )
        )
    if scan["has_platform_annotation"]:
        roles.append("platform_annotation")
        assets.append(
            _detected_asset(
                "platform_annotation",
                confidence=0.82,
                reason="SOFT 包含 PLATFORM 块或 platform table。",
                source_section="platform_table",
                source_format="geo_family_soft",
            )
        )
    if scan["has_clinical_metadata"]:
        roles.append("clinical_metadata")
        assets.append(
            _detected_asset(
                "clinical_metadata",
                confidence=0.68,
                reason="样本 characteristics 中包含年龄、性别、组织、肿瘤/正常等临床或分组线索。",
                source_section="sample_characteristics",
                source_format="geo_family_soft",
                extra={"sample_count": scan["sample_count"]},
            )
        )
    if not roles:
        return None
    role_labels = "、".join(TYPE_LABELS.get(role, role) for role in roles)
    reason = f"GEO family SOFT 容器，检测到：{role_labels}。"
    return _classification(
        "geo_soft_container",
        reason,
        0.86,
        roles=tuple(roles),
        detected_assets=tuple(assets),
        container_format="geo_family_soft",
    )


def _scan_geo_soft(path: Path) -> dict[str, object]:
    scan: dict[str, object] = {
        "has_geo_header": False,
        "has_expression_table": False,
        "has_sample_metadata": False,
        "has_platform_annotation": False,
        "has_clinical_metadata": False,
        "sample_count": 0,
        "value_description": "",
    }
    sample_ids: set[str] = set()
    sample_blocks = 0
    sample_characteristics = 0
    sample_table_begin = 0
    id_ref_seen = False
    value_seen = False
    clinical_tokens = ("age", "gender", "sex", "tissue", "tumor", "normal", "disease", "stage", "metastasis", "survival")
    try:
        handle = gzip.open(path, "rt", encoding="utf-8", errors="ignore") if path.name.lower().endswith(".gz") else path.open("r", encoding="utf-8", errors="ignore")
        with handle:
            for line in handle:
                stripped = line.strip()
                lower = stripped.lower()
                if stripped.startswith("^DATABASE") or stripped.startswith("^SERIES") or "gene expression omnibus" in lower:
                    scan["has_geo_header"] = True
                if stripped.startswith("!Series_sample_id"):
                    sample_ids.add(stripped.partition("=")[2].strip())
                elif stripped.startswith("^SAMPLE"):
                    sample_blocks += 1
                elif stripped.startswith("!Sample_title"):
                    sample_characteristics += 1
                elif stripped.startswith("!Sample_characteristics"):
                    sample_characteristics += 1
                    if any(token in lower for token in clinical_tokens):
                        scan["has_clinical_metadata"] = True
                elif stripped.startswith("^PLATFORM") or stripped.startswith("!platform_table_begin"):
                    scan["has_platform_annotation"] = True
                elif stripped.startswith("!sample_table_begin"):
                    sample_table_begin += 1
                elif stripped.startswith("#ID_REF") or lower == "id_ref" or lower.startswith("id_ref\t"):
                    id_ref_seen = True
                elif stripped.startswith("#VALUE") or lower == "value" or "\tvalue" in lower:
                    value_seen = True
                    if not scan["value_description"]:
                        scan["value_description"] = stripped.partition("=")[2].strip() if "=" in stripped else stripped
                if (
                    scan["has_geo_header"]
                    and scan["has_platform_annotation"]
                    and (sample_ids or sample_blocks)
                    and sample_characteristics
                    and sample_table_begin
                    and id_ref_seen
                    and value_seen
                ):
                    break
    except OSError:
        return scan
    sample_count = max(len(sample_ids), sample_blocks)
    scan["sample_count"] = sample_count
    scan["has_sample_metadata"] = bool(sample_ids or sample_blocks or sample_characteristics)
    scan["has_expression_table"] = bool(sample_table_begin and id_ref_seen and value_seen)
    return scan


def _is_geo_soft_path(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(".soft") or name.endswith(".soft.gz")


def _detected_asset(
    asset_type: str,
    *,
    confidence: float,
    reason: str,
    source_section: str = "file",
    source_format: str = "",
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "asset_type": asset_type,
        "label_zh": TYPE_LABELS.get(asset_type, asset_type),
        "confidence": confidence,
        "reason": reason,
        "source_section": source_section,
    }
    if source_format:
        payload["source_format"] = source_format
    if extra:
        payload.update(extra)
    return payload


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
    paths.extend(_registered_reference_files(root))
    return sorted(set(paths))


def _registered_reference_files(root: Path) -> list[Path]:
    records_dir = root / "acquisition" / "records"
    if not records_dir.exists():
        return []
    paths: list[Path] = []
    for record_path in records_dir.glob("*.json"):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if record.get("strategy") != "reference":
            continue
        for key in ("referenced_paths", "registered_files"):
            values = record.get(key)
            if not isinstance(values, list):
                continue
            for raw in values:
                candidate = Path(str(raw)).expanduser()
                if candidate.is_file():
                    paths.append(candidate.resolve())
                elif candidate.is_dir():
                    paths.extend(path.resolve() for path in candidate.rglob("*") if path.is_file() and path.suffix.lower() not in {".json"})
    return paths


def _type_counts(records: list[dict[str, object]]) -> dict[str, int]:
    counts = {key: 0 for key in TYPE_LABELS}
    for record in records:
        keys = [str(record.get("recognized_type") or "unknown")]
        keys.extend(str(role) for role in record.get("recognized_roles", []) or [])
        for key in dict.fromkeys(key for key in keys if key):
            counts[key] = counts.get(key, 0) + 1
    return counts


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
