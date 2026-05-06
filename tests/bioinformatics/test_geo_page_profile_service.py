from __future__ import annotations

import gzip
import json
from pathlib import Path

from app.bioinformatics.download.geo_page_profile_service import GeoDatasetProfileService


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

    assert profile.recommendation_level == "高"
    assert profile.candidate_comparisons
    comparison = profile.candidate_comparisons[0]
    assert comparison.label == "tumor vs normal"
    assert comparison.requires_user_confirmation is True
    assert profile.sample_structure_preview["sample_types"] == {"normal": 10, "tumor": 10}
    assert profile.suggested_download_files


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
    assert profile.candidate_comparisons[0].label == "treated vs control"
    assert profile.candidate_comparisons[0].group_sizes == {"control": 2, "treated": 2}
    assert profile.candidate_comparisons[0].confidence == "high"


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
    assert all(item.requires_user_confirmation for item in profile.candidate_comparisons)
    assert not (tmp_path / "manifests" / "manual_supplements" / "comparison_config.tsv").exists()


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
