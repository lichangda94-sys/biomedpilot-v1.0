from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import platform


@dataclass(slots=True)
class DataDirectories:
    root_dir: Path
    config_dir: Path
    logs_dir: Path
    state_dir: Path
    cache_dir: Path

    @classmethod
    def for_app(cls, app_slug: str) -> "DataDirectories":
        base = _platform_data_root(app_slug)
        return cls(
            root_dir=base,
            config_dir=base / "config",
            logs_dir=base / "logs",
            state_dir=base / "state",
            cache_dir=base / "cache",
        )

    def ensure_exists(self) -> None:
        for directory in (
            self.root_dir,
            self.config_dir,
            self.logs_dir,
            self.state_dir,
            self.cache_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


def _platform_data_root(app_slug: str) -> Path:
    system = platform.system()

    if system == "Windows":
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / app_slug

    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / app_slug

    xdg_data_home = os.getenv("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / app_slug

    return Path.home() / ".local" / "share" / app_slug
