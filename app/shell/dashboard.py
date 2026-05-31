from __future__ import annotations

from dataclasses import dataclass

from app.bioinformatics.workspace import bioinformatics_features
from app.labtools.workspace import labtools_features
from app.meta_analysis.workspace import meta_analysis_features
from app.shared.environment.checks import EnvironmentStatus, check_local_environment
from app.shared.project_center.service import ProjectCenter, ProjectRecord
from app.shared.task_center.service import TaskCenter, TaskRecord
from app.version import APP_CHANNEL, APP_VERSION


@dataclass(frozen=True)
class DashboardModel:
    product_name: str
    product_subtitle: str
    bioinformatics_features: tuple[str, ...]
    meta_analysis_features: tuple[str, ...]
    labtools_features: tuple[str, ...]
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
        product_subtitle=(
            "萤火虫 / Firefly 低保真全局壳层：Bioinformatics、Meta Analysis 与 LabTools · "
            f"{APP_VERSION} · 内部测试版 / {APP_CHANNEL}"
        ),
        bioinformatics_features=tuple(item.name for item in bioinformatics_features()),
        meta_analysis_features=tuple(item.name for item in meta_analysis_features()),
        labtools_features=(
            "通用计算器",
            "试剂制备",
            "实验记录",
            "外部图像引擎入口",
        ),
        recent_projects=tuple(project_center.list_projects(limit=5)),
        recent_tasks=tuple(task_center.list_tasks(limit=5)),
        environment=check_local_environment(),
        test_mode_label="测试模式：UI 会标注已开放、测试中、待接入和暂未开放功能。",
    )
