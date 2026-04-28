from __future__ import annotations

import os
from pathlib import Path
import shutil


def pytest_configure() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if os.getenv("QT_QPA_PLATFORM_PLUGIN_PATH"):
        return

    try:
        import PySide6
    except ModuleNotFoundError:
        return

    source_dir = Path(PySide6.__file__).parent / "Qt" / "plugins" / "platforms"
    target_dir = Path("/tmp/model9-qt-platforms")
    target_dir.mkdir(parents=True, exist_ok=True)
    for plugin_path in source_dir.glob("*.dylib"):
        target_path = target_dir / plugin_path.name
        shutil.copyfile(plugin_path, target_path)
        target_path.chmod(0o755)
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(target_dir)
