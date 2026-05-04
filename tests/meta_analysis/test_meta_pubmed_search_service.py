from __future__ import annotations

from app.meta_analysis.search.pubmed_search_service import PubMedSearchService


ESEARCH_COUNT_RESPONSE = b'{"esearchresult":{"count":"42","idlist":[]}}'
ESEARCH_RESPONSE = b'{"esearchresult":{"count":"3","idlist":["111","222","111"]}}'
EFETCH_RESPONSE = b"""<?xml version="1.0" encoding="UTF-8"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>111</PMID>
      <Article>
        <ArticleTitle>Mock PubMed Trial One</ArticleTitle>
        <Abstract><AbstractText>First PubMed abstract.</AbstractText></Abstract>
        <Journal><Title>Mock Journal</Title><JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue></Journal>
        <AuthorList><Author><ForeName>Alice</ForeName><LastName>Adams</LastName></Author></AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>222</PMID>
      <Article>
        <ArticleTitle>Mock PubMed Trial Two</ArticleTitle>
        <Abstract><AbstractText>Second PubMed abstract.</AbstractText></Abstract>
        <Journal><Title>Mock Journal 2</Title><JournalIssue><PubDate><Year>2025</Year></PubDate></JournalIssue></Journal>
        <AuthorList><Author><ForeName>Ben</ForeName><LastName>Baker</LastName></Author></AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>111</PMID>
      <Article>
        <ArticleTitle>Mock PubMed Trial One Duplicate</ArticleTitle>
        <Journal><Title>Mock Journal</Title><JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue></Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


def test_pubmed_count_preview() -> None:
    def fetcher(url: str, timeout_seconds: float) -> bytes:
        assert "esearch.fcgi" in url
        assert "retmax=0" in url
        return ESEARCH_COUNT_RESPONSE

    preview = PubMedSearchService(fetcher=fetcher).preview_pubmed_count('"Obesity"[Mesh]')

    assert preview.success
    assert preview.result_count == 42
    assert preview.errors == ()


def test_pubmed_search_results_deduplicate_by_pmid() -> None:
    def fetcher(url: str, timeout_seconds: float) -> bytes:
        return ESEARCH_RESPONSE if "esearch.fcgi" in url else EFETCH_RESPONSE

    result = PubMedSearchService(fetcher=fetcher).search_pubmed('"Obesity"[Mesh]', max_results=3)

    assert result.success
    assert result.result_count == 3
    assert result.returned_count == 2
    assert result.pmids == ("111", "222")
    assert result.records[0].title == "Mock PubMed Trial One"
    assert result.records[0].url == "https://pubmed.ncbi.nlm.nih.gov/111/"
    assert result.dedup_summary["duplicate_pmids_removed"] == 1


def test_pubmed_search_failure_is_structured() -> None:
    def fetcher(url: str, timeout_seconds: float) -> bytes:
        raise TimeoutError("NCBI rate limit")

    result = PubMedSearchService(fetcher=fetcher).search_pubmed('"Obesity"[Mesh]', max_results=3)

    assert not result.success
    assert result.returned_count == 0
    assert result.errors[0]["code"] == "pubmed_search_failed"
    assert result.errors[0]["message"] == "NCBI rate limit"
