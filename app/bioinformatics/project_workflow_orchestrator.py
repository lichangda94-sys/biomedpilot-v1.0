from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from app.bioinformatics.project_analysis_tasks import load_analysis_task_center
from app.bioinformatics.project_readiness import load_readiness_artifacts, run_project_readiness
from app.bioinformatics.project_recognition import load_recognition_report, run_project_recognition
from app.bioinformatics.project_standardization import generate_standardized_assets, load_standardization_artifacts
from app.bioinformatics.project_workspace_binding import load_latest_acquisition_summary


WORKFLOW_STATE = Path("manifests") / "project_workflow_state.json"
WORKFLOW_SUMMARY = Path("logs") / "workflow" / "project_workflow_summary.json"
WORKFLOW_REPORT = Path("logs") / "workflow" / "project_workflow_report.md"

WORKFLOW_STEPS: tuple[tuple[str, str], ...] = (
    ("workspace_validation", "工作区验证"),
    ("acquisition", "数据获取"),
    ("recognition", "数据识别"),
    ("initial_readiness", "初始 Ready 判断"),
    ("standardization", "标准化"),
    ("readiness_refresh", "Ready 刷新"),
    ("task_center", "分析任务中心"),
    ("results", "结果管理"),
    ("report", "报告生成"),
    ("final_validation", "最终验证"),
)


def workflow_status_zh(status: str) -> str:
    return {
        "not_started": "未开始",
        "running": "运行中",
        "completed": "已完成",
        "completed_with_warnings": "完成但有警告",
        "skipped": "已跳过",
        "failed": "失败",
        "unavailable": "不可用",
    }.get(status, "未知")


def load_workflow_state(project_root: str | Path) -> dict[str, object] | None:
    path = Path(project_root).expanduser().resolve() / WORKFLOW_STATE
    return _read_json(path) if path.exists() else None


def run_project_stage(project_root: str | Path, stage_key: str) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    label = dict(WORKFLOW_STEPS).get(stage_key, stage_key)
    try:
        payload = _stage_runner(stage_key)(root)
        warnings = [str(item) for item in payload.get("warnings", []) or []] if isinstance(payload, dict) else []
        status = "completed_with_warnings" if warnings else "completed"
        result = {
            "stage_key": stage_key,
            "label": label,
            "status": status,
            "status_zh": workflow_status_zh(status),
            "input": payload.get("input", []) if isinstance(payload, dict) else [],
            "output": payload.get("output", []) if isinstance(payload, dict) else [],
            "warnings": warnings,
            "next_step": payload.get("next_step", "继续下一步。") if isinstance(payload, dict) else "继续下一步。",
            "updated_at": _now(),
        }
    except Exception as exc:
        result = {
            "stage_key": stage_key,
            "label": label,
            "status": "failed",
            "status_zh": workflow_status_zh("failed"),
            "input": [],
            "output": [],
            "warnings": [f"{label} 失败：{exc}"],
            "next_step": "请检查项目文件或返回对应页面处理。",
            "updated_at": _now(),
        }
    _merge_stage_state(root, result)
    return result


