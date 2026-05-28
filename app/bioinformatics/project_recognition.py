from __future__ import annotations

import csv
import hashlib
import json
import gzip
import re
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

from app.bioinformatics.geo_family_soft_parser import parse_geo_family_soft
from app.bioinformatics.geo_series_matrix_parser import parse_geo_series_matrix
from app.bioinformatics.group_preview import GROUP_PREVIEW_REPORT, build_group_preview_report
from app.bioinformatics.tcga.barcode import validate_tcga_sample_barcodes

RECOGNITION_REPORT = Path("logs") / "recognition" / "recognition_report.json"
RECOGNIZED_FILES = Path("logs") / "recognition" / "recognized_files.json"
CURRENT_RECOGNITION_RUN = Path("logs") / "recognition" / "current_recognition_run.json"
RECOGNITION_RUNS_DIR = Path("logs") / "recognition" / "runs"
RECOGNITION_REPORT_SCHEMA_VERSION = "biomedpilot.recognition_report.v2"
RECOGNIZED_FILES_SCHEMA_VERSION = "biomedpilot.recognized_files.v2"
RECOGNITION_ENGINE_VERSION = "bioinformatics-recognition-engine.v2"

TYPE_LABELS = {
    "expression_matrix": "表达矩阵",
    "normalized_expression_matrix": "标准化表达矩阵",
    "raw_count_matrix": "原始计数矩阵",
    "sample_metadata": "样本注释",
    "phenotype_metadata": "表型信息",
    "clinical_metadata": "临床信息",
    "survival_metadata": "生存信息",
    "gene_annotation": "基因注释",
    "platform_annotation": "平台注释",
    "platform_reference_hint": "平台参考提示",
    "comparison_config": "分组比较配置",
    "differential_result_table": "差异结果表",
    "gmt_gene_set": "GMT 基因集",
    "geo_soft_container": "GEO SOFT 容器",
    "geo_series_matrix_container": "GEO Series Matrix 容器",
    "tcga_expression_matrix": "TCGA 表达矩阵",
    "tcga_clinical_metadata": "TCGA 临床信息",
    "tcga_sample_metadata": "TCGA 样本信息",
    "gtex_expression_matrix": "GTEx 表达矩阵",
    "gtex_sample_metadata": "GTEx 样本信息",
    "gdc_manifest": "GDC manifest / sample sheet",
    "raw_heavy_file": "RAW/heavy 文件",
    "tabular_text_file": "表格文本文件",
    "unknown": "未知文件",
}

INPUT_ELIGIBLE_ROLES = {
    "expression_matrix",
    "normalized_expression_matrix",
    "raw_count_matrix",
    "sample_metadata",
    "phenotype_metadata",
    "clinical_metadata",
    "survival_metadata",
    "platform_annotation",
    "gene_annotation",
    "comparison_config",
    "gmt_gene_set",
    "tcga_expression_matrix",
    "tcga_clinical_metadata",
    "tcga_sample_metadata",
    "gtex_expression_matrix",
    "gtex_sample_metadata",
}

TEXT_TABLE_SUFFIXES = {".csv", ".tsv", ".txt", ".matrix"}
EXPRESSION_ROLE_TYPES = {
    "expression_matrix",
    "normalized_expression_matrix",
    "raw_count_matrix",
    "tcga_expression_matrix",
    "gtex_expression_matrix",
}
REFERENCE_ONLY_TYPES = {"platform_annotation", "gene_annotation", "platform_reference_hint", "gdc_manifest", "gmt_gene_set"}
BLOCKED_TYPES = {"raw_heavy_file", "unknown"}
RAW_HEAVY_SUFFIXES = {
    ".bam",
    ".cram",
    ".sra",
    ".cel",
    ".idat",
    ".tar",
    ".tgz",
    ".zip",
    ".rar",
    ".7z",
}
RAW_HEAVY_COMPOUND_SUFFIXES = {
    ".fastq.gz",
    ".fq.gz",
    ".tar.gz",
    ".tar.bz2",
    ".tar.xz",
}
DEG_STAT_COLUMNS = {
    "logfc",
    "log2fc",
    "log2_fold_change",
    "log_fold_change",
    "fold_change",
    "avg_log2fc",
    "p",
    "pvalue",
    "p_value",
    "p_val",
    "p_val_adj",
    "p_value_adj",
    "adj_p_val",
    "adj_p_value",
    "padj",
    "fdr",
    "qvalue",
    "q_value",
    "false_discovery_rate",
    "stat",
    "statistic",
    "t",
    "b",
    "wald_stat",
}
CLINICAL_HINT_TOKENS = (
    "tumor",
    "normal",
    "cancer",
    "disease",
    "tissue",
    "stage",
    "grade",
    "sex",
    "gender",
    "age",
    "survival",
    "status",
    "treatment",
    "group",
    "condition",
)


@dataclass(frozen=True)
class RecognitionClassification:
    primary_type: str
    reason: str
    confidence: float
    roles: tuple[str, ...]
    detected_assets: tuple[dict[str, object], ...] = ()
    container_format: str = ""
    content_profile: dict[str, object] | None = None
    file_level_details: dict[str, object] | None = None


def run_project_recognition(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    files = _candidate_files(root)
    return _run_project_recognition_for_files(root, files)


def run_project_recognition_for_paths(
    project_root: str | Path,
    selected_paths: list[str | Path] | tuple[str | Path, ...],
    *,
    skipped_unselected_count: int = 0,
) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    files = _expand_selected_candidate_paths(root, selected_paths)
    report = _run_project_recognition_for_files(root, files)
    report["selected_input_count"] = len(files)
    report["skipped_unselected_count"] = max(0, int(skipped_unselected_count))
    report["selected_inputs"] = [str(path) for path in files]
    _write_json(root / RECOGNITION_REPORT, report)
    return report


def list_recognition_runs(project_root: str | Path, *, include_legacy: bool = True) -> list[dict[str, object]]:
    root = Path(project_root).expanduser().resolve()
    runs: list[dict[str, object]] = []
    report = load_recognition_report(root)
    if isinstance(report, dict):
        run_id = str(report.get("recognition_run_id") or "current_recognition_report")
        files = report.get("files") if isinstance(report.get("files"), list) else []
        warnings = report.get("warnings") if isinstance(report.get("warnings"), list) else []
        runs.append(
            {
                "run_id": run_id,
                "batch_label": "当前识别记录",
                "recognition_report_path": str(root / RECOGNITION_REPORT),
                "recognized_file_count": len(files),
                "warning_count": len(warnings),
                "status": str(report.get("report_status") or "current"),
                "is_current": True,
            }
        )
    runs_dir = root / RECOGNITION_RUNS_DIR
    if runs_dir.exists():
        for report_path in sorted(runs_dir.glob("*/recognition_report.json"), reverse=True):
            report = _read_json_if_exists(report_path) or {}
            if not isinstance(report, dict):
                continue
            run_id = str(report.get("recognition_run_id") or report_path.parent.name)
            if any(str(item.get("run_id")) == run_id for item in runs):
                continue
            files = report.get("files") if isinstance(report.get("files"), list) else []
            warnings = report.get("warnings") if isinstance(report.get("warnings"), list) else []
            runs.append(
                {
                    "run_id": run_id,
                    "batch_label": "历史识别记录",
                    "recognition_report_path": str(report_path),
                    "recognized_file_count": len(files),
                    "warning_count": len(warnings),
                    "status": str(report.get("report_status") or "completed"),
                    "is_current": False,
                }
            )
    return runs


def set_current_recognition_run(project_root: str | Path, run_id: str) -> bool:
    root = Path(project_root).expanduser().resolve()
    for run in list_recognition_runs(root):
        if str(run.get("run_id") or "") == run_id:
            _write_json(
                root / CURRENT_RECOGNITION_RUN,
                {
                    "schema_version": "biomedpilot.current_recognition_run.v2",
                    "run_id": run_id,
                    "recognition_report_path": str(run.get("recognition_report_path") or ""),
                    "set_at": _now(),
                },
            )
            return True
    return False


def delete_recognition_run(project_root: str | Path, run_id: str) -> bool:
    root = Path(project_root).expanduser().resolve()
    current = _read_json_if_exists(root / CURRENT_RECOGNITION_RUN) or {}
    if isinstance(current, dict) and str(current.get("run_id") or "") == run_id:
        try:
            (root / CURRENT_RECOGNITION_RUN).unlink(missing_ok=True)
        except OSError:
            pass
    report = load_recognition_report(root)
    if isinstance(report, dict) and str(report.get("recognition_run_id") or "") == run_id:
        try:
            (root / RECOGNITION_REPORT).unlink(missing_ok=True)
            (root / RECOGNIZED_FILES).unlink(missing_ok=True)
        except OSError:
            pass
        return True
    run_dir = root / RECOGNITION_RUNS_DIR / run_id
    if run_dir.exists() and run_dir.is_dir():
        import shutil

        shutil.rmtree(run_dir)
        return True
    return False


def _run_project_recognition_for_files(root: Path, files: list[Path]) -> dict[str, object]:
    warnings: list[str] = []
    records: list[dict[str, object]] = []
    generated_at = _now()
    recognition_run_id = f"rec-{uuid.uuid4().hex[:12]}"
    input_fingerprint = _build_input_fingerprint(files)
    if not files:
        warnings.append("未找到可识别的数据文件，请返回数据来源页补充数据。")
    for path in files:
        classification = classify_file_details(path)
        kind = classification.primary_type
        reason = classification.reason
        confidence = classification.confidence
        content_profile = classification.content_profile or {}
        file_size = path.stat().st_size if path.exists() else 0
        record = {
            "recognition_run_id": recognition_run_id,
            "recognition_engine_version": RECOGNITION_ENGINE_VERSION,
            "file_name": path.name,
            "original_path": str(path),
            "recognized_type": kind,
            "recognized_type_zh": TYPE_LABELS.get(kind, "未知文件"),
            "primary_type": kind,
            "primary_type_zh": TYPE_LABELS.get(kind, "未知文件"),
            "recognized_roles": list(classification.roles),
            "roles": list(classification.roles),
            "recognized_roles_zh": [TYPE_LABELS.get(role, role) for role in classification.roles],
            "secondary_roles": [role for role in classification.roles if role != kind],
            "detected_assets": list(classification.detected_assets),
            "container_format": classification.container_format,
            "content_profile": content_profile,
            "confidence": confidence,
            "file_size": file_size,
            "reason": reason,
            "warning": "低置信度，需要人工确认。" if confidence < 0.5 else "",
            "route_path": str(root / "recognized_data" / kind / path.name),
        }
        if classification.file_level_details:
            record.update(classification.file_level_details)
        record.update(_v2_record_profiles(record, path))
        record.update(_semantic_record_fields(kind, content_profile))
        records.append(record)
    warnings.extend(_recognition_warnings(records))
    group_preview = build_group_preview_report(root, records)
    report = {
        "schema_version": RECOGNITION_REPORT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "recognition_run_id": recognition_run_id,
        "recognition_engine_version": RECOGNITION_ENGINE_VERSION,
        "project_root": str(root),
        "input_fingerprint": input_fingerprint,
        "report_status": "current",
        "files": records,
        "type_counts": _type_counts(records),
        "group_preview": group_preview,
        "warnings": warnings,
    }
    _write_json(root / RECOGNITION_REPORT, report)
    _write_json(
        root / RECOGNIZED_FILES,
        {
            "schema_version": RECOGNIZED_FILES_SCHEMA_VERSION,
            "generated_at": generated_at,
            "recognition_run_id": recognition_run_id,
            "recognition_engine_version": RECOGNITION_ENGINE_VERSION,
            "project_root": str(root),
            "input_fingerprint": input_fingerprint,
            "report_status": "current",
            "files": records,
        },
    )
    _write_json(
        root / CURRENT_RECOGNITION_RUN,
        {
            "schema_version": "biomedpilot.current_recognition_run.v1",
            "generated_at": generated_at,
            "run_id": recognition_run_id,
            "run_dir": str(root / "logs" / "recognition"),
            "recognition_report_path": str(root / RECOGNITION_REPORT),
            "recognition_run_id": recognition_run_id,
            "recognition_engine_version": RECOGNITION_ENGINE_VERSION,
            "input_fingerprint": input_fingerprint,
            "report_path": str(root / RECOGNITION_REPORT),
            "recognized_files_path": str(root / RECOGNIZED_FILES),
        },
    )
    _write_json(
        root / "recognized_data" / "current.json",
        {
            "schema_version": "biomedpilot.current_recognition_run.v1",
            "run_id": recognition_run_id,
            "run_dir": str(root / "logs" / "recognition"),
            "recognition_report_path": str(root / RECOGNITION_REPORT),
            "set_at": generated_at,
        },
    )
    _write_json(root / GROUP_PREVIEW_REPORT, group_preview)
    return report


def load_recognition_report(project_root: str | Path) -> dict[str, object] | None:
    path = Path(project_root).expanduser().resolve() / RECOGNITION_REPORT
    if not path.exists():
        return None
    report = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(report, dict):
        stale_status = recognition_report_stale_status(project_root, report)
        report["stale_status"] = stale_status
        if stale_status.get("is_stale"):
            warning = str(stale_status.get("message") or "识别报告可能已过期，请重新识别。")
            warnings = [str(item) for item in report.get("warnings", []) or []]
            if warning not in warnings:
                warnings.append(warning)
                report["warnings"] = warnings
            report["report_status"] = "stale"
    return report


def recognition_report_stale_status(project_root: str | Path, report: dict[str, object] | None = None) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    loaded = report
    if loaded is None:
        path = root / RECOGNITION_REPORT
        if not path.exists():
            return {"is_stale": True, "reason": "missing_report", "message": "尚未生成数据识别报告。"}
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"is_stale": True, "reason": "unreadable_report", "message": "识别报告无法读取，请重新识别。"}
    schema = str(loaded.get("schema_version") or "")
    engine = str(loaded.get("recognition_engine_version") or "")
    if schema != RECOGNITION_REPORT_SCHEMA_VERSION or engine != RECOGNITION_ENGINE_VERSION:
        return {
            "is_stale": True,
            "reason": "schema_or_engine_mismatch",
            "message": "识别报告版本已过期，请重新识别。",
            "expected_schema_version": RECOGNITION_REPORT_SCHEMA_VERSION,
            "actual_schema_version": schema,
            "expected_engine_version": RECOGNITION_ENGINE_VERSION,
            "actual_engine_version": engine,
        }
    expected = loaded.get("input_fingerprint")
    files = [Path(str(item.get("original_path") or "")) for item in loaded.get("files", []) or [] if isinstance(item, dict) and item.get("original_path")]
    current = _build_input_fingerprint(files)
    if not isinstance(expected, dict) or expected.get("fingerprint_hash") != current.get("fingerprint_hash"):
        return {
            "is_stale": True,
            "reason": "source_files_changed",
            "message": "识别输入文件已变化，请重新识别。",
            "expected_fingerprint": expected,
            "current_fingerprint": current,
        }
    return {"is_stale": False, "reason": "", "message": "", "fingerprint_hash": current.get("fingerprint_hash")}


