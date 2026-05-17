from __future__ import annotations

import subprocess
from collections.abc import Callable

try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

    from app.labtools.imagej_bridge import (
        ENGINE_STATUS_AVAILABLE,
        ENGINE_STATUS_CONFIGURED_UNVERIFIED,
        ENGINE_STATUS_FAILED,
        ImageJFijiBridge,
        imagej_fiji_context_prompt,
        imagej_fiji_display_path,
        imagej_fiji_status_label,
        read_shared_imagej_fiji_status,
    )
    from app.shared.local_engines import detect_common_imagej_fiji_paths, imagej_fiji_install_guide_text
    from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    class LabToolsImageJFijiStatusPanel(QFrame):
        def __init__(
            self,
            *,
            workflow_name: str,
            bridge: ImageJFijiBridge | None = None,
            can_continue_without_engine: bool = True,
            runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        ) -> None:
            super().__init__()
            self.setObjectName("labToolsImageJFijiStatusPanel")
            self._workflow_name = workflow_name
            self._bridge = bridge or ImageJFijiBridge()
            self._can_continue_without_engine = can_continue_without_engine
            self._runner = runner
            self._build_ui()
            self.refresh_status()

        def refresh_status(self) -> None:
            status = read_shared_imagej_fiji_status(self._bridge)
            self._status_label.setText(imagej_fiji_status_label(status.status))
            self._path_label.setText(imagej_fiji_display_path(status.configured_path_or_endpoint))
            self._version_label.setText(status.detected_version)
            self._last_check_label.setText(status.last_check_at or "尚未验证")
            self._error_label.setText(status.last_error or "无")
            self._prompt_panel.setText(self._status_text(status))

        def _build_ui(self) -> None:
            self.setStyleSheet(self._stylesheet())
            layout = QVBoxLayout(self)
            layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
            layout.setSpacing(SPACING["sm"])

            title = QLabel("ImageJ/Fiji 本地后端状态")
            title.setObjectName("imageJFijiStatusTitle")
            summary = QLabel("LabTools 只读取共享本地工具状态；不会静默下载、静默安装或上传图片。")
            summary.setObjectName("imageJFijiStatusSummary")
            summary.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(summary)

            self._status_label = QLabel()
            self._status_label.setObjectName("imageJFijiStatusLabel")
            self._path_label = QLabel()
            self._path_label.setObjectName("imageJFijiPathLabel")
            self._version_label = QLabel()
            self._version_label.setObjectName("imageJFijiVersionLabel")
            self._last_check_label = QLabel()
            self._last_check_label.setObjectName("imageJFijiLastCheckLabel")
            self._error_label = QLabel()
            self._error_label.setObjectName("imageJFijiErrorLabel")
            for label in (self._path_label, self._version_label, self._last_check_label, self._error_label):
                label.setWordWrap(True)
            layout.addWidget(QLabel("当前状态"))
            layout.addWidget(self._status_label)
            layout.addWidget(QLabel("当前路径"))
            layout.addWidget(self._path_label)
            layout.addWidget(QLabel("检测版本"))
            layout.addWidget(self._version_label)
            layout.addWidget(QLabel("最近验证"))
            layout.addWidget(self._last_check_label)
            layout.addWidget(QLabel("错误摘要"))
            layout.addWidget(self._error_label)

            self._prompt_panel = QTextEdit()
            self._prompt_panel.setObjectName("imageJFijiSetupPromptPanel")
            self._prompt_panel.setReadOnly(True)
            self._prompt_panel.setMinimumHeight(110)
            layout.addWidget(self._prompt_panel)

            actions = QHBoxLayout()
            self._auto_detect_button = QPushButton("自动检测")
            self._auto_detect_button.setObjectName("imageJFijiAutoDetectButton")
            self._auto_detect_button.clicked.connect(self._handle_auto_detect)
            self._choose_path_button = QPushButton("选择路径")
            self._choose_path_button.setObjectName("imageJFijiChoosePathButton")
            self._choose_path_button.clicked.connect(self._handle_choose_path)
            self._validate_button = QPushButton("运行验证")
            self._validate_button.setObjectName("imageJFijiValidateButton")
            self._validate_button.clicked.connect(self._handle_validate)
            self._download_runtime_button = QPushButton("下载 runtime")
            self._download_runtime_button.setObjectName("imageJFijiDownloadRuntimeButton")
            self._download_runtime_button.clicked.connect(self._handle_download_runtime)
            self._guide_button = QPushButton("安装指南")
            self._guide_button.setObjectName("imageJFijiInstallGuideButton")
            self._guide_button.clicked.connect(self._handle_guide)
            for button in (
                self._auto_detect_button,
                self._choose_path_button,
                self._validate_button,
                self._download_runtime_button,
                self._guide_button,
            ):
                actions.addWidget(button)
            actions.addStretch(1)
            layout.addLayout(actions)

        def _status_text(self, status) -> str:
            if status.status == ENGINE_STATUS_AVAILABLE:
                return "\n".join(
                    (
                        f"{self._workflow_name} 可调用本机 ImageJ/Fiji。",
                        "这只表示共享本地后端通过 smoke test，不表示任何具体图像分析算法已经实现。",
                        "后续结果仍需人工复核。",
                    )
                )
            if status.status == ENGINE_STATUS_CONFIGURED_UNVERIFIED:
                return "\n".join(
                    (
                        f"{self._workflow_name} 已配置本机路径，但尚未验证。",
                        "请运行验证测试；非图像 LabTools 功能不受影响。",
                    )
                )
            if status.status == ENGINE_STATUS_FAILED:
                return "\n".join(
                    (
                        f"{self._workflow_name} 的 ImageJ/Fiji 验证失败。",
                        status.last_error or "请检查本机路径和 ImageJ/Fiji 安装。",
                        "可重新选择路径、查看安装指南，或继续使用已开放的 manual/testing MVP。",
                    )
                )
            return "\n".join(
                (
                    imagej_fiji_context_prompt(
                        workflow_name=self._workflow_name,
                        can_continue_without_engine=self._can_continue_without_engine,
                    ),
                    "BioMedPilot 不会静默下载、静默安装或上传图片。",
                )
            )

        def _handle_auto_detect(self) -> None:
            detected = detect_common_imagej_fiji_paths()
            if not detected:
                self._prompt_panel.setText(
                    "未在常见路径发现 ImageJ/Fiji。\n"
                    "BioMedPilot 不会静默下载或安装。请手动选择本机路径、查看安装指南，或继续 manual/testing MVP。"
                )
                self.refresh_status()
                return
            self._bridge.configure_path(detected[0])
            self.refresh_status()

        def _handle_choose_path(self) -> None:
            path, _ = QFileDialog.getOpenFileName(self, "选择 ImageJ/Fiji 可执行文件", "", "All files (*)")
            if not path:
                path = QFileDialog.getExistingDirectory(self, "选择 ImageJ.app / Fiji.app")
            if path:
                self._bridge.configure_path(path)
                self.refresh_status()

        def _handle_validate(self) -> None:
            try:
                self._bridge.check_status(persist=True, runner=self._runner)
            except ValueError as exc:
                self._prompt_panel.setText(str(exc))
            self.refresh_status()

        def _handle_download_runtime(self) -> None:
            try:
                result = self._bridge.prepare_runtime(
                    allow_network_download=True,
                    runner=self._runner,
                )
            except Exception as exc:
                self.refresh_status()
                self._prompt_panel.setText(f"ImageJ/Fiji runtime 准备失败：{exc}")
            else:
                self.refresh_status()
                self._prompt_panel.setText(
                    "\n".join(
                        (
                            "ImageJ/Fiji runtime 已准备。",
                            f"runtime：{result.runtime_root}",
                            f"manifest：{result.manifest_path}",
                            f"smoke test：{result.smoke_test_status}",
                        )
                    )
                )

        def _handle_guide(self) -> None:
            self._prompt_panel.setText(imagej_fiji_install_guide_text())

        def _stylesheet(self) -> str:
            return f"""
            QFrame#labToolsImageJFijiStatusPanel {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["md"]}px;
            }}
            QLabel#imageJFijiStatusTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["card_title"]}px;
                font-weight: 760;
            }}
            QLabel#imageJFijiStatusSummary {{
                color: {COLORS["muted"]};
            }}
            QTextEdit#imageJFijiSetupPromptPanel {{
                background: {COLORS["background"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px;
            }}
            """

else:  # pragma: no cover

    class LabToolsImageJFijiStatusPanel:  # type: ignore[no-redef]
        pass
