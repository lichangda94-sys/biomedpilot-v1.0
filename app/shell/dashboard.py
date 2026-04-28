from __future__ import annotations

from dataclasses import dataclass

from app.bioinformatics.workspace import bioinformatics_features
from app.meta_analysis.workspace import meta_analysis_features
from app.shared.environment.checks import EnvironmentStatus, check_local_environment
from app.shared.project_center.service import ProjectCenter, ProjectRecord
from app.shared.task_center.service import TaskCenter, TaskRecord


@dataclass(frozen=True)
class DashboardModel:
    product_name: str
    product_subtitle: str
    bioinformatics_features: tuple[str, ...]
    meta_analysis_features: tuple[str, ...]
    recent_projects: tuple[ProjectRecord, ...]
    recent_tasks: tuple[TaskRecord, ...]
    environment: EnvironmentStatus
    test_mode_label: str


def build_dashboard_model(
    project_center: ProjectCenter | None = None,
    task_center: TaskCenter | None = None,
) -> DashboardModel:
    project_center = project_center or ProjectCenter.default()
    task_center = task_center or TaskCenter.default()
    return DashboardModel(
        product_name="BioMedPilot / 医研智析",
        product_subtitle="统一入口，独立工作台：Bioinformatics Analysis 与 Meta Analysis",
        bioinformatics_features=tuple(item.name for item in bioinformatics_features()),
        meta_analysis_features=tuple(item.name for item in meta_analysis_features()),
        recent_projects=tuple(project_center.list_projects(limit=5)),
        recent_tasks=tuple(task_center.list_tasks(limit=5)),
        environment=check_local_environment(),
        test_mode_label="测试模式：UI 会标注已开放、测试中、待接入和暂未开放功能。",
    )

