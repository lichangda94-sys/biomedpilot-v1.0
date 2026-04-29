from __future__ import annotations

import json

from app.version import app_version_summary


def test_source_version_summary_reports_source_mode() -> None:
    summary = app_version_summary()

    assert summary.version == "0.1.0-internal-beta"
    assert summary.channel == "Developer Preview / testing"
    assert summary.launch_mode in {"source", "packaged-local-python"}


def test_packaged_build_info_overrides_launch_mode(tmp_path) -> None:
    (tmp_path / "BUILD_INFO.json").write_text(
        json.dumps(
            {
                "version": "0.1.0-internal-beta",
                "bundle_version": "0.1.0",
                "channel": "Developer Preview / testing",
                "launch_mode": "packaged-local-python",
                "git_head": "abc1234",
            }
        ),
        encoding="utf-8",
    )

    summary = app_version_summary(tmp_path)

    assert summary.launch_mode == "packaged-local-python"
    assert summary.git_head == "abc1234"
