from __future__ import annotations

import ssl
from types import SimpleNamespace

from app.bioinformatics.search_center import (
    GTEX_BATCH_WARNING,
    BioinformaticsSourceRouter,
    GeoSearchAdapter,
    GtexSearchAdapter,
    QueryUnderstandingLayer,
    TcgaGdcSearchAdapter,
    UnifiedDatasetCandidate,
)
from app.bioinformatics.search_center.ranker import DatasetCandidateRanker


def test_query_understanding_allows_only_three_dataset_sources_and_no_pubmed() -> None:
    query = QueryUnderstandingLayer().understand("低分化甲状腺癌")

    assert query.allowed_sources == ("geo", "tcga_gdc", "gtex")
    assert "TCGA-THCA" in query.tcga_project_ids
    assert "Thyroid" in query.gtex_tissues
    assert "pubmed" not in " ".join(query.allowed_sources).lower()


def test_thyroid_query_generates_geo_tcga_and_gtex_mappings() -> None:
    query = QueryUnderstandingLayer().understand("甲状腺癌")

    assert query.geo_query_candidates
    assert "TCGA-THCA" in query.tcga_project_ids
    assert "Thyroid" in query.gtex_tissues


def test_glioma_query_generates_gbm_lgg_and_brain_mappings() -> None:
    query = QueryUnderstandingLayer().understand("脑胶质瘤")
    text = " ".join([*query.disease_terms_en, *query.geo_query_candidates]).lower()

    assert "glioma" in text or "glioblastoma" in text
    assert {"TCGA-GBM", "TCGA-LGG"} <= set(query.tcga_project_ids)
    assert "Brain" in query.gtex_tissues
    assert query.search_execution_status != "disease_terms_missing"


def test_geo_adapter_respects_limit_and_does_not_truncate_to_four_results() -> None:
    class FakeFetcher:
        def __init__(self, timeout: int = 8) -> None:
            self.timeout = timeout

        def search_series(self, query: str, max_results: int, page_size: int, start: int = 0):
            return SimpleNamespace(
                query=query,
                total_count=30,
                next_start=start + max_results,
                fetched_all=False,
                results=[
                    SimpleNamespace(
                        gse_id=f"GSE{70000 + index}",
                        title_en=f"Thyroid carcinoma expression dataset {index}",
                        summary_en="Homo sapiens thyroid cancer expression profiling tumor normal",
                        organism="Homo sapiens",
                        platform="GPL570",
                        experiment_type="expression profiling",
                        sample_count=10 + index,
                    )
                    for index in range(max_results)
                ],
            )

    query = QueryUnderstandingLayer().understand("甲状腺癌")
    result = GeoSearchAdapter().search(query, online_enabled=True, limit=20, fetcher_cls=FakeFetcher)

    assert result.search_status == "completed"
    assert len(result.candidates) == 20
    assert result.next_start == 20


def test_tcga_adapter_returns_project_asset_inventory_not_literature_shape() -> None:
    def fake_fetcher(url: str, params: dict[str, str], timeout: int):
        if "/projects/" in url:
            return {"data": {"project_id": "TCGA-THCA", "name": "Thyroid Carcinoma", "primary_site": "Thyroid"}}
        if url.endswith("/files"):
            return {
                "data": {
                    "hits": [
                        {
                            "data_category": "Transcriptome Profiling",
                            "data_type": "Gene Expression Quantification",
                            "workflow_type": "STAR - Counts",
                            "cases": [{"samples": [{"sample_type": "Primary Tumor"}]}],
                        }
                    ]
                }
            }
        return {
            "data": {
                "hits": [
                    {
                        "case_id": "case-1",
                        "diagnoses": [{"vital_status": "Alive", "days_to_last_follow_up": 100}],
                        "samples": [{"sample_type": "Primary Tumor"}],
                    }
                ]
            }
        }

    query = QueryUnderstandingLayer().understand("甲状腺癌")
    result = TcgaGdcSearchAdapter(fetcher=fake_fetcher).search(query, online_enabled=True)
    candidate = result.candidates[0]
    text = str(candidate.to_dict()).lower()

    assert candidate.accession_or_project == "TCGA-THCA"
    assert candidate.source_specific_metadata["record_shape"] == "tcga_gdc_project_asset_inventory"
    assert candidate.has_expression_matrix is True
    assert candidate.has_clinical_metadata is True
    assert candidate.source_specific_metadata["survival_field_availability"] is True
    assert candidate.source_specific_metadata["biospecimen_availability"] is True
    assert "pmid" not in text
    assert "pubmed" not in text


