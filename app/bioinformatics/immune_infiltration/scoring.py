from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any
from uuid import uuid4

from app.bioinformatics.results.project_results import load_result_index, write_result_index

from .signature_models import ImmuneSignature, normalize_gene
from .signature_resources import load_builtin_signatures
from .validators import read_expression_matrix, value_type_policy


SCORING_SCHEMA_VERSION = "biomedpilot.immune_tme_scoring_manifest.v1"
RECEIPT_SCHEMA_VERSION = "biomedpilot.immune_tme_scoring_receipt.v1"


@dataclass(frozen=True)
class ImmuneScoringRunResult:
    status: str
    message: str
    run_id: str
    scoring_method: str
    value_transform: str
    score_matrix_path: str
    coverage_path: str
    sample_summary_path: str
    manifest_path: str
    receipt_path: str
    report_path: str
    result_index_path: str
    signature_count: int
    scored_signature_count: int
    sample_count: int
    gene_count: int
    warnings: list[str]
    limitations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_immune_scoring(
    project_root: str | Path,
    *,
    expression_matrix_path: str | Path,
    selected_signatures: list[ImmuneSignature] | tuple[ImmuneSignature, ...] | None = None,
    dataset_id: str = "",
    dataset_label: str = "",
    input_value_type: str = "unknown",
    gene_id_column: str | None = None,
    sample_columns: list[str] | tuple[str, ...] | None = None,
    scoring_method: str = "mean_zscore",
    value_transform: str = "none",
    run_config: dict[str, Any] | None = None,
) -> ImmuneScoringRunResult:
    root = Path(project_root).expanduser().resolve()
    matrix_path = Path(expression_matrix_path).expanduser().resolve()
    if not matrix_path.is_file():
        raise FileNotFoundError(f"表达矩阵不存在：{matrix_path}")
    method = _validate_method(scoring_method)
    transform = _validate_transform(value_transform)
    policy = value_type_policy(input_value_type)
    if not policy.get("can_run") and not bool((run_config or {}).get("allow_blocked_value_type")):
        raise ValueError(f"当前 value type 不适合 B7 评分：{policy.get('value_type') or input_value_type}")

    signatures = tuple(selected_signatures or load_builtin_signatures())
    if not signatures:
        raise ValueError("未选择 immune / TME signature。")

    rows, resolved_gene_col, resolved_sample_cols = read_expression_matrix(matrix_path, gene_id_column=gene_id_column)
    if sample_columns:
        wanted = [str(item) for item in sample_columns if str(item) in resolved_sample_cols]
        if wanted:
            resolved_sample_cols = wanted
    if not rows:
        raise ValueError("表达矩阵没有可读取的 gene rows。")
    if not resolved_sample_cols:
        raise ValueError("表达矩阵没有可读取的 sample columns。")

    warnings: list[str] = []
    expression = _expression_by_gene(rows, resolved_gene_col, resolved_sample_cols, transform, warnings)
    score_rows, coverage_rows = _score_signatures(
        expression_by_gene=expression,
        sample_columns=resolved_sample_cols,
        signatures=signatures,
        method=method,
        warnings=warnings,
    )

    run_id = _run_id()
    run_dir = root / "analysis" / "immune_infiltration" / "runs" / run_id
    score_path = run_dir / "immune_score_matrix.tsv"
    coverage_path = run_dir / "signature_gene_coverage.tsv"
    sample_summary_path = run_dir / "sample_score_summary.tsv"
    manifest_path = run_dir / "immune_scoring_manifest.json"
    receipt_path = run_dir / "immune_scoring_receipt.json"
    report_path = run_dir / "immune_tme_scoring_report.md"

    _write_score_matrix(score_path, score_rows, resolved_sample_cols)
    _write_coverage(coverage_path, coverage_rows)
    _write_sample_summary(sample_summary_path, score_rows, resolved_sample_cols)
    scored_count = sum(1 for row in coverage_rows if row["status"] in {"ok", "single_gene_signature", "low_coverage_warning"})
    limitations = _limitations()
    generated_at = _now()
    manifest = {
        "schema_version": SCORING_SCHEMA_VERSION,
        "generated_at": generated_at,
        "run_id": run_id,
        "dataset_id": dataset_id,
        "dataset_label": dataset_label,
        "input_expression_matrix_path": str(matrix_path),
        "input_value_type": policy.get("value_type") or input_value_type,
        "value_type_policy": policy,
        "gene_id_column": resolved_gene_col,
        "sample_columns": resolved_sample_cols,
        "sample_count": len(resolved_sample_cols),
        "gene_count": len(expression),
        "scoring_method": method,
        "value_transform": transform,
        "signature_count": len(signatures),
        "scored_signature_count": scored_count,
        "score_matrix_path": str(score_path),
        "signature_gene_coverage_path": str(coverage_path),
        "sample_score_summary_path": str(sample_summary_path),
        "report_path": str(report_path),
        "warnings": list(dict.fromkeys(warnings)),
        "limitations": limitations,
        "execution_level": "testing-level exploratory signature scoring",
        "blocked_downstream": ["DEG execution", "GSEA execution", "KM/Cox/log-rank", "report-ready clinical conclusion"],
    }
    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "status": "completed",
        "run_id": run_id,
        "message": "immune / TME signature scoring completed as exploratory bulk scoring.",
        "signature_count": len(signatures),
        "scored_signature_count": scored_count,
        "sample_count": len(resolved_sample_cols),
        "gene_count": len(expression),
        "warnings": manifest["warnings"],
        "artifacts": {
            "score_matrix": str(score_path),
            "coverage": str(coverage_path),
            "sample_summary": str(sample_summary_path),
            "manifest": str(manifest_path),
            "report": str(report_path),
        },
    }
    _write_json(manifest_path, manifest)
    _write_json(receipt_path, receipt)
    result_index_path = _register_result(root, manifest, score_path)
    return ImmuneScoringRunResult(
        status="completed",
        message="免疫浸润 / TME signature 评分已完成（探索性 bulk score）。",
        run_id=run_id,
        scoring_method=method,
        value_transform=transform,
        score_matrix_path=str(score_path),
        coverage_path=str(coverage_path),
        sample_summary_path=str(sample_summary_path),
        manifest_path=str(manifest_path),
        receipt_path=str(receipt_path),
        report_path=str(report_path),
        result_index_path=str(result_index_path),
        signature_count=len(signatures),
        scored_signature_count=scored_count,
        sample_count=len(resolved_sample_cols),
        gene_count=len(expression),
        warnings=list(manifest["warnings"]),
        limitations=limitations,
    )


