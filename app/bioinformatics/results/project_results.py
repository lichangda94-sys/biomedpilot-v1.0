from __future__ import annotations

import csv
import gzip
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree


RESULT_MANAGER = Path("manifests") / "result_manager.json"
RESULT_INDEX = Path("results") / "summaries" / "result_index.json"


def load_result_index(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    index_path = root / RESULT_INDEX
    manager_path = root / RESULT_MANAGER
    index = _read_json(index_path) if index_path.exists() else None
    manager = _read_json(manager_path) if manager_path.exists() else None
    entries = []
    if isinstance(index, dict):
        raw_entries = index.get("results") or index.get("entries") or []
        entries = [item for item in raw_entries if isinstance(item, dict)]
    entries.extend(_imported_deg_result_entries(root))
    warnings = []
    for entry in entries:
        path = Path(str(entry.get("path") or entry.get("file_path") or ""))
        if path and not path.is_absolute():
            path = root / path
        if path and not path.exists():
            warnings.append(f"结果文件缺失：{path}")
            entry["warning"] = entry.get("warning") or "文件缺失"
    return {
        "index": index,
        "manager": manager,
        "entries": entries,
        "warnings": warnings,
        "index_path": str(index_path),
        "manager_path": str(manager_path),
    }


def load_imported_deg_comparisons(project_root: str | Path) -> list[dict[str, object]]:
    root = Path(project_root).expanduser().resolve()
    comparisons: list[dict[str, object]] = []
    for asset in _deg_result_assets(root):
        for comparison in asset.get("comparisons", []) or []:
            if not isinstance(comparison, dict):
                continue
            comparisons.append(
                {
                    **comparison,
                    "source_asset_id": asset.get("asset_id", ""),
                    "source_file": asset.get("source_file", ""),
                    "source_file_name": asset.get("source_file_name", ""),
                    "species": asset.get("species", ""),
                    "species_group": asset.get("species_group", ""),
                    "gene_id_type": asset.get("gene_id_type", ""),
                    "source_label": "导入文件中的已有差异分析结果",
                }
            )
    return comparisons


def build_imported_deg_view(
    project_root: str | Path,
    *,
    source_asset_id: str = "",
    comparison_name: str = "",
    padj_threshold: float = 0.05,
    log2fc_threshold: float = 1.0,
    protein_coding_only: bool = False,
) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    assets = _deg_result_assets(root)
    if source_asset_id:
        assets = [asset for asset in assets if str(asset.get("asset_id") or "") == source_asset_id]
    selected_asset = assets[0] if assets else {}
    comparisons = [comparison for comparison in selected_asset.get("comparisons", []) or [] if isinstance(comparison, dict)]
    if comparison_name:
        selected_comparison = next((comparison for comparison in comparisons if str(comparison.get("comparison_name") or "") == comparison_name), comparisons[0] if comparisons else {})
    else:
        selected_comparison = next((comparison for comparison in comparisons if comparison.get("is_complete")), comparisons[0] if comparisons else {})
    if not selected_asset or not selected_comparison:
        return {"rows": [], "statistics": {}, "warnings": ["未找到 imported DEG comparison。"], "gene_lists": {}}
    source_file = Path(str(selected_asset.get("source_file") or "")).expanduser()
    if not source_file.is_absolute():
        source_file = root / source_file
    table_rows = _read_table_rows(source_file)
    if not table_rows:
        return {"rows": [], "statistics": {}, "warnings": [f"无法读取 DEG 来源表格：{source_file}"], "gene_lists": {}}
    header = [str(value) for value in table_rows[0]]
    body = table_rows[1:]
    column_index = {name: index for index, name in enumerate(header)}
    gene_columns = _gene_columns(header)
    log2fc_column = str(selected_comparison.get("log2fc_column") or "")
    pvalue_column = str(selected_comparison.get("pvalue_column") or "")
    padj_column = str(selected_comparison.get("padj_column") or "")
    warnings: list[str] = []
    if not padj_column:
        warnings.append("该 comparison 缺少 padj，当前使用 pvalue 进行临时筛选。")
    rows: list[dict[str, object]] = []
    for raw in body:
        get_value = lambda column: raw[column_index[column]] if column in column_index and column_index[column] < len(raw) else ""
        log2fc = _to_float(get_value(log2fc_column))
        pvalue = _to_float(get_value(pvalue_column))
        padj = _to_float(get_value(padj_column)) if padj_column else None
        threshold_p = padj if padj is not None else pvalue
        gene_biotype = get_value(gene_columns.get("gene_biotype", ""))
        if protein_coding_only and gene_biotype and gene_biotype != "protein_coding":
            continue
        significant = threshold_p is not None and log2fc is not None and threshold_p < padj_threshold and abs(log2fc) > log2fc_threshold
        direction = "upregulated" if significant and log2fc is not None and log2fc > 0 else "downregulated" if significant and log2fc is not None and log2fc < 0 else "not_significant"
        rows.append(
            {
                "gene_id": get_value(gene_columns.get("gene_id", "")),
                "gene_name": get_value(gene_columns.get("gene_name", "")),
                "log2FC": log2fc,
                "p value": pvalue,
                "adjusted p value": padj,
                "gene_biotype": gene_biotype,
                "gene_description": get_value(gene_columns.get("gene_description", "")),
                "significance": direction,
            }
        )
    significant_rows = [row for row in rows if row.get("significance") in {"upregulated", "downregulated"}]
    up_genes = [_preferred_gene_name(row) for row in significant_rows if row.get("significance") == "upregulated"]
    down_genes = [_preferred_gene_name(row) for row in significant_rows if row.get("significance") == "downregulated"]
    species = str(selected_asset.get("species") or "")
    species_group = str(selected_asset.get("species_group") or "")
    if species == "Mus musculus" or species_group == "mouse":
        enrichment_species = "mouse"
    elif species == "Homo sapiens" or species_group == "human":
        enrichment_species = "human"
    else:
        enrichment_species = species_group or species or "unknown"
    return {
        "source": "imported_deg_result",
        "source_label": "导入文件中的已有差异分析结果",
        "source_file": str(source_file),
        "source_asset_id": selected_asset.get("asset_id", ""),
        "comparison_name": selected_comparison.get("comparison_name", ""),
        "selected_thresholds": {"padj": padj_threshold, "abs_log2fc": log2fc_threshold, "protein_coding_only": protein_coding_only},
        "columns": ["gene_id", "gene_name", "log2FC", "p value", "adjusted p value", "gene_biotype", "gene_description"],
        "original_columns": {"log2fc": log2fc_column, "pvalue": pvalue_column, "padj": padj_column},
        "rows": rows,
        "statistics": {
            "total_genes": len(rows),
            "significant_genes": len(significant_rows),
            "upregulated": len(up_genes),
            "downregulated": len(down_genes),
        },
        "gene_lists": {"up_genes": up_genes, "down_genes": down_genes, "all_significant_genes": [*up_genes, *down_genes]},
        "species": species,
        "gene_id_type": selected_asset.get("gene_id_type", ""),
        "enrichment_species": enrichment_species,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "warnings": warnings,
    }


def write_result_index(project_root: str | Path, entries: list[dict[str, object]]) -> Path:
    root = Path(project_root).expanduser().resolve()
    path = root / RESULT_INDEX
    payload = {"schema_version": "biomedpilot.result_index.v1", "results": entries}
    _write_json(path, payload)
    _write_json(root / RESULT_MANAGER, {"schema_version": "biomedpilot.result_manager.v1", "result_count": len(entries)})
    return path


def _imported_deg_result_entries(root: Path) -> list[dict[str, object]]:
    entries = []
    for asset in _deg_result_assets(root):
        comparisons = [comparison for comparison in asset.get("comparisons", []) or [] if isinstance(comparison, dict)]
        entries.append(
            {
                "result_name": f"导入 DEG：{asset.get('source_file_name') or Path(str(asset.get('source_file') or '')).name}",
                "analysis_type": "imported_deg_result",
                "file_type": "xlsx/csv table",
                "created_at": asset.get("generated_at", "导入识别"),
                "path": asset.get("source_file", ""),
                "status": "available",
                "warning": "",
                "source": "导入文件中的已有差异分析结果",
                "source_asset_id": asset.get("asset_id", ""),
                "source_asset_type": "deg_result_table",
                "comparison_count": asset.get("comparison_count", len(comparisons)),
                "comparisons": comparisons,
                "species": asset.get("species", ""),
                "species_group": asset.get("species_group", ""),
                "gene_id_type": asset.get("gene_id_type", ""),
            }
        )
    return entries


def _deg_result_assets(root: Path) -> list[dict[str, object]]:
    registry_path = root / "manifests" / "standardized_assets_registry.json"
    if not registry_path.exists():
        return []
    try:
        registry = _read_json(registry_path)
    except (OSError, json.JSONDecodeError):
        return []
    assets = registry.get("assets") or registry.get("standardized_assets") or []
    return [asset for asset in assets if isinstance(asset, dict) and asset.get("asset_type") == "deg_result_table"]


def _read_table_rows(path: Path) -> list[list[str]]:
    if path.suffix.lower() == ".xlsx":
        return _read_xlsx_rows(path)
    opener = gzip.open if path.name.lower().endswith(".gz") else open
    delimiter = "\t" if path.suffix.lower() in {".tsv", ".txt"} or ".tsv" in path.name.lower() else ","
    try:
        with opener(path, "rt", encoding="utf-8", errors="ignore", newline="") as handle:  # type: ignore[arg-type]
            return [[str(cell).strip() for cell in row] for row in csv.reader(handle, delimiter=delimiter) if row]
    except OSError:
        return []


def _read_xlsx_rows(path: Path) -> list[list[str]]:
    try:
        with zipfile.ZipFile(path) as archive:
            shared_strings = _xlsx_shared_strings(archive)
            worksheet_name = next((name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")), "")
            if not worksheet_name:
                return []
            root = ElementTree.fromstring(archive.read(worksheet_name))
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError):
        return []
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rows: list[list[str]] = []
    for row in root.findall(".//m:sheetData/m:row", ns):
        values: dict[int, str] = {}
        for cell in row.findall("m:c", ns):
            ref = str(cell.attrib.get("r") or "")
            column_index = _xlsx_column_index(ref)
            value = ""
            if cell.attrib.get("t") == "inlineStr":
                value = "".join(text.text or "" for text in cell.findall(".//m:t", ns))
            else:
                raw = cell.find("m:v", ns)
                value = raw.text if raw is not None and raw.text is not None else ""
                if cell.attrib.get("t") == "s":
                    try:
                        value = shared_strings[int(value)]
                    except (ValueError, IndexError):
                        pass
            values[column_index] = str(value).strip()
        if values:
            rows.append([values.get(index, "") for index in range(max(values) + 1)])
    return rows


def _xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    except (KeyError, ElementTree.ParseError):
        return []
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    return ["".join(text.text or "" for text in item.findall(".//m:t", ns)) for item in root.findall("m:si", ns)]


def _xlsx_column_index(reference: str) -> int:
    letters = re.match(r"([A-Z]+)", reference.upper())
    if not letters:
        return 0
    value = 0
    for character in letters.group(1):
        value = value * 26 + ord(character) - ord("A") + 1
    return value - 1


def _gene_columns(header: list[str]) -> dict[str, str]:
    normalized = {re.sub(r"[^a-z0-9]+", "_", column.lower()).strip("_"): column for column in header}
    return {
        "gene_id": normalized.get("gene_id") or normalized.get("ensembl_gene_id") or header[0],
        "gene_name": normalized.get("gene_name") or normalized.get("gene_symbol") or normalized.get("symbol") or "",
        "gene_biotype": normalized.get("gene_biotype") or normalized.get("biotype") or "",
        "gene_description": normalized.get("gene_description") or normalized.get("description") or "",
    }


def _to_float(value: object) -> float | None:
    try:
        text = str(value).strip()
        return float(text) if text else None
    except (TypeError, ValueError):
        return None


def _preferred_gene_name(row: dict[str, object]) -> str:
    return str(row.get("gene_name") or row.get("gene_id") or "")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
