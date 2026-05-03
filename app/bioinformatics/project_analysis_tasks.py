from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.bioinformatics.project_readiness import load_readiness_artifacts


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
    {"task_type": "enrichment", "label": "富集分析", "default_parameters": {"method": "preview over-representation"}},
    {"task_type": "gsea", "label": "GSEA", "default_parameters": {"gene_set": "GMT gene set"}},
    {
        "task_type": "correlation",
        "label": "相关性分析",
        "default_parameters": {"target gene": "未设置", "method": "Pearson / Spearman", "minimum samples": "10"},
    },
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
    capability_rows = {}
    if isinstance(matrix, dict):
        for row in matrix.get("rows", []) or []:
            if isinstance(row, dict):
                capability_rows[str(row.get("analysis_type"))] = row

    tasks: list[dict[str, object]] = []
    for template in TASK_TEMPLATES:
        task_type = str(template["task_type"])
        capability = capability_rows.get(task_type, {})
        warnings = [str(item) for item in capability.get("warnings", []) or []] if isinstance(capability, dict) else []
        if task_type == "tcga_gtex_joint" and not warnings:
            warnings.append("当前未进行正式 batch correction，结果仅用于 preview / testing。")
        missing = [str(item) for item in capability.get("missing_inputs", []) or []] if isinstance(capability, dict) else []
        available = [str(item) for item in capability.get("available_inputs", []) or []] if isinstance(capability, dict) else []
        can_run = bool(capability.get("can_run")) if isinstance(capability, dict) else False
        tasks.append(
            {
                "task_type": task_type,
                "label": template["label"],
                "can_run": can_run,
                "available_inputs": available,
                "missing_inputs": missing if matrix else ["analysis_capability_matrix.json 尚未生成"],
                "warnings": warnings,
                "default_parameters": template["default_parameters"],
                "preview_status": "testing / preview",
            }
        )

    center = {
        "schema_version": "biomedpilot.analysis_task_center.v1",
        "generated_at": _now(),
        "project_root": str(root),
        "tasks": tasks,
    }
    _write_json(root / TASK_CENTER, center)
    return center


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
