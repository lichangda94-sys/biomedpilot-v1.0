from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.bioinformatics.adapters.legacy_geo import LegacyGeoAdapter
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


@dataclass(frozen=True)
class GeoImportPlanResult:
    success: bool
    project_id: str
    query_text: str
    full_geo_query: str
    accessions: list[str]
    max_results: int
    output_path: str
    message: str
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)


class GeoImportService:
    def __init__(
        self,
        *,
        adapter: LegacyGeoAdapter | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._adapter = adapter or LegacyGeoAdapter()
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def create_geo_import_plan(
        self,
        *,
        project_id: str,
        query_text: str,
        accession_text: str = "",
        max_results: int = 20,
    ) -> GeoImportPlanResult:
        task = self._start_task(project_id=project_id, query_text=query_text)
        validation_error = self._validate(query_text=query_text, accession_text=accession_text, max_results=max_results)
        if validation_error is not None:
            result = GeoImportPlanResult(
                success=False,
                project_id=project_id,
                query_text=query_text,
                full_geo_query="",
                accessions=[],
                max_results=max_results,
                output_path="",
                message=validation_error,
                error_count=1,
            )
            self._finish_task(task, result)
            return result

        try:
            plan = self._adapter.build_query_plan(
                query_text=query_text,
                accession_text=accession_text,
                max_results=max_results,
            )
            output_path = self._write_output(project_id, plan)
            result = GeoImportPlanResult(
                success=True,
                project_id=project_id,
                query_text=plan.query_text,
                full_geo_query=plan.full_geo_query,
                accessions=list(plan.accessions),
                max_results=plan.max_results,
                output_path=str(output_path),
                message=f"GEO 查询计划已生成：{len(plan.accessions)} 个 accession，最多检索 {plan.max_results} 条。",
                details={"legacy_source": plan.legacy_source, "online_search_executed": False},
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="bioinformatics",
                data_type="geo_query_plan",
                source_path="manual_input",
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = GeoImportPlanResult(
                success=False,
                project_id=project_id,
                query_text=query_text,
                full_geo_query="",
                accessions=[],
                max_results=max_results,
                output_path="",
                message="GEO 查询计划生成失败，请检查输入内容。",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def _validate(self, *, query_text: str, accession_text: str, max_results: int) -> str | None:
        if not query_text.strip() and not accession_text.strip():
            return "请输入 GEO 检索词或 GSE accession。"
        if max_results < 1 or max_results > 1000:
            return "max_results 必须在 1 到 1000 之间。"
        return None

    def _start_task(self, *, project_id: str, query_text: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.IMPORT,
            module="bioinformatics",
            title="GEO Query Import",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Creating GEO query plan for {query_text}" if query_text else "Creating GEO accession import plan",
        )

    def _finish_task(self, task: TaskRecord, result: GeoImportPlanResult) -> None:
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

    def _write_output(self, project_id: str, plan: object) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "bioinformatics" / "geo_import"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"geo_query_plan_{uuid4().hex[:12]}.json"
        payload = {
            "project_id": project_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "geo",
            "status": "ready_for_download_step",
            "online_search_executed": False,
            "plan": asdict(plan),
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path
