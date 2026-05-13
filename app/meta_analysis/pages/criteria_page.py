from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.models.criteria import CriteriaSet
from app.meta_analysis.services.criteria_service import CRITERIA_PATHS, CriteriaBuilderService
from app.meta_analysis.services.exclusion_criteria_library_service import (
    EXCLUSION_CRITERIA_LIBRARY_SCHEMA_VERSION,
    ExclusionCriteriaLibraryService,
)
from app.meta_analysis.ui_text import (
    CRITERIA_DESCRIPTION_ZH,
    CRITERIA_READINESS_STATUS_ZH,
    CRITERIA_SECTION_ZH,
    CRITERIA_TITLE_ZH,
    DEVELOPER_INFO_TITLE_ZH,
    INTERNAL_BETA_STATUS_ZH,
)
from app.version import APP_VERSION


@dataclass(frozen=True)
class CriteriaPageState:
    title: str
    status_label: str
    description: str
    project_dir: str
    empty_state: str
    input_summary: str
    output_summary: str
    next_step: str
    criteria: CriteriaSet | None
    inclusion_count: int
    exclusion_count: int
    readiness_status: str
    warnings: tuple[str, ...]
    output_paths: dict[str, str]
    screening_hints: tuple[str, ...]
    fulltext_hints: tuple[str, ...]
    testing_limitations: tuple[str, ...]
    exclusion_library_schema_version: str = ""
    exclusion_library_status: str = "not_started"
    exclusion_library_reason_count: int = 0
    exclusion_library_enabled_count: int = 0
    prisma_reason_map_path: str = ""
    title_zh: str = CRITERIA_TITLE_ZH
    status_label_zh: str = "内部测试"
    description_zh: str = CRITERIA_DESCRIPTION_ZH
    input_summary_zh: str = "输入：Protocol / PICO-PICOS、默认标准和 reviewer 自定义标准。"
    output_summary_zh: str = "输出：纳入标准、排除标准和 criteria summary。"
    next_step_zh: str = "下一步：使用标准开展标题摘要筛选。"
    empty_state_zh: str = "尚未生成纳入与排除标准。请先确认研究问题，再保存 criteria draft。"
    readiness_status_zh: str = "未开始"
    inclusion_title_zh: str = CRITERIA_SECTION_ZH["inclusion"]
    exclusion_title_zh: str = CRITERIA_SECTION_ZH["exclusion"]
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH


def initial_criteria_page_state(project_dir: Path | None = None) -> CriteriaPageState:
    output_paths = _output_paths(project_dir.expanduser().resolve()) if project_dir else {}
    return CriteriaPageState(
        title="Criteria Builder",
        status_label="Testing / Developer Preview",
        description="构建 inclusion / exclusion criteria，用于指导 title/abstract screening、full-text screening 和 PRISMA reason counts。",
        project_dir=str(project_dir.expanduser().resolve()) if project_dir else "",
        empty_state="尚未生成 criteria artifacts。请先确认 Protocol / PICO-PICOS，再保存 criteria draft。",
        input_summary="输入：Protocol / PICO-PICOS、默认纳入排除标准和 reviewer 自定义标准。",
        output_summary="输出：criteria/inclusion_criteria.json、criteria/exclusion_criteria.json、criteria/criteria_summary.md。",
        next_step="下一步：Title / Abstract Screening。",
        criteria=None,
        inclusion_count=0,
        exclusion_count=0,
        readiness_status="not_started",
        warnings=("missing_criteria_artifacts",),
        output_paths=output_paths,
        screening_hints=(),
        fulltext_hints=(),
        testing_limitations=(
            "Criteria 只作为 reviewer 决策提示，不自动纳入或排除文献。",
            "Developer Preview：PRISMA reason counts 仍依赖后续 screening/full-text decisions。",
        ),
        exclusion_library_schema_version=EXCLUSION_CRITERIA_LIBRARY_SCHEMA_VERSION,
        prisma_reason_map_path=str(project_dir.expanduser().resolve() / "criteria" / "prisma_reason_map_v1.json") if project_dir else "",
        title_zh=CRITERIA_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=CRITERIA_DESCRIPTION_ZH,
        readiness_status_zh=CRITERIA_READINESS_STATUS_ZH["not_started"],
    )


