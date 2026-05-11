from __future__ import annotations

import csv
import json
import gzip
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

from app.bioinformatics.group_preview import GROUP_PREVIEW_REPORT, build_group_preview_report

RECOGNITION_REPORT = Path("logs") / "recognition" / "recognition_report.json"
RECOGNITION_RUNS_DIR = Path("recognized_data") / "runs"
CURRENT_RECOGNITION_RUN = Path("recognized_data") / "current.json"

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
}

TEXT_TABLE_SUFFIXES = {".csv", ".tsv", ".txt", ".matrix"}
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


def run_project_recognition(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    files = _candidate_files(root)
    report = _run_project_recognition_for_files(root, files)
    _write_recognition_run(
        root,
        report,
        selected_inputs=[str(path) for path in files],
        batch_label="本次识别",
        set_current=True,
    )
    return report


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
    _write_recognition_run(
        root,
        report,
        selected_inputs=[str(path) for path in files],
        batch_label="本次识别",
        set_current=True,
    )
    return report


def _run_project_recognition_for_files(root: Path, files: list[Path]) -> dict[str, object]:
    warnings: list[str] = []
    records: list[dict[str, object]] = []
    if not files:
        warnings.append("未找到可识别的数据文件，请返回数据来源页补充数据。")
    for path in files:
        classification = classify_file_details(path)
        kind = classification.primary_type
        reason = classification.reason
        confidence = classification.confidence
        content_profile = classification.content_profile or {}
        record = {
            "file_name": path.name,
            "original_path": str(path),
            "recognized_type": kind,
            "recognized_type_zh": TYPE_LABELS.get(kind, "未知文件"),
            "recognized_roles": list(classification.roles),
            "recognized_roles_zh": [TYPE_LABELS.get(role, role) for role in classification.roles],
            "secondary_roles": [role for role in classification.roles if role != kind],
            "detected_assets": list(classification.detected_assets),
            "container_format": classification.container_format,
            "content_profile": content_profile,
            "confidence": confidence,
            "file_size": path.stat().st_size if path.exists() else 0,
            "reason": reason,
            "warning": "低置信度，需要人工确认。" if confidence < 0.5 else "",
            "route_path": str(root / "recognized_data" / kind / path.name),
        }
        record.update(_semantic_record_fields(kind, content_profile))
        records.append(record)
    warnings.extend(_recognition_warnings(records))
    group_preview = build_group_preview_report(root, records)
    report = {
        "schema_version": "biomedpilot.recognition_report.v1",
        "generated_at": _now(),
        "project_root": str(root),
        "files": records,
        "type_counts": _type_counts(records),
        "group_preview": group_preview,
        "warnings": warnings,
    }
    return report


def load_recognition_report(project_root: str | Path) -> dict[str, object] | None:
    root = Path(project_root).expanduser().resolve()
    current = _load_current_run(root)
    if current is None:
        return None
    report_path = Path(str(current.get("recognition_report_path") or ""))
    if not report_path.is_absolute():
        report_path = root / report_path
    try:
        return json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else None
    except (OSError, json.JSONDecodeError):
        return None


def list_recognition_runs(project_root: str | Path, *, include_legacy: bool = True) -> list[dict[str, object]]:
    root = Path(project_root).expanduser().resolve()
    if include_legacy:
        archive_legacy_recognition_report(root)
    runs_dir = root / RECOGNITION_RUNS_DIR
    current = _load_current_run(root) or {}
    current_run_id = str(current.get("run_id") or "")
    runs: list[dict[str, object]] = []
    if not runs_dir.exists():
        return []
    for run_dir in sorted((path for path in runs_dir.iterdir() if path.is_dir()), reverse=True):
        manifest_path = run_dir / "input_manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(manifest, dict):
            continue
        report_path = run_dir / "recognition_report.json"
        report = _read_json_if_exists(report_path) or {}
        files = report.get("files") if isinstance(report, dict) else []
        warnings = report.get("warnings") if isinstance(report, dict) else []
        runs.append(
            {
                **manifest,
                "run_id": str(manifest.get("run_id") or run_dir.name),
                "run_dir": str(run_dir),
                "recognition_report_path": str(report_path),
                "recognized_file_count": len(files) if isinstance(files, list) else 0,
                "warning_count": len(warnings) if isinstance(warnings, list) else 0,
                "status": str(manifest.get("status") or "completed"),
                "is_current": str(manifest.get("run_id") or run_dir.name) == current_run_id,
            }
        )
    return runs


def archive_legacy_recognition_report(project_root: str | Path) -> dict[str, object] | None:
    root = Path(project_root).expanduser().resolve()
    if (root / CURRENT_RECOGNITION_RUN).exists():
        return None
    legacy_path = root / RECOGNITION_REPORT
    if not legacy_path.exists():
        return None
    legacy_run_dir = root / RECOGNITION_RUNS_DIR / "legacy_recognition_report"
    manifest_path = legacy_run_dir / "input_manifest.json"
    if manifest_path.exists():
        return _read_json_if_exists(manifest_path)
    try:
        report = json.loads(legacy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(report, dict):
        return None
    report = _filter_system_file_records(report)
    _write_recognition_run(
        root,
        report,
        selected_inputs=[str(item.get("original_path") or "") for item in report.get("files", []) or [] if isinstance(item, dict)],
        batch_label="旧版识别记录",
        run_id="legacy_recognition_report",
        set_current=False,
        legacy=True,
    )
    return _read_json_if_exists(manifest_path)


def set_current_recognition_run(project_root: str | Path, run_id: str) -> bool:
    root = Path(project_root).expanduser().resolve()
    run_dir = root / RECOGNITION_RUNS_DIR / run_id
    report_path = run_dir / "recognition_report.json"
    if not report_path.exists():
        return False
    report = _read_json_if_exists(report_path) or {}
    group_preview = report.get("group_preview") if isinstance(report, dict) else {}
    _write_json(root / CURRENT_RECOGNITION_RUN, {
        "schema_version": "biomedpilot.current_recognition_run.v1",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "recognition_report_path": str(report_path),
        "set_at": _now(),
    })
    if isinstance(group_preview, dict):
        _write_json(root / GROUP_PREVIEW_REPORT, group_preview)
    return True


def delete_recognition_run(project_root: str | Path, run_id: str) -> bool:
    root = Path(project_root).expanduser().resolve()
    run_dir = root / RECOGNITION_RUNS_DIR / run_id
    if not run_dir.exists() or not run_dir.is_dir():
        return False
    current = _load_current_run(root) or {}
    if str(current.get("run_id") or "") == run_id:
        try:
            (root / CURRENT_RECOGNITION_RUN).unlink(missing_ok=True)
        except OSError:
            pass
    import shutil

    shutil.rmtree(run_dir)
    return True


def _write_recognition_run(
    root: Path,
    report: dict[str, object],
    *,
    selected_inputs: list[str],
    batch_label: str,
    set_current: bool,
    run_id: str | None = None,
    legacy: bool = False,
) -> dict[str, object]:
    clean_report = _filter_system_file_records(report)
    run_id = run_id or _unique_run_id(root)
    run_dir = root / RECOGNITION_RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    files = [item for item in clean_report.get("files", []) or [] if isinstance(item, dict)]
    warnings = [str(item) for item in clean_report.get("warnings", []) or []]
    manifest = {
        "schema_version": "biomedpilot.recognition_run.v1",
        "run_id": run_id,
        "batch_name": batch_label,
        "generated_at": str(clean_report.get("generated_at") or _now()),
        "input_data": [value for value in selected_inputs if str(value).strip()],
        "input_count": len([value for value in selected_inputs if str(value).strip()]),
        "recognized_file_count": len(files),
        "warning_count": len(warnings),
        "status": "completed",
        "legacy": legacy,
    }
    _write_json(run_dir / "input_manifest.json", manifest)
    _write_json(run_dir / "recognized_files.json", {"files": files})
    _write_json(run_dir / "recognition_report.json", clean_report)
    _write_json(run_dir / "warnings.json", {"warnings": warnings})
    if set_current:
        _write_json(root / CURRENT_RECOGNITION_RUN, {
            "schema_version": "biomedpilot.current_recognition_run.v1",
            "run_id": run_id,
            "run_dir": str(run_dir),
            "recognition_report_path": str(run_dir / "recognition_report.json"),
            "set_at": _now(),
        })
        group_preview = clean_report.get("group_preview")
        if isinstance(group_preview, dict):
            _write_json(root / GROUP_PREVIEW_REPORT, group_preview)
        _write_json(root / RECOGNITION_REPORT, clean_report)
    return manifest


def _unique_run_id(root: Path) -> str:
    base = "recognition_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    runs_dir = root / RECOGNITION_RUNS_DIR
    candidate = base
    index = 2
    while (runs_dir / candidate).exists():
        candidate = f"{base}_{index}"
        index += 1
    return candidate


def _load_current_run(root: Path) -> dict[str, object] | None:
    return _read_json_if_exists(root / CURRENT_RECOGNITION_RUN)


def _read_json_if_exists(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _filter_system_file_records(report: dict[str, object]) -> dict[str, object]:
    files = [
        item
        for item in report.get("files", []) or []
        if isinstance(item, dict)
        and not _is_system_file_name(str(item.get("file_name") or Path(str(item.get("original_path") or "")).name))
        and not _is_system_path(Path(str(item.get("original_path") or "")))
    ]
    clean = {**report, "files": files, "type_counts": _type_counts(files)}
    return clean


def _semantic_record_fields(file_kind: str, content_profile: dict[str, object]) -> dict[str, object]:
    fields: dict[str, object] = {"file_kind": file_kind}
    for key in ("semantic_type", "semantic_type_zh", "species", "species_group", "gene_id_type", "content_blocks"):
        value = content_profile.get(key)
        if value not in (None, "", []):
            fields[key] = value
    return fields


def _recognition_warnings(records: list[dict[str, object]]) -> list[str]:
    expression_records = [
        record
        for record in records
        if any(role in set(record.get("recognized_roles", []) or []) for role in ("expression_matrix", "normalized_expression_matrix", "raw_count_matrix"))
    ]
    if len(expression_records) > 1:
        return ["multiple expression candidates detected; manual review may be required"]
    return []


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
    )


def _classify_xlsx_table(path: Path) -> RecognitionClassification | None:
    profile = _profile_xlsx_table(path)
    if not profile:
        return None
    classification = _classification_from_table_profile(profile, source_format="xlsx_workbook", container_format="xlsx_workbook")
    if classification is None:
        return None
    return classification


def _classify_geo_series_matrix(path: Path) -> RecognitionClassification | None:
    scan = _scan_geo_series_matrix(path)
    if not scan.get("is_geo_series_matrix"):
        return None
    assets: list[dict[str, object]] = []
    roles: list[str] = []
    if scan.get("has_expression_matrix"):
        roles.append("expression_matrix")
        assets.append(
            _detected_asset(
                "expression_matrix",
                confidence=0.9,
                reason="GEO Series Matrix 表格包含 ID_REF 和 GSM 样本列。",
                source_section="series_matrix_table",
                source_format="geo_series_matrix",
                input_eligible=True,
                evidence=tuple(scan.get("expression_evidence", []) or ()),
                location={
                    "start_line": scan.get("table_begin_line"),
                    "end_line": scan.get("table_end_line"),
                    "header_line": scan.get("table_header_line"),
                },
                extra={"gsm_column_count": scan.get("gsm_column_count", 0)},
            )
        )
    if scan.get("has_sample_metadata"):
        roles.append("sample_metadata")
        assets.append(
            _detected_asset(
                "sample_metadata",
                confidence=0.86,
                reason="GEO Series Matrix 包含样本标题、GSM 编号或样本 characteristics。",
                source_section="sample_metadata",
                source_format="geo_series_matrix",
                input_eligible=True,
                evidence=tuple(scan.get("sample_evidence", []) or ()),
                location={
                    "start_line": scan.get("sample_metadata_start_line"),
                    "end_line": scan.get("sample_metadata_end_line"),
                },
                extra={"sample_count": scan.get("sample_count", 0)},
            )
        )
    platform_id = str(scan.get("platform_id") or "")
    if platform_id:
        roles.append("platform_reference_hint")
        assets.append(
            _detected_asset(
                "platform_reference_hint",
                confidence=0.82,
                reason="GEO Series Matrix 提供 GPL 平台编号，可用于后续平台注释匹配。",
                source_section="series_metadata",
                source_format="geo_series_matrix",
                input_eligible=False,
                evidence=tuple(scan.get("platform_evidence", []) or ()),
                location={"line": scan.get("platform_line")},
                extra={"platform_id": platform_id},
            )
        )
    phenotype_hits = list(scan.get("phenotype_hits", []) or [])
    if phenotype_hits:
        roles.append("phenotype_metadata")
        assets.append(
            _detected_asset(
                "phenotype_metadata",
                confidence=0.72,
                reason="样本 characteristics/source 中包含分组、组织、疾病或处理线索。",
                source_section="sample_metadata",
                source_format="geo_series_matrix",
                input_eligible=True,
                evidence=tuple(phenotype_hits),
                location={
                    "start_line": scan.get("sample_metadata_start_line"),
                    "end_line": scan.get("sample_metadata_end_line"),
                },
            )
        )
    clinical_hits = list(scan.get("clinical_hits", []) or [])
    if clinical_hits:
        roles.append("clinical_metadata")
        assets.append(
            _detected_asset(
                "clinical_metadata",
                confidence=0.7,
                reason="样本 metadata 中包含年龄、性别、分期、分级、生存或状态线索。",
                source_section="sample_metadata",
                source_format="geo_series_matrix",
                input_eligible=True,
                evidence=tuple(clinical_hits),
                location={
                    "start_line": scan.get("sample_metadata_start_line"),
                    "end_line": scan.get("sample_metadata_end_line"),
                },
            )
        )
    if not roles:
        return None
    role_labels = "、".join(TYPE_LABELS.get(role, role) for role in dict.fromkeys(roles))
    return _classification(
        "geo_series_matrix_container",
        f"GEO Series Matrix 容器，检测到：{role_labels}。",
        0.9,
        roles=tuple(dict.fromkeys(roles)),
        detected_assets=tuple(assets),
        container_format="geo_series_matrix",
        content_profile={
            "format": "geo_series_matrix",
            "series_accession": scan.get("series_accession") or "",
            "platform_id": platform_id,
            "sample_count": scan.get("sample_count", 0),
            "table_begin_line": scan.get("table_begin_line"),
            "table_end_line": scan.get("table_end_line"),
            "table_header_line": scan.get("table_header_line"),
            "table_data_row_count": scan.get("table_data_row_count", 0),
            "gsm_column_count": scan.get("gsm_column_count", 0),
        },
    )


def _classify_tabular_text(path: Path) -> RecognitionClassification | None:
    profile = _profile_tabular_text(path)
    if not profile:
        return None
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
    if primary == "differential_result_table":
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
    elif primary in {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix"}:
        confidence = 0.86 if primary == "raw_count_matrix" else 0.82
        assets.append(
            _detected_asset(
                primary,
                confidence=confidence,
                reason="表格第一列像基因/探针 ID，后续多列为高比例数值样本列。",
                source_section="tabular_matrix",
                source_format=source_format,
                input_eligible=True,
                evidence=tuple(evidence),
                location={"header_line": header_line},
                extra={
                    "delimiter": profile.get("delimiter"),
                    "numeric_column_count": profile.get("numeric_column_count", 0),
                    "sample_like_column_count": profile.get("sample_like_column_count", 0),
                },
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
    elif primary == "sample_metadata":
        roles.extend(str(role) for role in profile.get("extra_roles", []) or [])
        for role in dict.fromkeys(roles):
            role_reason = "表头包含 sample/group/condition/tissue/disease 等样本属性字段。"
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
    elif primary in {"clinical_metadata", "survival_metadata", "platform_annotation", "gene_annotation"}:
        roles.extend(str(role) for role in profile.get("extra_roles", []) or [])
        for role in dict.fromkeys(roles):
            input_eligible = role not in {"platform_reference_hint"}
            assets.append(
                _detected_asset(
                    role,
                    confidence=0.78,
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
    sample_like_column_count = sum(1 for column in header[1:] if _looks_like_sample_column(column))
    header_hits = _header_keyword_hits(normalized_header)
    first_column_values = [row[0] for row in rows if row]
    first_column_pattern = _first_column_id_pattern(first_column_values)
    blocks_summary = _tabular_content_blocks(header, normalized_header, first_column_values)
    content_blocks = list(blocks_summary.get("content_blocks", []) or [])
    expression_sample_columns = list(blocks_summary.get("expression_sample_columns", []) or [])
    diff_like = _is_differential_header(normalized_header)
    sample_metadata_like = _is_sample_metadata_header(normalized_header)
    clinical_like = _is_clinical_header(normalized_header)
    survival_like = _is_survival_header(normalized_header)
    annotation_like = _is_annotation_header(normalized_header)
    first_gene_like = _is_gene_identifier_header(normalized_header[0]) or first_column_pattern in {"ensembl_id", "probe_id", "gene_symbol", "entrez_id"} or bool(blocks_summary.get("gene_id_type"))
    numeric_ratio = numeric_cells / total_cells if total_cells else 0.0
    integer_numeric_ratio = integer_cells / numeric_cells if numeric_cells else 0.0
    non_negative_integer_ratio = non_negative_integer_cells / numeric_cells if numeric_cells else 0.0
    evidence: list[str] = [f"delimiter={delimiter}", f"columns={len(header)}", f"sampled_rows={sampled_row_count}"]
    extra_roles: list[str] = []
    possible_role = "unknown"
    has_embedded_annotation = False
    annotation_evidence: list[str] = []
    if diff_like and not expression_sample_columns:
        possible_role = "differential_result_table"
        evidence.extend(["logFC header", "p-value header", "adjusted p-value/FDR header"])
    elif clinical_like or survival_like:
        possible_role = "clinical_metadata"
        if survival_like:
            extra_roles.append("survival_metadata")
        evidence.extend(["clinical header keywords"])
        if survival_like:
            evidence.append("time/status survival fields")
    elif sample_metadata_like and numeric_ratio < 0.65:
        possible_role = "sample_metadata"
        if clinical_like:
            extra_roles.append("clinical_metadata")
        if survival_like:
            extra_roles.append("survival_metadata")
        evidence.extend(["sample metadata header keywords"])
    elif first_gene_like and len(numeric_column_indices) >= 2 and numeric_ratio >= 0.55:
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
    elif annotation_like and len(numeric_column_indices) < 2:
        possible_role = "platform_annotation" if any("probe" in item or item == "id_ref" for item in normalized_header) else "gene_annotation"
        evidence.extend(["annotation header keywords"])
    sample_columns = expression_sample_columns or [
        header[index]
        for index in numeric_column_indices
        if index < len(header) and not _is_non_expression_sample_column(normalized_header[index])
    ]
    profile = {
        "delimiter": delimiter,
        "header_line": header_line,
        "column_count": len(header),
        "sampled_row_count": sampled_row_count,
        "numeric_ratio": round(numeric_ratio, 4),
        "integer_numeric_ratio": round(integer_numeric_ratio, 4),
        "non_negative_integer_ratio": round(non_negative_integer_ratio, 4),
        "first_column_name": header[0],
        "first_column_id_pattern": first_column_pattern,
        "sample_like_column_count": sample_like_column_count,
        "numeric_column_count": len(numeric_column_indices),
        "sample_columns": sample_columns,
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

    deg_block = _deg_comparison_block(header, normalized_header)
    if deg_block:
        blocks.append(deg_block)

    annotation_block = _gene_annotation_block(header, normalized_header)
    if annotation_block:
        blocks.append(annotation_block)

    expression_sample_columns = []
    for block in (count_block, fpkm_block):
        if block:
            expression_sample_columns.extend(str(column) for column in block.get("sample_columns", []) or [])

    has_gene = bool(gene_block)
    has_expression = bool(count_block or fpkm_block)
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
    for column, normalized in zip(header, normalized_header, strict=False):
        parsed = _parse_deg_column(str(column), normalized)
        if parsed is None:
            continue
        comparison_key, comparison_name, metric = parsed
        grouped.setdefault(comparison_key, {})[metric] = str(column)
        display_names.setdefault(comparison_key, comparison_name)
    if not grouped:
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
    return {
        "block_type": "deg_comparisons",
        "comparison_count": len(comparisons),
        "complete_comparison_count": sum(1 for comparison in comparisons if comparison["is_complete"]),
        "comparisons": comparisons,
    }


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
    return _is_gene_annotation_column(normalized) or _parse_deg_column(normalized, normalized) is not None or _is_annotation_header([normalized])


def _is_geo_soft_path(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(".soft") or name.endswith(".soft.gz")


def _is_geo_series_matrix_path(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith("_series_matrix.txt") or name.endswith("_series_matrix.txt.gz") or bool(re.search(r"gse\d+.*gpl\d+.*series_matrix\.txt(?:\.gz)?$", name))


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


def _looks_like_sample_column(value: str) -> bool:
    normalized = _normalize_header(value)
    if not normalized:
        return False
    if normalized.startswith(("gsm", "srr", "err", "drr", "tcga")):
        return True
    if any(token in normalized for token in ("sample", "count", "counts", "tpm", "fpkm")):
        return True
    return re.fullmatch(r"[a-z]{0,3}\d+[a-z]?(?:_\d+)?", normalized) is not None


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
    has_logfc = any(header in {"logfc", "log2fc", "log2foldchange", "log2_fold_change", "log_fold_change"} or "logfc" in header or "log2foldchange" in header for header in headers)
    has_p = any(header in {"p", "pvalue", "p_value", "p_val", "p_val_adj", "p_value_adj"} or header.startswith("p_") or header.endswith("_pvalue") for header in headers)
    has_adj = any(header in {"adj_p_val", "adj_p_value", "padj", "fdr", "qvalue", "q_value", "false_discovery_rate"} or header.endswith(("_padj", "_fdr", "_qvalue")) for header in headers)
    has_stat = any(header in {"stat", "statistic", "t", "b", "wald_stat"} for header in headers)
    return has_logfc and has_p and (has_adj or has_stat)


def _is_sample_metadata_header(headers: list[str]) -> bool:
    has_sample = any(header in {"sample", "sample_id", "sampleid", "gsm", "geo_accession"} or "sample" in header for header in headers)
    has_attribute = any(any(token in header for token in ("group", "condition", "tissue", "disease", "case", "control", "treatment", "phenotype")) for header in headers)
    return has_sample and has_attribute


def _is_clinical_header(headers: list[str]) -> bool:
    clinical_tokens = ("age", "sex", "gender", "stage", "grade", "status", "vital", "death", "survival", "days", "months")
    return sum(1 for header in headers if any(token in header for token in clinical_tokens)) >= 2


def _is_survival_header(headers: list[str]) -> bool:
    has_time = any(any(token in header for token in ("time", "days", "months", "os", "dfs", "pfs", "survival")) for header in headers)
    has_status = any(any(token in header for token in ("status", "vital", "death", "event")) for header in headers)
    return has_time and has_status


def _is_annotation_header(headers: list[str]) -> bool:
    annotation_tokens = ("probe", "id_ref", "gene_symbol", "symbol", "gene_assignment", "entrez", "ensembl", "chromosome", "chr", "description", "biotype")
    return any(any(token in header for token in annotation_tokens) for header in headers)


def _tabular_role_reason(role: str) -> str:
    return {
        "clinical_metadata": "表头包含 age/sex/stage/grade/status 等临床字段。",
        "survival_metadata": "表头同时包含生存时间和状态字段。",
        "platform_annotation": "表头包含 probe/ID_REF/gene_symbol/ENTREZ/ENSEMBL/chromosome 等平台注释字段。",
        "gene_annotation": "表头包含 gene_symbol/ENTREZ/ENSEMBL/chromosome 等基因注释字段。",
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
    if _is_system_path(relative):
        return False
    parts = relative.parts
    if len(parts) >= 3 and parts[0] == "raw_data" and parts[1] == "geo" and parts[2] == "organized":
        return False
    return True


def _is_system_file_name(name: str) -> bool:
    return name == ".DS_Store" or name == "__MACOSX" or name.startswith("._")


def _is_system_path(path: Path) -> bool:
    return any(_is_system_file_name(part) for part in path.parts)


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
                if candidate.is_file() and _is_recognition_candidate_file(candidate, root):
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


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
