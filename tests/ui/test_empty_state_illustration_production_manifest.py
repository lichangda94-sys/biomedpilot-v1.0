import csv
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "docs/ui/resource_inventory/UI_B8b3_icon_replacement_readiness_matrix_20260521.csv"
MANIFEST_PATH = ROOT / "docs/ui/icon_production/UI_B8b6a_empty_state_illustration_production_manifest_20260521.csv"
EMPTY_STATE_ROOT = "docs/ui/icon_production/empty_states/"
ACTIVE_EMPTY_STATE_DIR = ROOT / "assets/images/empty_states"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_empty_state_manifest_matches_readiness_matrix() -> None:
    matrix_rows = _read_csv(MATRIX_PATH)
    manifest_rows = _read_csv(MANIFEST_PATH)
    expected_ids = {
        row["resource_id"]
        for row in matrix_rows
        if row["resource_family"] == "empty_states"
    }

    assert len(manifest_rows) == 6
    assert {row["resource_id"] for row in manifest_rows} == expected_ids
    assert {row["resource_family"] for row in manifest_rows} == {"empty_states"}


def test_empty_state_candidate_paths_are_docs_only_and_complete() -> None:
    rows = _read_csv(MANIFEST_PATH)
    seen_paths: set[str] = set()

    for row in rows:
        assert row["production_candidate"] == "true"
        assert row["replacement_ready"] == "false"
        assert row["ready_for_pilot_review"] == "true"
        assert row["source_placeholder_reference"].startswith("docs/ui/icon_extraction/batch_01/empty_states/")

        for key in ["svg_path", "png_24_path", "png_32_path", "png_48_path", "png_64_path"]:
            path = row[key]
            assert path.startswith(EMPTY_STATE_ROOT)
            assert not path.startswith(("assets/icons/", "assets/images/"))
            assert path not in seen_paths
            assert (ROOT / path).exists()
            seen_paths.add(path)


def test_empty_state_svgs_are_independent_vector_candidates() -> None:
    rows = _read_csv(MANIFEST_PATH)

    for row in rows:
        svg_text = (ROOT / row["svg_path"]).read_text(encoding="utf-8")
        assert "<svg" in svg_text
        assert "<image" not in svg_text
        assert "href=" not in svg_text
        assert ".png" not in svg_text
        assert "placeholder" not in svg_text.lower()


def test_empty_state_png_exports_have_expected_sizes_and_transparent_canvas() -> None:
    rows = _read_csv(MANIFEST_PATH)
    expected = {
        "png_24_path": (24, 24),
        "png_32_path": (32, 32),
        "png_48_path": (48, 48),
        "png_64_path": (64, 64),
    }

    for row in rows:
        for key, size in expected.items():
            image = Image.open(ROOT / row[key])
            assert image.mode == "RGBA"
            assert image.size == size
            assert image.getpixel((0, 0))[3] == 0


def test_empty_state_stage_does_not_touch_active_assets_or_deferred_families() -> None:
    rows = _read_csv(MANIFEST_PATH)

    assert all(row["resource_id"].startswith("empty_") for row in rows)
    assert all(not row["resource_id"].startswith(("status_", "result_", "report_", "export_", "share_")) for row in rows)
    assert all("app_icon" not in row["resource_id"] for row in rows)
    assert all(row["svg_path"].startswith(EMPTY_STATE_ROOT) for row in rows)
    assert all(not row["svg_path"].startswith("assets/") for row in rows)
    if ACTIVE_EMPTY_STATE_DIR.exists():
        assert all(path.name.startswith("empty_") for path in ACTIVE_EMPTY_STATE_DIR.glob("*"))
        assert not any(path.name.startswith(("status_", "result_", "report_", "export_", "share_")) for path in ACTIVE_EMPTY_STATE_DIR.glob("*"))
        assert not any("app_icon" in path.name for path in ACTIVE_EMPTY_STATE_DIR.glob("*"))


def test_empty_state_semantics_do_not_claim_formal_results_or_reports() -> None:
    rows = _read_csv(MANIFEST_PATH)
    by_id = {row["resource_id"]: row for row in rows}

    assert by_id["empty_result"]["semantic_key"] == "result.semantic.testing_summary_only"
    assert by_id["empty_missing_resource"]["semantic_key"] == "resource.status.not_configured"
    assert by_id["empty_preflight_only"]["semantic_key"] == "analysis.status.preflight_only"

    forbidden_semantics = {"result.semantic.formal_computed_result", "report.status.report_ready"}
    assert forbidden_semantics.isdisjoint({row["semantic_key"] for row in rows})
    assert all(row["replacement_ready"] == "false" for row in rows)
