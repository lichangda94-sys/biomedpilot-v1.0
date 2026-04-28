from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.project_navigation_model import NavigationItem, ProjectNavigationModel, ProjectType
from app.ui_style_tokens import COLORS, CONTROL_HEIGHT, SPACING
from app.ui_icon_registry import IconFactory
from core.project_workspace import ProjectWorkspaceState


class SidebarNavigationRow(QFrame):
    clicked = Signal(str)

    def __init__(self, item: NavigationItem, status: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._key = item.key
        self._status = status
        self.setObjectName("navItemRow")
        self.setProperty("workflowStatus", status)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(42)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING["sm"], 0, SPACING["sm"], 0)
        layout.setSpacing(SPACING["sm"])

        self._accent_bar = QFrame()
        self._accent_bar.setObjectName("navItemAccent")
        self._accent_bar.setFixedSize(3, 24)

        self._feature_icon = QLabel()
        self._feature_icon.setObjectName("navFeatureIcon")
        self._feature_icon.setPixmap(IconFactory.sidebar_icon(item.key).pixmap(IconFactory.icon_size("nav")))
        self._feature_icon.setFixedSize(22, 22)
        self._feature_icon.setAlignment(Qt.AlignCenter)

        self._title = QLabel(item.title)
        self._title.setObjectName("navItemTitle")
        self._title.setMinimumWidth(0)

        self._status_icon = QLabel()
        self._status_icon.setObjectName("navStatusIcon")
        self._status_icon.setFixedSize(16, 16)
        self._status_icon.setAlignment(Qt.AlignCenter)

        layout.addWidget(self._accent_bar)
        layout.addWidget(self._feature_icon)
        layout.addWidget(self._title, 1)
        layout.addWidget(self._status_icon)
        self.set_status(status)

    def key(self) -> str:
        return self._key

    def text(self) -> str:
        return self._title.text()

    def isChecked(self) -> bool:
        return self.property("workflowStatus") == "current"

    def setChecked(self, checked: bool) -> None:
        if checked:
            self.set_status("current")

    def click(self) -> None:
        self.clicked.emit(self._key)

    def set_status(self, status: str) -> None:
        self._status = status
        self.setProperty("workflowStatus", status)
        icon_key = {
            "completed": "completed",
            "current": "running",
            "needs_attention": "needs_attention",
            "locked": "locked",
            "not_started": "not_started",
        }.get(status, "not_started")
        self._status_icon.setPixmap(IconFactory.status_icon(icon_key).pixmap(IconFactory.icon_size("status")))
        self.style().unpolish(self)
        self.style().polish(self)
        for child in [self._accent_bar, self._feature_icon, self._title, self._status_icon]:
            child.style().unpolish(child)
            child.style().polish(child)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._key)
        super().mousePressEvent(event)


class TopBar(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("topBar")
        self.setFixedHeight(52)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING["md"], 0, SPACING["md"], 0)
        layout.setSpacing(SPACING["sm"])

        traffic_lights = QHBoxLayout()
        traffic_lights.setSpacing(6)
        for color, name in [
            ("#FF5F57", "windowCloseDot"),
            ("#FFBD2E", "windowMinimizeDot"),
            ("#28C840", "windowZoomDot"),
        ]:
            dot = QLabel("")
            dot.setObjectName(name)
            dot.setFixedSize(12, 12)
            dot.setStyleSheet(f"background: {color}; border-radius: 6px;")
            traffic_lights.addWidget(dot)
        left_spacer = QWidget()
        left_spacer.setFixedWidth(120)
        self._title_label = QLabel(title)
        self._title_label.setObjectName("topBarTitle")
        self._title_label.setAlignment(Qt.AlignCenter)

        actions = QHBoxLayout()
        actions.setSpacing(SPACING["xs"])
        for text, name in [
            ("搜索", "topBarSearchButton"),
            ("帮助", "topBarHelpButton"),
            ("通知", "topBarNotificationButton"),
        ]:
            button = QPushButton("")
            button.setObjectName(name)
            button.setToolTip(text)
            button.setIcon(IconFactory.toolbar_icon({"搜索": "search", "帮助": "attention", "通知": "notifications"}[text]))
            button.setIconSize(IconFactory.icon_size("toolbar"))
            button.setFixedSize(CONTROL_HEIGHT["button"], CONTROL_HEIGHT["button"])
            actions.addWidget(button)
        avatar = QLabel("XL")
        avatar.setObjectName("avatarPlaceholder")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(30, 30)
        actions.addWidget(avatar)
        menu = QLabel("⌄")
        menu.setObjectName("mutedLabel")
        menu.setAlignment(Qt.AlignCenter)
        actions.addWidget(menu)

        layout.addLayout(traffic_lights)
        layout.addWidget(left_spacer)
        layout.addWidget(self._title_label, 1)
        layout.addLayout(actions)


