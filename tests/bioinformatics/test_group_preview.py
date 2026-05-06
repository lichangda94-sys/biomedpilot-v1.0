from __future__ import annotations

from pathlib import Path

from app.bioinformatics.group_preview import build_group_preview_report


def test_geo_series_matrix_characteristics_detects_tumor_normal_groups(tmp_path: Path) -> None:
    source = tmp_path / "GSE12345-GPL570_series_matrix.txt"
    source.write_text(
        "\n".join(
            [
                "!Series_title = demo",
                "!Sample_geo_accession\tGSM1\tGSM2\tGSM3\tGSM4",
                "!Sample_characteristics_ch1\ttissue: tumor\ttissue: tumor\ttissue: normal\ttissue: normal",
                "!series_matrix_table_begin",
                "ID_REF\tGSM1\tGSM2\tGSM3\tGSM4",
                "1007_s_at\t1\t2\t3\t4",
                "!series_matrix_table_end",
            ]
        ),
        encoding="utf-8",
    )

    report = build_group_preview_report(tmp_path, [_record(source, "geo_series_matrix_container", ["expression_matrix", "sample_metadata"])])

    assert report["status"] == "preview_only"
    assert report["selected_preview_field"] == "tissue"
    assert report["group_count"] == 2
    assert report["group_sizes"] == {"normal": 2, "tumor": 2}
    assert report["expression_sample_count"] == 4
    assert report["metadata_sample_count"] == 4
    assert report["sample_id_match_status"] == "matched"


def test_sample_metadata_condition_detects_two_groups(tmp_path: Path) -> None:
    source = tmp_path / "sample_metadata.tsv"
    source.write_text("sample_id\tcondition\ns1\tcontrol\ns2\tcontrol\ns3\ttreated\ns4\ttreated\n", encoding="utf-8")

    report = build_group_preview_report(tmp_path, [_record(source, "sample_metadata", ["sample_metadata"])])

    assert report["status"] == "preview_only"
    assert report["selected_preview_field"] == "condition"
    assert report["group_sizes"] == {"control": 2, "treated": 2}
    assert report["confidence"] == "high"


def test_expression_matrix_column_pattern_is_low_confidence(tmp_path: Path) -> None:
    source = tmp_path / "expression.tsv"
    source.write_text("gene\tcontrol_1\tcontrol_2\ttreated_1\ttreated_2\nTP53\t1\t2\t3\t4\n", encoding="utf-8")

    report = build_group_preview_report(tmp_path, [_record(source, "normalized_expression_matrix", ["normalized_expression_matrix"])])

    assert report["status"] == "preview_only"
    assert report["confidence"] == "low"
    assert report["selected_preview_field"] == "expression_column_pattern"
    assert report["group_sizes"] == {"control": 2, "treated": 2}
    assert "不能作为正式比较组" in "；".join(report["warnings"])


def test_no_group_detected_for_metadata_without_group_field(tmp_path: Path) -> None:
    source = tmp_path / "samples.tsv"
    source.write_text("sample_id\tplatform\ns1\tGPL570\ns2\tGPL570\n", encoding="utf-8")

    report = build_group_preview_report(tmp_path, [_record(source, "sample_metadata", ["sample_metadata"])])

    assert report["status"] == "no_group_detected"
    assert report["group_count"] == 0
    assert report["candidate_group_fields"] == []
    assert "未在样本信息表中识别到明确分组字段" in report["missing_group_reason"]


def test_multiple_candidate_group_fields_are_preserved(tmp_path: Path) -> None:
    source = tmp_path / "sample_metadata.tsv"
    source.write_text(
        "sample_id\tgroup\tcondition\ns1\tcase\ttumor\ns2\tcase\ttumor\ns3\tcontrol\tnormal\ns4\tcontrol\tnormal\n",
        encoding="utf-8",
    )

    report = build_group_preview_report(tmp_path, [_record(source, "sample_metadata", ["sample_metadata"])])

    assert report["selected_preview_field"] == "group"
    assert report["candidate_group_fields"] == ["group", "condition"]
    assert "多个可能分组字段" in "；".join(report["warnings"])


def _record(path: Path, recognized_type: str, roles: list[str]) -> dict[str, object]:
    return {
        "file_name": path.name,
        "original_path": str(path),
        "recognized_type": recognized_type,
        "recognized_roles": roles,
    }
