from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QScrollArea, QStackedWidget, QTabBar, QVBoxLayout, QWidget

from app.shared.data_center.service import DataCenter
from app.shared.environment.checks import check_local_environment
from app.shared.project_center.service import ProjectCenter
from app.shared.report_center import REPORT_TYPES
from app.shared.semantic_keys import NavKey
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType
from app.shared.ui import card_title_qss, page_title_qss, surface_card_qss


def build_centers_page(
    *,
    project_center: ProjectCenter | None = None,
    data_center: DataCenter | None = None,
    task_center: TaskCenter | None = None,
) -> QScrollArea:
    project_center = project_center or ProjectCenter.default()
    data_center = data_center or DataCenter.default()
    task_center = task_center or TaskCenter.default()
    page = QScrollArea()
    page.setObjectName("centersPage")
    page.setWidgetResizable(True)
    page.setProperty("navKey", NavKey.CENTERS.value)
    page.setProperty("semanticKey", NavKey.CENTERS.value)
    page.setProperty("usabilityRole", "scrollable_shell_page")
    page.setAccessibleName("Shell centers page")

    content = QWidget()
    content.setObjectName("centersContent")
    root = QVBoxLayout(content)
    root.setContentsMargins(28, 24, 28, 24)
    root.setSpacing(14)
    title = QLabel("管理中心 / Centers")
    title.setObjectName("centersTitle")
    title.setStyleSheet(page_title_qss())
    root.addWidget(title)
    subtitle = QLabel("统一查看 Project、Data、Task、Report、Environment 和 Packaging 的本地状态；不会执行 release build 或外部安装。")
    subtitle.setObjectName("centersSubtitle")
    subtitle.setWordWrap(True)
    root.addWidget(subtitle)

    tabs = QTabBar()
    tabs.setObjectName("centersSecondaryNav")
    tabs.setProperty("buttonBehavior", "switches_between_shell_center_pages")
    stack = QStackedWidget()
    stack.setObjectName("centersContentStack")
    pages = (
        ("project", "Project Center", _project_center_page(project_center)),
        ("data", "Data Center", _data_center_page(data_center, project_center)),
        ("task", "Task Center", _task_center_page(task_center)),
        ("report", "Report Center", _report_center_page(project_center, data_center, task_center)),
        ("environment", "Environment Center", _environment_center_page(project_center)),
        ("packaging", "Packaging Center", _packaging_center_page(project_center)),
    )
    for key, label, widget in pages:
        tabs.addTab(label)
        tabs.setTabData(tabs.count() - 1, key)
        stack.addWidget(widget)
    tabs.currentChanged.connect(stack.setCurrentIndex)
    root.addWidget(tabs)
    root.addWidget(stack)
    root.addStretch(1)
    page.setWidget(content)
    return page


def _project_center_page(project_center: ProjectCenter) -> QWidget:
    page = _base_center_page("projectCenterPage", "project")
    output = _readonly_output("projectCenterStatusText")
    page.layout().addWidget(_summary_card("Project Center", "读取最近项目，或创建 testing-level 项目索引用于验证 Project Center 写入链路。"))
    row = _button_row()
    refresh = _center_button("刷新项目列表", "centersRefreshProjectsButton", "calls_project_center_recent_projects")
    create = _center_button("创建测试项目记录", "centersCreateProjectRecordButton", "calls_project_center_create_project_and_writes_projects_index")
    row.addWidget(refresh)
    row.addWidget(create)
    row.addStretch(1)
    page.layout().addLayout(row)
    page.layout().addWidget(output)

    def render() -> None:
        records = project_center.recent_projects(limit=20)
        output.setPlainText("\n".join(record.display_label() for record in records) or "暂无项目记录。")

    def create_record() -> None:
        record = project_center.create_project(project_name=f"Centers Test {uuid4().hex[:6]}", project_type="bioinformatics", status="testing")
        output.setPlainText(f"created_project_id={record.project_id}\nprojects_index={project_center.storage_path}")

    refresh.clicked.connect(render)
    create.clicked.connect(create_record)
    render()
    return page


