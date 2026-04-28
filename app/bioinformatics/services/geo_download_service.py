from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.bioinformatics.adapters.geo_download_adapter import GeoDownloadAdapter
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


@dataclass(frozen=True)
class GeoDownloadPlanResult:
    success: bool
    project_id: str
    source_path: str
    planned_accessions: int
    output_path: str
    message: str
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)


class GeoDownloadService:
    def __init__(
        self,
        *,
        adapter: GeoDownloadAdapter | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._adapter = adapter or GeoDownloadAdapter()
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def create_download_plan(self, *, project_id: str, geo_query_plan_path: str) -> GeoDownloadPlanResult:
        task = self._start_task(project_id=project_id, source_path=geo_query_plan_path)
        validation_error = self._validate(geo_query_plan_path)
        if validation_error is not None:
            result = GeoDownloadPlanResult(
                success=False,
                project_id=project_id,
                source_path=geo_query_plan_path,
                planned_accessions=0,
                output_path="",
                message=validation_error,
                error_count=1,
            )
            self._finish_task(task, result)
            return result

        source_path = Path(geo_query_plan_path).expanduser().resolve()
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            if "plan" not in payload:
                raise ValueError("Download 需要 GEO 查询计划 JSON。")
            download_root = self._storage_root / "projects" / project_id / "bioinformatics" / "downloads"
            download_root.mkdir(parents=True, exist_ok=True)
            items = self._adapter.build_download_plan(
                project_id=project_id,
                query_plan_payload=payload,
                download_root=download_root,
            )
            output_path = self._write_output(project_id, source_path, items)
            message = (
                f"GEO 下载计划已生成：{len(items)} 个 accession。实际下载尚未执行。"
                if items
                else "GEO 下载计划已生成，但没有明确 accession；请先执行受控在线检索或手动输入 GSE。"
            )
            result = GeoDownloadPlanResult(
                success=True,
                project_id=project_id,
                source_path=str(source_path),
                planned_accessions=len(items),
                output_path=str(output_path),
                message=message,
                details={"download_executed": False},
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="bioinformatics",
                data_type="geo_download_plan",
                source_path=str(source_path),
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = GeoDownloadPlanResult(
                success=False,
                project_id=project_id,
                source_path=str(source_path),
                planned_accessions=0,
                output_path="",
                message="GEO 下载计划生成失败，请确认输入来自数据检索 / 导入步骤。",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def _validate(self, geo_query_plan_path: str) -> str | None:
        if not geo_query_plan_path.strip():
            return "请选择 GEO 查询计划 JSON 文件。"
        path = Path(geo_query_plan_path).expanduser()
        if not path.exists():
            return "GEO 查询计划文件不存在，请检查路径。"
        if path.suffix.lower() != ".json":
            return "GEO 下载计划需要 JSON 输入。"
        return None

    def _start_task(self, *, project_id: str, source_path: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.DOWNLOAD,
            module="bioinformatics",
            title="GEO Download Plan",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Creating GEO download plan from {source_path}" if source_path else "Waiting for GEO query plan",
        )

    def _finish_task(self, task: TaskRecord, result: GeoDownloadPlanResult) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._task_center.save_task(
            TaskRecord(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED if result.success else TaskStatus.FAILED,
                module=task.module,
                title=task.title,
                created_at=task.created_at,
                updated_at=now,
                project_id=task.project_id,
                started_at=task.started_at,
                finished_at=now,
                summary=result.message,
                error_message="" if result.success else result.message,
            )
        )

    def _write_output(self, project_id: str, source_path: Path, items: list[object]) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "bioinformatics" / "geo_download"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"geo_download_plan_{uuid4().hex[:12]}.json"
        payload = {
            "project_id": project_id,
            "source_path": str(source_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "download_executed": False,
            "requires_user_confirmation": True,
            "download_items": [asdict(item) for item in items],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path
