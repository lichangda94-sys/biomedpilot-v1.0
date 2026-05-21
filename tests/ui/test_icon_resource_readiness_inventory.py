import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "docs/ui/resource_inventory/UI_B8b3_icon_replacement_readiness_matrix_20260521.csv"
PLAN_PATH = ROOT / "docs/ui/resource_inventory/UI_B8b_icon_asset_plan_20260521.csv"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_icon_readiness_matrix_is_unique_and_placeholder_only() -> None:
    rows = _read_csv(MATRIX_PATH)

    assert len(rows) == 74
    assert len({row["resource_id"] for row in rows}) == len(rows)
    assert len({row["target_future_path"] for row in rows}) == len(rows)
    assert len({row["required_final_svg_path"] for row in rows}) == len(rows)

    for row in rows:
        assert row["replacement_ready"] == "false"
        assert row["placeholder_reference_path"].startswith("docs/ui/icon_extraction/batch_01/")
        assert (ROOT / row["placeholder_reference_path"]).exists()
        assert row["required_final_svg_path"].startswith(("assets/icons/", "assets/images/"))
        assert row["target_future_path"] == row["required_final_svg_path"]
        assert "docs/ui/icon_extraction" not in row["required_final_svg_path"]


def test_icon_readiness_priorities_follow_stage_rules() -> None:
    rows = _read_csv(MATRIX_PATH)
    expected = {
        "modules": "P1",
        "labtools": "P1",
        "bio_pages": "P1",
        "meta_pages": "P1",
        "settings_resources": "P2",
        "result_report_export": "P3",
        "empty_states": "P3",
        "status": "P4",
    }

    for row in rows:
        assert row["replacement_priority"] == expected[row["resource_family"]]


def test_semantic_key_reuse_is_explicitly_documented() -> None:
    rows = _read_csv(MATRIX_PATH)
    by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_key[row["semantic_key"]].append(row)

    duplicate_groups = {key: group for key, group in by_key.items() if len(group) > 1}
    assert duplicate_groups
    for group in duplicate_groups.values():
        assert all(row["semantic_reuse_reason"] for row in group)


def test_high_risk_families_are_not_replacement_ready() -> None:
    rows = _read_csv(MATRIX_PATH)
    guarded_families = {"status", "result_report_export"}
    guarded = [row for row in rows if row["resource_family"] in guarded_families]

    assert guarded
    assert all(row["replacement_ready"] == "false" for row in guarded)
    assert all(row["semantic_risk"].startswith("high:") for row in guarded)


def test_app_icon_remains_deferred_to_ui_b10() -> None:
    rows = _read_csv(PLAN_PATH)
    app_rows = [row for row in rows if row["resource_id"] == "app_icon_deferred"]

    assert len(app_rows) == 1
    app_icon = app_rows[0]
    assert app_icon["can_extract_from_board"] == "false"
    assert app_icon["replacement_allowed_now"] == "false"
    assert app_icon["replacement_gate"] == "UI-B10 only"