def _data_center_page(data_center: DataCenter, project_center: ProjectCenter) -> QWidget:
    page = _base_center_page("dataCenterPage", "data")
    output = _readonly_output("dataCenterStatusText")
    page.layout().addWidget(_summary_card("Data Center", "读取本地数据资产索引；导出按钮只写 index summary，不移动或修改原始数据。"))
    row = _button_row()
    refresh = _center_button("刷新数据资产", "centersRefreshDataButton", "calls_data_center_list_assets")
    export = _center_button("导出数据资产索引", "centersExportDataIndexButton", "writes_data_center_index_summary_artifact")
    row.addWidget(refresh)
    row.addWidget(export)
    row.addStretch(1)
    page.layout().addLayout(row)
    page.layout().addWidget(output)

    def render() -> None:
        assets = data_center.list_assets()
        output.setPlainText("\n".join(f"{asset.project_id} · {asset.module} · {asset.data_type} · {asset.status}" for asset in assets) or "暂无数据资产。")

    def export_index() -> None:
        assets = data_center.list_assets()
        path = _center_artifact_root(project_center) / "data_center_index_summary.json"
        _write_json(path, {"asset_count": len(assets), "assets": [asdict(asset) for asset in assets]})
        output.setPlainText(f"data_center_index_summary={path}\nasset_count={len(assets)}")

    refresh.clicked.connect(render)
    export.clicked.connect(export_index)
    render()
    return page


def _task_center_page(task_center: TaskCenter) -> QWidget:
    page = _base_center_page("taskCenterPage", "task")
    output = _readonly_output("taskCenterStatusText")
    page.layout().addWidget(_summary_card("Task Center", "查看任务索引；测试任务按钮只写本地 testing task record，不启动真实分析。"))
    row = _button_row()
    refresh = _center_button("刷新任务列表", "centersRefreshTasksButton", "calls_task_center_list_tasks")
    create = _center_button("创建测试任务记录", "centersCreateTaskButton", "calls_task_center_register_testing_task")
    row.addWidget(refresh)
    row.addWidget(create)
    row.addStretch(1)
    page.layout().addLayout(row)
    page.layout().addWidget(output)

    def render() -> None:
        tasks = task_center.list_tasks(limit=30)
        output.setPlainText("\n".join(task.display_label() for task in tasks) or "暂无任务记录。")

    def create_task() -> None:
        task = task_center.register_task(f"centers-task-{uuid4().hex[:8]}", TaskType.IMPORT, "shell", "Centers testing task", status=TaskStatus.PENDING, summary="Testing-only shell center task.")
        output.setPlainText(f"created_task_id={task.task_id}\ntasks_index={task_center.storage_path}")

    refresh.clicked.connect(render)
    create.clicked.connect(create_task)
    render()
    return page


def _report_center_page(project_center: ProjectCenter, data_center: DataCenter, task_center: TaskCenter) -> QWidget:
    page = _base_center_page("reportCenterPage", "report")
    output = _readonly_output("reportCenterStatusText")
    page.layout().addWidget(_summary_card("Report Center", "生成 report center index summary；不生成正式报告，不打开 report-ready gate。"))
    row = _button_row()
    build = _center_button("生成报告中心索引", "centersBuildReportIndexButton", "writes_report_center_index_summary_artifact")
    row.addWidget(build)
    row.addStretch(1)
    page.layout().addLayout(row)
    page.layout().addWidget(output)

    def build_index() -> None:
        path = _center_artifact_root(project_center) / "report_center_index.json"
        payload = {
            "report_types": list(REPORT_TYPES),
            "project_count": len(project_center.list_projects(limit=None)),
            "data_asset_count": len(data_center.list_assets()),
            "task_count": len(task_center.list_tasks(limit=None)),
            "formal_report_ready": False,
        }
        _write_json(path, payload)
        output.setPlainText(json.dumps({"report_center_index": str(path), **payload}, ensure_ascii=False, indent=2))

    build.clicked.connect(build_index)
    output.setPlainText("尚未生成 report center index。")
    return page


