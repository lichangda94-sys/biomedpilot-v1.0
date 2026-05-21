# Bioinformatics GTEx G6.1-G6.5 Implementation Handoff

Date: 2026-05-19

## Scope

This stage brings the GTEx line up to the same implementation rhythm as TCGA B6, while preserving the boundary that GTEx is an independent normal tissue expression resource and is not an automatic TCGA normal control.

Implemented stages:

- G6.1: GTEx metadata preview and download plan draft.
- G6.2: Explicit GTEx raw file download execution from the plan.
- G6.3: GTEx expression matrix build from downloaded source files.
- G6.4: GTEx build artifacts registered for unified data check and preparation.
- G6.5: Readiness summary and UI handoff state that requires user confirmation before any explicit TCGA+GTEx joint configuration.

Out of scope:

- No TCGA+GTEx automatic merge.
- No batch correction execution.
- No automatic TCGA DEG/GSEA execution from GTEx.
- No B5.19 work.

## User Flow

1. Open the GTEx data source card.
2. Select tissue and purpose.
3. Click `预览 GTEx 可下载数据`.
4. Click `生成 GTEx 下载计划草案`.
5. Click `下载 GTEx 原始文件`.
6. Click `构建 GTEx 表达矩阵`.
7. Enter `数据检查与准备`.

The page shows the five-step workflow state and keeps the warning visible: GTEx does not become a TCGA normal control unless a later explicit joint configuration is created.

## Artifacts

G6.1 plan:

- `acquisition/gtex_download_plans/*.json`

G6.2 download execution:

- `acquisition/download_requests/*.json`
- `acquisition/download_receipts/*.json`
- `acquisition/source_manifests/*.json`
- `raw_data/gtex/<tissue>/<download_id>/...`

G6.3 expression build:

- `processed/gtex/<tissue>/<build_id>/gtex_expression_matrix.csv`
- `processed/gtex/<tissue>/<build_id>/gtex_sample_metadata.csv`
- `processed/gtex/<tissue>/<build_id>/gtex_donor_metadata.csv`
- `processed/gtex/<tissue>/<build_id>/gtex_tissue_metadata.csv`
- `processed/gtex/<tissue>/<build_id>/gtex_gene_annotation.csv`
- `processed/gtex/<tissue>/<build_id>/gtex_expression_build_manifest.json`

## Readiness Boundary

GTEx build artifacts are exposed to `project_readiness.py` as:

- `gtex_expression_matrix`
- `gtex_sample_metadata`
- `gtex_donor_metadata`
- `gene_annotation`

The readiness report includes `gtex_readiness`, sample matching status, value type policy, and warnings. TCGA+GTEx joint capability remains blocked until the user explicitly confirms a joint configuration and batch correction plan.

## Confirmation Point

G6.5 stops at: GTEx build artifacts are discoverable by the unified data check and preparation layer, and the UI can route the user there. The next stage needs user confirmation before implementing explicit TCGA+GTEx joint configuration semantics.
