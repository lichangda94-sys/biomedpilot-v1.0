import csv
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "docs/ui/resource_inventory/UI_B8b3_icon_replacement_readiness_matrix_20260521.csv"
MANIFEST_PATH = ROOT / "docs/ui/icon_production/UI_B8b3_5_p1_icon_production_manifest_20260521.csv"
P1_ROOT = "docs/ui/icon_production/p1/"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_p1_icon_production_manifest_matches_readiness_matrix() -> None:
    matrix_rows = _read_csv(MATRIX_PATH)
    manifest_rows = _read_csv(MANIFEST_PATH)
    expected_ids = {
        row["resource_id"]
        for row in matrix_rows
        if row["replacement_priority"] == "P1"
    }

    assert len(manifest_rows) == 31
    assert {row["resource_id"] for row in manifest_rows} == expected_ids
    assert {row["resource_family"] for row in manifest_rows} == {
        "modules",
        "labtools",
        "bio_pages",
        "meta_pages",
    }


def test_p1_icon_candidate_paths_are_docs_only_and_complete() -> None:
    rows = _read_csv(MANIFEST_PATH)
    seen_paths: set[str] = set()

    for row in rows:
        assert row["production_candidate"] == "true"
        assert row["replacement_ready"] == "false"
        assert row["ready_for_pilot_review"] == "true"
        assert row["source_placeholder_reference"].startswith("docs/ui/icon_extraction/batch_01/")

        for key in ["svg_path", "png_24_path", "png_32_path", "png_48_path", "png_64_path"]:
            path = row[key]
            assert path.startswith(P1_ROOT)
            assert not path.startswith(("assets/icons/", "assets/images/"))
            assert path not in seen_paths
            assert (ROOT / path).exists()
            seen_paths.add(path)


def test_p1_svg_files_are_vector_candidates_not_placeholder_rasters() -> None:
    rows = _read_csv(MANIFEST_PATH)

    for row in rows:
        svg_text = (ROOT / row["svg_path"]).read_text(encoding="utf-8")
        assert "<svg" in svg_text
        assert "<image" not in svg_text
        assert "href=" not in svg_text
        assert ".png" not in svg_text
        assert "placeholder" not in svg_text.lower()


def test_p1_png_exports_have_expected_sizes_and_transparent_canvas() -> None:
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


def test_non_p1_families_are_excluded_from_p1_production() -> None:
    rows = _read_csv(MANIFEST_PATH)
    excluded_families = {
        "status",
        "settings_resources",
        "result_report_export",
        "empty_states",
        "app_icon_deferred",
    }

    assert not ({row["resource_family"] for row in rows} & excluded_families)
    assert all("status_" not in row["resource_id"] for row in rows)
    assert all(not row["resource_id"].startswith("export_") for row in rows)
    assert all(not row["resource_id"].startswith("resource_") for row in rows)
    assert all(not row["resource_id"].startswith("empty_") for row in rows)
    assert all(row["resource_id"] != "app_icon_deferred" for row in rows)
