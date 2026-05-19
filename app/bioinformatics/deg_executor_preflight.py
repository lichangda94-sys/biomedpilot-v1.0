from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from app.bioinformatics.analysis_task_runs import load_analysis_task_run, list_analysis_task_runs, task_run_path
from app.bioinformatics.group_comparison_design import load_group_comparison_design
from app.bioinformatics.standardized_asset_selection import resolve_standardized_assets


DEG_EXECUTOR_PREFLIGHT_SCHEMA_VERSION = "bioinformatics_deg_executor_preflight.v1"
DEG_INPUTS_ROOT = Path("standardized_data") / "deg_inputs"


def run_deg_executor_preflight(project_root: str | Path, *, task_run_id: str | None = None) -> dict[str, object]:
    """Materialize and validate DEG executor inputs without running DEG statistics."""
    root = Path(project_root).expanduser().resolve()
    run = _load_target_run(root, task_run_id)
    if run is None:
        return _failed_payload(root, task_run_id or "", ["未找到 DEG 任务记录。请先生成 DEG 分析任务记录。"])

    run_id = str(run.get("run_id") or "")
    run_dir = task_run_path(root, "deg", run_id)
    input_dir = root / DEG_INPUTS_ROOT / run_id
    input_dir.mkdir(parents=True, exist_ok=True)

    warnings = ["当前只执行 DEG 输入校验，不执行真实差异表达分析。"]
    errors: list[str] = []
    count_asset = _source_count_asset(root, run)
    group_design = load_group_comparison_design(root) or {}
    comparisons = [item for item in run.get("comparisons", []) or [] if isinstance(item, dict)]
    if not comparisons:
        comparisons = [item for item in group_design.get("comparisons", []) or [] if isinstance(item, dict) and item.get("status") == "confirmed"]

    if not count_asset:
        errors.append("未找到当前 DEG 任务记录对应的 count matrix。")
    if not group_design:
        errors.append("未找到已确认的分组与比较设计。")
    if not comparisons:
        errors.append("未找到可校验的比较组。")

    materialized: dict[str, object] = {}
    if count_asset and group_design and comparisons:
        try:
            materialized = _materialize_inputs(root, input_dir, count_asset, group_design, comparisons)
            warnings.extend(str(item) for item in materialized.get("warnings", []) or [] if str(item))
            errors.extend(str(item) for item in materialized.get("errors", []) or [] if str(item))
        except Exception as exc:  # pragma: no cover - defensive guard for UI-triggered preflight.
            errors.append(f"DEG 输入物化失败：{exc}")

    status = "failed" if errors else "passed_with_warnings" if warnings else "passed"
    payload = {
        "schema_version": DEG_EXECUTOR_PREFLIGHT_SCHEMA_VERSION,
        "project_root": str(root),
        "run_id": run_id,
        "status": status,
        "execution_level": "preflight_only",
        "not_run": True,
        "count_asset_id": count_asset.get("asset_id", "") if count_asset else "",
        "source_task_run_path": str(run_dir / "task_run.json"),
        "input_dir": str(input_dir),
        "count_matrix_path": materialized.get("count_matrix_path", ""),
        "sample_design_path": materialized.get("sample_design_path", ""),
        "comparison_design_path": materialized.get("comparison_design_path", ""),
        "checks": materialized.get("checks", []),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "generated_at": _now(),
    }
    preflight_path = run_dir / "executor_preflight.json"
    _atomic_write_json(preflight_path, payload)
    _update_run_with_preflight(root, run, payload, preflight_path)
    return payload


def _load_target_run(root: Path, task_run_id: str | None) -> dict[str, object] | None:
    if task_run_id:
        return load_analysis_task_run(root, "deg", task_run_id)
    runs = list_analysis_task_runs(root, task_family="deg")
    return runs[0] if runs else None


def _source_count_asset(root: Path, run: dict[str, object]) -> dict[str, object]:
    source_assets = [item for item in run.get("source_assets", []) or [] if isinstance(item, dict)]
    source_asset_id = str(source_assets[0].get("asset_id") or "") if source_assets else ""
    resolved = resolve_standardized_assets(root, asset_types={"count_matrix"})
    assets = [item for item in resolved.get("assets", []) or [] if isinstance(item, dict)]
    if source_asset_id:
        for asset in assets:
            if str(asset.get("asset_id") or "") == source_asset_id:
                return asset
    return assets[0] if assets else {}


