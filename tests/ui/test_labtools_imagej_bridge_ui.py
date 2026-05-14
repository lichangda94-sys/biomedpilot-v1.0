from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture()
def qapp():
    try:
        from PySide6.QtWidgets import QApplication
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PySide6 UI runtime unavailable: {exc}")

    return QApplication.instance() or QApplication([])


def _visible_text(widget) -> str:
    from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit

    parts: list[str] = []
    for label in widget.findChildren(QLabel):
        parts.append(label.text())
    for button in widget.findChildren(QPushButton):
        parts.append(button.text())
    for panel in widget.findChildren(QTextEdit):
        parts.append(panel.toPlainText())
    return "\n".join(part for part in parts if part)


def _fake_imagej(tmp_path: Path, *, succeeds: bool) -> Path:
    executable = tmp_path / ("fake_imagej_ok.py" if succeeds else "fake_imagej_fail.py")
    if succeeds:
        body = """
if "--version" in sys.argv:
    print("ImageJ 1.54f")
    print("Java 1.8.0_322")
    raise SystemExit(0)
pathlib.Path(sys.argv[-1]).write_text("status=ok\\n", encoding="utf-8")
raise SystemExit(0)
"""
    else:
        body = """
if "--version" in sys.argv:
    raise SystemExit(0)
print("macro failed", file=sys.stderr)
raise SystemExit(2)
"""
    executable.write_text(
        "\n".join(
            (
                "#!/usr/bin/env python3",
                "from __future__ import annotations",
                "import pathlib",
                "import sys",
                body,
                "",
            )
        ),
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


def test_labtools_workspace_can_enter_imagej_fiji_bridge_settings(qapp) -> None:
    from PySide6.QtWidgets import QPushButton

    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    button = widget.findChild(QPushButton, "labToolsImageJBridgeSettingsButton")

    assert button is not None
    button.click()

    assert widget.current_page_key() == "imagej_fiji_bridge"
    text = _visible_text(widget)
    assert "ImageJ/Fiji 后端设置" in text
    assert "第一版推荐 Fiji Stable / Java 8" in text
    assert "未配置 / 已配置，尚未验证 / 可用 / 验证失败" in text


def test_imagej_bridge_settings_page_exposes_required_actions(qapp, tmp_path) -> None:
    from PySide6.QtWidgets import QPushButton

    from app.labtools.imagej_bridge import ImageJBridgeConfigStore
    from app.labtools.ui.imagej_bridge_widgets import LabToolsImageJBridgeWidget

    widget = LabToolsImageJBridgeWidget(store=ImageJBridgeConfigStore(tmp_path / "config.json"))
    text = _visible_text(widget)

    assert widget.findChild(QPushButton, "imagejAutoDetectButton") is not None
    assert widget.findChild(QPushButton, "imagejSelectPathButton") is not None
    assert widget.findChild(QPushButton, "imagejRunSmokeTestButton") is not None
    assert widget.findChild(QPushButton, "imagejOfficialDownloadButton") is not None
    assert widget.findChild(QPushButton, "imagejClearConfigButton") is not None
    assert "BioMedPilot 不内置 Fiji/ImageJ" in text
    assert "结果仍需人工复核" in text
    assert "WB 灰度已完成" not in text
    assert "自动 ROI 已完成" not in text
    assert "细胞计数已完成" not in text


def test_imagej_bridge_ui_smoke_success_shows_available(qapp, tmp_path) -> None:
    from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit

    from app.labtools.imagej_bridge import ImageJBridgeConfigStore
    from app.labtools.ui.imagej_bridge_widgets import LabToolsImageJBridgeWidget

    widget = LabToolsImageJBridgeWidget(store=ImageJBridgeConfigStore(tmp_path / "config.json"))
    widget.set_configured_path_for_testing(str(_fake_imagej(tmp_path, succeeds=True)))
    widget.findChild(QPushButton, "imagejRunSmokeTestButton").click()

    assert widget.findChild(QLabel, "imagejBridgeStatusLabel").text() == "可用"
    result_text = widget.findChild(QTextEdit, "imagejBridgeResultPanel").toPlainText()
    assert "smoke test 通过" in result_text
    assert "检测到版本：1.54f" in result_text


def test_imagej_bridge_ui_smoke_failure_shows_failed(qapp, tmp_path) -> None:
    from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit

    from app.labtools.imagej_bridge import ImageJBridgeConfigStore
    from app.labtools.ui.imagej_bridge_widgets import LabToolsImageJBridgeWidget

    widget = LabToolsImageJBridgeWidget(store=ImageJBridgeConfigStore(tmp_path / "config.json"))
    widget.set_configured_path_for_testing(str(_fake_imagej(tmp_path, succeeds=False)))
    widget.findChild(QPushButton, "imagejRunSmokeTestButton").click()

    assert widget.findChild(QLabel, "imagejBridgeStatusLabel").text() == "验证失败"
    result_text = widget.findChild(QTextEdit, "imagejBridgeResultPanel").toPlainText()
    assert "验证失败" in result_text
    assert "Traceback" not in result_text
