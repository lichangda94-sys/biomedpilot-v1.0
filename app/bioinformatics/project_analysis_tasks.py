from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.bioinformatics.comparison_config import load_confirmed_comparison_config
from app.bioinformatics.deg_task_plan import load_deg_task_plan
from app.bioinformatics.group_comparison_design import has_confirmed_group_comparison_design
from app.bioinformatics.project_readiness import load_readiness_artifacts
from app.bioinformatics.standardized_asset_selection import resolve_standardized_assets


TASK_CENTER = Path("manifests") / "analysis_task_center.json"
TASK_RECORD_DIR = Path("analysis") / "task_records"

TASK_TEMPLATES: tuple[dict[str, object], ...] = (
    {
        "task_type": "differential_expression",
        "label": "差异表达分析",
        "default_parameters": {
            "control group": "control",
            "case group": "case",
            "p value": "0.05",
            "FDR": "0.05",
            "logFC": "1.0",
            "method": "Preview Welch t-test；后续接 limma / DESeq2 / edgeR",
        },
    },
    {
        "task_type": "differential_expression_recompute",
        "label": "重新差异表达分析",
        "default_parameters": {
            "preferred_input": "count_matrix",
            "group_config": "需要用户确认",
            "method": "Preview；后续接 DESeq2 / edgeR / limma-voom",
        },
    },
    {"task_type": "enrichment", "label": "富集分析", "default_parameters": {"method": "preview over-representation"}},
    {"task_type": "deg_result_browse", "label": "查看差异基因结果", "default_parameters": {"source": "imported_deg_result"}},
    {"task_type": "volcano_plot", "label": "绘制火山图", "default_parameters": {"log2fc_threshold": "1.0", "padj_threshold": "0.05"}},
    {"task_type": "deg_filtering", "label": "按阈值筛选 DEG", "default_parameters": {"log2fc_threshold": "1.0", "padj_threshold": "0.05"}},
    {"task_type": "enrichment_from_deg", "label": "基于已有 DEG 做富集分析", "default_parameters": {"gene_list": "up/down/all significant"}},
    {"task_type": "gsea", "label": "GSEA", "default_parameters": {"gene_set": "GMT gene set"}},
    {
        "task_type": "correlation",
        "label": "相关性分析",
        "default_parameters": {"target gene": "未设置", "method": "Pearson / Spearman", "minimum samples": "10"},
    },
    {"task_type": "heatmap", "label": "表达热图", "default_parameters": {"source": "FPKM / normalized expression"}},
    {"task_type": "gene_expression_browse", "label": "候选基因表达查看", "default_parameters": {"gene": "未设置"}},
    {"task_type": "pca", "label": "PCA / 聚类", "default_parameters": {"status": "planned if implemented"}},
    {"task_type": "gene_annotation_display", "label": "gene annotation 浏览", "default_parameters": {"fields": "gene_name / description / biotype"}},
    {"task_type": "protein_coding_filter", "label": "protein-coding 筛选", "default_parameters": {"field": "gene_biotype"}},
    {"task_type": "report_annotation", "label": "报告注释", "default_parameters": {"source": "gene_annotation"}},
    {
        "task_type": "survival",
        "label": "生存分析",
        "default_parameters": {"target gene": "未设置", "time field": "未设置", "status field": "未设置", "grouping": "median"},
    },
    {"task_type": "clinical_association", "label": "临床变量关联", "default_parameters": {"method": "preview association"}},
    {
        "task_type": "tcga_gtex_joint",
        "label": "TCGA + GTEx 联合分析",
        "default_parameters": {"batch_correction": "未进行正式 batch correction；仅 preview / testing"},
    },
    {"task_type": "reporting", "label": "报告生成", "default_parameters": {"format": "Markdown"}},
)


@dataclass(frozen=True)
class CreatedAnalysisTask:
    task_id: str
    task_type: str
    label: str
    created_at: str
    status: str
    record_path: Path


