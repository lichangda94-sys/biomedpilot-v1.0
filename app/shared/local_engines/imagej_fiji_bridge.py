from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import subprocess

from app.shared.local_engines.engine_config import LocalEngineConfig, LocalEngineConfigStore
from app.shared.local_engines.engine_status import ENGINE_STATUS_AVAILABLE, ENGINE_STATUS_CONFIGURED_UNVERIFIED, EngineStatus
from app.shared.local_engines.imagej_fiji_detector import (
    DEFAULT_IMAGEJ_FIJI_TIMEOUT_SECONDS,
    IMAGEJ_FIJI_ENGINE_ID,
    default_imagej_fiji_status,
    detect_imagej_fiji_status,
    infer_imagej_fiji_bundled_java_home,
    resolve_imagej_fiji_executable,
)
from app.shared.local_engines.imagej_fiji_installer import ImageJFijiRuntimeInstallResult, prepare_imagej_fiji_runtime, run_imagej_fiji_macro
from app.shared.local_engines.imagej_fiji_runtime import (
    default_imagej_fiji_runtime_root,
    imagej_fiji_runtime_manifest_path,
    load_imagej_fiji_runtime_manifest,
)


@dataclass(frozen=True)
class ImageJFijiMacroExecutionResult:
    macro_path: str
    argument: str
    configured_path_or_endpoint: str
    executable_path: str
    java_home: str
    returncode: int
    stdout: str
    stderr: str
    status: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0

    def to_dict(self) -> dict[str, str | int | bool]:
        return {
            "macro_path": self.macro_path,
            "argument": self.argument,
            "configured_path_or_endpoint": self.configured_path_or_endpoint,
            "executable_path": self.executable_path,
            "java_home": self.java_home,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "status": self.status,
            "succeeded": self.succeeded,
        }


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

    def configure_runtime_root(self, runtime_root: str | Path | None = None) -> LocalEngineConfig:
        return self.configure_path(runtime_root or default_imagej_fiji_runtime_root())

    def prepare_runtime(self, *, runtime_root: str | Path | None = None, allow_network_download: bool = False, **kwargs) -> ImageJFijiRuntimeInstallResult:
        result = prepare_imagej_fiji_runtime(
            runtime_root=runtime_root or default_imagej_fiji_runtime_root(),
            allow_network_download=allow_network_download,
            **kwargs,
        )
        self._store.save(
            LocalEngineConfig(
                engine_id=IMAGEJ_FIJI_ENGINE_ID,
                configured_path_or_endpoint=result.runtime_root,
                last_status=default_imagej_fiji_status(ENGINE_STATUS_CONFIGURED_UNVERIFIED, configured_path=result.runtime_root),
            )
        )
        if kwargs.get("run_smoke_test", True):
            self.check_status(persist=True, runner=kwargs.get("runner", subprocess.run))
        return result

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

    def run_macro(
        self,
        *,
        macro_path: str | Path,
        argument: str | Path = "",
        headless: bool = True,
        runner=subprocess.run,
        timeout_seconds: int = DEFAULT_IMAGEJ_FIJI_TIMEOUT_SECONDS,
    ) -> ImageJFijiMacroExecutionResult:
        status = self.check_status(persist=True, runner=runner)
        if status.status != ENGINE_STATUS_AVAILABLE:
            raise RuntimeError(f"imagej_fiji_engine_not_available: {status.last_error or status.status}")
        executable_path, java_home, configured = self._resolve_callable_runtime(status.configured_path_or_endpoint)
        completed = run_imagej_fiji_macro(
            executable_path,
            macro_path=macro_path,
            argument=argument,
            headless=headless,
            java_home=java_home,
            runner=runner,
            timeout_seconds=timeout_seconds,
        )
        return ImageJFijiMacroExecutionResult(
            macro_path=str(macro_path),
            argument=str(argument),
            configured_path_or_endpoint=configured,
            executable_path=str(executable_path),
            java_home=str(java_home),
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            status="completed" if completed.returncode == 0 else "failed",
        )

    def _resolve_callable_runtime(self, configured_path: str | Path) -> tuple[Path, str, str]:
        configured = str(configured_path).strip()
        if not configured:
            raise RuntimeError("imagej_fiji_engine_not_configured")
        root = Path(configured).expanduser()
        if imagej_fiji_runtime_manifest_path(root).exists():
            manifest = load_imagej_fiji_runtime_manifest(root)
            return Path(manifest.executable_path).expanduser(), manifest.java_home or infer_imagej_fiji_bundled_java_home(manifest.executable_path), str(root)
        executable = resolve_imagej_fiji_executable(root)
        return executable, infer_imagej_fiji_bundled_java_home(executable), configured

    def clear(self) -> LocalEngineConfig:
        return self._store.clear()
