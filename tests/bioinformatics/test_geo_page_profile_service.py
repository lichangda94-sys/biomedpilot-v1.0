from __future__ import annotations

import gzip
import json
from pathlib import Path

from app.bioinformatics.services.geo_metadata_profile_service import GeoMetadataProfileService


GeoDatasetProfileService = GeoMetadataProfileService


def test_geo_profile_detects_tumor_normal_from_summary_and_design(tmp_path: Path) -> None:
    profile = GeoDatasetProfileService().build_profile(
        accession="GSE1000",
        candidate_metadata={
            "title_en": "Thyroid carcinoma expression profile",
            "summary_en": "Expression profiling of 10 tumor and 10 adjacent normal thyroid tissues.",
            "overall_design_en": "Tumor versus normal paired samples were analyzed by microarray.",
            "organism": "Homo sapiens",
            "sample_count": 20,
            "data_type": "microarray expression profiling",
        },
        asset_manifest=_manifest("GSE1000", expression_file=True),
    )

    assert profile.analysis_potential_level in {"低", "中"}
    assert profile.candidate_comparisons
    comparison = profile.candidate_comparisons[0]
    assert comparison.label == "tumor vs normal"
    assert comparison.requires_user_confirmation is True
    assert comparison.confidence == "low"
    assert comparison.sample_assignments == ()
    assert "summary/overall design" in " ".join(comparison.evidence)
    assert profile.sample_structure_preview["sample_types"] == {"normal": 10, "tumor": 10}
    assert profile.suggested_download_files
    assert profile.analysis_availability_status == ""


def test_geo_profile_detects_treated_control_from_sample_titles(tmp_path: Path) -> None:
    source = tmp_path / "GSE1001_family.soft.gz"
    _write_family_soft(
        source,
        title="drug response expression",
        samples=[
            ("GSM1", "control replicate 1", "cell line", ["treatment: control"]),
            ("GSM2", "control replicate 2", "cell line", ["treatment: control"]),
            ("GSM3", "treated replicate 1", "cell line", ["treatment: treated"]),
            ("GSM4", "treated replicate 2", "cell line", ["treatment: treated"]),
        ],
    )

    profile = GeoDatasetProfileService().build_profile(accession="GSE1001", family_soft_path=source)

    assert profile.sample_count == 4
    assert profile.geo_sample_count == 4
    assert profile.metadata_sample_count == 4
    assert profile.metadata_source == "family_soft"
    assert profile.candidate_comparisons[0].label == "treated vs control"
    assert profile.candidate_comparisons[0].group_sizes == {"control": 2, "treated": 2}
    assert profile.candidate_comparisons[0].confidence == "high"
    first_assignment = profile.candidate_comparisons[0].sample_assignments[0]
    assert first_assignment.sample_accession == "GSM1"
    assert first_assignment.assigned_group == "control"
    assert first_assignment.evidence_field == "treatment"
    assert first_assignment.evidence_text == "treatment: control"


def test_geo_profile_detects_resistant_sensitive_from_characteristics(tmp_path: Path) -> None:
    source = tmp_path / "GSE1002_family.soft.gz"
    _write_family_soft(
        source,
        title="resistance expression",
        samples=[
            ("GSM1", "sample 1", "tumor", ["response: resistant"]),
            ("GSM2", "sample 2", "tumor", ["response: resistant"]),
            ("GSM3", "sample 3", "tumor", ["response: sensitive"]),
            ("GSM4", "sample 4", "tumor", ["response: sensitive"]),
        ],
    )

    profile = GeoDatasetProfileService().build_profile(accession="GSE1002", family_soft_path=source)

    assert profile.candidate_comparisons[0].label == "resistant vs sensitive"
    assert profile.candidate_comparisons[0].group_sizes == {"resistant": 2, "sensitive": 2}


