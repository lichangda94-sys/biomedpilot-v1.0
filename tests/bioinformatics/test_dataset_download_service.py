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


class _FakeGeoAssetDiscoverer:
    def discover(self, accession: str, target_dir: Path, download_result: dict[str, object]) -> dict[str, object]:
        family_path = Path(str(download_result["family_soft_path"]))
        return {
            "schema_version": "biomedpilot.geo_asset_manifest.v1",
            "accession": accession,
            "assets": [
                {
                    "asset_type": "family_soft",
                    "role": "metadata_container",
                    "file_name": family_path.name,
                    "status": "downloaded",
                    "local_path": str(family_path),
                    "remote_url": f"https://example.org/{family_path.name}",
                    "input_eligible": True,
                    "needs_download": False,
                },
                {
                    "asset_type": "series_matrix",
                    "role": "expression_matrix_candidate",
                    "file_name": f"{accession}-GPL570_series_matrix.txt.gz",
                    "status": "remote_discovered",
                    "local_path": "",
                    "remote_url": f"https://example.org/{accession}-GPL570_series_matrix.txt.gz",
                    "input_eligible": False,
                    "needs_download": True,
                },
                {
                    "asset_type": "supplementary_file",
                    "role": "supplementary_expression_candidate",
                    "file_name": f"{accession}_counts.tsv.gz",
                    "status": "remote_discovered",
                    "local_path": "",
                    "remote_url": f"https://example.org/{accession}_counts.tsv.gz",
                    "input_eligible": False,
                    "needs_download": True,
                },
            ],
            "summary": {
                "family_soft_count": 1,
                "downloaded_family_soft_count": 1,
                "series_matrix_count": 1,
                "downloaded_series_matrix_count": 0,
                "supplementary_file_count": 1,
                "expression_candidate_count": 2,
                "metadata_downloaded": True,
                "series_matrix_discovered": True,
                "supplementary_files_discovered": True,
                "expression_matrix_status": "remote_discovered",
                "recognition_ready": True,
            },
            "ui_status_parts": ["元数据已下载", "表达矩阵待确认", "已发现补充文件", "可进入识别"],
            "warnings": [],
        }


class _FakeGeoRemoteAssetDownloader:
    def download_asset(self, asset: dict[str, object], target_dir: Path) -> dict[str, object]:
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / Path(str(asset["file_name"])).name
        if str(asset.get("asset_type")) == "series_matrix":
            path.write_text(
                "\n".join(
                    [
                        "!Series_title = demo",
                        "!Series_geo_accession = GSE33630",
                        "!Series_platform_id = GPL570",
                        "!Sample_title = tumor",
                        "!Sample_geo_accession = GSM1",
                        "!series_matrix_table_begin",
                        "ID_REF\tGSM1\tGSM2",
                        "1007_s_at\t1.0\t2.0",
                        "!series_matrix_table_end",
                    ]
                ),
                encoding="utf-8",
            )
        else:
            path.write_text("gene\tGSM1\tGSM2\nTP53\t1\t2\n", encoding="utf-8")
        return {"status": "success", "local_path": str(path), "bytes_downloaded": path.stat().st_size}


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
    service = DatasetDownloadService(geo_downloader=_FakeGeoDownloader(), geo_asset_discoverer=_FakeGeoAssetDiscoverer())

    result = service.create_candidate_download_task(
        project_root=root,
        candidate=_candidate(),
        original_chinese_topic="脑胶质瘤",
        execute_download=True,
    )

    assert result.success
    assert result.status == "geo_metadata_downloaded"
    assert "元数据已下载" in result.message
    assert result.download_executed is True
    assert len(result.downloaded_files) == 1
    assert Path(result.downloaded_files[0]).name == "GSE33630_family.soft.gz"
    manifest_path = Path(str(result.details["asset_manifest_path"]))
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert {item["asset_type"] for item in manifest["assets"]} == {"family_soft", "series_matrix", "supplementary_file"}
    assert manifest["summary"]["metadata_downloaded"] is True
    assert manifest["summary"]["series_matrix_discovered"] is True
    assert manifest["summary"]["supplementary_files_discovered"] is True
    assert result.acquisition_summary is not None
    assert result.acquisition_summary.strategy == "reference"
    assert result.downloaded_files[0] in result.acquisition_summary.referenced_paths
    record = json.loads(result.acquisition_summary.record_path.read_text(encoding="utf-8"))
    assert record["metadata"]["registration_status"] == "registered_metadata_source"
    assert record["metadata"]["ready_for_recognition"] == "ready"
    assert record["metadata"]["asset_manifest_path"] == str(manifest_path)
    assert record["metadata"]["asset_manifest_summary"]["expression_matrix_status"] == "remote_discovered"


