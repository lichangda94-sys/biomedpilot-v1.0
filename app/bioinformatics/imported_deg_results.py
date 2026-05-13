from __future__ import annotations

import csv
import gzip
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from app.bioinformatics.project_recognition import load_recognition_report
from app.bioinformatics.results.project_results import load_result_index, write_result_index


PREVIEW_ROW_LIMIT = 20


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
    preview_headers: tuple[str, ...]
    preview_rows: tuple[tuple[str, ...], ...]
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
            "preview_headers": list(self.preview_headers),
            "preview_rows": [list(row) for row in self.preview_rows],
            "warning": self.warning,
            "semantic_boundary": "imported_external_deg_not_biomedpilot_computed",
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
        "results": [result.to_dict() for result in results],
    }


def mark_imported_deg_report_candidates(project_root: str | Path) -> list[dict[str, object]]:
    root = Path(project_root).expanduser().resolve()
    current = load_result_index(root)
    entries = [dict(item) for item in current.get("entries", []) or [] if isinstance(item, dict)]
    seen_paths = {str(item.get("path") or item.get("file_path") or "") for item in entries}
    for result in list_imported_deg_results(root):
        if result.path in seen_paths or result.status == "missing":
            continue
        entries.append(
            {
                "result_name": result.name,
                "analysis_type": "differential_expression",
                "file_type": "table",
                "path": result.path,
                "status": "imported",
                "result_semantics": "imported result",
                "report_candidate": True,
                "warning": "导入表格中的已有差异分析结果，不是 BioMedPilot 重新计算。",
            }
        )
        seen_paths.add(result.path)
    write_result_index(root, entries)
    return entries


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
            preview_headers=(),
            preview_rows=(),
            warning="文件缺失",
        )
    headers, rows = _read_preview(path)
    mapping = _map_columns(headers)
    column_status = _column_status(mapping)
    status = "ready" if {"gene", "logfc"} <= set(mapping) and ("fdr" in mapping or "pvalue" in mapping) else "needs_confirmation"
    report_status = "是" if status == "ready" else "需确认"
    return ImportedDegResult(
        result_id=result_id,
        name=name,
        path=str(path),
        source_label="用户导入 / 外部分析结果",
        status=status,
        report_status=report_status,
        column_mapping=mapping,
        column_status=column_status,
        regulation_counts=_regulation_counts(headers, rows, mapping),
        preview_headers=tuple(headers),
        preview_rows=tuple(tuple(cell for cell in row) for row in rows),
    )


def _read_preview(path: Path) -> tuple[list[str], list[list[str]]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace", newline="") as handle:  # type: ignore[arg-type]
        first = handle.readline()
        if not first:
            return [], []
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        header = next(csv.reader([first], delimiter=delimiter))
        rows = []
        reader = csv.reader(handle, delimiter=delimiter)
        for index, row in enumerate(reader):
            if index >= PREVIEW_ROW_LIMIT:
                break
            rows.append(row)
        return header, rows


def _map_columns(headers: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for header in headers:
        key = _normalize_header(header)
        if "gene" not in mapping and key in {"gene", "genes", "geneid", "genesymbol", "symbol", "id"}:
            mapping["gene"] = header
        elif "logfc" not in mapping and key in {"logfc", "log2fc", "log2foldchange", "avglog2fc"}:
            mapping["logfc"] = header
        elif "pvalue" not in mapping and key in {"pvalue", "pval", "p", "pvalue", "pvalueadjusted", "pvalnominal"}:
            mapping["pvalue"] = header
        elif "fdr" not in mapping and key in {"padj", "adjpval", "adjpvalue", "adjustedpvalue", "fdr", "qvalue"}:
            mapping["fdr"] = header
    return mapping


def _column_status(mapping: dict[str, str]) -> str:
    parts = []
    for key, label in (("gene", "gene"), ("logfc", "logFC / log2FC"), ("pvalue", "p value"), ("fdr", "padj / FDR")):
        parts.append(f"{label}：{'已识别' if key in mapping else '待确认'}")
    return "；".join(parts)


def _regulation_counts(headers: list[str], rows: list[list[str]], mapping: dict[str, str]) -> dict[str, object]:
    if "logfc" not in mapping or ("fdr" not in mapping and "pvalue" not in mapping):
        return {"status": "unavailable", "message": "缺少 logFC 或显著性列，待确认"}
    header_index = {header: index for index, header in enumerate(headers)}
    logfc_index = header_index.get(mapping["logfc"])
    sig_column = mapping.get("fdr") or mapping.get("pvalue")
    sig_index = header_index.get(sig_column or "")
    if logfc_index is None or sig_index is None:
        return {"status": "unavailable", "message": "列映射无法定位，待确认"}
    up = down = not_significant = parsed = 0
    for row in rows:
        if max(logfc_index, sig_index) >= len(row):
            continue
        logfc = _to_float(row[logfc_index])
        sig = _to_float(row[sig_index])
        if logfc is None or sig is None:
            continue
        parsed += 1
        if sig <= 0.05 and logfc >= 1.0:
            up += 1
        elif sig <= 0.05 and logfc <= -1.0:
            down += 1
        else:
            not_significant += 1
    if not parsed:
        return {"status": "unavailable", "message": "没有可计算行，待确认"}
    return {
        "status": "computed",
        "up": up,
        "down": down,
        "not_significant": not_significant,
        "parsed_preview_rows": parsed,
        "threshold_note": "预览计数使用 |log2FC| >= 1 且 p value/FDR <= 0.05；仅用于导入结果浏览确认。",
    }


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
