from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.models.protocol import ProjectProtocol
from app.meta_analysis.search import MetaSearchStrategyDraft, build_meta_search_strategy_draft
from app.meta_analysis.services.protocol_service import PROTOCOL_RELATIVE_PATHS, ProjectProtocolService


SEARCH_STRATEGY_DRAFT_RELATIVE_PATH = "protocol/search_strategy_draft.json"
SEARCH_STRATEGY_AUDIT_RELATIVE_PATH = "protocol/search_strategy_audit.json"


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
    search_strategy_summary: str
    search_execution_status: str
    local_model_status: str


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
            "PubMed / Web of Science / Embase / CNKI 检索式必须由 reviewer 人工复核。",
        ),
        protocol=None,
        readiness_status="not_started",
        completeness_summary="No protocol artifact found.",
        warnings=("missing_protocol_artifact",),
        output_paths={},
        search_strategy_preview="",
        search_strategy_summary="",
        search_execution_status="draft_only",
        local_model_status="not_available",
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
        "search_strategy_draft": str(project_dir / SEARCH_STRATEGY_DRAFT_RELATIVE_PATH),
        "search_strategy_audit": str(project_dir / SEARCH_STRATEGY_AUDIT_RELATIVE_PATH),
    }
    if protocol is None:
        state = initial_protocol_page_state(project_dir)
        return ProtocolPageState(**{**state.__dict__, "output_paths": output_paths})
    preview_path = Path(paths.search_strategy_preview)
    preview = preview_path.read_text(encoding="utf-8") if preview_path.exists() else ""
    search_draft_path = project_dir / SEARCH_STRATEGY_DRAFT_RELATIVE_PATH
    search_payload = _load_json_object(search_draft_path)
    search_summary = _search_strategy_summary_from_payload(search_payload)
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
            "当前仅生成检索式草稿，尚未执行在线检索。",
        ),
        protocol=protocol,
        readiness_status=protocol.readiness_status,
        completeness_summary=completeness,
        warnings=protocol.warnings,
        output_paths=output_paths,
        search_strategy_preview=preview,
        search_strategy_summary=search_summary,
        search_execution_status=str(search_payload.get("search_execution_status") or "draft_only"),
        local_model_status=str(search_payload.get("local_model_status") or "not_available"),
    )


def build_protocol_search_strategy_draft(values: dict[str, object]) -> MetaSearchStrategyDraft:
    question = _search_question_from_values(values)
    return build_meta_search_strategy_draft(
        question,
        population=str(values.get("population") or ""),
        intervention_or_exposure=str(values.get("intervention_or_exposure") or ""),
        comparator=str(values.get("comparator") or ""),
        outcome=str(values.get("primary_outcome") or values.get("outcomes") or ""),
        study_design=str(values.get("study_design") or ""),
    )


def write_protocol_search_strategy_artifacts(project_dir: Path, draft: MetaSearchStrategyDraft) -> dict[str, str]:
    project_dir = project_dir.expanduser().resolve()
    draft_path = project_dir / SEARCH_STRATEGY_DRAFT_RELATIVE_PATH
    audit_path = project_dir / SEARCH_STRATEGY_AUDIT_RELATIVE_PATH
    _write_json(draft_path, draft.to_dict())
    _write_json(
        audit_path,
        {
            "schema_version": "meta_search_strategy_audit.v1",
            "target_context": draft.target_context,
            "local_model_status": draft.local_model_status,
            "search_execution_status": draft.search_execution_status,
            "query_draft_count": len(draft.query_drafts),
            "concept_group_count": len(draft.concept_groups),
            "audit": draft.audit,
            "warning_count": len(draft.warnings),
        },
    )
    return {
        "search_strategy_draft": str(draft_path),
        "search_strategy_audit": str(audit_path),
    }


def render_search_strategy_summary(draft: MetaSearchStrategyDraft) -> str:
    concept_lines = [
        f"- {group.label}: " + (", ".join(group.all_terms) or "empty")
        for group in draft.concept_groups
    ]
    return "\n".join(
        [
            f"PICO/PECO mode: {draft.review_framework}",
            f"target_context: {draft.target_context}",
            f"local_model_status: {draft.local_model_status}",
            f"search_execution_status={draft.search_execution_status}",
            "",
            "Concept blocks:",
            *concept_lines,
            "",
            "PubMed query draft (MeSH + tiab):",
            draft.pubmed_query_draft or "empty",
            "",
            "WOS query draft (draft-only):",
            draft.web_of_science_query_draft or "empty",
            "",
            "Embase query draft (draft-only):",
            draft.embase_query_draft or "empty",
            "",
            "CNKI query draft (draft-only):",
            draft.cnki_query_draft or "empty",
            "",
            "Warnings:",
            ", ".join(draft.warnings) if draft.warnings else "none",
            "",
            "No live literature search is executed. search_execution_report.json is not written.",
            "当前仅生成检索式草稿，尚未执行在线检索。",
        ]
    )


