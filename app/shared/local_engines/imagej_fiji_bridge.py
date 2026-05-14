from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import subprocess

from app.shared.local_engines.engine_config import LocalEngineConfig, LocalEngineConfigStore
from app.shared.local_engines.engine_status import ENGINE_STATUS_CONFIGURED_UNVERIFIED, EngineStatus
from app.shared.local_engines.imagej_fiji_detector import IMAGEJ_FIJI_ENGINE_ID, default_imagej_fiji_status, detect_imagej_fiji_status


class ImageJFijiBridge:
    def __init__(self, store: LocalEngineConfigStore | None = None) -> None:
        self._store = store or LocalEngineConfigStore(IMAGEJ_FIJI_ENGINE_ID)

    def load_config(self) -> LocalEngineConfig:
        return self._store.load()

    def configure_path(self, path: str | Path) -> LocalEngineConfig:
        configured_path = str(path).strip()
        if not configured_path:
            config = LocalEngineConfig(engine_id=IMAGEJ_FIJI_ENGINE_ID)
        else:
            status = replace(
                default_imagej_fiji_status(ENGINE_STATUS_CONFIGURED_UNVERIFIED, configured_path=configured_path),
                last_error="已配置路径，尚未验证。",
            )
            config = LocalEngineConfig(
                engine_id=IMAGEJ_FIJI_ENGINE_ID,
                configured_path_or_endpoint=configured_path,
                last_status=status,
            )
        self._store.save(config)
        return config

    def check_status(self, *, persist: bool = True, runner=subprocess.run) -> EngineStatus:
        config = self._store.load()
        status = detect_imagej_fiji_status(configured_path=config.configured_path_or_endpoint, runner=runner)
        if persist:
            self._store.save(
                LocalEngineConfig(
                    engine_id=IMAGEJ_FIJI_ENGINE_ID,
                    configured_path_or_endpoint=status.configured_path_or_endpoint,
                    last_status=status,
                )
            )
        return status

    def clear(self) -> LocalEngineConfig:
        return self._store.clear()
