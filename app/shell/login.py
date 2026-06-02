from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
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

from app.app_identity import load_app_icon, load_ui01_login_icon, load_ui01_login_pixmap, load_welcome_hero_pixmap
from app.ui_style_tokens import SPACING, login_stylesheet


@dataclass(frozen=True)
class LocalSession:
    username: str
    role: str
    tier: str
    license_status: str
    login_time: str


class _ScaledPixmapLabel(QLabel):
    def __init__(self, pixmap: QPixmap, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._source_pixmap = QPixmap()
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(320, 255)
        self.setMaximumSize(832, 663)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.set_hero_pixmap(pixmap)

    def set_hero_pixmap(self, pixmap: QPixmap) -> None:
        self._source_pixmap = pixmap
        self._update_pixmap()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._update_pixmap()

    def _update_pixmap(self) -> None:
        if self._source_pixmap.isNull():
            self.clear()
            return
        target = self.contentsRect().size()
        if target.width() <= 0 or target.height() <= 0:
            return
        self.setPixmap(self._source_pixmap.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation))


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

        main = QWidget()
        main.setObjectName("loginMainContent")
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(40, 34, 40, 34)
        main_layout.setSpacing(24)
        main_layout.addStretch(1)

        hero = _ScaledPixmapLabel(load_welcome_hero_pixmap())
        hero.setObjectName("welcomeHeroImage")
        hero.setAccessibleName("Welcome firefly laboratory image")
        if hero.pixmap() is None or hero.pixmap().isNull():
            hero.setText("萤火虫 / Firefly")
            hero.setObjectName("loginBrandIcon")
        main_layout.addWidget(hero, 7, alignment=Qt.AlignHCenter | Qt.AlignBottom)
        main_layout.addWidget(self._build_welcome_card(), 0, alignment=Qt.AlignHCenter | Qt.AlignTop)
        main_layout.addStretch(1)
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

        title = QLabel("Developer Preview")
        title.setObjectName("loginTopTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addStretch(1)

        version = QLabel("0.1.0-internal-beta  ·  Local Preview")
        version.setObjectName("loginTopVersion")
        layout.addWidget(version)

        settings_button = QPushButton()
        settings_button.setObjectName("loginTopIconButton")
        settings_button.setFixedSize(28, 28)
        settings_button.setIcon(load_ui01_login_icon("preview"))
        settings_button.setIconSize(QSize(18, 18))
        settings_button.setToolTip("设置中心")
        settings_button.setProperty("buttonBehavior", "navigates_to_shell_route_settings")
        settings_button.setProperty("formalActionEnabled", False)
        settings_button.setProperty("fileWriteAllowed", False)
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
        card.setFixedWidth(260)
        card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(11)

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
        enter_button.setAccessibleName("Enter local workspace")
        enter_button.setProperty("usabilityRole", "primary_entry_action")
        enter_button.setProperty("buttonBehavior", "navigates_to_shell_route_dashboard")
        enter_button.setProperty("formalActionEnabled", False)
        enter_button.setProperty("fileWriteAllowed", False)
        enter_button.setDefault(True)
        enter_button.setIcon(load_ui01_login_icon("welcome_enter"))
        enter_button.setIconSize(QSize(16, 16))
        enter_button.setFixedSize(260, 47)
        enter_button.clicked.connect(self.enter_workspace)
        layout.addWidget(enter_button)

        about_button = QPushButton("关于")
        about_button.setObjectName("aboutButton")
        about_button.setAccessibleName("Open about")
        about_button.setProperty("usabilityRole", "secondary_entry_action")
        about_button.setProperty("buttonBehavior", "navigates_to_shell_route_about")
        about_button.setProperty("formalActionEnabled", False)
        about_button.setProperty("fileWriteAllowed", False)
        about_button.setIcon(load_ui01_login_icon("welcome_about"))
        about_button.setIconSize(QSize(14, 14))
        about_button.setFixedSize(260, 42)
        about_button.clicked.connect(self.about_requested.emit)
        layout.addWidget(about_button)
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
