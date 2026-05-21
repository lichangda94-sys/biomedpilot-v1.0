import csv
from pathlib import Path

from app.shared.result_report_export_shell import empty_result_preview_state
from app.shared.semantic_keys import ReportStatusKey, ResultSemanticKey


ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_MANIFEST = ROOT / "docs/ui/icon_production/UI_B8b7a_result_report_export_icon_production_manifest_20260521.csv"
GATING_MANIFEST = ROOT / "docs/ui/UI_B8b7b_result_report_export_icon_gating_manifest_20260521.csv"
ACTIVE_RRE_DIR = ROOT / "assets/icons/result_report_export"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_gating_manifest_covers_all_result_report_export_candidates() -> None:
    production_rows = _read_csv(PRODUCTION_MANIFEST)
    gating_rows = _read_csv(GATING_MANIFEST)

    assert len(production_rows) == 14
    assert len(gating_rows) == 14
    assert {row["resource_id"] for row in gating_rows} == {row["resource_id"] for row in production_rows}
    assert {row["candidate_svg_path"] for row in gating_rows} == {row["svg_path"] for row in production_rows}


def test_only_low_risk_marker_icons_are_allowed_for_initial_pilot() -> None:
    rows = _read_csv(GATING_MANIFEST)
    allowed = {row["resource_id"] for row in rows if row["pilot_allowed"] == "true"}

    assert allowed == {
        "result_overview",
        "result_table",
        "result_summary",
        "report_template",
        "result_clear",
    }

    for row in rows:
        if row["pilot_allowed"] == "true":
            assert row["gating_decision"] == "pilot_allowed"
            assert row["active_usage_allowed"] == "true"
            assert row["disabled_state_required"] == "true"
            assert row["must_preserve_gate"] == "true"
            assert row["allowed_surface"] in {
                "page_region_marker_only",
                "draft_template_marker_only",
                "disabled_helper_icon_only",
            }


def test_generate_export_share_archive_icons_are_not_action_pilot_allowed() -> None:
    rows = _read_csv(GATING_MANIFEST)
    by_id = {row["resource_id"]: row for row in rows}
    guarded = {
        "report_generate",
        "export_result",
        "export_pdf",
        "export_excel",
        "export_csv",
        "export_archive",
        "share_result",
    }

    for resource_id in guarded:
        row = by_id[resource_id]
        assert row["pilot_allowed"] == "false"
        assert row["active_usage_allowed"] == "false"
        assert row["disabled_state_required"] == "true"
        assert row["must_preserve_gate"] == "true"
        assert row["gating_decision"] in {"blocked_until_function_ready", "future_only"}
        assert row["allowed_surface"] == "none"


def test_chart_and_statistics_icons_stay_disabled_or_future_only() -> None:
    rows = _read_csv(GATING_MANIFEST)
    by_id = {row["resource_id"]: row for row in rows}

    for resource_id in {"result_chart", "result_statistics"}:
        row = by_id[resource_id]
        assert row["pilot_allowed"] == "false"
        assert row["active_usage_allowed"] == "false"
        assert row["gating_decision"] == "disabled_affordance_only"
        assert row["disabled_state_required"] == "true"
        assert row["must_preserve_gate"] == "true"
        assert "fake" in row["blocker_reason"] or "formal" in row["blocker_reason"]


def test_gating_manifest_does_not_point_to_active_assets_or_deferred_families() -> None:
    rows = _read_csv(GATING_MANIFEST)

    assert all(row["candidate_svg_path"].startswith("docs/ui/icon_production/result_report_export/svg/") for row in rows)
    assert all(not row["candidate_svg_path"].startswith("assets/icons/result_report_export/") for row in rows)
    assert all(not row["resource_id"].startswith(("status_", "empty_")) for row in rows)
    assert all("app_icon" not in row["resource_id"] for row in rows)
    assert not ACTIVE_RRE_DIR.exists()


def test_gating_manifest_keeps_non_formal_semantics() -> None:
    rows = _read_csv(GATING_MANIFEST)
    semantics = {row["semantic_key"] for row in rows}

    assert ResultSemanticKey.FORMAL_COMPUTED_RESULT.value not in semantics
    assert ReportStatusKey.REPORT_READY_FUTURE.value not in semantics
    assert "report.status.report_ready" not in semantics
    assert ResultSemanticKey.TESTING_SUMMARY_ONLY.value in semantics
    assert ReportStatusKey.DRAFT.value in semantics


def test_gating_review_does_not_rewrite_result_report_export_shell_state() -> None:
    state = empty_result_preview_state(module="bioinformatics")

    assert state.result_semantic_key == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert state.report_status_key == ReportStatusKey.DRAFT.value
    assert state.export_gate.value == "disabled_empty_result"
    assert state.export_enabled is False
    assert state.report_ready_package_allowed is False
