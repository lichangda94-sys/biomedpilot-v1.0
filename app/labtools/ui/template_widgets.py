from __future__ import annotations

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from app.labtools.experiment_templates import (
        EXPERIMENT_TEMPLATE_REVIEW_NOTICE,
        ExperimentRecordDraft,
        ExperimentTemplate,
        ExperimentTemplateError,
        ExperimentTemplateLibrary,
        create_record_draft,
        draft_markdown_preview,
        load_experiment_draft_store,
        save_experiment_draft_store,
    )
    from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    class LabToolsTemplateWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("labToolsTemplateWorkspace")
            self.setStyleSheet(self._stylesheet())
            self._library = ExperimentTemplateLibrary()
            self._templates = self._library.list_templates()
            self._current_template: ExperimentTemplate | None = None
            self._drafts: list[ExperimentRecordDraft] = []
            self._build_ui()
            self._refresh_templates()

        def template_count(self) -> int:
            return len(self._templates)

        def record_drafts(self) -> tuple[ExperimentRecordDraft, ...]:
            return tuple(self._drafts)

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["xl"])
            root.setSpacing(SPACING["md"])

            title = QLabel("实验模板")
            title.setObjectName("labToolsSectionTitle")
            notice = QLabel(EXPERIMENT_TEMPLATE_REVIEW_NOTICE)
            notice.setObjectName("templateNotice")
            notice.setWordWrap(True)
            root.addWidget(title)
            root.addWidget(notice)

            body = QHBoxLayout()
            body.setSpacing(SPACING["md"])
            self._template_list = QListWidget()
            self._template_list.setObjectName("templateList")
            self._template_list.setMinimumWidth(280)
            self._template_list.currentItemChanged.connect(self._handle_template_selected)
            body.addWidget(self._template_list, 1)

            right = QVBoxLayout()
            right.setSpacing(SPACING["md"])
            self._template_detail = QTextEdit()
            self._template_detail.setObjectName("templateResultPanel")
            self._template_detail.setReadOnly(True)
            right.addWidget(self._template_detail, 1)
            right.addWidget(self._build_draft_card(), 2)
            body.addLayout(right, 2)
            root.addLayout(body, 1)

        def _build_draft_card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            layout.setSpacing(SPACING["sm"])
            heading = QLabel("结构化记录草稿")
            heading.setObjectName("templateCardTitle")
            self._purpose = QTextEdit()
            self._purpose.setObjectName("templateInput")
            self._purpose.setPlaceholderText("实验目的")
            self._purpose.setMinimumHeight(52)
            self._sample_groups = self._text_area("样本分组，每行一条")
            self._reagents = self._text_area("试剂/材料，每行一条")
            self._key_parameters = self._text_area("关键参数，每行一条")
            self._output_files = self._text_area("输出文件/记录，每行一条")
            self._notes = self._text_area("备注，可选")
            button = QPushButton("生成记录草稿")
            button.setObjectName("primaryButton")
            button.clicked.connect(self._handle_create_draft)
            self._draft_preview = QTextEdit()
            self._draft_preview.setObjectName("templateResultPanel")
            self._draft_preview.setReadOnly(True)
            self._draft_preview.setText("选择模板后，可生成本地结构化草稿；仅在用户选择路径后保存 JSON，不自动保存、不生成正式 ELN。")
            actions = QHBoxLayout()
            save_button = QPushButton("保存记录草稿 JSON")
            save_button.setObjectName("secondaryButton")
            save_button.clicked.connect(self._handle_save_drafts)
            load_button = QPushButton("载入记录草稿 JSON")
            load_button.setObjectName("secondaryButton")
            load_button.clicked.connect(self._handle_load_drafts)
            actions.addWidget(save_button)
            actions.addWidget(load_button)
            layout.addWidget(heading)
            layout.addWidget(self._purpose)
            layout.addWidget(self._sample_groups)
            layout.addWidget(self._reagents)
            layout.addWidget(self._key_parameters)
            layout.addWidget(self._output_files)
            layout.addWidget(self._notes)
            layout.addWidget(button)
            layout.addLayout(actions)
            layout.addWidget(self._draft_preview, 1)
            return frame

        def _text_area(self, placeholder: str) -> QTextEdit:
            field = QTextEdit()
            field.setObjectName("templateInput")
            field.setPlaceholderText(placeholder)
            field.setMinimumHeight(52)
            return field

        def _refresh_templates(self) -> None:
            self._template_list.clear()
            for template in self._templates:
                item = QListWidgetItem(f"{template.name}\n{template.category}")
                item.setData(Qt.UserRole, template.template_id)
                self._template_list.addItem(item)
            if self._templates:
                self._template_list.setCurrentRow(0)

        def _handle_template_selected(self, current: QListWidgetItem | None) -> None:
            if current is None:
                return
            template_id = str(current.data(Qt.UserRole) or "")
            self._current_template = self._library.get_template(template_id)
            self._render_template_detail()
            self._seed_fields_from_template()

        def _render_template_detail(self) -> None:
            template = self._current_template
            if template is None:
                self._template_detail.setText("请选择实验模板。")
                return
            lines = [
                template.name,
                f"分类：{template.category}",
                f"说明：{template.description}",
                f"版本：{template.version}",
                "",
                "样本分组字段",
                *[f"- {item}" for item in template.sample_group_fields],
                "",
                "试剂/材料字段",
                *[f"- {item}" for item in template.reagent_fields],
                "",
                "关键参数字段",
                *[f"- {item}" for item in template.key_parameter_fields],
                "",
                "输出文件/记录字段",
                *[f"- {item}" for item in template.output_file_fields],
                "",
                "边界提示",
                *[f"- {item}" for item in template.safety_notes],
                "",
                "复核提示",
                template.review_notice,
            ]
            self._template_detail.setText("\n".join(lines))

        def _seed_fields_from_template(self) -> None:
            template = self._current_template
            if template is None:
                return
            self._purpose.setText(template.purpose_prompt)
            self._sample_groups.setText("\n".join(template.sample_group_fields[:3]))
            self._reagents.setText("\n".join(template.reagent_fields[:3]))
            self._key_parameters.setText("\n".join(template.key_parameter_fields[:4]))
            self._output_files.setText("\n".join(template.output_file_fields[:3]))
            self._notes.setText("\n".join(template.note_fields[:2]))

        def _handle_create_draft(self) -> None:
            if self._current_template is None:
                self._draft_preview.setText("请先选择实验模板。")
                return
            try:
                draft = create_record_draft(
                    self._current_template,
                    purpose=self._purpose.toPlainText(),
                    sample_groups=self._lines(self._sample_groups),
                    reagents=self._lines(self._reagents),
                    key_parameters=self._lines(self._key_parameters),
                    output_files=self._lines(self._output_files),
                    notes=self._lines(self._notes),
                )
            except ExperimentTemplateError as exc:
                self._draft_preview.setText(f"记录草稿需要调整\n{exc}")
                return
            self._drafts.append(draft)
            self._draft_preview.setText(draft_markdown_preview(draft))

        def _handle_save_drafts(self) -> None:
            if not self._drafts:
                self._draft_preview.setText("尚未生成实验记录草稿，未写入任何文件。")
                return
            path = self._select_draft_save_path()
            if not path:
                self._draft_preview.setText("已取消保存；未写入任何文件。")
                return
            try:
                result = self._perform_save_drafts(path)
            except ExperimentTemplateError as exc:
                self._draft_preview.setText(f"保存需要调整\n{exc}")
                return
            self._draft_preview.setText(
                "\n".join(
                    [
                        "实验记录草稿 JSON 已保存",
                        f"路径：{result.path}",
                        f"schema：{result.schema_version}",
                        f"草稿数：{result.draft_count}",
                        "",
                        "复核提示",
                        result.review_notice,
                    ]
                )
            )

        def _handle_load_drafts(self) -> None:
            path = self._select_draft_load_path()
            if not path:
                self._draft_preview.setText("已取消载入；当前记录草稿未改变。")
                return
            try:
                result = self._perform_load_drafts(path)
            except ExperimentTemplateError as exc:
                self._draft_preview.setText(f"载入需要调整\n{exc}")
                return
            if result.drafts:
                self._draft_preview.setText(
                    "\n".join(
                        [
                            "实验记录草稿 JSON 已载入",
                            f"路径：{result.path}",
                            f"schema：{result.schema_version}",
                            f"载入草稿数：{result.draft_count}",
                            "",
                            draft_markdown_preview(result.drafts[-1]),
                        ]
                    )
                )
            else:
                self._draft_preview.setText("实验记录草稿 JSON 已载入，但文件中没有草稿。")

        def _select_draft_save_path(self) -> str:
            path, _selected_filter = QFileDialog.getSaveFileName(
                self,
                "保存实验记录草稿 JSON",
                "labtools_experiment_record_drafts.json",
                "JSON Files (*.json)",
            )
            return path

        def _select_draft_load_path(self) -> str:
            path, _selected_filter = QFileDialog.getOpenFileName(
                self,
                "载入实验记录草稿 JSON",
                "",
                "JSON Files (*.json)",
            )
            return path

        def _perform_save_drafts(self, path: str):
            return save_experiment_draft_store(tuple(self._drafts), path)

        def _perform_load_drafts(self, path: str):
            result = load_experiment_draft_store(path)
            self._drafts.extend(result.drafts)
            return result

        def _lines(self, field: QTextEdit) -> tuple[str, ...]:
            return tuple(line.strip() for line in field.toPlainText().splitlines() if line.strip())

        def _stylesheet(self) -> str:
            return f"""
            QWidget#labToolsTemplateWorkspace {{
                background: {COLORS["background"]};
                color: {COLORS["text"]};
                font-size: {FONT_SIZE["body"]}px;
            }}
            QLabel#labToolsSectionTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["page_title"]}px;
                font-weight: 760;
            }}
            QLabel#templateNotice {{
                color: {COLORS["muted"]};
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 10px;
            }}
            QLabel#templateCardTitle {{
                color: {COLORS["bio"]};
                font-weight: 700;
            }}
            QFrame#labToolsCard {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
            }}
            QListWidget#templateList, QTextEdit#templateResultPanel, QTextEdit#templateInput {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px;
            }}
            QPushButton#primaryButton {{
                color: #FFFFFF;
                background: {COLORS["bio"]};
                border: 1px solid {COLORS["bio"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 12px;
                font-weight: 700;
            }}
            QPushButton#secondaryButton {{
                color: {COLORS["bio"]};
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 12px;
                font-weight: 700;
            }}
            """

else:  # pragma: no cover

    class LabToolsTemplateWidget:  # type: ignore[no-redef]
        pass
