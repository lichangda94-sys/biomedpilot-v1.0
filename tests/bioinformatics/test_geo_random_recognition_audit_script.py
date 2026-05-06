from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.bio_geo_random_recognition_audit as audit
from app.bioinformatics.retrieval.geo_search_service import GeoDatasetResult
from app.bioinformatics.services.geo_metadata_profile_service import GeoMetadataProfile, GeoSupplementaryFile


def test_parse_args_defaults_and_explicit_values() -> None:
    default = audit.parse_args([])
    explicit = audit.parse_args(
        [
            "--queries",
            "thyroid cancer, breast cancer",
            "--per-query",
            "2",
            "--max-total",
            "4",
            "--seed",
            "123",
            "--download-mode",
            "profile_only",
            "--max-file-mb",
            "7",
            "--max-total-mb",
            "9",
            "--no-skip-raw",
            "--workdir",
            "/tmp/geo-audit-test",
            "--keep-files",
            "--output",
            "docs/out.md",
        ]
    )

    assert default.queries == ("thyroid cancer", "breast cancer", "lung cancer", "colorectal cancer", "melanoma")
    assert default.seed == 202605
    assert explicit.queries == ("thyroid cancer", "breast cancer")
    assert explicit.per_query == 2
    assert explicit.max_total == 4
    assert explicit.seed == 123
    assert explicit.download_mode == "profile_only"
    assert explicit.skip_raw is False
    assert explicit.keep_files is True


def test_stratified_sampling_is_seed_reproducible() -> None:
    config = audit.AuditConfig(queries=("q",), per_query=3, max_total=3, seed=42)
    candidates = [audit.GeoAuditCandidate("q", f"GSE{i}", f"title {i}", "", "q") for i in range(9)]
    levels = ["高", "中", "低"] * 3
    profiles = {candidate.accession: GeoMetadataProfile(accession=candidate.accession, analysis_potential_level=levels[index]) for index, candidate in enumerate(candidates)}

    first, _ = audit.stratified_sample_candidates(candidates, profiles, config)
    second, _ = audit.stratified_sample_candidates(candidates, profiles, config)

    assert [item.accession for item in first] == [item.accession for item in second]
    assert {profiles[item.accession].analysis_potential_level for item in first} == {"高", "中", "低"}


def test_plan_downloads_respects_max_file_and_raw_skip() -> None:
    profile = _profile_with_assets(
        GeoSupplementaryFile("GSE1_series_matrix.txt.gz", remote_url=_geo("matrix/GSE1_series_matrix.txt.gz"), asset_type="series_matrix", predicted_type="expression_matrix", file_size=3),
        GeoSupplementaryFile("GSE1_expression.tsv.gz", remote_url=_geo("suppl/GSE1_expression.tsv.gz"), asset_type="supplementary_file", predicted_type="expression_matrix", file_size=2 * 1024 * 1024),
        GeoSupplementaryFile("GSE1_RAW.tar", remote_url=_geo("suppl/GSE1_RAW.tar"), asset_type="supplementary_file", predicted_type="raw_data", file_size=2),
    )
    config = audit.AuditConfig(queries=("q",), download_mode="metadata_plus_small_supplementary", max_file_mb=1, max_total_mb=10)

    decisions = audit.plan_downloads(profile, config)
    by_name = {item.file_name: item for item in decisions}

    assert by_name["GSE1_series_matrix.txt.gz"].decision == "download"
    assert by_name["GSE1_expression.tsv.gz"].decision == "skipped"
    assert "max_file_mb" in by_name["GSE1_expression.tsv.gz"].reason
    assert by_name["GSE1_RAW.tar"].decision == "skipped"
    assert "raw" in by_name["GSE1_RAW.tar"].reason.lower()


def test_download_selected_assets_respects_total_limit(tmp_path: Path) -> None:
    config = audit.AuditConfig(queries=("q",), download_mode="metadata_plus_small_supplementary", max_file_mb=10, max_total_mb=1)
    candidate = audit.GeoAuditCandidate("q", "GSE1", "title", "", "q")
    profile = GeoMetadataProfile(accession="GSE1")
    decisions = [
        audit.DownloadDecision("a.tsv", _geo("suppl/a.tsv"), "supplementary_file", "expression_matrix", "download", "small", 700_000),
        audit.DownloadDecision("b.tsv", _geo("suppl/b.tsv"), "supplementary_file", "expression_matrix", "download", "small", 700_000),
    ]

    downloaded, resolved, total, warnings = audit.download_selected_assets(
        candidate,
        profile,
        decisions,
        tmp_path,
        config,
        fetcher=lambda url, timeout: b"x" * 700_000,
    )

    assert len(downloaded) == 1
    assert total == 700_000
    assert warnings == []
    assert resolved[1].decision == "skipped"
    assert "max_total_mb" in resolved[1].reason


