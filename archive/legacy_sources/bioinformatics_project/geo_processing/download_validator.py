"""Validation and asset organization for downloaded GEO datasets."""

from __future__ import annotations

import gzip
import json
import math
import os
import re
import tarfile
import zipfile
from collections import Counter, deque
from pathlib import Path
from typing import Any, Iterable

from .detector.matrix_classifier import classify_tabular_matrix, looks_like_diff_result_columns
from .detector.rules import RAW_EXTENSIONS
from .detector.utils import normalize_extension, preview_delimited_rows, preview_xlsx_rows, read_text_head
from .download_models import DownloadValidationResult, FileScoreResult
from .module1_contracts import (
    build_dataset_manifest_draft_payload,
    build_file_inventory_payload,
    build_handoff_package_payload,
    build_parser_hints_payload,
    normalize_file_role,
)

SYSTEM_NOISE_NAMES = {".ds_store", "thumbs.db", "desktop.ini"}
ACCESSION_RE = re.compile(r"(GSE\d+)", re.IGNORECASE)
GSM_RE = re.compile(r"\bGSM\d+\b", re.IGNORECASE)
SRA_URL_RE = re.compile(r"https?://\S*(?:sra|trace\.ncbi)\S*", re.IGNORECASE)
ARCHIVE_EXTENSIONS = {".zip", ".tar", ".tgz", ".tar.gz"}
TEXT_LIKE_EXTENSIONS = {
    ".txt",
    ".tsv",
    ".csv",
    ".soft",
    ".xml",
    ".txt.gz",
    ".tsv.gz",
    ".csv.gz",
    ".soft.gz",
    ".xml.gz",
    ".xls",
    ".xlsx",
}
STRUCTURED_BINARY_TEXT_EXTENSIONS = {".xls", ".xlsx"}
STREAM_MARKERS = (
    "^SERIES",
    "^SAMPLE",
    "!Series_",
    "!Sample_",
    "!sample_table_begin",
    "!sample_table_end",
    "!platform_table_begin",
    "!platform_table_end",
)
GENERATED_NAME_PATTERNS = (
    re.compile(r"download_validation\.json$", re.IGNORECASE),
    re.compile(r"module3_detection\.json$", re.IGNORECASE),
    re.compile(r"sandbox_summary\.json$", re.IGNORECASE),
    re.compile(r"selected_results\.(json|csv)$", re.IGNORECASE),
    re.compile(r"remote_candidates\.json$", re.IGNORECASE),
    re.compile(r"scored_candidates\.json$", re.IGNORECASE),
    re.compile(r".*_download_summary\.json$", re.IGNORECASE),
    re.compile(r"run_summary\.json$", re.IGNORECASE),
    re.compile(r"group_summary\.csv$", re.IGNORECASE),
    re.compile(r"phenotype_table\.csv$", re.IGNORECASE),
    re.compile(r"expression_.*\.csv$", re.IGNORECASE),
    re.compile(r"download_transaction_log\.json$", re.IGNORECASE),
    re.compile(r"core_download_summary\.json$", re.IGNORECASE),
    re.compile(r"expected_vs_actual_diff\.json$", re.IGNORECASE),
)
HTML_ERROR_PATTERNS = (
    "<html",
    "<!doctype html",
    "<head",
    "<body",
    "<title",
)
EXPRESSION_NAME_HINTS = (
    "matrix",
    "expression",
    "expr",
    "counts",
    "normalized",
    "tpm",
    "fpkm",
    "rpkm",
    "series_matrix",
)
SAMPLE_NAME_HINTS = (
    "sample",
    "metadata",
    "phenotype",
    "design",
    "annotation",
    "group",
    "characteristics",
)
CLINICAL_HINTS = (
    "clinical",
    "patient",
    "survival",
    "outcome",
    "response",
    "stage",
    "grade",
    "pathology",
)
PLATFORM_HINTS = ("gpl", "platform", "annotation", "probe", "mapping", "gene symbol")
README_HINTS = ("readme", "protocol", "note", "summary", "instruction", "method")
SUPPORTING_DOC_HINTS = README_HINTS + ("pdf", "format", "read me")
DIFF_NAME_HINTS = ("deg", "deseq", "edger", "limma", "volcano", "differential")
DIFF_COLUMN_HINTS = (
    "logfc",
    "padj",
    "adj.p.val",
    "adj_p_val",
    "adj p val",
    "p.value",
    "p_value",
    "p value",
    "pvalue",
    "basemean",
    "lfcse",
    "qvalue",
    "fdr",
)
CLINICAL_COLUMNS = {
    "age",
    "sex",
    "gender",
    "stage",
    "grade",
    "survival",
    "os",
    "dfs",
    "recurrence",
    "metastasis",
    "response",
    "pathology",
}
SAMPLE_COLUMNS = {
    "gsm",
    "sample_id",
    "sample",
    "title",
    "source_name",
    "characteristics",
    "group",
    "condition",
    "treatment",
    "subtype",
    "mutation",
    "replicate",
    "timepoint",
}
FEATURE_COLUMNS = {"id_ref", "gene", "gene_id", "symbol", "probe", "probe_id", "transcript_id", "ensembl_gene_id"}

EXPRESSION_THRESHOLD = 0.62
SAMPLE_ANNOTATION_THRESHOLD = 0.5
CLINICAL_THRESHOLD = 0.55
RAW_THRESHOLD = 0.8
PLATFORM_THRESHOLD = 0.58
JUNK_THRESHOLD = 0.75

TOP_LEVEL_FAILURE_STAGES = {
    "source_landing",
    "content_inspection",
    "semantic_classification",
    "dataset_aggregation",
}
FAILURE_STAGE_ALIASES = {
    "remote_discovery": "source_landing",
    "remote_scoring": "source_landing",
    "download_execution": "source_landing",
    "source_landing": "source_landing",
    "local_validation": "content_inspection",
    "content_inspection": "content_inspection",
    "file_classification": "semantic_classification",
    "semantic_classification": "semantic_classification",
    "dataset_detection": "dataset_aggregation",
    "organization": "dataset_aggregation",
    "sandbox_render": "dataset_aggregation",
    "dataset_aggregation": "dataset_aggregation",
}
FAILURE_STAGES = set(FAILURE_STAGE_ALIASES)
PRIMARY_STAGE_SNAPSHOT_NAMES = {
    "source_landing": "01_source_landing.json",
    "content_inspection": "02_content_inspection.json",
    "semantic_classification": "03_semantic_classification.json",
    "dataset_aggregation": "04_dataset_aggregation.json",
}


def _append_unique(bucket: list[str], message: str | None) -> None:
    if message and message not in bucket:
        bucket.append(message)


def _trace_file(result: FileScoreResult, message: str | None) -> None:
    _append_unique(result.decision_trace, message)


def _should_export_debug_snapshots(root: Path) -> bool:
    return True


def normalize_failure_stage(stage: str | None) -> str | None:
    if not stage:
        return None
    return FAILURE_STAGE_ALIASES.get(stage, stage)


def attach_sub_failure_stage(payload: dict[str, Any], stage: str | None) -> dict[str, Any]:
    normalized = normalize_failure_stage(stage)
    if not normalized:
        return payload
    payload["failure_stage"] = normalized
    if stage and stage != normalized:
        payload["sub_failure_stage"] = stage
    return payload


