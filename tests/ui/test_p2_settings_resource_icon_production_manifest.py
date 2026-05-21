import csv
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "docs/ui/resource_inventory/UI_B8b3_icon_replacement_readiness_matrix_20260521.csv"
MANIFEST_PATH = ROOT / "docs/ui/icon_production/UI_B8b5a_p2_settings_resource_icon_production_manifest_20260521.csv"
P2_ROOT = "docs/ui/icon_production/p2_settings/"
SETTINGS_ACTIVE_DIR = ROOT / "assets/icons/settings/resources"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_p2_settings_manifest_matches_readiness_matrix() -> None:
    matrix_rows = _read_csv(MATRIX_PATH)
    manifest_rows = _read_csv(MANIFEST_PATH)
    expected_ids = {
        row["resource_id"]
        for row in matrix_rows
        if row["replacement_priority"] == "P2" and row["resource_family"] == "settings_resources"
    }

    assert len(manifest_rows) == 13
    assert {row["resource_id"] for row in manifest_rows} == expected_ids
    assert {row["resource_family"] for row in manifest_rows} == {"settings_resources"}


def test_p2_settings_candidate_paths_are_docs_only_and_complete() -> None:
    rows = _read_csv(MANIFEST_PATH)
    seen_paths: set[str] = set()

    for row in rows:
        assert row["production_candidate"] == "true"
        assert row["replacement_ready"] == "false"
        assert row["ready_for_pilot_review"] == "true"
        assert row["source_placeholder_reference"].startswith("docs/ui/icon_extraction/batch_01/settings_resources/")

        for key in ["svg_path", "png_24_path", "png_32_path", "png_48_path", "png_64_path"]:
            path = row[key]
            assert path.startswith(P2_ROOT)
            assert not path.startswith(("assets/icons/", "assets/images/"))
            assert path not in seen_paths
            assert (ROOT / path).exists()
            seen_paths.add(path)


def test_p2_settings_svg_files_are_vector_candidates_not_placeholder_rasters() -> None:
    rows = _read_csv(MANIFEST_PATH)

    for row in rows:
        svg_text = (ROOT / row["svg_path"]).read_text(encoding="utf-8")
        assert "<svg" in svg_text
        assert "<image" not in svg_text
        assert "href=" not in svg_text
        assert ".png" not in svg_text
        assert "placeholder" not in svg_text.lower()


def test_p2_settings_png_exports_have_expected_sizes_and_transparent_canvas() -> None:
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


def test_p2_settings_production_manifest_remains_docs_only_and_active_pilot_stays_scoped() -> None:
    rows = _read_csv(MANIFEST_PATH)

    assert all(row["resource_id"].startswith("resource_") for row in rows)
    assert all("status_" not in row["resource_id"] for row in rows)
    assert all(not row["resource_id"].startswith(("result_", "report_", "export_", "share_", "empty_")) for row in rows)
    assert all(row["resource_id"] != "app_icon_deferred" for row in rows)
    assert all("app_icon" not in row["resource_id"] for row in rows)
    assert all(row["svg_path"].startswith(P2_ROOT) for row in rows)
    assert all(not row["svg_path"].startswith("assets/") for row in rows)

    if SETTINGS_ACTIVE_DIR.exists():
        active_svg_names = {path.name for path in SETTINGS_ACTIVE_DIR.glob("*.svg")}
        assert active_svg_names == {f"{row['resource_id']}.svg" for row in rows}
        assert not any(path.name.startswith("status_") for path in SETTINGS_ACTIVE_DIR.glob("*"))
        assert not any(path.name.startswith(("result_", "report_", "export_", "share_", "empty_")) for path in SETTINGS_ACTIVE_DIR.glob("*"))
        assert not any("app_icon" in path.name for path in SETTINGS_ACTIVE_DIR.glob("*"))


def test_p2_settings_semantic_risk_stays_guarded_for_external_capabilities() -> None:
    rows = _read_csv(MANIFEST_PATH)
    high_risk_ids = {
        "resource_imagej_fiji",
        "resource_pdf_ocr",
        "resource_local_model",
        "resource_cloud_ai",
    }
    by_id = {row["resource_id"]: row for row in rows}

    for resource_id in high_risk_ids:
        row = by_id[resource_id]
        assert row["semantic_risk"].startswith("high:")
        assert "detect-first/user-triggered semantics" in row["qa_notes"]
        assert row["replacement_ready"] == "false"
