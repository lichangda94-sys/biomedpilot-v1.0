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
    from PySide6.QtWidgets import QPushButton

    assert template_widget.objectName() == "labToolsTemplateWorkspace"
    assert template_widget.template_count() == 5
    buttons = [button.text() for button in template_widget.findChildren(QPushButton)]
    button_map = {button.text(): button for button in template_widget.findChildren(QPushButton)}

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
    assert "保存记录草稿 JSON" in buttons
    assert "载入记录草稿 JSON" in buttons
    assert button_map["保存记录草稿 JSON"].isEnabled() is True
    assert button_map["载入记录草稿 JSON"].isEnabled() is True


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


def test_template_widget_save_requires_created_draft(template_widget, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(template_widget, "_select_draft_save_path", lambda: str(tmp_path / "drafts.json"))

    template_widget._handle_save_drafts()

    text = template_widget._draft_preview.toPlainText()
    assert "尚未生成实验记录草稿" in text
    assert not (tmp_path / "drafts.json").exists()


def test_template_widget_cancel_save_does_not_write(template_widget, tmp_path, monkeypatch) -> None:
    _create_valid_ui_draft(template_widget)
    monkeypatch.setattr(template_widget, "_select_draft_save_path", lambda: "")

    template_widget._handle_save_drafts()

    text = template_widget._draft_preview.toPlainText()
    assert "已取消保存" in text
    assert "已保存" not in text
    assert not list(tmp_path.iterdir())


def test_template_widget_save_and_load_success(template_widget, tmp_path, monkeypatch) -> None:
    _create_valid_ui_draft(template_widget)
    save_path = tmp_path / "ui record drafts.json"
    monkeypatch.setattr(template_widget, "_select_draft_save_path", lambda: str(save_path))

    template_widget._handle_save_drafts()

    saved_files = list(tmp_path.iterdir())
    assert len(saved_files) == 1
    assert saved_files[0].name == "ui_record_drafts.json"
    save_text = template_widget._draft_preview.toPlainText()
    assert "实验记录草稿 JSON 已保存" in save_text
    assert "schema" in save_text
    assert "人工核对" in save_text
    assert "完整 ELN" in save_text

    from app.labtools.ui.template_widgets import LabToolsTemplateWidget

    second_widget = LabToolsTemplateWidget()
    monkeypatch.setattr(second_widget, "_select_draft_load_path", lambda: str(saved_files[0]))
    second_widget._handle_load_drafts()

    load_text = second_widget._draft_preview.toPlainText()
    assert "实验记录草稿 JSON 已载入" in load_text
    assert "载入草稿数：1" in load_text
    assert "LabTools 实验记录结构化草稿" in load_text
    assert len(second_widget.record_drafts()) == 1


def test_template_widget_save_failure_is_user_visible(template_widget, tmp_path, monkeypatch) -> None:
    _create_valid_ui_draft(template_widget)
    monkeypatch.setattr(template_widget, "_select_draft_save_path", lambda: str(tmp_path / "missing" / "drafts.json"))

    template_widget._handle_save_drafts()

    text = template_widget._draft_preview.toPlainText()
    assert "保存需要调整" in text
    assert "保存路径所在文件夹不存在" in text
    assert "实验记录草稿 JSON 已保存" not in text


def test_template_widget_load_failure_is_user_visible(template_widget, tmp_path, monkeypatch) -> None:
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{bad", encoding="utf-8")
    monkeypatch.setattr(template_widget, "_select_draft_load_path", lambda: str(bad_path))

    template_widget._handle_load_drafts()

    text = template_widget._draft_preview.toPlainText()
    assert "载入需要调整" in text
    assert "有效 JSON" in text
    assert template_widget.record_drafts() == ()


def test_template_widget_cancel_load_keeps_existing_drafts(template_widget, monkeypatch) -> None:
    _create_valid_ui_draft(template_widget)
    monkeypatch.setattr(template_widget, "_select_draft_load_path", lambda: "")

    template_widget._handle_load_drafts()

    text = template_widget._draft_preview.toPlainText()
    assert "已取消载入" in text
    assert len(template_widget.record_drafts()) == 1


def _create_valid_ui_draft(template_widget) -> None:
    template_widget._purpose.setText("记录 qPCR 实验计划")
    template_widget._sample_groups.setText("control n=3\ntreated n=3")
    template_widget._reagents.setText("master mix\nprimer")
    template_widget._key_parameters.setText("20 uL\n3 repeats")
    template_widget._output_files.setText("raw_ct.csv\nplate_layout.csv")
    template_widget._notes.setText("人工复核 primer")
    template_widget._handle_create_draft()
