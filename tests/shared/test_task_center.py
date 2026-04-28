from __future__ import annotations

from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def test_task_center_registers_pending_task(tmp_path) -> None:
    center = TaskCenter(tmp_path / "tasks.json")
    task = center.register_task("task-1", TaskType.IMPORT, "meta_analysis", "Import references")
    records = center.list_tasks()
    assert records == [task]
    assert records[0].status is TaskStatus.PENDING


def test_task_center_registers_literature_import_details(tmp_path) -> None:
    center = TaskCenter(tmp_path / "tasks.json")
    task = center.register_task(
        "task-lit",
        TaskType.LITERATURE_IMPORT,
        "meta_analysis",
        "Literature Import",
        project_id="meta-test",
        status=TaskStatus.RUNNING,
        started_at="2026-04-28T00:00:00+00:00",
        summary="Importing sample.nbib",
    )
    records = center.list_tasks()
    assert records == [task]
    assert records[0].project_id == "meta-test"
    assert records[0].summary == "Importing sample.nbib"


def test_task_center_registers_prepare_screening_details(tmp_path) -> None:
    center = TaskCenter(tmp_path / "tasks.json")
    task = center.register_task(
        "task-prepare",
        TaskType.PREPARE_SCREENING,
        "meta_analysis",
        "Prepare for Screening",
        project_id="meta-test",
        status=TaskStatus.RUNNING,
        started_at="2026-04-28T00:00:00+00:00",
        summary="Preparing screening records",
    )
    records = center.list_tasks()
    assert records == [task]
    assert records[0].task_type is TaskType.PREPARE_SCREENING


def test_task_center_registers_duplicate_review_details(tmp_path) -> None:
    center = TaskCenter(tmp_path / "tasks.json")
    task = center.register_task(
        "task-duplicate",
        TaskType.DUPLICATE_REVIEW,
        "meta_analysis",
        "Duplicate Review",
        project_id="meta-test",
        status=TaskStatus.RUNNING,
        started_at="2026-04-28T00:00:00+00:00",
        summary="Reviewing duplicate candidates",
    )
    records = center.list_tasks()
    assert records == [task]
    assert records[0].task_type is TaskType.DUPLICATE_REVIEW


def test_task_center_registers_screening_details(tmp_path) -> None:
    center = TaskCenter(tmp_path / "tasks.json")
    task = center.register_task(
        "task-screening",
        TaskType.SCREENING,
        "meta_analysis",
        "Screening",
        project_id="meta-test",
        status=TaskStatus.RUNNING,
        started_at="2026-04-28T00:00:00+00:00",
        summary="Creating screening queue",
    )
    records = center.list_tasks()
    assert records == [task]
    assert records[0].task_type is TaskType.SCREENING


def test_task_center_registers_extraction_details(tmp_path) -> None:
    center = TaskCenter(tmp_path / "tasks.json")
    task = center.register_task(
        "task-extraction",
        TaskType.EXTRACTION,
        "meta_analysis",
        "Extraction",
        project_id="meta-test",
        status=TaskStatus.RUNNING,
        started_at="2026-04-28T00:00:00+00:00",
        summary="Creating extraction pool",
    )
    records = center.list_tasks()
    assert records == [task]
    assert records[0].task_type is TaskType.EXTRACTION
