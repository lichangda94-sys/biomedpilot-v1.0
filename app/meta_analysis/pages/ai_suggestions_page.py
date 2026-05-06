from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.models.ai_suggestion import SUGGESTION_TYPES, TARGET_TYPES
from app.meta_analysis.services.ai_assisted_extraction_queue_service import (
    AI_EXTRACTION_QUEUE_SCHEMA_VERSION,
    AIAssistedExtractionQueueService,
)
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class AISuggestionsPageState:
    title: str
    description: str
    status_label: str
    input_summary: str
    output_summary: str
    next_step: str
    warning_summary: str
    queue_columns: tuple[str, ...]
    target_type_options: tuple[str, ...]
    suggestion_type_options: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    safety_rules: tuple[str, ...]
    empty_state: str


@dataclass(frozen=True)
class AIExtractionSuggestionQueuePageState:
    title: str
    status_label: str
    project_dir: str
    queue_schema_version: str
    queue_path: str
    validation_path: str
    application_path: str
    suggestion_count: int
    pending_count: int
    accepted_count: int
    rejected_count: int
    edited_count: int
    source_options: tuple[str, ...]
    review_actions: tuple[str, ...]
    safety_rules: tuple[str, ...]
    empty_state: str
    warnings: tuple[str, ...] = ()


def initial_ai_suggestions_state() -> AISuggestionsPageState:
    feature = get_feature("meta-ai-assisted-review")
    return AISuggestionsPageState(
        title="AI Suggestions Queue / AI 辅助建议队列",
        description="AI 仅生成候选建议；必须由人工 accept / reject / edit，并且 accepted 后还需要明确 apply。AI 不会直接覆盖 screening、extraction、analysis 或 report 正式数据。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
        input_summary="输入：本地/mock suggestion provider 或受控 AI adapter 生成的候选建议。",
        output_summary="输出：ai_suggestions 队列和人工审核 action task；不会直接改正式数据。",
        next_step="下一步：人工 accept / reject / edit；accepted 后仍需明确 apply。",
        warning_summary="pending、rejected、edited 或未 apply 的 suggestion 不能进入正式数据。",
        queue_columns=(
            "suggestion_id",
            "suggestion_type",
            "target_type",
            "target_id",
            "suggested_value",
            "rationale",
            "confidence",
            "status",
            "reviewer_action",
        ),
        target_type_options=TARGET_TYPES,
        suggestion_type_options=SUGGESTION_TYPES,
        allowed_actions=("accept", "reject", "edit", "apply_accepted"),
        safety_rules=(
            "pending_suggestion_cannot_enter_formal_data",
            "rejected_suggestion_cannot_enter_formal_data",
            "accepted_suggestion_requires_explicit_apply",
            "ai_never_overwrites_screening_extraction_analysis_results",
        ),
        empty_state="当前没有 AI suggestions。可由 mock/local provider 生成 testing suggestion。",
    )


def ai_extraction_suggestion_queue_state_from_project(
    project_dir: Path,
    *,
    service: AIAssistedExtractionQueueService | None = None,
) -> AIExtractionSuggestionQueuePageState:
    project_dir = project_dir.expanduser().resolve()
    service = service or AIAssistedExtractionQueueService()
    suggestions = service.list_extraction_suggestions(project_dir)
    pending = [item for item in suggestions if item.status == "pending"]
    accepted = [item for item in suggestions if item.status == "accepted"]
    rejected = [item for item in suggestions if item.status == "rejected"]
    edited = [item for item in suggestions if item.status == "edited"]
    warnings: list[str] = []
    if not suggestions:
        warnings.append("no_ai_extraction_suggestions")
    return AIExtractionSuggestionQueuePageState(
        title="AI-assisted Extraction Queue / AI 辅助提取建议",
        status_label="Testing / suggestion-only",
        project_dir=str(project_dir),
        queue_schema_version=AI_EXTRACTION_QUEUE_SCHEMA_VERSION,
        queue_path=str(service.queue_path(project_dir)),
        validation_path=str(service.validation_path(project_dir)),
        application_path=str(service.application_path(project_dir)),
        suggestion_count=len(suggestions),
        pending_count=len(pending),
        accepted_count=len(accepted),
        rejected_count=len(rejected),
        edited_count=len(edited),
        source_options=("abstract", "parsed_pdf_text", "manual_text"),
        review_actions=("accept", "reject", "edit", "apply_accepted_as_manual_draft"),
        safety_rules=(
            "AI/PDF parsing output is suggestion only.",
            "Pending/rejected/edited suggestions cannot write extraction drafts.",
            "Accepted suggestions apply only as manual extraction draft effect rows.",
            "No analysis-ready dataset, statistics run, or PRISMA update is created.",
        ),
        empty_state="当前没有 AI extraction suggestions。可从 abstract、parsed PDF text 或手动文本生成 suggestion。",
        warnings=tuple(warnings),
    )


try:
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QLabel = QVBoxLayout = QWidget = None


if QWidget is not None:

    class AISuggestionsPage(QWidget):
        def __init__(self) -> None:
            super().__init__()
            state = initial_ai_suggestions_state()
            root = QVBoxLayout(self)
            title = QLabel(state.title)
            title.setStyleSheet("font-size: 20px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(state.description)
            description.setWordWrap(True)
            root.addWidget(description)
            root.addWidget(QLabel(f"功能状态：{state.status_label}"))
            extraction_state = ai_extraction_suggestion_queue_state_from_project(Path.cwd())
            extraction_label = QLabel(
                "\n".join(
                    [
                        f"{extraction_state.title} · {extraction_state.status_label}",
                        f"Suggestions: {extraction_state.suggestion_count}",
                        f"Review actions: {' / '.join(extraction_state.review_actions)}",
                        "Accepted suggestion 也只会写入 manual extraction draft，不会进入 analysis-ready dataset。",
                    ]
                )
            )
            extraction_label.setWordWrap(True)
            root.addWidget(extraction_label)
            root.addWidget(QLabel(state.empty_state))
            root.addStretch(1)

else:

    class AISuggestionsPage:  # type: ignore[no-redef]
        pass