def criteria_page_state_from_project(
    project_dir: Path,
    *,
    service: CriteriaBuilderService | None = None,
    exclusion_library_service: ExclusionCriteriaLibraryService | None = None,
) -> CriteriaPageState:
    service = service or CriteriaBuilderService()
    exclusion_library_service = exclusion_library_service or ExclusionCriteriaLibraryService()
    project_dir = project_dir.expanduser().resolve()
    criteria = service.load_criteria(project_dir)
    library = exclusion_library_service.load_library(project_dir)
    output_paths = _output_paths(project_dir)
    if criteria is None:
        base = initial_criteria_page_state(project_dir)
        return CriteriaPageState(
            **{
                **base.__dict__,
                "exclusion_library_status": library.status if library else "not_started",
                "exclusion_library_reason_count": len(library.reasons) if library else 0,
                "exclusion_library_enabled_count": len([reason for reason in library.reasons if reason.enabled]) if library else 0,
                "prisma_reason_map_path": str(exclusion_library_service.prisma_reason_map_path(project_dir)),
            }
        )
    return CriteriaPageState(
        title="Criteria Builder",
        status_label="Testing / Developer Preview",
        description="当前页面显示 inclusion / exclusion criteria、criteria summary 路径和后续 screening/full-text hints。",
        project_dir=str(project_dir),
        empty_state="",
        input_summary="读取 criteria JSON artifacts，并引用 Protocol / PICO-PICOS。",
        output_summary="criteria_summary.md 可供 tester 和 reviewer 复制到 screening/full-text 工作流说明中。",
        next_step="进入 Title / Abstract Screening，并按 criteria 记录 exclusion reasons。",
        criteria=criteria,
        inclusion_count=len(criteria.inclusion_criteria),
        exclusion_count=len(criteria.exclusion_criteria),
        readiness_status=criteria.readiness_status,
        warnings=criteria.warnings,
        output_paths=output_paths,
        screening_hints=service.criteria_hints(project_dir, stage="title_abstract"),
        fulltext_hints=service.criteria_hints(project_dir, stage="full_text"),
        testing_limitations=(
            "Criteria 不会自动修改 screening_decisions 或 fulltext decisions。",
            "如 criteria 与 protocol 不一致，必须由 reviewer 人工修订。",
            "Exclusion Criteria Library v1 只提供结构化原因和 PRISMA mapping，不自动排除文献。",
        ),
        exclusion_library_schema_version=EXCLUSION_CRITERIA_LIBRARY_SCHEMA_VERSION,
        exclusion_library_status=library.status if library else "not_started",
        exclusion_library_reason_count=len(library.reasons) if library else 0,
        exclusion_library_enabled_count=len([reason for reason in library.reasons if reason.enabled]) if library else 0,
        prisma_reason_map_path=str(exclusion_library_service.prisma_reason_map_path(project_dir)),
        title_zh=CRITERIA_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=CRITERIA_DESCRIPTION_ZH,
        readiness_status_zh=CRITERIA_READINESS_STATUS_ZH.get(criteria.readiness_status, criteria.readiness_status),
    )


def _output_paths(project_dir: Path) -> dict[str, str]:
    return {key: str(project_dir / relative) for key, relative in CRITERIA_PATHS.items()}


try:
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QLabel = QVBoxLayout = QWidget = None


if QWidget is not None:

    class CriteriaPage(QWidget):
        def __init__(self) -> None:
            super().__init__()
            state = initial_criteria_page_state()
            root = QVBoxLayout(self)
            title = QLabel(f"{state.title_zh} · {state.status_label_zh}")
            title.setStyleSheet("font-size: 18px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(state.description_zh)
            description.setWordWrap(True)
            root.addWidget(description)
            note = QLabel(f"{state.empty_state_zh}\n下一步：{state.next_step_zh}")
            note.setWordWrap(True)
            root.addWidget(note)

else:

    class CriteriaPage:  # type: ignore[no-redef]
        pass