def test_download_modes_profile_metadata_and_small_supplementary(tmp_path: Path) -> None:
    profile = _profile_with_assets(
        GeoSupplementaryFile("GSE1_family.soft.gz", remote_url=_geo("soft/GSE1_family.soft.gz"), asset_type="family_soft", predicted_type="metadata_container", file_size=20),
        GeoSupplementaryFile("GSE1_series_matrix.txt.gz", remote_url=_geo("matrix/GSE1_series_matrix.txt.gz"), asset_type="series_matrix", predicted_type="expression_matrix", file_size=20),
        GeoSupplementaryFile("GSE1_expression.tsv.gz", remote_url=_geo("suppl/GSE1_expression.tsv.gz"), asset_type="supplementary_file", predicted_type="expression_matrix", file_size=20),
    )

    profile_only = audit.plan_downloads(profile, audit.AuditConfig(queries=("q",), download_mode="profile_only"))
    metadata = audit.plan_downloads(profile, audit.AuditConfig(queries=("q",), download_mode="metadata_only"))
    small = audit.plan_downloads(profile, audit.AuditConfig(queries=("q",), download_mode="metadata_plus_small_supplementary"))

    assert all(item.decision == "skipped" for item in profile_only)
    assert {item.file_name for item in metadata if item.decision == "download"} == {"GSE1_family.soft.gz", "GSE1_series_matrix.txt.gz"}
    assert {item.file_name for item in small if item.decision == "download"} == {"GSE1_family.soft.gz", "GSE1_series_matrix.txt.gz", "GSE1_expression.tsv.gz"}


def test_report_generation_writes_markdown_and_jsonl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    result = audit.GseAuditResult(
        accession="GSE1",
        query="thyroid cancer",
        seed=1,
        selected=True,
        selection_reason="test",
        analysis_potential_level="高",
        profile={
            "title": "Title",
            "summary": "Summary",
            "overall_design": "Design",
            "metadata_sample_count": 2,
            "candidate_comparisons": [{"label": "tumor vs normal", "group_sizes": {"tumor": 1, "normal": 1}, "confidence": "high", "requires_user_confirmation": True}],
            "supplementary_file_preview": [
                {
                    "file_name": "GSE1_gene_counts_TPM.txt.gz",
                    "predicted_type": "expression_matrix",
                    "download_priority": "高",
                    "should_default_select": True,
                }
            ],
        },
        recognition_report={"files": [{"recognized_type": "expression_matrix", "recognized_roles": ["expression_matrix", "sample_metadata"]}], "group_preview": {"group_count": 2, "group_sizes": {"tumor": 1, "normal": 1}, "confidence": "high"}},
        readiness_report={"overall_status": "partially_ready"},
        downloaded_files=[str(tmp_path / "a.tsv")],
    )
    config = audit.AuditConfig(queries=("thyroid cancer",), output=Path("docs/report.md"))

    md = audit.write_markdown_report([result], config, config.output)
    jsonl = audit.write_jsonl_results([result], config, run_id="run-1")

    assert md.exists()
    assert jsonl.exists()
    assert "测试配置" in md.read_text(encoding="utf-8")
    assert "GSE1" in md.read_text(encoding="utf-8")
    assert "错误类型归纳" in md.read_text(encoding="utf-8")
    assert "suspected_group_misclassification_count" in md.read_text(encoding="utf-8")
    assert "recommended expression supplementary" in md.read_text(encoding="utf-8")
    assert '"accession": "GSE1"' in jsonl.read_text(encoding="utf-8")
    assert '"supplementary_high_priority_count": 1' in jsonl.read_text(encoding="utf-8")


def test_collect_geo_candidates_continues_after_query_failure() -> None:
    class FakeSearch:
        def search(self, query: str, **kwargs):
            if query == "bad":
                raise RuntimeError("network down")
            return SimpleNamespace(
                error_message="",
                results=(GeoDatasetResult("GSE1", "Title", "Summary", query, 1.0, "matched"),),
            )

    config = audit.AuditConfig(queries=("bad", "good"), per_query=1)
    candidates, skipped = audit.collect_geo_candidates(config, search_service=FakeSearch())  # type: ignore[arg-type]

    assert [item.accession for item in candidates] == ["GSE1"]
    assert skipped
    assert "search_exception" in skipped[0].skipped_reason


def test_run_audit_profile_only_does_not_download_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSearch:
        def search(self, query: str, **kwargs):
            return SimpleNamespace(
                error_message="",
                results=(GeoDatasetResult("GSE1", "Title", "tumor and normal expression", query, 1.0, "matched"),),
            )

    config = audit.AuditConfig(queries=("thyroid cancer",), per_query=1, max_total=1, download_mode="profile_only", workdir=tmp_path / "audit", keep_files=True)
    monkeypatch.setattr(audit, "remote_file_size", lambda url, timeout: 100)
    results = audit.run_audit(
        config,
        search_service=FakeSearch(),  # type: ignore[arg-type]
        fetcher=lambda url, timeout: _quick_text().encode(),
        directory_lister=lambda url, timeout: [{"file_name": "GSE1_series_matrix.txt.gz", "remote_url": _geo("matrix/GSE1_series_matrix.txt.gz"), "size_bytes": 100}],
    )

    selected = [item for item in results if item.selected]
    assert len(selected) == 1
    assert selected[0].downloaded_files == []
    assert all(decision.decision == "skipped" for decision in selected[0].download_decisions)


def _profile_with_assets(*assets: GeoSupplementaryFile) -> GeoMetadataProfile:
    return GeoMetadataProfile(accession="GSE1", supplementary_file_preview=assets)


def _geo(path: str) -> str:
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/GSE0nnn/GSE1/{path}"


def _quick_text() -> str:
    return "\n".join(
        [
            "^SERIES = GSE1",
            "!Series_title = Test",
            "!Series_summary = tumor and normal expression",
            "!Series_overall_design = tumor versus normal",
            "!Series_platform_id = GPL570",
        ]
    )
