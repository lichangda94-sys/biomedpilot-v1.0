from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.app_identity import load_app_icon, load_ui01_login_icon, load_ui01_login_pixmap
from app.ui_style_tokens import SPACING, login_stylesheet


@dataclass(frozen=True)
class LocalSession:
    username: str
    role: str
    tier: str
    license_status: str
    login_time: str


class BioMedPilotLoginWidget(QWidget):
    """Welcome shell kept under the legacy class name for existing imports."""

    login_succeeded = Signal(object)
    settings_requested = Signal()
    about_requested = Signal()

    def __init__(
        self,
        on_login: Callable[[LocalSession], None] | None = None,
        on_settings: Callable[[], None] | None = None,
        on_about: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._session: LocalSession | None = None
        self.setObjectName("welcomePage")
        self.setStyleSheet(login_stylesheet())
        self._build_ui()
        if on_login is not None:
            self.login_succeeded.connect(on_login)
        if on_settings is not None:
            self.settings_requested.connect(on_settings)
        if on_about is not None:
            self.about_requested.connect(on_about)

    def session(self) -> LocalSession | None:
        return self._session

    def reset_session(self) -> None:
        self._session = None
        self._username_input.setText("local_workspace_user")
        self._password_input.clear()
        self._error_label.clear()
        self._error_label.setVisible(False)

    def error_message(self) -> str:
        return self._error_label.text()

    def set_credentials(self, username: str, password: str) -> None:
        self._username_input.setText(username)
        self._password_input.setText(password)

    def attempt_login(self) -> LocalSession:
        return self.enter_workspace()

    def enter_workspace(self) -> LocalSession:
        username = self._username_input.text().strip() or "local_workspace_user"
        session = LocalSession(
            username=username,
            role="local_test_user",
            tier="Developer Preview",
            license_status="local_testing",
            login_time=datetime.now().astimezone().isoformat(timespec="seconds"),
        )
        self._session = session
        self._password_input.clear()
        self._error_label.clear()
        self._error_label.setVisible(False)
        self.login_succeeded.emit(session)
        return session

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_top_bar())

        main = QWidget()
        main.setObjectName("loginMainContent")
        main_layout = QHBoxLayout(main)
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(18)
        main_layout.addWidget(self._build_brand_panel(), 5)
        main_layout.addWidget(self._build_welcome_card(), 4)
        root.addWidget(main, 1)

    def _build_top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("loginTopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 10, 24, 10)
        layout.setSpacing(SPACING["md"])

        traffic = QWidget()
        traffic_layout = QHBoxLayout(traffic)
        traffic_layout.setContentsMargins(0, 0, 0, 0)
        traffic_layout.setSpacing(8)
        for name in ("trafficDotRed", "trafficDotYellow", "trafficDotGreen"):
            dot = QLabel()
            dot.setObjectName(name)
            dot.setFixedSize(13, 13)
            traffic_layout.addWidget(dot)
        layout.addWidget(traffic)
        layout.addStretch(1)

        title = QLabel("萤火虫 / Firefly")
        title.setObjectName("loginTopTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addStretch(1)

        version = QLabel("BioMedPilot / 医研智析  ·  0.1.0-internal-beta  ·  Developer Preview")
        version.setObjectName("loginTopVersion")
        layout.addWidget(version)

        settings_button = QPushButton()
        settings_button.setObjectName("loginTopIconButton")
        settings_button.setFixedSize(28, 28)
        settings_button.setIcon(load_ui01_login_icon("preview"))
        settings_button.setIconSize(QSize(18, 18))
        settings_button.setToolTip("设置中心")
        settings_button.clicked.connect(self.settings_requested.emit)
        layout.addWidget(settings_button)
        return bar

    def _build_brand_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("loginBrandPanel")
        panel.setMinimumWidth(360)
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(30, 28, 30, 26)
        layout.setSpacing(SPACING["sm"])
        layout.addStretch(1)

        brand_icon = QLabel()
        brand_icon.setObjectName("loginBrandIcon")
        brand_icon.setFixedSize(108, 108)
        icon = load_app_icon()
        brand_icon.setPixmap(icon.pixmap(96, 96) if not icon.isNull() else load_ui01_login_pixmap("brand", 96))
        brand_icon.setVisible(not brand_icon.pixmap().isNull())

        title = QLabel("萤火虫 / Firefly")
        title.setObjectName("brandTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        chinese_name = QLabel("BioMedPilot / 医研智析")
        chinese_name.setObjectName("brandChineseName")
        chinese_name.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("低保真全局壳层：统一入口、三模块工作台、测试反馈与设置中心")
        subtitle.setObjectName("brandSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)

        layout.addWidget(brand_icon, alignment=Qt.AlignHCenter)
        layout.addWidget(title)
        layout.addWidget(chinese_name)
        layout.addSpacing(SPACING["sm"])
        layout.addWidget(subtitle)
        layout.addSpacing(SPACING["lg"])

        tag_row = QHBoxLayout()
        tag_row.setSpacing(SPACING["md"])
        for icon_key, tag in (
            ("brand", "Bioinformatics"),
            ("security", "Meta Analysis"),
            ("license", "LabTools"),
        ):
            label = QLabel(tag)
            label.setObjectName("capabilityTag")
            pixmap = load_ui01_login_pixmap(icon_key, 22)
            if not pixmap.isNull():
                label.setPixmap(pixmap)
                label.setText(f"  {tag}")
            tag_row.addWidget(label)
        tag_row.setAlignment(Qt.AlignHCenter)
        layout.addLayout(tag_row)
        layout.addStretch(1)

        version = QLabel("Developer Preview / 本地测试版：不含正式登录、订阅或授权流程。")
        version.setObjectName("brandVersionLabel")
        version.setWordWrap(True)
        layout.addWidget(version)
        return panel

    def _build_welcome_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("loginCard")
        card.setMinimumWidth(330)
        card.setMaximumWidth(520)
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 28, 30, 24)
        layout.setSpacing(SPACING["sm"])

        title = QLabel("Welcome / 欢迎")
        title.setObjectName("loginTitle")
        title.setAlignment(Qt.AlignCenter)
        hint = QLabel("进入本地工作台，查看 Dashboard、Sidebar、About 与 Test Feedback 壳层。")
        hint.setObjectName("loginHint")
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addSpacing(SPACING["md"])

        self._username_input = QLineEdit()
        self._username_input.setObjectName("usernameInput")
        self._username_input.setText("local_workspace_user")
        self._username_input.setVisible(False)
        layout.addWidget(self._username_input)

        self._password_input = QLineEdit()
        self._password_input.setObjectName("passwordInput")
        self._password_input.setEchoMode(QLineEdit.Password)
        self._password_input.setVisible(False)
        layout.addWidget(self._password_input)

        self._error_label = QLabel("")
        self._error_label.setObjectName("loginErrorLabel")
        self._error_label.setWordWrap(True)
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        enter_button = QPushButton("进入本地工作台")
        enter_button.setObjectName("primaryButton")
        enter_button.setIcon(load_ui01_login_icon("login"))
        enter_button.setIconSize(QSize(22, 22))
        enter_button.clicked.connect(self.enter_workspace)
        layout.addWidget(enter_button)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 4, 0, 0)
        settings_button = QPushButton("设置中心")
        settings_button.setObjectName("linkButton")
        settings_button.setIcon(load_ui01_login_icon("preview"))
        settings_button.clicked.connect(self.settings_requested.emit)
        about_button = QPushButton("关于")
        about_button.setObjectName("linkButton")
        about_button.setIcon(load_ui01_login_icon("brand"))
        about_button.clicked.connect(self.about_requested.emit)
        actions.addWidget(settings_button)
        actions.addStretch(1)
        actions.addWidget(about_button)
        layout.addLayout(actions)

        layout.addSpacing(SPACING["sm"])
        layout.addWidget(self._build_scope_panel())
        layout.addStretch(1)
        return card

    def _build_scope_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("loginAccountPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(SPACING["sm"])
        for text in (
            "一级入口：Dashboard、Bioinformatics、Meta Analysis、LabTools、Settings。",
            "辅助入口：About、Test Feedback。",
            "当前阶段只提供低保真壳层，不代表正式分析能力。",
        ):
            label = QLabel(text)
            label.setObjectName("loginMetaLabel")
            label.setWordWrap(True)
            layout.addWidget(label)
        return panel
