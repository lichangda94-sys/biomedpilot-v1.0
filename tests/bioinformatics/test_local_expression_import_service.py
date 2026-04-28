from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.bioinformatics.pages.local_expression_import_page import initial_local_expression_import_state
from app.bioinformatics.services.local_expression_import_service import LocalExpressionImportService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[LocalExpressionImportService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = LocalExpressionImportService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def write_text_matrix(path: Path, delimiter: str) -> Path:
    path.write_text(
        delimiter.join(["gene_symbol", "GSM001", "GSM002", "sample_note"]) + "\n"
        + delimiter.join(["TP53", "1.2", "2.4", "control"]) + "\n"
        + delimiter.join(["EGFR", "", "4.8", "tumor"]) + "\n",
        encoding="utf-8",
    )
    return path


def test_local_expression_import_rejects_empty_path(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.import_expression_matrix(project_id="bio-test", source_path="")
    assert not result.success
    assert "请输入" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_local_expression_import_rejects_missing_file(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.import_expression_matrix(project_id="bio-test", source_path=str(tmp_path / "missing.csv"))
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].error_message == result.message
    assert data_center.list_assets() == []


def test_local_expression_import_rejects_unsupported_extension(tmp_path) -> None:
    source = tmp_path / "matrix.json"
    source.write_text("{}", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.import_expression_matrix(project_id="bio-test", source_path=str(source))
    assert not result.success
    assert "CSV、TSV、TXT 或 XLSX" in result.message


def test_local_expression_import_reads_csv_and_registers_asset(tmp_path) -> None:
    source = write_text_matrix(tmp_path / "matrix.csv", ",")
    service, task_center, data_center = make_service(tmp_path)
    result = service.import_expression_matrix(project_id="bio-test", source_path=str(source))
    assert result.success
    assert result.source_type == "csv"
    assert result.row_count == 2
    assert result.column_count == 4
    assert result.candidate_gene_columns == ["gene_symbol"]
    assert result.candidate_sample_columns == ["GSM001", "GSM002", "sample_note"]
    assert result.numeric_sample_column_count == 2
    assert result.missing_value_rate == 0.1667
    output = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert output["data_type"] == "expression_matrix"
    assert output["status"] == "ready_for_asset_confirmation"
    assert output["raw_file_modified"] is False
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.IMPORT
    assert task.module == "bioinformatics"
    assert "local_expression_import" in task.summary
    asset = data_center.list_assets("bio-test")[0]
    assert asset.module == "bioinformatics"
    assert asset.data_type == "expression_matrix"
    assert asset.source_path == str(source)
    assert asset.output_path == result.output_path
    assert asset.status == "available"


def test_local_expression_import_reads_tsv(tmp_path) -> None:
    source = write_text_matrix(tmp_path / "matrix.tsv", "\t")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.import_expression_matrix(project_id="bio-test", source_path=str(source))
    assert result.success
    assert result.source_type == "tsv"
    assert result.numeric_sample_column_count == 2


def test_local_expression_import_reads_txt_as_tab_delimited(tmp_path) -> None:
    source = write_text_matrix(tmp_path / "matrix.txt", "\t")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.import_expression_matrix(project_id="bio-test", source_path=str(source))
    assert result.success
    assert result.source_type == "txt"
    assert result.candidate_gene_columns == ["gene_symbol"]


def test_local_expression_import_reads_xlsx(tmp_path) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    source = tmp_path / "matrix.xlsx"
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(["probe_id", "TCGA-01", "TCGA-02"])
    worksheet.append(["1007_s_at", 10.0, 12.5])
    worksheet.append(["1053_at", 8.1, None])
    workbook.save(source)
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.import_expression_matrix(project_id="bio-test", source_path=str(source))
    assert result.success
    assert result.source_type == "xlsx"
    assert result.candidate_gene_columns == ["probe_id"]
    assert result.candidate_sample_columns == ["TCGA-01", "TCGA-02"]
    assert result.numeric_sample_column_count == 2
    assert result.missing_value_rate == 0.25


def test_local_expression_import_warns_for_weak_matrix_shape(tmp_path) -> None:
    source = tmp_path / "weak.csv"
    source.write_text("description\nnot numeric\n", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.import_expression_matrix(project_id="bio-test", source_path=str(source))
    assert result.success
    assert any("没有识别到 gene/probe 列" in warning for warning in result.warnings)
    assert any("数值样本列太少" in warning for warning in result.warnings)
    assert any("文件行列数异常" in warning for warning in result.warnings)


def test_local_expression_import_warns_for_high_missing_rate(tmp_path) -> None:
    source = tmp_path / "missing.csv"
    source.write_text("gene,S1,S2\nA,,\nB,1,\n", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.import_expression_matrix(project_id="bio-test", source_path=str(source))
    assert result.success
    assert result.missing_value_rate == 0.5
    assert any("缺失值比例较高" in warning for warning in result.warnings)


def test_local_expression_import_feature_status_and_page_state() -> None:
    feature = get_feature("bio-local-expression-import")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "CSV / TSV / TXT / XLSX" in feature.description
    state = initial_local_expression_import_state()
    assert state.title == "本地表达矩阵导入"
    assert state.status_label == "测试中"
    assert state.import_button_label == "导入表达矩阵"
    assert "数据资产确认" in state.next_step
