from __future__ import annotations

import csv
import gzip
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.project_recognition import load_recognition_report
from app.bioinformatics.results.project_results import load_result_index, write_result_index


PREVIEW_ROW_LIMIT = 20
MAX_SUMMARY_ROWS = 100_000
IMPORTED_DEG_ROOT = Path("analysis") / "deg" / "imported"
IMPORTED_DEG_MANIFEST = "imported_deg_result_manifest.json"
MANUAL_MAPPING_FILE = "column_mapping.json"
DEFAULT_THRESHOLDS = {"log2fc_abs": 1.0, "significance": 0.05}


@dataclass(frozen=True)
class ImportedDegResult:
    result_id: str
    name: str
    path: str
    source_label: str
    status: str
    report_status: str
    column_mapping: dict[str, str]
    column_status: str
    regulation_counts: dict[str, object]
    top_up_genes: tuple[dict[str, object], ...]
    top_down_genes: tuple[dict[str, object], ...]
    thresholds: dict[str, object]
    manifest_path: str
    generated_at: str
    mapping_status: str
    preview_headers: tuple[str, ...]
    preview_rows: tuple[tuple[str, ...], ...]
    user_note: str = ""
    warning: str = ""

    def to_user_row(self) -> list[object]:
        counts = self.regulation_counts
        up = counts.get("up", "待确认")
        down = counts.get("down", "待确认")
        nonsig = counts.get("not_significant", "待确认")
        if counts.get("status") != "computed":
            count_text = "待确认"
        else:
            count_text = f"上调 {up}；下调 {down}；不显著 {nonsig}"
        return [
            self.name,
            self.source_label,
            _status_label(self.status),
            self.report_status,
            self.column_status,
            count_text,
            _next_step(self),
        ]

    def to_dict(self) -> dict[str, object]:
        return {
            "result_id": self.result_id,
            "name": self.name,
            "path": self.path,
            "source_label": self.source_label,
            "status": self.status,
            "report_status": self.report_status,
            "column_mapping": self.column_mapping,
            "column_status": self.column_status,
            "regulation_counts": self.regulation_counts,
            "top_up_genes": list(self.top_up_genes),
            "top_down_genes": list(self.top_down_genes),
            "thresholds": self.thresholds,
            "manifest_path": self.manifest_path,
            "generated_at": self.generated_at,
            "mapping_status": self.mapping_status,
            "preview_headers": list(self.preview_headers),
            "preview_rows": [list(row) for row in self.preview_rows],
            "user_note": self.user_note,
            "warning": self.warning,
            "semantic_boundary": "imported_external_deg_not_biomedpilot_computed",
        }

    def to_manifest(self) -> dict[str, object]:
        return {
            "schema_version": "biomedpilot.imported_deg_result_manifest.v1",
            "result_id": self.result_id,
            "created_at": self.generated_at,
            "source_kind": "user_imported_external_deg_table",
            "semantic_boundary": "imported_external_deg_not_biomedpilot_computed",
            "source_file_name": Path(self.path).name if self.path else "",
            "source_label": self.source_label,
            "column_mapping": self.column_mapping,
            "mapping_status": self.mapping_status,
            "thresholds": self.thresholds,
            "regulation_counts": self.regulation_counts,
            "top_up_genes": list(self.top_up_genes),
            "top_down_genes": list(self.top_down_genes),
            "warnings": [self.warning] if self.warning else [],
            "report_candidate": self.status == "ready",
            "report_sentence_policy": "用户导入的外部分析结果显示",
            "user_note": self.user_note,
        }


def list_imported_deg_results(project_root: str | Path) -> list[ImportedDegResult]:
    root = Path(project_root).expanduser().resolve()
    raw_entries = _imported_deg_entries(root)
    results: list[ImportedDegResult] = []
    for index, entry in enumerate(raw_entries, start=1):
        result = _build_result(root, entry, fallback_index=index)
        results.append(result)
    return results