def _build_input_fingerprint(files: list[Path]) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    for path in files:
        expanded = Path(path).expanduser()
        exists = expanded.exists()
        stat = expanded.stat() if exists else None
        entry: dict[str, object] = {
            "path": str(expanded.resolve()) if exists else str(expanded),
            "exists": exists,
            "size_bytes": stat.st_size if stat is not None else 0,
            "mtime_ns": stat.st_mtime_ns if stat is not None else 0,
        }
        if exists and stat is not None and stat.st_size <= 10 * 1024 * 1024 and not _is_raw_heavy_path(expanded):
            digest = hashlib.sha256()
            try:
                with expanded.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
                entry["sha256"] = digest.hexdigest()
            except OSError:
                entry["sha256"] = ""
        entries.append(entry)
    entries.sort(key=lambda item: str(item.get("path") or ""))
    fingerprint_hash = hashlib.sha256(json.dumps(entries, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {"algorithm": "path-size-mtime-smallfile-sha256", "fingerprint_hash": fingerprint_hash, "files": entries}


def _v2_record_profiles(record: dict[str, object], path: Path) -> dict[str, object]:
    content_profile = record.get("content_profile") if isinstance(record.get("content_profile"), dict) else {}
    roles = [str(role) for role in record.get("recognized_roles", []) or [] if str(role)]
    primary = str(record.get("recognized_type") or "unknown")
    standardization_status, status_zh, next_action = _standardization_status_for_record(primary, roles, record)
    evidence = {
        "filename": path.name,
        "headers": content_profile.get("header") or content_profile.get("headers") or [],
        "parser_result": record.get("container_format") or content_profile.get("container_type") or "",
        "source_manifest": _source_manifest_reference(path),
        "barcode_sample_id": content_profile.get("tcga_sample_barcodes") or content_profile.get("gtex_sample_ids") or [],
        "numeric_profile": {
            "numeric_ratio": content_profile.get("numeric_ratio"),
            "integer_numeric_ratio": content_profile.get("integer_numeric_ratio"),
            "numeric_column_count": content_profile.get("numeric_column_count"),
        },
    }
    dimensions = record.get("expression_matrix_dimensions") if isinstance(record.get("expression_matrix_dimensions"), dict) else {}
    matrix_profile = {
        "gene_or_probe_id_column": content_profile.get("first_column_name") or record.get("id_column") or "",
        "gene_id_type_candidate": record.get("gene_id_type_candidate") or content_profile.get("first_column_id_pattern") or "",
        "sample_columns": content_profile.get("sample_columns") or record.get("sample_columns") or [],
        "value_type_candidate": record.get("expression_value_type_candidate") or content_profile.get("expression_value_type_candidate") or "",
        "numeric_ratio": content_profile.get("numeric_ratio"),
        "row_count": content_profile.get("sampled_row_count") or dimensions.get("rows"),
        "column_count": content_profile.get("column_count") or dimensions.get("columns"),
    }
    metadata_profile = {
        "sample_id_columns": content_profile.get("sample_id_columns") or [],
        "clinical_fields": content_profile.get("clinical_fields") or record.get("clinical_candidate_fields") or [],
        "group_candidates": record.get("phenotype_candidate_fields") or content_profile.get("group_candidate_fields") or [],
        "species_evidence": record.get("species_evidence") or content_profile.get("species_evidence") or [],
        "tcga_sample_type_summary": content_profile.get("tcga_sample_type_summary") or {},
        "gtex_tissue_candidates": content_profile.get("gtex_tissue_candidates") or [],
    }
    risk_profile = {
        "raw_heavy": primary == "raw_heavy_file" or bool(content_profile.get("raw_heavy")),
        "large_file": _is_large_file_size(record.get("file_size")),
        "unsupported": primary == "unknown",
        "ambiguous": float(record.get("confidence") or 0) < 0.6,
        "risk_level": "blocked" if standardization_status == "blocked" else ("review" if standardization_status == "reference_only" else "normal"),
    }
    return {
        "standardization_status": standardization_status,
        "standardization_status_zh": status_zh,
        "next_action": next_action,
        "evidence": evidence,
        "matrix_profile": matrix_profile,
        "metadata_profile": metadata_profile,
        "risk_profile": risk_profile,
    }


def _standardization_status_for_record(primary: str, roles: list[str], record: dict[str, object]) -> tuple[str, str, str]:
    if primary in BLOCKED_TYPES or primary == "raw_heavy_file":
        return "blocked", "不能用于分析", "保留来源记录；普通流程不解析或下载 RAW/heavy 文件。"
    assets = [asset for asset in record.get("detected_assets", []) or [] if isinstance(asset, dict)]
    if any(asset.get("input_eligible") is True for asset in assets) or any(role in INPUT_ELIGIBLE_ROLES for role in roles):
        return "eligible", "可进入标准化", "进入标准化阶段，由用户确认用途、样本列、值类型和分组。"
    if primary in REFERENCE_ONLY_TYPES or any(role in REFERENCE_ONLY_TYPES for role in roles):
        return "reference_only", "仅作参考/注释", "作为注释、manifest 或参考文件保留，不作为主表达输入。"
    return "blocked", "不能用于分析", "当前识别结果不能作为标准化输入。"


def _source_manifest_reference(path: Path) -> dict[str, object]:
    for parent in path.parents:
        acquisition_root = parent / "acquisition" / "source_manifests"
        if acquisition_root.exists():
            return _find_source_manifest_for_path(acquisition_root, path)
    return {}


def _find_source_manifest_for_path(manifest_root: Path, path: Path) -> dict[str, object]:
    target = str(path.resolve()) if path.exists() else str(path)
    for manifest_path in sorted(manifest_root.glob("*.json"), reverse=True):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        records = manifest.get("files") or manifest.get("file_records") or []
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            values = {str(record.get("local_path") or ""), str(record.get("source_path") or ""), str(record.get("path") or "")}
            if target in values:
                return {
                    "manifest_path": str(manifest_path),
                    "source": manifest.get("source") or manifest.get("source_type") or "",
                    "matched_record_status": record.get("status") or "",
                    "matched_record_role": record.get("role") or "",
                    "matched_record_message": record.get("message") or "",
                }
    return {}


def _is_large_file_size(value: object) -> bool:
    try:
        return int(value) >= 500 * 1024 * 1024
    except (TypeError, ValueError):
        return False


def _recognition_warnings(records: list[dict[str, object]]) -> list[str]:
    warnings: list[str] = []
    expression_records = [
        record
        for record in records
        if any(role in set(record.get("recognized_roles", []) or []) for role in EXPRESSION_ROLE_TYPES)
    ]
    if len(expression_records) > 1:
        warnings.append("multiple expression candidates detected; manual review may be required")
    if records and not any(record.get("recognized_roles") for record in records):
        warnings.append("未检测到明确的基因表达、差异分析或样本注释结构。")
    return warnings


def _semantic_record_fields(file_kind: str, content_profile: dict[str, object]) -> dict[str, object]:
    fields: dict[str, object] = {"file_kind": file_kind}
    for key in ("semantic_type", "semantic_type_zh", "species", "species_group", "gene_id_type", "content_blocks"):
        value = content_profile.get(key)
        if value not in (None, "", []):
            fields[key] = value
    if "species" not in fields:
        evidence_text = " ".join(str(item) for item in content_profile.get("species_evidence", []) or [])
        if "Mus musculus" in evidence_text:
            fields["species"] = "Mus musculus"
            fields["species_group"] = "mouse"
        elif "Homo sapiens" in evidence_text:
            fields["species"] = "Homo sapiens"
            fields["species_group"] = "human"
    return fields


def classify_file(path: Path) -> tuple[str, str, float]:
    classification = classify_file_details(path)
    return classification.primary_type, classification.reason, classification.confidence


def classify_file_details(path: Path) -> RecognitionClassification:
    name = path.name.lower()
    if _is_raw_heavy_path(path):
        return _classification(
            "raw_heavy_file",
            "文件类型属于 RAW/heavy 数据，普通识别与标准化流程默认阻断。",
            0.92,
            roles=("raw_heavy_file",),
            detected_assets=(
                _detected_asset(
                    "raw_heavy_file",
                    confidence=0.92,
                    reason="FASTQ/SRA/BAM/CRAM/CEL/IDAT 或大型归档文件需要专门预处理，当前流程不解析。",
                    input_eligible=False,
                    evidence=(path.name,),
                    extra={"risk_level": "blocked", "blocked_reason": "raw_heavy"},
                ),
            ),
            content_profile={"raw_heavy": True, "suffixes": _suffixes_lower(path)},
        )
    if name.endswith((".gmt", ".gmx")):
        return _classification("gmt_gene_set", "文件扩展名提示为基因集。", 0.85)
    if _is_geo_soft_path(path):
        geo_soft = _classify_geo_soft(path)
        if geo_soft is not None:
            return geo_soft
    if _is_geo_series_matrix_path(path):
        geo_series = _classify_geo_series_matrix(path)
        if geo_series is not None:
            return geo_series
    if any(token in name for token in ("comparison", "contrast")):
        return _classification("comparison_config", "文件名包含分组比较配置提示。", 0.74)
    if _is_tabular_text_path(path):
        tabular = _classify_tabular_text(path)
        if tabular is not None:
            return tabular
    if path.suffix.lower() == ".xlsx":
        workbook_kind = _classify_xlsx_table(path)
        if workbook_kind is not None:
            return workbook_kind
    if _is_gdc_manifest_name(name):
        return _classification(
            "gdc_manifest",
            "文件名提示为 GDC manifest 或 sample sheet，作为下载/样本选择控制文件，不作为表达矩阵。",
            0.78,
            roles=("gdc_manifest",),
            detected_assets=(
                _detected_asset(
                    "gdc_manifest",
                    confidence=0.78,
                    reason="GDC manifest/sample sheet 属于获取控制文件，仅作参考。",
                    input_eligible=False,
                    evidence=(path.name,),
                ),
            ),
        )
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
    return _classification("unknown", "未匹配到稳定识别规则。", 0.2, roles=())


def _classification(
    primary_type: str,
    reason: str,
    confidence: float,
    *,
    roles: tuple[str, ...] | None = None,
    detected_assets: tuple[dict[str, object], ...] = (),
    container_format: str = "",
    content_profile: dict[str, object] | None = None,
    file_level_details: dict[str, object] | None = None,
) -> RecognitionClassification:
    normalized_roles = tuple(dict.fromkeys(roles if roles is not None else (() if primary_type == "unknown" else (primary_type,))))
    return RecognitionClassification(
        primary_type=primary_type,
        reason=reason,
        confidence=confidence,
        roles=normalized_roles,
        detected_assets=detected_assets or tuple(_detected_asset(role, confidence=confidence, reason=reason) for role in normalized_roles),
        container_format=container_format,
        content_profile=content_profile,
        file_level_details=file_level_details,
    )


def _classify_xlsx_table(path: Path) -> RecognitionClassification | None:
    profile = _profile_xlsx_table(path)
    if not profile:
        return None
    profile["filename"] = path.name
    profile["expression_value_type_candidate"] = _expression_value_type_candidate([path.name, *[str(item) for item in profile.get("header", []) or []]])
    classification = _classification_from_table_profile(profile, source_format="xlsx_workbook", container_format="xlsx_workbook")
    if classification is None:
        return None
    return classification


def _classify_geo_series_matrix(path: Path) -> RecognitionClassification | None:
    profile = parse_geo_series_matrix(path)
    if (
        not profile.get("series_accession")
        and not profile.get("sample_metadata_fields")
        and not profile.get("table_begin_line")
        and not profile.get("platform_accessions")
    ):
        return None
    assets: list[dict[str, object]] = []
    roles: list[str] = []
    parser_depth = str(profile.get("parser_depth") or "container_only")
    sample_count = int(profile.get("sample_count") or 0)
    sample_columns = [str(item) for item in profile.get("sample_columns", []) or []]
    if profile.get("expression_matrix_presence"):
        roles.append("expression_matrix")
        assets.append(
            _detected_asset(
                "expression_matrix",
                confidence=0.9,
                reason="已检测到 GEO Series Matrix 表达矩阵区域，可进入标准化阶段进一步确认。",
                source_section="series_matrix_table",
                source_format="geo_series_matrix",
                input_eligible=True,
                evidence=(
                    "ID_REF header" if str(profile.get("id_column") or "").upper() == "ID_REF" else f"id_column={profile.get('id_column') or ''}",
                    f"sample_columns={len(sample_columns)}",
                    f"expression_value_type_candidate={profile.get('expression_value_type_candidate') or 'unknown'}",
                    f"gene_id_type_candidate={profile.get('gene_id_type_candidate') or 'unknown'}",
                ),
                location={
                    "start_line": profile.get("table_begin_line"),
                    "end_line": profile.get("table_end_line"),
                    "header_line": profile.get("table_header_line"),
                },
                extra={
                    "sample_count": sample_count,
                    "matrix_dimensions": profile.get("expression_matrix_dimensions", {}),
                    "expression_value_type_candidate": profile.get("expression_value_type_candidate"),
                    "gene_id_type_candidate": profile.get("gene_id_type_candidate"),
                    "requires_user_confirmation": True,
                },
            )
        )
    if sample_count or profile.get("sample_metadata_fields"):
        roles.append("sample_metadata")
        assets.append(
            _detected_asset(
                "sample_metadata",
                confidence=0.86,
                reason="已解析 GEO Series Matrix 样本 accession、标题、source_name 或 characteristics metadata。",
                source_section="sample_metadata",
                source_format="geo_series_matrix",
                input_eligible=True,
                evidence=tuple(str(item) for item in profile.get("sample_metadata_fields", []) or ()),
                extra={"sample_count": sample_count, "parser_depth": parser_depth},
            )
        )
    platform_accessions = [str(item) for item in profile.get("platform_accessions", []) or []]
    if platform_accessions:
        roles.append("platform_reference_hint")
        assets.append(
            _detected_asset(
                "platform_reference_hint",
                confidence=0.82,
                reason="GEO Series Matrix 提供 GPL 平台编号；ID_REF 映射仍需在标准化阶段确认。",
                source_section="series_metadata",
                source_format="geo_series_matrix",
                input_eligible=False,
                evidence=tuple(platform_accessions),
                extra={"platform_id": platform_accessions[0], "platform_accessions": platform_accessions},
            )
        )
    phenotype_fields = [str(item) for item in profile.get("phenotype_candidate_fields", []) or []]
    if phenotype_fields:
        roles.append("phenotype_metadata")
        assets.append(
            _detected_asset(
                "phenotype_metadata",
                confidence=0.72,
                reason="样本分组为候选推断，需用户确认后才能进行 DEG 分析。",
                source_section="sample_metadata",
                source_format="geo_series_matrix",
                input_eligible=True,
                evidence=tuple(phenotype_fields),
                extra={"requires_user_confirmation": True, "phenotype_candidate_values_preview": profile.get("phenotype_candidate_values_preview", {})},
            )
        )
    clinical_fields = [str(item) for item in profile.get("clinical_candidate_fields", []) or []]
    if clinical_fields:
        roles.append("clinical_metadata")
        assets.append(
            _detected_asset(
                "clinical_metadata",
                confidence=0.7,
                reason="样本 metadata 中包含年龄、性别、分期、分级、生存或状态候选线索。",
                source_section="sample_metadata",
                source_format="geo_series_matrix",
                input_eligible=True,
                evidence=tuple(clinical_fields),
                extra={"requires_user_confirmation": True},
            )
        )
    if not roles:
        return None
    role_labels = "、".join(TYPE_LABELS.get(role, role) for role in dict.fromkeys(roles))
    depth_labels = {
        "container_only": "已识别 GEO Series Matrix 容器",
        "metadata_parsed": "已解析 Series/Sample metadata",
        "matrix_detected": "检测到表达矩阵区域",
        "matrix_previewed": "已解析表达矩阵结构预览",
    }
    if profile.get("expression_matrix_presence"):
        reason = (
            f"GEO Series Matrix 已解析，{depth_labels.get(parser_depth, parser_depth)}；检测到：{role_labels}。"
            "表达值类型、ID_REF 映射和候选分组需用户确认。"
        )
    else:
        reason = f"GEO Series Matrix 已解析，{depth_labels.get(parser_depth, parser_depth)}；尚未确认表达矩阵区域。"
    file_level_keys = {
        "file_format",
        "container_type",
        "parser_depth",
        "series_accession",
        "platform_accessions",
        "sample_count",
        "sample_accessions",
        "sample_metadata_fields",
        "phenotype_candidate_fields",
        "phenotype_candidate_values_preview",
        "expression_matrix_presence",
        "expression_matrix_dimensions",
        "id_column",
        "sample_columns",
        "expression_value_type_candidate",
        "gene_id_type_candidate",
        "species_evidence",
        "warnings",
        "requires_user_confirmation",
        "can_enter_standardization",
    }
    return _classification(
        "geo_series_matrix_container",
        reason,
        0.9,
        roles=tuple(dict.fromkeys(roles)),
        detected_assets=tuple(assets),
        container_format="geo_series_matrix",
        content_profile=profile,
        file_level_details={key: profile.get(key) for key in file_level_keys},
    )


def _classify_tabular_text(path: Path) -> RecognitionClassification | None:
    profile = _profile_tabular_text(path)
    if not profile:
        return None
    profile["filename"] = path.name
    profile["expression_value_type_candidate"] = _expression_value_type_candidate([path.name, *[str(item) for item in profile.get("header", []) or []]])
    return _classification_from_table_profile(profile, source_format="tabular_text", container_format="tabular_text")


def _classification_from_table_profile(
    profile: dict[str, object],
    *,
    source_format: str,
    container_format: str,
) -> RecognitionClassification | None:
    primary = str(profile.get("possible_table_role") or "unknown")
    if primary == "unknown":
        return None
    roles: list[str] = [primary]
    assets: list[dict[str, object]] = []
    header_line = int(profile.get("header_line") or 1)
    evidence = [str(item) for item in profile.get("evidence", []) or []]
    source_domain = str(profile.get("source_domain") or "")
    if primary in {"normalized_expression_matrix", "raw_count_matrix", "expression_matrix"} and source_domain == "tcga":
        primary = "tcga_expression_matrix"
        roles = [primary, "sample_metadata"]
        evidence.extend(["TCGA barcode sample columns", "TCGA sample type code evidence"])
    elif primary in {"normalized_expression_matrix", "raw_count_matrix", "expression_matrix"} and source_domain == "gtex":
        primary = "gtex_expression_matrix"
        roles = [primary, "sample_metadata"]
        evidence.extend(["GTEx sample id columns", "GTEx normal reference expression evidence"])
    elif primary in {"clinical_metadata", "survival_metadata", "sample_metadata"} and source_domain == "tcga":
        has_clinical_role = "clinical_metadata" in [str(role) for role in profile.get("extra_roles", []) or []]
        primary = "tcga_clinical_metadata" if primary in {"clinical_metadata", "survival_metadata"} or has_clinical_role else "tcga_sample_metadata"
        roles = [primary, "clinical_metadata" if "clinical" in primary else "sample_metadata"]
        if primary == "tcga_clinical_metadata":
            roles.append("survival_metadata")
        evidence.append("TCGA barcode or patient clinical field evidence")
    elif primary in {"clinical_metadata", "survival_metadata", "sample_metadata"} and source_domain == "gtex":
        primary = "gtex_sample_metadata"
        roles = [primary, "sample_metadata"]
        evidence.append("GTEx sample/subject phenotype field evidence")
    if primary == "gdc_manifest":
        assets.append(
            _detected_asset(
                primary,
                confidence=0.8,
                reason="表头匹配 GDC manifest 或 sample sheet，属于下载/选择控制文件。",
                source_section="tabular_header",
                source_format=source_format,
                input_eligible=False,
                evidence=tuple(evidence),
                location={"header_line": header_line},
            )
        )
    elif primary == "differential_result_table":
        assets.append(
            _detected_asset(
                primary,
                confidence=0.88,
                reason="表头包含 logFC、P 值和校正 P/FDR 字段，属于差异分析结果表。",
                source_section="tabular_header",
                source_format=source_format,
                input_eligible=False,
                evidence=tuple(evidence),
                location={"header_line": header_line},
            )
        )
    elif primary in {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}:
        confidence = 0.86 if primary == "raw_count_matrix" else 0.82
        if primary in {"tcga_expression_matrix", "gtex_expression_matrix"}:
            confidence = 0.88
        assets.append(
            _detected_asset(
                primary,
                confidence=confidence,
                reason=_expression_asset_reason(primary),
                source_section="tabular_matrix",
                source_format=source_format,
                input_eligible=True,
                evidence=tuple(evidence),
                location={"header_line": header_line},
                extra={
                    "delimiter": profile.get("delimiter"),
                    "numeric_column_count": profile.get("numeric_column_count", 0),
                    "sample_like_column_count": profile.get("sample_like_column_count", 0),
                    "expression_value_type_candidate": profile.get("expression_value_type_candidate") or _expression_value_type_from_role(primary),
                    "tcga_sample_type_summary": profile.get("tcga_sample_type_summary") or {},
                    "gtex_tissue_candidates": profile.get("gtex_tissue_candidates") or [],
                },
            )
        )
        if primary == "tcga_expression_matrix":
            assets.append(
                _detected_asset(
                    "tcga_sample_metadata",
                    confidence=0.78,
                    reason="TCGA barcode 可推断 patient barcode 与 tumor/normal sample type。",
                    source_section="tabular_header",
                    source_format=source_format,
                    input_eligible=True,
                    evidence=tuple(str(item) for item in profile.get("tcga_sample_barcodes", []) or ()),
                    location={"header_line": header_line},
                    extra={"tcga_sample_type_summary": profile.get("tcga_sample_type_summary") or {}},
                )
            )
        if primary == "gtex_expression_matrix":
            assets.append(
                _detected_asset(
                    "gtex_sample_metadata",
                    confidence=0.74,
                    reason="GTEx sample ID 或组织字段提示该文件可作为 normal reference metadata。",
                    source_section="tabular_header",
                    source_format=source_format,
                    input_eligible=True,
                    evidence=tuple(str(item) for item in profile.get("gtex_sample_ids", []) or profile.get("gtex_tissue_candidates", []) or ()),
                    location={"header_line": header_line},
                )
            )
        if profile.get("has_embedded_annotation"):
            roles.append("platform_annotation")
            assets.append(
                _detected_asset(
                    "platform_annotation",
                    confidence=0.68,
                    reason="表达矩阵中同时包含 gene symbol、ENTREZ、ENSEMBL 或 chromosome 等注释列。",
                    source_section="tabular_annotation_columns",
                    source_format=source_format,
                    input_eligible=True,
                    evidence=tuple(profile.get("annotation_evidence", []) or ()),
                    location={"header_line": header_line},
                )
            )
    elif primary in {"sample_metadata", "tcga_sample_metadata", "gtex_sample_metadata"}:
        roles.extend(str(role) for role in profile.get("extra_roles", []) or [])
        for role in dict.fromkeys(roles):
            role_reason = "表头包含 sample/group/condition/tissue/disease 等样本属性字段。"
            if role == "tcga_sample_metadata":
                role_reason = "表头包含 TCGA barcode、sample type 或 GDC sample metadata 线索。"
            elif role == "gtex_sample_metadata":
                role_reason = "表头包含 GTEx sample/subject/tissue phenotype 线索。"
            if role == "clinical_metadata":
                role_reason = "表头包含 age/sex/stage/grade/status 等临床字段。"
            elif role == "survival_metadata":
                role_reason = "表头同时包含生存时间和状态字段。"
            assets.append(
                _detected_asset(
                    role,
                    confidence=0.8 if role == "sample_metadata" else 0.76,
                    reason=role_reason,
                    source_section="tabular_metadata",
                    source_format=source_format,
                    input_eligible=True,
                    evidence=tuple(evidence),
                    location={"header_line": header_line},
                )
            )
    elif primary in {"clinical_metadata", "survival_metadata", "platform_annotation", "gene_annotation", "tcga_clinical_metadata"}:
        roles.extend(str(role) for role in profile.get("extra_roles", []) or [])
        for role in dict.fromkeys(roles):
            input_eligible = role not in {"platform_reference_hint"}
            assets.append(
                _detected_asset(
                    role,
                    confidence=0.82 if role == "tcga_clinical_metadata" else 0.78,
                    reason=_tabular_role_reason(role),
                    source_section="tabular_header",
                    source_format=source_format,
                    input_eligible=input_eligible,
                    evidence=tuple(evidence),
                    location={"header_line": header_line},
                )
            )
    else:
        return None
    normalized_roles = tuple(dict.fromkeys(roles))
    primary_type = "tabular_text_file" if len(normalized_roles) > 1 and primary in {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix"} else primary
    role_labels = "、".join(TYPE_LABELS.get(role, role) for role in normalized_roles)
    return _classification(
        primary_type,
        f"表格内容识别为：{role_labels}。",
        max(float(asset.get("confidence_score") or 0.7) for asset in assets),
        roles=normalized_roles,
        detected_assets=tuple(assets),
        container_format=container_format,
        content_profile={key: value for key, value in profile.items() if key not in {"evidence", "extra_roles", "annotation_evidence"}},
    )


def _classify_geo_soft(path: Path) -> RecognitionClassification | None:
    profile = parse_geo_family_soft(path)
    if not profile.get("series_accession") and not profile.get("sample_count") and not profile.get("platform_count"):
        return None
    roles: list[str] = []
    assets: list[dict[str, object]] = []
    sample_count = int(profile.get("sample_count") or 0)
    parser_depth = str(profile.get("parser_depth") or "container_only")
    if profile.get("expression_table_presence"):
        roles.append("expression_matrix")
        assets.append(
            _detected_asset(
                "expression_matrix",
                confidence=0.86,
                reason="SOFT sample table 包含 ID_REF / VALUE 表达候选；进入标准化前需要用户确认。",
                source_section="sample_table",
                source_format="geo_family_soft",
                input_eligible=True,
                evidence=tuple(profile.get("gene_id_evidence", []) or ("ID_REF/VALUE sample table",)),
                extra={
                    "sample_count": sample_count,
                    "parser_depth": parser_depth,
                    "requires_user_confirmation": True,
                    "expression_table_row_count": profile.get("expression_table_row_count", 0),
                },
            )
        )
    if sample_count or profile.get("sample_metadata_fields"):
        roles.append("sample_metadata")
        assets.append(
            _detected_asset(
                "sample_metadata",
                confidence=0.84,
                reason="已解析 SOFT SAMPLE 块、样本标题、source_name_ch1 或 characteristics_ch1。",
                source_section="sample_metadata",
                source_format="geo_family_soft",
                input_eligible=True,
                evidence=tuple(str(item) for item in profile.get("sample_metadata_fields", []) or ()),
                extra={"sample_count": sample_count, "parser_depth": parser_depth},
            )
        )
    if profile.get("phenotype_candidate_fields"):
        roles.append("phenotype_metadata")
        assets.append(
            _detected_asset(
                "phenotype_metadata",
                confidence=0.78,
                reason="SOFT SAMPLE metadata 中提取到 treatment、genotype、tissue、disease 或 cell line 等候选表型字段。",
                source_section="sample_metadata",
                source_format="geo_family_soft",
                input_eligible=True,
                evidence=tuple(str(item) for item in profile.get("phenotype_candidate_fields", []) or ()),
                extra={"sample_count": sample_count, "parser_depth": parser_depth, "requires_user_confirmation": True},
            )
        )
    if profile.get("platform_annotation_presence"):
        roles.append("platform_annotation")
        assets.append(
            _detected_asset(
                "platform_annotation",
                confidence=0.82,
                reason="已解析 SOFT PLATFORM 块，并检测平台注释表或平台注释字段。",
                source_section="platform_table",
                source_format="geo_family_soft",
                input_eligible=True,
                evidence=tuple(profile.get("gene_id_evidence", []) or profile.get("platform_accessions", []) or ("PLATFORM block",)),
                extra={
                    "platform_count": profile.get("platform_count", 0),
                    "platform_annotation_presence": bool(profile.get("platform_annotation_presence")),
                    "parser_depth": parser_depth,
                },
            )
        )
    if profile.get("clinical_candidate_fields"):
        roles.append("clinical_metadata")
        assets.append(
            _detected_asset(
                "clinical_metadata",
                confidence=0.68,
                reason="SOFT SAMPLE characteristics 中包含年龄、性别、分期、状态等临床候选字段。",
                source_section="sample_characteristics",
                source_format="geo_family_soft",
                input_eligible=True,
                evidence=tuple(str(item) for item in profile.get("clinical_candidate_fields", []) or ()),
                extra={"sample_count": sample_count, "parser_depth": parser_depth, "requires_user_confirmation": True},
            )
        )
    if not roles:
        return None
    role_labels = "、".join(TYPE_LABELS.get(role, role) for role in roles)
    depth_labels = {
        "container_only": "已识别 GEO SOFT 容器",
        "metadata_parsed": "已解析样本/平台元数据",
        "table_detected": "检测到平台或表达表格",
        "table_parsed": "已解析表格结构",
    }
    if profile.get("expression_table_presence"):
        reason = f"GEO family SOFT 容器，{depth_labels.get(parser_depth, parser_depth)}；检测到：{role_labels}；表达表格为候选输入，需用户确认。"
    elif profile.get("sample_count") or profile.get("platform_annotation_presence"):
        reason = f"GEO family SOFT 容器，{depth_labels.get(parser_depth, parser_depth)}；尚未确认表达矩阵。"
    else:
        reason = f"GEO family SOFT 容器，{depth_labels.get(parser_depth, parser_depth)}。"
    file_level_keys = {
        "file_format",
        "container_type",
        "parser_depth",
        "sample_count",
        "sample_block_count",
        "platform_count",
        "platform_block_presence",
        "sample_metadata_fields",
        "phenotype_candidate_fields",
        "platform_annotation_presence",
        "expression_table_presence",
        "species_evidence",
        "gene_id_evidence",
        "warnings",
        "can_enter_standardization",
        "requires_user_confirmation",
    }
    return _classification(
        "geo_soft_container",
        reason,
        0.86,
        roles=tuple(roles),
        detected_assets=tuple(assets),
        container_format="geo_family_soft",
        content_profile=profile,
        file_level_details={key: profile.get(key) for key in file_level_keys},
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


def _scan_geo_series_matrix(path: Path) -> dict[str, object]:
    scan: dict[str, object] = {
        "is_geo_series_matrix": False,
        "has_expression_matrix": False,
        "has_sample_metadata": False,
        "series_accession": "",
        "platform_id": "",
        "platform_line": None,
        "sample_count": 0,
        "gsm_column_count": 0,
        "table_begin_line": None,
        "table_end_line": None,
        "table_header_line": None,
        "table_data_row_count": 0,
        "sample_metadata_start_line": None,
        "sample_metadata_end_line": None,
        "expression_evidence": [],
        "sample_evidence": [],
        "platform_evidence": [],
        "phenotype_hits": [],
        "clinical_hits": [],
    }
    sample_lines: list[int] = []
    sample_accessions: set[str] = set()
    in_matrix_table = False
    header_columns: list[str] = []
    phenotype_tokens = {"tumor", "normal", "cancer", "disease", "tissue", "treatment", "group", "condition"}
    clinical_tokens = {"stage", "grade", "sex", "gender", "age", "survival", "status"}
    try:
        with _open_text(path) as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                lower = stripped.lower()
                if not stripped:
                    continue
                if stripped.startswith("!Series_title"):
                    scan["is_geo_series_matrix"] = True
                elif stripped.startswith("!Series_geo_accession"):
                    scan["is_geo_series_matrix"] = True
                    scan["series_accession"] = _metadata_value(stripped)
                elif stripped.startswith("!Series_platform_id"):
                    scan["is_geo_series_matrix"] = True
                    platform_id = _metadata_value(stripped)
                    scan["platform_id"] = platform_id
                    scan["platform_line"] = line_number
                    scan["platform_evidence"] = [f"Series_platform_id={platform_id}"] if platform_id else ["!Series_platform_id"]
                elif stripped.startswith("!Sample_title"):
                    sample_lines.append(line_number)
                    scan["sample_evidence"] = _append_unique(scan["sample_evidence"], "!Sample_title")
                elif stripped.startswith("!Sample_geo_accession"):
                    sample_lines.append(line_number)
                    sample_accession = _metadata_value(stripped)
                    if sample_accession:
                        sample_accessions.add(sample_accession)
                    scan["sample_evidence"] = _append_unique(scan["sample_evidence"], "!Sample_geo_accession")
                elif stripped.startswith("!Sample_characteristics_ch1") or stripped.startswith("!Sample_source_name_ch1"):
                    sample_lines.append(line_number)
                    token = stripped.split("=", 1)[0]
                    scan["sample_evidence"] = _append_unique(scan["sample_evidence"], token)
                    for hint in phenotype_tokens:
                        if hint in lower:
                            scan["phenotype_hits"] = _append_unique(scan["phenotype_hits"], hint)
                    for hint in clinical_tokens:
                        if hint in lower:
                            scan["clinical_hits"] = _append_unique(scan["clinical_hits"], hint)
                elif stripped.startswith("!series_matrix_table_begin"):
                    scan["is_geo_series_matrix"] = True
                    in_matrix_table = True
                    scan["table_begin_line"] = line_number
                    scan["expression_evidence"] = _append_unique(scan["expression_evidence"], "!series_matrix_table_begin")
                elif stripped.startswith("!series_matrix_table_end"):
                    scan["table_end_line"] = line_number
                    scan["expression_evidence"] = _append_unique(scan["expression_evidence"], "!series_matrix_table_end")
                    break
                elif in_matrix_table and scan["table_header_line"] is None:
                    header_columns = [_clean_cell(cell) for cell in _split_delimited_line(stripped, "\t")]
                    if header_columns and _normalize_header(header_columns[0]) == "id_ref":
                        scan["table_header_line"] = line_number
                        scan["expression_evidence"] = _append_unique(scan["expression_evidence"], "ID_REF header")
                        gsm_count = sum(1 for column in header_columns[1:] if _looks_like_sample_column(column))
                        scan["gsm_column_count"] = gsm_count
                        if gsm_count:
                            scan["expression_evidence"] = _append_unique(scan["expression_evidence"], "GSM sample columns")
                elif in_matrix_table and scan["table_header_line"] is not None:
                    cells = [_clean_cell(cell) for cell in _split_delimited_line(stripped, "\t")]
                    if len(cells) >= 2 and not stripped.startswith("!"):
                        scan["table_data_row_count"] = int(scan.get("table_data_row_count") or 0) + 1
    except OSError:
        return scan
    if not scan["platform_id"]:
        filename_platform = _platform_id_from_name(path.name)
        if filename_platform:
            scan["platform_id"] = filename_platform
            scan["platform_evidence"] = [f"filename contains {filename_platform}"]
    if sample_lines:
        scan["sample_metadata_start_line"] = min(sample_lines)
        scan["sample_metadata_end_line"] = max(sample_lines)
    scan["sample_count"] = max(len(sample_accessions), int(scan.get("gsm_column_count") or 0))
    scan["has_sample_metadata"] = bool(sample_lines or sample_accessions)
    scan["has_expression_matrix"] = bool(
        scan.get("table_begin_line")
        and scan.get("table_header_line")
        and int(scan.get("gsm_column_count") or 0) >= 1
        and int(scan.get("table_data_row_count") or 0) >= 1
    )
    if scan["has_expression_matrix"]:
        scan["is_geo_series_matrix"] = True
    return scan


def _profile_tabular_text(path: Path, *, max_rows: int = 250) -> dict[str, object] | None:
    try:
        lines: list[tuple[int, str]] = []
        with _open_text(path) as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if stripped:
                    lines.append((line_number, stripped))
                if len(lines) >= max_rows:
                    break
    except OSError:
        return None
    if not lines:
        return None
    delimiter = _detect_delimiter(path, [line for _, line in lines[:20]])
    header_line, header = _find_tabular_header(lines, delimiter)
    if not header or len(header) < 2:
        return None
    rows: list[list[str]] = []
    for line_number, line in lines:
        if line_number <= header_line:
            continue
        parsed = [_clean_cell(cell) for cell in _split_delimited_line(line, delimiter)]
        if len(parsed) >= 2:
            rows.append(parsed)
    return _profile_table_from_rows(header=header, rows=rows, delimiter=_delimiter_name(delimiter), header_line=header_line)


def _profile_xlsx_table(path: Path, *, max_rows: int = 250) -> dict[str, object] | None:
    try:
        rows = _xlsx_rows(path, max_rows=max_rows)
    except Exception:
        return None
    rows = [[_clean_cell(cell) for cell in row] for row in rows if any(_clean_cell(cell) for cell in row)]
    if not rows:
        return None
    header = rows[0]
    if len(header) < 2:
        return None
    data_rows = [row for row in rows[1:] if len(row) >= 2]
    return _profile_table_from_rows(header=header, rows=data_rows, delimiter="xlsx", header_line=1)


def _profile_table_from_rows(*, header: list[str], rows: list[list[str]], delimiter: str, header_line: int) -> dict[str, object]:
    normalized_header = [_normalize_header(column) for column in header]
    data_column_count = max(len(header) - 1, 0)
    numeric_by_column: dict[int, int] = {index: 0 for index in range(1, len(header))}
    integer_by_column: dict[int, int] = {index: 0 for index in range(1, len(header))}
    numeric_cells = 0
    integer_cells = 0
    non_negative_integer_cells = 0
    total_cells = 0
    for row in rows:
        for index in range(1, min(len(row), len(header))):
            total_cells += 1
            numeric = _to_float(row[index])
            if numeric is None:
                continue
            numeric_cells += 1
            numeric_by_column[index] += 1
            if _is_integer_value(row[index], numeric):
                integer_cells += 1
                integer_by_column[index] += 1
                if numeric >= 0:
                    non_negative_integer_cells += 1
    sampled_row_count = len(rows)
    numeric_column_indices = [
        index
        for index, count in numeric_by_column.items()
        if sampled_row_count and count / max(sampled_row_count, 1) >= 0.7
    ]
    deg_stat_column_count = sum(1 for column in normalized_header[1:] if column in DEG_STAT_COLUMNS or column.replace("_", "") in {"adjpval", "pvaladj", "qvalue"})
    sample_column_scores = {index: _sample_column_score(header[index], normalized_header[index], rows, index) for index in range(1, len(header))}
    sample_like_column_count = sum(1 for score in sample_column_scores.values() if score >= 2)
    header_hits = _header_keyword_hits(normalized_header)
    first_column_values = [row[0] for row in rows if row]
    first_column_pattern = _first_column_id_pattern(first_column_values)
    blocks_summary = _tabular_content_blocks(header, normalized_header, first_column_values)
    content_blocks = [block for block in blocks_summary.get("content_blocks", []) or [] if isinstance(block, dict)]
    expression_sample_columns = [str(item) for item in blocks_summary.get("expression_sample_columns", []) or [] if str(item)]
    tcga_barcodes = _tcga_barcodes_from_values([*header, *first_column_values])
    gtex_sample_ids = _gtex_sample_ids_from_values([*header, *first_column_values])
    diff_like = _is_differential_header(normalized_header)
    sample_metadata_like = _is_sample_metadata_header(normalized_header)
    clinical_like = _is_clinical_header(normalized_header)
    survival_like = _is_survival_header(normalized_header)
    annotation_like = _is_annotation_header(normalized_header)
    gdc_manifest_like = _is_gdc_manifest_header(normalized_header)
    first_gene_like = _is_gene_identifier_header(normalized_header[0]) or first_column_pattern in {"ensembl_id", "probe_id", "gene_symbol", "entrez_id"}
    numeric_ratio = numeric_cells / total_cells if total_cells else 0.0
    integer_numeric_ratio = integer_cells / numeric_cells if numeric_cells else 0.0
    non_negative_integer_ratio = non_negative_integer_cells / numeric_cells if numeric_cells else 0.0
    evidence: list[str] = [f"delimiter={delimiter}", f"columns={len(header)}", f"sampled_rows={sampled_row_count}"]
    extra_roles: list[str] = []
    possible_role = "unknown"
    has_embedded_annotation = False
    annotation_evidence: list[str] = []
    has_deg_block = any(block.get("block_type") == "deg_comparisons" for block in content_blocks)
    has_expression_block = any(str(block.get("block_type") or "").endswith("_expression_matrix") for block in content_blocks)
    if gdc_manifest_like:
        possible_role = "gdc_manifest"
        evidence.extend(["GDC manifest/sample sheet header"])
    elif (diff_like or has_deg_block) and not expression_sample_columns:
        possible_role = "differential_result_table"
        evidence.extend(["logFC header", "p-value header", "adjusted p-value/FDR header"])
    elif sample_metadata_like and numeric_ratio < 0.65:
        possible_role = "sample_metadata"
        if clinical_like:
            extra_roles.append("clinical_metadata")
        if survival_like:
            extra_roles.append("survival_metadata")
        evidence.extend(["sample metadata header keywords"])
    elif clinical_like or survival_like:
        possible_role = "clinical_metadata"
        if survival_like:
            extra_roles.append("survival_metadata")
        evidence.extend(["clinical header keywords"])
        if survival_like:
            evidence.append("time/status survival fields")
    elif annotation_like and not expression_sample_columns and numeric_ratio < 0.55:
        possible_role = "platform_annotation" if any("probe" in item or item == "id_ref" for item in normalized_header) else "gene_annotation"
        evidence.extend(["annotation header keywords"])
    elif first_gene_like and len(numeric_column_indices) >= 2 and numeric_ratio >= 0.55 and deg_stat_column_count < max(2, len(numeric_column_indices) // 2):
        possible_role = "raw_count_matrix" if integer_numeric_ratio >= 0.9 and non_negative_integer_ratio >= 0.95 else "normalized_expression_matrix"
        evidence.extend(["gene/probe first column", "numeric sample columns"])
        if sample_like_column_count:
            evidence.append("sample-like column names")
        annotation_columns = [
            str(column)
            for block in content_blocks
            if isinstance(block, dict) and block.get("block_type") in {"gene_annotation", "gene_identifier"}
            for column in (block.get("annotation_fields", []) or block.get("gene_name_columns", []) or [])
        ]
        has_embedded_annotation = bool(annotation_columns)
        annotation_evidence = [f"annotation column: {column}" for column in annotation_columns]
    sample_columns = expression_sample_columns or [
        header[index]
        for index in numeric_column_indices
        if index < len(header) and not _is_non_expression_sample_column(normalized_header[index])
    ]
    if possible_role == "unknown" and content_blocks:
        if has_deg_block:
            possible_role = "differential_result_table"
            evidence.extend(["embedded DEG comparison columns"])
        elif has_expression_block:
            possible_role = "raw_count_matrix" if any(block.get("value_type") == "count" for block in content_blocks) else "normalized_expression_matrix"
            evidence.extend(["embedded expression matrix columns"])
    profile = {
        "delimiter": delimiter,
        "header": header,
        "normalized_header": normalized_header,
        "header_line": header_line,
        "column_count": len(header),
        "sampled_row_count": sampled_row_count,
        "numeric_ratio": round(numeric_ratio, 4),
        "integer_numeric_ratio": round(integer_numeric_ratio, 4),
        "non_negative_integer_ratio": round(non_negative_integer_ratio, 4),
        "first_column_name": header[0],
        "first_column_id_pattern": first_column_pattern,
        "sample_like_column_count": sample_like_column_count,
        "deg_stat_column_count": deg_stat_column_count,
        "numeric_column_count": len(numeric_column_indices),
        "sample_columns": sample_columns,
        "sample_column_scores": {header[index]: score for index, score in sample_column_scores.items() if index < len(header)},
        "sample_id_columns": [header[index] for index, normalized in enumerate(normalized_header) if _is_sample_id_header(normalized)],
        "clinical_fields": [header[index] for index, normalized in enumerate(normalized_header) if _is_clinical_header([normalized]) or _is_survival_header([normalized])],
        "group_candidate_fields": [header[index] for index, normalized in enumerate(normalized_header) if any(token in normalized for token in ("group", "condition", "tissue", "disease", "case", "control", "treatment", "phenotype"))],
        "expression_value_type_candidate": _expression_value_type_candidate(header),
        "tcga_sample_barcodes": tcga_barcodes[:20],
        "tcga_sample_type_summary": _tcga_sample_type_summary(tcga_barcodes),
        "gtex_sample_ids": gtex_sample_ids[:20],
        "gtex_tissue_candidates": _gtex_tissue_candidates([*header, *first_column_values]),
        "source_domain": _source_domain_from_profile(normalized_header, tcga_barcodes, gtex_sample_ids),
        "known_keyword_hits": header_hits,
        "possible_table_role": possible_role,
        "evidence": evidence,
        "extra_roles": extra_roles,
        "has_embedded_annotation": has_embedded_annotation,
        "annotation_evidence": annotation_evidence,
    }
    if content_blocks:
        profile["content_blocks"] = content_blocks
    for key in ("semantic_type", "semantic_type_zh", "species", "species_group", "gene_id_type"):
        value = blocks_summary.get(key)
        if value:
            profile[key] = value
    return profile


def _tabular_content_blocks(header: list[str], normalized_header: list[str], first_column_values: list[str]) -> dict[str, object]:
    blocks: list[dict[str, object]] = []
    gene_block = _gene_identifier_block(header, normalized_header, first_column_values)
    if gene_block:
        blocks.append(gene_block)

    count_columns = _expression_columns_by_suffix(header, normalized_header, ("count", "counts"))
    count_block = _expression_matrix_block("count_expression_matrix", "count", count_columns)
    if count_block:
        blocks.append(count_block)

    fpkm_columns = _expression_columns_by_suffix(header, normalized_header, ("fpkm",))
    fpkm_block = _expression_matrix_block("fpkm_expression_matrix", "fpkm", fpkm_columns)
    if fpkm_block:
        fpkm_block["matches_count_sample_ids"] = sorted(fpkm_block.get("inferred_sample_ids", [])) == sorted(count_block.get("inferred_sample_ids", [])) if count_block else False
        blocks.append(fpkm_block)

    tpm_columns = _expression_columns_by_suffix(header, normalized_header, ("tpm",))
    tpm_block = _expression_matrix_block("tpm_expression_matrix", "tpm", tpm_columns)
    if tpm_block:
        tpm_block["matches_count_sample_ids"] = sorted(tpm_block.get("inferred_sample_ids", [])) == sorted(count_block.get("inferred_sample_ids", [])) if count_block else False
        blocks.append(tpm_block)

    deg_block = _deg_comparison_block(header, normalized_header)
    if deg_block:
        blocks.append(deg_block)

    annotation_block = _gene_annotation_block(header, normalized_header)
    if annotation_block:
        blocks.append(annotation_block)

    expression_sample_columns = []
    for block in (count_block, fpkm_block, tpm_block):
        if block:
            expression_sample_columns.extend(str(column) for column in block.get("sample_columns", []) or [])

    has_gene = bool(gene_block)
    has_expression = bool(count_block or fpkm_block or tpm_block)
    has_results_or_annotation = bool(deg_block or annotation_block)
    result: dict[str, object] = {
        "content_blocks": blocks,
        "expression_sample_columns": list(dict.fromkeys(expression_sample_columns)),
    }
    if gene_block:
        for key in ("species", "species_group", "gene_id_type"):
            if gene_block.get(key):
                result[key] = gene_block[key]
    if has_gene and has_expression and has_results_or_annotation:
        result["semantic_type"] = "rna_seq_integrated_result_table"
        result["semantic_type_zh"] = "RNA-seq 综合表达结果表"
    return result


def _gene_identifier_block(header: list[str], normalized_header: list[str], first_column_values: list[str]) -> dict[str, object]:
    gene_id_columns = [
        header[index]
        for index, normalized in enumerate(normalized_header)
        if normalized in {"gene_id", "ensembl_gene_id", "ensembl_id", "gene", "id_ref", "feature_id", "transcript_id"}
        or ("ensembl" in normalized and "gene" in normalized)
    ]
    gene_name_columns = [
        header[index]
        for index, normalized in enumerate(normalized_header)
        if normalized in {"gene_name", "gene_symbol", "symbol", "genesymbol"}
    ]
    gene_system = _infer_gene_id_system(first_column_values)
    if not gene_id_columns and not gene_name_columns and not gene_system.get("gene_id_type"):
        return {}
    block: dict[str, object] = {
        "block_type": "gene_identifier",
        "gene_id_columns": list(dict.fromkeys(str(column) for column in gene_id_columns)),
        "gene_name_columns": list(dict.fromkeys(str(column) for column in gene_name_columns)),
    }
    example_values = [value for value in first_column_values[:5] if str(value).strip()]
    if example_values:
        block["example_values"] = example_values
    for key, value in gene_system.items():
        if value:
            block[key] = value
    return block


def _infer_gene_id_system(values: list[str]) -> dict[str, str]:
    usable = [str(value).strip().upper().split(".", 1)[0] for value in values if str(value).strip()]
    if not usable:
        return {}
    patterns = (
        ("ensembl_mouse_transcript_id", "Mus musculus", "mouse", r"^ENSMUST\d+"),
        ("ensembl_mouse_gene_id", "Mus musculus", "mouse", r"^ENSMUSG\d+"),
        ("ensembl_human_gene_id", "Homo sapiens", "human", r"^ENSG\d+"),
    )
    threshold = max(1, len(usable) // 2 + 1)
    for gene_id_type, species, species_group, pattern in patterns:
        if sum(1 for value in usable if re.match(pattern, value)) >= threshold:
            return {"gene_id_type": gene_id_type, "species": species, "species_group": species_group}
    return {}


def _expression_columns_by_suffix(header: list[str], normalized_header: list[str], suffixes: tuple[str, ...]) -> list[dict[str, str]]:
    columns: list[dict[str, str]] = []
    suffix_pattern = "|".join(re.escape(suffix) for suffix in suffixes)
    for column, normalized in zip(header, normalized_header, strict=False):
        match = re.fullmatch(rf"(.+)_({suffix_pattern})", normalized)
        if not match:
            continue
        sample_id = _sample_id_from_expression_column(str(column), (match.group(2),))
        if not sample_id:
            sample_id = match.group(1)
        columns.append({"column": str(column), "sample_id": sample_id})
    return columns


def _sample_id_from_expression_column(column: str, suffixes: tuple[str, ...]) -> str:
    suffix_pattern = "|".join(re.escape(suffix) for suffix in suffixes)
    match = re.match(rf"^(.+)_({suffix_pattern})$", column.strip(), flags=re.IGNORECASE)
    return match.group(1) if match else ""


def _expression_matrix_block(block_type: str, value_type: str, columns: list[dict[str, str]]) -> dict[str, object]:
    if not columns:
        return {}
    sample_ids = [item["sample_id"] for item in columns]
    groups = [_sample_group_from_id(sample_id) for sample_id in sample_ids]
    group_counts: dict[str, int] = {}
    for group in groups:
        if group:
            group_counts[group] = group_counts.get(group, 0) + 1
    return {
        "block_type": block_type,
        "value_type": value_type,
        "sample_count": len(columns),
        "sample_columns": [item["column"] for item in columns],
        "inferred_sample_ids": sample_ids,
        "inferred_groups": list(dict.fromkeys(group for group in groups if group)),
        "replicate_count_by_group": group_counts,
    }


def _sample_group_from_id(sample_id: str) -> str:
    value = str(sample_id).strip()
    match = re.match(r"^(.+?)[_-]?\d+[A-Za-z]?$", value)
    if match:
        return match.group(1).strip("_-")
    return value


def _deg_comparison_block(header: list[str], normalized_header: list[str]) -> dict[str, object]:
    grouped: dict[str, dict[str, str]] = {}
    display_names: dict[str, str] = {}
    single_columns = _single_deg_metric_columns(header, normalized_header)
    for column, normalized in zip(header, normalized_header, strict=False):
        parsed = _parse_deg_column(str(column), normalized)
        if parsed is None:
            continue
        comparison_key, comparison_name, metric = parsed
        grouped.setdefault(comparison_key, {})[metric] = str(column)
        display_names.setdefault(comparison_key, comparison_name)
    if not grouped and not single_columns:
        return {}
    comparisons: list[dict[str, object]] = []
    for comparison_key, columns in grouped.items():
        name = display_names.get(comparison_key, comparison_key)
        left, right = _split_comparison_name(name)
        comparisons.append(
            {
                "comparison_name": name,
                "left_condition": left,
                "right_condition": right,
                "log2fc_column": columns.get("log2fc", ""),
                "pvalue_column": columns.get("pvalue", ""),
                "padj_column": columns.get("padj", ""),
                "is_complete": bool(columns.get("log2fc") and columns.get("pvalue") and columns.get("padj")),
            }
        )
    if single_columns:
        comparisons.insert(
            0,
            {
                "comparison_name": "imported_deg_results",
                "left_condition": "",
                "right_condition": "",
                "log2fc_column": single_columns.get("log2fc", ""),
                "pvalue_column": single_columns.get("pvalue", ""),
                "padj_column": single_columns.get("padj", ""),
                "is_complete": bool(single_columns.get("log2fc") and single_columns.get("pvalue") and single_columns.get("padj")),
            },
        )
    return {
        "block_type": "deg_comparisons",
        "comparison_count": len(comparisons),
        "complete_comparison_count": sum(1 for comparison in comparisons if comparison["is_complete"]),
        "comparisons": comparisons,
    }


def _single_deg_metric_columns(header: list[str], normalized_header: list[str]) -> dict[str, str]:
    columns: dict[str, str] = {}
    for column, normalized in zip(header, normalized_header, strict=False):
        metric = _deg_metric_from_header(normalized)
        if metric and metric not in columns:
            columns[metric] = str(column)
    return columns if "log2fc" in columns and ("pvalue" in columns or "padj" in columns) else {}


def _deg_metric_from_header(normalized: str) -> str:
    metric_map = {
        "log2foldchange": "log2fc",
        "log2fc": "log2fc",
        "logfc": "log2fc",
        "log2_fold_change": "log2fc",
        "log_fold_change": "log2fc",
        "p": "pvalue",
        "pvalue": "pvalue",
        "p_value": "pvalue",
        "p_val": "pvalue",
        "p_value_adj": "padj",
        "p_val_adj": "padj",
        "adj_p_val": "padj",
        "adj_p_value": "padj",
        "padj": "padj",
        "fdr": "padj",
        "qvalue": "padj",
        "q_value": "padj",
        "false_discovery_rate": "padj",
    }
    return metric_map.get(normalized, "")


def _parse_deg_column(column: str, normalized: str) -> tuple[str, str, str] | None:
    metric_map = {
        "log2foldchange": "log2fc",
        "log2fc": "log2fc",
        "logfc": "log2fc",
        "pvalue": "pvalue",
        "p_value": "pvalue",
        "padj": "padj",
        "fdr": "padj",
        "qvalue": "padj",
        "q_value": "padj",
    }
    normalized_match = re.fullmatch(r"(.+)_(log2foldchange|log2fc|logfc|pvalue|p_value|padj|fdr|qvalue|q_value)", normalized)
    if not normalized_match:
        return None
    raw_match = re.match(r"^(.+)_(log2FoldChange|log2fc|logFC|pvalue|p_value|padj|fdr|qvalue|q_value)$", column.strip(), flags=re.IGNORECASE)
    comparison_name = raw_match.group(1) if raw_match else normalized_match.group(1)
    comparison_key = _normalize_header(comparison_name)
    metric = metric_map[normalized_match.group(2)]
    return comparison_key, comparison_name, metric


def _split_comparison_name(name: str) -> tuple[str, str]:
    parts = re.split(r"vs", str(name), maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 2:
        return parts[0], parts[1]
    return name, ""


def _gene_annotation_block(header: list[str], normalized_header: list[str]) -> dict[str, object]:
    annotation_fields = [
        str(column)
        for column, normalized in zip(header, normalized_header, strict=False)
        if _is_gene_annotation_column(normalized)
    ]
    if not annotation_fields:
        return {}
    return {
        "block_type": "gene_annotation",
        "annotation_fields": list(dict.fromkeys(annotation_fields)),
    }


def _is_gene_annotation_column(normalized: str) -> bool:
    return normalized in {
        "gene_name",
        "gene_chr",
        "gene_chromosome",
        "chromosome",
        "chr",
        "gene_start",
        "start",
        "gene_end",
        "end",
        "gene_strand",
        "strand",
        "gene_length",
        "length",
        "gene_biotype",
        "biotype",
        "gene_description",
        "description",
        "tf_family",
        "gene_symbol",
        "symbol",
        "genesymbol",
    }


def _is_non_expression_sample_column(normalized: str) -> bool:
    return (
        _is_gene_annotation_column(normalized)
        or _parse_deg_column(normalized, normalized) is not None
        or bool(_deg_metric_from_header(normalized))
        or _is_annotation_header([normalized])
    )


def _is_geo_soft_path(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(".soft") or name.endswith(".soft.gz")


def _is_raw_heavy_path(path: Path) -> bool:
    name = path.name.lower()
    suffixes = _suffixes_lower(path)
    if any(name.endswith(suffix) for suffix in RAW_HEAVY_COMPOUND_SUFFIXES):
        return True
    if suffixes and suffixes[-1] in RAW_HEAVY_SUFFIXES:
        return True
    return path.suffix.lower() in {".fastq", ".fq"}


def _is_gdc_manifest_name(name: str) -> bool:
    normalized = name.lower()
    return "gdc" in normalized and ("manifest" in normalized or "sample_sheet" in normalized or "sample-sheet" in normalized)


def _is_geo_series_matrix_path(path: Path) -> bool:
    name = path.name.lower()
    suffixes = _suffixes_lower(path)
    text_like = bool(suffixes and (suffixes[-1] == ".txt" or suffixes[-2:] == [".txt", ".gz"]))
    return (
        ("series_matrix" in name and (name.endswith(".txt") or name.endswith(".txt.gz")))
        or name.endswith("_series_matrix.txt")
        or name.endswith("_series_matrix.txt.gz")
        or bool(re.search(r"gse\d+.*gpl\d+.*series_matrix\.txt(?:\.gz)?$", name))
        or (text_like and _file_has_geo_series_matrix_marker(path))
    )


def _file_has_geo_series_matrix_marker(path: Path, *, max_lines: int = 200) -> bool:
    try:
        with _open_text(path) as handle:
            for index, line in enumerate(handle):
                if index >= max_lines:
                    break
                stripped = line.strip()
                if stripped.startswith("!series_matrix_table_begin") or stripped.startswith("!Series_") or stripped.startswith("!Sample_"):
                    return True
    except OSError:
        return False
    return False


def _is_tabular_text_path(path: Path) -> bool:
    suffixes = _suffixes_lower(path)
    if suffixes and suffixes[-1] == ".gz":
        suffixes = suffixes[:-1]
    return bool(suffixes and suffixes[-1] in TEXT_TABLE_SUFFIXES)


def _suffixes_lower(path: Path) -> list[str]:
    return [suffix.lower() for suffix in path.suffixes]


def _open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8", errors="ignore") if path.name.lower().endswith(".gz") else path.open("r", encoding="utf-8", errors="ignore")


def _metadata_value(line: str) -> str:
    return _clean_cell(line.partition("=")[2].strip())


def _append_unique(values: object, value: str) -> list[str]:
    result = [str(item) for item in values or []]
    if value and value not in result:
        result.append(value)
    return result


def _platform_id_from_name(name: str) -> str:
    match = re.search(r"(GPL\d+)", name, flags=re.IGNORECASE)
    return match.group(1).upper() if match else ""


def _split_delimited_line(line: str, delimiter: str) -> list[str]:
    try:
        return next(csv.reader([line], delimiter=delimiter))
    except csv.Error:
        return line.split(delimiter)


def _clean_cell(value: object) -> str:
    return str(value).strip().strip('"').strip("'")


def _detect_delimiter(path: Path, lines: list[str]) -> str:
    suffixes = _suffixes_lower(path)
    if suffixes and suffixes[-1] == ".gz":
        suffixes = suffixes[:-1]
    if suffixes and suffixes[-1] == ".csv":
        return ","
    if suffixes and suffixes[-1] == ".tsv":
        return "\t"
    tab_score = sum(line.count("\t") for line in lines)
    comma_score = sum(line.count(",") for line in lines)
    return "\t" if tab_score >= comma_score else ","


def _delimiter_name(delimiter: str) -> str:
    return "tab" if delimiter == "\t" else "comma"


def _find_tabular_header(lines: list[tuple[int, str]], delimiter: str) -> tuple[int, list[str]]:
    for line_number, line in lines:
        if line.startswith("!") or line.startswith("^"):
            continue
        normalized_line = line[1:] if line.startswith("#") else line
        cells = [_clean_cell(cell) for cell in _split_delimited_line(normalized_line, delimiter)]
        if len(cells) >= 2:
            return line_number, cells
    return 0, []


def _to_float(value: str) -> float | None:
    raw = _clean_cell(value)
    if raw in {"", "NA", "N/A", "NaN", "nan", "null", "None"}:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _is_integer_value(raw_value: str, numeric_value: float) -> bool:
    return numeric_value.is_integer() and re.fullmatch(r"[+-]?\d+(?:\.0+)?", _clean_cell(raw_value)) is not None


def _sample_column_score(column: str, normalized: str, rows: list[list[str]], index: int) -> int:
    score = 0
    if _looks_like_sample_column(column):
        score += 2
    if normalized.startswith(("tcga", "gtex", "gsm", "srr", "err", "drr")):
        score += 2
    if normalized in DEG_STAT_COLUMNS or _is_annotation_header([normalized]):
        score -= 4
    sampled = 0
    numeric = 0
    for row in rows[:100]:
        if index >= len(row):
            continue
        sampled += 1
        if _to_float(row[index]) is not None:
            numeric += 1
    if sampled and numeric / sampled >= 0.7:
        score += 1
    return score


def _looks_like_sample_column(value: str) -> bool:
    normalized = _normalize_header(value)
    if not normalized:
        return False
    if normalized.startswith(("gsm", "srr", "err", "drr", "tcga", "gtex")):
        return True
    if any(token in normalized for token in ("sample", "count", "counts", "tpm", "fpkm")) and normalized not in DEG_STAT_COLUMNS:
        return True
    return re.fullmatch(r"[a-z]{0,3}\d+[a-z]?(?:_\d+)?", normalized) is not None


def _tcga_barcodes_from_values(values: list[str]) -> list[str]:
    barcodes: list[str] = []
    for value in values:
        for match in re.findall(r"TCGA-[A-Z0-9]{2}-[A-Z0-9]{4}(?:-[0-9]{2}[A-Z]?)?", str(value), flags=re.IGNORECASE):
            normalized = match.upper()
            if normalized not in barcodes:
                barcodes.append(normalized)
    return barcodes


def _tcga_sample_type_summary(barcodes: list[str]) -> dict[str, object]:
    if not barcodes:
        return {}
    validation = validate_tcga_sample_barcodes(barcodes)
    counts: dict[str, int] = {}
    tumor = 0
    normal = 0
    for parsed in validation.get("valid_barcodes", []) or []:
        if not isinstance(parsed, dict):
            continue
        code = str(parsed.get("sample_type_code") or "unknown")
        counts[code] = counts.get(code, 0) + 1
        tumor += 1 if parsed.get("is_tumor") else 0
        normal += 1 if parsed.get("is_normal") else 0
    return {
        "valid_count": validation.get("valid_count", 0),
        "invalid_count": validation.get("invalid_count", 0),
        "sample_type_counts": counts,
        "tumor_sample_count": tumor,
        "normal_sample_count": normal,
    }


def _gtex_sample_ids_from_values(values: list[str]) -> list[str]:
    ids: list[str] = []
    for value in values:
        for match in re.findall(r"GTEX-[A-Z0-9]+(?:-[A-Z0-9]+){1,4}", str(value), flags=re.IGNORECASE):
            normalized = match.upper()
            if normalized not in ids:
                ids.append(normalized)
    return ids


def _gtex_tissue_candidates(values: list[str]) -> list[str]:
    candidates: list[str] = []
    for value in values:
        lowered = str(value).lower()
        if "tissue" in lowered or "tissuesitedetail" in lowered or "tissue_site_detail" in lowered:
            cleaned = _clean_cell(value)
            if cleaned and cleaned not in candidates:
                candidates.append(cleaned)
    return candidates[:20]


def _source_domain_from_profile(headers: list[str], tcga_barcodes: list[str], gtex_sample_ids: list[str]) -> str:
    header_text = " ".join(headers)
    if tcga_barcodes or "tcga" in header_text or "submitter_id" in header_text or "case_id" in header_text:
        return "tcga"
    if gtex_sample_ids or "gtex" in header_text or "smts" in headers or "smtssd" in headers or "tissue_site_detail" in header_text:
        return "gtex"
    return ""


def _expression_value_type_candidate(headers: list[str]) -> str:
    text = " ".join(_normalize_header(header) for header in headers)
    if any(token in text for token in ("raw_count", "counts", "count")):
        return "count"
    if "tpm" in text:
        return "TPM"
    if "fpkm" in text:
        return "FPKM"
    if "cpm" in text:
        return "CPM"
    if any(token in text for token in ("log2", "log_expression", "logexpr")):
        return "log_expression"
    if "normalized" in text or "norm" in text:
        return "normalized_expression"
    return "unknown_expression_value"


def _expression_value_type_from_role(role: str) -> str:
    if role == "raw_count_matrix":
        return "count"
    return "unknown_expression_value"


def _expression_asset_reason(role: str) -> str:
    if role == "tcga_expression_matrix":
        return "表格第一列像基因/探针 ID，后续多列为 TCGA barcode 样本表达值。"
    if role == "gtex_expression_matrix":
        return "表格第一列像基因/探针 ID，后续多列为 GTEx normal reference 样本表达值。"
    return "表格第一列像基因/探针 ID，后续多列为高比例数值样本列。"


def _header_keyword_hits(headers: list[str]) -> list[str]:
    keywords = {
        "gene",
        "symbol",
        "id_ref",
        "probe",
        "ensembl",
        "sample",
        "sample_id",
        "gsm",
        "group",
        "condition",
        "tissue",
        "disease",
        "case",
        "control",
        "treatment",
        "age",
        "sex",
        "gender",
        "stage",
        "grade",
        "status",
        "survival",
        "os_time",
        "os_status",
        "logfc",
        "p_value",
        "adj_p_val",
        "padj",
        "fdr",
        "qvalue",
    }
    hits: list[str] = []
    for header in headers:
        for keyword in keywords:
            if keyword in header and keyword not in hits:
                hits.append(keyword)
    return hits


def _first_column_id_pattern(values: list[str]) -> str:
    if not values:
        return "unknown"
    sample = values[:100]
    ensembl = sum(1 for value in sample if re.match(r"ENS[A-Z]*G\d+", _clean_cell(value), flags=re.IGNORECASE))
    probe = sum(1 for value in sample if re.match(r"\d+_[a-z]+_at|[A-Z]{2,}\d+", _clean_cell(value), flags=re.IGNORECASE))
    gene_symbol = sum(1 for value in sample if re.match(r"[A-Za-z][A-Za-z0-9.-]{1,12}$", _clean_cell(value)))
    entrez = sum(1 for value in sample if re.fullmatch(r"\d{3,12}", _clean_cell(value)))
    threshold = max(1, int(len(sample) * 0.5))
    if ensembl >= threshold:
        return "ensembl_id"
    if probe >= threshold:
        return "probe_id"
    if entrez >= threshold:
        return "entrez_id"
    if gene_symbol >= threshold:
        return "gene_symbol"
    return "unknown"


def _is_gene_identifier_header(header: str) -> bool:
    return any(token in header for token in ("gene", "ensembl", "probe", "symbol", "id_ref", "feature", "transcript"))


def _is_differential_header(headers: list[str]) -> bool:
    has_logfc = any(header in {"logfc", "log2fc", "log2_fold_change", "log_fold_change"} or "logfc" in header for header in headers)
    has_p = any(header in {"p", "pvalue", "p_value", "p_val", "p_val_adj", "p_value_adj"} or header.startswith("p_") for header in headers)
    has_adj = any(header in {"adj_p_val", "adj_p_value", "padj", "fdr", "qvalue", "q_value", "false_discovery_rate"} for header in headers)
    has_stat = any(header in {"stat", "statistic", "t", "b", "wald_stat"} for header in headers)
    return has_logfc and has_p and (has_adj or has_stat)


def _is_sample_id_header(header: str) -> bool:
    return header in {"sample", "sample_id", "sampleid", "gsm", "geo_accession", "barcode", "submitter_id", "case_submitter_id"} or "sample_id" in header


def _is_sample_metadata_header(headers: list[str]) -> bool:
    has_sample = any(_is_sample_id_header(header) or "sample" in header or header.startswith(("gtex", "tcga")) for header in headers)
    has_attribute = any(any(token in header for token in ("group", "condition", "tissue", "disease", "case", "control", "treatment", "phenotype", "smts", "smtssd", "sample_type")) for header in headers)
    return has_sample and has_attribute


def _is_clinical_header(headers: list[str]) -> bool:
    clinical_tokens = ("age", "sex", "gender", "stage", "grade", "status", "vital", "death", "survival", "days", "months")
    return sum(1 for header in headers if any(token in header for token in clinical_tokens)) >= 2


def _is_survival_header(headers: list[str]) -> bool:
    has_time = any(any(token in header for token in ("time", "days", "months", "os", "dfs", "pfs", "survival")) for header in headers)
    has_status = any(any(token in header for token in ("status", "vital", "death", "event")) for header in headers)
    return has_time and has_status


def _is_annotation_header(headers: list[str]) -> bool:
    annotation_tokens = ("probe", "id_ref", "gene_symbol", "symbol", "gene_assignment", "entrez", "ensembl", "chromosome", "chr", "description")
    return any(any(token in header for token in annotation_tokens) for header in headers)


def _is_gdc_manifest_header(headers: list[str]) -> bool:
    header_set = set(headers)
    return {"id", "filename"} <= header_set and bool(header_set & {"md5", "size", "state", "data_type", "experimental_strategy"})


def _tabular_role_reason(role: str) -> str:
    return {
        "clinical_metadata": "表头包含 age/sex/stage/grade/status 等临床字段。",
        "survival_metadata": "表头同时包含生存时间和状态字段。",
        "platform_annotation": "表头包含 probe/ID_REF/gene_symbol/ENTREZ/ENSEMBL/chromosome 等平台注释字段。",
        "gene_annotation": "表头包含 gene_symbol/ENTREZ/ENSEMBL/chromosome 等基因注释字段。",
        "tcga_clinical_metadata": "表头包含 TCGA patient/sample barcode、临床字段或生存字段。",
        "tcga_sample_metadata": "表头包含 TCGA barcode、sample type 或 GDC sample metadata 字段。",
        "gtex_sample_metadata": "表头包含 GTEx sample/subject/tissue phenotype 字段。",
    }.get(role, "表格内容命中该资产角色。")


def _detected_asset(
    asset_type: str,
    *,
    confidence: float,
    reason: str,
    source_section: str = "file",
    source_format: str = "",
    input_eligible: bool | None = None,
    evidence: tuple[str, ...] = (),
    location: dict[str, object] | None = None,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    clean_location = {key: value for key, value in (location or {"source_section": source_section}).items() if value is not None}
    clean_evidence = [str(item) for item in evidence if str(item)] or [reason]
    payload: dict[str, object] = {
        "role": asset_type,
        "asset_type": asset_type,
        "label_zh": TYPE_LABELS.get(asset_type, asset_type),
        "confidence": _confidence_label(confidence),
        "confidence_score": confidence,
        "input_eligible": asset_type in INPUT_ELIGIBLE_ROLES if input_eligible is None else input_eligible,
        "evidence": clean_evidence,
        "location": clean_location,
        "reason": reason,
        "source_section": source_section,
    }
    if source_format:
        payload["source_format"] = source_format
    if extra:
        payload.update(extra)
    return payload


def _confidence_label(value: float) -> str:
    if value >= 0.8:
        return "high"
    if value >= 0.6:
        return "medium"
    return "low"


def _xlsx_first_row(path: Path, *, max_cells: int = 200) -> list[str]:
    rows = _xlsx_rows(path, max_rows=1, max_cells=max_cells)
    return rows[0] if rows else []


def _xlsx_rows(path: Path, *, max_rows: int = 250, max_cells: int = 500) -> list[list[str]]:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        worksheet_name = "xl/worksheets/sheet1.xml"
        if worksheet_name not in names:
            return []
        shared_strings = _xlsx_shared_strings(archive, names)
        worksheet = ElementTree.fromstring(archive.read(worksheet_name))
        parsed_rows: list[list[str]] = []
        for row in worksheet.findall(".//{*}sheetData/{*}row")[:max_rows]:
            values_by_column: dict[int, str] = {}
            for cell in list(row.findall("{*}c"))[:max_cells]:
                column_index = _xlsx_column_index(str(cell.attrib.get("r", "")))
                values_by_column[column_index] = _xlsx_cell_value(cell, shared_strings)
            if values_by_column:
                parsed_rows.append([values_by_column.get(index, "") for index in range(max(values_by_column) + 1)])
        return parsed_rows


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
            paths.extend(path for path in base.rglob("*") if _is_recognition_candidate_file(path, root))
    paths.extend(_registered_reference_files(root))
    deduped: dict[str, Path] = {}
    for path in paths:
        key = str(path.resolve()) if path.exists() else str(path)
        deduped.setdefault(key, path.resolve() if path.exists() else path)
    return sorted(deduped.values())


def _expand_selected_candidate_paths(root: Path, selected_paths: list[str | Path] | tuple[str | Path, ...]) -> list[Path]:
    paths: list[Path] = []
    for raw in selected_paths:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = root / path
        if path.is_file() and _is_recognition_candidate_file(path, root):
            paths.append(path.resolve())
        elif path.is_dir():
            paths.extend(candidate.resolve() for candidate in path.rglob("*") if _is_recognition_candidate_file(candidate, root))
    deduped: dict[str, Path] = {}
    for path in paths:
        key = str(path.resolve()) if path.exists() else str(path)
        deduped.setdefault(key, path.resolve() if path.exists() else path)
    return sorted(deduped.values())


def _is_recognition_candidate_file(path: Path, root: Path) -> bool:
    if not path.is_file() or path.suffix.lower() in {".json"}:
        return False
    if path.name.lower().endswith((".part", ".tmp", ".download", ".partial")):
        return False
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError:
        relative = path
    parts = relative.parts
    if len(parts) >= 3 and parts[0] == "raw_data" and parts[1] == "geo" and parts[2] == "organized":
        return False
    return True


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
                    paths.extend(path.resolve() for path in candidate.rglob("*") if _is_recognition_candidate_file(path, root))
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


def _read_json_if_exists(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