def _materialize_inputs(
    root: Path,
    input_dir: Path,
    count_asset: dict[str, object],
    group_design: dict[str, object],
    comparisons: list[dict[str, object]],
) -> dict[str, object]:
    source_file = _asset_source_path(root, count_asset)
    rows = _read_table_rows(source_file)
    warnings: list[str] = []
    errors: list[str] = []
    if not rows:
        return {"warnings": warnings, "errors": [f"无法读取 count matrix 来源表格：{source_file}"], "checks": []}

    header = [str(item) for item in rows[0]]
    body = rows[1:]
    sample_columns = [str(item) for item in count_asset.get("sample_columns", []) or [] if str(item)]
    if not sample_columns:
        sample_columns = _infer_sample_columns(header)
        warnings.append("count asset 未记录 sample_columns，已按列名规则临时推断。")
    missing_columns = [column for column in sample_columns if column not in header]
    if missing_columns:
        errors.append(f"count matrix 缺少样本列：{', '.join(missing_columns)}")

    gene_column = _gene_id_column(header, count_asset)
    if gene_column not in header:
        errors.append("count matrix 缺少 gene_id 列。")

    sample_ids = [str(item) for item in count_asset.get("inferred_sample_ids", []) or [] if str(item)]
    if len(sample_ids) != len(sample_columns):
        sample_ids = sample_columns
        warnings.append("sample id 与 count 列数量不一致，已临时使用列名作为 sample id。")

    sample_to_group = _sample_to_group(group_design)
    sample_design_rows = []
    for sample_id, column in zip(sample_ids, sample_columns, strict=False):
        group = sample_to_group.get(sample_id) or sample_to_group.get(column) or _group_from_column(column, group_design)
        if not group:
            warnings.append(f"样本未匹配到已确认分组：{sample_id}")
        sample_design_rows.append({"sample_id": sample_id, "source_column": column, "group": group or "未确认"})

    column_index = {column: index for index, column in enumerate(header)}
    matrix_rows: list[list[str]] = [["gene_id", *sample_ids]]
    seen_gene_ids: set[str] = set()
    duplicate_gene_ids = 0
    invalid_count_values = 0
    missing_values = 0
    for raw in body:
        gene_id = _cell(raw, column_index.get(gene_column))
        if not gene_id:
            missing_values += 1
            continue
        if gene_id in seen_gene_ids:
            duplicate_gene_ids += 1
        seen_gene_ids.add(gene_id)
        output_row = [gene_id]
        for column in sample_columns:
            value = _cell(raw, column_index.get(column))
            if value == "":
                missing_values += 1
            elif not _is_non_negative_integer(value):
                invalid_count_values += 1
            output_row.append(value)
        matrix_rows.append(output_row)

    if duplicate_gene_ids:
        warnings.append(f"检测到重复 gene_id：{duplicate_gene_ids} 个。")
    if missing_values:
        warnings.append(f"检测到空值或缺失 gene_id/count：{missing_values} 处。")
    if invalid_count_values:
        errors.append(f"count matrix 存在非非负整数值：{invalid_count_values} 处。")

    count_path = input_dir / "count_matrix.tsv"
    sample_design_path = input_dir / "sample_design.tsv"
    comparison_path = input_dir / "comparisons.tsv"
    _write_tsv(count_path, matrix_rows)
    _write_dict_tsv(sample_design_path, ["sample_id", "source_column", "group"], sample_design_rows)
    _write_dict_tsv(
        comparison_path,
        ["comparison_name", "case_group", "control_group"],
        [
            {
                "comparison_name": str(item.get("comparison_name") or ""),
                "case_group": str(item.get("case_group") or ""),
                "control_group": str(item.get("control_group") or ""),
            }
            for item in comparisons
        ],
    )

    checks = [
        {"check_id": "count_matrix_readable", "status": "passed", "detail": str(source_file)},
        {"check_id": "sample_columns_present", "status": "failed" if missing_columns else "passed", "detail": ", ".join(missing_columns)},
        {"check_id": "gene_id_present", "status": "failed" if gene_column not in header else "passed", "detail": gene_column},
        {"check_id": "count_values_non_negative_integer", "status": "failed" if invalid_count_values else "passed", "detail": str(invalid_count_values)},
        {"check_id": "sample_design_materialized", "status": "passed", "detail": str(sample_design_path)},
        {"check_id": "comparison_design_materialized", "status": "passed", "detail": str(comparison_path)},
    ]
    return {
        "count_matrix_path": str(count_path),
        "sample_design_path": str(sample_design_path),
        "comparison_design_path": str(comparison_path),
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
        "checksums": {
            "count_matrix_sha256": _sha256(count_path),
            "sample_design_sha256": _sha256(sample_design_path),
            "comparison_design_sha256": _sha256(comparison_path),
        },
    }