def imported_deg_summary(project_root: str | Path) -> dict[str, object]:
    results = list_imported_deg_results(project_root)
    status_counts: dict[str, int] = {}
    for result in results:
        status_counts[result.status] = status_counts.get(result.status, 0) + 1
    return {
        "count": len(results),
        "status_counts": status_counts,
        "reportable_count": sum(1 for result in results if result.report_status in {"是", "需确认"}),
        "included_result_ids": [result.result_id for result in results if result.status == "ready"],
        "results": [result.to_dict() for result in results],
    }


def mark_imported_deg_report_candidates(project_root: str | Path) -> list[dict[str, object]]:
    root = Path(project_root).expanduser().resolve()
    current = load_result_index(root)
    entries = [dict(item) for item in current.get("entries", []) or [] if isinstance(item, dict)]
    for result in list_imported_deg_results(root):
        if result.status != "ready":
            continue
        manifest_path = write_imported_deg_manifest(root, result)
        entry_payload = _result_index_entry(root, result, manifest_path)
        existing = _find_existing_entry(entries, result)
        if existing is None:
            entries.append(entry_payload)
        else:
            existing.update(entry_payload)
    write_result_index(root, entries)
    return entries


def save_imported_deg_column_mapping(
    project_root: str | Path,
    *,
    result_id: str,
    column_mapping: dict[str, str],
    user_note: str = "",
) -> Path:
    root = Path(project_root).expanduser().resolve()
    mapping_dir = root / IMPORTED_DEG_ROOT / result_id
    payload = {
        "schema_version": "biomedpilot.imported_deg_column_mapping.v1",
        "updated_at": _now(),
        "result_id": result_id,
        "column_mapping": {str(key): str(value) for key, value in column_mapping.items() if str(value).strip()},
        "user_note": user_note,
        "user_confirmed": True,
    }
    path = mapping_dir / MANUAL_MAPPING_FILE
    _write_json(path, payload)
    return path


def write_imported_deg_manifest(project_root: str | Path, result: ImportedDegResult) -> Path:
    root = Path(project_root).expanduser().resolve()
    manifest_path = root / IMPORTED_DEG_ROOT / result.result_id / IMPORTED_DEG_MANIFEST
    _write_json(manifest_path, result.to_manifest())
    return manifest_path


def _imported_deg_entries(root: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    seen_paths: set[str] = set()
    result_index = load_result_index(root)
    for item in result_index.get("entries", []) or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("analysis_type") or "") != "differential_expression":
            continue
        semantics = str(item.get("result_semantics") or item.get("status") or "").lower()
        if "import" not in semantics:
            continue
        path = str(item.get("path") or item.get("file_path") or "")
        entries.append({"name": item.get("result_name") or item.get("name") or "导入差异分析结果", "path": path, "source": "result_index", "raw": item})
        if path:
            seen_paths.add(path)
    recognition = load_recognition_report(root)
    if isinstance(recognition, dict):
        for item in recognition.get("files", []) or []:
            if not isinstance(item, dict) or str(item.get("recognized_type") or "") != "differential_result_table":
                continue
            path = str(item.get("original_path") or item.get("route_path") or "")
            if path and path in seen_paths:
                continue
            entries.append(
                {
                    "name": f"导入差异分析表格：{item.get('file_name') or '未命名表格'}",
                    "path": path,
                    "source": "recognition",
                    "raw": item,
                }
            )
            if path:
                seen_paths.add(path)
    return entries


