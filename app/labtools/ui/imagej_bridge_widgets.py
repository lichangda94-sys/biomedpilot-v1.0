from __future__ import annotations

import subprocess
from collections.abc import Callable

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from app.labtools.imagej_bridge import (
        IMAGEJ_RECOMMENDED_BACKEND,
        ImageJBridgeConfig,
        ImageJBridgeConfigStore,
        ImageJBridgeError,
        detect_common_imagej_paths,
        imagej_status_label,
        run_imagej_smoke_test,
    )
    from app.ui_style_tokens import COLORS, CONTROL_HEIGHT, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    class LabToolsImageJBridgeWidget(QWidget):
        def __init__(
            self,
            *,
            store: ImageJBridgeConfigStore | None = None,
            runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        ) -> None:
            super().__init__()
            self.setObjectName("labToolsImageJBridgeSettingsPage")
            self.setStyleSheet(self._stylesheet())
            self._store = store or ImageJBridgeConfigStore()
            self._runner = runner
            self._config = self._load_initial_config()
            self._build_ui()
            self._refresh_status()

        def config(self) -> ImageJBridgeConfig:
            return self._config

        def set_configured_path_for_testing(self, path: str) -> None:
            self._set_configured_path(path)

        def _load_initial_config(self) -> ImageJBridgeConfig:
            try:
                return self._store.load()
            except ImageJBridgeError:
                from app.labtools.imagej_bridge import default_imagej_bridge_config

                return default_imagej_bridge_config()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            root.setSpacing(SPACING["lg"])

            title = QLabel("ImageJ/Fiji 后端设置")
            title.setObjectName("imageJBridgeTitle")
            description = QLabel("BioMedPilot 不内置 Fiji/ImageJ。后续图像分析将通过用户配置的 Fiji/ImageJ 和宏自动化完成，结果仍需人工复核。")
            description.setObjectName("imageJBridgeDescription")
            description.setWordWrap(True)
            recommendation = QLabel("第一版推荐 Fiji Stable / Java 8。其他版本可尝试使用，但需通过本机 smoke test。")
            recommendation.setObjectName("imageJBridgeRecommendation")
            recommendation.setWordWrap(True)
            status_legend = QLabel("状态文案：未配置 / 已配置，尚未验证 / 可用 / 验证失败")
            status_legend.setObjectName("imageJBridgeStatusLegend")
            status_legend.setWordWrap(True)
            boundary = QLabel("本页只配置外部 Fiji/ImageJ bridge；不表示 WB 灰度、自动 ROI、细胞计数或批量图像处理已经可用。")
            boundary.setObjectName("imageJBridgeBoundary")
            boundary.setWordWrap(True)
            root.addWidget(title)
            root.addWidget(description)
            root.addWidget(recommendation)
            root.addWidget(status_legend)
            root.addWidget(boundary)

            details = self._card()
            details_layout = QGridLayout(details)
            details_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._status_label = QLabel()
            self._status_label.setObjectName("imagejBridgeStatusLabel")
            self._path_label = QLabel()
            self._path_label.setObjectName("imagejBridgePathLabel")
            self._version_label = QLabel()
            self._version_label.setObjectName("imagejBridgeVersionLabel")
            self._java_label = QLabel()
            self._java_label.setObjectName("imagejBridgeJavaVersionLabel")
            self._last_test_label = QLabel()
            self._last_test_label.setObjectName("imagejBridgeLastTestLabel")
            self._error_label = QLabel()
            self._error_label.setObjectName("imagejBridgeErrorLabel")
            for label in (self._path_label, self._version_label, self._java_label, self._last_test_label, self._error_label):
                label.setWordWrap(True)
            rows = (
                ("当前状态", self._status_label),
                ("当前路径", self._path_label),
                ("检测到的版本", self._version_label),
                ("Java version", self._java_label),
                ("最近一次验证时间", self._last_test_label),
                ("最近一次错误摘要", self._error_label),
            )
            for index, (label, widget) in enumerate(rows):
                details_layout.addWidget(QLabel(label), index, 0)
                details_layout.addWidget(widget, index, 1)
            root.addWidget(details)

            path_card = self._card()
            path_layout = QGridLayout(path_card)
            path_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._path_field = QLineEdit()
            self._path_field.setObjectName("imagejBridgeConfiguredPathField")
            self._path_field.setPlaceholderText("选择或输入 Fiji.app / ImageJ 可执行文件 / Fiji 可执行脚本路径")
            self._path_field.setMinimumHeight(CONTROL_HEIGHT["field"])
            path_layout.addWidget(QLabel("配置路径"), 0, 0)
            path_layout.addWidget(self._path_field, 0, 1)
            root.addWidget(path_card)

            actions = self._card()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._auto_detect_button = QPushButton("自动检测 Fiji/ImageJ")
            self._auto_detect_button.setObjectName("imagejAutoDetectButton")
            self._auto_detect_button.clicked.connect(self._handle_auto_detect)
            self._select_path_button = QPushButton("选择 Fiji/ImageJ 路径")
            self._select_path_button.setObjectName("imagejSelectPathButton")
            self._select_path_button.clicked.connect(self._handle_select_path)
            self._run_smoke_button = QPushButton("运行验证测试")
            self._run_smoke_button.setObjectName("imagejRunSmokeTestButton")
            self._run_smoke_button.clicked.connect(self._handle_run_smoke_test)
            self._official_button = QPushButton("显示官方下载地址说明")
            self._official_button.setObjectName("imagejOfficialDownloadButton")
            self._official_button.clicked.connect(self._handle_show_official_download)
            self._clear_button = QPushButton("清除配置")
            self._clear_button.setObjectName("imagejClearConfigButton")
            self._clear_button.clicked.connect(self._handle_clear_config)
            for button in (
                self._auto_detect_button,
                self._select_path_button,
                self._run_smoke_button,
                self._official_button,
                self._clear_button,
            ):
                actions_layout.addWidget(button)
            actions_layout.addStretch(1)
            root.addWidget(actions)

            self._result_panel = QTextEdit()
            self._result_panel.setObjectName("imagejBridgeResultPanel")
            self._result_panel.setReadOnly(True)
            self._result_panel.setMinimumHeight(160)
            root.addWidget(self._result_panel, 1)

        def _handle_auto_detect(self) -> None:
            detected = detect_common_imagej_paths()
            if not detected:
                self._result_panel.setText("未在常见路径发现 Fiji/ImageJ。请手动选择 Fiji.app、ImageJ 可执行文件或 Fiji 可执行脚本。")
                return
            self._set_configured_path(detected[0])
            self._result_panel.setText(f"已检测到候选路径：{detected[0]}\n状态：已配置，尚未验证。")

        def _handle_select_path(self) -> None:
            selected = self._select_executable_path()
            if not selected:
                return
            self._set_configured_path(selected)
            self._result_panel.setText("已保存 ImageJ/Fiji 路径。请运行验证测试。")

        def _handle_run_smoke_test(self) -> None:
            path_text = self._path_field.text().strip()
            if path_text and path_text != self._config.configured_path:
                self._set_configured_path(path_text)
            result = run_imagej_smoke_test(self._config, runner=self._runner)
            self._config = result.config
            self._save_config(self._config)
            self._refresh_status()
            if result.available:
                version_note = "未验证版本，但当前可调用" if result.detected_version == "unknown_version" else f"检测到版本：{result.detected_version}"
                self._result_panel.setText(f"ImageJ/Fiji smoke test 通过。\n{version_note}\n状态：可用\n结果仍需人工复核。")
            else:
                self._result_panel.setText(f"ImageJ/Fiji smoke test 验证失败。\n{result.error_message}")

        def _handle_show_official_download(self) -> None:
            self._result_panel.setText(
                "官方下载地址说明：\n"
                "- Fiji: https://fiji.sc/\n"
                "- ImageJ: https://imagej.net/software/fiji/\n"
                f"- 推荐版本策略：{IMAGEJ_RECOMMENDED_BACKEND}；其他版本可尝试使用，但需通过本机 smoke test。\n"
                "- BioMedPilot 不自动下载、不静默安装、不打包 Fiji/ImageJ。"
            )

        def _handle_clear_config(self) -> None:
            self._config = self._store.clear()
            self._refresh_status()
            self._result_panel.setText("ImageJ/Fiji 配置已清除。")

        def _set_configured_path(self, path: str) -> None:
            from app.labtools.imagej_bridge import configure_imagej_path

            self._config = configure_imagej_path(path)
            self._save_config(self._config)
            self._refresh_status()

        def _save_config(self, config: ImageJBridgeConfig) -> None:
            try:
                self._store.save(config)
            except ImageJBridgeError as exc:
                self._result_panel.setText(str(exc))

        def _refresh_status(self) -> None:
            self._path_field.setText(self._config.configured_path)
            self._status_label.setText(imagej_status_label(self._config.status))
            self._path_label.setText(self._config.configured_path or "未配置")
            self._version_label.setText(self._config.detected_version or "unknown_version")
            self._java_label.setText(self._config.java_version or "unknown_version")
            self._last_test_label.setText(self._config.last_smoke_test_at or "尚未验证")
            self._error_label.setText(self._config.last_error or "无")
            if not self._result_panel.toPlainText():
                self._result_panel.setText("尚未运行验证测试。")

        def _select_executable_path(self) -> str:
            path, _ = QFileDialog.getOpenFileName(self, "选择 Fiji/ImageJ 可执行文件", "", "All files (*)")
            if path:
                return path
            directory = QFileDialog.getExistingDirectory(self, "选择 Fiji.app / ImageJ.app")
            return directory or ""

        def _card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("imageJBridgeCard")
            return frame

        def _stylesheet(self) -> str:
            return f"""
            QWidget#labToolsImageJBridgeSettingsPage {{
                background: {COLORS["background"]};
                color: {COLORS["text"]};
                font-size: {FONT_SIZE["body"]}px;
            }}
            QLabel#imageJBridgeTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["page_title"]}px;
                font-weight: 780;
            }}
            QLabel#imageJBridgeDescription, QLabel#imageJBridgeStatusLegend {{
                color: {COLORS["muted"]};
            }}
            QLabel#imageJBridgeRecommendation, QLabel#imageJBridgeBoundary {{
                color: {COLORS["text"]};
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 10px;
            }}
            QFrame#imageJBridgeCard {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["md"]}px;
            }}
            QTextEdit#imagejBridgeResultPanel {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 10px;
            }}
            """

else:  # pragma: no cover

    class LabToolsImageJBridgeWidget:  # type: ignore[no-redef]
        pass
