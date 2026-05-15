from __future__ import annotations

import pytest

from app.labtools.experiment_templates import (
    EXPERIMENT_TEMPLATE_SCHEMA_VERSION,
    ExperimentTemplateError,
    ExperimentTemplateLibrary,
    create_record_draft,
    draft_markdown_preview,
)


def test_default_experiment_templates_cover_expected_drafts() -> None:
    library = ExperimentTemplateLibrary()
    templates = library.list_templates()
    names = [template.name for template in templates]

    assert "qPCR 实验计划模板" in names
    assert "Western blot 实验计划模板" in names
    assert "细胞实验接种计划模板" in names
    assert "Scratch assay 记录模板" in names
    assert "免疫荧光图像记录模板" in names
    assert len(templates) == 5
    assert all("人工复核" in template.review_notice for template in templates)


def test_create_experiment_record_draft_is_json_compatible_and_reviewable() -> None:
    template = ExperimentTemplateLibrary().get_template("qpcr_plan_draft")
    assert template is not None

    draft = create_record_draft(
        template,
        purpose="验证目标基因表达",
        sample_groups=("control n=3", "treated n=3"),
        reagents=("qPCR master mix", "primer pair"),
        key_parameters=("20 uL reaction", "3 technical replicates"),
        output_files=("raw_ct.csv", "plate_layout.csv"),
        notes=("人工复核 primer 和内参。",),
    )
    payload = draft.to_dict()

    assert payload["schema_version"] == EXPERIMENT_TEMPLATE_SCHEMA_VERSION
    assert payload["template_id"] == "qpcr_plan_draft"
    assert payload["status"] == "draft_manual_review_required"
    assert payload["sample_groups"] == ["control n=3", "treated n=3"]
    assert "人工复核" in payload["review_notice"]


def test_record_draft_validation_requires_core_sections() -> None:
    template = ExperimentTemplateLibrary().get_template("cell_seeding_plan_draft")
    assert template is not None

    with pytest.raises(ExperimentTemplateError, match="实验目的"):
        create_record_draft(
            template,
            purpose="",
            sample_groups=("A",),
            reagents=("medium",),
            key_parameters=("24 well",),
            output_files=("plate map",),
        )

    with pytest.raises(ExperimentTemplateError, match="样本分组"):
        create_record_draft(
            template,
            purpose="接种计划",
            sample_groups=("",),
            reagents=("medium",),
            key_parameters=("24 well",),
            output_files=("plate map",),
        )


def test_markdown_preview_keeps_draft_not_eln_semantics() -> None:
    template = ExperimentTemplateLibrary().get_template("scratch_assay_record_draft")
    assert template is not None
    draft = create_record_draft(
        template,
        purpose="记录划痕实验",
        sample_groups=("control time 0h", "treated time 24h"),
        reagents=("培养基",),
        key_parameters=("manual ROI rule", "threshold bright"),
        output_files=("roi_export_manifest.json",),
        notes=("不自动判断迁移效果。",),
    )

    markdown = draft_markdown_preview(draft)

    assert "LabTools 实验记录结构化草稿" in markdown
    assert "人工复核" in markdown
    assert "完整 ELN" in markdown
    assert "正式操作规程" in markdown
    forbidden = ["无需人工复核", "自动生成正式结论", "production-grade"]
    assert not any(term in markdown for term in forbidden)