def _write_debug_snapshot(root: Path, name: str, payload: Any) -> str:
    snapshot_dir = root / "organized" / "reports" / "debug_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    file_name = PRIMARY_STAGE_SNAPSHOT_NAMES.get(name, f"{name}.json")
    path = snapshot_dir / file_name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def _load_expected_payload(root: Path) -> dict[str, Any] | None:
    expected_path = root / "expected.json"
    if not expected_path.exists():
        return None
    try:
        payload = json.loads(expected_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _build_expected_vs_actual_payload(root: Path, actual: dict[str, Any]) -> dict[str, Any]:
    expected_path = root / "expected.json"
    expected = _load_expected_payload(root)
    if expected is None:
        return {
            "enabled": False,
            "expected_path": str(expected_path),
            "matched_fields": [],
            "mismatched_fields": [],
            "likely_failure_stage": None,
            "summary": "expected.json not found; 未启用对照测试",
        }
    diff = compare_expected_vs_actual(expected, actual)
    return {
        "enabled": True,
        "expected_path": str(expected_path),
        **diff,
    }


def _write_expected_vs_actual_outputs(root: Path, payload: dict[str, Any]) -> dict[str, str]:
    reports_dir = root / "organized" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "expected_vs_actual_diff.json"
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    debug_path = Path(_write_debug_snapshot(root, "expected_vs_actual_diff", payload))
    return {
        "report": str(report_path),
        "debug_snapshot": str(debug_path),
    }


def _collect_existing_stage_payloads(root: Path) -> dict[str, Any]:
    stage_files = {
        "remote_candidates": "remote_candidates.json",
        "scored_candidates": "scored_candidates.json",
        "download_plan": "download_plan.json",
        "transaction_log": "download_transaction_log.json",
    }
    collected: dict[str, Any] = {}
    for stage_name, file_name in stage_files.items():
        matches = sorted(root.rglob(file_name))
        if not matches:
            collected[stage_name] = {"available": False, "source": None, "payload": None}
            continue
        source = matches[0]
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except Exception as exc:
            collected[stage_name] = {
                "available": False,
                "source": str(source),
                "payload": {"error": f"failed to read {file_name}: {exc}"},
            }
            continue
        collected[stage_name] = {"available": True, "source": str(source), "payload": payload}
    return collected


def _default_top_problem_summary(status: str, failure_reason: str | None) -> str:
    if failure_reason:
        return f"{status}: {failure_reason}"
    return f"{status}: no blocking issue detected"


def _default_suggested_next_fix(next_action: str | None) -> str:
    return next_action or "inspect decision_trace, conflicts, and stage snapshots to identify the next layer to adjust"


def _infer_failure_stage_from_fields(fields: list[str]) -> str:
    download_fields = {"status", "download_success", "file_count", "nonempty_file_count", "errors", "broken_files"}
    local_fields = {"candidate_matrix_files", "candidate_metadata_files", "candidate_clinical_files", "payload_type"}
    classification_fields = {"has_expression_payload", "has_sample_annotation", "has_clinical_annotation", "expression_sources", "raw_files", "platform_annotation_files"}
    detection_fields = {"technology_type", "matrix_level", "value_semantic", "recommended_strategy", "confidence"}
    if any(field in download_fields for field in fields):
        return "source_landing"
    if any(field in detection_fields for field in fields):
        return "dataset_aggregation"
    if any(field in classification_fields for field in fields):
        return "semantic_classification"
    if any(field in local_fields for field in fields):
        return "content_inspection"
    return "content_inspection"


def compare_expected_vs_actual(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    matched_fields: list[str] = []
    mismatched_fields: list[dict[str, Any]] = []
    for field, expected_value in expected.items():
        actual_value = actual.get(field)
        if actual_value == expected_value:
            matched_fields.append(field)
        else:
            mismatched_fields.append({"field": field, "expected": expected_value, "actual": actual_value})
    likely_failure_stage = _infer_failure_stage_from_fields([item["field"] for item in mismatched_fields])
    summary = (
        "all expected fields matched"
        if not mismatched_fields
        else f"{len(matched_fields)} matched, {len(mismatched_fields)} mismatched; likely drift starts at {likely_failure_stage}"
    )
    return {
        "matched_fields": matched_fields,
        "mismatched_fields": mismatched_fields,
        "likely_failure_stage": likely_failure_stage if mismatched_fields else None,
        "summary": summary,
    }


def _ensure_validation_defaults(result: DownloadValidationResult) -> DownloadValidationResult:
    result.failure_stage = normalize_failure_stage(result.failure_stage) or "content_inspection"
    result.top_problem_summary = result.top_problem_summary or _default_top_problem_summary(result.status, result.failure_reason)
    result.suggested_next_fix = result.suggested_next_fix or _default_suggested_next_fix(result.next_action)
    return result


def normalize_gse_id(gse_id: str, download_dir: str) -> str:
    """Prefer accession parsed from actual GEO files over directory names."""
    root = Path(download_dir).expanduser().resolve()
    candidate_names: list[str] = [(gse_id or "").strip(), root.name]
    if root.exists():
        geo_like_patterns = (
            "*family.soft*",
            "*series_matrix*",
            "*.miniml*",
            "*.xml",
            "GPL*",
            "GSE*",
        )
        for pattern in geo_like_patterns:
            candidate_names.extend(path.name for path in root.rglob(pattern) if path.is_file())
    for candidate in candidate_names:
        match = ACCESSION_RE.search(candidate.upper())
        if match:
            return match.group(1).upper()
    return (gse_id or root.name).strip().upper() or root.name.upper()


def _is_generated_output(root: Path, path: Path) -> bool:
    relative = path.relative_to(root)
    lower = str(relative).lower()
    if path.name.lower() in SYSTEM_NOISE_NAMES or path.name.startswith("._"):
        return True
    if any(part.lower() == "__macosx" for part in relative.parts):
        return True
    if any(part.lower() == "organized" for part in relative.parts):
        return True
    if any(part.lower().startswith("processed_gse") for part in relative.parts):
        return True
    return any(pattern.search(lower) for pattern in GENERATED_NAME_PATTERNS)


def scan_download_directory(download_dir: str) -> list[str]:
    root = Path(download_dir).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        return []
    return [
        str(path)
        for path in sorted(item for item in root.rglob("*") if item.is_file())
        if not _is_generated_output(root, path)
    ]


def _load_download_transaction_context(download_dir: str) -> dict[str, Any]:
    root = Path(download_dir).expanduser().resolve()
    candidates = [
        root / "raw_downloads" / "reports" / "download_transaction_log.json",
        root / "raw_downloads" / "geo_downloads" / "download_transaction_log.json",
    ]
    payload = {"transaction_log": [], "errors": [], "summary": None}
    summary_path = root / "raw_downloads" / "reports" / "core_download_summary.json"
    if summary_path.exists():
        try:
            payload["summary"] = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception as exc:
            payload["errors"].append(f"failed to read core download summary: {exc}")
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            entries = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception as exc:
            payload["errors"].append(f"failed to read download transaction log: {exc}")
            continue
        if not isinstance(entries, list):
            payload["errors"].append("download transaction log is not a list")
            continue
        payload["transaction_log"] = entries
        for entry in entries:
            if entry.get("error_message"):
                payload["errors"].append(str(entry["error_message"]))
            elif entry.get("response_status") == "failed":
                payload["errors"].append("request failed without explicit error message")
            elif entry.get("response_status") == "recorded_only":
                continue
            elif entry.get("response_status") == "success" and (
                not entry.get("file_exists_after_save") or not entry.get("final_size_on_disk", 0)
            ):
                payload["errors"].append("zero-byte file saved or destination path mismatch")
        break
    summary = payload.get("summary") or {}
    if summary.get("error"):
        payload["errors"].append(str(summary["error"]))
    for item in summary.get("errors", []) or []:
        payload["errors"].append(str(item))
    return payload


def check_download_path_consistency(download_dir: str) -> dict[str, Any]:
    root = Path(download_dir).expanduser().resolve()
    summary_path = root / "raw_downloads" / "reports" / "core_download_summary.json"
    summary: dict[str, Any] = {}
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            summary = {}
    path_consistency = dict(summary.get("path_consistency", {}))
    if path_consistency:
        return path_consistency
    return {
        "dataset_root": str(root),
        "downloader_writes_to": str(root / "raw_downloads"),
        "validation_scans": str(root),
        "organized_reports_to": str(root / "organized" / "reports"),
        "raw_report_dir": str(root / "raw_downloads" / "reports"),
        "download_targets": [],
        "paths_consistent": True,
        "outside_raw_download_root": [],
    }


def _safe_preview(file_path: str, max_lines: int = 12) -> list[str]:
    extension = normalize_extension(file_path)
    if extension in {".xls", ".xlsx"}:
        return ["\t".join(row) for row in preview_xlsx_rows(file_path, max_rows=max_lines, max_columns=12)]
    return read_text_head(file_path, max_lines=max_lines, max_bytes=65536)


def _open_text_handle(file_path: str):
    if normalize_extension(file_path).endswith(".gz"):
        return gzip.open(file_path, "rt", encoding="utf-8", errors="replace")
    return Path(file_path).open("rt", encoding="utf-8", errors="replace")


def can_open_gzip_preview(file_path: str) -> bool:
    try:
        with gzip.open(file_path, "rt", encoding="utf-8", errors="replace") as handle:
            handle.readline()
        return True
    except Exception:
        return False


def _looks_binary(file_path: str) -> bool:
    try:
        with Path(file_path).open("rb") as handle:
            chunk = handle.read(512)
    except OSError:
        return False
    return bool(chunk) and b"\x00" in chunk


def _preview_rows(file_path: str, preview_lines: list[str]) -> list[list[str]]:
    extension = normalize_extension(file_path)
    if extension in {".xls", ".xlsx"}:
        return [line.split("\t") for line in preview_lines]
    return preview_delimited_rows(preview_lines)


def _preview_text_like_lines(file_path: str, max_lines: int = 40) -> list[str]:
    extension = normalize_extension(file_path)
    if extension in {".xls", ".xlsx"}:
        return ["\t".join(row) for row in preview_xlsx_rows(file_path, max_rows=max_lines, max_columns=40)]
    return read_text_head(file_path, max_lines=max_lines, max_bytes=262144)


def is_html_error_page(file_path: str) -> bool:
    extension = normalize_extension(file_path)
    if extension in STRUCTURED_BINARY_TEXT_EXTENSIONS or extension in RAW_EXTENSIONS or path_looks_like_archive(file_path.lower()):
        return False
    preview_lines = [line.strip() for line in _safe_preview(file_path, max_lines=12) if line.strip()]
    preview = "\n".join(preview_lines).lower()
    if not preview:
        return False
    if any(token in preview for token in HTML_ERROR_PATTERNS):
        return True
    if len(preview_lines) > 3:
        return False
    return preview.startswith(("404", "not found", "access denied", "forbidden", "redirecting"))


def _has_diff_result_hints(lowered_name: str, header: list[str], preview_lines: list[str]) -> bool:
    if any(token in lowered_name for token in DIFF_NAME_HINTS):
        return True
    header_text = "\t".join(str(item).strip().lower() for item in header if str(item).strip())
    if header_text:
        header_hits = sum(1 for token in DIFF_COLUMN_HINTS if token in header_text)
        if header_hits >= 2:
            return True
    preview_head = "\n".join(line.strip().lower() for line in preview_lines[:5] if line.strip())
    preview_hits = sum(1 for token in DIFF_COLUMN_HINTS if token in preview_head)
    return preview_hits >= 2


def _section_signals(lines: list[str]) -> list[str]:
    signals: list[str] = []
    rows = preview_delimited_rows(lines)
    dense_rows = preview_delimited_rows([line for line in lines if "\t" in line or "," in line])
    table_rows = dense_rows or rows
    lowered = "\n".join(lines).lower()
    if any(line.startswith("^SERIES") for line in lines):
        signals.append("series_block")
    if any(line.startswith("^SAMPLE") for line in lines):
        signals.append("sample_block")
    if any("!sample_table_begin" in line.lower() for line in lines):
        signals.append("sample_table_marker")
    if any("!platform_table_begin" in line.lower() for line in lines):
        signals.append("platform_table_marker")
    if any("!sample_table_end" in line.lower() for line in lines):
        signals.append("sample_table_end_marker")
    if any("!platform_table_end" in line.lower() for line in lines):
        signals.append("platform_table_end_marker")
    if table_rows and max((len(row) for row in table_rows), default=0) >= 4:
        signals.append("tabular_block")
    if table_rows:
        numeric = _numeric_stats(table_rows)
        sample_cols = _sample_columns(table_rows[0])
        if numeric["numeric_ratio"] >= 0.55 and len(sample_cols) >= 2:
            signals.append("numeric_matrix_block")
        if table_rows[0] and table_rows[0][0].strip().lower() in FEATURE_COLUMNS:
            signals.append("feature_id_column")
    if GSM_RE.search(lowered):
        signals.append("gsm_identifiers")
    return sorted(dict.fromkeys(signals))


def sample_text_file_sections(file_path: str, max_lines_per_section: int = 40) -> dict[str, Any]:
    extension = normalize_extension(file_path)
    if extension in {".xls", ".xlsx"}:
        head = _preview_text_like_lines(file_path, max_lines=max_lines_per_section)
        return {
            "head_preview": head,
            "middle_preview": head,
            "tail_preview": head,
            "head_signals": _section_signals(head),
            "middle_signals": _section_signals(head),
            "tail_signals": _section_signals(head),
            "line_count": len(head),
        }

    head: list[str] = []
    middle_window: deque[str] = deque(maxlen=max_lines_per_section * 2)
    tail_window: deque[str] = deque(maxlen=max_lines_per_section)
    line_count = 0
    try:
        with _open_text_handle(file_path) as handle:
            for raw_line in handle:
                line = raw_line.rstrip("\n\r")
                line_count += 1
                if len(head) < max_lines_per_section:
                    head.append(line)
                middle_window.append(line)
                tail_window.append(line)
    except Exception:
        return {
            "head_preview": [],
            "middle_preview": [],
            "tail_preview": [],
            "head_signals": [],
            "middle_signals": [],
            "tail_signals": [],
            "line_count": 0,
        }

    if line_count <= max_lines_per_section * 3:
        middle = list(middle_window)[:max_lines_per_section]
    else:
        middle_list = list(middle_window)
        start = max(0, (len(middle_list) - max_lines_per_section) // 2)
        middle = middle_list[start : start + max_lines_per_section]

    tail = list(tail_window)
    return {
        "head_preview": head,
        "middle_preview": middle,
        "tail_preview": tail,
        "head_signals": _section_signals(head),
        "middle_signals": _section_signals(middle),
        "tail_signals": _section_signals(tail),
        "line_count": line_count,
    }


def scan_geo_markers_streaming(file_path: str, markers: list[str] | tuple[str, ...]) -> dict[str, int]:
    marker_counts = {marker: 0 for marker in markers}
    try:
        with _open_text_handle(file_path) as handle:
            for raw_line in handle:
                line = raw_line.rstrip("\n\r")
                lowered = line.lower()
                for marker in markers:
                    needle = marker.lower()
                    if needle.startswith("^"):
                        if lowered.startswith(needle):
                            marker_counts[marker] += 1
                    elif needle in lowered:
                        marker_counts[marker] += 1
    except Exception:
        return marker_counts
    return marker_counts


def inspect_large_text_like_file(file_path: str) -> dict[str, Any]:
    section_data = sample_text_file_sections(file_path)
    marker_counts = scan_geo_markers_streaming(file_path, STREAM_MARKERS)
    global_markers_found = [marker for marker, count in marker_counts.items() if count > 0]
    inferred_structure = []
    for key in ("head_signals", "middle_signals", "tail_signals"):
        for signal in section_data.get(key, []):
            if signal not in inferred_structure:
                inferred_structure.append(signal)
    if marker_counts.get("!sample_table_begin", 0):
        inferred_structure.append("sample_table_present")
    if marker_counts.get("!platform_table_begin", 0):
        inferred_structure.append("platform_table_present")
    if marker_counts.get("^SAMPLE", 0) >= 2:
        inferred_structure.append("multiple_sample_blocks")
    if (
        "numeric_matrix_block" in section_data.get("middle_signals", [])
        or "numeric_matrix_block" in section_data.get("tail_signals", [])
    ):
        inferred_structure.append("matrix_like_middle_or_tail")
    return {
        **section_data,
        "marker_counts": marker_counts,
        "global_markers_found": global_markers_found,
        "inferred_structure": inferred_structure,
    }


def _soft_scan(file_path: str, max_lines: int = 15000, max_bytes: int = 2_000_000) -> dict[str, Any]:
    marker_counts = {"sample_blocks": 0, "sample_table_begin": 0, "sample_table_end": 0, "sample_attrs": 0, "series_attrs": 0}
    sample_ids: set[str] = set()
    lines_scanned = 0
    bytes_scanned = 0
    opener = gzip.open if normalize_extension(file_path).endswith(".gz") else Path(file_path).open
    try:
        with opener(file_path, "rt", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                lines_scanned += 1
                bytes_scanned += len(line.encode("utf-8", errors="ignore"))
                lowered = line.strip().lower()
                if lowered.startswith("^sample"):
                    marker_counts["sample_blocks"] += 1
                if lowered.startswith("!sample_table_begin"):
                    marker_counts["sample_table_begin"] += 1
                if lowered.startswith("!sample_table_end"):
                    marker_counts["sample_table_end"] += 1
                if lowered.startswith("!sample_"):
                    marker_counts["sample_attrs"] += 1
                if lowered.startswith("!series_"):
                    marker_counts["series_attrs"] += 1
                for gsm in GSM_RE.findall(line):
                    sample_ids.add(gsm.upper())
                if lines_scanned >= max_lines or bytes_scanned >= max_bytes:
                    break
    except Exception:
        return {"lines_scanned": 0, "sample_count": 0, "has_sample_table": False, "marker_counts": marker_counts}
    return {
        "lines_scanned": lines_scanned,
        "sample_count": len(sample_ids),
        "has_sample_table": marker_counts["sample_table_begin"] > 0,
        "marker_counts": marker_counts,
    }


def _numeric_stats(rows: list[list[str]]) -> dict[str, Any]:
    total = 0
    numeric = 0
    values: list[float] = []
    for row in rows[1:]:
        for cell in row[1:]:
            value = str(cell).strip()
            if not value:
                continue
            total += 1
            try:
                number = float(value)
            except ValueError:
                continue
            numeric += 1
            if math.isfinite(number):
                values.append(number)
    return {
        "numeric_ratio": (numeric / total) if total else 0.0,
        "value_count": len(values),
        "integer_ratio": sum(float(value).is_integer() for value in values) / len(values) if values else 0.0,
    }


def _sample_columns(header: Iterable[str]) -> list[str]:
    cleaned = [str(item).strip() for item in header if str(item).strip()]
    return [
        item
        for item in cleaned[1:]
        if item.lower() not in FEATURE_COLUMNS and not item.lower().endswith("_id") and item.lower() not in CLINICAL_COLUMNS
    ]


def _add_score(current: float, delta: float, bucket: list[str], reason: str) -> float:
    bucket.append(reason)
    return current + delta


def _guess_source_scope(relative_path: str) -> str:
    lowered = relative_path.lower()
    if "raw_downloads/supplementary" in lowered or lowered.startswith("supplementary/") or "/supplementary/" in lowered:
        return "series_supplementary"
    if "metadata_records" in lowered:
        return "metadata_record"
    if any(part in lowered for part in ("raw_downloads", "geo_downloads", "supplementary", "metadata_records")):
        return "downloaded"
    if lowered.startswith(".") or "/." in lowered:
        return "system"
    return "downloaded"


def inspect_archive_file(file_path: str) -> dict[str, Any]:
    path = Path(file_path)
    members: list[str] = []
    try:
        if normalize_extension(str(path)) == ".zip":
            with zipfile.ZipFile(path) as archive:
                members = archive.namelist()[:300]
        else:
            with tarfile.open(path) as archive:
                members = [member.name for member in archive.getmembers()[:300]]
    except Exception as exc:
        return {
            "archive_contains_candidate_expression": False,
            "archive_contains_raw_data": False,
            "archive_contains_annotation": False,
            "archive_contains_supporting_docs": False,
            "archive_member_count": 0,
            "archive_preview_members": [],
            "warnings": [f"archive inspection failed: {exc}"],
        }

    lowered = "\n".join(members).lower()
    return {
        "archive_contains_candidate_expression": any(token in lowered for token in EXPRESSION_NAME_HINTS),
        "archive_contains_raw_data": any(ext in lowered for ext in RAW_EXTENSIONS),
        "archive_contains_annotation": any(token in lowered for token in PLATFORM_HINTS + SAMPLE_NAME_HINTS),
        "archive_contains_supporting_docs": any(token in lowered for token in SUPPORTING_DOC_HINTS),
        "archive_member_count": len(members),
        "archive_preview_members": members[:25],
        "warnings": [],
    }


def score_remote_candidate(file_meta: dict) -> float:
    """Score supplementary metadata from the remote side before local download."""
    name = str(file_meta.get("name") or file_meta.get("file_name") or "").lower()
    url = str(file_meta.get("remote_url") or file_meta.get("url") or "").lower()
    extension = normalize_extension(name or url)
    score = 0.0
    if any(token in name or token in url for token in EXPRESSION_NAME_HINTS):
        score += 0.35
    if any(token in name or token in url for token in SAMPLE_NAME_HINTS):
        score += 0.18
    if any(token in name or token in url for token in CLINICAL_HINTS):
        score += 0.12
    if extension in RAW_EXTENSIONS:
        score += 0.22
    if extension in ARCHIVE_EXTENSIONS:
        score += 0.16
    if any(token in name or token in url for token in PLATFORM_HINTS):
        score += 0.1
    if any(token in name or token in url for token in README_HINTS):
        score -= 0.15
    return round(max(0.0, min(1.0, score)), 3)


def score_local_file_candidate(file_info: dict) -> FileScoreResult:
    source_level = str(file_info.get("source_level") or file_info.get("source_scope") or "downloaded")
    source_path = str(file_info.get("source_path") or file_info.get("relative_path") or file_info.get("path") or "")
    result = FileScoreResult(
        path=str(file_info["path"]),
        relative_path=str(file_info["relative_path"]),
        size_bytes=int(file_info["size_bytes"]),
        source_level=source_level,
        source_path=source_path,
        source_scope=source_level,
    )
    extension = str(file_info["extension"])
    preview_lines = list(file_info.get("preview_lines", []))
    preview_rows = list(file_info.get("preview_rows", [])) or _preview_rows(result.path, preview_lines)
    header = preview_rows[0] if preview_rows else []
    sample_columns = _sample_columns(header)
    numeric = _numeric_stats(preview_rows)
    lowered_name = result.relative_path.lower()
    lowered_preview = "\n".join(preview_lines[:20]).lower()
    container_type = str(file_info.get("container_type", "unknown"))
    soft_scan = dict(file_info.get("soft_scan", {}))
    matrix_classification = dict(file_info.get("matrix_classification", {}))
    section_scan = dict(file_info.get("section_scan", {}))
    archive_info = dict(file_info.get("archive_info", {}))
    section_has_matrix = "numeric_matrix_block" in section_scan.get("middle_signals", []) or "numeric_matrix_block" in section_scan.get("tail_signals", [])
    section_has_feature_ids = "feature_id_column" in section_scan.get("middle_signals", []) or "feature_id_column" in section_scan.get("tail_signals", [])

    result.preview_lines = preview_lines[:12]
    result.extra = {
        "source_level": result.source_level,
        "source_path": result.source_path,
        "extension": extension,
        "container_type": container_type,
        "sample_column_count": len(sample_columns),
        "numeric_ratio": round(numeric["numeric_ratio"], 3),
        "soft_scan": soft_scan,
        "matrix_classification": matrix_classification,
        "archive_info": archive_info,
        "head_preview": list(section_scan.get("head_preview", [])),
        "middle_preview": list(section_scan.get("middle_preview", [])),
        "tail_preview": list(section_scan.get("tail_preview", [])),
        "head_signals": list(section_scan.get("head_signals", [])),
        "middle_signals": list(section_scan.get("middle_signals", [])),
        "tail_signals": list(section_scan.get("tail_signals", [])),
        "global_markers_found": list(section_scan.get("global_markers_found", [])),
        "marker_counts": dict(section_scan.get("marker_counts", {})),
        "inferred_structure": list(section_scan.get("inferred_structure", [])),
    }

    if file_info.get("excluded"):
        result.excluded = True
        result.excluded_reason = str(file_info.get("excluded_reason"))
        result.primary_label = "ignored"
        result.confidence = 1.0
        result.junk_score = 1.0
        result.reasons.append(result.excluded_reason)
        _trace_file(result, f"excluded because {result.excluded_reason}")
        return result

    if extension in RAW_EXTENSIONS:
        result.raw_data_score = _add_score(result.raw_data_score, 0.9, result.reasons, "known raw-data extension detected")
        _trace_file(result, f"local extension indicates raw data {extension}")
    if extension in ARCHIVE_EXTENSIONS or path_looks_like_archive(result.relative_path):
        result.extra["is_archive"] = True
        result.raw_data_score = _add_score(result.raw_data_score, 0.12, result.reasons, "archive retained for inspection")
        _trace_file(result, "filename suggests archive payload")
        if archive_info.get("archive_contains_candidate_expression"):
            result.expression_score = _add_score(result.expression_score, 0.22, result.reasons, "archive contains expression-like members")
            _trace_file(result, "archive inspection found expression-like members")
        if archive_info.get("archive_contains_raw_data"):
            result.raw_data_score = _add_score(result.raw_data_score, 0.35, result.reasons, "archive contains raw-data members")
            _trace_file(result, "archive inspection found raw-data members")
        if archive_info.get("archive_contains_annotation"):
            result.platform_annotation_score = _add_score(result.platform_annotation_score, 0.16, result.reasons, "archive contains annotation-like members")
            _trace_file(result, "archive inspection found annotation-like members")
        if archive_info.get("archive_contains_supporting_docs"):
            result.junk_score = _add_score(result.junk_score, 0.08, result.warnings, "archive contains supporting documentation")

    if any(token in lowered_name for token in EXPRESSION_NAME_HINTS):
        result.expression_score = _add_score(result.expression_score, 0.2, result.reasons, "filename contains expression-style keyword")
        _trace_file(result, "filename suggests processed expression payload")
    if container_type == "series_matrix":
        result.expression_score = _add_score(result.expression_score, 0.35, result.reasons, "series_matrix container detected")
        _trace_file(result, "container recognized as series_matrix")
    if section_has_matrix:
        result.expression_score = _add_score(result.expression_score, 0.18, result.reasons, "middle/tail section contains numeric matrix-like block")
        _trace_file(result, "section scan found numeric matrix block")
    if section_has_feature_ids:
        result.expression_score = _add_score(result.expression_score, 0.1, result.reasons, "middle/tail section exposes feature identifier column")
        _trace_file(result, "section scan found feature identifier column")
    if rows_look_tabular(preview_rows):
        result.expression_score = _add_score(result.expression_score, 0.08, result.reasons, "tabular preview parsed successfully")
    if len(preview_rows) >= 4 and len(header) >= 3:
        result.expression_score = _add_score(result.expression_score, 0.08, result.reasons, "table has enough rows and columns")
    if numeric["numeric_ratio"] >= 0.6:
        result.expression_score = _add_score(result.expression_score, 0.18, result.reasons, "high numeric cell ratio")
    if len(sample_columns) >= 2:
        result.expression_score = _add_score(result.expression_score, 0.16, result.reasons, "multiple sample-like columns detected")
    if header and header[0].strip().lower() in FEATURE_COLUMNS:
        result.expression_score = _add_score(result.expression_score, 0.12, result.reasons, "feature identifier column detected")
    if matrix_classification.get("is_expression_matrix"):
        result.expression_score = _add_score(result.expression_score, 0.16, result.reasons, "matrix classifier supports expression payload")
        _trace_file(result, "matrix classifier passed")
    if result.size_bytes >= 8_192:
        result.expression_score = _add_score(result.expression_score, 0.04, result.reasons, "file size supports non-trivial payload")

    if container_type in {"family_soft", "miniml", "series_matrix"}:
        result.sample_annotation_score = _add_score(result.sample_annotation_score, 0.24, result.reasons, "metadata-capable GEO container detected")
        _trace_file(result, "container can carry GEO metadata")
    if container_type == "family_soft":
        result.sample_annotation_score = _add_score(result.sample_annotation_score, 0.08, result.reasons, "family.soft metadata source detected")
        _trace_file(result, "container recognized as family.soft")
    if any(token in lowered_name for token in SAMPLE_NAME_HINTS):
        result.sample_annotation_score = _add_score(result.sample_annotation_score, 0.18, result.reasons, "filename contains sample-annotation keyword")
    if any(column.strip().lower() in SAMPLE_COLUMNS for column in header):
        result.sample_annotation_score = _add_score(result.sample_annotation_score, 0.2, result.reasons, "sample-annotation columns detected")
    if GSM_RE.search(lowered_preview):
        result.sample_annotation_score = _add_score(result.sample_annotation_score, 0.14, result.reasons, "GSM identifiers detected")
    if soft_scan.get("sample_count", 0) >= 2:
        result.sample_annotation_score = _add_score(result.sample_annotation_score, 0.18, result.reasons, "family.soft full scan found multiple sample blocks")
    if soft_scan.get("marker_counts", {}).get("sample_attrs", 0) >= 2:
        result.sample_annotation_score = _add_score(result.sample_annotation_score, 0.08, result.reasons, "family.soft contains sample-level attributes")
    if soft_scan.get("has_sample_table"):
        result.sample_annotation_score = _add_score(result.sample_annotation_score, 0.16, result.reasons, "family.soft full scan found sample_table markers")
    if section_scan.get("marker_counts", {}).get("^SAMPLE", 0) >= 2:
        result.sample_annotation_score = _add_score(result.sample_annotation_score, 0.12, result.reasons, "streaming marker scan found multiple ^SAMPLE blocks")

    if any(token in lowered_name for token in CLINICAL_HINTS):
        result.clinical_score = _add_score(result.clinical_score, 0.2, result.reasons, "filename contains clinical keyword")
        _trace_file(result, "filename suggests clinical payload")
    clinical_column_hits = len({column.strip().lower() for column in header} & CLINICAL_COLUMNS)
    if clinical_column_hits >= 2:
        result.clinical_score = _add_score(result.clinical_score, 0.28, result.reasons, "clinical columns detected")
    elif clinical_column_hits >= 1 and GSM_RE.search(lowered_preview):
        result.clinical_score = _add_score(result.clinical_score, 0.12, result.reasons, "clinical fields align with sample rows")

    if any(token in lowered_name for token in PLATFORM_HINTS):
        result.platform_annotation_score = _add_score(result.platform_annotation_score, 0.28, result.reasons, "filename contains platform-annotation keyword")
        _trace_file(result, "filename suggests platform annotation")
    if header and header[0].strip().lower() in {"id", "probe", "probe_id"} and any("gene" in column.lower() for column in header[1:4]):
        result.platform_annotation_score = _add_score(result.platform_annotation_score, 0.22, result.reasons, "probe-to-gene mapping structure detected")
    if container_type == "platform_annotation":
        result.platform_annotation_score = _add_score(result.platform_annotation_score, 0.3, result.reasons, "platform annotation container detected")

    if any(token in lowered_name for token in README_HINTS):
        result.junk_score = _add_score(result.junk_score, 0.4, result.warnings, "looks like readme/protocol/note file")
        _trace_file(result, "filename suggests supporting documentation")
    if _has_diff_result_hints(lowered_name, header, preview_lines):
        result.junk_score = _add_score(result.junk_score, 0.35, result.warnings, "looks like differential-result table")
        result.expression_score = max(0.0, result.expression_score - 0.3)
        _trace_file(result, "excluded from expression preference because diff-result hints were found")
    if looks_like_diff_result_columns([str(item) for item in header]):
        result.junk_score = _add_score(result.junk_score, 0.3, result.warnings, "diff-result columns detected")
        result.expression_score = max(0.0, result.expression_score - 0.25)
        _trace_file(result, "column pattern indicates differential-result table")
    if not preview_rows and extension not in RAW_EXTENSIONS and extension not in ARCHIVE_EXTENSIONS:
        result.junk_score = _add_score(result.junk_score, 0.3, result.warnings, "tabular preview could not be parsed")
    if len(header) <= 2 and extension not in RAW_EXTENSIONS and not section_has_matrix:
        result.expression_score = max(0.0, result.expression_score - 0.15)
        result.warnings.append("table has too few columns for gene-by-sample payload")
    if len(sample_columns) < 2 and extension not in RAW_EXTENSIONS and not section_has_matrix:
        result.expression_score = max(0.0, result.expression_score - 0.18)
        result.warnings.append("sample-like columns are insufficient for expression payload")
    if numeric["numeric_ratio"] < 0.35 and extension not in RAW_EXTENSIONS and not section_has_matrix:
        result.expression_score = max(0.0, result.expression_score - 0.12)
        result.warnings.append("numeric density is too low for expression payload")
    if (
        _looks_binary(result.path)
        and extension not in RAW_EXTENSIONS
        and extension not in ARCHIVE_EXTENSIONS
        and extension not in STRUCTURED_BINARY_TEXT_EXTENSIONS
        and not extension.endswith(".gz")
    ):
        result.junk_score = _add_score(result.junk_score, 0.35, result.warnings, "binary-like file is not a known raw-data format")
    if result.size_bytes < 64 and extension not in RAW_EXTENSIONS and extension not in ARCHIVE_EXTENSIONS:
        result.junk_score = _add_score(result.junk_score, 0.25, result.warnings, "file is tiny and unlikely to contain useful payload")

    for field_name in (
        "expression_score",
        "sample_annotation_score",
        "clinical_score",
        "raw_data_score",
        "platform_annotation_score",
        "junk_score",
    ):
        setattr(result, field_name, round(max(0.0, min(1.0, getattr(result, field_name))), 3))
    if not result.decision_trace:
        _trace_file(result, "file entered local validation without decisive signals")
    return result


def score_file_candidate(file_info: dict) -> FileScoreResult:
    """Backward-compatible alias for local candidate scoring."""
    return score_local_file_candidate(file_info)


def inspect_file_content(file_info: dict) -> FileScoreResult:
    """Step 2: inspect content without deciding the final semantic role."""
    return score_local_file_candidate(file_info)


def rows_look_tabular(rows: list[list[str]]) -> bool:
    return bool(rows and max((len(row) for row in rows), default=0) >= 3)


def path_looks_like_archive(relative_path: str) -> bool:
    lowered = relative_path.lower()
    return lowered.endswith(".tar") or lowered.endswith(".tar.gz") or lowered.endswith(".tgz") or lowered.endswith(".zip")


def accept_as_expression_payload(score_result: FileScoreResult) -> bool:
    diff_like = any("diff-result" in warning or "differential-result" in warning for warning in score_result.warnings)
    return (
        not score_result.excluded
        and score_result.expression_score >= EXPRESSION_THRESHOLD
        and not diff_like
    )


def classify_file_by_scores(score_result: FileScoreResult) -> FileScoreResult:
    if score_result.excluded:
        score_result.primary_label = "ignored"
        score_result.confidence = 1.0
        _trace_file(score_result, f"excluded because {score_result.excluded_reason}")
        score_result.accepted_as_candidate_matrix = False
        score_result.accepted_as_payload = False
        return score_result

    score_map = {
        "expression_payload": score_result.expression_score,
        "sample_annotation": score_result.sample_annotation_score,
        "clinical_annotation": score_result.clinical_score,
        "raw_data": score_result.raw_data_score,
        "platform_annotation": score_result.platform_annotation_score,
        "ignored": score_result.junk_score,
    }

    diff_like = any("diff-result" in warning or "differential-result" in warning for warning in score_result.warnings)
    matrix_ok = accept_as_expression_payload(score_result)
    is_archive = path_looks_like_archive(score_result.relative_path)
    if score_result.junk_score >= JUNK_THRESHOLD and score_result.junk_score > max(v for k, v in score_map.items() if k != "ignored"):
        score_result.primary_label = "ignored"
        _trace_file(score_result, "excluded because junk score dominated other roles")
    elif is_archive:
        score_result.primary_label = "archive"
        _trace_file(score_result, "accepted as archive candidate")
    elif score_result.raw_data_score >= RAW_THRESHOLD:
        score_result.primary_label = "raw_data"
        _trace_file(score_result, "accepted as raw-data candidate")
    elif matrix_ok:
        score_result.primary_label = "expression_payload"
        _trace_file(score_result, "accepted as expression candidate")
    elif score_result.sample_annotation_score >= SAMPLE_ANNOTATION_THRESHOLD and score_result.sample_annotation_score >= score_result.clinical_score:
        score_result.primary_label = "sample_annotation"
        _trace_file(score_result, "accepted as sample-annotation candidate")
    elif score_result.clinical_score >= CLINICAL_THRESHOLD:
        score_result.primary_label = "clinical_annotation"
        _trace_file(score_result, "accepted as clinical-annotation candidate")
    elif score_result.platform_annotation_score >= PLATFORM_THRESHOLD:
        score_result.primary_label = "platform_annotation"
        _trace_file(score_result, "accepted as platform-annotation candidate")
    elif max(score_map.values()) >= 0.35:
        score_result.primary_label = "supporting_file"
        _trace_file(score_result, "retained as supporting file because some evidence exists")
    else:
        score_result.primary_label = "ignored"
        _trace_file(score_result, "excluded because no score passed retention threshold")

    score_pairs = sorted(score_map.items(), key=lambda item: item[1], reverse=True)
    top = score_pairs[0][1]
    second = score_pairs[1][1] if len(score_pairs) > 1 else 0.0
    score_result.confidence = round(max(0.0, min(1.0, top - second + 0.5 * top)), 3)
    if score_result.primary_label != "expression_payload" and score_result.expression_score >= 0.45 and not diff_like:
        score_result.secondary_labels.append("expression_candidate")
        _trace_file(score_result, "retained as secondary expression candidate")
    if score_result.primary_label != "sample_annotation" and score_result.sample_annotation_score >= 0.35:
        score_result.secondary_labels.append("sample_annotation")
    if score_result.clinical_score >= 0.35 and score_result.primary_label != "clinical_annotation":
        score_result.secondary_labels.append("clinical_annotation")
    if score_result.platform_annotation_score >= 0.3 and score_result.primary_label != "platform_annotation":
        score_result.secondary_labels.append("platform_annotation")
    score_result.accepted_as_candidate_matrix = matrix_ok or "expression_candidate" in score_result.secondary_labels
    score_result.accepted_as_payload = score_result.primary_label in {"expression_payload", "raw_data", "sample_annotation", "clinical_annotation", "platform_annotation", "archive"}
    score_result.source_scope = score_result.source_level
    return score_result


def _safe_link_or_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        return
    try:
        target.symlink_to(source)
    except OSError:
        import shutil

        shutil.copy2(source, target)


def organize_dataset_files(dataset_dir: str, score_results: list[FileScoreResult]) -> dict[str, list[str]]:
    root = Path(dataset_dir).expanduser().resolve()
    organized_root = root / "organized"
    target_dirs = {
        "expression": organized_root / "expression" / "original_candidates",
        "expression_standardized": organized_root / "expression" / "standardized",
        "sample_annotation": organized_root / "sample_annotation",
        "clinical": organized_root / "clinical",
        "raw_data": organized_root / "raw_data",
        "platform_annotation": organized_root / "platform_annotation",
        "archives": organized_root / "archives",
        "other_supporting_files": organized_root / "other_supporting_files",
        "reports": organized_root / "reports",
    }
    for path in target_dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    mapping = {key: [] for key in target_dirs}

    for score in score_results:
        if score.excluded:
            continue
        source = Path(score.path)
        targets: list[str] = []
        if score.primary_label == "expression_payload":
            targets.append("expression")
        elif score.primary_label == "sample_annotation":
            targets.append("sample_annotation")
        elif score.primary_label == "clinical_annotation":
            targets.append("clinical")
        elif score.primary_label == "raw_data":
            targets.append("raw_data")
        elif score.primary_label == "platform_annotation":
            targets.append("platform_annotation")
        elif score.primary_label == "archive":
            targets.append("archives")
        else:
            targets.append("other_supporting_files")

        for secondary in score.secondary_labels:
            if secondary == "expression_candidate":
                targets.append("expression")
            elif secondary == "sample_annotation":
                targets.append("sample_annotation")
            elif secondary == "clinical_annotation":
                targets.append("clinical")
            elif secondary == "platform_annotation":
                targets.append("platform_annotation")

        for target_name in sorted(dict.fromkeys(targets)):
            target = target_dirs[target_name] / source.name
            _safe_link_or_copy(source, target)
            mapping[target_name].append(str(target))
            score.organized_targets.append(str(target))

    return {key: sorted(dict.fromkeys(value)) for key, value in mapping.items()}


def export_data_asset_index(output_path: str, score_results: list[FileScoreResult], organized_map: dict[str, list[str]]) -> None:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    files_payload: list[dict[str, Any]] = []
    for item in score_results:
        payload = item.to_dict()
        payload["standardized_role"] = normalize_file_role(payload)
        files_payload.append(payload)
    payload = {"files": files_payload, "organized_paths": organized_map}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_dataset_core_objects(score_results: list[FileScoreResult]) -> dict[str, Any]:
    expression = [item.relative_path for item in score_results if item.primary_label == "expression_payload"]
    sample = [item.relative_path for item in score_results if item.primary_label == "sample_annotation"]
    clinical = [item.relative_path for item in score_results if item.primary_label == "clinical_annotation"]
    raw = [item.relative_path for item in score_results if item.primary_label == "raw_data"]
    platform = [item.relative_path for item in score_results if item.primary_label == "platform_annotation"]
    archives = [item.relative_path for item in score_results if item.primary_label == "archive"]
    supporting = [item.relative_path for item in score_results if item.primary_label == "supporting_file"]
    ignored = [item.relative_path for item in score_results if item.primary_label == "ignored"]
    external_sources = sorted(
        {
            match.group(0)
            for item in score_results
            for match in SRA_URL_RE.finditer("\n".join(item.preview_lines))
        }
    )

    payload_type = "none"
    if expression:
        payload_type = "expression_matrix"
    elif raw:
        payload_type = "raw_only"
    elif any("diff-result" in " ".join(item.warnings) for item in score_results):
        payload_type = "diff_result_only"
    elif sample or clinical:
        payload_type = "metadata_only"
    elif platform:
        payload_type = "annotation_only"
    elif any("gsm identifiers detected" in " ".join(item.reasons).lower() for item in score_results):
        payload_type = "sample_id_only"

    return {
        "has_expression_payload": bool(expression),
        "has_sample_annotation": bool(sample),
        "has_clinical_annotation": bool(clinical),
        "expression_sources": expression,
        "sample_annotation_sources": sample,
        "clinical_sources": clinical,
        "raw_files": raw,
        "platform_annotation_files": platform,
        "supporting_files": supporting,
        "archive_files": archives,
        "external_sources": external_sources,
        "payload_type": payload_type,
        "external_raw_source": external_sources[0] if external_sources else None,
        "ignored_files": ignored,
    }


def determine_dataset_status_from_core_objects(core_objects: dict[str, Any]) -> str:
    if core_objects["has_expression_payload"] and core_objects["has_sample_annotation"]:
        return "ANALYSIS_READY"
    if core_objects["has_expression_payload"] and (core_objects["has_clinical_annotation"] or core_objects["platform_annotation_files"]):
        return "PARTIAL_BUT_USABLE"
    if core_objects["has_expression_payload"]:
        return "EXPRESSION_ONLY"
    if core_objects["payload_type"] == "metadata_only":
        return "METADATA_ONLY"
    if core_objects["payload_type"] == "raw_only":
        return "RAW_ONLY"
    if any(
        [
            core_objects["raw_files"],
            core_objects["platform_annotation_files"],
            core_objects["supporting_files"],
            core_objects["archive_files"],
            core_objects["external_sources"],
            core_objects["payload_type"] in {"annotation_only", "diff_result_only", "sample_id_only"},
        ]
    ):
        return "NO_EXPRESSION_PAYLOAD"
    return "EMPTY_OR_BROKEN"


def inspect_download_file(file_path: str) -> dict[str, Any]:
    path = Path(file_path).expanduser().resolve()
    source_level = _guess_source_scope(str(path))
    source_path = str(path)
    extension = normalize_extension(str(path))
    preview_lines = _safe_preview(str(path))
    preview_rows = _preview_rows(str(path), preview_lines)
    section_scan = (
        inspect_large_text_like_file(str(path))
        if extension in TEXT_LIKE_EXTENSIONS
        else {
            "head_preview": preview_lines[:12],
            "middle_preview": preview_lines[:12],
            "tail_preview": preview_lines[:12],
            "head_signals": [],
            "middle_signals": [],
            "tail_signals": [],
            "marker_counts": {},
            "global_markers_found": [],
            "inferred_structure": [],
        }
    )
    size_bytes = path.stat().st_size if path.exists() else 0
    excluded_reason = None
    if not path.exists():
        excluded_reason = "file does not exist"
    elif size_bytes == 0:
        excluded_reason = "0 byte file"
    elif path.name.lower() in SYSTEM_NOISE_NAMES or path.name.startswith("._"):
        excluded_reason = "system-noise file was excluded"
    elif extension.endswith(".gz") and not can_open_gzip_preview(str(path)):
        excluded_reason = "gzip is corrupted and cannot be previewed"
    elif is_html_error_page(str(path)):
        excluded_reason = "html error/redirect page was excluded"
    elif (
        _looks_binary(str(path))
        and extension not in RAW_EXTENSIONS
        and extension not in ARCHIVE_EXTENSIONS
        and extension not in STRUCTURED_BINARY_TEXT_EXTENSIONS
        and not extension.endswith(".gz")
    ):
        excluded_reason = "binary-like file is not a known raw-data format"

    container_type = "unknown"
    lowered = path.name.lower()
    if "series_matrix" in lowered:
        container_type = "series_matrix"
    elif "family.soft" in lowered:
        container_type = "family_soft"
    elif extension in {".xml", ".xml.gz"}:
        container_type = "miniml"
    elif extension in RAW_EXTENSIONS:
        container_type = "raw_file"
    elif any(token in lowered for token in PLATFORM_HINTS):
        container_type = "platform_annotation"
    elif path_looks_like_archive(lowered):
        container_type = "archive"
    elif preview_rows or preview_lines:
        container_type = "supplementary"

    matrix_classification = classify_tabular_matrix(str(path)) if preview_rows and extension not in RAW_EXTENSIONS else {}
    if extension in {".xls", ".xlsx"} and not matrix_classification:
        matrix_classification = {
            "is_expression_matrix": False,
            "preview_rows": preview_rows[:12],
            "columns": preview_rows[0] if preview_rows else [],
        }
    soft_scan = _soft_scan(str(path)) if "family.soft" in lowered else {}
    archive_info = inspect_archive_file(str(path)) if path_looks_like_archive(lowered) and path.exists() else {}
    file_info = {
        "path": str(path),
        "relative_path": path.name,
        "size_bytes": size_bytes,
        "extension": extension,
        "preview_lines": preview_lines,
        "preview_rows": preview_rows,
        "excluded": excluded_reason is not None,
        "excluded_reason": excluded_reason,
        "container_type": container_type,
        "source_level": source_level,
        "source_scope": source_level,
        "source_path": source_path,
        "soft_scan": soft_scan,
        "matrix_classification": matrix_classification,
        "section_scan": section_scan,
        "archive_info": archive_info,
    }
    scored = classify_file_by_scores(inspect_file_content(file_info))
    payload = scored.to_dict()
    payload.update(
        {
            "container_type": container_type,
            "source_level": scored.source_level,
            "source_path": scored.source_path,
            "preview_rows": preview_rows[:10],
            "detected_gsm_count": soft_scan.get("sample_count") or len(set(GSM_RE.findall("\n".join(preview_lines)))) or None,
            "sample_column_count": len(_sample_columns(preview_rows[0] if preview_rows else [])) or None,
            "content_kind": scored.primary_label,
            "content_signature": container_type,
            "file_role": scored.primary_label,
            "accepted_as_candidate_matrix": scored.accepted_as_candidate_matrix,
            "accepted_as_payload": scored.accepted_as_payload,
            "is_html_error": excluded_reason == "html error/redirect page was excluded",
            "errors": [excluded_reason] if excluded_reason and "excluded" not in excluded_reason else [],
            "head_preview": section_scan.get("head_preview", []),
            "middle_preview": section_scan.get("middle_preview", []),
            "tail_preview": section_scan.get("tail_preview", []),
            "head_signals": section_scan.get("head_signals", []),
            "middle_signals": section_scan.get("middle_signals", []),
            "tail_signals": section_scan.get("tail_signals", []),
            "global_markers_found": section_scan.get("global_markers_found", []),
            "marker_counts": section_scan.get("marker_counts", {}),
            "archive_info": archive_info,
        }
    )
    return payload


def detect_downloaded_gsm_count(download_dir: str) -> int | None:
    counts: list[int] = []
    for file_path in scan_download_directory(download_dir):
        detail = inspect_download_file(file_path)
        if detail.get("detected_gsm_count"):
            counts.append(int(detail["detected_gsm_count"]))
        if detail.get("sample_column_count"):
            counts.append(int(detail["sample_column_count"]))
    return max(counts) if counts else None


def stage_1_source_landing(root: Path) -> dict[str, Any]:
    file_paths = scan_download_directory(str(root))
    download_context = _load_download_transaction_context(str(root))
    path_consistency = check_download_path_consistency(str(root))
    source_records = [
        {
            "path": str(Path(file_path).resolve()),
            "relative_path": str(Path(file_path).resolve().relative_to(root)),
            "source_level": _guess_source_scope(file_path),
            "source_path": str(Path(file_path).resolve()),
        }
        for file_path in file_paths
    ]
    return {
        "stage": "source_landing",
        "root": str(root),
        "file_paths": file_paths,
        "download_context": download_context,
        "path_consistency": path_consistency,
        "source_records": source_records,
    }


def stage_2_content_inspection(file_paths: list[str]) -> list[dict[str, Any]]:
    inspected_details: list[dict[str, Any]] = []
    for file_path in file_paths:
        inspected_details.append(inspect_download_file(file_path))
    return inspected_details


def stage_3_semantic_classification(root: Path, inspected_details: list[dict[str, Any]]) -> tuple[list[FileScoreResult], int]:
    score_results: list[FileScoreResult] = []
    nonempty_file_count = 0
    for detail in inspected_details:
        relative_path = str(Path(detail["path"]).resolve().relative_to(root))
        detail["relative_path"] = relative_path
        score = FileScoreResult(
            path=detail["path"],
            relative_path=relative_path,
            size_bytes=int(detail["size_bytes"]),
            excluded=bool(detail["excluded"]),
            excluded_reason=detail.get("excluded_reason"),
            expression_score=float(detail["expression_score"]),
            sample_annotation_score=float(detail["sample_annotation_score"]),
            clinical_score=float(detail["clinical_score"]),
            raw_data_score=float(detail["raw_data_score"]),
            platform_annotation_score=float(detail["platform_annotation_score"]),
            junk_score=float(detail["junk_score"]),
            primary_label=str(detail["primary_label"]),
            secondary_labels=list(detail.get("secondary_labels", [])),
            accepted_as_candidate_matrix=bool(detail.get("accepted_as_candidate_matrix")),
            accepted_as_payload=bool(detail.get("accepted_as_payload")),
            source_level=str(detail.get("source_level") or detail.get("source_scope") or _guess_source_scope(relative_path)),
            source_path=str(detail.get("source_path") or detail.get("path") or relative_path),
            source_scope=str(detail.get("source_level") or detail.get("source_scope") or _guess_source_scope(relative_path)),
            confidence=float(detail["confidence"]),
            reasons=list(detail.get("reasons", [])),
            decision_trace=list(detail.get("decision_trace", [])),
            warnings=list(detail.get("warnings", [])),
            preview_lines=list(detail.get("preview_lines", [])),
            extra=dict(detail.get("extra", {})),
        )
        score.source_scope = score.source_level
        score.extra.setdefault("source_level", score.source_level)
        score.extra.setdefault("source_path", score.source_path)
        score.extra.setdefault("source_scope", score.source_scope)
        score_results.append(score)
        if score.size_bytes > 0:
            nonempty_file_count += 1
    return score_results, nonempty_file_count


def _set_status_fields(result: DownloadValidationResult, status: str, next_action: str, failure_reason: str | None) -> DownloadValidationResult:
    result.status = status
    result.failure_reason = failure_reason
    result.next_action = next_action
    result.download_success = status != "EMPTY_OR_BROKEN"
    if status in {"EMPTY_OR_BROKEN", "RAW_ONLY"} and result.failure_stage is None:
        result.failure_stage = "source_landing"
    elif status in {"NO_EXPRESSION_PAYLOAD", "METADATA_ONLY", "EXPRESSION_ONLY"} and result.failure_stage is None:
        result.failure_stage = "semantic_classification"
    elif result.failure_stage is None:
        result.failure_stage = "dataset_aggregation"

    if failure_reason == "NO_REAL_DOWNLOADED_FILES":
        result.top_problem_summary = "下载阶段没有留下可验证的 GEO 文件。"
        result.suggested_next_fix = "优先检查 source_landing 阶段的远端发现、下载计划、目标路径和非空文件保存。"
    elif failure_reason == "MISSING_SAMPLE_ANNOTATION":
        result.top_problem_summary = "表达矩阵已找到，但样本注释不足。"
        result.suggested_next_fix = "优先检查 semantic_classification 对 family.soft、sample sheet、phenotype 表的接受规则。"
    elif failure_reason == "NO_EXPRESSION_PAYLOAD":
        result.top_problem_summary = "目录中有 GEO 资产，但当前规则没有接受任何可分析表达矩阵。"
        result.suggested_next_fix = "先看 semantic_classification 的 decision_trace 与 data_asset_index，判断是表达放行没通过，还是确实只有 metadata / annotation / diff result。"
    elif failure_reason == "RAW_ONLY_DATASET":
        result.top_problem_summary = "仅发现原始数据，当前流程不会直接进入表达矩阵分析。"
        result.suggested_next_fix = "这通常不是 source_landing 错误，应改 dataset_aggregation 的路由或 downstream preprocessing strategy。"
    else:
        result.top_problem_summary = result.top_problem_summary or ("当前验收未发现阻断问题。" if not failure_reason else None)
        result.suggested_next_fix = result.suggested_next_fix or next_action
    return _ensure_validation_defaults(result)


def stage_4_dataset_aggregation(
    root: Path,
    result: DownloadValidationResult,
    score_results: list[FileScoreResult],
    stage_1_payload: dict[str, Any],
) -> DownloadValidationResult:
    download_context = stage_1_payload["download_context"]
    path_consistency = stage_1_payload["path_consistency"]

    for score in score_results:
        relative_path = score.relative_path
        if score.excluded:
            result.broken_files.append(relative_path)
            if score.excluded_reason and "excluded" not in score.excluded_reason:
                result.errors.append(f"{relative_path}: {score.excluded_reason}")
            continue
        if "series_matrix" in relative_path.lower():
            result.has_series_matrix = True
        if "family.soft" in relative_path.lower():
            result.has_family_soft = True
        if normalize_extension(relative_path) in {".xml", ".xml.gz"}:
            result.has_miniml = True
        if normalize_extension(relative_path) in RAW_EXTENSIONS:
            result.has_raw_files = True
        if any(token in relative_path.lower() for token in PLATFORM_HINTS):
            result.has_platform_hint = True
        if score.extra.get("container_type") in {"supplementary", "archive"}:
            result.has_supplementary = True

        if score.primary_label == "expression_payload":
            result.candidate_matrix_files.append(relative_path)
        elif score.primary_label == "sample_annotation":
            result.candidate_metadata_files.append(relative_path)
        elif score.primary_label == "clinical_annotation":
            result.candidate_clinical_files.append(relative_path)
        elif score.primary_label == "raw_data":
            result.raw_files.append(relative_path)
        elif score.primary_label == "platform_annotation":
            result.platform_annotation_files.append(relative_path)
        elif score.primary_label == "archive":
            result.archive_files.append(relative_path)
        elif score.primary_label == "supporting_file":
            result.supporting_files.append(relative_path)
        else:
            result.ignored_files.append(relative_path)
        result.warnings.extend(f"{relative_path}: {warning}" for warning in score.warnings)

    core_objects = build_dataset_core_objects(score_results)
    result.has_expression_payload = core_objects["has_expression_payload"]
    result.has_sample_annotation = core_objects["has_sample_annotation"]
    result.has_clinical_annotation = core_objects["has_clinical_annotation"]
    result.expression_sources = sorted(dict.fromkeys(core_objects["expression_sources"]))
    result.sample_annotation_sources = sorted(dict.fromkeys(core_objects["sample_annotation_sources"]))
    result.clinical_sources = sorted(dict.fromkeys(core_objects["clinical_sources"]))
    result.raw_files = sorted(dict.fromkeys(core_objects["raw_files"]))
    result.platform_annotation_files = sorted(dict.fromkeys(core_objects["platform_annotation_files"]))
    result.supporting_files = sorted(dict.fromkeys(core_objects["supporting_files"]))
    result.archive_files = sorted(dict.fromkeys(core_objects["archive_files"]))
    result.external_sources = sorted(dict.fromkeys(core_objects["external_sources"]))
    result.external_raw_source = core_objects["external_raw_source"]
    result.payload_type = core_objects["payload_type"]
    result.detected_gsm_count = detect_downloaded_gsm_count(str(root))
    result.candidate_matrix_files = list(result.expression_sources)
    result.candidate_metadata_files = list(result.sample_annotation_sources)
    result.candidate_clinical_files = list(result.clinical_sources)
    result.candidate_matrix_count = len(result.candidate_matrix_files)
    result.candidate_metadata_count = len(result.candidate_metadata_files)
    result.candidate_clinical_count = len(result.candidate_clinical_files)
    result.broken_files = sorted(dict.fromkeys(result.broken_files))
    result.ignored_files = sorted(dict.fromkeys(result.ignored_files))
    result.warnings = sorted(dict.fromkeys(result.warnings))
    result.errors = sorted(dict.fromkeys([*result.errors, *download_context["errors"]]))

    result.organized_paths = {"reports": []}
    has_raw_scan_files = any(Path(file_path).exists() for file_path in stage_1_payload["file_paths"])
    if result.file_count > 0 and has_raw_scan_files:
        try:
            organized_paths = organize_dataset_files(str(root), score_results)
            asset_index_path = root / "organized" / "reports" / "data_asset_index.json"
            export_data_asset_index(str(asset_index_path), score_results, organized_paths)
            organized_paths["reports"] = sorted(dict.fromkeys([*organized_paths.get("reports", []), str(asset_index_path)]))
            result.organized_paths = organized_paths
            result.extra["data_asset_index_path"] = str(asset_index_path)
        except Exception as exc:
            result.failure_stage = "dataset_aggregation"
            result.extra["sub_failure_stage"] = "organization"
            result.errors.append(f"organization failed: {exc}")

    result.extra["file_scores"] = [item.to_dict() for item in score_results]
    result.extra["core_objects"] = core_objects
    result.extra["download_transaction_log"] = download_context["transaction_log"]
    result.extra["download_summary"] = download_context["summary"]
    result.extra["path_consistency"] = path_consistency
    result.extra["decision_traces"] = {item.relative_path: item.decision_trace for item in score_results}

    has_any_geo_file = any(
        [
            result.has_series_matrix,
            result.has_family_soft,
            result.has_miniml,
            result.has_supplementary,
            bool(result.raw_files),
            bool(result.archive_files),
            bool(result.platform_annotation_files),
            bool(result.supporting_files),
        ]
    )
    raw_download_success = bool(
        download_context["summary"].get("download_success")
        if isinstance(download_context.get("summary"), dict)
        else False
    )
    if path_consistency.get("outside_raw_download_root"):
        result.errors.append("destination path mismatch")
        result.failure_stage = "source_landing"
        result.extra["sub_failure_stage"] = "download_execution"
    if not path_consistency.get("paths_consistent", True):
        result.errors.append("validation scan path and downloader write path are inconsistent")
        result.failure_stage = "source_landing"
        result.extra["sub_failure_stage"] = "download_execution"
    if result.file_count == 0 and not result.errors:
        result.errors.append("download finished with no saved files")
        result.failure_stage = "source_landing"
        result.extra["sub_failure_stage"] = "download_execution"
    if result.file_count == 0 or result.nonempty_file_count == 0 or not has_any_geo_file or not has_raw_scan_files or (download_context["transaction_log"] and not raw_download_success):
        reason = "NO_REAL_DOWNLOADED_FILES"
        if not result.errors:
            result.errors.append("download finished with no saved GEO files")
        result.failure_stage = "source_landing"
        result.extra["sub_failure_stage"] = "download_execution"
        result = _set_status_fields(result, "EMPTY_OR_BROKEN", "download appears broken; inspect downloader and retry", reason)
    elif result.has_expression_payload and result.has_sample_annotation:
        result.failure_stage = "dataset_aggregation"
        result = _set_status_fields(result, "ANALYSIS_READY", "organized assets are ready for downstream analysis modules", None)
    elif result.has_expression_payload and (result.has_clinical_annotation or result.has_platform_hint or result.has_family_soft):
        result.failure_stage = "dataset_aggregation"
        result = _set_status_fields(result, "PARTIAL_BUT_USABLE", "expression payload exists; verify annotation alignment before automated analysis", None)
    elif result.has_expression_payload:
        result.failure_stage = "dataset_aggregation"
        result.extra["sub_failure_stage"] = "missing_sample_annotation"
        result = _set_status_fields(result, "EXPRESSION_ONLY", "expression payload exists, but sample annotation is insufficient", "MISSING_SAMPLE_ANNOTATION")
    elif result.payload_type == "metadata_only":
        result.failure_stage = "semantic_classification"
        result.extra["sub_failure_stage"] = "no_expression_payload"
        result = _set_status_fields(result, "METADATA_ONLY", "metadata exists but no expression payload is available", "NO_EXPRESSION_PAYLOAD")
    elif result.payload_type == "raw_only":
        result.failure_stage = "semantic_classification"
        result.extra["sub_failure_stage"] = "raw_only_dataset"
        result = _set_status_fields(result, "RAW_ONLY", "raw data exists but current workflow requires preprocessing before analysis", "RAW_ONLY_DATASET")
    elif result.payload_type in {"annotation_only", "diff_result_only", "sample_id_only"} or any(
        [result.platform_annotation_files, result.archive_files, result.supporting_files, result.external_sources]
    ):
        result.failure_stage = "semantic_classification"
        result.extra["sub_failure_stage"] = "no_expression_payload"
        result = _set_status_fields(result, "NO_EXPRESSION_PAYLOAD", "GEO content exists, but no directly analyzable expression payload was found", "NO_EXPRESSION_PAYLOAD")
    else:
        result.failure_stage = "content_inspection"
        result.extra["sub_failure_stage"] = "empty_or_broken"
        result = _set_status_fields(result, "EMPTY_OR_BROKEN", "download appears broken; inspect downloader and retry", "EMPTY_OR_BROKEN")
    return _ensure_validation_defaults(result)


def validate_downloaded_dataset(gse_id: str, download_dir: str) -> DownloadValidationResult:
    root = Path(download_dir).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        missing = DownloadValidationResult(
            gse_id=normalize_gse_id(gse_id, str(root)),
            download_dir=str(root),
            status="EMPTY_OR_BROKEN",
            download_success=False,
            file_count=0,
            nonempty_file_count=0,
            failure_stage="source_landing",
            failure_reason="DOWNLOAD_DIR_MISSING",
            next_action="download directory does not exist; rerun downloader",
            top_problem_summary="下载目录不存在，流程在本地校验前就已中断。",
            suggested_next_fix="先修复 source_landing：确认 dataset root、raw_downloads 写入路径和目录创建逻辑。",
            errors=["download directory does not exist or is not a directory"],
            organized_paths={"reports": []},
        )
        missing.extra["sub_failure_stage"] = "download_execution"
        return _ensure_validation_defaults(missing)

    stage_1_payload = stage_1_source_landing(root)
    result = DownloadValidationResult(
        gse_id=normalize_gse_id(gse_id, str(root)),
        download_dir=str(root),
        status="EMPTY_OR_BROKEN",
        download_success=False,
        file_count=len(stage_1_payload["file_paths"]),
        nonempty_file_count=0,
        failure_stage="content_inspection",
    )
    inspected_details = stage_2_content_inspection(stage_1_payload["file_paths"])
    score_results, result.nonempty_file_count = stage_3_semantic_classification(root, inspected_details)
    result = stage_4_dataset_aggregation(root, result, score_results, stage_1_payload)
    expected_vs_actual = _build_expected_vs_actual_payload(root, result.to_dict())
    result.extra["expected_vs_actual_diff"] = expected_vs_actual
    if expected_vs_actual.get("enabled") and expected_vs_actual.get("mismatched_fields"):
        result.failure_stage = expected_vs_actual.get("likely_failure_stage") or result.failure_stage
    result.extra["expected_vs_actual_paths"] = _write_expected_vs_actual_outputs(root, expected_vs_actual)
    result.extra.setdefault("debug_snapshot_paths", {})
    result.extra["debug_snapshot_paths"]["expected_vs_actual_diff"] = result.extra["expected_vs_actual_paths"]["debug_snapshot"]
    result.extra["test_chain_status"] = {
        "accepted_candidate_matrix_count": sum(1 for item in score_results if item.accepted_as_candidate_matrix),
        "accepted_payload_count": sum(1 for item in score_results if item.accepted_as_payload),
        "expected_diff_enabled": bool(expected_vs_actual.get("enabled")),
    }
    reports_dir = root / "organized" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    file_inventory_payload = build_file_inventory_payload(
        result.gse_id,
        str(root),
        result.extra.get("file_scores", []),
        legacy_status=result.status,
    )
    parser_hints_payload = build_parser_hints_payload(result.to_dict())
    dataset_manifest_draft_payload = build_dataset_manifest_draft_payload(result.to_dict())
    handoff_package_payload = build_handoff_package_payload(result.to_dict())
    file_inventory_path = reports_dir / "file_inventory.json"
    parser_hints_path = reports_dir / "parser_hints.json"
    dataset_manifest_draft_path = reports_dir / "dataset_manifest_draft.json"
    handoff_package_path = reports_dir / "module1_handoff.json"
    file_inventory_path.write_text(json.dumps(file_inventory_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    parser_hints_path.write_text(json.dumps(parser_hints_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    dataset_manifest_draft_path.write_text(json.dumps(dataset_manifest_draft_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    handoff_package_path.write_text(json.dumps(handoff_package_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    result.extra["module1_contract_paths"] = {
        "file_inventory": str(file_inventory_path),
        "parser_hints": str(parser_hints_path),
        "dataset_manifest_draft": str(dataset_manifest_draft_path),
        "module1_handoff": str(handoff_package_path),
    }
    if _should_export_debug_snapshots(root):
        debug_snapshot_paths = result.extra.setdefault("debug_snapshot_paths", {})
        debug_snapshot_paths["source_landing"] = _write_debug_snapshot(
            root,
            "source_landing",
            attach_sub_failure_stage(
                {
                    "stage": "source_landing",
                    "source_records": stage_1_payload["source_records"],
                    "download_context": stage_1_payload["download_context"],
                    "path_consistency": stage_1_payload["path_consistency"],
                },
                "source_landing",
            ),
        )
        debug_snapshot_paths["content_inspection"] = _write_debug_snapshot(
            root,
            "content_inspection",
            {
                "stage": "content_inspection",
                "files": [
                    {
                        "path": item.get("path"),
                        "relative_path": item.get("relative_path"),
                        "source_level": item.get("source_level"),
                        "source_path": item.get("source_path"),
                        "container_type": item.get("container_type"),
                        "excluded": item.get("excluded"),
                        "excluded_reason": item.get("excluded_reason"),
                        "expression_score": item.get("expression_score"),
                        "sample_annotation_score": item.get("sample_annotation_score"),
                        "clinical_score": item.get("clinical_score"),
                        "raw_data_score": item.get("raw_data_score"),
                        "platform_annotation_score": item.get("platform_annotation_score"),
                        "junk_score": item.get("junk_score"),
                        "head_signals": item.get("head_signals"),
                        "middle_signals": item.get("middle_signals"),
                        "tail_signals": item.get("tail_signals"),
                        "marker_counts": item.get("marker_counts"),
                    }
                    for item in inspected_details
                ],
            },
        )
        debug_snapshot_paths["semantic_classification"] = _write_debug_snapshot(
            root,
            "semantic_classification",
            {
                "stage": "semantic_classification",
                "files": [item.to_dict() for item in score_results],
            },
        )
        dataset_aggregation_payload = attach_sub_failure_stage(
            {
                "stage": "dataset_aggregation",
                **result.to_dict(),
            },
            result.extra.get("sub_failure_stage") or result.failure_stage,
        )
        debug_snapshot_paths["dataset_aggregation"] = _write_debug_snapshot(
            root,
            "dataset_aggregation",
            dataset_aggregation_payload,
        )
        stage_payloads = _collect_existing_stage_payloads(root)
        for stage_name, payload in stage_payloads.items():
            debug_snapshot_paths[stage_name] = _write_debug_snapshot(root, stage_name, payload)
        debug_snapshot_paths["download_validation"] = _write_debug_snapshot(root, "download_validation", result.to_dict())
        if result.extra.get("data_asset_index_path") and Path(result.extra["data_asset_index_path"]).exists():
            asset_payload = json.loads(Path(result.extra["data_asset_index_path"]).read_text(encoding="utf-8"))
            debug_snapshot_paths["data_asset_index"] = _write_debug_snapshot(root, "data_asset_index", asset_payload)
    return _ensure_validation_defaults(result)


def export_download_validation_report(result: DownloadValidationResult, output_path: str) -> None:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
