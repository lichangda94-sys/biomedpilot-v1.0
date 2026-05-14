from __future__ import annotations

try:
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QWidget

    from app.labtools.image_analysis import IMAGE_REVIEW_NOTICE
    from app.labtools.image_analysis.local_engine_consumer import (
        LABTOOLS_IMAGE_ANALYSIS_BOUNDARY,
        check_labtools_imagej_fiji_status,
        clear_labtools_imagej_fiji_path,
        configure_labtools_imagej_fiji_path,
        labtools_imagej_fiji_prompt,
        load_labtools_imagej_fiji_status,
    )
    from app.ui_style_tokens import COLORS, CONTROL_HEIGHT, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    class LabToolsImageAnalysisWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("labToolsImageAnalysisWorkspace")
            self.setStyleSheet(self._stylesheet())
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["xl"])
            root.setSpacing(SPACING["md"])

            title = QLabel("图像能力边界")
            title.setObjectName("labToolsSectionTitle")
            notice = QLabel(IMAGE_REVIEW_NOTICE)
            notice.setObjectName("imageNotice")
            notice.setWordWrap(True)
            root.addWidget(title)
            root.addWidget(notice)
            root.addWidget(self._build_imagej_fiji_card())

            summary = QTextEdit()
            summary.setObjectName("imageResultPanel")
            summary.setReadOnly(True)
            summary.setText(
                "\n".join(
                    [
                        "本阶段仅消费 shared ImageJ/Fiji 本机引擎状态。",
                        "不会上传图片，不联网，不调用模型服务。",
                        "不会生成 WB/gel、agarose、cell counting、automatic ROI 或 pathology workflow 结果。",
                    ]
                )
            )
            root.addWidget(summary, 1)

        def _build_imagej_fiji_card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            layout.setSpacing(SPACING["sm"])

            heading = QLabel("ImageJ/Fiji 本机引擎")
            heading.setObjectName("imageCardTitle")
            prompt = QLabel(labtools_imagej_fiji_prompt())
            prompt.setObjectName("imageTaskStatus")
            prompt.setWordWrap(True)
            boundary = QLabel(LABTOOLS_IMAGE_ANALYSIS_BOUNDARY)
            boundary.setObjectName("imageTaskStatus")
            boundary.setWordWrap(True)

            row = QHBoxLayout()
            self._imagej_path_field = QLineEdit()
            self._imagej_path_field.setObjectName("imageJPathField")
            self._imagej_path_field.setPlaceholderText("选择或填写本机 Fiji.app、ImageJ.app 或可执行文件路径")
            self._imagej_path_field.setMinimumHeight(CONTROL_HEIGHT["field"])
            save = QPushButton("保存路径")
            save.setObjectName("secondaryButton")
            save.clicked.connect(self._handle_configure_imagej_fiji)
            check = QPushButton("检测 ImageJ/Fiji")
            check.setObjectName("secondaryButton")
            check.clicked.connect(self._handle_check_imagej_fiji)
            clear = QPushButton("清除")
            clear.setObjectName("secondaryButton")
            clear.clicked.connect(self._handle_clear_imagej_fiji)
            row.addWidget(self._imagej_path_field, 1)
            row.addWidget(save)
            row.addWidget(check)
            row.addWidget(clear)

            self._imagej_status_label = QLabel("")
            self._imagej_status_label.setObjectName("imageTaskStatus")
            self._imagej_status_label.setWordWrap(True)
            layout.addWidget(heading)
            layout.addWidget(prompt)
            layout.addWidget(boundary)
            layout.addLayout(row)
            layout.addWidget(self._imagej_status_label)
            self._render_imagej_fiji_status(load_labtools_imagej_fiji_status())
            return frame

        def _handle_configure_imagej_fiji(self) -> None:
            try:
                status = configure_labtools_imagej_fiji_path(self._imagej_path_field.text())
            except ValueError as exc:
                self._imagej_status_label.setText(f"ImageJ/Fiji 配置需要调整：{exc}")
                return
            self._render_imagej_fiji_status(status)

        def _handle_check_imagej_fiji(self) -> None:
            try:
                status = check_labtools_imagej_fiji_status()
            except ValueError as exc:
                self._imagej_status_label.setText(f"ImageJ/Fiji 检测需要调整：{exc}")
                return
            self._render_imagej_fiji_status(status)

        def _handle_clear_imagej_fiji(self) -> None:
            try:
                status = clear_labtools_imagej_fiji_path()
            except ValueError as exc:
                self._imagej_status_label.setText(f"ImageJ/Fiji 配置需要调整：{exc}")
                return
            self._render_imagej_fiji_status(status)

        def _render_imagej_fiji_status(self, status) -> None:
            if hasattr(self, "_imagej_path_field"):
                self._imagej_path_field.setText(status.configured_path_or_endpoint)
            detail = status.last_error or "未执行检测；可继续 manual-review 准备流程。"
            self._imagej_status_label.setText(
                "\n".join(
                    [
                        f"状态：{status.status}",
                        f"版本：{status.detected_version}",
                        f"路径：{status.configured_path_or_endpoint or '未配置'}",
                        detail,
                    ]
                )
            )

        def _stylesheet(self) -> str:
            return f"""
            QWidget#labToolsImageAnalysisWorkspace {{
                background: {COLORS['background']};
            }}
            QLabel#labToolsSectionTitle {{
                color: {COLORS['bio']};
                font-size: {FONT_SIZE['page_title']}px;
                font-weight: 760;
            }}
            QFrame#labToolsCard, QTextEdit#imageResultPanel {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS['md']}px;
            }}
            QLabel#imageNotice {{
                color: {COLORS['danger']};
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS['sm']}px;
                padding: 9px 11px;
            }}
            QLabel#imageCardTitle {{
                color: {COLORS['text']};
                font-size: {FONT_SIZE['card_title']}px;
                font-weight: 700;
            }}
            QLabel#imageTaskStatus {{
                color: {COLORS['muted']};
            }}
            """

else:  # pragma: no cover

    class LabToolsImageAnalysisWidget:  # type: ignore[no-redef]
        pass
