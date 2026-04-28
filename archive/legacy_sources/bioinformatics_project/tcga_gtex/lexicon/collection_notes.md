# English Lexicon v1

## Purpose

This English lexicon is the structured middle layer between future Chinese directory-style search and native TCGA/GDC or GTEx field-level retrieval. It is intended to support searchable, filterable, and displayable controlled vocabulary terms that can later map to database-native entities, fields, and field values.

## Why there are two layers

The lexicon is split into two generated outputs:

- `english_core_terms_full.csv`
  This is the backend-oriented foundation. It contains the full set of core structured English terms that we want to preserve for mapping, routing, and source-specific field dispatch.

- `english_ui_terms_curated.csv`
  This is the frontend-oriented layer. It is derived from the full lexicon and only keeps high-value navigation and search-hint terms that fit directory-style Chinese retrieval pages.

Above those two English term layers, the module now also keeps a database-agnostic concept layer:

- `concept_catalog.csv`
  This is the shared concept inventory for disease, tissue, sample type, analysis resource, access, and database-entity concepts.

- `concept_source_mappings.csv`
  This is the adaptation layer that maps shared concepts to source-specific TCGA/GDC filters, GTEx filters, and future GEO query-expansion terms.

## What “full” means in this project

The full lexicon is not a dump of every English token and it is not a free-text corpus. In this project, “full” means:

- full core structured vocabulary
- full high-value controlled fields
- full high-value enumerated values
- full TCGA project and cancer-related core terms
- full GTEx tissue and resource-oriented core terms

The full lexicon intentionally excludes:

- free-text summaries
- publication-style descriptions
- paper abstracts
- unstable miscellaneous text fragments
- low-value technical field paths that are not useful for retrieval, filtering, or presentation

## What “curated” means in this project

The curated lexicon is the high-value UI layer for:

- Chinese directory navigation
- Chinese retrieval suggestions
- frontend category browsing
- concise search-hint wording

It should include representative diseases, tissues, sample types, data resources, and access concepts, but it should avoid exposing internal implementation fields directly.

## Why concepts and source adapters are separated

TCGA/GDC and GTEx are primarily structured retrieval systems. They benefit from concept-to-field or concept-to-resource mappings such as:

- concept -> `project.project_id`
- concept -> `project.disease_type`
- concept -> `cases.primary_site`
- concept -> `tissue`
- concept -> `resource_name`

GEO is different. GEO is expected to rely much more on free-text query expansion, query phrasing, and ranking hints rather than on one stable set of database-native filter fields. Because of that, GEO should not share the same low-level execution logic as TCGA/GDC or GTEx.

The shared concept layer exists so that:

- TCGA/GDC can use structured field mappings
- GTEx can use tissue and resource mappings
- GEO can later use the same concepts for query expansion and ranking hints

without forcing all three sources into the same execution model.

## Current source strategy

The current v1 seed data is manually curated from stable, official-style, and reusable structures such as:

- TCGA/GDC project identifiers, project names, disease types, primary sites, sample classes, and common file filters
- GTEx tissues, common subregions, expression resource names, phenotype resources, and access/release concepts
- shared display concepts that are useful across sources

## Planned extension path

The next expansion path is:

1. Chinese core lexicon
   Chinese terms will map onto full English concept terms first, and then further onto structured field names and field values.

2. Directory-style Chinese retrieval pages
   Curated English terms will act as the source layer for category cards, browse lists, and search hints in a Chinese navigation UI.

3. GEO extension
   GEO will reuse the concept layer and aliases, but it will implement its own query-expansion and ranking adapter rather than reusing TCGA/GDC or GTEx structured filter execution.

## Out of scope for v1

The current lexicon still does not include:

- free-text summaries
- publication-style descriptions
- automatic crawling of all remote values
- live query dispatch to TCGA/GDC or GTEx adapters
- full GEO retrieval logic
