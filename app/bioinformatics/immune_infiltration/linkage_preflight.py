from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from app.bioinformatics.comparison_config import load_confirmed_comparison_config
from app.bioinformatics.data_sources.tcga_clinical_builder import latest_tcga_clinical_build_manifest_path

from .signature_models import normalize_gene
from .validators import read_expression_matrix


def build_linkage_preflight(
    project_root: str | Path,
    *,
    score_matrix_path: str | Path | None = None,
    expression_matrix_path: str | Path | None = None,
    target_gene: str = "",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    score_samples = _score_samples(score_matrix_path)
    group = _group_comparison_preflight(root, score_samples)
    correlation = _target_gene_correlation_preflight(expression_matrix_path, target_gene, score_samples)
    clinical = _clinical_preflight(root, score_samples)
    return {
        "schema_version": "biomedpilot.immune_tme_linkage_preflight.v1",
        "score_sample_count": len(score_samples),
        "group_comparison": group,
        "target_gene_correlation": correlation,
        "clinical_association": clinical,
        "not_supported_in_b7": ["KM", "Cox", "log-rank", "survival plot", "clinical conclusion"],
        "limitations": [
            "B7 只提供 immune / TME score 与分组、基因表达、clinical metadata 的后续配置 preflight。",
            "B7 不执行 KM/Cox/log-rank，也不生成生存分析图或临床结论。",
        ],
    }


def _group_comparison_preflight(root: Path, score_samples: set[str]) -> dict[str, Any]:
    config = load_confirmed_comparison_config(root)
    if config is None:
        return {"status": "not_configured", "ready": False, "message": "尚未确认分组。"}
    assignments = config.group_assignments
    matched = sorted(sample for sample in score_samples if sample in assignments)
    sizes: dict[str, int] = {}
    for sample in matched:
        group = assignments.get(sample, "")
        if group:
            sizes[group] = sizes.get(group, 0) + 1
    ready = len(sizes) >= 2 and all(count >= 1 for count in sizes.values())
    return {
        "status": "ready" if ready else "sample_mismatch_or_single_group",
        "ready": ready,
        "matched_sample_count": len(matched),
        "group_sizes": dict(sorted(sizes.items())),
        "message": "可进入 score group comparison preflight。" if ready else "评分样本与分组配置未形成至少两组。",
    }


def _target_gene_correlation_preflight(
    expression_matrix_path: str | Path | None,
    target_gene: str,
    score_samples: set[str],
) -> dict[str, Any]:
    gene = normalize_gene(target_gene)
    if not gene:
        return {"status": "target_gene_missing", "ready": False, "message": "尚未设置 target gene。"}
    path = Path(expression_matrix_path).expanduser().resolve() if expression_matrix_path else None
    if path is None or not path.is_file():
        return {"status": "expression_matrix_missing", "ready": False, "target_gene": gene}
    rows, gene_col, sample_columns = read_expression_matrix(path)
    matrix_genes = {normalize_gene(row.get(gene_col, "")) for row in rows}
    matched_samples = sorted(set(sample_columns) & score_samples)
    ready = gene in matrix_genes and len(matched_samples) >= 3
    return {
        "status": "ready" if ready else ("target_gene_not_found" if gene not in matrix_genes else "sample_count_too_low"),
        "ready": ready,
        "target_gene": gene,
        "matched_sample_count": len(matched_samples),
        "message": "可进入 target gene correlation preflight。" if ready else "target gene 或可匹配样本不足。",
    }


def _clinical_preflight(root: Path, score_samples: set[str]) -> dict[str, Any]:
    manifest_path = latest_tcga_clinical_build_manifest_path(root)
    if manifest_path is None:
        return {"status": "clinical_unavailable", "ready": False, "message": "未发现 TCGA clinical build manifest。"}
    manifest = _read_json(manifest_path)
    mapping_path = Path(str(manifest.get("mapping_table_path") or ""))
    survival_path = Path(str(manifest.get("survival_table_path") or ""))
    mapped_samples = _mapped_samples(mapping_path)
    survival_cases = _survival_cases(survival_path)
    matched_samples = sorted(score_samples & mapped_samples)
    ready = bool(matched_samples) and bool(survival_cases)
    return {
        "status": "ready" if ready else "clinical_partial",
        "ready": ready,
        "clinical_manifest_path": str(manifest_path),
        "matched_sample_count": len(matched_samples),
        "survival_case_count": len(survival_cases),
        "message": "可进入 clinical association / basic OS preflight；B7 不执行生存分析。" if ready else "clinical 映射或基础 OS 字段不足。",
    }


def _score_samples(score_matrix_path: str | Path | None) -> set[str]:
    if not score_matrix_path:
        return set()
    path = Path(score_matrix_path).expanduser().resolve()
    if not path.is_file():
        return set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader, [])
    return {col for col in header[5:] if col}


def _mapped_samples(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    samples = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            sample = str(row.get("sample_barcode") or row.get("sample_submitter_id") or "").strip()
            if sample and str(row.get("has_clinical") or "").lower() in {"true", "1", "yes"}:
                samples.add(sample)
    return samples


def _survival_cases(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    cases = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            case = str(row.get("case_id") or row.get("case_submitter_id") or "").strip()
            if case and str(row.get("OS_time") or "").strip() and str(row.get("OS_event") or "").strip():
                cases.add(case)
    return cases


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


__all__ = ["build_linkage_preflight"]
