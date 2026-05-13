# Medical Terms License Attribution

BioMedPilot uses a shared medical term lookup layer. The default package includes only curated `zh_term_overrides.json`, `mini_medical_terms_index.json`, this metadata file, and attribution text. A full `medical_terms_index.sqlite` may be generated separately as an optional enhancement resource.

## MONDO

MONDO is planned as the primary disease vocabulary for optional full-index builds. MONDO content is available under CC BY 4.0. When included in a generated full index, attribution should identify MONDO and its release/version from the generated `source_metadata.json`.

## DOID

The Disease Ontology (DOID) is planned as a disease fallback vocabulary for optional full-index builds. DOID is available under CC0 1.0.

## NCIt

The NCI Thesaurus (NCIt) is planned for oncology terminology in optional full-index builds. NCIt content is available under CC BY 4.0. When included, attribution should identify the National Cancer Institute Thesaurus and the processed release/version.

## MeSH / NLM

Medical Subject Headings (MeSH) are produced by the U.S. National Library of Medicine. If MeSH terms are used in a generated full index, acknowledge NLM as the source. Use of MeSH does not imply endorsement by NLM, NIH, or the U.S. Government.

## EFO

The Experimental Factor Ontology (EFO) is planned for experiment-variable and data-resource annotations in optional full-index builds. EFO is available under the Apache License 2.0.

## UMLS / SNOMED CT

UMLS and SNOMED CT are not included by default and are not part of the packaged Stage 2 index because they have separate access and redistribution requirements.
