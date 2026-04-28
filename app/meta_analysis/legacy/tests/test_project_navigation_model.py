from __future__ import annotations

import unittest

from app.project_navigation_model import ProjectNavigationModel


class ProjectNavigationModelTests(unittest.TestCase):
    def test_bioinformatics_navigation_contains_required_items(self) -> None:
        model = ProjectNavigationModel("bioinformatics")

        titles = model.titles()

        for title in [
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
        ]:
            self.assertIn(title, titles)

    def test_meta_analysis_navigation_contains_required_items(self) -> None:
        model = ProjectNavigationModel("meta_analysis")

        titles = model.titles()

        for title in [
            "项目总览",
            "PICO / 检索",
            "文献导入",
            "文献筛选",
            "数据提取",
            "Profile Readiness",
            "统计分析",
            "报告导出",
            "任务中心",
        ]:
            self.assertIn(title, titles)

    def test_select_updates_current_item(self) -> None:
        model = ProjectNavigationModel("bioinformatics")

        selected = model.select("deg")

        self.assertEqual(selected.title, "差异分析")
        self.assertEqual(model.current_item.title, "差异分析")