def test_gtex_adapter_returns_normal_reference_with_batch_warning() -> None:
    def fake_fetcher(url: str, params: dict[str, str], timeout: int):
        return {"data": [{"tissueSiteDetailId": "Thyroid", "tissueSiteDetail": "Thyroid", "rnaSeqSampleCount": 653, "datasetId": "GTEx_v8"}]}

    query = QueryUnderstandingLayer().understand("甲状腺癌")
    result = GtexSearchAdapter(fetcher=fake_fetcher).search(query, online_enabled=True)
    candidate = result.candidates[0]

    assert candidate.source == "gtex"
    assert candidate.disease == "normal reference"
    assert candidate.tissue == "Thyroid"
    assert candidate.source_specific_metadata["normal_reference"] is True
    assert GTEX_BATCH_WARNING in candidate.warnings


def test_gtex_ssl_error_returns_friendly_reference_candidate() -> None:
    def failing_fetcher(url: str, params: dict[str, str], timeout: int):
        raise ssl.SSLError("CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate")

    query = QueryUnderstandingLayer().understand("脑胶质瘤")
    result = GtexSearchAdapter(fetcher=failing_fetcher).search(query, online_enabled=True)
    text = " ".join([*result.warnings, result.error_message or "", *result.candidates[0].warnings])

    assert result.candidates
    assert "GTEx 在线检查失败：证书验证失败；已保留候选正常组织参考。" in text
    assert "CERTIFICATE_VERIFY_FAILED" not in text


def test_unified_candidate_schema_sorts_all_three_sources() -> None:
    candidates = (
        UnifiedDatasetCandidate("geo", "GSE1", "GEO", "Homo sapiens", "thyroid cancer", "thyroid", "RNA-seq", 10, True, True, False, True, ("deg",), True, 70, (), {}),
        UnifiedDatasetCandidate("tcga_gdc", "TCGA-THCA", "TCGA", "Homo sapiens", "thyroid cancer", "thyroid", "counts", 500, True, True, True, False, ("survival",), True, 95, (), {}),
        UnifiedDatasetCandidate("gtex", "GTEX-THYROID", "GTEx", "Homo sapiens", "normal reference", "Thyroid", "TPM", 653, True, True, False, False, ("reference",), True, 85, (GTEX_BATCH_WARNING,), {}),
    )

    ranked = DatasetCandidateRanker().rank(candidates)

    assert [candidate.source for candidate in ranked] == ["tcga_gdc", "gtex", "geo"]


def test_router_aggregates_three_sources_with_mock_live_adapters() -> None:
    def tcga_fetcher(url: str, params: dict[str, str], timeout: int):
        if "/projects/" in url:
            return {"data": {"project_id": "TCGA-THCA", "name": "Thyroid Carcinoma"}}
        if url.endswith("/files"):
            return {"data": {"hits": [{"data_category": "Transcriptome Profiling", "data_type": "Gene Expression Quantification", "workflow_type": "STAR - Counts"}]}}
        return {"data": {"hits": [{"diagnoses": [{"vital_status": "Alive"}], "samples": [{"sample_type": "Primary Tumor"}]}]}}

    def gtex_fetcher(url: str, params: dict[str, str], timeout: int):
        return {"data": [{"tissueSiteDetailId": "Thyroid", "tissueSiteDetail": "Thyroid", "sampleCount": 10}]}

    class GeoFetcher:
        def __init__(self, timeout: int = 8) -> None:
            self.timeout = timeout

        def search_series(self, query: str, max_results: int, page_size: int, start: int = 0):
            return SimpleNamespace(query=query, total_count=1, next_start=1, fetched_all=True, results=[])

    router = BioinformaticsSourceRouter(
        tcga_adapter=TcgaGdcSearchAdapter(fetcher=tcga_fetcher),
        gtex_adapter=GtexSearchAdapter(fetcher=gtex_fetcher),
    )
    result = router.search("甲状腺癌", online_enabled=True, geo_fetcher_cls=GeoFetcher)

    assert set(result.source_results) == {"geo", "tcga_gdc", "gtex"}
    assert result.source_results["tcga_gdc"].candidates
    assert result.source_results["gtex"].candidates
