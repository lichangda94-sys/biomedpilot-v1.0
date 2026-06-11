from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.analysis_runtime.task_bridge import run_analysis_module_task

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
    standard_result_package_dir: str
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
    run_id = _run_id()
    bridge_input_dir = root / "analysis" / "immune_infiltration" / "runs" / run_id / "task_bridge_inputs"
    bridge_expression_path = bridge_input_dir / "expression_matrix.tsv"
    bridge_signature_path = bridge_input_dir / "signature_table.tsv"
    _write_task_bridge_expression_matrix(
        bridge_expression_path,
        rows,
        gene_col=resolved_gene_col,
        sample_columns=resolved_sample_cols,
        transform=transform,
        warnings=warnings,
    )
    _write_task_bridge_signature_table(bridge_signature_path, signatures)
    package_dir = root / "analysis" / "standard_packages" / run_id
    bridge_result = run_analysis_module_task(
        root,
        {
            "schema_version": "biomedpilot.analysis.module_input.v1",
            "module_id": "immune_infiltration",
            "mode": "lite",
            "task_id": run_id,
            "project_id": dataset_id or root.name,
            "inputs": {
                "input_package_id": dataset_id,
                "source_dataset_id": dataset_id,
                "expression_matrix_path": str(bridge_expression_path),
                "signature_table_path": str(bridge_signature_path),
            },
            "parameters": {
                "analysis_family": "immune_infiltration",
                "method": "base_r_signature_mean_fixture",
                "scoring_method": method,
                "value_transform": transform,
                "input_value_type": policy.get("value_type") or input_value_type,
                "signature_count": len(signatures),
                "clinical_conclusion_policy": "not_generated",
            },
            "runtime": {"random_seed": 7, "requested_environment": "r-bio-core-lite"},
        },
        output_dir=package_dir,
        worker_backend="rscript",
    )

    score_path = package_dir / "tables" / "immune_score_matrix.tsv"
    coverage_path = package_dir / "tables" / "signature_gene_coverage.tsv"
    sample_summary_path = package_dir / "tables" / "sample_score_summary.tsv"
    report_path = package_dir / "reports" / "README_lite.md"
    manifest_path = package_dir / "logs" / "immune_scoring_manifest.json"
    receipt_path = package_dir / "logs" / "immune_scoring_receipt.json"
    coverage_rows = _read_tsv_dicts(coverage_path)
    scored_count = sum(1 for row in coverage_rows if row.get("status") in {"ok", "single_gene_signature", "low_coverage_warning"})
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
        "gene_count": _bridge_gene_count(bridge_expression_path),
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
        "worker_backend": "rscript",
        "worker_boundary": "standard_r_worker",
        "task_system_invocation": "task_center_registered",
        "standard_result_package_dir": str(package_dir),
        "bridge_status": str(bridge_result.get("status") or ""),
        "bridge_blockers": list(bridge_result.get("blockers", []) or []),
        "blocked_downstream": ["DEG execution", "GSEA execution", "KM/Cox/log-rank", "report-ready clinical conclusion"],
    }
    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "status": "completed" if bridge_result.get("status") == "passed" else "blocked",
        "run_id": run_id,
        "message": "immune / TME signature scoring completed through the standard R worker lite path.",
        "signature_count": len(signatures),
        "scored_signature_count": scored_count,
        "sample_count": len(resolved_sample_cols),
        "gene_count": manifest["gene_count"],
        "warnings": manifest["warnings"],
        "blockers": manifest["bridge_blockers"],
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
    result_index_path = root / "results" / "summaries" / "result_index.json"
    return ImmuneScoringRunResult(
        status="completed" if bridge_result.get("status") == "passed" else "blocked",
        message="免疫浸润 / TME signature 评分已通过标准 R worker lite 路径完成（探索性 bulk score）。",
        run_id=run_id,
        scoring_method=method,
        value_transform=transform,
        score_matrix_path=str(score_path),
        coverage_path=str(coverage_path),
        sample_summary_path=str(sample_summary_path),
        manifest_path=str(manifest_path),
        receipt_path=str(receipt_path),
        report_path=str(report_path),
        standard_result_package_dir=str(package_dir),
        result_index_path=str(result_index_path),
        signature_count=len(signatures),
        scored_signature_count=scored_count,
        sample_count=len(resolved_sample_cols),
        gene_count=int(manifest["gene_count"]),
        warnings=list(manifest["warnings"]),
        limitations=limitations,
    )


def latest_immune_scoring_manifest_path(project_root: str | Path) -> Path | None:
    root = Path(project_root).expanduser().resolve()
    manifests = sorted((root / "analysis" / "immune_infiltration" / "runs").glob("*/immune_scoring_manifest.json"))
    return manifests[-1] if manifests else None



def _write_task_bridge_expression_matrix(
    path: Path,
    rows: list[dict[str, str]],
    *,
    gene_col: str,
    sample_columns: list[str],
    transform: str,
    warnings: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    invalid_values = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["gene", *sample_columns], delimiter="\t")
        writer.writeheader()
        for row in rows:
            gene = normalize_gene(row.get(gene_col, ""))
            if not gene:
                continue
            output_row: dict[str, Any] = {"gene": gene}
            for sample in sample_columns:
                value, ok = _to_float(row.get(sample, ""))
                if not ok:
                    invalid_values += 1
                output_row[sample] = _transform_value(value, transform)
            writer.writerow(output_row)
    if invalid_values:
        warnings.append(f"non_numeric_expression_values:{invalid_values}")


def _write_task_bridge_signature_table(path: Path, signatures: tuple[ImmuneSignature, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["signature", "gene"], delimiter="\t")
        writer.writeheader()
        for signature in signatures:
            for gene in signature.genes:
                normalized = normalize_gene(gene)
                if normalized:
                    writer.writerow({"signature": signature.signature_id, "gene": normalized})


def _read_tsv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter="\t")]


def _bridge_gene_count(path: Path) -> int:
    if not path.is_file():
        return 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return sum(1 for row in reader if str(row.get("gene") or "").strip())


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