def _environment_center_page(project_center: ProjectCenter) -> QWidget:
    page = _base_center_page("environmentCenterPage", "environment")
    output = _readonly_output("environmentCenterStatusText")
    page.layout().addWidget(_summary_card("Environment Center", "运行本地环境检测；只检测 Python、PySide6、R 路径和 storage root，不安装依赖。"))
    row = _button_row()
    check = _center_button("运行环境检测", "centersRunEnvironmentCheckButton", "calls_check_local_environment_and_writes_status_artifact")
    row.addWidget(check)
    row.addStretch(1)
    page.layout().addLayout(row)
    page.layout().addWidget(output)

    def run_check() -> None:
        status = check_local_environment()
        path = _center_artifact_root(project_center) / "environment_status.json"
        _write_json(path, asdict(status))
        output.setPlainText(json.dumps({"environment_status": str(path), **asdict(status)}, ensure_ascii=False, indent=2))

    check.clicked.connect(run_check)
    output.setPlainText("尚未运行环境检测。")
    return page


def _packaging_center_page(project_center: ProjectCenter) -> QWidget:
    page = _base_center_page("packagingCenterPage", "packaging")
    output = _readonly_output("packagingCenterStatusText")
    page.layout().addWidget(_summary_card("Packaging Center", "只生成 release build preflight；不会执行 package_app、不会签名、不会启动 .app。"))
    row = _button_row()
    preflight = _center_button("生成打包预检", "centersBuildPackagingPreflightButton", "writes_packaging_preflight_artifact")
    build = _center_button("执行 release build", "centersRunReleaseBuildButton", "disabled_release_build_requires_explicit_release_build_command", enabled=False, disabled_reason="release_build_execution_not_allowed_from_centers_preview")
    row.addWidget(preflight)
    row.addWidget(build)
    row.addStretch(1)
    page.layout().addLayout(row)
    page.layout().addWidget(output)

    def build_preflight() -> None:
        path = _center_artifact_root(project_center) / "packaging_preflight.json"
        payload = {
            "python_executable": sys.executable,
            "project_index": str(project_center.storage_path),
            "release_build_allowed": False,
            "disabled_reason": "release_build_execution_not_allowed_from_centers_preview",
            "expected_manual_command": "python3 scripts/package_app.py --output-dir dist --app-name BioMedPilot",
        }
        _write_json(path, payload)
        output.setPlainText(json.dumps({"packaging_preflight": str(path), **payload}, ensure_ascii=False, indent=2))

    preflight.clicked.connect(build_preflight)
    output.setPlainText("尚未生成打包预检。")
    return page


def _base_center_page(object_name: str, center_key: str) -> QWidget:
    page = QWidget()
    page.setObjectName(object_name)
    page.setProperty("centerKey", center_key)
    page.setProperty("navKey", NavKey.CENTERS.value)
    page.setProperty("semanticKey", NavKey.CENTERS.value)
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)
    return page


def _summary_card(title: str, body: str) -> QFrame:
    card = QFrame()
    card.setObjectName("centersSummaryCard")
    card.setStyleSheet(surface_card_qss("QFrame#centersSummaryCard"))
    layout = QVBoxLayout(card)
    heading = QLabel(title)
    heading.setStyleSheet(card_title_qss())
    text = QLabel(body)
    text.setWordWrap(True)
    layout.addWidget(heading)
    layout.addWidget(text)
    return card


def _button_row() -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(10)
    return row


def _center_button(text: str, object_name: str, behavior: str, *, enabled: bool = True, disabled_reason: str = "") -> QPushButton:
    button = QPushButton(text)
    button.setObjectName(object_name)
    button.setEnabled(enabled)
    button.setProperty("buttonBehavior", behavior)
    button.setProperty("formalActionEnabled", False)
    button.setProperty("fileWriteAllowed", "writes_" in behavior or "register" in behavior or "create" in behavior)
    button.setProperty("navKey", NavKey.CENTERS.value)
    button.setProperty("semanticKey", NavKey.CENTERS.value)
    if not enabled:
        button.setProperty("disabledReason", disabled_reason or behavior)
        button.setToolTip(disabled_reason or behavior)
    return button


def _readonly_output(object_name: str) -> QPlainTextEdit:
    output = QPlainTextEdit()
    output.setObjectName(object_name)
    output.setReadOnly(True)
    output.setMinimumHeight(180)
    return output


def _center_artifact_root(project_center: ProjectCenter) -> Path:
    root = project_center.storage_path.expanduser().resolve().parents[1] / "centers"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
