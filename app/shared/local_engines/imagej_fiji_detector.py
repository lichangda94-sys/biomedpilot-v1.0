from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from app.shared.local_engines.engine_status import (
    ENGINE_STATUS_AVAILABLE,
    ENGINE_STATUS_FAILED,
    ENGINE_STATUS_NOT_CONFIGURED,
    EngineStatus,
    UNKNOWN_VERSION,
    utc_now,
)
from app.shared.local_engines.install_guides import imagej_fiji_install_guide_text


IMAGEJ_FIJI_ENGINE_ID = "imagej_fiji"
IMAGEJ_FIJI_ENGINE_NAME = "ImageJ/Fiji 图像分析引擎"
IMAGEJ_FIJI_ENGINE_TYPE = "local_image_analysis_backend"
IMAGEJ_FIJI_RECOMMENDED_VERSION = "Fiji Stable / ImageJ 1.x or 2.x"
DEFAULT_IMAGEJ_FIJI_TIMEOUT_SECONDS = 20

Runner = Callable[..., subprocess.CompletedProcess[str]]


def default_imagej_fiji_status(status: str = ENGINE_STATUS_NOT_CONFIGURED, *, configured_path: str = "", last_error: str = "") -> EngineStatus:
    return EngineStatus(
        engine_id=IMAGEJ_FIJI_ENGINE_ID,
        engine_name=IMAGEJ_FIJI_ENGINE_NAME,
        engine_type=IMAGEJ_FIJI_ENGINE_TYPE,
        configured_path_or_endpoint=configured_path,
        recommended_version=IMAGEJ_FIJI_RECOMMENDED_VERSION,
        status=status,
        last_error=last_error,
        install_guide_url_or_text=imagej_fiji_install_guide_text(),
    )


def detect_common_imagej_fiji_paths(home: str | Path | None = None) -> tuple[str, ...]:
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


def resolve_imagej_fiji_executable(configured_path: str | Path) -> Path:
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
        raise ValueError("Fiji/ImageJ app 内未找到可执行文件")
    if _is_executable_file(path):
        return path
    raise ValueError("Fiji/ImageJ 路径无效或不可执行")


def detect_imagej_fiji_status(
    *,
    configured_path: str | Path | None = None,
    runner: Runner = subprocess.run,
    timeout_seconds: int = DEFAULT_IMAGEJ_FIJI_TIMEOUT_SECONDS,
) -> EngineStatus:
    candidate_path = str(configured_path or "").strip()
    if not candidate_path:
        detected = detect_common_imagej_fiji_paths()
        if not detected:
            return default_imagej_fiji_status(
                ENGINE_STATUS_NOT_CONFIGURED,
                last_error="未找到 Fiji/ImageJ，请在需要图像分析 workflow 时自动检测或选择本机路径。",
            )
        candidate_path = detected[0]
    try:
        executable = resolve_imagej_fiji_executable(candidate_path)
    except ValueError as exc:
        return _failed_status(candidate_path, str(exc))
    return run_imagej_fiji_smoke_test(
        executable,
        configured_path=candidate_path,
        runner=runner,
        timeout_seconds=timeout_seconds,
    )


def run_imagej_fiji_smoke_test(
    executable: str | Path,
    *,
    configured_path: str | Path = "",
    runner: Runner = subprocess.run,
    timeout_seconds: int = DEFAULT_IMAGEJ_FIJI_TIMEOUT_SECONDS,
) -> EngineStatus:
    executable_path = Path(executable)
    version = detect_imagej_fiji_version(executable_path, runner=runner, timeout_seconds=timeout_seconds)
    with tempfile.TemporaryDirectory(prefix="biomedpilot_imagej_fiji_") as temp_dir:
        temp_path = Path(temp_dir)
        macro_path = temp_path / "biomedpilot_imagej_fiji_smoke.ijm"
        output_path = temp_path / "smoke_result.txt"
        macro_path.write_text(_smoke_macro_text(), encoding="utf-8")
        command = (
            str(executable_path),
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
            return _failed_status(
                str(configured_path or executable_path),
                "ImageJ/Fiji 验证超时，请检查本机宏执行环境。",
                detected_version=version,
            )
        except OSError as exc:
            return _failed_status(
                str(configured_path or executable_path),
                f"ImageJ/Fiji 验证无法启动：{exc}",
                detected_version=version,
            )
        if completed.returncode != 0:
            return _failed_status(
                str(configured_path or executable_path),
                _summarize_process_error(completed),
                detected_version=version,
            )
        try:
            result_text = output_path.read_text(encoding="utf-8").strip()
        except OSError:
            return _failed_status(
                str(configured_path or executable_path),
                "ImageJ/Fiji 验证失败：未生成 smoke test 输出文件。",
                detected_version=version,
            )
        if "status=ok" not in result_text:
            return _failed_status(
                str(configured_path or executable_path),
                "ImageJ/Fiji 验证失败：输出文件未包含 status=ok。",
                detected_version=version,
                smoke_test_result=result_text[:500],
            )
    return EngineStatus(
        engine_id=IMAGEJ_FIJI_ENGINE_ID,
        engine_name=IMAGEJ_FIJI_ENGINE_NAME,
        engine_type=IMAGEJ_FIJI_ENGINE_TYPE,
        configured_path_or_endpoint=str(configured_path or executable_path),
        detected_version=version,
        recommended_version=IMAGEJ_FIJI_RECOMMENDED_VERSION,
        status=ENGINE_STATUS_AVAILABLE,
        last_check_at=utc_now(),
        last_error="",
        smoke_test_result="status=ok",
        install_guide_url_or_text=imagej_fiji_install_guide_text(),
    )


def detect_imagej_fiji_version(
    executable: str | Path,
    *,
    runner: Runner = subprocess.run,
    timeout_seconds: int = DEFAULT_IMAGEJ_FIJI_TIMEOUT_SECONDS,
) -> str:
    try:
        completed = runner([str(executable), "--version"], capture_output=True, text=True, timeout=timeout_seconds)
    except (subprocess.TimeoutExpired, OSError):
        return UNKNOWN_VERSION
    return parse_imagej_fiji_version_output("\n".join(part for part in (completed.stdout, completed.stderr) if part))


def parse_imagej_fiji_version_output(text: str) -> str:
    if not text.strip():
        return UNKNOWN_VERSION
    for pattern in (
        r"(?:Fiji|ImageJ)\s+([0-9][^\s,;]*)",
        r"version[:=]\s*([0-9][^\s,;]*)",
    ):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return UNKNOWN_VERSION


def _failed_status(
    configured_path: str,
    error_message: str,
    *,
    detected_version: str = UNKNOWN_VERSION,
    smoke_test_result: str = "",
) -> EngineStatus:
    return EngineStatus(
        engine_id=IMAGEJ_FIJI_ENGINE_ID,
        engine_name=IMAGEJ_FIJI_ENGINE_NAME,
        engine_type=IMAGEJ_FIJI_ENGINE_TYPE,
        configured_path_or_endpoint=configured_path,
        detected_version=detected_version,
        recommended_version=IMAGEJ_FIJI_RECOMMENDED_VERSION,
        status=ENGINE_STATUS_FAILED,
        last_check_at=utc_now(),
        last_error=error_message,
        smoke_test_result=smoke_test_result,
        install_guide_url_or_text=imagej_fiji_install_guide_text(),
    )


def _is_executable_file(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def _smoke_macro_text() -> str:
    return "\n".join(
        (
            "output = getArgument();",
            'newImage("BioMedPilot ImageJ/Fiji smoke test", "8-bit black", 16, 16, 1);',
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
