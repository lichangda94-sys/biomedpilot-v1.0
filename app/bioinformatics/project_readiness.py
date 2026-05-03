from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.project_recognition import load_recognition_report


READINESS_REPORT = Path("logs") / "readiness" / "readiness_report.json"
CAPABILITY_MATRIX = Path("manifests") / "analysis_capability_matrix.json"

ANALYSIS_ROWS = (
    ("differential_expression", "差异表达分析", {"expression_matrix", "sample_metadata", "comparison_config"}),
    ("enrichment", "富集分析", {"expression_matrix"}),
    ("gsea", "GSEA", {"expression_matrix", "gmt_gene_set"}),
    ("correlation", "相关性分析", {"expression_matrix"}),
    ("survival", "生存分析", {"expression_matrix", "clinical_metadata"}),
    ("clinical_association", "临床变量关联", {"clinical_metadata"}),
    ("tcga_gtex_joint", "TCGA + GTEx 联合分析", {"expression_matrix", "sample_metadata"}),
    ("reporting", "报告生成", {"analysis_result"}),
)

CORE_INPUTS = {"expression_matrix", "raw_count_matrix"}


def run_project_readiness(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    recognition = load_recognition_report(root) or {}
    files = list(recognition.get("files", []) or [])
    available = {str(item.get("recognized_type")) for item in files if item.get("recognized_type") and item.get("recognized_type") != "unknown"}
    has_core_input = bool(available & CORE_INPUTS)
    warnings: list[str] = [str(item) for item in recognition.get("warnings", []) or []]
    if not has_core_input:
        warnings.append("无表达矩阵。")
    if "sample_metadata" not in available:
        warnings.append("样本信息缺失。")
    if "clinical_metadata" not in available:
        warnings.append("临床信息缺失。")
    rows = []
    for key, label, required in ANALYSIS_ROWS:
        missing = sorted(required - available)
        can_run = bool(has_core_input) and not missing and (key not in {"tcga_gtex_joint", "reporting"})
        row_warnings = []
        if key == "tcga_gtex_joint":
            row_warnings.append("TCGA + GTEx 尚未批次校正，结果仅用于 preview / testing。")
        if key == "reporting":
            row_warnings.append("报告生成不参与 Ready 判定；需先有真实分析结果。")
        next_step = "可创建预览任务。" if can_run else "请补充缺失输入或返回前序页面。"
        if key == "reporting":
            next_step = "请先创建并执行分析任务，生成结果后再进入报告。"
        rows.append(
            {
                "analysis_type": key,
                "label": label,
                "can_run": can_run,
                "available_inputs": sorted(required & available),
                "missing_inputs": missing,
                "warnings": row_warnings,
                "next_step": next_step,
            }
        )
    ready_rows = [row for row in rows if row["can_run"] and row["analysis_type"] != "reporting"]
    if not has_core_input:
        overall = "not_ready"
    elif ready_rows and warnings:
        overall = "ready_with_warnings"
    elif ready_rows:
        overall = "partially_ready"
    else:
        overall = "not_ready"
    report = {
        "schema_version": "biomedpilot.readiness_report.v1",
        "generated_at": _now(),
        "project_root": str(root),
        "overall_status": overall,
        "available_inputs": sorted(available),
        "has_core_input": has_core_input,
        "warnings": warnings,
    }
    matrix = {
        "schema_version": "biomedpilot.analysis_capability_matrix.v1",
        "generated_at": report["generated_at"],
        "rows": rows,
    }
    _write_json(root / READINESS_REPORT, report)
    _write_json(root / CAPABILITY_MATRIX, matrix)
    return {"readiness_report": report, "capability_matrix": matrix}


def load_readiness_artifacts(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    readiness_path = root / READINESS_REPORT
    matrix_path = root / CAPABILITY_MATRIX
    return {
        "readiness_report": _read_json(readiness_path) if readiness_path.exists() else None,
        "capability_matrix": _read_json(matrix_path) if matrix_path.exists() else None,
        "readiness_path": str(readiness_path),
        "matrix_path": str(matrix_path),
    }


def readiness_status_zh(status: str) -> str:
    return {
        "not_ready": "尚未准备好",
        "partially_ready": "部分准备就绪",
        "ready": "已准备好",
        "ready_with_warnings": "已准备好，但存在警告",
        "unavailable": "暂不可运行",
    }.get(status, "未知")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