def test_geo_profile_does_not_promote_cell_lines_as_groups(tmp_path: Path) -> None:
    source = tmp_path / "GSE1010_family.soft.gz"
    _write_family_soft(
        source,
        title="cell line expression",
        samples=[
            ("GSM1", "A375 replicate 1", "A375", ["cell line: A375"]),
            ("GSM2", "A375 replicate 2", "A375", ["cell line: A375"]),
            ("GSM3", "Cal-62 replicate 1", "Cal-62", ["cell line: Cal-62"]),
            ("GSM4", "Cal-62 replicate 2", "Cal-62", ["cell line: Cal-62"]),
        ],
    )

    profile = GeoDatasetProfileService().build_profile(accession="GSE1010", family_soft_path=source)

    assert profile.candidate_comparisons == ()
    assert profile.sample_structure_preview["status"] == "no_group_detected"


def test_geo_profile_keeps_dose_and_timepoint_labels_low_or_absent(tmp_path: Path) -> None:
    source = tmp_path / "GSE1011_family.soft.gz"
    _write_family_soft(
        source,
        title="time course expression",
        samples=[
            ("GSM1", "0h rep1", "A549", ["condition: 0h"]),
            ("GSM2", "0h rep2", "A549", ["condition: 0h"]),
            ("GSM3", "24h rep1", "A549", ["condition: 24h"]),
            ("GSM4", "24h rep2", "A549", ["condition: 24h"]),
        ],
    )

    profile = GeoDatasetProfileService().build_profile(accession="GSE1011", family_soft_path=source)

    assert not profile.candidate_comparisons or profile.candidate_comparisons[0].confidence == "low"


def test_geo_profile_keeps_multiple_candidate_comparisons_preview_only(tmp_path: Path) -> None:
    source = tmp_path / "GSE1003-GPL570_series_matrix.txt"
    source.write_text(
        "\n".join(
            [
                "!Series_title = thyroid samples",
                "!Sample_geo_accession\tGSM1\tGSM2\tGSM3\tGSM4",
                "!Sample_characteristics_ch1\ttissue: tumor\ttissue: tumor\ttissue: normal\ttissue: normal",
                "!Sample_characteristics_ch1\tgenotype: mutant\tgenotype: wild type\tgenotype: mutant\tgenotype: wild type",
                "!series_matrix_table_begin",
                "ID_REF\tGSM1\tGSM2\tGSM3\tGSM4",
                "GeneA\t1\t2\t3\t4",
                "!series_matrix_table_end",
            ]
        ),
        encoding="utf-8",
    )

    profile = GeoDatasetProfileService().build_profile(accession="GSE1003", series_matrix_path=source)

    assert len(profile.candidate_comparisons) >= 2
    assert {item.comparison_id.split(":", 1)[0] for item in profile.candidate_comparisons} >= {"tissue", "genotype"}
    assert all(item.requires_user_confirmation for item in profile.candidate_comparisons)
    assert not (tmp_path / "manifests" / "manual_supplements" / "comparison_config.tsv").exists()


def test_series_matrix_parser_prefers_geo_accession_count_over_long_description_rows(tmp_path: Path) -> None:
    source = tmp_path / "GSE1009_series_matrix.txt"
    source.write_text(
        "\n".join(
            [
                "!Series_title = thyroid samples",
                "!Sample_geo_accession\tGSM1\tGSM2",
                "!Sample_title\tcontrol 1\ttumor 1",
                "!Sample_description\tcontrol desc\ttumor desc\textra prose that is not a sample",
                "!Sample_characteristics_ch1\tpathological diagnostic: normal\tpathological diagnostic: tumor",
                "!series_matrix_table_begin",
                "ID_REF\tGSM1\tGSM2",
                "GeneA\t1\t2",
                "!series_matrix_table_end",
            ]
        ),
        encoding="utf-8",
    )

    profile = GeoDatasetProfileService().build_profile(accession="GSE1009", series_matrix_path=source)

    assert profile.metadata_sample_count == 2
    assert [record.sample_accession for record in profile.sample_records] == ["GSM1", "GSM2"]
    assert profile.candidate_comparisons[0].group_sizes == {"normal": 1, "tumor": 1}


