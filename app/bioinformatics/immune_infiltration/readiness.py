from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.bioinformatics.comparison_config import load_confirmed_comparison_config
from app.bioinformatics.data_sources.gtex_expression_builder import latest_gtex_expression_build_manifest_path
from app.bioinformatics.data_sources.tcga_clinical_builder import latest_tcga_clinical_build_manifest_path, latest_tcga_expression_build_manifest_path
from app.bioinformatics.project_standardization import load_standardization_artifacts

from .signature_models import ImmuneSignature, normalize_gene
from .signature_resources import load_builtin_signatures
from .validators import matrix_profile, normalize_value_type, value_type_policy


@dataclass(frozen=True)
class ImmuneScoringInputDataset:
    dataset_id: str
    label: str
    source: str
    expression_matrix_path: str
    value_type: str
    gene_id_column: str
    gene_id_type: str
    sample_columns: tuple[str, ...]
    gene_count: int
    sample_count: int
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["sample_columns"] = list(self.sample_columns)
        return payload


def list_immune_scoring_input_datasets(project_root: str | Path) -> list[ImmuneScoringInputDataset]:
    root = Path(project_root).expanduser().resolve()
    datasets: list[ImmuneScoringInputDataset] = []
    datasets.extend(_tcga_datasets(root))
    datasets.extend(_gtex_datasets(root))
    datasets.extend(_standardized_or_recognition_datasets(root))
    deduped: dict[str, ImmuneScoringInputDataset] = {}
    for dataset in datasets:
        deduped.setdefault(dataset.dataset_id, dataset)
    return list(deduped.values())


