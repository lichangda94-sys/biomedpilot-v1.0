from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtCore import QSize
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
from app.ui_style_tokens import COLORS, SPACING, login_stylesheet


@dataclass(frozen=True)
class LocalSession:
    username: str
    role: str
    tier: str
    license_status: str
    login_time: str


class BioMedPilotLoginWidget(QWidget):
    login_succeeded = Signal(object)

    def __init__(
        self,
        on_login: Callable[[LocalSession], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._session: LocalSession | None = None
        self.setObjectName("loginPage")
        self.setStyleSheet(login_stylesheet())
        self._build_ui()
        if on_login is not None:
            self.login_succeeded.connect(on_login)

    def session(self) -> LocalSession | None:
        return self._session

    def reset_session(self) -> None:
        self._session = None
        self._password_input.clear()
        self._error_label.clear()
        self._error_label.setVisible(False)

    def error_message(self) -> str:
        return self._error_label.text()

    def set_credentials(self, username: str, password: str) -> None:
        self._username_input.setText(username)
        self._password_input.setText(password)

    def attempt_login(self) -> LocalSession | None:
        username = self._username_input.text().strip()
        password = self._password_input.text()
        if not username or not password:
            self._session = None
            self._error_label.setText("请输入用户名和密码。")
            self._error_label.setVisible(True)
            return None

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
        main_layout.addWidget(self._build_login_card(), 4)
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

        title = QLabel("BioMedPilot / 医研智析")
        title.setObjectName("loginTopTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addStretch(1)

        version = QLabel("0.1.0-internal-beta  /  Developer Preview  /  本地测试版")
        version.setObjectName("loginTopVersion")
        layout.addWidget(version)

        settings_button = QPushButton()
        settings_button.setObjectName("loginTopIconButton")
        settings_button.setFixedSize(28, 28)
        settings_button.setIcon(load_ui01_login_icon("preview"))
        settings_button.setIconSize(QSize(18, 18))
        settings_button.setToolTip("设置入口占位")
        settings_button.setEnabled(False)
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
        title = QLabel("BioMedPilot")
        title.setObjectName("brandTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        chinese_name = QLabel("医研智析")
        chinese_name.setObjectName("brandChineseName")
        chinese_name.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("面向临床与转化医学研究的数据分析与报告生成平台")
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
        for icon_key, tag in (("brand", "生信分析"), ("security", "Meta 分析"), ("license", "科研报告生成")):
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

        version = QLabel("0.1.0-internal-beta / Developer Preview / 本地测试版")
        version.setObjectName("brandVersionLabel")
        version.setWordWrap(True)
        layout.addWidget(version)
        return panel

    def _build_login_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("loginCard")
        card.setMinimumWidth(330)
        card.setMaximumWidth(520)
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 28, 30, 24)
        layout.setSpacing(SPACING["sm"])

        title = QLabel("欢迎使用 BioMedPilot")
        title.setObjectName("loginTitle")
        title.setAlignment(Qt.AlignCenter)
        hint = QLabel("登录以进入项目、工作流与分析任务")
        hint.setObjectName("loginHint")
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addSpacing(SPACING["md"])

        self._username_input = QLineEdit()
        self._username_input.setObjectName("usernameInput")
        self._username_input.setPlaceholderText("用户名")
        user_icon = load_ui01_login_icon("user")
        if not user_icon.isNull():
            self._username_input.addAction(user_icon, QLineEdit.LeadingPosition)
        layout.addWidget(self._username_input)

        self._password_input = QLineEdit()
        self._password_input.setObjectName("passwordInput")
        self._password_input.setPlaceholderText("密码")
        self._password_input.setEchoMode(QLineEdit.Password)
        security_icon = load_ui01_login_icon("security")
        if not security_icon.isNull():
            self._password_input.addAction(security_icon, QLineEdit.LeadingPosition)
        forgot_icon = load_ui01_login_icon("forgot")
        if not forgot_icon.isNull():
            self._password_input.addAction(forgot_icon, QLineEdit.TrailingPosition)
        self._password_input.returnPressed.connect(self.attempt_login)
        layout.addWidget(self._password_input)

        self._error_label = QLabel("")
        self._error_label.setObjectName("loginErrorLabel")
        self._error_label.setWordWrap(True)
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        login_button = QPushButton("进入 BioMedPilot")
        login_button.setObjectName("primaryButton")
        login_button.setIcon(load_ui01_login_icon("login"))
        login_button.setIconSize(QSize(22, 22))
        login_button.clicked.connect(self.attempt_login)
        layout.addWidget(login_button)

        link_row = QHBoxLayout()
        link_row.setContentsMargins(10, 4, 10, 2)
        register_button = QPushButton("注册账号（占位）")
        register_button.setObjectName("linkButton")
        register_button.setIcon(load_ui01_login_icon("register"))
        register_button.setIconSize(QSize(18, 18))
        register_button.setEnabled(False)
        forgot_button = QPushButton("忘记密码（占位）")
        forgot_button.setObjectName("linkButton")
        forgot_button.setIcon(load_ui01_login_icon("forgot"))
        forgot_button.setIconSize(QSize(18, 18))
        forgot_button.setEnabled(False)
        link_row.addWidget(register_button)
        link_row.addStretch(1)
        link_row.addWidget(forgot_button)
        layout.addLayout(link_row)

        layout.addSpacing(SPACING["sm"])
        layout.addWidget(self._build_account_panel())
        layout.addStretch(1)
        return card

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("loginFieldLabel")
        return label

    def _meta_value(self, label: str, value: str, *, icon_key: str | None = None) -> QWidget:
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])
        if icon_key:
            icon_label = QLabel()
            icon_label.setObjectName("loginMetaIcon")
            icon_label.setFixedSize(24, 24)
            icon_label.setPixmap(load_ui01_login_pixmap(icon_key, 20))
            icon_label.setVisible(not icon_label.pixmap().isNull())
            layout.addWidget(icon_label)
        name = QLabel(label)
        name.setObjectName("loginMetaLabel")
        name.setFixedWidth(112)
        value_label = QLabel(value)
        value_label.setObjectName("loginMetaValue")
        value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(name)
        layout.addWidget(value_label, 1)
        return row

    def _build_account_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("loginAccountPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(SPACING["sm"])

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(SPACING["md"])
        user_icon = QLabel()
        user_icon.setObjectName("loginMetaIcon")
        user_icon.setFixedSize(38, 38)
        user_icon.setPixmap(load_ui01_login_pixmap("user", 34))
        user_icon.setVisible(not user_icon.pixmap().isNull())
        header_layout.addWidget(user_icon)

        account_text = QWidget()
        account_layout = QVBoxLayout(account_text)
        account_layout.setContentsMargins(0, 0, 0, 0)
        account_layout.setSpacing(2)
        account_label = QLabel("当前账号等级")
        account_label.setObjectName("loginMetaLabel")
        account_value = QLabel("本地测试用户")
        account_value.setObjectName("loginAccountValue")
        account_layout.addWidget(account_label)
        account_layout.addWidget(account_value)
        header_layout.addWidget(account_text, 1)

        shield_icon = QLabel()
        shield_icon.setObjectName("loginMetaIcon")
        shield_icon.setFixedSize(28, 28)
        shield_icon.setPixmap(load_ui01_login_pixmap("security", 24))
        shield_icon.setVisible(not shield_icon.pixmap().isNull())
        header_layout.addWidget(shield_icon)
        layout.addWidget(header)

        status_row = QHBoxLayout()
        status_row.setSpacing(SPACING["xs"])
        status_row.addWidget(self._status_tile("订阅服务", "未启用", "subscription"))
        status_row.addWidget(self._status_tile("VIP 服务", "占位", "vip"))
        status_row.addWidget(self._status_tile("License 状态", "本地测试", "license"))
        layout.addLayout(status_row)
        return panel

    def _status_tile(self, title: str, value: str, icon_key: str) -> QFrame:
        tile = QFrame()
        tile.setObjectName("loginStatusTile")
        layout = QHBoxLayout(tile)
        layout.setContentsMargins(8, 7, 8, 7)
        layout.setSpacing(SPACING["xs"])
        icon_label = QLabel()
        icon_label.setObjectName("loginMetaIcon")
        icon_label.setFixedSize(28, 28)
        icon_label.setPixmap(load_ui01_login_pixmap(icon_key, 24))
        icon_label.setVisible(not icon_label.pixmap().isNull())
        layout.addWidget(icon_label)

        text_holder = QWidget()
        text_layout = QVBoxLayout(text_holder)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(1)
        title_label = QLabel(title)
        title_label.setObjectName("loginStatusTitle")
        value_label = QLabel(value)
        value_label.setObjectName("loginStatusValue")
        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)
        layout.addWidget(text_holder, 1)
        return tile
