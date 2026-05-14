from __future__ import annotations

from pathlib import Path


AUDIT_DOC = Path(__file__).resolve().parents[2] / "docs" / "labtools_tool_logic_audit.md"


def test_labtools_tool_logic_audit_document_exists_and_covers_core_tools() -> None:
    assert AUDIT_DOC.exists()
    text = AUDIT_DOC.read_text(encoding="utf-8")

    assert "实验计算器" in text
    assert "图像辅助分析" in text or "image_assistance" in text
    assert "Recipe draft" in text or "recipe_draft" in text
    assert "Experiment record draft" in text or "experiment_record_draft" in text


def test_labtools_tool_logic_audit_has_required_decision_fields() -> None:
    text = AUDIT_DOC.read_text(encoding="utf-8")

    assert "user_logic_confirmed" in text
    assert "needs_user_discussion" in text
    assert "needs_code整改" in text
    assert "recommended_next_action" in text or "Recommended next action" in text


def test_labtools_tool_logic_audit_blocks_high_risk_future_tools_until_discussion() -> None:
    text = AUDIT_DOC.read_text(encoding="utf-8")

    required_terms = (
        "Absorbance / OD calculation",
        "Protein concentration",
        "Wound healing full workflow",
        "Transwell assay",
        "WB / gel grayscale",
        "Cell counting",
    )
    for term in required_terms:
        assert term in text

    assert "Create Tool Logic Card before development" in text


def test_labtools_tool_logic_audit_avoids_misleading_final_result_language() -> None:
    text = AUDIT_DOC.read_text(encoding="utf-8")
    forbidden_terms = (
        "production-grade",
        "clinical diagnosis",
        "正式结论",
        "无需人工复核",
    )
    for term in forbidden_terms:
        assert term not in text
