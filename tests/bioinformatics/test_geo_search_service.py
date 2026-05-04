from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from app.bioinformatics.retrieval import GeoSearchService


def _fake_ncbi(url: str) -> dict[str, object]:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if parsed.path.endswith("esearch.fcgi"):
        assert "GSE[ETYP]" in query["term"][0]
        assert "Homo sapiens[Organism]" in query["term"][0]
        assert "glioma" in query["term"][0].lower()
        return {"esearchresult": {"idlist": ["1", "2"]}}
    return {
        "result": {
            "uids": ["1", "2"],
            "1": {
                "uid": "1",
                "accession": "GSEGLIOMA1",
                "title": "Glioma RNA-seq expression profiling dataset",
                "summary": "Human glioblastoma and lower grade glioma transcriptome samples.",
            },
            "2": {
                "uid": "2",
                "accession": "GSEBROAD1",
                "title": "General expression profiling dataset",
                "summary": "A mixed tissue expression profiling series.",
            },
        }
    }


def test_geo_search_executes_disease_aware_queries_and_ranks_results() -> None:
    response = GeoSearchService(opener=_fake_ncbi).search("脑胶质瘤", max_results=5)

    assert response.search_status == "completed"
    assert response.executed_queries
    assert response.executed_queries[0].startswith("(")
    assert "glioma" in response.executed_queries[0].lower()
    assert "glioblastoma" in response.executed_queries[0].lower()
    assert "GSE[ETYP]" in response.executed_queries[0]
    assert "Homo sapiens[Organism]" in response.executed_queries[0]
    assert response.results[0].accession == "GSEGLIOMA1"
    assert response.results[0].query_used
    assert "疾病词" in response.results[0].disease_relevance_reason


def test_geo_search_blocks_broad_query_without_confirmation() -> None:
    response = GeoSearchService(opener=_fake_ncbi).search("表达谱", max_results=5)

    assert response.search_status == "blocked_broad_query"
    assert response.executed_queries == ()
    assert response.results == ()
