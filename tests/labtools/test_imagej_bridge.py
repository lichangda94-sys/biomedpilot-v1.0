from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from app.labtools.imagej_bridge import (
    IMAGEJ_STATUS_AVAILABLE,
    IMAGEJ_STATUS_CONFIGURED_UNVERIFIED,
    IMAGEJ_STATUS_FAILED,
    IMAGEJ_STATUS_NOT_CONFIGURED,
    UNKNOWN_VERSION,
    ImageJBridgeConfigStore,
    configure_imagej_path,
    default_imagej_bridge_config,
    parse_imagej_version_output,
    run_imagej_smoke_test,
)


def _fake_imagej(tmp_path: Path, body: str) -> Path:
    executable = tmp_path / "fake_imagej.py"
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


def test_imagej_bridge_default_state_is_not_configured() -> None:
    config = default_imagej_bridge_config()

    assert config.status == IMAGEJ_STATUS_NOT_CONFIGURED
    assert config.configured_path == ""


def test_configuring_path_marks_bridge_configured_unverified(tmp_path) -> None:
    config = configure_imagej_path(tmp_path / "Fiji.app")

    assert config.status == IMAGEJ_STATUS_CONFIGURED_UNVERIFIED
    assert config.configured_path.endswith("Fiji.app")


def test_invalid_path_validation_fails_with_readable_error(tmp_path) -> None:
    config = configure_imagej_path(tmp_path / "missing")

    result = run_imagej_smoke_test(config)

    assert result.status == IMAGEJ_STATUS_FAILED
    assert "路径无效" in result.error_message
    assert "Traceback" not in result.error_message


def test_fake_executable_smoke_test_status_ok_marks_available(tmp_path) -> None:
    executable = _fake_imagej(
        tmp_path,
        """
if "--version" in sys.argv:
    print("ImageJ 1.54f")
    print("Java 1.8.0_322")
    raise SystemExit(0)
pathlib.Path(sys.argv[-1]).write_text("status=ok\\n", encoding="utf-8")
raise SystemExit(0)
""",
    )

    result = run_imagej_smoke_test(configure_imagej_path(executable))

    assert result.status == IMAGEJ_STATUS_AVAILABLE
    assert result.available
    assert result.smoke_test_result == "status=ok"
    assert result.detected_version == "1.54f"
    assert result.java_version == "1.8.0_322"
    assert result.config.status == IMAGEJ_STATUS_AVAILABLE


def test_smoke_test_output_missing_marks_failed(tmp_path) -> None:
    executable = _fake_imagej(
        tmp_path,
        """
if "--version" in sys.argv:
    raise SystemExit(0)
raise SystemExit(0)
""",
    )

    result = run_imagej_smoke_test(configure_imagej_path(executable))

    assert result.status == IMAGEJ_STATUS_FAILED
    assert "未生成 smoke test 输出文件" in result.error_message


def test_smoke_test_timeout_marks_failed_without_traceback(tmp_path) -> None:
    executable = _fake_imagej(tmp_path, "raise SystemExit(0)")

    def timeout_runner(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs.get("timeout", 1))

    result = run_imagej_smoke_test(configure_imagej_path(executable), runner=timeout_runner)

    assert result.status == IMAGEJ_STATUS_FAILED
    assert "验证超时" in result.error_message
    assert "Traceback" not in result.error_message


def test_version_parse_failure_does_not_block_successful_smoke_test(tmp_path) -> None:
    executable = _fake_imagej(
        tmp_path,
        """
if "--version" in sys.argv:
    print("custom local build")
    raise SystemExit(0)
pathlib.Path(sys.argv[-1]).write_text("status=ok\\n", encoding="utf-8")
raise SystemExit(0)
""",
    )

    result = run_imagej_smoke_test(configure_imagej_path(executable))

    assert result.status == IMAGEJ_STATUS_AVAILABLE
    assert result.detected_version == UNKNOWN_VERSION
    assert result.java_version == UNKNOWN_VERSION


def test_version_parser_accepts_imagej_and_java_text() -> None:
    imagej_version, java_version = parse_imagej_version_output("Fiji 2.14.0\nOpenJDK Runtime 1.8.0_322")

    assert imagej_version == "2.14.0"
    assert java_version == "1.8.0_322"


def test_config_json_round_trip_and_clear(tmp_path) -> None:
    store = ImageJBridgeConfigStore(tmp_path / "imagej_bridge_config.json")
    config = configure_imagej_path(sys.executable)

    store.save(config)
    loaded = store.load()

    assert loaded.to_dict() == config.to_dict()

    cleared = store.clear()

    assert cleared.status == IMAGEJ_STATUS_NOT_CONFIGURED
    assert not store.resolved_path().exists()