def _update_run_with_preflight(root: Path, run: dict[str, object], payload: dict[str, object], preflight_path: Path) -> None:
    run_id = str(run.get("run_id") or "")
    run_dir = task_run_path(root, "deg", run_id)
    task_run_payload = {key: value for key, value in run.items() if key not in {"run_dir", "task_run_path"}}
    task_run_payload["deg_preflight_manifest"] = {
        "status": payload.get("status", ""),
        "path": _display_path(root, preflight_path),
        "input_dir": _display_path(root, Path(str(payload.get("input_dir") or ""))),
        "count_matrix_path": _display_path(root, Path(str(payload.get("count_matrix_path") or ""))),
        "sample_design_path": _display_path(root, Path(str(payload.get("sample_design_path") or ""))),
        "comparison_design_path": _display_path(root, Path(str(payload.get("comparison_design_path") or ""))),
        "warnings": payload.get("warnings", []),
        "errors": payload.get("errors", []),
    }
    task_run_payload["updated_at"] = _now()
    _atomic_write_json(run_dir / "task_run.json", task_run_payload)
    _atomic_write_json(
        run_dir / "inputs.json",
        {
            "schema_version": "bioinformatics_analysis_task_run_inputs.v1",
            "source_task_plan": task_run_payload.get("source_task_plan", ""),
            "source_group_design": task_run_payload.get("source_group_design", ""),
            "source_assets": task_run_payload.get("source_assets", []),
            "deg_executor_preflight": task_run_payload["deg_preflight_manifest"],
        },
    )
    _atomic_write_json(run_dir / "warnings.json", {"warnings": payload.get("warnings", []), "errors": payload.get("errors", [])})


def _asset_source_path(root: Path, asset: dict[str, object]) -> Path:
    for key in ("source_file", "file_path"):
        raw = str(asset.get(key) or "")
        if not raw:
            continue
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = root / path
        if path.is_file():
            return path
    return root / str(asset.get("source_file") or asset.get("file_path") or "")


def _read_table_rows(path: Path) -> list[list[str]]:
    if not path.is_file():
        return []
    delimiter = "\t" if path.suffix.lower() in {".tsv", ".txt"} else ","
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [[str(cell) for cell in row] for row in csv.reader(handle, delimiter=delimiter)]


def _infer_sample_columns(header: list[str]) -> list[str]:
    excluded = {"gene_id", "gene", "gene_name", "gene_symbol", "gene_biotype", "gene_description"}
    return [
        column
        for column in header
        if column.lower() not in excluded
        and not column.lower().endswith(("log2foldchange", "logfc", "pvalue", "p_value", "padj", "fdr", "qvalue"))
    ]


def _gene_id_column(header: list[str], asset: dict[str, object]) -> str:
    columns = [str(item) for item in asset.get("gene_id_columns", []) or [] if str(item)]
    for column in columns:
        if column in header:
            return column
    for candidate in ("gene_id", "GeneID", "Gene", "ID", "id"):
        if candidate in header:
            return candidate
    return columns[0] if columns else "gene_id"


def _sample_to_group(group_design: dict[str, object]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for group in group_design.get("sample_groups", []) or []:
        if not isinstance(group, dict):
            continue
        group_name = str(group.get("user_group_name") or group.get("inferred_group_id") or "")
        for sample_id in group.get("sample_ids", []) or []:
            mapping[str(sample_id)] = group_name
        for source_column in group.get("source_columns", []) or []:
            mapping[str(source_column)] = group_name
    return mapping


def _group_from_column(column: str, group_design: dict[str, object]) -> str:
    for group in group_design.get("sample_groups", []) or []:
        if not isinstance(group, dict):
            continue
        inferred = str(group.get("inferred_group_id") or "")
        if inferred and column.startswith(inferred):
            return str(group.get("user_group_name") or inferred)
    return ""


def _cell(row: list[str], index: int | None) -> str:
    if index is None or index < 0 or index >= len(row):
        return ""
    return str(row[index]).strip()


def _is_non_negative_integer(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    try:
        numeric = float(text)
    except ValueError:
        return False
    return numeric >= 0 and numeric.is_integer()


def _write_tsv(path: Path, rows: Iterable[Iterable[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, path)


def _write_dict_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    _write_tsv(path, [fieldnames, *[[row.get(field, "") for field in fieldnames] for row in rows]])


def _display_path(root: Path, path: Path) -> str:
    if not str(path):
        return ""
    try:
        return str(path.resolve().relative_to(root))
    except (OSError, ValueError):
        return str(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _failed_payload(root: Path, run_id: str, errors: list[str]) -> dict[str, object]:
    return {
        "schema_version": DEG_EXECUTOR_PREFLIGHT_SCHEMA_VERSION,
        "project_root": str(root),
        "run_id": run_id,
        "status": "failed",
        "execution_level": "preflight_only",
        "not_run": True,
        "warnings": ["当前只执行 DEG 输入校验，不执行真实差异表达分析。"],
        "errors": errors,
        "generated_at": _now(),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    with temp_path.open("w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, path)
