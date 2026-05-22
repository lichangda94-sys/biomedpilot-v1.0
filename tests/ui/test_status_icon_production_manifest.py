import csv
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "docs/ui/resource_inventory/UI_B8b3_icon_replacement_readiness_matrix_20260521.csv"
MANIFEST_PATH = ROOT / "docs/ui/icon_production/UI_B8b8a_status_icon_production_manifest_20260521.csv"
STATUS_ROOT = "docs/ui/icon_production/status/"
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


def test_status_manifest_matches_readiness_matrix() -> None:
    matrix_rows = _read_csv(MATRIX_PATH)
    manifest_rows = _read_csv(MANIFEST_PATH)
    expected_ids = {
        row["resource_id"]
        for row in matrix_rows
        if row["resource_family"] == "status"
    }

    assert len(manifest_rows) == 10
    assert {row["resource_id"] for row in manifest_rows} == expected_ids
    assert {row["resource_family"] for row in manifest_rows} == {"status"}


def test_status_candidate_paths_are_docs_only_and_complete() -> None:
    rows = _read_csv(MANIFEST_PATH)
    seen_paths: set[str] = set()

    for row in rows:
        assert row["production_candidate"] == "true"
        assert row["replacement_ready"] == "false"
        assert row["ready_for_pilot_review"] == "false"
        assert row["requires_semantic_gating_review"] == "true"
        assert row["source_placeholder_reference"].startswith("docs/ui/icon_extraction/batch_01/status/")

        for key in ["svg_path", "png_24_path", "png_32_path", "png_48_path", "png_64_path"]:
            path = row[key]
            assert path.startswith(STATUS_ROOT)
            assert not path.startswith(("assets/icons/", "assets/images/"))
            assert path not in seen_paths
            assert (ROOT / path).exists()
            seen_paths.add(path)


def test_status_svgs_are_independent_vector_candidates() -> None:
    rows = _read_csv(MANIFEST_PATH)

    for row in rows:
        svg_text = (ROOT / row["svg_path"]).read_text(encoding="utf-8")
        assert "<svg" in svg_text
        assert "<image" not in svg_text
        assert "href=" not in svg_text
        assert ".png" not in svg_text
        assert "placeholder" not in svg_text.lower()


def test_status_png_exports_have_expected_sizes_and_transparent_canvas() -> None:
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


def test_status_stage_does_not_touch_active_assets_or_other_families() -> None:
    rows = _read_csv(MANIFEST_PATH)

    assert all(row["resource_id"].startswith("status_") for row in rows)
    assert all(not row["resource_id"].startswith(("result_", "report_", "export_", "share_", "empty_")) for row in rows)
    assert all("app_icon" not in row["resource_id"] for row in rows)
    assert all(row["svg_path"].startswith(STATUS_ROOT) for row in rows)
    assert all(not row["svg_path"].startswith("assets/") for row in rows)
    if ACTIVE_STATUS_DIR.exists():
        active_stems = {path.stem.removesuffix("_24").removesuffix("_32").removesuffix("_48").removesuffix("_64") for path in ACTIVE_STATUS_DIR.glob("*")}
        assert active_stems == STATUS_IDS
        assert not any(path.name.startswith(("result_", "report_", "export_", "share_", "empty_")) for path in ACTIVE_STATUS_DIR.glob("*"))
        assert not any("app_icon" in path.name for path in ACTIVE_STATUS_DIR.glob("*"))


def test_status_semantics_stay_non_final_until_gating_review() -> None:
    rows = _read_csv(MANIFEST_PATH)
    by_id = {row["resource_id"]: row for row in rows}

    assert by_id["status_testing"]["semantic_key"] == "feature.status.testing"
    assert by_id["status_planned"]["semantic_key"] == "feature.status.planned"
    assert by_id["status_shell_only"]["semantic_key"] == "feature.status.shell_only"
    assert by_id["status_developer_preview"]["semantic_key"] == "feature.status.developer_preview"
    assert by_id["status_preflight_only"]["semantic_key"] == "analysis.status.preflight_only"
    assert by_id["status_draft"]["semantic_key"] == "report.status.draft"

    forbidden_semantics = {"result.semantic.formal_computed_result", "report.status.report_ready"}
    assert forbidden_semantics.isdisjoint({row["semantic_key"] for row in rows})
    assert all(row["semantic_risk"].startswith("high:") for row in rows)
    assert all(row["replacement_ready"] == "false" for row in rows)