def load_analysis_task_center(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    matrix = load_readiness_artifacts(root).get("capability_matrix")
    asset_capabilities = _standardized_asset_capabilities(root)
    asset_capability_rows = {str(row.get("task_id") or ""): row for row in asset_capabilities if isinstance(row, dict)}
    capability_rows = {}
    if isinstance(matrix, dict):
        for row in matrix.get("rows", []) or []:
            if isinstance(row, dict):
                capability_rows[str(row.get("analysis_type"))] = row

    tasks: list[dict[str, object]] = []
    for template in TASK_TEMPLATES:
        task_type = str(template["task_type"])
        capability = capability_rows.get(task_type, {})
        asset_capability = asset_capability_rows.get(task_type, {})
        warnings = [str(item) for item in capability.get("warnings", []) or []] if isinstance(capability, dict) else []
        if isinstance(asset_capability, dict) and asset_capability.get("reason"):
            warnings.append(str(asset_capability.get("reason")))
        if task_type == "tcga_gtex_joint" and any(item.get("task_id") == "human_cohort_integration" and item.get("status") == "not_available" for item in asset_capabilities):
            warnings.append("小鼠数据：不推荐 TCGA/GTEx 人类队列整合。")
        if task_type == "tcga_gtex_joint" and not warnings:
            warnings.append("当前未进行正式 batch correction，结果仅用于 preview / testing。")
        missing = [str(item) for item in capability.get("missing_inputs", []) or []] if isinstance(capability, dict) else []
        if isinstance(asset_capability, dict) and asset_capability.get("status") == "ready_with_group_confirmation":
            missing = list(dict.fromkeys([*missing, "confirmed_group_config"]))
        if isinstance(asset_capability, dict) and asset_capability.get("status") == "needs_asset_selection":
            missing = list(dict.fromkeys([*missing, "default_standardized_asset_selection"]))
        available = [str(item) for item in capability.get("available_inputs", []) or []] if isinstance(capability, dict) else []
        if isinstance(asset_capability, dict) and asset_capability.get("source_asset_type"):
            available = list(dict.fromkeys([*available, str(asset_capability.get("source_asset_type"))]))
        can_run = bool(capability.get("can_run")) if isinstance(capability, dict) else False
        if isinstance(asset_capability, dict) and asset_capability.get("status") == "available":
            can_run = True
        elif isinstance(asset_capability, dict) and asset_capability.get("status") == "ready_with_group_confirmation":
            can_run = False
        elif isinstance(asset_capability, dict) and asset_capability.get("status") == "needs_asset_selection":
            can_run = False
        capability_status = asset_capability.get("status") if isinstance(asset_capability, dict) and asset_capability else ("available" if can_run else "not_available")
        tasks.append(
            {
                "task_type": task_type,
                "label": template["label"],
                "can_run": can_run,
                "capability_status": capability_status,
                "source_asset_type": asset_capability.get("source_asset_type") if isinstance(asset_capability, dict) else "",
                "available_inputs": available,
                "missing_inputs": missing if (matrix or asset_capability) else ["analysis_capability_matrix.json 尚未生成"],
                "warnings": warnings,
                "default_parameters": template["default_parameters"],
                "preview_status": f"{capability_status} · testing / preview",
            }
        )

    center = {
        "schema_version": "biomedpilot.analysis_task_center.v1",
        "generated_at": _now(),
        "project_root": str(root),
        "tasks": tasks,
        "capabilities": asset_capabilities,
        "task_groups": _task_groups_from_capabilities(asset_capabilities),
    }
    _write_json(root / TASK_CENTER, center)
    return center


def _standardized_asset_capabilities(root: Path) -> list[dict[str, object]]:
    resolved = resolve_standardized_assets(root)
    assets = [asset for asset in resolved.get("assets", []) or [] if isinstance(asset, dict)]
    has_confirmed_group_config = load_confirmed_comparison_config(root) is not None or has_confirmed_group_comparison_design(root)
    deg_plan = load_deg_task_plan(root)
    capabilities: list[dict[str, object]] = []
    for asset_type in resolved.get("blocked_asset_types", []) or []:
        capabilities.extend(_asset_selection_required_capabilities(str(asset_type)))
    for asset in assets:
        asset_type = str(asset.get("asset_type") or "")
        if asset_type == "count_matrix":
            group_count = len(asset.get("inferred_groups", []) or [])
            if deg_plan:
                status = "configured_not_run"
                reason = "已创建 DEG task plan；当前只保存配置，尚未执行真实差异表达分析。"
            elif has_confirmed_group_config:
                status = "available"
                reason = "检测到 count matrix，已确认分组，可创建 DEG task plan。"
            else:
                status = "ready_with_group_confirmation"
                reason = f"检测到 {group_count} 个推断分组，请确认实验分组后重新差异分析。"
            capabilities.extend(
                [
                    {
                        "task_id": "differential_expression_recompute",
                        "status": status,
                        "source_asset_type": "count_matrix",
                        "source_asset_id": asset.get("asset_id", ""),
                        "reason": reason,
                    },
                    {
                        "task_id": "normalization",
                        "status": "available",
                        "source_asset_type": "count_matrix",
                        "source_asset_id": asset.get("asset_id", ""),
                        "reason": "检测到 count matrix，可进行标准化转换。",
                    },
                    {
                        "task_id": "qc",
                        "status": "available",
                        "source_asset_type": "count_matrix",
                        "source_asset_id": asset.get("asset_id", ""),
                        "reason": "检测到 count matrix，可进行样本 QC。",
                    },
                ]
            )
        elif asset_type == "normalized_expression_matrix":
            value_type = str(asset.get("value_type") or "normalized")
            for task_id, reason in {
                "heatmap": f"检测到 {value_type.upper()} expression matrix，可用于表达热图。",
                "correlation": f"检测到 {value_type.upper()} expression matrix，可用于样本相关性。",
                "gene_expression_browse": f"检测到 {value_type.upper()} expression matrix，可用于候选基因表达查看。",
                "pca": "PCA / 聚类入口已规划；当前标记为 planned。",
            }.items():
                capabilities.append(
                    {
                        "task_id": task_id,
                        "status": "planned" if task_id == "pca" else "available",
                        "source_asset_type": "normalized_expression_matrix",
                        "source_asset_id": asset.get("asset_id", ""),
                        "reason": reason,
                    }
                )
        elif asset_type == "deg_result_table":
            for task_id, reason in {
                "deg_result_browse": "检测到已有 DEG comparison，可直接浏览差异基因结果。",
                "volcano_plot": "检测到已有 DEG comparison，可用于火山图输入。",
                "deg_filtering": "检测到已有 DEG comparison，可按 padj/log2FC 筛选。",
                "enrichment_from_deg": "检测到已有 DEG comparison，可作为富集分析输入。",
            }.items():
                capabilities.append(
                    {
                        "task_id": task_id,
                        "status": "available" if task_id != "enrichment_from_deg" else "ready_with_threshold_selection",
                        "source_asset_type": "deg_result_table",
                        "source_asset_id": asset.get("asset_id", ""),
                        "reason": reason,
                    }
                )
        elif asset_type == "gene_annotation":
            for task_id, reason in {
                "gene_annotation_display": "检测到 gene annotation，可用于注释浏览。",
                "protein_coding_filter": "检测到 gene_biotype，可用于 protein-coding 筛选。" if "gene_biotype" in (asset.get("annotation_fields") or []) else "检测到 gene annotation，可规划 protein-coding 筛选。",
                "report_annotation": "检测到 gene annotation，可用于报告注释。",
            }.items():
                capabilities.append(
                    {
                        "task_id": task_id,
                        "status": "available",
                        "source_asset_type": "gene_annotation",
                        "source_asset_id": asset.get("asset_id", ""),
                        "reason": reason,
                    }
                )
    if any(str(asset.get("species") or "") == "Mus musculus" for asset in assets):
        capabilities.append(
            {
                "task_id": "human_cohort_integration",
                "status": "not_available",
                "source_asset_type": "species_metadata",
                "reason": "小鼠数据：适合动物模型分析、方法验证和机制探索；不推荐 TCGA/GTEx 人类队列整合。",
            }
        )
    return _dedupe_capabilities(capabilities)


def _asset_selection_required_capabilities(asset_type: str) -> list[dict[str, object]]:
    reason = "检测到多个同类标准化资产，请先在标准化资产页选择默认资产。"
    task_map = {
        "count_matrix": ("differential_expression_recompute", "normalization", "qc"),
        "normalized_expression_matrix": ("heatmap", "correlation", "gene_expression_browse", "pca"),
        "deg_result_table": ("deg_result_browse", "volcano_plot", "deg_filtering", "enrichment_from_deg"),
        "gene_annotation": ("gene_annotation_display", "protein_coding_filter", "report_annotation"),
    }
    return [
        {
            "task_id": task_id,
            "status": "needs_asset_selection",
            "source_asset_type": asset_type,
            "source_asset_id": "",
            "reason": reason,
        }
        for task_id in task_map.get(asset_type, ())
    ]


def _dedupe_capabilities(capabilities: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: dict[tuple[str, str], dict[str, object]] = {}
    for capability in capabilities:
        key = (str(capability.get("task_id") or ""), str(capability.get("source_asset_id") or capability.get("source_asset_type") or ""))
        deduped.setdefault(key, capability)
    return list(deduped.values())


def _task_groups_from_capabilities(capabilities: list[dict[str, object]]) -> list[dict[str, object]]:
    available = {str(item.get("task_id") or ""): item for item in capabilities if item.get("status") in {"available", "ready_with_threshold_selection", "ready_with_group_confirmation"}}
    needs_selection = {str(item.get("task_id") or ""): item for item in capabilities if item.get("status") == "needs_asset_selection"}
    groups = []
    if needs_selection:
        groups.append({"group": "需要选择默认资产", "tasks": list(needs_selection)})
    if {"deg_result_browse", "volcano_plot", "deg_filtering", "enrichment_from_deg"} & set(available):
        groups.append({"group": "可直接使用已有结果", "tasks": [task for task in ("deg_result_browse", "volcano_plot", "deg_filtering", "enrichment_from_deg") if task in available]})
    count_tasks = [task for task in ("differential_expression_recompute", "qc", "normalization") if task in available]
    if count_tasks:
        needs_group_confirmation = available.get("differential_expression_recompute", {}).get("status") == "ready_with_group_confirmation"
        groups.append({"group": "需要确认分组后运行" if needs_group_confirmation else "已确认分组后可运行", "tasks": count_tasks})
    if {"heatmap", "correlation", "gene_expression_browse", "pca"} & set(available):
        groups.append({"group": "表达数据探索", "tasks": [task for task in ("heatmap", "correlation", "gene_expression_browse", "pca") if task in available]})
    if {"gene_annotation_display", "protein_coding_filter", "report_annotation"} & set(available):
        groups.append({"group": "注释与报告", "tasks": [task for task in ("gene_annotation_display", "protein_coding_filter", "report_annotation") if task in available]})
    return groups


def create_analysis_task(project_root: str | Path, task_type: str) -> CreatedAnalysisTask:
    root = Path(project_root).expanduser().resolve()
    center = load_analysis_task_center(root)
    task = next((item for item in center.get("tasks", []) or [] if isinstance(item, dict) and item.get("task_type") == task_type), None)
    if not isinstance(task, dict):
        raise ValueError(f"未知分析任务类型：{task_type}")
    if not task.get("can_run"):
        missing = "、".join(str(item) for item in task.get("missing_inputs", []) or []) or "未知输入"
        raise ValueError(f"该任务当前不可创建，缺失输入：{missing}")

    task_id = f"task-{uuid4().hex[:8]}"
    created_at = _now()
    record = {
        "schema_version": "biomedpilot.analysis_task_record.v1",
        "task_id": task_id,
        "task_type": task_type,
        "label": task.get("label") or task_type,
        "created_at": created_at,
        "status": "created",
        "parameters": task.get("default_parameters") or {},
        "warnings": task.get("warnings") or [],
        "execution": "not_run",
        "note": "当前只创建任务记录，不运行正式统计分析。",
    }
    record_path = root / TASK_RECORD_DIR / f"{task_id}.json"
    _write_json(record_path, record)
    return CreatedAnalysisTask(
        task_id=task_id,
        task_type=task_type,
        label=str(record["label"]),
        created_at=created_at,
        status="created",
        record_path=record_path,
    )


def load_task_records(project_root: str | Path) -> list[dict[str, object]]:
    root = Path(project_root).expanduser().resolve()
    records = []
    for path in sorted((root / TASK_RECORD_DIR).glob("*.json")):
        try:
            payload = _read_json(path)
        except Exception:
            continue
        payload["record_path"] = str(path)
        records.append(payload)
    return records


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