def test_geo_manifest_assets_download_updates_manifest_and_registers_files(tmp_path: Path) -> None:
    root = tmp_path / "project"
    service = DatasetDownloadService(
        geo_downloader=_FakeGeoDownloader(),
        geo_asset_discoverer=_FakeGeoAssetDiscoverer(),
        geo_asset_downloader=_FakeGeoRemoteAssetDownloader(),
    )
    metadata = service.create_candidate_download_task(
        project_root=root,
        candidate=_candidate(),
        original_chinese_topic="脑胶质瘤",
        execute_download=True,
    )

    result = service.download_geo_manifest_assets(project_root=root, accession_or_project="GSE33630")

    assert metadata.status == "geo_metadata_downloaded"
    assert result.success
    assert result.status == "geo_assets_downloaded"
    assert len(result.downloaded_files) == 2
    assert any(Path(path).name.endswith("_series_matrix.txt.gz") for path in result.downloaded_files)
    manifest = json.loads(Path(str(result.details["asset_manifest_path"])).read_text(encoding="utf-8"))
    assert manifest["summary"]["expression_matrix_status"] == "downloaded"
    assert manifest["summary"]["downloaded_supplementary_file_count"] == 1
    assert all(
        asset["status"] == "downloaded"
        for asset in manifest["assets"]
        if asset["asset_type"] in {"series_matrix", "supplementary_file"}
    )
    assert result.acquisition_summary is not None
    record = json.loads(result.acquisition_summary.record_path.read_text(encoding="utf-8"))
    assert record["strategy"] == "reference"
    assert record["metadata"]["download_status"] == "geo_assets_downloaded"
    assert record["metadata"]["asset_manifest_summary"]["expression_matrix_status"] == "downloaded"


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
        return '{"brief_zh":"该数据集比较胶质瘤样本和正常脑组织对照。","covered_terms":["胶质瘤","正常脑组织"],"missing_or_uncertain":[]}'

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
    assert summary.model_status["translate_model_status"] == "available"
    assert summary.model_status["brief_model_status"] == "available"


def test_geo_text_summary_service_accepts_latest_translate_model_alias() -> None:
    service = GeoTextSummaryService(model_names_provider=lambda: ("translategemma:latest", "medgemma:4b"))

    status = service.model_availability()

    assert service.is_available()
    assert status["translate_model_status"] == "available"
    assert status["brief_model_status"] == "available"


def test_geo_text_summary_service_requires_translate_and_medical_models() -> None:
    service = GeoTextSummaryService(model_names_provider=lambda: ("translategemma:latest",))

    summary = service.summarize(GeoStudyTextInput(accession="GSE33630", title_en="Glioma expression profile"))

    assert summary.status == "local_model_unavailable"
    assert summary.model_status["translate_model_status"] == "available"
    assert summary.model_status["brief_model_status"] == "missing"
    assert "医学提炼模型 medgemma:4b" in summary.error_message


def test_geo_text_summary_service_falls_back_when_brief_json_is_empty() -> None:
    def generator(model: str, prompt: str) -> str:
        if model == "translategemma":
            return '{"title_zh":"甲状腺滤泡癌表达谱","summary_zh":"研究甲状腺滤泡癌、滤泡腺瘤和正常甲状腺组织。","overall_design_zh":"比较甲状腺滤泡癌、滤泡腺瘤和正常甲状腺对照的 microarray 表达谱。"}'
        return '{"brief_zh":"","covered_terms":[],"missing_or_uncertain":["模型未能提炼简介"]}'

    service = GeoTextSummaryService(generator=generator, availability_checker=lambda: True)
    summary = service.summarize(
        GeoStudyTextInput(
            accession="GSETEST",
            title_en="Expression profiling of follicular thyroid carcinoma",
            summary_en="Follicular thyroid carcinoma, follicular adenoma and normal thyroid tissue.",
            overall_design_en="Microarray comparison of FTC, adenoma and normal thyroid controls.",
        )
    )

    assert summary.status == "completed"
    assert summary.brief_zh == "比较甲状腺滤泡癌、滤泡腺瘤和正常甲状腺对照的 microarray 表达谱。"
    assert "医学模型 brief_zh 为空" in "；".join(summary.quality_warnings)


def test_geo_text_summary_service_falls_back_when_local_model_unavailable() -> None:
    service = GeoTextSummaryService(availability_checker=lambda: False)

    summary = service.summarize(GeoStudyTextInput(accession="GSE33630", title_en="Glioma expression profile"))

    assert summary.status == "local_model_unavailable"
    assert summary.brief_zh == ""
    assert "不可用" in summary.error_message
