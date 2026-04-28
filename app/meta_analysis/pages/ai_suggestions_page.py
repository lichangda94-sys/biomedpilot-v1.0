from __future__ import annotations

from dataclasses import dataclass

from app.meta_analysis.models.ai_suggestion import SUGGESTION_TYPES, TARGET_TYPES
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class AISuggestionsPageState:
    title: str
    description: str
    status_label: str
    queue_columns: tuple[str, ...]
    target_type_options: tuple[str, ...]
    suggestion_type_options: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    safety_rules: tuple[str, ...]
    empty_state: str


def initial_ai_suggestions_state() -> AISuggestionsPageState:
    feature = get_feature("meta-ai-assisted-review")
    return AISuggestionsPageState(
        title="AI Suggestions Queue / AI 辅助建议队列",
        description="AI 仅生成候选建议；必须由人工 accept / reject / edit，并且 accepted 后还需要明确 apply。AI 不会直接覆盖 screening、extraction、analysis 或 report 正式数据。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
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
            root.addWidget(QLabel(state.empty_state))
            root.addStretch(1)

else:

    class AISuggestionsPage:  # type: ignore[no-redef]
        pass
