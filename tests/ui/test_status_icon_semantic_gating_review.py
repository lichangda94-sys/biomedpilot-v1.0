from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

from app.shared.semantic_keys import ReportStatusKey, ResultSemanticKey


ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_MANIFEST = ROOT / "docs/ui/icon_production/UI_B8b8a_status_icon_production_manifest_20260521.csv"
GATING_MANIFEST = ROOT / "docs/ui/UI_B8b8b_status_icon_semantic_gating_manifest_20260521.csv"
ACTIVE_STATUS_DIR = ROOT / "assets/icons/status"
STATUS_IDS = {
    "status_testing",
    "status_planned",
    "status_shell_only",
    "status_developer_preview",
    "status_blocked",
    "status_available",
    "status_not_configured",
    "status_failed",
    "status_preflight_only",
    "status_draft",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_gating_manifest_covers_all_status_candidates() -> None:
    production_rows = _read_csv(PRODUCTION_MANIFEST)
    gating_rows = _read_csv(GATING_MANIFEST)

    assert len(production_rows) == 10
    assert len(gating_rows) == 10
    assert {row["resource_id"] for row in gating_rows} == {row["resource_id"] for row in production_rows}
    assert {row["candidate_svg_path"] for row in gating_rows} == {row["svg_path"] for row in production_rows}


def test_status_gating_manifest_stays_docs_only() -> None:
    rows = _read_csv(GATING_MANIFEST)

    assert all(row["candidate_svg_path"].startswith("docs/ui/icon_production/status/svg/") for row in rows)
    assert all(not row["candidate_svg_path"].startswith("assets/icons/status/") for row in rows)
    assert all(row["resource_id"].startswith("status_") for row in rows)
    assert all("app_icon" not in row["resource_id"] for row in rows)
    if ACTIVE_STATUS_DIR.exists():
        active_stems = {path.stem.removesuffix("_24").removesuffix("_32").removesuffix("_48").removesuffix("_64") for path in ACTIVE_STATUS_DIR.glob("*")}
        assert active_stems == STATUS_IDS
        assert not any(path.name.startswith(("result_", "report_", "export_", "share_", "empty_")) for path in ACTIVE_STATUS_DIR.glob("*"))
        assert not any("app_icon" in path.name for path in ACTIVE_STATUS_DIR.glob("*"))


def test_allowed_status_icons_require_labels_semantics_and_gates() -> None:
    rows = _read_csv(GATING_MANIFEST)

    for row in rows:
        assert row["pilot_allowed"] == "true"
        assert row["active_usage_allowed"] == "true"
        assert row["required_label"]
        assert row["required_tooltip"]
        assert row["disabled_state_required"] == "true"
        assert row["must_preserve_semantic_key"] == "true"
        assert row["must_preserve_status_key"] == "true"
        assert row["must_preserve_gate"] == "true"
        assert row["allowed_surface"] in {
            "status_chip_only",
            "blocked_status_chip_only",
            "detected_resource_status_chip_only",
            "resource_status_chip_only",
            "analysis_status_chip_only",
            "report_status_chip_only",
        }


def test_resource_available_status_stays_detect_first_and_conditional() -> None:
    rows = _read_csv(GATING_MANIFEST)
    by_id = {row["resource_id"]: row for row in rows}
    row = by_id["status_available"]

    assert row["gating_decision"] == "conditional_pilot_allowed"
    assert row["semantic_key"] == "resource.status.available"
    assert row["allowed_surface"] == "detected_resource_status_chip_only"
    assert "detect-first" in row["blocker_reason"]
    assert "install" in row["required_tooltip"].lower()
    assert "enable" in row["required_tooltip"].lower()


def test_planned_testing_shell_preflight_and_draft_do_not_imply_completion() -> None:
    rows = _read_csv(GATING_MANIFEST)
    by_id = {row["resource_id"]: row for row in rows}

    guarded = {
        "status_testing": "formal or production-ready",
        "status_planned": "not runnable",
        "status_shell_only": "no business implementation",
        "status_developer_preview": "not implied",
        "status_preflight_only": "no formal DEG GSEA survival clinical or report-ready result",
        "status_draft": "not report-ready",
    }
    for resource_id, required_phrase in guarded.items():
        assert required_phrase in by_id[resource_id]["required_tooltip"]


def test_gating_manifest_keeps_non_formal_semantics() -> None:
    rows = _read_csv(GATING_MANIFEST)
    semantics = {row["semantic_key"] for row in rows}

    assert ResultSemanticKey.FORMAL_COMPUTED_RESULT.value not in semantics
    assert ReportStatusKey.REPORT_READY_FUTURE.value not in semantics
    assert "report.status.report_ready" not in semantics
    assert "feature.status.testing" in semantics
    assert "analysis.status.preflight_only" in semantics
    assert ReportStatusKey.DRAFT.value in semantics


def test_status_chip_primitives_keep_existing_semantic_properties() -> None:
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    from app.shared.ui_components import make_status_chip

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    assert app is not None

    expected = {
        "testing": "feature.status.testing",
        "planned": "feature.status.planned",
        "shell_only": "feature.status.shell_only",
        "developer_preview": "feature.status.developer_preview",
        "blocked": "feature.status.blocked",
        "available": "resource.status.available",
        "not_configured": "resource.status.not_configured",
        "failed": "resource.status.failed",
        "preflight_only": "analysis.status.preflight_only",
        "draft": "report.status.draft",
    }

    for status_key, semantic_key in expected.items():
        chip = make_status_chip(status_key=status_key)
        assert chip.objectName() == "uiStatusChip"
        assert chip.property("statusKey") == status_key
        assert chip.property("semanticKey") == semantic_key