def test_geo_profile_penalizes_non_bulk_expression_modalities() -> None:
    profile = GeoDatasetProfileService().build_profile(
        accession="GSE1004",
        candidate_metadata={
            "title_en": "Single-cell ATAC-seq of thyroid carcinoma",
            "summary_en": "single-cell chromatin accessibility profiling",
            "organism": "Homo sapiens",
            "sample_count": 4,
            "data_type": "single-cell ATAC-seq",
        },
    )

    assert profile.recommendation_level in {"低", "不建议"}


def test_geo_profile_uses_chinese_summary_and_checks_consistency(tmp_path: Path) -> None:
    recognition = {
        "group_preview": {
            "sample_count": 8,
            "expression_sample_count": 8,
            "metadata_sample_count": 8,
            "sample_id_match_status": "matched",
            "group_sizes": {"control": 4, "treated": 4},
        },
        "files": [
            {
                "detected_assets": [
                    {"role": "platform_reference_hint", "platform_id": "GPL999"}
                ]
            }
        ],
    }
    profile = GeoDatasetProfileService().build_profile(
        accession="GSE1005",
        candidate_metadata={
            "title_en": "Glioma expression",
            "summary_en": "10 tumor and 10 normal samples.",
            "overall_design_en": "Tumor versus normal.",
            "platform_accessions": ["GPL570"],
            "sample_count": 20,
            "organism": "Homo sapiens",
        },
        summary_payload={"title_zh": "胶质瘤表达谱", "summary_zh": "胶质瘤样本摘要。", "brief_zh": "比较肿瘤和正常样本。"},
        recognition_report=recognition,
    )

    assert profile.chinese_title == "胶质瘤表达谱"
    assert profile.chinese_brief == "比较肿瘤和正常样本。"
    assert profile.consistency_review["status"] == "needs_review"
    assert any("不完全一致" in warning for warning in profile.warnings)


def test_geo_profile_reports_downloaded_availability_after_recognition() -> None:
    recognition = {
        "group_preview": {
            "status": "preview_only",
            "expression_sample_count": 4,
            "metadata_sample_count": 4,
            "sample_id_match_status": "matched",
        },
        "files": [
            {
                "recognized_type": "geo_series_matrix_container",
                "recognized_roles": ["expression_matrix", "sample_metadata"],
                "content_profile": {"sample_columns": ["GSM1", "GSM2", "GSM3", "GSM4"]},
            }
        ],
    }
    profile = GeoDatasetProfileService().build_profile(
        accession="GSE1006",
        candidate_metadata={
            "title_en": "bulk expression",
            "summary_en": "tumor and normal expression",
            "data_type": "microarray expression profiling",
            "sample_count": 4,
        },
        recognition_report=recognition,
    )

    assert profile.expression_sample_count == 4
    assert profile.analysis_availability_status in {"需要确认比较组", "暂不建议"}
    assert "可运行" not in profile.analysis_potential_level


def test_geo_profile_supplementary_preview_flags_large_raw_file() -> None:
    profile = GeoDatasetProfileService().build_profile(
        accession="GSE1007",
        asset_manifest={
            "assets": [
                {
                    "asset_type": "supplementary_file",
                    "role": "raw_data_candidate",
                    "file_name": "GSE1007_RAW.tar",
                    "remote_url": "https://example.test/GSE1007_RAW.tar",
                    "status": "remote_discovered",
                    "size_bytes": 900 * 1024 * 1024,
                }
            ],
            "summary": {},
        },
    )

    preview = profile.supplementary_file_preview[0]
    assert preview.predicted_type == "raw_data"
    assert preview.risk_level == "高"
    assert "确认后下载" in preview.recommendation


