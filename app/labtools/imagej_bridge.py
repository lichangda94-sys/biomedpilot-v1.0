from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


LABTOOLS_IMAGEJ_BRIDGE_CONFIG_SCHEMA_VERSION = "labtools_imagej_bridge_config.v1"
IMAGEJ_BACKEND_TYPE = "external_fiji_imagej_macro_bridge"
IMAGEJ_RECOMMENDED_BACKEND = "Fiji Stable / Java 8"
IMAGEJ_STATUS_NOT_CONFIGURED = "not_configured"
IMAGEJ_STATUS_CONFIGURED_UNVERIFIED = "configured_unverified"
IMAGEJ_STATUS_AVAILABLE = "available"
IMAGEJ_STATUS_FAILED = "failed"
IMAGEJ_STATUS_VALUES = (
    IMAGEJ_STATUS_NOT_CONFIGURED,
    IMAGEJ_STATUS_CONFIGURED_UNVERIFIED,
    IMAGEJ_STATUS_AVAILABLE,
    IMAGEJ_STATUS_FAILED,
)
UNKNOWN_VERSION = "unknown_version"
DEFAULT_IMAGEJ_BRIDGE_TIMEOUT_SECONDS = 20


class ImageJBridgeError(ValueError):
    pass


@dataclass(frozen=True)
class ImageJBridgeConfig:
    schema_version: str = LABTOOLS_IMAGEJ_BRIDGE_CONFIG_SCHEMA_VERSION
    backend_type: str = IMAGEJ_BACKEND_TYPE
    recommended_backend: str = IMAGEJ_RECOMMENDED_BACKEND
    configured_path: str = ""
    detected_version: str = UNKNOWN_VERSION
    java_version: str = UNKNOWN_VERSION
    status: str = IMAGEJ_STATUS_NOT_CONFIGURED
    last_smoke_test_at: str = ""
    last_smoke_test_result: str = ""
    last_error: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "backend_type": self.backend_type,
            "recommended_backend": self.recommended_backend,
            "configured_path": self.configured_path,
            "detected_version": self.detected_version,
            "java_version": self.java_version,
            "status": self.status,
            "last_smoke_test_at": self.last_smoke_test_at,
            "last_smoke_test_result": self.last_smoke_test_result,
            "last_error": self.last_error,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class ImageJBridgeSmokeResult:
    status: str
    executable_path: str
    detected_version: str
    java_version: str
    command_used: tuple[str, ...]
    smoke_test_result: str
    error_message: str
    config: ImageJBridgeConfig

    @property
    def available(self) -> bool:
        return self.status == IMAGEJ_STATUS_AVAILABLE


@dataclass
class ImageJBridgeConfigStore:
    config_path: Path | None = None

    def resolved_path(self) -> Path:
        if self.config_path is not None:
            return self.config_path
        return Path.home() / ".biomedpilot" / "labtools" / "imagej_bridge_config.json"

    def load(self) -> ImageJBridgeConfig:
        path = self.resolved_path()
        if not path.exists():
            return default_imagej_bridge_config()
        try:
            return imagej_bridge_config_from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, ImageJBridgeError) as exc:
            raise ImageJBridgeError("ImageJ/Fiji 配置 JSON 无效，无法载入") from exc

    def save(self, config: ImageJBridgeConfig) -> Path:
        path = self.resolved_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(config.to_dict(), ensure_ascii=False, indent=2) + "\n"
        try:
            path.write_text(payload, encoding="utf-8")
        except OSError as exc:
            raise ImageJBridgeError("无法写入 ImageJ/Fiji 配置，请检查路径权限") from exc
        return path

    def clear(self) -> ImageJBridgeConfig:
        config = default_imagej_bridge_config()
        path = self.resolved_path()
        if path.exists():
            try:
                path.unlink()
            except OSError as exc:
                raise ImageJBridgeError("无法清除 ImageJ/Fiji 配置，请检查路径权限") from exc
        return config


def default_imagej_bridge_config() -> ImageJBridgeConfig:
    return ImageJBridgeConfig(updated_at=_utc_now())


def configure_imagej_path(path: str | Path) -> ImageJBridgeConfig:
    configured_path = str(path).strip()
    if not configured_path:
        return default_imagej_bridge_config()
    return ImageJBridgeConfig(
        configured_path=configured_path,
        status=IMAGEJ_STATUS_CONFIGURED_UNVERIFIED,
        updated_at=_utc_now(),
    )


