from __future__ import annotations

from PIL import Image

from app.labtools.image_analysis.fluorescence import (
    FLUORESCENCE_FORMULA,
    FluorescenceAnalysisParameters,
    FluorescenceROI,
    analyze_fluorescence_roi,
    fluorescence_markdown_report_fragment,
    fluorescence_metrics_table_text,
    fluorescence_parameter_summary,
)


def test_fluorescence_markdown_report_fragment_contains_review_sections(tmp_path) -> None:
    image_path = tmp_path / "report.png"
    image = Image.new("L", (4, 2))
    image.putdata([10, 10, 30, 30, 10, 10, 30, 30])
    image.save(image_path)
    result = analyze_fluorescence_roi(
        FluorescenceAnalysisParameters(
            image_path=str(image_path),
            signal_roi=FluorescenceROI("signal", 0, 0, 2, 2, "signal"),
            background_roi=FluorescenceROI("background", 2, 0, 2, 2, "background"),
        ),
        task_id="task-report",
    )

    fragment = fluorescence_markdown_report_fragment(result)
    table = fluorescence_metrics_table_text(result)
    parameters = fluorescence_parameter_summary(result)

    assert "## 荧光强度 ROI 分析片段" in fragment
    assert "### 图片摘要" in fragment
    assert "report.png" in fragment
    assert "### ROI 参数" in fragment
    assert "signal ROI：x=0, y=0, width=2, height=2" in fragment
    assert FLUORESCENCE_FORMULA in fragment
    assert "corrected_total_fluorescence" in fragment
    assert "### Warnings" in fragment
    assert "CTF 为负值" in fragment
    assert "### 人工复核提示" in fragment
    assert "请人工复核 ROI" in fragment
    assert "metric | value | unit | note" in table
    assert "图片尺寸：4 x 2 px" in parameters
