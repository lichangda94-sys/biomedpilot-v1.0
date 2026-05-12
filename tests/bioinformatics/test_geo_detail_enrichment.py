from __future__ import annotations

from pathlib import Path

from app.bioinformatics.retrieval.geo_detail_enrichment import (
    GEO_QUERY_URL,
    GeoDetailEnrichmentService,
    build_geo_detail_metadata,
)
from app.bioinformatics.services.organism_display import get_organism_display_name


GSE60235_SELF_SOFT = """^SERIES = GSE60235
!Series_title = Expression data measured by microarray of CD4+ T cells from healthy individuals stimulated with anti-CD3/CD28
!Series_status = Public on Aug 28 2014
!Series_submission_date = Aug 08 2014
!Series_last_update_date = Jul 26 2018
!Series_summary = This SubSeries in the ImmVar project investigates the response of selected genes in T cells from healthy human individuals to ascertain the impact of genetic or non-genetic variation on T cell activation parameters.
!Series_summary = We measured gene expression from resting and activated CD4+ T cells derived from the peripheral blood of healthy individuals. We activated the primary T cells with anti-CD3/CD28 beads alone or with IFNb or Th17 polarizing cytokines.
!Series_overall_design = We collected peripheral blood from each human donor. We isolated peripheral blood mononuclear cells by Ficoll, and negatively selected for CD4+ T cells using RosettaSep. We then either left cells unstimulated or stimulated them with beads conjugated with anti-CD3 and anti-CD28.
!Series_type = Expression profiling by array
!Series_contributor = Chun,,Ye
!Series_contributor = Ting,,Feng
!Series_contributor = Aviv,,Regev
!Series_contributor = Christophe,,Benoist
!Series_pubmed_id = 25214635
!Series_platform_id = GPL6244
!Series_sample_id = GSM1468447
!Series_sample_id = GSM1468448
!Series_sample_id = GSM1468449
!Series_sample_organism = Homo sapiens
!Series_supplementary_file = ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE60nnn/GSE60235/suppl/GSE60235_RAW.tar
!Series_relation = SubSeries of: GSE60236
!Series_relation = BioProject: https://www.ncbi.nlm.nih.gov/bioproject/PRJNA257802
"""

GSE60235_GSM_SOFT = """^SAMPLE = GSM1468447
!Sample_title = IGTB19 Unstimulated 4hr
!Sample_geo_accession = GSM1468447
!Sample_characteristics_ch1 = donor: IGTB19
!Sample_characteristics_ch1 = stimulation: unstimulated
^SAMPLE = GSM1468448
!Sample_title = IGTB231 anti-CD3/CD28 4hr
!Sample_geo_accession = GSM1468448
!Sample_characteristics_ch1 = donor: IGTB231
!Sample_characteristics_ch1 = stimulation: anti-CD3/CD28
"""

GSE60235_HTML = """
<html><body>
<table>
<tr><td>Platforms (1)</td><td><table><tr><td><a href="/geo/query/acc.cgi?acc=GPL6244">GPL6244</a></td><td>[HuGene-1_0-st] Affymetrix Human Gene 1.0 ST Array [transcript (gene) version]</td></tr></table></td></tr>
<tr><td>Samples (75)</td><td><table><tr><td><a href="/geo/query/acc.cgi?acc=GSM1468447">GSM1468447</a></td><td>IGTB19 Unstimulated 4hr</td></tr></table></td></tr>
</table>
<table>
<tr><td><strong>Supplementary file</strong></td><td><strong>Size</strong></td><td><strong>Download</strong></td><td><strong>File type/resource</strong></td></tr>
<tr><td>GSE60235_RAW.tar</td><td title="344688640">328.7 Mb</td><td><a href="/geo/download/?acc=GSE60235&amp;format=file">(http)</a></td><td>TAR (of CEL)</td></tr>
<tr><td class="message">Processed data included within Sample table</td></tr>
</table>
<p>Ye CJ, Feng T, Kwon HK, Raj T, et al. Science 2014; PMID: 25214635</p>
</body></html>
"""


def test_gse60235_detail_enrichment_parses_official_geo_metadata(tmp_path: Path) -> None:
    def fetch_text(url: str, params: dict[str, str]) -> str:
        assert url == GEO_QUERY_URL
        if params.get("targ") == "self" and params.get("form") == "text":
            return GSE60235_SELF_SOFT
        if params.get("targ") == "gsm" and params.get("form") == "text":
            return GSE60235_GSM_SOFT
        return GSE60235_HTML

    detail = GeoDetailEnrichmentService(fetch_text=fetch_text).enrich("GSE60235", project_root=tmp_path)

    assert detail.accession == "GSE60235"
    assert detail.organism == "Homo sapiens"
    assert "人类" in detail.organism_display_name
    assert "CD4+ T cells" in detail.title
    assert "ImmVar" in detail.summary
    assert "peripheral blood" in detail.overall_design
    assert detail.sample_count == 75
    assert any(platform.accession == "GPL6244" and "Affymetrix Human Gene 1.0 ST Array" in platform.title for platform in detail.platforms)
    assert any(sample.accession == "GSM1468447" for sample in detail.sample_preview)
    assert any(item.file_name == "GSE60235_RAW.tar" and item.file_type == "TAR (of CEL)" and item.file_size == "328.7 Mb" for item in detail.supplementary_files)
    assert detail.pmid == "25214635"
    assert detail.bioproject == "PRJNA257802"
    assert detail.superseries == "GSE60236"
    assert (tmp_path / "acquisition" / "geo_detail_cache" / "GSE60235_detail.json").exists()


def test_gse60235_detail_metadata_keeps_raw_organism_and_adds_display_name() -> None:
    detail = build_geo_detail_metadata("GSE60235", self_text=GSE60235_SELF_SOFT, gsm_text=GSE60235_GSM_SOFT, html_text=GSE60235_HTML)
    metadata = detail.to_candidate_metadata()

    assert metadata["organism"] == "Homo sapiens"
    assert metadata["organism_zh"] == "人类"
    assert metadata["organism_display_name"] == "人类（Homo sapiens）"
    assert get_organism_display_name("Unknown species") == "Unknown species（未映射中文名）"
