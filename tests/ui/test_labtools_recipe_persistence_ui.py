from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.labtools.recipes.recipe_models import RecipeComponent, RecipeDraft

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _draft() -> RecipeDraft:
    return RecipeDraft(
        name="UI 用户配方",
        category="用户自定义",
        description="UI persistence test",
        stock_concentration="1×",
        default_volume=100,
        default_volume_unit="mL",
        components=(RecipeComponent("NaCl", 0.8, "g", "主要盐"),),
        preparation_notes=("按 SOP 复核。",),
        safety_notes=("按 SDS 复核。",),
        edited_by_user=True,
    )


@pytest.fixture()
def recipe_widget():
    try:
        from PySide6.QtWidgets import QApplication, QPushButton

        from app.labtools.ui.recipe_widgets import LabToolsRecipeWidget
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PySide6 UI runtime unavailable: {exc}")

    app = QApplication.instance() or QApplication([])
    widget = LabToolsRecipeWidget()
    assert app is not None
    buttons = {button.text(): button for button in widget.findChildren(QPushButton)}
    assert "保存用户配方 JSON" in buttons
    assert "载入用户配方 JSON" in buttons
    assert buttons["保存用户配方 JSON"].isEnabled() is True
    assert buttons["载入用户配方 JSON"].isEnabled() is True
    return widget


def test_recipe_persistence_ui_save_requires_confirmed_recipe(recipe_widget, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(recipe_widget, "_select_user_recipe_save_path", lambda: str(tmp_path / "drafts.json"))

    recipe_widget._handle_save_user_recipes()

    text = recipe_widget._user_recipe_summary.toPlainText()
    assert "尚未确认用户配方" in text
    assert not (tmp_path / "drafts.json").exists()


def test_recipe_persistence_ui_shows_safety_category_and_manual_review_boundaries(recipe_widget) -> None:
    from PySide6.QtWidgets import QLabel, QTextEdit

    text = "\n".join(
        [label.text() for label in recipe_widget.findChildren(QLabel)]
        + [panel.toPlainText() for panel in recipe_widget.findChildren(QTextEdit)]
    )

    assert "routine_buffer_draft" in text
    assert "user_verified_only" in text
    assert "requires_lab_sop_review" in text
    assert "本地草稿" in text
    assert "人工核对" in text
    assert "浓度" in text
    assert "pH" in text
    assert "储存条件" in text
    assert "有效期" in text
    assert "危险性" in text
    assert "不构成安全操作规范" in text
    assert "不自动适配所有实验" in text
    for forbidden in ("production-grade", "临床诊断", "正式 SOP 已生成"):
        assert forbidden not in text


def test_recipe_persistence_ui_cancel_save_does_not_write(recipe_widget, tmp_path, monkeypatch) -> None:
    recipe_widget.user_recipe_store().confirm_draft(_draft())
    monkeypatch.setattr(recipe_widget, "_select_user_recipe_save_path", lambda: "")

    recipe_widget._handle_save_user_recipes()

    text = recipe_widget._user_recipe_summary.toPlainText()
    assert "已取消保存" in text
    assert "已保存" not in text
    assert not list(tmp_path.iterdir())


def test_recipe_persistence_ui_save_and_load_success(recipe_widget, tmp_path, monkeypatch) -> None:
    recipe_widget.user_recipe_store().confirm_draft(_draft())
    save_path = tmp_path / "ui drafts.json"
    monkeypatch.setattr(recipe_widget, "_select_user_recipe_save_path", lambda: str(save_path))

    recipe_widget._handle_save_user_recipes()

    saved_files = list(tmp_path.iterdir())
    assert len(saved_files) == 1
    assert saved_files[0].name == "ui_drafts.json"
    save_text = recipe_widget._user_recipe_summary.toPlainText()
    assert "用户配方 JSON 已保存" in save_text
    assert "schema" in save_text
    assert "routine_buffer_draft" in save_text
    assert "人工核对" in save_text
    assert "危险性" in save_text

    from app.labtools.ui.recipe_widgets import LabToolsRecipeWidget

    second_widget = LabToolsRecipeWidget()
    monkeypatch.setattr(second_widget, "_select_user_recipe_load_path", lambda: str(saved_files[0]))
    second_widget._handle_load_user_recipes()

    load_text = second_widget._user_recipe_summary.toPlainText()
    assert "用户配方 JSON 已载入" in load_text
    assert "载入配方数：1" in load_text
    assert "实际写入当前内存配方数：1" in load_text
    assert "recipe_id 冲突数：0" in load_text
    assert "载入版本：user-confirmed-draft" in load_text
    assert "requires_lab_sop_review" in load_text
    assert "pH" in load_text
    assert second_widget.user_recipe_store().list_recipes()[0].name == "UI 用户配方"


def test_recipe_persistence_ui_save_failure_is_user_visible(recipe_widget, tmp_path, monkeypatch) -> None:
    recipe_widget.user_recipe_store().confirm_draft(_draft())
    monkeypatch.setattr(recipe_widget, "_select_user_recipe_save_path", lambda: str(tmp_path / "missing" / "drafts.json"))

    recipe_widget._handle_save_user_recipes()

    text = recipe_widget._user_recipe_summary.toPlainText()
    assert "保存需要调整" in text
    assert "保存路径所在文件夹不存在" in text
    assert "用户配方 JSON 已保存" not in text


def test_recipe_persistence_ui_load_failure_is_user_visible(recipe_widget, tmp_path, monkeypatch) -> None:
    recipe_widget.user_recipe_store().confirm_draft(_draft())
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{bad", encoding="utf-8")
    monkeypatch.setattr(recipe_widget, "_select_user_recipe_load_path", lambda: str(bad_path))

    recipe_widget._handle_load_user_recipes()

    text = recipe_widget._user_recipe_summary.toPlainText()
    assert "载入需要调整" in text
    assert "有效 JSON" in text
    assert recipe_widget.user_recipe_store().list_recipes()[0].name == "UI 用户配方"


def test_recipe_persistence_ui_cancel_load_keeps_existing_recipes(recipe_widget, monkeypatch) -> None:
    recipe_widget.user_recipe_store().confirm_draft(_draft())
    monkeypatch.setattr(recipe_widget, "_select_user_recipe_load_path", lambda: "")

    recipe_widget._handle_load_user_recipes()

    text = recipe_widget._user_recipe_summary.toPlainText()
    assert "已取消载入" in text
    assert recipe_widget.user_recipe_store().list_recipes()[0].name == "UI 用户配方"


def test_recipe_persistence_ui_reports_import_conflict_without_overwrite(recipe_widget, tmp_path, monkeypatch) -> None:
    recipe_widget.user_recipe_store().confirm_draft(_draft())
    save_path = tmp_path / "conflict.json"
    monkeypatch.setattr(recipe_widget, "_select_user_recipe_save_path", lambda: str(save_path))
    recipe_widget._handle_save_user_recipes()

    saved_file = next(tmp_path.iterdir())
    monkeypatch.setattr(recipe_widget, "_select_user_recipe_load_path", lambda: str(saved_file))
    recipe_widget._handle_load_user_recipes()

    text = recipe_widget._user_recipe_summary.toPlainText()
    assert "recipe_id 冲突数：1" in text
    assert "未覆盖现有用户配方" in text
    assert "imported copy" in text
    assert "requires_lab_sop_review" in text
    assert len(recipe_widget.user_recipe_store().list_recipes()) == 2