def _build_result(root: Path, entry: dict[str, object], *, fallback_index: int) -> ImportedDegResult:
    raw_path = str(entry.get("path") or "")
    path = Path(raw_path).expanduser() if raw_path else Path()
    if raw_path and not path.is_absolute():
        path = root / path
    name = str(entry.get("name") or f"导入差异分析结果 {fallback_index}")
    result_id = _slug_text(f"{fallback_index}-{name}-{path.name if raw_path else 'missing'}")
    manual_mapping, user_note, user_confirmed = _load_manual_mapping(root, result_id)
    manifest_path = root / IMPORTED_DEG_ROOT / result_id / IMPORTED_DEG_MANIFEST
    generated_at = _now()
    if not raw_path or not path.is_file():
        return ImportedDegResult(
            result_id=result_id,
            name=name,
            path=str(path) if raw_path else "",
            source_label="用户导入 / 外部分析结果",
            status="missing",
            report_status="否",
            column_mapping={},
            column_status="文件缺失，无法识别主要列",
            regulation_counts={"status": "unavailable", "message": "待确认"},
            top_up_genes=(),
            top_down_genes=(),
            thresholds=dict(DEFAULT_THRESHOLDS),
            manifest_path=str(manifest_path),
            generated_at=generated_at,
            mapping_status="missing_file",
            preview_headers=(),
            preview_rows=(),
            user_note=user_note,
            warning="文件缺失",
        )
    headers, preview_rows, summary_rows, read_warnings = _read_table(path)
    auto_mapping = _map_columns(headers)
    mapping = _merge_mapping(auto_mapping, manual_mapping, headers)
    column_status = _column_status(mapping)
    status = "ready" if {"gene", "logfc"} <= set(mapping) and ("fdr" in mapping or "pvalue" in mapping) else "needs_confirmation"
    report_status = "是" if status == "ready" else "需确认"
    regulation_counts, top_up, top_down = _summarize_rows(headers, summary_rows, mapping)
    warning = "；".join(read_warnings)
    mapping_status = "user_confirmed" if user_confirmed and status == "ready" else ("auto_mapped" if status == "ready" else "needs_confirmation")
    return ImportedDegResult(
        result_id=result_id,
        name=name,
        path=str(path),
        source_label="用户导入 / 外部分析结果",
        status=status,
        report_status=report_status,
        column_mapping=mapping,
        column_status=column_status,
        regulation_counts=regulation_counts,
        top_up_genes=tuple(top_up),
        top_down_genes=tuple(top_down),
        thresholds=dict(DEFAULT_THRESHOLDS),
        manifest_path=str(manifest_path),
        generated_at=generated_at,
        mapping_status=mapping_status,
        preview_headers=tuple(headers),
        preview_rows=tuple(tuple(cell for cell in row) for row in preview_rows),
        user_note=user_note,
        warning=warning,
    )


