import csv
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "docs/ui/resource_inventory/UI_B8b3_icon_replacement_readiness_matrix_20260521.csv"
MANIFEST_PATH = ROOT / "docs/ui/icon_production/UI_B8b7a_result_report_export_icon_production_manifest_20260521.csv"
RRE_ROOT = "docs/ui/icon_production/result_report_export/"
ACTIVE_RRE_DIR = ROOT / "assets/icons/result_report_export"
ACTIVE_PILOT_ALLOWED_IDS = {"result_overview", "result_table", "result_summary", "report_template", "result_clear"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_result_report_export_manifest_matches_readiness_matrix() -> None:
    matrix_rows = _read_csv(MATRIX_PATH)
    manifest_rows = _read_csv(MANIFEST_PATH)
    expected_ids = {
        row["resource_id"]
        for row in matrix_rows
        if row["resource_family"] == "result_report_export"
    }

    assert len(manifest_rows) == 14
    assert {row["resource_id"] for row in manifest_rows} == expected_ids
    assert {row["resource_family"] for row in manifest_rows} == {"result_report_export"}


def test_result_report_export_candidate_paths_are_docs_only_and_complete() -> None:
    rows = _read_csv(MANIFEST_PATH)
    seen_paths: set[str] = set()

    for row in rows:
        assert row["production_candidate"] == "true"
        assert row["replacement_ready"] == "false"
        assert row["ready_for_pilot_review"] == "false"
        assert row["requires_gating_review"] == "true"
        assert row["source_placeholder_reference"].startswith("docs/ui/icon_extraction/batch_01/result_report_export/")

        for key in ["svg_path", "png_24_path", "png_32_path", "png_48_path", "png_64_path"]:
            path = row[key]
            assert path.startswith(RRE_ROOT)
            assert not path.startswith(("assets/icons/", "assets/images/"))
            assert path not in seen_paths
            assert (ROOT / path).exists()
            seen_paths.add(path)


def test_result_report_export_svgs_are_independent_vector_candidates() -> None:
    rows = _read_csv(MANIFEST_PATH)

    for row in rows:
        svg_text = (ROOT / row["svg_path"]).read_text(encoding="utf-8")
        assert "<svg" in svg_text
        assert "<image" not in svg_text
        assert "href=" not in svg_text
        assert ".png" not in svg_text
        assert "placeholder" not in svg_text.lower()


def test_result_report_export_png_exports_have_expected_sizes_and_transparent_canvas() -> None:
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


def test_result_report_export_stage_does_not_touch_active_assets_or_deferred_families() -> None:
    rows = _read_csv(MANIFEST_PATH)

    assert all(row["resource_id"].startswith(("result_", "report_", "export_", "share_")) for row in rows)
    assert all(not row["resource_id"].startswith(("status_", "empty_")) for row in rows)
    assert all("app_icon" not in row["resource_id"] for row in rows)
    assert all(row["svg_path"].startswith(RRE_ROOT) for row in rows)
    assert all(not row["svg_path"].startswith("assets/") for row in rows)
    if ACTIVE_RRE_DIR.exists():
        active_stems = {path.stem.removesuffix("_24").removesuffix("_32").removesuffix("_48").removesuffix("_64") for path in ACTIVE_RRE_DIR.glob("*")}
        assert active_stems == ACTIVE_PILOT_ALLOWED_IDS
        assert not any(path.name.startswith(("status_", "empty_")) for path in ACTIVE_RRE_DIR.glob("*"))
        assert not any("app_icon" in path.name for path in ACTIVE_RRE_DIR.glob("*"))


def test_result_report_export_semantics_remain_gated_and_non_formal() -> None:
    rows = _read_csv(MANIFEST_PATH)
    by_id = {row["resource_id"]: row for row in rows}

    assert by_id["result_overview"]["semantic_key"] == "result.semantic.testing_summary_only"
    assert by_id["result_chart"]["semantic_key"] == "result.semantic.testing_summary_only"
    assert by_id["result_table"]["semantic_key"] == "result.semantic.testing_summary_only"
    assert by_id["result_statistics"]["semantic_key"] == "analysis.status.testing_level"
    assert by_id["report_generate"]["semantic_key"] == "report.status.draft"
    assert by_id["report_template"]["semantic_key"] == "report.status.draft"
    assert by_id["export_excel"]["semantic_key"] == "export.format.xlsx"
    assert by_id["export_csv"]["semantic_key"] == "export.format.csv"

    forbidden_semantics = {"result.semantic.formal_computed_result", "report.status.report_ready"}
    assert forbidden_semantics.isdisjoint({row["semantic_key"] for row in rows})
    assert all(row["semantic_risk"].startswith("high:") for row in rows)
    assert all(row["replacement_ready"] == "false" for row in rows)