def build_immune_infiltration_readiness(
    project_root: str | Path,
    *,
    dataset_id: str | None = None,
    signatures: list[ImmuneSignature] | tuple[ImmuneSignature, ...] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    datasets = list_immune_scoring_input_datasets(root)
    selected = _select_dataset(datasets, dataset_id)
    selected_signatures = tuple(signatures or load_builtin_signatures())
    blockers: list[str] = []
    warnings: list[str] = []
    if selected is None:
        blockers.append("expression_matrix_missing")
        return {
            "schema_version": "biomedpilot.immune_infiltration_readiness.v1",
            "status": "blocked",
            "blockers": blockers,
            "warnings": warnings,
            "input_summary": {},
            "available_datasets": [dataset.to_dict() for dataset in datasets],
            "value_type_policy": {},
            "signature_coverage_preview": [],
            "can_run_scoring": False,
            "can_run_group_comparison": False,
            "can_run_gene_correlation": False,
            "can_link_clinical": False,
            "tcga_gtex_boundary": "TCGA + GTEx 不自动合并；GTEx 不自动作为 TCGA normal control。",
        }
    policy = value_type_policy(selected.value_type)
    if not policy.get("can_run"):
        blockers.append(f"value_type_blocked:{policy.get('value_type')}")
    if not selected.gene_id_column:
        blockers.append("gene_identifier_column_missing")
    if not selected.sample_columns:
        blockers.append("sample_columns_missing")
    if selected.sample_count < 1:
        blockers.append("sample_columns_missing")
    elif selected.sample_count < 2:
        warnings.append("sample_count_below_recommended_2")
    if selected.gene_count < 1:
        blockers.append("gene_rows_missing")
    elif selected.gene_count < 10:
        warnings.append("gene_count_below_recommended_10")
    if selected.gene_id_type not in {"symbol", "ensembl"}:
        warnings.append(f"gene_id_type_may_need_mapping:{selected.gene_id_type}")
    coverage = _coverage_preview(selected, selected_signatures)
    if not selected_signatures:
        blockers.append("selected_signatures_missing")
    if selected_signatures and not any(int(item.get("matched_gene_count") or 0) > 0 for item in coverage):
        blockers.append("selected_signatures_have_no_gene_coverage")
    if selected.source == "gtex":
        warnings.append("GTEx 不自动作为 TCGA normal control；TCGA+GTEx 需要显式联合配置和批次校正。")
    comparison = load_confirmed_comparison_config(root)
    clinical_manifest = latest_tcga_clinical_build_manifest_path(root) if selected.source == "tcga" else None
    status = "blocked" if blockers else ("warning" if warnings or str(policy.get("status")) == "usable" else "ready")
    return {
        "schema_version": "biomedpilot.immune_infiltration_readiness.v1",
        "status": status,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
        "input_summary": selected.to_dict(),
        "available_datasets": [dataset.to_dict() for dataset in datasets],
        "value_type_policy": policy,
        "signature_coverage_preview": coverage,
        "can_run_scoring": not blockers,
        "can_run_group_comparison": not blockers and comparison is not None,
        "can_run_gene_correlation": not blockers,
        "can_link_clinical": not blockers and clinical_manifest is not None,
        "clinical_manifest_path": str(clinical_manifest or ""),
        "tcga_gtex_boundary": "TCGA + GTEx 不自动合并；GTEx 不自动作为 TCGA normal control。",
        "limitations": [_limitations_text()],
    }


def _tcga_datasets(root: Path) -> list[ImmuneScoringInputDataset]:
    manifest_path = latest_tcga_expression_build_manifest_path(root)
    if manifest_path is None:
        return []
    manifest = _read_json(manifest_path)
    metric_paths = manifest.get("metric_matrix_paths") if isinstance(manifest.get("metric_matrix_paths"), dict) else {}
    datasets = []
    for metric, value_type in (("tpm", "TPM"), ("fpkm", "FPKM"), ("fpkm_uq", "FPKM-UQ"), ("raw_counts", "raw_counts")):
        path = Path(str(metric_paths.get(metric) or ""))
        if not path.is_file():
            continue
        profile = matrix_profile(path)
        datasets.append(
            ImmuneScoringInputDataset(
                dataset_id=f"tcga:{manifest.get('project_id') or 'project'}:{metric}",
                label=f"TCGA {manifest.get('project_id') or ''} {value_type}",
                source="tcga",
                expression_matrix_path=str(path),
                value_type=value_type,
                gene_id_column=str(profile.get("gene_id_column") or "gene_id"),
                gene_id_type=str(profile.get("gene_id_type") or "ensembl"),
                sample_columns=tuple(str(item) for item in profile.get("sample_columns", []) or []),
                gene_count=int(profile.get("gene_count") or 0),
                sample_count=int(profile.get("sample_count") or 0),
                metadata={"build_manifest_path": str(manifest_path), "project_id": manifest.get("project_id") or ""},
            )
        )
    return datasets


def _gtex_datasets(root: Path) -> list[ImmuneScoringInputDataset]:
    manifest_path = latest_gtex_expression_build_manifest_path(root)
    if manifest_path is None:
        return []
    manifest = _read_json(manifest_path)
    path = Path(str(manifest.get("expression_matrix_path") or ""))
    if not path.is_file():
        return []
    profile = matrix_profile(path)
    return [
        ImmuneScoringInputDataset(
            dataset_id=f"gtex:{manifest.get('tissue_id') or 'tissue'}:TPM",
            label=f"GTEx {manifest.get('tissue_site_detail') or manifest.get('tissue_id') or ''} TPM",
            source="gtex",
            expression_matrix_path=str(path),
            value_type="TPM",
            gene_id_column=str(profile.get("gene_id_column") or "gene_id"),
            gene_id_type=str(profile.get("gene_id_type") or "symbol"),
            sample_columns=tuple(str(item) for item in profile.get("sample_columns", []) or []),
            gene_count=int(profile.get("gene_count") or 0),
            sample_count=int(profile.get("sample_count") or 0),
            metadata={"build_manifest_path": str(manifest_path), "tissue_id": manifest.get("tissue_id") or ""},
        )
    ]


def _standardized_or_recognition_datasets(root: Path) -> list[ImmuneScoringInputDataset]:
    artifacts = load_standardization_artifacts(root)
    registry = artifacts.get("registry") if isinstance(artifacts.get("registry"), dict) else {}
    assets = [item for item in registry.get("assets", []) or [] if isinstance(item, dict)] if isinstance(registry, dict) else []
    datasets = []
    for asset in assets:
        asset_type = str(asset.get("asset_type") or "")
        if asset_type not in {"expression_matrix", "normalized_expression_matrix", "gtex_expression_matrix", "tcga_expression_matrix", "raw_count_matrix"}:
            continue
        path = Path(str(asset.get("file_path") or asset.get("path") or ""))
        if not path.is_file():
            continue
        profile = matrix_profile(path)
        value_type = normalize_value_type(asset.get("expression_value_type"), asset_type=asset_type)
        datasets.append(
            ImmuneScoringInputDataset(
                dataset_id=f"asset:{asset.get('asset_id') or path.stem}",
                label=str(asset.get("label_zh") or path.name),
                source="standardized_asset",
                expression_matrix_path=str(path),
                value_type=value_type,
                gene_id_column=str(profile.get("gene_id_column") or "gene_id"),
                gene_id_type=str(asset.get("gene_id_type") or profile.get("gene_id_type") or "unknown"),
                sample_columns=tuple(str(item) for item in profile.get("sample_columns", []) or []),
                gene_count=int(profile.get("gene_count") or 0),
                sample_count=int(profile.get("sample_count") or 0),
                metadata={"asset_id": asset.get("asset_id") or "", "asset_type": asset_type},
            )
        )
    return datasets


def _select_dataset(datasets: list[ImmuneScoringInputDataset], dataset_id: str | None) -> ImmuneScoringInputDataset | None:
    if dataset_id:
        return next((dataset for dataset in datasets if dataset.dataset_id == dataset_id), None)
    runnable = [dataset for dataset in datasets if value_type_policy(dataset.value_type).get("can_run")]
    return runnable[0] if runnable else (datasets[0] if datasets else None)


def _coverage_preview(dataset: ImmuneScoringInputDataset, signatures: tuple[ImmuneSignature, ...]) -> list[dict[str, Any]]:
    genes = _matrix_genes(dataset.expression_matrix_path, dataset.gene_id_column)
    normalized_genes = {normalize_gene(gene) for gene in genes}
    rows = []
    for signature in signatures:
        matched = [gene for gene in signature.genes if normalize_gene(gene) in normalized_genes]
        missing = [gene for gene in signature.genes if normalize_gene(gene) not in normalized_genes]
        requested = len(signature.genes)
        rows.append(
            {
                "signature_id": signature.signature_id,
                "display_name": signature.display_name,
                "category": signature.category,
                "requested_gene_count": requested,
                "matched_gene_count": len(matched),
                "missing_gene_count": len(missing),
                "coverage_ratio": round(len(matched) / requested, 4) if requested else 0.0,
                "status": "single_gene_signature" if requested == 1 and matched else ("ok" if matched else "failed_no_matched_genes"),
            }
        )
    return rows


def _matrix_genes(path: str, gene_col: str) -> list[str]:
    from .validators import read_expression_matrix

    rows, resolved_gene_col, _ = read_expression_matrix(path, gene_id_column=gene_col)
    return [str(row.get(resolved_gene_col) or "").strip() for row in rows if str(row.get(resolved_gene_col) or "").strip()]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _limitations_text() -> str:
    return "本模块计算的是基于 bulk 表达矩阵的探索性 immune / TME signature score，不等同于真实免疫细胞比例。"


__all__ = ["ImmuneScoringInputDataset", "build_immune_infiltration_readiness", "list_immune_scoring_input_datasets"]