class SidebarNavigation(QFrame):
    def __init__(
        self,
        items: tuple[NavigationItem, ...],
        on_select: Callable[[str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("sidebarNavigation")
        self.setFixedWidth(220)
        self._buttons: dict[str, SidebarNavigationRow] = {}
        self._base_titles: dict[str, str] = {}
        self._base_statuses: dict[str, str] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["md"], SPACING["lg"], SPACING["md"], SPACING["lg"])
        layout.setSpacing(SPACING["xs"])

        logo = QLabel("BioMedPilot")
        logo.setObjectName("sidebarLogo")
        logo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(logo)
        layout.addSpacing(SPACING["md"])
        status_map = {
            "home": "current",
            "data-search": "completed",
            "data-assets": "completed",
            "sample-groups": "needs_attention",
            "deg": "locked",
            "enrichment": "locked",
            "correlation": "not_started",
            "survival": "not_started",
            "visualization": "not_started",
            "reporting": "not_started",
            "tasks": "not_started",
        }
        for item in items:
            status = status_map.get(item.key, "not_started")
            title = item.title
            button = SidebarNavigationRow(item, status)
            button.clicked.connect(on_select)
            self._buttons[item.key] = button
            self._base_titles[item.key] = title
            self._base_statuses[item.key] = status
            layout.addWidget(button)
        layout.addStretch(1)

        profile = QFrame()
        profile.setObjectName("sidebarProfileCard")
        profile.setMinimumHeight(126)
        profile_layout = QVBoxLayout(profile)
        profile_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        profile_layout.setSpacing(SPACING["sm"])
        user_row = QHBoxLayout()
        initials = QLabel("XL")
        initials.setObjectName("sidebarAvatar")
        initials.setAlignment(Qt.AlignCenter)
        initials.setFixedSize(36, 36)
        user_text = QVBoxLayout()
        username = QLabel("xiaoliang")
        username.setObjectName("sidebarUserName")
        user_text.addWidget(username)
        edition = QLabel("高级版")
        edition.setObjectName("mutedLabel")
        user_text.addWidget(edition)
        user_row.addWidget(initials)
        user_row.addLayout(user_text, 1)
        profile_layout.addLayout(user_row)
        storage = QLabel("存储空间\n324 GB / 1 TB")
        storage.setObjectName("mutedLabel")
        profile_layout.addWidget(storage)
        bar = QFrame()
        bar.setObjectName("storageUsageBar")
        bar.setFixedHeight(6)
        profile_layout.addWidget(bar)
        layout.addWidget(profile)

    def set_selected(self, key: str, accent_color: str) -> None:
        for item_key, button in self._buttons.items():
            status = self._base_statuses.get(item_key, "not_started")
            if item_key == key:
                status = "current"
            button.set_status(str(status))

    def buttons(self) -> dict[str, SidebarNavigationRow]:
        return self._buttons

    def _status_symbol(self, status: str) -> str:
        return {
            "completed": "✓",
            "current": "●",
            "needs_attention": "!",
            "locked": "🔒",
            "not_started": "○",
        }.get(status, "○")


class MainWorkspace(QStackedWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("mainWorkspace")


def make_scrollable_workspace_page(page: QWidget) -> QScrollArea:
    scroll_area = QScrollArea()
    scroll_area.setObjectName("mainWorkspaceScrollArea")
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll_area.setWidget(page)
    return scroll_area


class BottomStatusBar(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("bottomStatusBar")
        self.setFixedHeight(32)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING["md"], 0, SPACING["md"], 0)

        self._state_label = QPushButton("就绪")
        self._state_label.setObjectName("statusTaskButton")
        self._version_label = QLabel("BioMedPilot 0.1.0")
        self._version_label.setObjectName("statusLabel")
        self._version_label.setAlignment(Qt.AlignCenter)
        self._resource_label = QLabel("内存 1.2 GB · CPU 8%")
        self._resource_label.setObjectName("statusLabel")
        self._resource_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(self._state_label, 1)
        layout.addWidget(self._version_label, 1)
        layout.addWidget(self._resource_label, 1)

    def set_status(self, state_text: str, version_text: str, resource_text: str) -> None:
        self._state_label.setText(state_text)
        self._version_label.setText(version_text)
        self._resource_label.setText(resource_text)

    def status_text(self) -> str:
        return " · ".join(
            [
                self._state_label.text(),
                self._version_label.text(),
                self._resource_label.text(),
            ]
        )

    def state_button(self) -> QPushButton:
        return self._state_label


class ProjectShellWidget(QWidget):
    def __init__(
        self,
        *,
        project_type: ProjectType,
        title: str,
        accent_color: str,
        home_widget_factory: Callable[[], QWidget],
        settings_panel_factory: Callable[[], QWidget] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._navigation_model = ProjectNavigationModel(project_type)
        self._project_type = project_type
        self._title = title
        self._accent_color = accent_color
        self._project_state: ProjectWorkspaceState | None = None
        self._pages: dict[str, QWidget] = {}
        self._nav_buttons: dict[str, QPushButton] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["sm"])
        root.setSpacing(SPACING["md"])

        if project_type == "bioinformatics":
            self._top_bar = TopBar(title)
            root.addWidget(self._top_bar)
            self._project_status_label = QLabel("未打开项目 · 就绪")
            self._project_status_label.setObjectName("mutedLabel")
        else:
            self._top_bar = self._build_header(title)
            root.addWidget(self._top_bar)

        body = QHBoxLayout()
        body.setSpacing(SPACING["md"])
        root.addLayout(body, 1)

        if project_type == "bioinformatics":
            self._sidebar_navigation = SidebarNavigation(
                self._navigation_model.items,
                self.select_navigation_item,
            )
            self._nav_buttons = self._sidebar_navigation.buttons()
            body.addWidget(self._sidebar_navigation)
        else:
            self._sidebar_navigation = None
            nav = self._build_navigation()
            body.addWidget(nav)

        self._stack = MainWorkspace()
        body.addWidget(self._stack, 1)

        if settings_panel_factory is not None:
            self._settings_panel = settings_panel_factory()
            body.addWidget(self._settings_panel)
        else:
            self._settings_panel = None

        for item in self._navigation_model.items:
            page = home_widget_factory() if item.key == "home" else self._build_placeholder_page(item)
            stack_page = make_scrollable_workspace_page(page) if project_type == "bioinformatics" else page
            self._pages[item.key] = stack_page
            self._stack.addWidget(stack_page)

        status_text = (
            "就绪 · BioMedPilot 0.1.0 · 内存 1.2 GB · CPU 8%"
            if project_type == "bioinformatics"
            else "Current status: Ready · Last log: UI shell loaded · Save: Saved / Mock · Memory 1.2 GB / CPU 8%"
        )
        if project_type == "bioinformatics":
            self._bottom_status_bar = BottomStatusBar()
            self._bottom_status_bar.state_button().clicked.connect(lambda: self.select_navigation_item("tasks"))
            root.addWidget(self._bottom_status_bar)
            self._status_label = QLabel(status_text)
            self._status_label.setObjectName("statusLabel")
        else:
            self._bottom_status_bar = None
            self._status_label = QLabel(status_text)
            self._status_label.setObjectName("statusLabel")
            root.addWidget(self._status_label)
        self.select_navigation_item("home")

    def _build_header(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("heroCard")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        title_label = QLabel(title)
        title_label.setObjectName("workspaceTitle")
        project_status = (
            "未打开项目 · 就绪"
            if self._project_type == "bioinformatics"
            else "No project open · UI shell loaded"
        )
        self._project_status_label = QLabel(project_status)
        self._project_status_label.setObjectName("mutedLabel")
        self._project_status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(title_label)
        layout.addWidget(self._project_status_label)
        return frame

    def _build_navigation(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("sidePanel")
        frame.setFixedWidth(188)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["sm"], SPACING["md"], SPACING["sm"], SPACING["md"])
        layout.setSpacing(SPACING["xs"])
        for item in self._navigation_model.items:
            button = QPushButton(item.title)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, key=item.key: self.select_navigation_item(key))
            self._nav_buttons[item.key] = button
            layout.addWidget(button)
        layout.addStretch(1)
        return frame

    def _build_placeholder_page(self, item: NavigationItem) -> QWidget:
        if self._project_type == "bioinformatics":
            return self._build_bioinformatics_workbench_page(item)
        page = QFrame()
        page.setObjectName("card")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
        layout.setSpacing(SPACING["md"])

        title = QLabel(item.title)
        title.setObjectName("sectionTitle")
        description = QLabel(item.description)
        description.setObjectName("mutedLabel")
        description.setWordWrap(True)
        status = QLabel(f"Status: {item.status_label}")
        status.setObjectName("mutedLabel")
        boundary = QLabel("Demo placeholder. Not implemented yet; does not run statistics, analysis, downloads, or report export.")
        boundary.setObjectName("mutedLabel")
        boundary.setWordWrap(True)
        future = QLabel(f"Future service / view model：{item.future_component}")
        future.setObjectName("mutedLabel")
        mock_output = QLabel("Mock output: empty state. No analysis, download, network request, or report export is triggered.")
        mock_output.setObjectName("mutedLabel")
        mock_output.setWordWrap(True)
        action = QPushButton(item.primary_action)
        action.setEnabled(False)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(status)
        layout.addWidget(boundary)
        layout.addWidget(future)
        layout.addWidget(mock_output)
        layout.addWidget(action, alignment=Qt.AlignLeft)
        layout.addStretch(1)
        return page

    def _build_bioinformatics_workbench_page(self, item: NavigationItem) -> QWidget:
        page_content = self._bioinformatics_page_content(item.key)
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["md"])

        header = QFrame()
        header.setObjectName("card")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["lg"])
        title = QLabel(item.title)
        title.setObjectName("sectionTitle")
        description = QLabel(item.description)
        description.setObjectName("mutedLabel")
        description.setWordWrap(True)
        status = QLabel(f"{item.status_label} · 请先完成必要的数据和参数设置。")
        status.setObjectName("friendlyStatusLabel")
        status.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addWidget(description)
        header_layout.addWidget(status)
        layout.addWidget(header)

        content = QGridLayout()
        content.setSpacing(SPACING["md"])
        layout.addLayout(content, 1)
        content.addWidget(
            self._bio_page_panel(
                "输入区",
                page_content["inputs"],
            ),
            0,
            0,
        )
        content.addWidget(
            self._bio_page_panel(
                "输出预览区",
                page_content["outputs"],
            ),
            0,
            1,
        )
        content.addWidget(
            self._bio_page_panel(
                "空状态",
                page_content["empty"],
            ),
            1,
            0,
        )
        content.addWidget(
            self._bio_page_panel("状态说明", page_content["status"]),
            1,
            1,
        )

        action_row = QHBoxLayout()
        action = QPushButton(item.primary_action)
        action.setObjectName("primaryButton")
        action.setEnabled(False)
        hint = QLabel("提示：该功能需要数据、分组和运行环境准备完成后才能启动。")
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        action_row.addWidget(action)
        action_row.addWidget(hint, 1)
        layout.addLayout(action_row)
        return page

    def _bioinformatics_page_content(self, key: str) -> dict[str, list[str]]:
        content = {
            "data-search": {
                "inputs": ["数据源：GEO / TCGA / GTEx", "关键词：lung cancer", "物种：Homo sapiens", "筛选条件：表达谱数据"],
                "outputs": ["候选数据集：GSE31210、TCGA-LUAD、GTEx Lung", "预览字段：样本数、平台、分组、更新时间"],
                "empty": ["尚未执行检索。", "输入关键词并选择数据源后，这里会展示候选数据集。"],
                "status": ["Requires setup", "检索入口已准备，网络与账号配置完成后可连接真实数据源。"],
            },
            "data-assets": {
                "inputs": ["表达矩阵：未选择", "样本注释表：未选择", "平台注释：可选", "临床信息：可选"],
                "outputs": ["资产清单预览：表达矩阵、样本表、基因注释、临床表", "质量提示：列名、样本 ID、基因 ID 将在导入后检查"],
                "empty": ["当前项目还没有可识别的数据资产。", "导入文件后会自动汇总资产类型和可用状态。"],
                "status": ["Needs data", "不会修改原始文件，只生成项目内资产索引。"],
            },
            "sample-groups": {
                "inputs": ["分组字段：condition", "病例组：Tumor", "对照组：Normal", "批次字段：batch"],
                "outputs": ["分组预览：病例 256 · 对照 256", "平衡性检查：样本数量、缺失标签、批次分布"],
                "empty": ["尚未建立样本分组。", "识别分组后，差异分析和可视化页面会使用同一套比较组。"],
                "status": ["Needs data", "自动识别结果需要人工确认后再用于分析。"],
            },
            "deg": {
                "inputs": ["数据集：TCGA-LUAD", "比较组：Tumor vs Normal", "方法：DESeq2", "阈值：log2FC 1.0 · FDR 0.05"],
                "outputs": ["Volcano Plot 预览", "Top genes 表格：Gene、log2FC、FDR、方向", "结果摘要：上调、下调、不显著"],
                "empty": ["尚未运行差异表达分析。", "确认数据和分组后即可生成 DEG 结果。"],
                "status": ["Needs data", "本页面只准备任务和展示预览，不在未确认时运行统计模型。"],
            },
            "enrichment": {
                "inputs": ["输入基因集：差异基因列表", "数据库：GO BP / KEGG / Hallmark", "背景集：表达矩阵检测基因", "校正方法：BH"],
                "outputs": ["富集条形图预览", "通路表格：Term、Count、FDR、Genes", "进度：运行中 45%"],
                "empty": ["尚未获得可用于富集分析的基因列表。", "完成差异分析后可自动带入上调和下调基因。"],
                "status": ["Coming soon", "通路结果会在任务完成后进入近期结果列表。"],
            },
            "correlation": {
                "inputs": ["目标基因：EGFR", "关联变量：免疫评分 / 临床表型", "相关方法：Spearman", "样本范围：当前比较组"],
                "outputs": ["散点图矩阵预览", "相关系数表：变量、rho、P value、FDR", "显著相关变量高亮"],
                "empty": ["尚未选择目标基因或表型变量。", "选择变量后会展示相关性预览和可视化结果。"],
                "status": ["Coming soon", "相关性结果用于探索性分析，需要结合研究设计解读。"],
            },
            "survival": {
                "inputs": ["目标基因：EGFR", "分组方式：中位数切分", "结局：Overall survival", "临床字段：time / status"],
                "outputs": ["Kaplan-Meier 曲线预览", "风险表：High / Low expression", "统计：HR、95% CI、Log-rank P"],
                "empty": ["尚未连接可用的生存随访数据。", "导入临床表并映射 time/status 后可生成生存分析。"],
                "status": ["Requires setup", "需要确认随访时间单位和结局编码，避免错误解释。"],
            },
            "visualization": {
                "inputs": ["图表类型：火山图 / 热图 / 箱线图 / 通路图", "结果来源：LUAD_DEG_20240520", "配色：科研默认", "导出格式：PNG / PDF"],
                "outputs": ["图表画廊预览", "待导出：Volcano Plot、Heatmap、Top pathway barplot", "图注与参数摘要"],
                "empty": ["当前没有可重新生成的图表。", "完成分析后可在此统一管理和导出图表。"],
                "status": ["Needs data", "重新生成图表只使用已有结果，不重新运行分析。"],
            },
            "reporting": {
                "inputs": ["报告模板：生信分析标准报告", "结果包：LUAD 项目结果", "包含内容：方法、表格、图表、系统消息", "导出格式：DOCX / PDF"],
                "outputs": ["报告目录预览", "章节：数据来源、样本分组、差异分析、富集分析、可视化", "图表清单和参数附录"],
                "empty": ["尚未选择可导出的结果包。", "至少完成一个分析结果后可生成报告。"],
                "status": ["Coming soon", "报告导出会保留方法参数，便于医学科研复核。"],
            },
            "tasks": {
                "inputs": ["任务范围：当前项目", "状态筛选：就绪 / 运行中 / 已完成 / 需要处理", "时间范围：最近 7 天", "结果类型：全部"],
                "outputs": ["任务列表预览：LUAD_DEG、LUAD_KEGG、LUAD_Heatmap", "状态列：运行中、已完成、等待中", "可查看每个任务的结果摘要"],
                "empty": ["当前没有需要处理的任务。", "启动分析后，这里会显示任务进度和结果入口。"],
                "status": ["就绪", "任务中心用于观察进度，不显示内部日志和技术堆栈。"],
            },
        }
        return content.get(
            key,
            {
                "inputs": ["数据集：未选择", "样本分组：需要配置", "分析参数：可在右侧面板调整"],
                "outputs": ["预览将在数据准备完成后显示。"],
                "empty": ["当前页面尚未收到可分析数据。"],
                "status": ["就绪", "请按页面提示完成数据准备。"],
            },
        )

    def _bio_page_panel(
        self,
        title: str,
        lines: list[str],
        row_span: int = 1,
        col_span: int = 1,
    ) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 700; background: transparent;")
        layout.addWidget(title_label)
        for line in lines:
            label = QLabel(line)
            label.setObjectName("mutedLabel")
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addStretch(1)
        return frame

    def select_navigation_item(self, key: str) -> None:
        item = self._navigation_model.select(key)
        for item_key, button in self._nav_buttons.items():
            if hasattr(button, "setChecked"):
                button.setChecked(item_key == key)
            if isinstance(button, QPushButton):
                if item_key == key:
                    button.setStyleSheet(f"background: {COLORS['bio_soft']}; color: {self._accent_color}; font-weight: 600;")
                else:
                    button.setStyleSheet("")
        if self._sidebar_navigation is not None:
            self._sidebar_navigation.set_selected(key, self._accent_color)
        self._stack.setCurrentWidget(self._pages[key])
        project_text = self._project_state.name if self._project_state else "none"
        save_text = self._project_state.status if self._project_state else "no project"
        if self._project_type == "bioinformatics":
            project_text = self._project_state.name if self._project_state else "未打开项目"
            self._status_label.setText(
                f"就绪 · 当前页面：{item.title} · 项目：{project_text} · BioMedPilot 0.1.0 · 内存 1.2 GB · CPU 8%"
            )
            if self._bottom_status_bar is not None:
                self._bottom_status_bar.set_status(
                    f"就绪 · 当前页面：{item.title}",
                    "BioMedPilot 0.1.0",
                    "内存 1.2 GB · CPU 8%",
                )
        else:
            self._status_label.setText(
                f"Current page: {item.title} · Project: {project_text} · Save: {save_text}"
            )

    def current_page_title(self) -> str:
        return self._navigation_model.current_item.title

    def current_navigation_key(self) -> str:
        return self._navigation_model.current_item.key

    def current_status_text(self) -> str:
        return self._status_label.text()

    def set_project_state(self, state: ProjectWorkspaceState | None) -> None:
        self._project_state = state
        if state is None:
            if self._project_type == "bioinformatics":
                self._project_status_label.setText("未打开项目 · 就绪")
                self._status_label.setText(
                    f"就绪 · 当前页面：{self.current_page_title()} · 项目：未打开项目 · BioMedPilot 0.1.0 · 内存 1.2 GB · CPU 8%"
                )
                if self._bottom_status_bar is not None:
                    self._bottom_status_bar.set_status(
                        f"就绪 · 当前页面：{self.current_page_title()}",
                        "BioMedPilot 0.1.0",
                        "内存 1.2 GB · CPU 8%",
                    )
            else:
                self._project_status_label.setText("No project open · UI shell loaded")
                self._status_label.setText(
                    f"Current page: {self.current_page_title()} · Project: none · Save: no project"
                )
            return
        self._project_status_label.setText(
            f"{state.name} · {state.status} · {state.last_saved_at}"
        )
        if self._project_type == "bioinformatics":
            self._status_label.setText(
                f"就绪 · 当前页面：{self.current_page_title()} · 项目：{state.name} · BioMedPilot 0.1.0 · 内存 1.2 GB · CPU 8%"
            )
            if self._bottom_status_bar is not None:
                self._bottom_status_bar.set_status(
                    f"就绪 · 当前页面：{self.current_page_title()}",
                    "BioMedPilot 0.1.0",
                    "内存 1.2 GB · CPU 8%",
                )
        else:
            self._status_label.setText(
                f"Current page: {self.current_page_title()} · Project: {state.name} · Save: {state.status}"
            )

    def current_project_state(self) -> ProjectWorkspaceState | None:
        return self._project_state

    def navigation_titles(self) -> list[str]:
        return self._navigation_model.titles()
