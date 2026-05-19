from __future__ import annotations

import csv
import gzip
import json
import os
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

from app.bioinformatics.analysis_task_runs import list_analysis_task_runs
from app.bioinformatics.standardized_asset_selection import resolve_standardized_assets


RESULT_MANAGER = Path("manifests") / "result_manager.json"
RESULT_INDEX = Path("results") / "summaries" / "result_index.json"
RESULT_INDEX_SCHEMA_VERSION = "bioinformatics_result_index.v1"


def load_result_index(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    index_path = root / RESULT_INDEX
    manager_path = root / RESULT_MANAGER
    index = _read_json(index_path) if index_path.exists() else None
    manager = _read_json(manager_path) if manager_path.exists() else None
    entries = _stored_completed_entries(index)
    entries.extend(_imported_deg_result_entries(root))
    entries.extend(_analysis_task_run_entries(root))
    entries = _dedupe_entries(entries)
    warnings = _deg_asset_selection_warnings(root)
    for entry in entries:
        path = Path(str(entry.get("path") or entry.get("file_path") or ""))
        if path and not path.is_absolute():
            path = root / path
        if path and not path.exists():
            warnings.append(f"结果文件缺失：{path}")
            entry["warning"] = entry.get("warning") or "文件缺失"
    items = [_result_item_from_entry(entry, index + 1) for index, entry in enumerate(entries)]
    generated_index = {
        "schema_version": RESULT_INDEX_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": items,
        "results": entries,
        "warnings": list(dict.fromkeys(warnings)),
    }
    _write_json(index_path, generated_index)
    _write_json(root / RESULT_MANAGER, {"schema_version": "biomedpilot.result_manager.v1", "result_count": len(entries), "item_count": len(items)})
    return {
        "index": generated_index,
        "manager": manager,
        "entries": entries,
        "items": items,
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
        warnings = _deg_asset_selection_warnings(root) or ["未找到 imported DEG comparison。"]
        return {"rows": [], "statistics": {}, "warnings": warnings, "gene_lists": {}}
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
    normalized_entries = [_completed_result_entry(entry, index + 1) for index, entry in enumerate(entries)]
    items = [_result_item_from_entry(entry, index + 1) for index, entry in enumerate(normalized_entries)]
    payload = {
        "schema_version": RESULT_INDEX_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": items,
        "results": normalized_entries,
        "warnings": [],
    }
    _write_json(path, payload)
    _write_json(root / RESULT_MANAGER, {"schema_version": "biomedpilot.result_manager.v1", "result_count": len(normalized_entries), "item_count": len(items)})
    return path


def _stored_completed_entries(index: dict[str, object] | None) -> list[dict[str, object]]:
    if not isinstance(index, dict):
        return []
    raw_entries = index.get("results") or index.get("entries") or []
    entries = [dict(item) for item in raw_entries if isinstance(item, dict)]
    raw_items = [item for item in index.get("items", []) or [] if isinstance(item, dict)]
    for item in raw_items:
        if str(item.get("item_type") or "") in {"imported_deg_result", "analysis_task_run", "task_run_record"}:
            continue
        if any(entry.get("item_id") == item.get("item_id") for entry in entries):
            continue
        entries.append(dict(item))
    completed = []
    for index, entry in enumerate(entries, start=1):
        if str(entry.get("item_type") or "") in {"imported_deg_result", "analysis_task_run", "task_run_record"}:
            continue
        if str(entry.get("analysis_type") or "") in {"imported_deg_result", "analysis_task_run"}:
            continue
        completed.append(_completed_result_entry(entry, index))
    return completed


def _completed_result_entry(entry: dict[str, object], index: int) -> dict[str, object]:
    item = dict(entry)
    item.setdefault("item_id", str(item.get("result_id") or f"completed_result_{index:03d}"))
    item.setdefault("item_type", "completed_result")
    item.setdefault("analysis_type", item.get("task_type") or "analysis_result")
    item.setdefault("status", "created")
    item.setdefault("source", "analysis_output")
    item.setdefault("description", item.get("result_name") or "分析输出结果")
    return item


def _imported_deg_result_entries(root: Path) -> list[dict[str, object]]:
    entries = []
    for index, asset in enumerate(_deg_result_assets(root), start=1):
        comparisons = [comparison for comparison in asset.get("comparisons", []) or [] if isinstance(comparison, dict)]
        item_id = f"imported_deg_{index:03d}"
        entries.append(
            {
                "item_id": item_id,
                "item_type": "imported_deg_result",
                "result_name": f"导入 DEG：{asset.get('source_file_name') or Path(str(asset.get('source_file') or '')).name}",
                "analysis_type": "imported_deg_result",
                "file_type": "xlsx/csv table",
                "created_at": asset.get("generated_at", "导入识别"),
                "path": asset.get("source_file", ""),
                "status": "available",
                "warning": "",
                "source": "imported_table",
                "description": "导入表格中的已有差异分析结果",
                "source_label": "导入文件中的已有差异分析结果",
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


def _analysis_task_run_entries(root: Path) -> list[dict[str, object]]:
    entries = []
    for run in list_analysis_task_runs(root):
        run_id = str(run.get("run_id") or "")
        run_dir = Path(str(run.get("run_dir") or ""))
        path = run_dir / "task_run.json" if run_dir else Path(str(run.get("task_run_path") or ""))
        try:
            display_path = str(path.relative_to(root))
        except ValueError:
            display_path = str(path)
        entries.append(
            {
                "item_id": run_id,
                "item_type": "analysis_task_run",
                "result_name": f"分析任务记录：{run_id}",
                "analysis_type": "analysis_task_run",
                "task_type": run.get("task_type", ""),
                "task_family": run.get("task_family", ""),
                "file_type": "task_run.json",
                "created_at": run.get("created_at", ""),
                "path": display_path,
                "source_run_path": display_path,
                "status": run.get("status", ""),
                "warning": "",
                "source": "analysis_task_run_record",
                "description": "重新差异分析任务记录；当前版本尚未执行真实 DEG。",
                "source_assets": run.get("source_assets", []),
                "comparison_count": len([item for item in run.get("comparisons", []) or [] if isinstance(item, dict)]),
                "comparisons": run.get("comparisons", []),
                "parameters": run.get("parameters", {}),
                "outputs": run.get("outputs", []),
                "deg_preflight_manifest": run.get("deg_preflight_manifest", {}),
            }
        )
    return entries


def _dedupe_entries(entries: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, object]] = []
    for entry in entries:
        key = (str(entry.get("item_type") or entry.get("analysis_type") or ""), str(entry.get("item_id") or entry.get("source_asset_id") or entry.get("path") or ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


def _result_item_from_entry(entry: dict[str, object], index: int) -> dict[str, object]:
    item_type = str(entry.get("item_type") or ("analysis_task_run" if entry.get("analysis_type") == "analysis_task_run" else "completed_result"))
    item_id = str(entry.get("item_id") or f"{item_type}_{index:03d}")
    return {
        "item_id": item_id,
        "item_type": item_type,
        "status": entry.get("status", ""),
        "result_name": entry.get("result_name", ""),
        "analysis_type": entry.get("analysis_type", ""),
        "task_type": entry.get("task_type", ""),
        "source_asset_id": entry.get("source_asset_id", ""),
        "source": entry.get("source", ""),
        "description": entry.get("description") or entry.get("source_label") or entry.get("result_name") or "",
        "path": entry.get("path", ""),
        "source_run_path": entry.get("source_run_path", ""),
        "comparison_count": entry.get("comparison_count", 0),
        "deg_preflight_manifest": entry.get("deg_preflight_manifest", {}),
    }


def _deg_result_assets(root: Path) -> list[dict[str, object]]:
    resolved = resolve_standardized_assets(root, asset_types={"deg_result_table"})
    return [asset for asset in resolved.get("assets", []) or [] if isinstance(asset, dict) and asset.get("asset_type") == "deg_result_table"]


def _deg_asset_selection_warnings(root: Path) -> list[str]:
    resolved = resolve_standardized_assets(root, asset_types={"deg_result_table"})
    if "deg_result_table" not in set(resolved.get("blocked_asset_types", []) or []):
        return []
    return [str(item) for item in resolved.get("warnings", []) or [] if str(item)] or ["请先在标准化资产页选择默认 DEG 结果资产。"]


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
    temp_path = path.with_name(f".{path.name}.tmp")
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    with temp_path.open("w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, path)
