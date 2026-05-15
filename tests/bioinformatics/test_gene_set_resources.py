from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.gene_set_resources import (
    GENE_SET_REGISTRY,
    build_gsea_gene_set_readiness,
    get_selected_gene_set,
    import_gmt_file,
    initialize_gene_set_registry,
    list_local_gene_sets,
    registry_path,
    remove_gene_set,
    select_gene_set,
    unselect_gene_set,
    validate_gene_set_registry,
)
from app.bioinformatics.project_readiness import run_project_readiness
from app.bioinformatics.project_workspace import create_bioinformatics_project


def _write_valid_gmt(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "HALLMARK_APOPTOSIS\tna\tBAX\tCASP3\tTP53",
                "CUSTOM_INTERFERON\tcurated\tSTAT1\tIRF1",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_invalid_gmt(path: Path) -> Path:
    path.write_text("BROKEN_SET\tmissing_genes\n", encoding="utf-8")
    return path


def _project_root(tmp_path: Path) -> Path:
    return create_bioinformatics_project("Gene Set Registry Project", tmp_path).project_root


def test_gene_set_registry_initializes_and_empty_selection(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)

    registry = initialize_gene_set_registry(project_root)

    assert registry["resources"] == []
    assert registry_path(project_root) == project_root / GENE_SET_REGISTRY
    assert registry_path(project_root).is_file()
    assert list_local_gene_sets(project_root) == []
    assert get_selected_gene_set(project_root) is None


def test_import_valid_gmt_copies_file_and_registers_available_resource(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    source = _write_valid_gmt(tmp_path / "custom_signature.gmt")
    original_text = source.read_text(encoding="utf-8")

    result = import_gmt_file(
        project_root,
        source,
        {
            "name": "Custom thyroid signatures",
            "collection_type": "Custom",
            "species": "human",
            "gene_id_type": "symbol",
            "source_name": "unit test import",
            "license_note": "user supplied",
        },
    )

    resource = result["resource"]
    copied_path = Path(str(result["copied_path"]))
    assert resource["status"] == "available"
    assert resource["gene_set_count"] == 2
    assert resource["gene_count_preview"][0]["gene_count"] == 3
    assert copied_path.is_file()
    assert copied_path != source
    assert copied_path.read_text(encoding="utf-8") == original_text
    assert source.read_text(encoding="utf-8") == original_text
    assert copied_path.is_relative_to(project_root / "user_data" / "bioinformatics" / "gene_sets" / "custom")
    registry = json.loads(registry_path(project_root).read_text(encoding="utf-8"))
    assert registry["resources"][0]["name"] == "Custom thyroid signatures"


def test_import_invalid_gmt_registers_invalid_validation_summary(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    source = _write_invalid_gmt(tmp_path / "broken.gmt")

    result = import_gmt_file(project_root, source, {"name": "Broken GMT"})

    resource = result["resource"]
    assert resource["status"] == "invalid"
    assert "Invalid GMT" in resource["validation_summary"]
    assert Path(str(result["copied_path"])).is_file()


def test_select_gene_set_is_single_choice_and_unselects(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    first = import_gmt_file(project_root, _write_valid_gmt(tmp_path / "first.gmt"), {"name": "First"})["resource"]
    second = import_gmt_file(project_root, _write_valid_gmt(tmp_path / "second.gmt"), {"name": "Second"})["resource"]

    select_gene_set(project_root, str(first["resource_id"]))
    select_gene_set(project_root, str(second["resource_id"]))

    selected = get_selected_gene_set(project_root)
    assert selected is not None
    assert selected["resource_id"] == second["resource_id"]
    resources = list_local_gene_sets(project_root)
    assert [item["selected_for_gsea"] for item in resources].count(True) == 1

    unselect_gene_set(project_root)
    assert get_selected_gene_set(project_root) is None


def test_validate_registry_marks_missing_after_local_gmt_deleted(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    resource = import_gmt_file(project_root, _write_valid_gmt(tmp_path / "delete_me.gmt"), {"name": "Delete me"})["resource"]
    select_gene_set(project_root, str(resource["resource_id"]))
    local_path = project_root / str(resource["local_path"])
    local_path.unlink()

    validation = validate_gene_set_registry(project_root)

    resource_after = validation["resources"][0]
    assert resource_after["status"] == "missing"
    readiness = build_gsea_gene_set_readiness(project_root)
    assert "gsea_gene_set_missing" in readiness["blocking_errors"]
    assert "gsea_gene_set_file_missing" in readiness["blocking_errors"]


def test_gsea_preflight_readiness_blocks_only_gsea_when_unselected(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)

    readiness = build_gsea_gene_set_readiness(project_root)
    report = run_project_readiness(project_root)["readiness_report"]

    assert readiness["selected"] is False
    assert readiness["blocking_errors"] == ["gsea_gene_set_not_selected"]
    assert report["gsea_gene_set_status"]["blocks_current_data_check"] is False  # type: ignore[index]
    assert report["gsea_gene_set_status"]["blocks_standardization"] is False  # type: ignore[index]
    assert report["gsea_gene_set_status"]["blocks_deg_preflight"] is False  # type: ignore[index]


def test_remove_gene_set_updates_registry_and_deletes_cached_copy(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    resource = import_gmt_file(project_root, _write_valid_gmt(tmp_path / "remove_me.gmt"), {"name": "Remove me"})["resource"]
    cached = project_root / str(resource["local_path"])

    removed = remove_gene_set(project_root, str(resource["resource_id"]))

    assert removed["removed_resource"]["resource_id"] == resource["resource_id"]
    assert list_local_gene_sets(project_root) == []
    assert not cached.exists()
