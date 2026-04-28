from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

from core.config import AppConfig
from core.data_dirs import DataDirectories
from tests.qt_test_utils import get_qapplication


class WorkbenchShellTests(unittest.TestCase):
    def test_workbench_home_contains_two_primary_entries(self) -> None:
        get_qapplication()
        from app.workbench_home_widget import WorkbenchHomeWidget

        widget = WorkbenchHomeWidget(
            on_open_bioinformatics=lambda: None,
            on_open_meta_analysis=lambda: None,
        )

        self.assertIn("Bioinformatics", widget.entry_titles())
        self.assertIn("Meta Analysis", widget.entry_titles())
        self.assertIn("internal testing build", widget.capability_notice_text())
        self.assertEqual(
            widget.project_action_labels(),
            ["Create Project", "Open Project", "Load Demo Project"],
        )
        self.assertIn("No project opened", widget.current_project_text())

    def test_bioinformatics_shell_navigation_updates_current_page_title(self) -> None:
        get_qapplication()
        from app.bioinformatics_workspace_widget import BioinformaticsWorkspaceWidget

        widget = BioinformaticsWorkspaceWidget()

        widget.select_navigation_item("deg")
        self.assertEqual(widget.current_page_title(), "差异分析")
        self.assertEqual(widget.current_navigation_key(), "deg")
        self.assertIn("差异分析", widget.current_status_text())

        widget.select_navigation_item("enrichment")
        self.assertEqual(widget.current_page_title(), "富集分析")
        self.assertEqual(widget.current_navigation_key(), "enrichment")

    def test_bioinformatics_workspace_exposes_production_shell_copy(self) -> None:
        get_qapplication()
        from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget
        from app.bioinformatics_workspace_widget import AnalysisSettingsPanel, BioinformaticsWorkspaceWidget
        from app.project_shell_widget import BottomStatusBar, MainWorkspace, SidebarNavigation, TopBar

        widget = BioinformaticsWorkspaceWidget()

        self.assertIsNotNone(widget.findChild(TopBar))
        self.assertIsNotNone(widget.findChild(SidebarNavigation))
        self.assertIsNotNone(widget.findChild(MainWorkspace))
        self.assertIsNotNone(widget.findChild(AnalysisSettingsPanel))
        self.assertIsNotNone(widget.findChild(BottomStatusBar))
        self.assertEqual(widget.findChild(TopBar).height(), 52)
        self.assertEqual(widget.findChild(SidebarNavigation).width(), 220)
        self.assertEqual(widget.findChild(AnalysisSettingsPanel).width(), 300)
        self.assertEqual(widget.findChild(BottomStatusBar).height(), 32)
        self.assertEqual(
            widget.navigation_titles(),
            [
                "首页",
                "数据检索",
                "数据资产",
                "样本分组",
                "差异分析",
                "富集分析",
                "相关性分析",
                "生存分析",
                "可视化",
                "报告导出",
                "任务中心",
            ],
        )
        visible_text = "\n".join(
            [label.text() for label in widget.findChildren(QLabel)]
            + [button.text() for button in widget.findChildren(QPushButton)]
        )
        for expected in [
            "数据源",
            "当前项目",
            "活跃任务",
            "样本数",
            "GEO · TCGA · GTEx",
            "Lung Cancer Study",
            "TCGA-LUAD",
            "病例 256 · 对照 256",
            "差异表达 · Volcano Plot",
            "差异表达 · Heatmap (Top 50)",
            "上调 286 · 下调 194 · 不显著 18,420",
            "对照组 · 病例组",
            "查看详情",
            "近期结果",
            "LUAD_DEG_20240520",
            "LUAD_KEGG_20240519",
            "LUAD_Survival_20240518",
            "LUAD_Correlation_20240518",
            "分析流程",
            "富集分析：运行中 45%",
            "系统消息",
            "数据源更新：GEO 索引已同步",
            "分析设置",
            "就绪",
            "BioMedPilot 0.1.0",
            "示例项目预览 · Demo Preview",
            "当前展示为示例数据。导入真实数据后，这里将显示你的项目结果。",
            "分析前检查",
            "表达矩阵",
            "Ready",
            "样本分组",
            "Needs attention",
            "样本分组尚未完成，无法开始差异分析。请先进入样本分组页面完成分组。",
            "推荐下一步：检查样本分组",
        ]:
            self.assertIn(expected, visible_text)
        top_bar = widget.findChild(TopBar)
        self.assertEqual(
            sorted(button.toolTip() for button in top_bar.findChildren(QPushButton) if button.toolTip()),
            ["帮助", "搜索", "通知"],
        )
        for forbidden in ["debug", "sandbox", "fixture", "traceback", "raw JSON", "Mock", "placeholder", "stack trace"]:
            self.assertNotIn(forbidden, visible_text)

    def test_bioinformatics_navigation_pages_expose_production_skeletons(self) -> None:
        get_qapplication()
        from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget
        from app.bioinformatics_workspace_widget import BioinformaticsWorkspaceWidget

        widget = BioinformaticsWorkspaceWidget()
        expected_pages = {
            "data-search": ("数据检索", "开始检索", "Dataset ID"),
            "enrichment": ("富集分析", "运行富集分析", "Dotplot preview"),
            "correlation": ("相关性分析", "运行相关性分析", "Scatter preview"),
            "survival": ("生存分析", "运行生存分析", "KM plot preview"),
        }

        for key, (title, action, preview) in expected_pages.items():
            widget.select_navigation_item(key)
            self.assertEqual(widget.current_page_title(), title)
            visible_text = "\n".join(
                [label.text() for label in widget.findChildren(QLabel)]
                + [button.text() for button in widget.findChildren(QPushButton)]
            )
            table_text = "\n".join(
                table.horizontalHeaderItem(column).text()
                for table in widget.findChildren(QTableWidget)
                for column in range(table.columnCount())
                if table.horizontalHeaderItem(column) is not None
            )
            for expected in [title, "输入区", "输出 / 预览区", "空状态", "状态说明", action]:
                self.assertIn(expected, visible_text)
            self.assertIn(preview, visible_text + "\n" + table_text)
            for forbidden in ["debug", "test", "raw JSON", "traceback"]:
                self.assertNotIn(forbidden, visible_text)

    def test_bioinformatics_workflow_navigation_statuses_and_status_bar_action(self) -> None:
        get_qapplication()
        from PySide6.QtWidgets import QLabel, QPushButton
        from app.bioinformatics_workspace_widget import BioinformaticsWorkspaceWidget
        from app.project_shell_widget import BottomStatusBar, SidebarNavigation, SidebarNavigationRow

        widget = BioinformaticsWorkspaceWidget()
        sidebar = widget.findChild(SidebarNavigation)
        self.assertIsNotNone(sidebar)
        rows = sidebar.findChildren(SidebarNavigationRow)
        self.assertEqual(len(rows), 11)
        row_by_title = {row.text(): row for row in rows}
        expected_statuses = {
            "首页": "current",
            "数据检索": "completed",
            "数据资产": "completed",
            "样本分组": "needs_attention",
            "差异分析": "locked",
            "富集分析": "locked",
            "相关性分析": "not_started",
            "任务中心": "not_started",
        }
        for title, status in expected_statuses.items():
            self.assertEqual(row_by_title[title].property("workflowStatus"), status)

        widget.select_navigation_item("deg")
        self.assertIn("请先完成样本分组后再进入差异分析", widget.current_status_text())
        bottom_status = widget.findChild(BottomStatusBar)
        self.assertIsNotNone(bottom_status)
        bottom_status.state_button().click()
        self.assertEqual(widget.current_navigation_key(), "tasks")

        visible_text = "\n".join(
            [label.text() for label in widget.findChildren(QLabel)]
            + [button.text() for button in widget.findChildren(QPushButton)]
        )
        for forbidden in ["debug", "test", "raw JSON", "traceback", "stack trace"]:
            self.assertNotIn(forbidden, visible_text)

    def test_bioinformatics_visual_system_exposes_icons_and_stable_panel_rows(self) -> None:
        get_qapplication()
        from PySide6.QtWidgets import QLabel, QFrame, QPushButton, QScrollArea
        from app.bioinformatics_workspace_widget import AnalysisSettingsPanel, BioinformaticsWorkspaceWidget
        from app.project_shell_widget import SidebarNavigation, TopBar
        from app.ui_style_tokens import CONTROL_HEIGHT, FONT_SIZE, ICON_SIZE
        from app.ui_icon_registry import IconFactory

        self.assertEqual(FONT_SIZE["app_title"], 24)
        self.assertEqual(ICON_SIZE["nav"], 18)
        self.assertEqual(CONTROL_HEIGHT["primary"], 42)
        for icon_name in ["home", "search", "assets", "groups", "deg", "completed", "attention", "locked"]:
            self.assertFalse(IconFactory.toolbar_icon(icon_name).isNull())

        widget = BioinformaticsWorkspaceWidget()
        sidebar = widget.findChild(SidebarNavigation)
        self.assertTrue(all(not button.icon().isNull() for button in sidebar.findChildren(QPushButton)))
        top_bar = widget.findChild(TopBar)
        self.assertTrue(all(not button.icon().isNull() for button in top_bar.findChildren(QPushButton) if button.toolTip()))

        settings = widget.findChild(AnalysisSettingsPanel)
        self.assertIsNotNone(settings)
        self.assertIsNotNone(settings.findChild(QScrollArea, "analysisSettingsScrollArea"))
        self.assertGreaterEqual(len(widget.findChildren(QScrollArea, "mainWorkspaceScrollArea")), 11)
        self.assertGreaterEqual(len(widget.findChildren(QFrame, "emptyStateCard")), 6)
        rows = settings.findChildren(QFrame, "readinessRow")
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row.minimumHeight() >= 28 for row in rows))
        badges = settings.findChildren(QLabel, "readinessBadgeWarning") + settings.findChildren(QLabel, "readinessBadgeReady")
        self.assertEqual(len(badges), 4)
        self.assertTrue(all(badge.wordWrap() for badge in badges))
        chips = settings.findChildren(QFrame, "comparisonControlChip") + settings.findChildren(QFrame, "comparisonCaseChip")
        self.assertEqual(len(chips), 2)
        self.assertTrue(all(chip.minimumHeight() >= 66 for chip in chips))

    def test_data_assets_page_exposes_asset_table_and_next_steps(self) -> None:
        get_qapplication()
        from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget
        from app.bioinformatics_workspace_widget import BioinformaticsWorkspaceWidget

        widget = BioinformaticsWorkspaceWidget()
        widget.select_navigation_item("data-assets")

        visible_text = "\n".join(
            [label.text() for label in widget.findChildren(QLabel)]
            + [button.text() for button in widget.findChildren(QPushButton)]
        )
        for expected in [
            "数据资产概览",
            "资产分类表",
            "资产详情面板",
            "识别数据资产",
            "预览",
            "重新分配类型",
            "导入缺失文件",
            "请先处理“缺失”和“不可用”的资产，再进入样本分组和差异分析。",
        ]:
            self.assertIn(expected, visible_text)
        tables = widget.findChildren(QTableWidget, "dataAssetClassificationTable")
        self.assertEqual(len(tables), 1)
        table_text = "\n".join(
            tables[0].item(row, column).text()
            for row in range(tables[0].rowCount())
            for column in range(tables[0].columnCount())
        )
        for expected in [
            "表达矩阵",
            "样本注释",
            "临床数据",
            "平台注释",
            "原始补充文件",
            "支持文档",
            "已识别",
            "需要检查",
            "缺失",
            "不可用",
        ]:
            self.assertIn(expected, table_text)

    def test_sample_groups_page_exposes_sample_table_and_group_warnings(self) -> None:
        get_qapplication()
        from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget
        from app.bioinformatics_workspace_widget import BioinformaticsWorkspaceWidget

        widget = BioinformaticsWorkspaceWidget()
        widget.select_navigation_item("sample-groups")

        visible_text = "\n".join(
            [label.text() for label in widget.findChildren(QLabel)]
            + [button.text() for button in widget.findChildren(QPushButton)]
        )
        for expected in [
            "样本表格",
            "分组统计卡片",
            "自动识别分组",
            "手动编辑分组",
            "分组检查提示",
            "请至少设置两个分析组。",
            "Control 组 n=256",
            "Case 组 n=256",
            "未分组 n=12",
            "有未分组样本时，请先手动指定最终分组或设为不纳入，再继续差异分析。",
        ]:
            self.assertIn(expected, visible_text)
        tables = widget.findChildren(QTableWidget, "sampleGroupingTable")
        self.assertEqual(len(tables), 1)
        headers = [tables[0].horizontalHeaderItem(index).text() for index in range(7)]
        self.assertEqual(headers, ["Sample ID", "样本标题", "来源", "自动识别分组", "最终分组", "是否纳入", "备注"])
        self.assertEqual(tables[0].item(4, 4).text(), "未分组")

    def test_visualization_page_exposes_chart_builder_layout(self) -> None:
        get_qapplication()
        from PySide6.QtWidgets import QLabel, QPushButton
        from app.bioinformatics_workspace_widget import BioinformaticsWorkspaceWidget

        widget = BioinformaticsWorkspaceWidget()
        widget.select_navigation_item("visualization")
        visible_text = "\n".join(
            [label.text() for label in widget.findChildren(QLabel)]
            + [button.text() for button in widget.findChildren(QPushButton)]
        )
        for expected in [
            "图表类型列表",
            "Volcano Plot",
            "Heatmap",
            "Boxplot",
            "PCA Plot",
            "GO Dotplot",
            "KEGG Dotplot",
            "GSEA Curve",
            "Correlation Scatter",
            "KM Curve",
            "图表预览",
            "图表设置",
            "标题：LUAD differential expression",
            "坐标轴：log2FC / -log10(FDR)",
            "字体大小：12 pt",
            "图例位置：右上",
            "图片尺寸：1800 × 1400 px",
            "分辨率：300 dpi",
            "加入报告：是",
            "重新生成",
            "导出 PNG",
            "导出 PDF",
            "加入报告",
            "导出 PNG / PDF Requires setup",
        ]:
            self.assertIn(expected, visible_text)

    def test_reporting_page_exposes_report_export_setup_state(self) -> None:
        get_qapplication()
        from PySide6.QtWidgets import QCheckBox, QLabel, QPushButton
        from app.bioinformatics_workspace_widget import BioinformaticsWorkspaceWidget

        widget = BioinformaticsWorkspaceWidget()
        widget.select_navigation_item("reporting")
        visible_text = "\n".join(
            [label.text() for label in widget.findChildren(QLabel)]
            + [button.text() for button in widget.findChildren(QPushButton)]
            + [checkbox.text() for checkbox in widget.findChildren(QCheckBox)]
        )
        for expected in [
            "报告模板选择",
            "报告内容勾选",
            "语言选择",
            "格式选择",
            "预览区域",
            "研究问题",
            "数据集信息",
            "数据处理流程",
            "样本分组",
            "差异分析结果",
            "富集分析结果",
            "相关性分析结果",
            "生存分析结果",
            "图表",
            "方法草稿",
            "生成报告",
            "预览报告",
            "导出 Word",
            "导出 PDF",
            "导出图表包",
            "Word：Requires setup",
            "PDF：Requires setup",
            "图表包：Coming soon",
            "导出 Word / PDF / 图表包 Coming soon",
        ]:
            self.assertIn(expected, visible_text)

    def test_differential_analysis_page_exposes_near_real_workflow_preview(self) -> None:
        get_qapplication()
        from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget
        from app.bioinformatics_workspace_widget import BioinformaticsWorkspaceWidget, VolcanoPlotPreview

        widget = BioinformaticsWorkspaceWidget()
        widget.select_navigation_item("deg")

        visible_text = "\n".join(
            [label.text() for label in widget.findChildren(QLabel)]
            + [button.text() for button in widget.findChildren(QPushButton)]
        )
        for expected in [
            "差异分析",
            "比较组卡片",
            "对照组：Normal",
            "病例组：Tumor",
            "样本数：病例 256 · 对照 256",
            "分析参数摘要",
            "方法：DESeq2",
            "|log2FC| ≥ 1.0",
            "FDR < 0.05",
            "Volcano Plot 预览",
            "上调 286 · 下调 194 · 不显著 18,420",
            "DEG table preview",
            "样本分组信息缺失，无法运行差异表达分析。请先进入样本分组页面，为样本指定对照组和病例组。",
            "前往样本分组",
            "开始差异分析",
            "导出 DEG 表",
            "查看火山图",
        ]:
            self.assertIn(expected, visible_text)

        self.assertGreaterEqual(len(widget.findChildren(VolcanoPlotPreview)), 1)
        tables = widget.findChildren(QTableWidget, "degTablePreview")
        self.assertEqual(len(tables), 1)
        table = tables[0]
        self.assertEqual([table.horizontalHeaderItem(i).text() for i in range(4)], ["Gene", "log2FC", "FDR", "Regulation"])
        self.assertEqual(table.item(0, 0).text(), "EGFR")
        for forbidden in ["traceback", "raw JSON"]:
            self.assertNotIn(forbidden, visible_text)

    def test_task_center_exposes_user_friendly_errors_and_task_statuses(self) -> None:
        get_qapplication()
        from PySide6.QtWidgets import QLabel, QPushButton, QFrame, QTableWidget, QTabWidget, QToolButton
        from app.bioinformatics_workspace_widget import BioinformaticsWorkspaceWidget
        from app.project_shell_widget import BottomStatusBar

        widget = BioinformaticsWorkspaceWidget()
        widget.select_navigation_item("tasks")

        tabs = widget.findChild(QTabWidget, "taskStatusTabs")
        self.assertIsNotNone(tabs)
        self.assertEqual([tabs.tabText(index) for index in range(tabs.count())], ["Running", "Completed", "Failed", "All"])

        tables = widget.findChildren(QTableWidget, "taskCenterTable")
        self.assertEqual(len(tables), 1)
        table = tables[0]
        self.assertEqual(
            [table.horizontalHeaderItem(index).text() for index in range(table.columnCount())],
            ["任务名称", "项目", "类型", "进度", "状态", "更新时间", "操作"],
        )
        table_text = "\n".join(
            table.item(row, column).text()
            for row in range(table.rowCount())
            for column in range(table.columnCount())
        )
        for expected in ["Running", "Completed", "Failed", "Needs Attention", "Waiting"]:
            self.assertIn(expected, table_text)

        visible_text = "\n".join(
            [label.text() for label in widget.findChildren(QLabel)]
            + [button.text() for button in widget.findChildren(QPushButton)]
            + [button.text() for button in widget.findChildren(QToolButton)]
            + [tabs.tabText(index) for index in range(tabs.count())]
        )
        for expected in [
            "任务中心",
            "任务表",
            "任务详情面板",
            "用户友好错误区",
            "发生了什么：样本分组信息缺失，无法运行差异表达分析。",
            "为什么不能继续：差异分析需要明确的对照组和病例组。",
            "用户应该去哪里修复：请先进入样本分组页面，为样本指定对照组和病例组。",
            "前往样本分组",
            "Technical Details",
        ]:
            self.assertIn(expected, visible_text)

        technical_details = widget.findChild(QFrame, "technicalDetailsFrame")
        self.assertIsNotNone(technical_details)
        self.assertTrue(technical_details.isHidden())
        self.assertIn("需要处理：样本分组缺失", widget.current_status_text())
        bottom_status = widget.findChild(BottomStatusBar)
        self.assertIsNotNone(bottom_status)
        self.assertIn("需要处理：样本分组缺失", bottom_status.status_text())
        for forbidden in ["traceback", "KeyError", "raw JSON", "stack trace", "internal parser output"]:
            self.assertNotIn(forbidden, visible_text)
            self.assertNotIn(forbidden, table_text)

    def test_meta_workspace_navigation_contains_demo_modules_and_statuses(self) -> None:
        get_qapplication()
        from app.meta_analysis_workspace_widget import MetaAnalysisWorkspaceWidget

        widget = MetaAnalysisWorkspaceWidget()

        for title in [
            "项目总览",
            "PICO / 检索",
            "文献导入",
            "文献筛选",
            "数据提取",
            "Profile Readiness",
            "统计分析",
            "报告导出",
        ]:
            self.assertIn(title, widget.navigation_titles())

        widget.select_navigation_item("analysis")
        self.assertEqual(widget.current_page_title(), "统计分析")
        self.assertIn("Project: none", widget.current_status_text())

    def test_meta_workspace_home_exposes_professional_dashboard_regions(self) -> None:
        get_qapplication()
        from PySide6.QtWidgets import QLabel, QTableWidget
        from app.meta_analysis_workspace_widget import MetaAnalysisWorkspaceWidget

        widget = MetaAnalysisWorkspaceWidget()

        visible_text = "\n".join(label.text() for label in widget.findChildren(QLabel))
        for expected in [
            "Meta 分析项目总览",
            "当前项目进度",
            "中央森林图结果区",
            "PRISMA 流程",
            "分析设置",
            "GRADE 概览",
            "RoB 2.0",
            "最近输出文件",
            "Demo data",
        ]:
            self.assertIn(expected, visible_text)

        forest_tables = widget.findChildren(QTableWidget, "metaForestPlotTable")
        self.assertEqual(len(forest_tables), 1)

    def test_main_window_title_updates_when_system_changes(self) -> None:
        get_qapplication()
        from app.main_window import MainWindow

        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            data_dirs = DataDirectories(
                root_dir=root_dir,
                config_dir=root_dir / "config",
                logs_dir=root_dir / "logs",
                state_dir=root_dir / "state",
                cache_dir=root_dir / "cache",
            )
            data_dirs.ensure_exists()
            window = MainWindow(
                config=AppConfig(app_name="Model9", app_slug="model9", organization_name="model9"),
                data_dirs=data_dirs,
            )

            self.assertEqual(window.current_system_title(), "BioMedPilot · 生信分析")
            self.assertEqual(window.current_workspace_key(), "bioinformatics")
            self.assertEqual(window.current_project_summary_text(), "No project opened")

            window.open_bioinformatics_workspace()
            self.assertEqual(window.current_system_title(), "BioMedPilot · 生信分析")
            self.assertEqual(window.current_workspace_key(), "bioinformatics")

            window.open_meta_analysis_workspace()
            self.assertEqual(window.current_system_title(), "BioMedPilot · Meta 分析")
            self.assertEqual(window.current_workspace_key(), "meta_analysis")

    def test_home_project_actions_create_and_load_demo_project(self) -> None:
        get_qapplication()
        from app.main_window import MainWindow

        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            data_dirs = DataDirectories(
                root_dir=root_dir,
                config_dir=root_dir / "config",
                logs_dir=root_dir / "logs",
                state_dir=root_dir / "state",
                cache_dir=root_dir / "cache",
            )
            data_dirs.ensure_exists()
            window = MainWindow(
                config=AppConfig(app_name="Model9", app_slug="model9", organization_name="model9"),
                data_dirs=data_dirs,
            )

            created = window.create_internal_testing_meta_project()

            self.assertEqual(created.project_id, "internal-testing-meta-project")
            self.assertIn("Internal Testing Meta Project", window.current_project_summary_text())
            self.assertIn("Internal Testing Meta Project", window._workbench_home_widget.current_project_text())

            demo = window.load_demo_profile_readiness_project()
            self.assertEqual(demo.project_id, "demo-profile-readiness")
            self.assertIn("Demo Profile Readiness Project", window._workbench_home_widget.current_project_text())

    def test_main_window_project_create_open_save_updates_workspace_state(self) -> None:
        get_qapplication()
        from app.main_window import MainWindow

        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            data_dirs = DataDirectories(
                root_dir=root_dir,
                config_dir=root_dir / "config",
                logs_dir=root_dir / "logs",
                state_dir=root_dir / "state",
                cache_dir=root_dir / "cache",
            )
            data_dirs.ensure_exists()
            window = MainWindow(
                config=AppConfig(app_name="Model9", app_slug="model9", organization_name="model9"),
                data_dirs=data_dirs,
            )

            state = window.create_project_workspace(
                project_type="meta_analysis",
                name="Diagnostic Accuracy Demo",
                project_id="diagnostic-demo",
            )

            self.assertEqual(window.current_workspace_key(), "meta_analysis")
            self.assertEqual(window.current_project_state().project_id, "diagnostic-demo")

            saved = window.save_current_project_workspace()
            self.assertIsNotNone(saved)
            self.assertEqual(saved.status, "saved")

            opened = window.open_project_workspace(state.project_dir)
            self.assertEqual(opened.name, "Diagnostic Accuracy Demo")
            self.assertEqual(window.current_workspace_key(), "meta_analysis")

    def test_main_window_explicitly_saves_and_loads_profile_editor_rows(self) -> None:
        get_qapplication()
        from app.main_window import MainWindow

        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            data_dirs = DataDirectories(
                root_dir=root_dir,
                config_dir=root_dir / "config",
                logs_dir=root_dir / "logs",
                state_dir=root_dir / "state",
                cache_dir=root_dir / "cache",
            )
            data_dirs.ensure_exists()
            window = MainWindow(
                config=AppConfig(app_name="Model9", app_slug="model9", organization_name="model9"),
                data_dirs=data_dirs,
            )
            state = window.create_project_workspace(
                project_type="meta_analysis",
                name="Row Persistence Demo",
                project_id="row-persistence-demo",
            )
            editor = window._meta_analysis_workspace_widget.row_editor()
            editor.set_profile_type("BIOMARKER_PREVALENCE_ASSOCIATION_META")
            editor.set_rows(
                [
                    {
                        "row_id": "HER2_ESCC_PREVALENCE_001",
                        "row_subtype": "BIOMARKER_PREVALENCE",
                        "biomarker_name": "HER2",
                        "effect_measure": "prevalence",
                        "positive_events": "12",
                        "total_n": "80",
                    }
                ]
            )

            saved_path = window.save_current_profile_editor_rows()

            self.assertIsNotNone(saved_path)
            self.assertTrue(saved_path.exists())
            self.assertFalse(editor.is_dirty())
            editor.set_rows([])
            rows = window.load_profile_editor_rows("BIOMARKER_PREVALENCE_ASSOCIATION_META")
            self.assertEqual(rows[0]["row_id"], "HER2_ESCC_PREVALENCE_001")
            self.assertEqual(editor.cell_text(0, 0), "HER2_ESCC_PREVALENCE_001")
            self.assertFalse(editor.is_dirty())
            self.assertIn("profile_rows", str(saved_path.relative_to(state.project_dir)))

    def test_main_window_profile_row_buttons_save_and_load_project_rows(self) -> None:
        get_qapplication()
        from app.main_window import MainWindow

        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            data_dirs = DataDirectories(
                root_dir=root_dir,
                config_dir=root_dir / "config",
                logs_dir=root_dir / "logs",
                state_dir=root_dir / "state",
                cache_dir=root_dir / "cache",
            )
            data_dirs.ensure_exists()
            window = MainWindow(
                config=AppConfig(app_name="Model9", app_slug="model9", organization_name="model9"),
                data_dirs=data_dirs,
            )
            window.create_project_workspace(
                project_type="meta_analysis",
                name="Button Row Demo",
                project_id="button-row-demo",
            )
            editor = window._meta_analysis_workspace_widget.row_editor()
            editor.set_profile_type("TREATMENT_EFFECT_META")
            editor.set_rows(
                [
                    {
                        "row_id": "te-1",
                        "outcome_name": "Mortality",
                        "effect_measure": "OR",
                    }
                ]
            )

            self.assertTrue(editor.save_rows_button_enabled())
            self.assertTrue(editor.load_rows_button_enabled())
            editor.trigger_save_rows()

            self.assertIn("Rows saved", editor.action_status_text())
            editor.set_rows([])
            editor.trigger_load_rows()
            self.assertEqual(editor.cell_text(0, 0), "te-1")
            self.assertIn("Loaded 1 row", editor.action_status_text())
            self.assertIn("Save rows only saves CSV", editor.note_text())
            self.assertIn("does not run meta-analysis", editor.note_text())

    def test_main_window_blocks_invalid_profile_editor_save(self) -> None:
        get_qapplication()
        from app.main_window import MainWindow

        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            data_dirs = DataDirectories(
                root_dir=root_dir,
                config_dir=root_dir / "config",
                logs_dir=root_dir / "logs",
                state_dir=root_dir / "state",
                cache_dir=root_dir / "cache",
            )
            data_dirs.ensure_exists()
            window = MainWindow(
                config=AppConfig(app_name="Model9", app_slug="model9", organization_name="model9"),
                data_dirs=data_dirs,
            )
            window.create_project_workspace(
                project_type="meta_analysis",
                name="Invalid Row Demo",
                project_id="invalid-row-demo",
            )
            editor = window._meta_analysis_workspace_widget.row_editor()
            editor.set_profile_type("BIOMARKER_PREVALENCE_ASSOCIATION_META")
            editor.set_rows(
                [
                    {
                        "row_id": "bio-1",
                        "row_subtype": "BIOMARKER_PREVALENCE",
                        "biomarker_name": "HER2",
                        "effect_measure": "prevalence",
                    }
                ]
            )

            with self.assertRaises(ValueError):
                window.save_current_profile_editor_rows()

    def test_main_window_load_requires_discard_confirmation_when_dirty(self) -> None:
        get_qapplication()
        from app.main_window import MainWindow

        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            data_dirs = DataDirectories(
                root_dir=root_dir,
                config_dir=root_dir / "config",
                logs_dir=root_dir / "logs",
                state_dir=root_dir / "state",
                cache_dir=root_dir / "cache",
            )
            data_dirs.ensure_exists()
            window = MainWindow(
                config=AppConfig(app_name="Model9", app_slug="model9", organization_name="model9"),
                data_dirs=data_dirs,
            )
            window.create_project_workspace(
                project_type="meta_analysis",
                name="Dirty Load Demo",
                project_id="dirty-load-demo",
            )
            editor = window._meta_analysis_workspace_widget.row_editor()
            editor.set_profile_type("TREATMENT_EFFECT_META")
            editor.set_rows(
                [
                    {
                        "row_id": "te-1",
                        "outcome_name": "Mortality",
                        "effect_measure": "OR",
                    }
                ]
            )
            editor._table.item(0, 1).setText("binary")

            with self.assertRaises(ValueError):
                window.load_profile_editor_rows("TREATMENT_EFFECT_META")

            rows = window.load_profile_editor_rows(
                "TREATMENT_EFFECT_META",
                discard_unsaved_changes=True,
            )
            self.assertEqual(rows, [])
            self.assertFalse(editor.is_dirty())