def imagej_bridge_config_from_dict(payload: Any) -> ImageJBridgeConfig:
    if not isinstance(payload, dict):
        raise ImageJBridgeError("ImageJ/Fiji 配置 JSON 无效，无法载入")
    if payload.get("schema_version") != LABTOOLS_IMAGEJ_BRIDGE_CONFIG_SCHEMA_VERSION:
        raise ImageJBridgeError("ImageJ/Fiji 配置 JSON 无效，无法载入")
    status = str(payload.get("status", IMAGEJ_STATUS_NOT_CONFIGURED))
    if status not in IMAGEJ_STATUS_VALUES:
        status = IMAGEJ_STATUS_FAILED
    return ImageJBridgeConfig(
        schema_version=LABTOOLS_IMAGEJ_BRIDGE_CONFIG_SCHEMA_VERSION,
        backend_type=str(payload.get("backend_type", IMAGEJ_BACKEND_TYPE)),
        recommended_backend=str(payload.get("recommended_backend", IMAGEJ_RECOMMENDED_BACKEND)),
        configured_path=str(payload.get("configured_path", "")),
        detected_version=str(payload.get("detected_version", UNKNOWN_VERSION) or UNKNOWN_VERSION),
        java_version=str(payload.get("java_version", UNKNOWN_VERSION) or UNKNOWN_VERSION),
        status=status,
        last_smoke_test_at=str(payload.get("last_smoke_test_at", "")),
        last_smoke_test_result=str(payload.get("last_smoke_test_result", "")),
        last_error=str(payload.get("last_error", "")),
        updated_at=str(payload.get("updated_at", "")) or _utc_now(),
    )


def detect_common_imagej_paths(home: str | Path | None = None) -> tuple[str, ...]:
    home_path = Path(home).expanduser() if home is not None else Path.home()
    candidates = (
        Path("/Applications/Fiji.app"),
        Path("/Applications/ImageJ.app"),
        home_path / "Applications" / "Fiji.app",
        home_path / "Applications" / "ImageJ.app",
        home_path / "Fiji.app",
        home_path / "ImageJ.app",
        home_path / "Fiji" / "ImageJ-macosx",
        home_path / "ImageJ" / "ImageJ-macosx",
    )
    return tuple(str(path) for path in candidates if path.exists())


def resolve_imagej_executable(configured_path: str | Path) -> Path:
    path = Path(configured_path).expanduser()
    if path.is_dir() and path.suffix == ".app":
        for relative in (
            Path("Contents/MacOS/ImageJ-macosx"),
            Path("Contents/MacOS/ImageJ"),
            Path("Contents/MacOS/Fiji"),
        ):
            candidate = path / relative
            if _is_executable_file(candidate):
                return candidate
        raise ImageJBridgeError("Fiji/ImageJ app 内未找到可执行文件")
    if _is_executable_file(path):
        return path
    raise ImageJBridgeError("Fiji/ImageJ 路径无效或不可执行")


def run_imagej_smoke_test(
    config: ImageJBridgeConfig,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    timeout_seconds: int = DEFAULT_IMAGEJ_BRIDGE_TIMEOUT_SECONDS,
) -> ImageJBridgeSmokeResult:
    if not config.configured_path:
        return _failed_result(config, (), "尚未配置 Fiji/ImageJ 路径")
    try:
        executable = resolve_imagej_executable(config.configured_path)
    except ImageJBridgeError as exc:
        return _failed_result(config, (), str(exc))

    version, java_version = detect_imagej_version(executable, runner=runner, timeout_seconds=timeout_seconds)
    with tempfile.TemporaryDirectory(prefix="labtools_imagej_bridge_") as temp_dir:
        temp_path = Path(temp_dir)
        macro_path = temp_path / "labtools_imagej_smoke_test.ijm"
        output_path = temp_path / "smoke_test_result.csv"
        macro_path.write_text(_smoke_macro_text(), encoding="utf-8")
        command = (
            str(executable),
            "--headless",
            "-macro",
            str(macro_path),
            str(output_path),
        )
        try:
            completed = runner(
                list(command),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=str(temp_path),
            )
        except subprocess.TimeoutExpired:
            return _failed_result(
                config,
                command,
                "ImageJ/Fiji 验证超时，请检查宏执行环境",
                detected_version=version,
                java_version=java_version,
            )
        except OSError as exc:
            return _failed_result(
                config,
                command,
                f"ImageJ/Fiji 验证无法启动：{exc}",
                detected_version=version,
                java_version=java_version,
            )
        if completed.returncode != 0:
            error = _summarize_process_error(completed)
            return _failed_result(config, command, error, detected_version=version, java_version=java_version)
        try:
            result_text = output_path.read_text(encoding="utf-8")
        except OSError:
            return _failed_result(
                config,
                command,
                "ImageJ/Fiji 验证失败：未生成 smoke test 输出文件",
                detected_version=version,
                java_version=java_version,
            )
        if "status=ok" not in result_text:
            return _failed_result(
                config,
                command,
                "ImageJ/Fiji 验证失败：输出文件未包含 status=ok",
                detected_version=version,
                java_version=java_version,
                smoke_result=result_text.strip(),
            )
    now = _utc_now()
    updated = replace(
        config,
        configured_path=str(config.configured_path),
        detected_version=version,
        java_version=java_version,
        status=IMAGEJ_STATUS_AVAILABLE,
        last_smoke_test_at=now,
        last_smoke_test_result="status=ok",
        last_error="",
        updated_at=now,
    )
    return ImageJBridgeSmokeResult(
        status=IMAGEJ_STATUS_AVAILABLE,
        executable_path=str(executable),
        detected_version=version,
        java_version=java_version,
        command_used=command,
        smoke_test_result="status=ok",
        error_message="",
        config=updated,
    )