def latest_immune_scoring_manifest_path(project_root: str | Path) -> Path | None:
    root = Path(project_root).expanduser().resolve()
    manifests = sorted((root / "analysis" / "immune_infiltration" / "runs").glob("*/immune_scoring_manifest.json"))
    return manifests[-1] if manifests else None


def _score_signatures(
    *,
    expression_by_gene: dict[str, dict[str, float]],
    sample_columns: list[str],
    signatures: tuple[ImmuneSignature, ...],
    method: str,
    warnings: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    score_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []
    for signature in signatures:
        matched_genes = [normalize_gene(gene) for gene in signature.genes if normalize_gene(gene) in expression_by_gene]
        missing_genes = [gene for gene in signature.genes if normalize_gene(gene) not in expression_by_gene]
        requested = len(signature.genes)
        ratio = len(matched_genes) / requested if requested else 0.0
        status = _coverage_status(requested, len(matched_genes), ratio)
        if status == "failed_no_matched_genes":
            warnings.append(f"{signature.signature_id}: no matched genes")
        elif status == "low_coverage_warning":
            warnings.append(f"{signature.signature_id}: low gene coverage")
        coverage_rows.append(
            {
                "signature_id": signature.signature_id,
                "display_name": signature.display_name,
                "category": signature.category,
                "requested_gene_count": requested,
                "matched_gene_count": len(matched_genes),
                "missing_gene_count": len(missing_genes),
                "coverage_ratio": f"{ratio:.4f}",
                "matched_genes": ",".join(matched_genes),
                "missing_genes": ",".join(missing_genes),
                "status": status,
            }
        )
        score_row: dict[str, Any] = {
            "signature_id": signature.signature_id,
            "display_name": signature.display_name,
            "category": signature.category,
            "matched_gene_count": len(matched_genes),
            "coverage_status": status,
        }
        for sample in sample_columns:
            score_row[sample] = "" if not matched_genes else _sample_score(expression_by_gene, matched_genes, sample, method)
        score_rows.append(score_row)
    return score_rows, coverage_rows


def _sample_score(
    expression_by_gene: dict[str, dict[str, float]],
    matched_genes: list[str],
    sample: str,
    method: str,
) -> float:
    values = [expression_by_gene[gene].get(sample, 0.0) for gene in matched_genes]
    if not values:
        return float("nan")
    if method == "mean_expression":
        return round(mean(values), 6)
    z_values = []
    for gene in matched_genes:
        sample_values = list(expression_by_gene[gene].values())
        sd = pstdev(sample_values) if len(sample_values) > 1 else 0.0
        z_values.append(0.0 if sd == 0 else (expression_by_gene[gene].get(sample, 0.0) - mean(sample_values)) / sd)
    return round(mean(z_values), 6) if z_values else float("nan")


def _coverage_status(requested: int, matched: int, ratio: float) -> str:
    if requested == 0 or matched == 0:
        return "failed_no_matched_genes"
    if requested == 1:
        return "single_gene_signature"
    if matched < 3 or ratio < 0.2:
        return "low_coverage_warning"
    return "ok"


def _expression_by_gene(
    rows: list[dict[str, str]],
    gene_col: str,
    sample_columns: list[str],
    transform: str,
    warnings: list[str],
) -> dict[str, dict[str, float]]:
    values_by_gene: dict[str, dict[str, list[float]]] = {}
    invalid_values = 0
    for row in rows:
        gene = normalize_gene(row.get(gene_col, ""))
        if not gene:
            continue
        slot = values_by_gene.setdefault(gene, {sample: [] for sample in sample_columns})
        for sample in sample_columns:
            value, ok = _to_float(row.get(sample, ""))
            if not ok:
                invalid_values += 1
            slot[sample].append(_transform_value(value, transform))
    if invalid_values:
        warnings.append(f"non_numeric_expression_values:{invalid_values}")
    return {
        gene: {sample: round(mean(values), 6) if values else 0.0 for sample, values in sample_values.items()}
        for gene, sample_values in values_by_gene.items()
    }


def _to_float(value: object) -> tuple[float, bool]:
    text = str(value if value is not None else "").strip()
    if text in {"", "NA", "NaN", "nan", "null"}:
        return 0.0, False
    try:
        return float(text), True
    except ValueError:
        return 0.0, False


def _transform_value(value: float, transform: str) -> float:
    if transform == "log2_x_plus_1":
        return math.log2(max(value, 0.0) + 1.0)
    return value


def _write_score_matrix(path: Path, rows: list[dict[str, Any]], sample_columns: list[str]) -> None:
    fieldnames = ["signature_id", "display_name", "category", "matched_gene_count", "coverage_status", *sample_columns]
    _write_tsv(path, fieldnames, rows)


def _write_coverage(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "signature_id",
        "display_name",
        "category",
        "requested_gene_count",
        "matched_gene_count",
        "missing_gene_count",
        "coverage_ratio",
        "matched_genes",
        "missing_genes",
        "status",
    ]
    _write_tsv(path, fieldnames, rows)


def _write_sample_summary(path: Path, rows: list[dict[str, Any]], sample_columns: list[str]) -> None:
    summary_rows = []
    for sample in sample_columns:
        values = [float(row[sample]) for row in rows if str(row.get(sample, "")).strip()]
        summary_rows.append(
            {
                "sample_id": sample,
                "scored_signature_count": len(values),
                "mean_score": round(mean(values), 6) if values else "",
                "min_score": round(min(values), 6) if values else "",
                "max_score": round(max(values), 6) if values else "",
            }
        )
    _write_tsv(path, ["sample_id", "scored_signature_count", "mean_score", "min_score", "max_score"], summary_rows)


def _write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _register_result(root: Path, manifest: dict[str, Any], score_path: Path) -> Path:
    result_index = load_result_index(root)
    entries = [item for item in result_index.get("entries", []) if isinstance(item, dict)]
    run_id = str(manifest.get("run_id") or "")
    entries = [item for item in entries if item.get("result_id") != run_id]
    entries.append(
        {
            "result_id": run_id,
            "result_name": "免疫浸润 / TME signature score",
            "result_type": "探索性 bulk signature score",
            "analysis_type": "immune_tme_scoring",
            "label": "免疫浸润 / TME评分",
            "path": str(score_path),
            "manifest_path": str(Path(str(score_path)).with_name("immune_scoring_manifest.json")),
            "created_at": manifest.get("generated_at"),
            "status": "completed",
            "result_semantics": "testing-level exploratory score",
            "report_candidate": True,
            "short_description": "基于 bulk 表达矩阵的 immune / TME signature score，不等同于真实免疫细胞比例。",
            "warning": "Bulk signature score 不等同于真实免疫细胞比例；不可作为临床结论。",
        }
    )
    return write_result_index(root, entries)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _validate_method(method: str) -> str:
    normalized = str(method or "").strip()
    if normalized not in {"mean_zscore", "mean_expression"}:
        raise ValueError(f"不支持的 scoring method：{method}")
    return normalized


def _validate_transform(transform: str) -> str:
    normalized = str(transform or "").strip()
    if normalized not in {"none", "log2_x_plus_1"}:
        raise ValueError(f"不支持的 value transform：{transform}")
    return normalized


def _limitations() -> list[str]:
    return [
        "本模块计算的是基于 bulk 表达矩阵的探索性 immune / TME signature score，不等同于真实免疫细胞比例。",
        "B7 不执行 CIBERSORT/xCell/ESTIMATE，也不生成临床结论。",
        "raw counts 默认不能直接评分；推荐 TPM 或已经标准化的表达矩阵。",
        "当前结果只进入 exploratory preview 和后续 preflight，不自动执行 DEG/GSEA/KM/Cox/log-rank。",
    ]


def _run_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d")
    return f"immune_score_{stamp}_{uuid4().hex[:8]}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


__all__ = ["ImmuneScoringRunResult", "latest_immune_scoring_manifest_path", "run_immune_scoring"]