def _search_question_from_values(values: dict[str, object]) -> str:
    fields = (
        values.get("review_question"),
        values.get("project_title"),
        values.get("population"),
        values.get("intervention_or_exposure"),
        values.get("comparator"),
        values.get("outcomes"),
        values.get("primary_outcome"),
        values.get("study_design"),
    )
    return " ".join(str(value).strip() for value in fields if str(value).strip())


def _search_strategy_summary_from_payload(payload: dict[str, object]) -> str:
    if not payload:
        return ""
    concept_groups = [
        f"- {item.get('label')}: "
        + ", ".join(
            [
                *[str(value) for value in item.get("terms_zh", []) if str(value).strip()],
                *[str(value) for value in item.get("terms_en", []) if str(value).strip()],
                *[str(value) for value in item.get("mesh_terms", []) if str(value).strip()],
            ]
        )
        for item in payload.get("concept_groups", [])
        if isinstance(item, dict)
    ]
    query_by_database = {
        str(item.get("database")): str(item.get("query") or "")
        for item in payload.get("query_drafts", [])
        if isinstance(item, dict)
    }
    return "\n".join(
        [
            f"PICO/PECO mode: {payload.get('review_framework', '')}",
            f"target_context: {payload.get('target_context', '')}",
            f"local_model_status: {payload.get('local_model_status', '')}",
            f"search_execution_status={payload.get('search_execution_status', '')}",
            "",
            "Concept blocks:",
            *concept_groups,
            "",
            "PubMed query draft (MeSH + tiab):",
            query_by_database.get("pubmed", ""),
            "",
            "WOS query draft (draft-only):",
            query_by_database.get("web_of_science", ""),
            "",
            "Embase query draft (draft-only):",
            query_by_database.get("embase", ""),
            "",
            "CNKI query draft (draft-only):",
            query_by_database.get("cnki", ""),
        ]
    )


def _load_json_object(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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
            self._search_strategy_summary = QTextEdit()
            self._search_strategy_summary.setObjectName("metaSearchStrategyDraftPreview")
            self._search_strategy_summary.setReadOnly(True)
            self._search_strategy_summary.setPlaceholderText("Search strategy draft will appear after saving the protocol.")
            root.addWidget(self._search_strategy_summary)

        def _save(self) -> None:
            self.save_protocol_draft()

        def save_protocol_draft(self) -> MetaSearchStrategyDraft:
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
            search_strategy = build_protocol_search_strategy_draft(values)
            search_paths = write_protocol_search_strategy_artifacts(project_dir, search_strategy)
            summary_text = render_search_strategy_summary(search_strategy)
            self._search_strategy_summary.setPlainText(summary_text)
            self._summary.setText(
                f"{result.message}\n"
                f"readiness: {result.protocol.readiness_status}\n"
                f"warnings: {', '.join(result.warnings) if result.warnings else 'none'}\n"
                f"preview: {result.artifact_paths.search_strategy_preview}\n"
                f"search_strategy_draft: {search_paths['search_strategy_draft']}\n"
                f"search_strategy_audit: {search_paths['search_strategy_audit']}\n"
                f"local_model_status: {search_strategy.local_model_status}\n"
                f"search_execution_status={search_strategy.search_execution_status}"
            )
            return search_strategy

        def set_protocol_inputs(
            self,
            *,
            project_dir: Path,
            project_title: str,
            review_question: str,
            pico: str,
            method_profile: str,
        ) -> None:
            self._project_dir.setText(str(project_dir))
            self._project_title.setText(project_title)
            self._review_question.setPlainText(review_question)
            self._pico.setPlainText(pico)
            self._method_profile.setText(method_profile)

        def search_strategy_summary_text(self) -> str:
            return self._search_strategy_summary.toPlainText()

else:

    class ProtocolPage:  # type: ignore[no-redef]
        pass
