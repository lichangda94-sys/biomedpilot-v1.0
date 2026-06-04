from __future__ import annotations

import gzip
import json
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from app.bioinformatics.gene_set_resources import (
    GENE_SET_REGISTRY,
    RUNTIME_GENE_SET_DOWNLOAD_POLICY,
    build_gsea_gene_set_readiness,
    download_gene_set_resource,
    get_selected_gene_set,
    import_gmt_file,
    initialize_gene_set_registry,
    list_downloadable_gene_set_resources,
    list_local_gene_sets,
    refresh_downloaded_gene_set,
    registry_path,
    remove_gene_set,
    select_gene_set,
    unselect_gene_set,
    validate_gene_set_registry,
)
from app.bioinformatics.project_readiness import run_project_readiness
from app.bioinformatics.project_workspace import create_bioinformatics_project
import app.bioinformatics.gene_set_resources as gene_set_resources


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


def _reactome_zip_bytes() -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("ReactomePathways.gmt", "R-HSA-1\tReactome pathway\tTP53\tBAX\nR-HSA-2\tReactome pathway\tSTAT1\tIRF1\n")
    return buffer.getvalue()


def _go_gaf_bytes() -> bytes:
    gaf = "\n".join(
        [
            "!gaf-version: 2.2",
            "UniProtKB\tP04637\tTP53\t\tGO:0006915\tPMID:1\tIDA\t\tP\tcellular tumor antigen p53\t\tprotein\ttaxon:9606\t20260515\tGO_Central",
            "UniProtKB\tQ07812\tBAX\t\tGO:0006915\tPMID:1\tIDA\t\tP\tBAX\t\tprotein\ttaxon:9606\t20260515\tGO_Central",
            "UniProtKB\tP42224\tSTAT1\t\tGO:0005634\tPMID:1\tIDA\t\tC\tSTAT1\t\tprotein\ttaxon:9606\t20260515\tGO_Central",
            "UniProtKB\tP10914\tIRF1\t\tGO:0003700\tPMID:1\tIDA\t\tF\tIRF1\t\tprotein\ttaxon:9606\t20260515\tGO_Central",
            "UniProtKB\tBAD\tBAD1\tNOT\tGO:0006915\tPMID:1\tIDA\t\tP\tBAD\t\tprotein\ttaxon:9606\t20260515\tGO_Central",
            "",
        ]
    )
    return gzip.compress(gaf.encode("utf-8"))


def _kegg_fetcher(url: str, _timeout: int) -> bytes:
    if "list/pathway/hsa" in url:
        return b"path:hsa00010\tGlycolysis / Gluconeogenesis - Homo sapiens (human)\npath:hsa04010\tMAPK signaling pathway - Homo sapiens (human)\n"
    if "link/pathway/hsa" in url:
        return b"hsa:10327\tpath:hsa00010\nhsa:124\tpath:hsa00010\nhsa:5594\tpath:hsa04010\n"
    raise AssertionError(url)


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


def test_list_downloadable_gene_set_resources_includes_common_sources(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)

    resources = list_downloadable_gene_set_resources(project_root)
    by_id = {item["resource_id"]: item for item in resources}

    assert {"reactome_pathways", "go_bp_human", "go_cc_human", "go_mf_human", "kegg_hsa_pathways", "msigdb_hallmark_user_import", "custom_gmt_import"} <= set(by_id)
    assert by_id["reactome_pathways"]["downloadable"] is False
    assert by_id["reactome_pathways"]["runtime_download_policy"] == RUNTIME_GENE_SET_DOWNLOAD_POLICY
    assert by_id["go_bp_human"]["downloadable"] is False
    assert by_id["kegg_hsa_pathways"]["downloadable"] is False
    assert by_id["msigdb_hallmark_user_import"]["downloadable"] is False
    assert "导入" in by_id["msigdb_hallmark_user_import"]["operation"]


def test_runtime_gene_set_download_is_blocked_by_default(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)

    with pytest.raises(RuntimeError, match=RUNTIME_GENE_SET_DOWNLOAD_POLICY):
        download_gene_set_resource(project_root, "reactome_pathways", fetcher=lambda *_: _reactome_zip_bytes())


