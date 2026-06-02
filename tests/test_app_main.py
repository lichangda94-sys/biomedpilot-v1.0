from __future__ import annotations

from app.main import parse_args


def test_parse_args_ignores_launchservices_process_serial_number() -> None:
    args = parse_args(["-psn_0_12345", "--smoke-test"])

    assert args.smoke_test is True


def test_parse_args_supports_gui_startup_check_output() -> None:
    args = parse_args(["--gui-startup-check", "--gui-startup-check-output", "/tmp/startup.json"])

    assert args.gui_startup_check is True
    assert args.gui_startup_check_output == "/tmp/startup.json"