def run_project_workflow(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    steps = [run_project_stage(root, key) for key, _ in WORKFLOW_STEPS]
    status = "completed_with_warnings" if any(step.get("warnings") for step in steps) else "completed"
    state = _state_payload(root, steps, status)
    _write_state(root, state)
    return state


def default_workflow_state(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    return _state_payload(
        root,
        [
            {
                "stage_key": key,
                "label": label,
                "status": "not_started",
                "status_zh": workflow_status_zh("not_started"),
                "input": [],
                "output": [],
                "warnings": [],
                "next_step": "尚未运行工作流。",
                "updated_at": "尚未生成",
            }
            for key, label in WORKFLOW_STEPS
        ],
        "not_started",
    )


def _stage_runner(stage_key: str) -> Callable[[Path], dict[str, object]]:
    runners: dict[str, Callable[[Path], dict[str, object]]] = {
        "workspace_validation": _workspace_validation,
        "acquisition": _acquisition_status,
        "recognition": _recognition,
        "initial_readiness": _readiness,
        "standardization": _standardization,
        "readiness_refresh": _readiness,
        "task_center": _task_center,
        "results": _results_read_only,
        "report": _report_read_only,
        "final_validation": _final_validation,
    }
    if stage_key not in runners:
        raise ValueError(f"未知工作流步骤：{stage_key}")
    return runners[stage_key]


def _workspace_validation(root: Path) -> dict[str, object]:
    warnings = []
    for filename in ("project_manifest.json", "project_config.json"):
        if not (root / filename).exists():
            warnings.append(f"缺少 {filename}")
    return {"input": [str(root)], "output": ["project_manifest.json", "project_config.json"], "warnings": warnings}


def _acquisition_status(root: Path) -> dict[str, object]:
    summary = load_latest_acquisition_summary(root)
    if summary is None:
        return {"input": [], "output": [], "warnings": ["尚未生成数据获取记录。"], "next_step": "返回数据来源选择页。"}
    warnings = list(summary.warnings)
    if summary.strategy == "plan_only":
        warnings.append("plan_only 仅生成获取计划，需要补充文件或后续执行下载。")
    return {"input": list(summary.registered_files), "output": [str(summary.plan_path), str(summary.record_path), str(summary.handoff_path)], "warnings": warnings}


def _recognition(root: Path) -> dict[str, object]:
    report = run_project_recognition(root)
    return {"input": ["raw_data/", "acquisition/"], "output": [str(root / "logs/recognition/recognition_report.json")], "warnings": report.get("warnings", [])}


def _readiness(root: Path) -> dict[str, object]:
    artifacts = run_project_readiness(root)
    report = artifacts.get("readiness_report", {}) if isinstance(artifacts, dict) else {}
    return {
        "input": ["logs/recognition/recognition_report.json"],
        "output": [str(root / "logs/readiness/readiness_report.json"), str(root / "manifests/analysis_capability_matrix.json")],
        "warnings": report.get("warnings", []) if isinstance(report, dict) else [],
    }


def _standardization(root: Path) -> dict[str, object]:
    artifacts = generate_standardized_assets(root)
    registry = artifacts.get("registry", {}) if isinstance(artifacts, dict) else {}
    return {
        "input": ["当前识别批次：recognized_data/current.json"],
        "output": [str(root / "manifests/standardized_assets_registry.json"), str(root / "standardized_data/analysis_ready_assets/analysis_ready_manifest.json")],
        "warnings": registry.get("warnings", []) if isinstance(registry, dict) else [],
    }


def _task_center(root: Path) -> dict[str, object]:
    center = load_analysis_task_center(root)
    return {"input": ["manifests/analysis_capability_matrix.json"], "output": [str(root / "manifests/analysis_task_center.json")], "warnings": [] if center.get("tasks") else ["尚未生成可用任务。"]}


def _results_read_only(root: Path) -> dict[str, object]:
    index = root / "results" / "summaries" / "result_index.json"
    if not index.exists():
        return {"input": [], "output": [], "warnings": ["暂无结果索引。"], "next_step": "先在分析任务中心创建并运行任务。"}
    return {"input": [str(index)], "output": [str(index)], "warnings": []}


def _report_read_only(root: Path) -> dict[str, object]:
    report = root / "reports" / "project_analysis_report.md"
    if not report.exists():
        return {"input": [], "output": [], "warnings": ["尚未生成项目报告。"], "next_step": "进入报告页生成 Markdown 报告。"}
    return {"input": [str(report)], "output": [str(report)], "warnings": []}


def _final_validation(root: Path) -> dict[str, object]:
    warnings = []
    if load_recognition_report(root) is None:
        warnings.append("未找到 recognition report。")
    if load_readiness_artifacts(root).get("readiness_report") is None:
        warnings.append("未找到 readiness report。")
    if load_standardization_artifacts(root).get("registry") is None:
        warnings.append("未找到 standardized assets registry。")
    return {"input": ["project artifacts"], "output": ["workflow validation"], "warnings": warnings}


def _merge_stage_state(root: Path, stage: dict[str, object]) -> None:
    current = load_workflow_state(root) or default_workflow_state(root)
    steps = []
    replaced = False
    for item in current.get("steps", []) or []:
        if isinstance(item, dict) and item.get("stage_key") == stage.get("stage_key"):
            steps.append(stage)
            replaced = True
        else:
            steps.append(item)
    if not replaced:
        steps.append(stage)
    status = "completed_with_warnings" if any(isinstance(step, dict) and step.get("warnings") for step in steps) else "completed"
    _write_state(root, _state_payload(root, steps, status))


def _state_payload(root: Path, steps: list[dict[str, object]], status: str) -> dict[str, object]:
    current_stage = next((str(step.get("label")) for step in steps if step.get("status") not in {"completed", "completed_with_warnings"}), "最终验证")
    return {
        "schema_version": "biomedpilot.project_workflow_state.v1",
        "generated_at": _now(),
        "project_root": str(root),
        "overall_status": status,
        "current_stage": current_stage,
        "ready_status": _ready_status(root),
        "steps": steps,
    }


def _ready_status(root: Path) -> str:
    report = load_readiness_artifacts(root).get("readiness_report")
    return str(report.get("overall_status") or "尚未生成") if isinstance(report, dict) else "尚未生成"


def _write_state(root: Path, state: dict[str, object]) -> None:
    _write_json(root / WORKFLOW_STATE, state)
    _write_json(root / WORKFLOW_SUMMARY, state)
    lines = ["# BioMedPilot 生信工作流总控", ""]
    for step in state.get("steps", []) or []:
        if isinstance(step, dict):
            lines.append(f"- {step.get('label')}: {step.get('status_zh')}")
    report_path = root / WORKFLOW_REPORT
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
