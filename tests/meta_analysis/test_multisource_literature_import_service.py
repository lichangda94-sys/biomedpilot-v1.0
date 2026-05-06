from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.literature_import_page import execute_multisource_literature_import, preview_literature_import_files
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.literature_library_service import LITERATURE_LIBRARY_SCHEMA_VERSION, NORMALIZED_LITERATURE_RECORD_SCHEMA_VERSION
from app.meta_analysis.services.multisource_literature_import_service import (
    MULTISOURCE_IMPORT_DIAGNOSTICS_SCHEMA_VERSION,
    MULTISOURCE_SUPPORTED_FORMATS,
    SOURCE_CNKI,
    SOURCE_COCHRANE_RIS,
    SOURCE_EMBASE_RIS,
    SOURCE_ENDNOTE,
    SOURCE_PUBMED_XML,
    SOURCE_WOS_PLAIN,
    SOURCE_WOS_TAB,
    SOURCE_ZOTERO,
    MultiSourceLiteratureImportService,
)


def test_multisource_import_parses_wos_plain_and_writes_normalized_library(tmp_path: Path) -> None:
    source = tmp_path / "wos.txt"
    source.write_text(
        """PT J
AU Smith J
AU Lee K
TI Obesity and thyroid cancer risk
SO Journal of WOS
PY 2024
DI 10.1000/wos.1
AB WOS abstract.
UT WOS:0001
ER
""",
        encoding="utf-8",
    )

    result = MultiSourceLiteratureImportService().import_file(
        tmp_path,
        source_path=source,
        source_format=SOURCE_WOS_PLAIN,
        source_database="Web of Science",
        search_strategy="TS=(obesity)",
    )
    library = json.loads(Path(result.library_records_path).read_text(encoding="utf-8"))
    record = library["records"][0]
    diagnostics = json.loads(Path(result.diagnostics_path).read_text(encoding="utf-8"))

    assert result.success
    assert result.imported_count == 1
    assert library["schema_version"] == LITERATURE_LIBRARY_SCHEMA_VERSION
    assert record["schema_version"] == NORMALIZED_LITERATURE_RECORD_SCHEMA_VERSION
    assert record["source_type"] == SOURCE_WOS_PLAIN
    assert record["source_query"] == "TS=(obesity)"
    assert record["doi"] == "10.1000/wos.1"
    assert record["screening_status"] == "not_started"
    assert record["provenance"]["online_execution"] is False
    assert diagnostics["schema_version"] == MULTISOURCE_IMPORT_DIAGNOSTICS_SCHEMA_VERSION


def test_multisource_import_parses_pubmed_xml_cnki_and_wos_tab(tmp_path: Path) -> None:
    xml = tmp_path / "pubmed.xml"
    xml.write_text(
        """<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><ArticleTitle>XML Trial</ArticleTitle><Abstract><AbstractText>XML abstract.</AbstractText></Abstract><Journal><Title>XML Journal</Title><JournalIssue><PubDate><Year>2025</Year></PubDate></JournalIssue></Journal><AuthorList><Author><ForeName>Alice</ForeName><LastName>Adams</LastName></Author></AuthorList></Article></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="doi">10.1000/xml.1</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>""",
        encoding="utf-8",
    )
    cnki = tmp_path / "cnki.txt"
    cnki.write_text("题名：中文甲状腺癌研究\n作者：张三; 李四\n来源：中国医学\n年：2024\n摘要：中文摘要\nDOI：10.1000/cnki.1\n", encoding="utf-8")
    tab = tmp_path / "wos.tsv"
    tab.write_text("Title\tAuthors\tSource Title\tPublication Year\tDOI\tAbstract\nTab Trial\tChen C; Wang W\tTab Journal\t2023\t10.1000/tab.1\tTab abstract\n", encoding="utf-8")

    service = MultiSourceLiteratureImportService()
    pubmed = service.import_file(tmp_path, source_path=xml, source_format=SOURCE_PUBMED_XML)
    cnki_result = service.import_file(tmp_path, source_path=cnki, source_format=SOURCE_CNKI)
    tab_result = service.import_file(tmp_path, source_path=tab, source_format=SOURCE_WOS_TAB)
    library = json.loads(Path(tab_result.library_records_path).read_text(encoding="utf-8"))
    source_types = {record["source_type"] for record in library["records"]}

    assert pubmed.imported_count == 1
    assert cnki_result.imported_count == 1
    assert tab_result.imported_count == 1
    assert {SOURCE_PUBMED_XML, SOURCE_CNKI, SOURCE_WOS_TAB} <= source_types
    assert len(library["records"]) == 3


def test_multisource_import_parses_ris_profiles_for_zotero_endnote_embase_cochrane(tmp_path: Path) -> None:
    ris = tmp_path / "records.ris"
    ris.write_text(
        """TY  - JOUR
ID  - RIS-001
TI  - RIS profile title
AU  - Adams, Alice
JO  - RIS Journal
PY  - 2022
DO  - 10.1000/ris.1
AB  - RIS abstract.
ER  -
""",
        encoding="utf-8",
    )
    service = MultiSourceLiteratureImportService()
    for source_format in (SOURCE_ZOTERO, SOURCE_ENDNOTE, SOURCE_EMBASE_RIS, SOURCE_COCHRANE_RIS):
        project_dir = tmp_path / source_format
        result = service.import_file(project_dir, source_path=ris, source_format=source_format)
        library = json.loads(Path(result.library_records_path).read_text(encoding="utf-8"))
        assert result.success
        assert library["records"][0]["source_type"] == source_format
        assert library["records"][0]["raw_extra"]


def test_multisource_import_missing_fields_do_not_crash_and_do_not_advance_prisma(tmp_path: Path) -> None:
    sparse = tmp_path / "sparse.csv"
    sparse.write_text("title,authors\nSparse title,\n", encoding="utf-8")

    result = MultiSourceLiteratureImportService().import_file(tmp_path, source_path=sparse, source_format="csv")
    diagnostics = json.loads(Path(result.diagnostics_path).read_text(encoding="utf-8"))
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)

    assert result.success
    assert diagnostics["warning_counts"]["缺少 DOI"] == 1
    assert diagnostics["warning_counts"]["缺少 PMID"] == 1
    assert diagnostics["warning_counts"]["缺少摘要"] == 1
    assert diagnostics["warning_counts"]["缺少年份"] == 1
    assert diagnostics["warning_counts"]["作者字段不完整"] == 1
    assert not (tmp_path / "screening").exists()
    assert prisma.records_screened == 0
    assert prisma.studies_included == 0


def test_multisource_import_page_preview_and_helper_support_new_formats(tmp_path: Path) -> None:
    cnki = tmp_path / "cnki.txt"
    cnki.write_text("题名：中文研究\n作者：张三\n来源：中文期刊\n年：2024\n", encoding="utf-8")

    state = preview_literature_import_files((str(cnki),), import_format="auto")
    result = execute_multisource_literature_import(project_dir=tmp_path / "project", source_path=str(cnki), source_format="auto")

    assert "cnki_export" in MULTISOURCE_SUPPORTED_FORMATS
    assert state.previews[0].detected_format == SOURCE_CNKI
    assert state.previews[0].supported is True
    assert result.success
    assert result.source_format == SOURCE_CNKI
