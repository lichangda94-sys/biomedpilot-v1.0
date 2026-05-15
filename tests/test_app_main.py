from __future__ import annotations

from app.main import parse_args


def test_parse_args_ignores_launchservices_process_serial_number() -> None:
    args = parse_args(["-psn_0_12345", "--smoke-test"])

    assert args.smoke_test is True
