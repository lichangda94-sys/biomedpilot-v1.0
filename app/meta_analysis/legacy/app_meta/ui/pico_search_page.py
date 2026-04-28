from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app_meta.core.project_state import MetaProjectState
from app_meta.ui.components import SectionCard
from app_meta.ui.theme import Theme


REVIEW_TYPES = (
    "Treatment comparative meta-analysis",
    "Biomarker prevalence / association meta-analysis",
    "Continuous biomarker difference meta-analysis",
    "Exposure level and disease risk meta-analysis",
    "Longitudinal exposure and incident risk meta-analysis",
)

DATABASES = (
    "PubMed",
    "Embase",
    "Web of Science",
    "Cochrane Library",
    "Scopus",
    "CNKI",
    "Wanfang",
    "VIP",
)

READINESS_ITEMS = (
    "Research question defined",
    "PICO complete",
    "Review type selected",
    "Primary outcome defined",
    "Database selected",
    "Search query generated",
)


class PicoSearchPage(QWidget):
    def __init__(self, project_state: MetaProjectState, on_action: Callable[[str], None]) -> None:
        super().__init__()
        self._project_state = project_state
        self._on_action = on_action
        self._database_checks: dict[str, QCheckBox] = {}
        self._readiness_labels: dict[str, QLabel] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(_scroll_stylesheet())
        root.addWidget(scroll, 1)

        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 2, 0)
        layout.setSpacing(16)
        layout.addLayout(self._header())

        columns = QHBoxLayout()
        columns.setSpacing(16)
        columns.addLayout(self._left_column(), 1)
        columns.addLayout(self._right_column())
        layout.addLayout(columns, 1)
        layout.addStretch(1)
        scroll.setWidget(page)

    def _header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("PICO / Search")
        title.setObjectName("pageTitle")
        subtitle = QLabel("定义研究问题、PICO 框架、检索数据库与初始布尔检索式")
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        header.addWidget(title)
        header.addWidget(subtitle)
        return header

    def _left_column(self) -> QVBoxLayout:
        column = QVBoxLayout()
        column.setSpacing(16)
        column.addWidget(self._research_question_card())
        column.addWidget(self._pico_card())
        column.addWidget(self._review_database_card())
        column.addWidget(self._search_terms_card())
        column.addWidget(self._query_preview_card())
        return column

    def _right_column(self) -> QVBoxLayout:
        column = QVBoxLayout()
        column.setSpacing(16)
        column.setContentsMargins(0, 0, 0, 0)
        column.addWidget(self._readiness_card())
        column.addWidget(self._tips_card())
        column.addWidget(self._action_card())
        column.addStretch(1)
        return column

    def _research_question_card(self) -> SectionCard:
        card = SectionCard("Research Question")
        form = _form_layout()

        self.project_title = self._line_edit(self._project_state.project_name)
        self.condition = self._line_edit("重症肺炎")
        self.intervention = self._line_edit("糖皮质激素")
        self.comparator = self._line_edit("标准治疗 / 安慰剂")
        self.outcome = self._line_edit(self._project_state.current_outcome)
        self.population = self._line_edit("成人重症肺炎患者")

        for label, field in (
            ("Project title", self.project_title),
            ("Disease / condition", self.condition),
            ("Intervention / exposure", self.intervention),
            ("Comparator", self.comparator),
            ("Outcome", self.outcome),
            ("Population", self.population),
        ):
            form.addRow(_form_label(label), field)
        card.layout.addLayout(form)
        return card

    def _pico_card(self) -> SectionCard:
        card = SectionCard("PICO Framework")
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(12)

        self.p_population = self._text_edit("Adults with severe pneumonia requiring hospital-based care", 74)
        self.p_intervention = self._text_edit(
            "Systemic corticosteroids, including hydrocortisone or methylprednisolone",
            74,
        )
        self.p_comparator = self._text_edit("Usual care, placebo, or no corticosteroid treatment", 74)
        self.p_outcomes = self._text_edit("All-cause mortality; clinical cure; ICU length of stay; adverse events", 74)

        for index, (label, widget) in enumerate(
            (
                ("P: Population", self.p_population),
                ("I/E: Intervention or Exposure", self.p_intervention),
                ("C: Comparator", self.p_comparator),
                ("O: Outcomes", self.p_outcomes),
            )
        ):
            grid.addWidget(_field_block(label, widget), index // 2, index % 2)
        card.layout.addLayout(grid)
        return card

    def _review_database_card(self) -> SectionCard:
        card = SectionCard("Review Type and Databases")
        self.review_type = QComboBox()
        self.review_type.addItems(REVIEW_TYPES)
        self.review_type.setCurrentText(REVIEW_TYPES[0])
        self.review_type.setMinimumHeight(38)
        card.layout.addWidget(_field_block("Review type", self.review_type))

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        for index, name in enumerate(DATABASES):
            check = QCheckBox(name)
            check.setChecked(True)
            check.setStyleSheet(f"color: {Theme.text}; spacing: 8px;")
            self._database_checks[name] = check
            grid.addWidget(check, index // 4, index % 4)
        card.layout.addLayout(grid)
        return card

    def _search_terms_card(self) -> SectionCard:
        card = SectionCard("Search Terms")
        form = _form_layout()
        self.disease_terms = self._text_edit(
            "severe pneumonia OR critical pneumonia OR severe community-acquired pneumonia",
            88,
        )
        self.intervention_terms = self._text_edit(
            "corticosteroid OR glucocorticoid OR hydrocortisone OR methylprednisolone",
            88,
        )
        self.outcome_terms = self._text_edit("mortality OR death OR survival", 88)
        self.study_type_terms = self._text_edit("randomized controlled trial OR clinical trial OR cohort", 88)

        for label, field in (
            ("Disease terms", self.disease_terms),
            ("Intervention/exposure terms", self.intervention_terms),
            ("Outcome terms", self.outcome_terms),
            ("Study type terms", self.study_type_terms),
        ):
            form.addRow(_form_label(label), field)
        card.layout.addLayout(form)
        return card

    def _query_preview_card(self) -> SectionCard:
        card = SectionCard("Boolean Query Preview")
        actions = QHBoxLayout()
        actions.setSpacing(10)
        generate = QPushButton("Generate Draft Query")
        generate.setObjectName("primaryButton")
        copy = QPushButton("Copy Query")
        generate.clicked.connect(self.generate_query)
        copy.clicked.connect(self.copy_query)
        actions.addWidget(generate)
        actions.addWidget(copy)
        actions.addStretch(1)
        card.layout.addLayout(actions)

        self.query_preview = QTextEdit()
        self.query_preview.setMinimumHeight(160)
        self.query_preview.setMaximumHeight(190)
        self.query_preview.setPlaceholderText("Generated Boolean query will appear here.")
        self.query_preview.setStyleSheet(_input_stylesheet())
        card.layout.addWidget(self.query_preview)
        return card

    def _readiness_card(self) -> SectionCard:
        card = SectionCard("Protocol readiness")
        card.setFixedWidth(320)
        for key in READINESS_ITEMS:
            row = QHBoxLayout()
            row.setSpacing(8)
            dot = QLabel("●")
            dot.setFixedWidth(16)
            label = QLabel(key)
            label.setWordWrap(True)
            label.setStyleSheet(f"color: {Theme.text};")
            row.addWidget(dot)
            row.addWidget(label, 1)
            card.layout.addLayout(row)
            self._readiness_labels[key] = dot

        self.validation_message = QLabel("Protocol setup looks ready for a draft search strategy.")
        self.validation_message.setWordWrap(True)
        self.validation_message.setStyleSheet(
            f"background: {Theme.success_soft}; color: {Theme.success}; border-radius: 10px; padding: 10px;"
        )
        card.layout.addWidget(self.validation_message)
        self._update_readiness({})
        return card

    def _tips_card(self) -> SectionCard:
        card = SectionCard("Search strategy tips")
        card.setFixedWidth(320)
        for tip in (
            "Use both MeSH and free-text terms",
            "Record exact database search dates",
            "Save original export files",
            "Keep deduplication decisions auditable",
        ):
            label = QLabel(f"• {tip}")
            label.setObjectName("smallMuted")
            label.setWordWrap(True)
            card.layout.addWidget(label)
        return card

    def _action_card(self) -> SectionCard:
        card = SectionCard("Actions")
        card.setFixedWidth(320)
        self.action_message = QLabel("Draft changes are local to this session.")
        self.action_message.setObjectName("smallMuted")
        self.action_message.setWordWrap(True)
        card.layout.addWidget(self.action_message)

        for index, (label, handler) in enumerate(
            (
                ("Save Draft", self.save_draft),
                ("Validate", self.validate_protocol),
                ("Mark as Complete", self.mark_complete),
            )
        ):
            button = QPushButton(label)
            button.setMinimumHeight(38)
            if index == 2:
                button.setObjectName("primaryButton")
            button.clicked.connect(lambda checked=False, callback=handler: callback())
            card.layout.addWidget(button)
        return card

    def save_draft(self) -> None:
        self.action_message.setStyleSheet(f"color: {Theme.primary};")
        self.action_message.setText("Draft saved in the current demo session.")
        self._on_action("Save Draft")

    def mark_complete(self) -> None:
        self.validate_protocol(show_success=False)
        if all(self._readiness().values()):
            self.action_message.setStyleSheet(f"color: {Theme.success};")
            self.action_message.setText("PICO/Search marked as complete for this demo workflow.")
            self._on_action("Mark as Complete")

    def generate_query(self) -> None:
        groups = [
            self._normalized_terms(self.disease_terms),
            self._normalized_terms(self.intervention_terms),
            self._normalized_terms(self.outcome_terms),
            self._normalized_terms(self.study_type_terms),
        ]
        query = " AND\n".join(f"({group})" for group in groups if group)
        self.query_preview.setPlainText(query)
        self._on_action("Generate Draft Query")
        self.validate_protocol(show_success=False)

    def copy_query(self) -> None:
        self.query_preview.selectAll()
        self.query_preview.copy()
        self.action_message.setStyleSheet(f"color: {Theme.primary};")
        self.action_message.setText("Query copied to clipboard.")
        self._on_action("Copy Query")

    def validate_protocol(self, show_success: bool = True) -> None:
        readiness = self._readiness()
        missing = [label for label, is_ready in readiness.items() if not is_ready]
        self._update_readiness(readiness)
        if missing:
            self.validation_message.setStyleSheet(
                f"background: {Theme.danger_soft}; color: {Theme.danger}; border-radius: 10px; padding: 10px;"
            )
            self.validation_message.setText("Missing required items: " + "; ".join(missing))
            self.action_message.setStyleSheet(f"color: {Theme.danger};")
            self.action_message.setText("Validation needs attention before completion.")
        else:
            self.validation_message.setStyleSheet(
                f"background: {Theme.success_soft}; color: {Theme.success}; border-radius: 10px; padding: 10px;"
            )
            self.validation_message.setText("Protocol setup looks complete. Ready for search strategy review.")
            self.action_message.setStyleSheet(f"color: {Theme.success};")
            self.action_message.setText("Validation passed.")
            if show_success:
                self._on_action("Validate")

    def _readiness(self) -> dict[str, bool]:
        return {
            "Research question defined": all(
                self._has_text(field)
                for field in (self.project_title, self.condition, self.intervention, self.comparator, self.population)
            ),
            "PICO complete": all(
                self._has_text(field)
                for field in (self.p_population, self.p_intervention, self.p_comparator, self.p_outcomes)
            ),
            "Review type selected": bool(self.review_type.currentText()),
            "Primary outcome defined": self._has_text(self.outcome),
            "Database selected": any(check.isChecked() for check in self._database_checks.values()),
            "Search query generated": bool(self.query_preview.toPlainText().strip()),
        }

    def _update_readiness(self, readiness: dict[str, bool]) -> None:
        if not readiness:
            readiness = self._readiness()
        for label, dot in self._readiness_labels.items():
            color = Theme.success if readiness.get(label, False) else Theme.muted_light
            dot.setStyleSheet(f"color: {color}; font-size: 16px;")

    def _line_edit(self, text: str = "") -> QLineEdit:
        field = QLineEdit()
        field.setText(text)
        field.setMinimumHeight(38)
        field.setStyleSheet(_input_stylesheet())
        return field

    def _text_edit(self, text: str = "", height: int = 78) -> QTextEdit:
        field = QTextEdit()
        field.setPlainText(text)
        field.setMinimumHeight(height)
        field.setMaximumHeight(height + 28)
        field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        field.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        field.setStyleSheet(_input_stylesheet())
        return field

    def _has_text(self, widget: QLineEdit | QTextEdit) -> bool:
        if isinstance(widget, QLineEdit):
            return bool(widget.text().strip())
        return bool(widget.toPlainText().strip())

    def _normalized_terms(self, widget: QTextEdit) -> str:
        return " ".join(widget.toPlainText().strip().split())


def _form_layout() -> QFormLayout:
    form = QFormLayout()
    form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
    form.setHorizontalSpacing(18)
    form.setVerticalSpacing(12)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
    return form


def _form_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("smallMuted")
    label.setMinimumWidth(160)
    return label


def _field_block(label: str, widget: QWidget) -> QWidget:
    block = QWidget()
    block.setStyleSheet("background: transparent;")
    layout = QVBoxLayout(block)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(7)
    title = QLabel(label)
    title.setStyleSheet(f"font-weight: 700; color: {Theme.text};")
    layout.addWidget(title)
    layout.addWidget(widget)
    return block


def _input_stylesheet() -> str:
    return (
        f"background: {Theme.card}; border: 1px solid {Theme.border}; "
        f"border-radius: {Theme.radius_small}px; padding: 8px 10px;"
    )


def _scroll_stylesheet() -> str:
    return f"""
    QScrollArea {{
        border: 0;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 2px 0 2px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {Theme.border};
        border-radius: 4px;
        min-height: 36px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    """
