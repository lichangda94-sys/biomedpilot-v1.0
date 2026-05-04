from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.download import DatasetDownloadService, GeoStudyTextInput, GeoTextSummaryService
from app.bioinformatics.search_center.models import UnifiedDatasetCandidate


def _candidate(source: str = "geo", accession: str = "GSE33630") -> UnifiedDatasetCandidate:
    metadata = {
        "query_used": '("glioma" OR "glioblastoma") AND GSE[ETYP]',
        "title_en": "Glioma RNA-seq expression profile",
        "summary_en": "Human glioblastoma and lower grade glioma transcriptome samples.",
        "platform_accessions": ["GPL11154"],
    }
    if source == "tcga_gdc":
        metadata = {"project_id": accession, "project_name": "Thyroid Carcinoma", "mapping_status": "mapped_not_online_checked"}
    elif source == "gtex":
        metadata = {"tissue_name": "Thyroid", "role": "normal_reference", "mapping_status": "mapped_not_online_checked"}
    return UnifiedDatasetCandidate(
        source=source,
        accession_or_project=accession,
        display_title="Thyroid Carcinoma" if source == "tcga_gdc" else ("GTEx Thyroid normal reference" if source == "gtex" else "Glioma RNA-seq expression profile"),
        organism="Homo sapiens",
        disease="glioma" if source == "geo" else "normal reference",
        tissue="brain" if source == "geo" else "Thyroid",
        data_modality="RNA-seq",
        sample_count=45,
        has_expression_matrix=source == "geo",
        has_sample_metadata=source == "geo",
        has_clinical_metadata=False,
        has_platform_annotation=source == "geo",
        recommended_analyses=("data_recognition",),
        download_plan_available=source == "geo",
        score=80,
        warnings=(),
        source_specific_metadata=metadata,
    )


class _FakeGeoDownloader:
    def download(self, accession: str, target_dir: Path) -> dict[str, object]:
        path = target_dir / f"{accession}_family.soft.gz"
        path.write_bytes(b"fake soft")
        return {
            "status": "success",
            "accession": accession,
            "family_soft_path": str(path),
            "full_download_success": True,
        }


def test_geo_candidate_download_task_writes_request_receipt_and_plan_record(tmp_path: Path) -> None:
    root = tmp_path / "project"
    service = DatasetDownloadService()

    result = service.create_candidate_download_task(
        project_root=root,
        candidate=_candidate(),
        original_chinese_topic="脑胶质瘤",
        execute_download=False,
    )

    assert result.success
    assert result.status == "registered_pending_geo_download"
    assert result.download_executed is False
    assert result.downloaded_files == ()
    assert Path(result.request_path).exists()
    assert Path(result.receipt_path).exists()
    receipt = json.loads(Path(result.receipt_path).read_text(encoding="utf-8"))
    assert receipt["download_executed"] is False
    assert receipt["downloaded_files"] == []
    assert receipt["metadata"]["original_chinese_topic"] == "脑胶质瘤"
    assert result.acquisition_summary is not None
    assert result.acquisition_summary.source_type == "geo_accession"
    record = json.loads(result.acquisition_summary.record_path.read_text(encoding="utf-8"))
    assert record["strategy"] == "plan_only"
    assert record["metadata"]["download_receipt_path"] == result.receipt_path
    assert record["metadata"]["ready_for_recognition"] == "pending_source_download"


def test_geo_candidate_execute_download_registers_downloaded_file_as_reference(tmp_path: Path) -> None:
    root = tmp_path / "project"
    service = DatasetDownloadService(geo_downloader=_FakeGeoDownloader())

    result = service.create_candidate_download_task(
        project_root=root,
        candidate=_candidate(),
        original_chinese_topic="脑胶质瘤",
        execute_download=True,
    )

    assert result.success
    assert result.status == "downloaded"
    assert result.download_executed is True
    assert len(result.downloaded_files) == 1
    assert Path(result.downloaded_files[0]).name == "GSE33630_family.soft.gz"
    assert result.acquisition_summary is not None
    assert result.acquisition_summary.strategy == "reference"
    assert result.downloaded_files[0] in result.acquisition_summary.referenced_paths
    record = json.loads(result.acquisition_summary.record_path.read_text(encoding="utf-8"))
    assert record["metadata"]["registration_status"] == "registered_downloaded_source"
    assert record["metadata"]["ready_for_recognition"] == "ready"


def test_tcga_and_gtex_download_tasks_do_not_fake_files(tmp_path: Path) -> None:
    service = DatasetDownloadService()
    tcga = service.create_candidate_download_task(
        project_root=tmp_path / "project",
        candidate=_candidate("tcga_gdc", "TCGA-THCA"),
        original_chinese_topic="甲状腺癌",
        execute_download=False,
    )
    gtex = service.create_candidate_download_task(
        project_root=tmp_path / "project",
        candidate=_candidate("gtex", "GTEX-THYROID"),
        original_chinese_topic="甲状腺癌",
        execute_download=False,
    )

    assert tcga.status == "registered_pending_gdc_download"
    assert gtex.status == "registered_pending_gtex_source_selection"
    assert tcga.downloaded_files == ()
    assert gtex.downloaded_files == ()
    assert "真实下载待接入" in tcga.message
    assert "真实下载待接入" in gtex.message


def test_geo_text_summary_service_uses_local_models_when_available() -> None:
    def generator(model: str, prompt: str) -> str:
        if model == "translategemma":
            return '{"title_zh":"胶质瘤表达谱","summary_zh":"胶质瘤与正常脑组织样本。","overall_design_zh":"肿瘤和正常对照。"}'
        return "该数据集比较胶质瘤样本和正常脑组织对照。"

    service = GeoTextSummaryService(generator=generator, availability_checker=lambda: True)
    summary = service.summarize(
        GeoStudyTextInput(
            accession="GSE33630",
            title_en="Glioma expression profile",
            summary_en="Glioma and normal brain samples.",
            overall_design_en="Tumor versus normal control.",
        )
    )

    assert summary.status == "completed"
    assert summary.title_zh == "胶质瘤表达谱"
    assert summary.brief_zh == "该数据集比较胶质瘤样本和正常脑组织对照。"


def test_geo_text_summary_service_falls_back_when_local_model_unavailable() -> None:
    service = GeoTextSummaryService(availability_checker=lambda: False)

    summary = service.summarize(GeoStudyTextInput(accession="GSE33630", title_en="Glioma expression profile"))

    assert summary.status == "local_model_unavailable"
    assert summary.brief_zh == ""
    assert "不可用" in summary.error_message
