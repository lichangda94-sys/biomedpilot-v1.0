from __future__ import annotations

import json

from app.bioinformatics.project_workspace import (
    BIOINFORMATICS_PROJECT_DIRECTORIES,
    PROJECT_CONFIG_FILENAME,
    PROJECT_MANIFEST_FILENAME,
    create_bioinformatics_project,
    open_bioinformatics_project,
)


def test_create_bioinformatics_project_writes_contract_files(tmp_path) -> None:
    summary = create_bioinformatics_project("Demo Project", tmp_path)

    assert summary.project_name == "Demo Project"
    assert summary.project_root.exists()
    assert summary.manifest_path.name == PROJECT_MANIFEST_FILENAME
    assert summary.config_path.name == PROJECT_CONFIG_FILENAME
    assert summary.current_stage == "project_created"
    assert summary.readiness_status == "ready_for_data_source_selection"
    assert summary.warning_count == 0
    for directory in BIOINFORMATICS_PROJECT_DIRECTORIES:
        assert (summary.project_root / directory).is_dir()

    manifest = json.loads(summary.manifest_path.read_text(encoding="utf-8"))
    assert manifest["project_type"] == "bioinformatics"
    assert manifest["project_name"] == "Demo Project"
    assert manifest["directories"]["raw_data"].endswith("raw_data")


def test_open_valid_bioinformatics_project_reads_summary(tmp_path) -> None:
    created = create_bioinformatics_project("Readable Project", tmp_path)

    validation = open_bioinformatics_project(created.project_root)

    assert validation.is_valid
    assert validation.summary is not None
    assert validation.summary.project_name == "Readable Project"
    assert validation.summary.project_root == created.project_root
    assert validation.summary.current_stage == "project_created"
    assert validation.summary.readiness_status == "ready_for_data_source_selection"


def test_open_invalid_bioinformatics_project_reports_chinese_error(tmp_path) -> None:
    invalid_dir = tmp_path / "plain-folder"
    invalid_dir.mkdir()

    validation = open_bioinformatics_project(invalid_dir)

    assert not validation.is_valid
    assert validation.summary is None
    assert validation.errors == ("该文件夹不是有效的生信分析项目，或缺少 project_manifest.json。",)


def test_open_project_with_sparse_manifest_uses_safe_defaults(tmp_path) -> None:
    project_root = tmp_path / "sparse"
    project_root.mkdir()
    (project_root / PROJECT_MANIFEST_FILENAME).write_text(
        json.dumps({"project_type": "bioinformatics"}, ensure_ascii=False),
        encoding="utf-8",
    )

    validation = open_bioinformatics_project(project_root)

    assert validation.is_valid
    assert validation.summary is not None
    assert validation.summary.project_name == "未知"
    assert validation.summary.created_at == "未记录"
    assert validation.summary.current_stage == "未知"
    assert validation.summary.readiness_status == "尚未生成"