def test_reactome_fake_zip_download_registers_available_resource(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    calls: list[str] = []

    def fetcher(url: str, _timeout: int) -> bytes:
        calls.append(url)
        return _reactome_zip_bytes()

    result = download_gene_set_resource(project_root, "reactome_pathways", fetcher=fetcher, allow_runtime_download=True)

    resource = result["resource"]
    assert resource["collection_type"] == "Reactome"
    assert resource["source_type"] == "downloaded"
    assert resource["status"] == "available"
    assert resource["gene_set_count"] == 2
    assert Path(project_root / resource["local_path"]).is_file()
    assert resource["checksum"]
    assert len(calls) == 1

    cached = download_gene_set_resource(project_root, "reactome_pathways", fetcher=lambda *_: (_ for _ in ()).throw(AssertionError("should not fetch")))
    assert cached["cached"] is True


def test_go_fake_annotation_generates_bp_cc_mf_gmt_resources(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)

    def fetcher(_url: str, _timeout: int) -> bytes:
        return _go_gaf_bytes()

    bp = download_gene_set_resource(project_root, "go_bp_human", fetcher=fetcher, allow_runtime_download=True)["resource"]
    cc = download_gene_set_resource(project_root, "go_cc_human", fetcher=fetcher, allow_runtime_download=True)["resource"]
    mf = download_gene_set_resource(project_root, "go_mf_human", fetcher=fetcher, allow_runtime_download=True)["resource"]

    assert bp["collection_type"] == "GO_BP"
    assert cc["collection_type"] == "GO_CC"
    assert mf["collection_type"] == "GO_MF"
    assert bp["gene_set_count"] == 1
    assert cc["gene_set_count"] == 1
    assert mf["gene_set_count"] == 1
    assert "BAD1" not in Path(project_root / bp["local_path"]).read_text(encoding="utf-8")


def test_kegg_fake_rest_generates_human_pathway_gmt(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)

    result = download_gene_set_resource(project_root, "kegg_hsa_pathways", fetcher=_kegg_fetcher, allow_runtime_download=True)

    resource = result["resource"]
    assert resource["collection_type"] == "KEGG"
    assert resource["gene_id_type"] == "entrez"
    assert resource["gene_set_count"] == 2
    text = Path(project_root / resource["local_path"]).read_text(encoding="utf-8")
    assert "hsa00010" in text
    assert "10327" in text
    assert "academic" in resource["license_note"]


def test_download_failure_does_not_break_existing_registry_or_selection(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    existing = download_gene_set_resource(project_root, "reactome_pathways", fetcher=lambda *_: _reactome_zip_bytes(), allow_runtime_download=True)["resource"]
    select_gene_set(project_root, str(existing["resource_id"]))

    try:
        refresh_downloaded_gene_set(project_root, "reactome_pathways", fetcher=lambda *_: (_ for _ in ()).throw(RuntimeError("offline")), allow_runtime_download=True)
    except RuntimeError:
        pass

    selected = get_selected_gene_set(project_root)
    assert selected is not None
    assert selected["resource_id"] == "reactome_pathways"
    assert selected["status"] == "available"


def test_downloaded_resource_missing_file_validates_missing_and_can_reselect_after_refresh(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    resource = download_gene_set_resource(project_root, "kegg_hsa_pathways", fetcher=_kegg_fetcher, allow_runtime_download=True)["resource"]
    select_gene_set(project_root, "kegg_hsa_pathways")
    Path(project_root / resource["local_path"]).unlink()

    validation = validate_gene_set_registry(project_root)

    missing = next(item for item in validation["resources"] if item["resource_id"] == "kegg_hsa_pathways")
    assert missing["status"] == "missing"
    refreshed = refresh_downloaded_gene_set(project_root, "kegg_hsa_pathways", fetcher=_kegg_fetcher, allow_runtime_download=True)["resource"]
    assert refreshed["status"] == "available"
    selected = get_selected_gene_set(project_root)
    assert selected is not None
    assert selected["resource_id"] == "kegg_hsa_pathways"


def test_default_fetcher_sends_user_agent_and_uses_https_context(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self) -> bytes:
            return b"ok"

    def fake_urlopen(request, *, timeout, context):
        captured["url"] = request.full_url
        captured["user_agent"] = request.headers.get("User-agent")
        captured["timeout"] = timeout
        captured["context"] = context
        return FakeResponse()

    monkeypatch.setattr(gene_set_resources, "urlopen", fake_urlopen)

    payload = gene_set_resources._fetch_bytes("https://example.test/resource.gmt", fetcher=None, timeout=12)

    assert payload == b"ok"
    assert captured["url"] == "https://example.test/resource.gmt"
    assert captured["user_agent"] == gene_set_resources.DOWNLOAD_USER_AGENT
    assert captured["timeout"] == 12
    assert captured["context"] is not None