def _read_table(path: Path) -> tuple[list[str], list[list[str]], list[list[str]], list[str]]:
    if path.suffix.lower() == ".xlsx":
        return _read_xlsx_table(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace", newline="") as handle:  # type: ignore[arg-type]
        first = handle.readline()
        if not first:
            return [], [], [], ["文件为空，无法读取表头。"]
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        header = next(csv.reader([first], delimiter=delimiter))
        preview_rows: list[list[str]] = []
        summary_rows: list[list[str]] = []
        warnings: list[str] = []
        reader = csv.reader(handle, delimiter=delimiter)
        for index, row in enumerate(reader):
            if index < PREVIEW_ROW_LIMIT:
                preview_rows.append(row)
            if index < MAX_SUMMARY_ROWS:
                summary_rows.append(row)
            elif index == MAX_SUMMARY_ROWS:
                warnings.append(f"表格超过 {MAX_SUMMARY_ROWS} 行，摘要仅基于前 {MAX_SUMMARY_ROWS} 行。")
        return header, preview_rows, summary_rows, warnings


def _read_xlsx_table(path: Path) -> tuple[list[str], list[list[str]], list[list[str]], list[str]]:
    try:
        from app.bioinformatics.project_recognition import _xlsx_rows  # existing no-dependency XLSX reader

        rows = _xlsx_rows(path, max_rows=MAX_SUMMARY_ROWS + 1, max_cells=500)
    except Exception as exc:
        return [], [], [], [f"xlsx 读取失败：{exc}"]
    clean_rows = [[str(cell) for cell in row] for row in rows if any(str(cell).strip() for cell in row)]
    if not clean_rows:
        return [], [], [], ["xlsx 文件为空或未读取到 sheet1。"]
    header = clean_rows[0]
    summary_rows = clean_rows[1:]
    warnings = []
    if len(rows) > MAX_SUMMARY_ROWS + 1:
        warnings.append(f"表格超过 {MAX_SUMMARY_ROWS} 行，摘要仅基于前 {MAX_SUMMARY_ROWS} 行。")
    return header, summary_rows[:PREVIEW_ROW_LIMIT], summary_rows[:MAX_SUMMARY_ROWS], warnings


def _map_columns(headers: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for header in headers:
        key = _normalize_header(header)
        if "gene" not in mapping and key in {"gene", "genes", "geneid", "genesymbol", "symbol", "id", "ensembl", "entrezid", "idref"}:
            mapping["gene"] = header
        elif "logfc" not in mapping and key in {"logfc", "log2fc", "log2foldchange", "logfoldchange", "avglog2fc"}:
            mapping["logfc"] = header
        elif "pvalue" not in mapping and key in {"pvalue", "pval", "p", "pvalue", "pvalnominal", "pvalueunadjusted"}:
            mapping["pvalue"] = header
        elif "fdr" not in mapping and key in {"padj", "adjpval", "adjpvalue", "adjustedpvalue", "fdr", "qvalue"}:
            mapping["fdr"] = header
        elif "statistic" not in mapping and key in {"stat", "statistic", "t", "b", "waldstat", "waldstatistic", "zscore"}:
            mapping["statistic"] = header
        elif "base_mean" not in mapping and key in {"basemean", "meanexpression", "baseavg", "avgexpr", "averagelogexpression"}:
            mapping["base_mean"] = header
    return mapping


def _column_status(mapping: dict[str, str]) -> str:
    parts = []
    for key, label in (
        ("gene", "gene"),
        ("logfc", "logFC / log2FC"),
        ("pvalue", "p value"),
        ("fdr", "padj / FDR"),
        ("statistic", "statistic"),
        ("base_mean", "baseMean / mean expression"),
    ):
        parts.append(f"{label}：{'已识别' if key in mapping else '待确认'}")
    return "；".join(parts)


def _summarize_rows(headers: list[str], rows: list[list[str]], mapping: dict[str, str]) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    if "logfc" not in mapping or ("fdr" not in mapping and "pvalue" not in mapping):
        return {"status": "unavailable", "message": "缺少 logFC 或显著性列，待确认"}, [], []
    header_index = {header: index for index, header in enumerate(headers)}
    logfc_index = header_index.get(mapping["logfc"])
    sig_column = mapping.get("fdr") or mapping.get("pvalue")
    sig_index = header_index.get(sig_column or "")
    gene_index = header_index.get(mapping.get("gene", ""))
    if logfc_index is None or sig_index is None:
        return {"status": "unavailable", "message": "列映射无法定位，待确认"}, [], []
    up = down = not_significant = parsed = 0
    top_candidates: list[dict[str, object]] = []
    for row in rows:
        if max(logfc_index, sig_index) >= len(row):
            continue
        logfc = _to_float(row[logfc_index])
        sig = _to_float(row[sig_index])
        if logfc is None or sig is None:
            continue
        parsed += 1
        gene = row[gene_index].strip() if gene_index is not None and gene_index < len(row) else ""
        if sig <= 0.05 and logfc >= 1.0:
            up += 1
            top_candidates.append({"gene": gene, "logFC": logfc, "significance": sig, "direction": "up"})
        elif sig <= 0.05 and logfc <= -1.0:
            down += 1
            top_candidates.append({"gene": gene, "logFC": logfc, "significance": sig, "direction": "down"})
        else:
            not_significant += 1
    if not parsed:
        return {"status": "unavailable", "message": "没有可计算行，待确认"}, [], []
    top_up = sorted((item for item in top_candidates if item["direction"] == "up"), key=lambda item: (-abs(float(item["logFC"])), float(item["significance"])))[:10]
    top_down = sorted((item for item in top_candidates if item["direction"] == "down"), key=lambda item: (-abs(float(item["logFC"])), float(item["significance"])))[:10]
    return (
        {
            "status": "computed",
            "up": up,
            "down": down,
            "not_significant": not_significant,
            "parsed_rows": parsed,
            "threshold_note": "计数使用 |log2FC| >= 1 且 p value/FDR <= 0.05；仅用于导入结果浏览和报告草稿。",
        },
        top_up,
        top_down,
    )


def _status_label(status: str) -> str:
    return {
        "ready": "可浏览",
        "needs_confirmation": "格式待确认",
        "missing": "缺少文件",
    }.get(status, "不可用")


def _next_step(result: ImportedDegResult) -> str:
    if result.status == "ready":
        return "可查看详情或标记为报告候选；必须说明为外部导入结果。"
    if result.status == "needs_confirmation":
        return "请确认列映射后再纳入报告草稿。"
    return "请重新导入文件或修正项目记录。"


def _merge_mapping(auto_mapping: dict[str, str], manual_mapping: dict[str, str], headers: list[str]) -> dict[str, str]:
    valid_headers = set(headers)
    merged = dict(auto_mapping)
    for key, value in manual_mapping.items():
        if value in valid_headers:
            merged[key] = value
    return merged


def _load_manual_mapping(root: Path, result_id: str) -> tuple[dict[str, str], str, bool]:
    path = root / IMPORTED_DEG_ROOT / result_id / MANUAL_MAPPING_FILE
    if not path.exists():
        return {}, "", False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}, "", False
    raw_mapping = payload.get("column_mapping")
    mapping = {str(key): str(value) for key, value in raw_mapping.items()} if isinstance(raw_mapping, dict) else {}
    return mapping, str(payload.get("user_note") or ""), bool(payload.get("user_confirmed"))


def _result_short_description(result: ImportedDegResult) -> str:
    counts = result.regulation_counts
    if counts.get("status") == "computed":
        return f"用户导入的外部 DEG 表；上调 {counts.get('up')}，下调 {counts.get('down')}，不显著 {counts.get('not_significant')}。"
    return "用户导入的外部 DEG 表；列映射仍需确认。"


def _result_index_entry(root: Path, result: ImportedDegResult, manifest_path: Path) -> dict[str, object]:
    return {
        "result_id": result.result_id,
        "result_name": result.name,
        "result_type": "导入结果",
        "analysis_type": "differential_expression",
        "file_type": "table",
        "path": result.path,
        "source_label": "用户导入 / 外部差异分析结果",
        "status": "imported",
        "result_semantics": "imported result",
        "report_candidate": True,
        "report_usage_label": "可进入报告草稿，必须标明导入来源",
        "short_description": _result_short_description(result),
        "generated_at": result.generated_at,
        "manifest_ref": _relative_to_root(root, manifest_path),
        "display_action": "查看详情",
        "warning": "导入表格中的已有差异分析结果，不是 BioMedPilot 重新计算。",
    }


def _find_existing_entry(entries: list[dict[str, object]], result: ImportedDegResult) -> dict[str, object] | None:
    for entry in entries:
        if str(entry.get("result_id") or "") == result.result_id:
            return entry
        if str(entry.get("path") or entry.get("file_path") or "") == result.path:
            return entry
    return None


def _relative_to_root(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root).as_posix())
    except ValueError:
        return str(path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower())


def _slug_text(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-").lower()
    return slug or "imported-deg"


def _to_float(value: object) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
