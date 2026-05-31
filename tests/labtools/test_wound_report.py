from __future__ import annotations

from PIL import Image

from app.labtools.image_analysis.wound_healing import (
    WOUND_FORMULA,
    WoundHealingParameters,
    WoundHealingROI,
    analyze_wound_healing_area,
    wound_markdown_report_fragment,
    wound_metrics_table_text,
    wound_parameter_summary,
)


def test_wound_markdown_report_fragment_contains_review_sections(tmp_path) -> None:
    image_path = tmp_path / "wound-report.png"
    image = Image.new("L", (10, 10))
    image.putdata([250] * 25 + [20] * 75)
    image.save(image_path)
    result = analyze_wound_healing_area(
        WoundHealingParameters(str(image_path), WoundHealingROI("analysis ROI", 0, 0, 10, 10), 200, "bright"),
        task_id="task-report",
    )

    fragment = wound_markdown_report_fragment(result)
    table = wound_metrics_table_text(result)
    parameters = wound_parameter_summary(result)

    assert "## 划痕实验面积分析片段" in fragment
    assert "### 图片摘要" in fragment
    assert "wound-report.png" in fragment
    assert "### ROI 参数" in fragment
    assert "ROI：x=0, y=0, width=10, height=10" in fragment
    assert "### 阈值和模式" in fragment
    assert "阈值：200" in fragment
    assert "划痕模式：bright" in fragment
    assert WOUND_FORMULA in fragment
    assert "scratch_area_fraction" in fragment
    assert "### Warnings" in fragment
    assert "### 人工复核提示" in fragment
    assert "基于用户 ROI 和阈值" in fragment
    assert "metric | value | unit | note" in table
    assert "图片尺寸：10 x 10 px" in parameters
