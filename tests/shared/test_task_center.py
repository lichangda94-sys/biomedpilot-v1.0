from __future__ import annotations

from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def test_task_center_registers_pending_task(tmp_path) -> None:
    center = TaskCenter(tmp_path / "tasks.json")
    task = center.register_task("task-1", TaskType.IMPORT, "meta_analysis", "Import references")
    records = center.list_tasks()
    assert records == [task]
    assert records[0].status is TaskStatus.PENDING

