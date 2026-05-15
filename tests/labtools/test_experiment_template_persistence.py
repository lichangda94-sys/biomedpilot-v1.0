from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.labtools.experiment_templates import (
    EXPERIMENT_TEMPLATE_SCHEMA_VERSION,
    LABTOOLS_EXPERIMENT_RECORD_DRAFT_STORE_SCHEMA_VERSION,
    ExperimentTemplateError,
    ExperimentTemplateLibrary,
    build_experiment_draft_store_payload,
    create_record_draft,
    evaluate_experiment_record_draft,
    load_experiment_draft_store,
    save_experiment_draft_store,
)


def _draft():
    template = ExperimentTemplateLibrary().get_template("qpcr_plan_draft")
    assert template is not None
    return create_record_draft(
        template,
        purpose="验证目标基因表达",
        sample_groups=("control n=3", "treated n=3"),
        reagents=("qPCR master mix", "primer pair"),
        key_parameters=("20 uL reaction", "3 technical replicates"),
        output_files=("raw_ct.csv", "plate_layout.csv"),
        notes=("人工复核 primer 和内参。",),
    )


def test_experiment_draft_payload_has_schema_and_draft_semantics() -> None:
    draft = _draft()

    payload = build_experiment_draft_store_payload((draft,))

    assert payload["schema_version"] == LABTOOLS_EXPERIMENT_RECORD_DRAFT_STORE_SCHEMA_VERSION
    assert payload["export_type"] == "labtools_experiment_record_draft_store"
    assert payload["software_channel"] == "Developer Preview / testing"
    assert payload["review_status"] == "manual_review_required"
    assert payload["draft_count"] == 1
    assert payload["source_schema_version"] == EXPERIMENT_TEMPLATE_SCHEMA_VERSION
    assert payload["drafts"][0]["draft_id"] == draft.draft_id
    assert payload["draft_reviews"][0]["status"] == "manual_review_required"
    assert "不自动保存、不写数据库、不联网、不调用 AI" in payload["persistence_note"]
    assert "人工核对" in payload["safety_note"]
    assert "完整 ELN" in payload["safety_note"]


def test_save_and_load_experiment_draft_store_round_trip(tmp_path) -> None:
    draft = _draft()
    target = tmp_path / "record drafts.json"

    save_result = save_experiment_draft_store((draft,), target)
    load_result = load_experiment_draft_store(save_result.path)

    saved_path = Path(save_result.path)
    payload = json.loads(saved_path.read_text(encoding="utf-8"))
    assert save_result.success is True
    assert saved_path.name == "record_drafts.json"
    assert payload["schema_version"] == LABTOOLS_EXPERIMENT_RECORD_DRAFT_STORE_SCHEMA_VERSION
    assert load_result.success is True
    assert load_result.draft_count == 1
    assert load_result.drafts[0].draft_id == draft.draft_id
    assert load_result.drafts[0].template_name == draft.template_name
    assert "人工核对" in load_result.review_notice


def test_save_experiment_draft_store_does_not_overwrite_existing_file(tmp_path) -> None:
    draft = _draft()
    target = tmp_path / "drafts.json"

    first = save_experiment_draft_store((draft,), target)
    first_text = Path(first.path).read_text(encoding="utf-8")
    second = save_experiment_draft_store((draft,), target)

    assert first.path != second.path
    assert Path(first.path).read_text(encoding="utf-8") == first_text
    assert Path(second.path).name == "drafts_001.json"


def test_save_experiment_draft_store_sanitizes_unsafe_filename(tmp_path) -> None:
    draft = _draft()

    result = save_experiment_draft_store((draft,), tmp_path / "草稿: qPCR 1.json")

    assert Path(result.path).name == "qPCR_1.json"
    assert "/" not in Path(result.path).name
    assert ":" not in Path(result.path).name


def test_load_experiment_draft_store_rejects_bad_schema(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"schema_version": "old", "drafts": []}), encoding="utf-8")

    with pytest.raises(ExperimentTemplateError, match="schema 不匹配"):
        load_experiment_draft_store(path)


def test_save_experiment_draft_store_rejects_empty_and_missing_parent(tmp_path) -> None:
    draft = _draft()
    with pytest.raises(ExperimentTemplateError, match="尚未生成"):
        save_experiment_draft_store((), tmp_path / "drafts.json")

    with pytest.raises(ExperimentTemplateError, match="保存路径所在文件夹不存在"):
        save_experiment_draft_store((draft,), tmp_path / "missing" / "drafts.json")


def test_load_experiment_draft_store_rejects_missing_path() -> None:
    with pytest.raises(ExperimentTemplateError, match="请选择实验记录草稿 JSON 文件"):
        load_experiment_draft_store("")


def test_experiment_draft_review_blocks_out_of_scope_protocol_terms() -> None:
    template = ExperimentTemplateLibrary().get_template("cell_seeding_plan_draft")
    assert template is not None
    draft = create_record_draft(
        template,
        purpose="人体实验治疗建议",
        sample_groups=("treated",),
        reagents=("medium",),
        key_parameters=("24 well",),
        output_files=("record.md",),
    )

    review = evaluate_experiment_record_draft(draft)

    assert review.allowed is False
    assert "LabTools 不保存" in review.errors[0]


def test_experiment_draft_review_keeps_manual_review_required() -> None:
    review = evaluate_experiment_record_draft(_draft())

    assert review.allowed is True
    assert review.status == "manual_review_required"
    assert "SOP" in review.review_notice
