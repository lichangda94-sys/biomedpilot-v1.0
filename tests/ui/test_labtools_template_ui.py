from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture()
def template_widget():
    try:
        from PySide6.QtWidgets import QApplication

        from app.labtools.ui.template_widgets import LabToolsTemplateWidget
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PySide6 UI runtime unavailable: {exc}")

    app = QApplication.instance() or QApplication([])
    widget = LabToolsTemplateWidget()
    assert app is not None
    return widget


def test_template_widget_lists_lightweight_templates(template_widget) -> None:
    assert template_widget.objectName() == "labToolsTemplateWorkspace"
    assert template_widget.template_count() == 5

    text = "\n".join(
        [
            template_widget._template_detail.toPlainText(),
            template_widget._draft_preview.toPlainText(),
        ]
    )
    assert "qPCR 实验计划模板" in text
    assert "本地结构化草稿" in text
    assert "不自动保存" in text
    assert "正式 ELN" in text


def test_template_widget_creates_record_draft(template_widget) -> None:
    template_widget._purpose.setText("记录 qPCR 实验计划")
    template_widget._sample_groups.setText("control n=3\ntreated n=3")
    template_widget._reagents.setText("master mix\nprimer")
    template_widget._key_parameters.setText("20 uL\n3 repeats")
    template_widget._output_files.setText("raw_ct.csv\nplate_layout.csv")
    template_widget._notes.setText("人工复核 primer")

    template_widget._handle_create_draft()

    preview = template_widget._draft_preview.toPlainText()
    assert len(template_widget.record_drafts()) == 1
    assert "LabTools 实验记录结构化草稿" in preview
    assert "draft_manual_review_required" in preview
    assert "人工复核" in preview


def test_template_widget_validation_error_is_visible(template_widget) -> None:
    template_widget._purpose.setText("")
    template_widget._sample_groups.setText("control")
    template_widget._reagents.setText("master mix")
    template_widget._key_parameters.setText("20 uL")
    template_widget._output_files.setText("raw_ct.csv")

    template_widget._handle_create_draft()

    assert "记录草稿需要调整" in template_widget._draft_preview.toPlainText()
    assert template_widget.record_drafts() == ()