def test_geo_profile_supplementary_prioritizes_expression_tables() -> None:
    profile = GeoDatasetProfileService().build_profile(
        accession="GSE1012",
        asset_manifest={
            "assets": [
                {
                    "asset_type": "supplementary_file",
                    "file_name": "GSE1012_gene_counts_TPM.txt.gz",
                    "remote_url": "https://example.test/GSE1012_gene_counts_TPM.txt.gz",
                    "status": "remote_discovered",
                    "size_bytes": 3 * 1024 * 1024,
                },
                {
                    "asset_type": "supplementary_file",
                    "file_name": "GSE1012_sample_annotation.tsv",
                    "remote_url": "https://example.test/GSE1012_sample_annotation.tsv",
                    "status": "remote_discovered",
                    "size_bytes": 1024,
                },
                {
                    "asset_type": "supplementary_file",
                    "file_name": "GSE1012_RAW.tar",
                    "remote_url": "https://example.test/GSE1012_RAW.tar",
                    "status": "remote_discovered",
                    "size_bytes": 40 * 1024 * 1024,
                },
                {
                    "asset_type": "supplementary_file",
                    "file_name": "GSE1012_reads.fastq.gz",
                    "remote_url": "https://example.test/GSE1012_reads.fastq.gz",
                    "status": "remote_discovered",
                    "size_bytes": 30 * 1024 * 1024,
                },
                {
                    "asset_type": "supplementary_file",
                    "file_name": "GSE1012_diffexpr-results.csv.gz",
                    "remote_url": "https://example.test/GSE1012_diffexpr-results.csv.gz",
                    "status": "remote_discovered",
                    "size_bytes": 1024,
                },
            ],
            "summary": {},
        },
    )

    by_name = {item.file_name: item for item in profile.supplementary_file_preview}

    assert by_name["GSE1012_gene_counts_TPM.txt.gz"].predicted_type == "expression_matrix"
    assert by_name["GSE1012_gene_counts_TPM.txt.gz"].download_priority == "高"
    assert by_name["GSE1012_gene_counts_TPM.txt.gz"].should_default_select is True
    assert by_name["GSE1012_sample_annotation.tsv"].download_priority == "中"
    assert by_name["GSE1012_RAW.tar"].download_priority == "不建议"
    assert by_name["GSE1012_reads.fastq.gz"].should_default_select is False
    assert by_name["GSE1012_diffexpr-results.csv.gz"].predicted_type == "differential_result_table"
    assert by_name["GSE1012_diffexpr-results.csv.gz"].should_default_select is False
    assert profile.suggested_download_files[0] == "GSE1012_gene_counts_TPM.txt.gz"


def test_geo_profile_chinese_brief_does_not_create_groups() -> None:
    profile = GeoDatasetProfileService().build_profile(
        accession="GSE1008",
        candidate_metadata={"title_en": "unstructured dataset", "sample_count": 6},
        summary_payload={"brief_zh": "该数据集比较肿瘤和正常样本。"},
    )

    assert not profile.candidate_comparisons
    assert profile.sample_structure_preview["status"] == "no_group_detected"


def _write_family_soft(path: Path, *, title: str, samples: list[tuple[str, str, str, list[str]]]) -> None:
    lines = [
        "^SERIES = GSETEST",
        f"!Series_title = {title}",
        "!Series_summary = Human expression profiling.",
        "!Series_overall_design = Sample groups were compared.",
        "!Series_platform_id = GPL570",
    ]
    for accession, sample_title, source_name, characteristics in samples:
        lines.extend(
            [
                f"^SAMPLE = {accession}",
                f"!Sample_geo_accession = {accession}",
                f"!Sample_title = {sample_title}",
                f"!Sample_source_name_ch1 = {source_name}",
            ]
        )
        lines.extend(f"!Sample_characteristics_ch1 = {item}" for item in characteristics)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def _manifest(accession: str, *, expression_file: bool) -> dict[str, object]:
    assets = [
        {
            "asset_type": "family_soft",
            "role": "metadata_container",
            "file_name": f"{accession}_family.soft.gz",
            "remote_url": f"https://example.test/{accession}_family.soft.gz",
            "status": "downloaded",
        }
    ]
    if expression_file:
        assets.append(
            {
                "asset_type": "supplementary_file",
                "role": "supplementary_expression_candidate",
                "file_name": f"{accession}_expression_matrix.tsv.gz",
                "remote_url": f"https://example.test/{accession}_expression_matrix.tsv.gz",
                "status": "remote_discovered",
            }
        )
    return {
        "accession": accession,
        "assets": assets,
        "summary": {"expression_candidate_count": 1 if expression_file else 0},
    }
