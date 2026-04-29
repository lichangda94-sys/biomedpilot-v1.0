from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.models.protocol import ProjectProtocol
from app.meta_analysis.services.protocol_service import PROTOCOL_RELATIVE_PATHS, ProjectProtocolService


@dataclass(frozen=True)
class ProtocolPageState:
    title: str
    status_label: str
    description: str
    project_dir: str
    empty_state: str
    input_summary: str
    output_summary: str
    next_step: str
    testing_limitations: tuple[str, ...]
    protocol: ProjectProtocol | None
    readiness_status: str
    completeness_summary: str
    warnings: tuple[str, ...]
    output_paths: dict[str, str]
    search_strategy_preview: str


def initial_protocol_page_state(project_dir: Path | None = None) -> ProtocolPageState:
    return ProtocolPageState(
        title="Protocol / Research Question",
        status_label="Testing / Developer Preview",
        description="记录 Meta 分析研究题目、研究问题、PICO/PICOS、目标方法类型和可复制的检索式草稿。",
        project_dir=str(project_dir.expanduser().resolve()) if project_dir else "",
        empty_state="尚未保存 review_protocol.json。请先填写核心 PICO/PICOS 字段并保存 draft。",
        input_summary="研究题目、review question、PICO/PICOS、primary outcome、planned databases。",
        output_summary="protocol/review_protocol.json、protocol/search_terms_draft.json、protocol/search_strategy_preview.md、protocol/protocol_summary.md。",
        next_step="保存并人工复核检索式草稿后，进入 Literature Import。",
        testing_limitations=(
            "本模块只生成 draft search strategy，不执行真实数据库检索。",
            "PubMed / Web of Science / CNKI / WanFang 检索式必须由 reviewer 人工复核。",
        ),
        protocol=None,
        readiness_status="not_started",
        completeness_summary="No protocol artifact found.",
        warnings=("missing_protocol_artifact",),
        output_paths={},
        search_strategy_preview="",
    )


def protocol_page_state_from_project(project_dir: Path, *, service: ProjectProtocolService | None = None) -> ProtocolPageState:
    service = service or ProjectProtocolService()
    project_dir = project_dir.expanduser().resolve()
    protocol = service.load_protocol(project_dir)
    paths = service.protocol_paths(project_dir)
    output_paths = {
        "review_protocol": paths.review_protocol,
        "search_terms_draft": paths.search_terms_draft,
        "search_strategy_preview": paths.search_strategy_preview,
        "protocol_summary": paths.protocol_summary,
    }
    if protocol is None:
        state = initial_protocol_page_state(project_dir)
        return ProtocolPageState(**{**state.__dict__, "output_paths": output_paths})
    preview_path = Path(paths.search_strategy_preview)
    preview = preview_path.read_text(encoding="utf-8") if preview_path.exists() else ""
    missing_core = [warning for warning in protocol.warnings if warning.startswith("missing_")]
    completeness = "Core protocol fields complete." if not missing_core else f"Missing core fields: {', '.join(missing_core)}."
    return ProtocolPageState(
        title="Protocol / Research Question",
        status_label="Testing / Developer Preview",
        description="当前页面显示本地 protocol artifact、PICO/PICOS 完整性、检索式草稿路径和 reviewer warning。",
        project_dir=str(project_dir),
        empty_state="",
        input_summary="读取 protocol/review_protocol.json 中的研究问题、PICO/PICOS、方法类型和数据库计划。",
        output_summary="写入 protocol/review_protocol.json、search_terms_draft.json、search_strategy_preview.md 和 protocol_summary.md。",
        next_step="如果 readiness 为 ready/completed，请进入 Literature Import；如果有 warnings，请先人工补全 protocol。",
        testing_limitations=(
            "Developer Preview：检索式是 draft，不是投稿级最终检索式。",
            "本阶段不调用 PubMed / Web of Science / CNKI / WanFang API。",
        ),
        protocol=protocol,
        readiness_status=protocol.readiness_status,
        completeness_summary=completeness,
        warnings=protocol.warnings,
        output_paths=output_paths,
        search_strategy_preview=preview,
    )


try:
    from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QLabel = QLineEdit = QPushButton = QTextEdit = QVBoxLayout = QWidget = None


if QWidget is not None:

    class ProtocolPage(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._service = ProjectProtocolService()
            self._state = initial_protocol_page_state()
            root = QVBoxLayout(self)
            title = QLabel(f"{self._state.title} · {self._state.status_label}")
            title.setStyleSheet("font-size: 18px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(self._state.description)
            description.setWordWrap(True)
            root.addWidget(description)
            self._project_dir = QLineEdit()
            self._project_dir.setPlaceholderText("Meta project directory")
            root.addWidget(self._project_dir)
            self._project_title = QLineEdit()
            self._project_title.setPlaceholderText("研究题目")
            root.addWidget(self._project_title)
            self._review_question = QTextEdit()
            self._review_question.setPlaceholderText("研究问题 / review question")
            self._review_question.setMaximumHeight(90)
            root.addWidget(self._review_question)
            self._pico = QTextEdit()
            self._pico.setPlaceholderText("PICO/PICOS：population; intervention/exposure; comparator; outcomes; study design")
            self._pico.setMaximumHeight(100)
            root.addWidget(self._pico)
            self._method_profile = QLineEdit()
            self._method_profile.setPlaceholderText("Method profile, e.g. TREATMENT_EFFECT_META")
            root.addWidget(self._method_profile)
            save = QPushButton("Save Protocol Draft")
            save.clicked.connect(self._save)
            root.addWidget(save)
            self._summary = QLabel(self._state.empty_state)
            self._summary.setWordWrap(True)
            root.addWidget(self._summary)

        def _save(self) -> None:
            project_dir = Path(self._project_dir.text()).expanduser()
            pico_parts = [part.strip() for part in self._pico.toPlainText().split(";")]
            values = {
                "project_title": self._project_title.text(),
                "review_question": self._review_question.toPlainText(),
                "population": pico_parts[0] if len(pico_parts) > 0 else "",
                "intervention_or_exposure": pico_parts[1] if len(pico_parts) > 1 else "",
                "comparator": pico_parts[2] if len(pico_parts) > 2 else "",
                "outcomes": pico_parts[3] if len(pico_parts) > 3 else "",
                "study_design": pico_parts[4] if len(pico_parts) > 4 else "",
                "primary_outcome": pico_parts[3] if len(pico_parts) > 3 else "",
                "meta_analysis_type": self._method_profile.text(),
                "method_profile_id": self._method_profile.text(),
            }
            result = self._service.save_protocol(project_dir, values)
            self._summary.setText(
                f"{result.message}\n"
                f"readiness: {result.protocol.readiness_status}\n"
                f"warnings: {', '.join(result.warnings) if result.warnings else 'none'}\n"
                f"preview: {result.artifact_paths.search_strategy_preview}"
            )

else:

    class ProtocolPage:  # type: ignore[no-redef]
        pass