def detect_imagej_version(
    executable: str | Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    timeout_seconds: int = DEFAULT_IMAGEJ_BRIDGE_TIMEOUT_SECONDS,
) -> tuple[str, str]:
    command = [str(executable), "--version"]
    try:
        completed = runner(command, capture_output=True, text=True, timeout=timeout_seconds)
    except (subprocess.TimeoutExpired, OSError):
        return UNKNOWN_VERSION, UNKNOWN_VERSION
    text = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    return parse_imagej_version_output(text)


def parse_imagej_version_output(text: str) -> tuple[str, str]:
    if not text.strip():
        return UNKNOWN_VERSION, UNKNOWN_VERSION
    imagej_version = UNKNOWN_VERSION
    java_version = UNKNOWN_VERSION
    imagej_patterns = (
        r"(?:Fiji|ImageJ)\s+([0-9][^\s,;]*)",
        r"version[:=]\s*([0-9][^\s,;]*)",
    )
    java_patterns = (
        r"(?:Java|OpenJDK)[^\d]*([0-9]+(?:\.[0-9._]+)?)",
        r"java\.version[:=]\s*([0-9][^\s,;]*)",
    )
    for pattern in imagej_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            imagej_version = match.group(1)
            break
    for pattern in java_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            java_version = match.group(1)
            break
    return imagej_version, java_version


def imagej_status_label(status: str) -> str:
    return {
        IMAGEJ_STATUS_NOT_CONFIGURED: "未配置",
        IMAGEJ_STATUS_CONFIGURED_UNVERIFIED: "已配置，尚未验证",
        IMAGEJ_STATUS_AVAILABLE: "可用",
        IMAGEJ_STATUS_FAILED: "验证失败",
    }.get(status, "验证失败")


def _failed_result(
    config: ImageJBridgeConfig,
    command: tuple[str, ...],
    error_message: str,
    *,
    detected_version: str = UNKNOWN_VERSION,
    java_version: str = UNKNOWN_VERSION,
    smoke_result: str = "",
) -> ImageJBridgeSmokeResult:
    now = _utc_now()
    updated = replace(
        config,
        detected_version=detected_version,
        java_version=java_version,
        status=IMAGEJ_STATUS_FAILED,
        last_smoke_test_at=now,
        last_smoke_test_result=smoke_result,
        last_error=error_message,
        updated_at=now,
    )
    return ImageJBridgeSmokeResult(
        status=IMAGEJ_STATUS_FAILED,
        executable_path="",
        detected_version=detected_version,
        java_version=java_version,
        command_used=command,
        smoke_test_result=smoke_result,
        error_message=error_message,
        config=updated,
    )


def _is_executable_file(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def _smoke_macro_text() -> str:
    return "\n".join(
        (
            'output = getArgument();',
            'newImage("LabTools smoke test", "8-bit black", 16, 16, 1);',
            'File.saveString("status=ok\\n", output);',
            'run("Quit");',
            "",
        )
    )


def _summarize_process_error(completed: subprocess.CompletedProcess[str]) -> str:
    text = "\n".join(part.strip() for part in (completed.stderr, completed.stdout) if part and part.strip())
    if not text:
        text = f"exit code {completed.returncode}"
    return f"ImageJ/Fiji 验证失败：{text[:500]}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
