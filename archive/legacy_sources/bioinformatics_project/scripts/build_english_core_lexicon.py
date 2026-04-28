"""Build the English lexicon CSV resources for the TCGA/GTEx module."""

from __future__ import annotations

import csv
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tcga_gtex.config_rules import get_default_rule_service

FULL_TERM_HEADERS = [
    "term_id",
    "source",
    "bucket",
    "term_en",
    "term_type",
    "parent_term",
    "field_name",
    "field_value",
    "entity_scope",
    "access_scope",
    "display_label_en",
    "notes",
    "priority",
    "is_active",
]

CURATED_TERM_HEADERS = [
    "ui_term_id",
    "source",
    "category",
    "title_en",
    "display_label_en",
    "linked_term_ids",
    "default_priority",
    "recommended_for_navigation",
    "recommended_for_search_hint",
    "notes",
    "is_active",
]

ALIAS_HEADERS = [
    "alias_id",
    "term_id",
    "alias_en",
    "alias_kind",
    "priority",
]

CONCEPT_HEADERS = [
    "concept_id",
    "concept_en",
    "concept_category",
    "parent_concept_id",
    "synonyms_en",
    "notes",
]

CONCEPT_SOURCE_MAPPING_HEADERS = [
    "mapping_id",
    "concept_id",
    "source",
    "rule_kind",
    "target_field",
    "target_value",
    "target_term_id",
    "notes",
    "is_active",
]

CHINESE_CONCEPT_TERM_HEADERS = [
    "zh_term_id",
    "concept_id",
    "term_zh",
    "category_zh",
    "alias_type",
    "priority",
    "display_label_zh",
    "notes",
    "is_active",
]

# Backward-compatible alias kept for older callers/tests.
TERM_HEADERS = FULL_TERM_HEADERS

_RULE_SERVICE = get_default_rule_service()
_BUILDER_INPUTS = _RULE_SERVICE.load_lexicon_builder_inputs()

TCGA_PROJECTS = _BUILDER_INPUTS["tcga_projects"]
GTEX_TISSUE_CATALOG = _BUILDER_INPUTS["gtex_tissue_catalog"]
TCGA_SAMPLE_TYPE_VALUES = _BUILDER_INPUTS["tcga_sample_type_values"]
TCGA_TISSUE_TYPE_VALUES = _BUILDER_INPUTS["tcga_tissue_type_values"]
TCGA_TUMOR_DESCRIPTOR_VALUES = _BUILDER_INPUTS["tcga_tumor_descriptor_values"]
TCGA_DATA_CATEGORY_VALUES = _BUILDER_INPUTS["tcga_data_category_values"]
TCGA_DATA_TYPE_VALUES = _BUILDER_INPUTS["tcga_data_type_values"]
TCGA_EXPERIMENTAL_STRATEGY_VALUES = _BUILDER_INPUTS["tcga_experimental_strategy_values"]
TCGA_WORKFLOW_TYPE_VALUES = _BUILDER_INPUTS["tcga_workflow_type_values"]
UI_EXCLUDED_FIELD_NAMES = set(_BUILDER_INPUTS["ui_excluded_field_names"])


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def make_term(
    *,
    term_id: str,
    source: str,
    bucket: str,
    term_en: str,
    term_type: str,
    parent_term: str = "",
    field_name: str = "",
    field_value: str = "",
    entity_scope: str = "",
    access_scope: str = "unknown",
    display_label_en: str = "",
    notes: str = "",
    priority: int = 100,
    is_active: str = "true",
) -> dict[str, str]:
    return {
        "term_id": term_id,
        "source": source,
        "bucket": bucket,
        "term_en": term_en,
        "term_type": term_type,
        "parent_term": parent_term,
        "field_name": field_name,
        "field_value": field_value,
        "entity_scope": entity_scope,
        "access_scope": access_scope,
        "display_label_en": display_label_en or term_en,
        "notes": notes,
        "priority": str(priority),
        "is_active": is_active,
    }


def make_concept(
    *,
    concept_id: str,
    concept_en: str,
    concept_category: str,
    parent_concept_id: str = "",
    synonyms_en: list[str] | None = None,
    notes: str = "",
) -> dict[str, str]:
    return {
        "concept_id": concept_id,
        "concept_en": concept_en,
        "concept_category": concept_category,
        "parent_concept_id": parent_concept_id,
        "synonyms_en": "|".join(synonyms_en or []),
        "notes": notes,
    }


def make_concept_mapping(
    *,
    mapping_id: str,
    concept_id: str,
    source: str,
    rule_kind: str,
    target_field: str = "",
    target_value: str = "",
    target_term_id: str = "",
    notes: str = "",
    is_active: str = "true",
) -> dict[str, str]:
    return {
        "mapping_id": mapping_id,
        "concept_id": concept_id,
        "source": source,
        "rule_kind": rule_kind,
        "target_field": target_field,
        "target_value": target_value,
        "target_term_id": target_term_id,
        "notes": notes,
        "is_active": is_active,
    }


def make_chinese_term(
    *,
    zh_term_id: str,
    concept_id: str,
    term_zh: str,
    category_zh: str,
    alias_type: str,
    priority: int,
    display_label_zh: str,
    notes: str = "",
    is_active: str = "true",
) -> dict[str, str]:
    return {
        "zh_term_id": zh_term_id,
        "concept_id": concept_id,
        "term_zh": term_zh,
        "category_zh": category_zh,
        "alias_type": alias_type,
        "priority": str(priority),
        "display_label_zh": display_label_zh,
        "notes": notes,
        "is_active": is_active,
    }


def build_full_terms() -> list[dict[str, str]]:
    terms: list[dict[str, str]] = []
    priority = 10

    def add_term(**kwargs: str) -> None:
        nonlocal priority
        kwargs.setdefault("priority", priority)
        terms.append(make_term(**kwargs))
        priority += 10

    for term_en, entity_scope, source in [
        ("projects", "projects", "shared"),
        ("cases", "cases", "shared"),
        ("files", "files", "shared"),
        ("annotations", "annotations", "tcga_gdc"),
        ("tissue", "tissue", "gtex"),
        ("dataset", "dataset", "gtex"),
        ("sample attributes", "samples", "gtex"),
        ("subject phenotypes", "cases", "gtex"),
        ("gene expression", "dataset", "gtex"),
        ("eQTL", "dataset", "gtex"),
        ("sQTL", "dataset", "gtex"),
    ]:
        add_term(
            term_id=f"{source}.entity.{slugify(term_en)}",
            source=source,
            bucket="source_entities",
            term_en=term_en,
            term_type="entity",
            field_name=slugify(term_en) if source == "gtex" else term_en.rstrip("s") + "_id",
            entity_scope=entity_scope,
            access_scope="mixed" if source != "gtex" else "open",
            display_label_en=term_en.title() if term_en not in {"eQTL", "sQTL"} else term_en,
            notes="Core source entity used for structured browsing and retrieval.",
        )

    for term_en, field_name, display_label in [
        ("project_id", "project.project_id", "Project ID"),
        ("name", "project.name", "Project Name"),
        ("disease_type", "project.disease_type", "Disease Type"),
        ("primary_site", "cases.primary_site", "Primary Site"),
        ("state", "files.state", "State"),
        ("sample_type", "cases.samples.sample_type", "Sample Type"),
        ("tissue_type", "cases.samples.tissue_type", "Tissue Type"),
        ("tumor_descriptor", "cases.samples.tumor_descriptor", "Tumor Descriptor"),
        ("data_category", "files.data_category", "Data Category"),
        ("data_type", "files.data_type", "Data Type"),
        ("experimental_strategy", "files.experimental_strategy", "Experimental Strategy"),
        ("workflow_type", "files.analysis.workflow_type", "Workflow Type"),
        ("access", "files.access", "Access"),
        ("access_level", "access", "Access Level"),
    ]:
        add_term(
            term_id=f"tcga_gdc.field.{slugify(term_en)}",
            source="tcga_gdc",
            bucket="disease_or_project_terms" if term_en in {"project_id", "name", "disease_type", "primary_site"} else ("access_and_mode_terms" if term_en in {"state"} else "sample_terms" if term_en in {"sample_type", "tissue_type", "tumor_descriptor"} else "data_terms"),
            term_en=term_en,
            term_type="field",
            parent_term="shared.entity.projects" if term_en in {"project_id", "name", "disease_type"} else "shared.entity.cases" if term_en in {"primary_site"} else "shared.entity.files" if term_en in {"state", "data_category", "data_type", "experimental_strategy", "workflow_type", "access", "access_level"} else "shared.entity.cases",
            field_name=field_name,
            entity_scope="projects" if term_en in {"project_id", "name", "disease_type"} else "cases" if term_en == "primary_site" else "files" if term_en in {"state", "data_category", "data_type", "experimental_strategy", "workflow_type", "access", "access_level"} else "samples",
            access_scope="mixed",
            display_label_en=display_label,
            notes="Core structured TCGA/GDC field retained for mapping and filter routing.",
        )

    add_term(
        term_id="tcga_gdc.mode.released",
        source="tcga_gdc",
        bucket="access_and_mode_terms",
        term_en="released",
        term_type="value",
        field_name="files.state",
        field_value="released",
        entity_scope="files",
        access_scope="open",
        display_label_en="Released",
        notes="Common TCGA/GDC file lifecycle state.",
    )

    for term_en, field_value, access_scope, source in [
        ("open", "open", "open", "shared"),
        ("controlled", "controlled", "controlled", "shared"),
        ("open access", "open access", "open", "gtex"),
        ("protected", "protected", "protected", "gtex"),
        ("release", "release", "open", "gtex"),
    ]:
        add_term(
            term_id=f"{source}.access.{slugify(term_en)}",
            source=source,
            bucket="access_and_mode_terms",
            term_en=term_en,
            term_type="concept",
            field_name="access" if term_en != "release" else "release",
            field_value=field_value,
            entity_scope="dataset" if source == "gtex" else "files",
            access_scope=access_scope,
            display_label_en=term_en.title() if term_en not in {"open access"} else "Open Access",
            notes="Access or release concept kept for cross-source navigation.",
        )

    for value in TCGA_SAMPLE_TYPE_VALUES:
        access_scope = "controlled" if "Cancer" in value and "Normal" not in value else "open"
        add_term(
            term_id=f"tcga_gdc.sample_type.{slugify(value)}",
            source="tcga_gdc",
            bucket="sample_terms",
            term_en=value.lower(),
            term_type="value",
            parent_term="tcga_gdc.field.sample_type",
            field_name="cases.samples.sample_type",
            field_value=value,
            entity_scope="samples",
            access_scope=access_scope,
            display_label_en=value,
            notes="High-value TCGA/GDC sample type value.",
        )

    for value in TCGA_TISSUE_TYPE_VALUES:
        add_term(
            term_id=f"tcga_gdc.tissue_type.{slugify(value)}",
            source="tcga_gdc",
            bucket="sample_terms",
            term_en=value.lower(),
            term_type="value",
            parent_term="tcga_gdc.field.tissue_type",
            field_name="cases.samples.tissue_type",
            field_value=value,
            entity_scope="samples",
            access_scope="open",
            display_label_en=value,
            notes="High-value TCGA/GDC tissue type value.",
        )

    for value in TCGA_TUMOR_DESCRIPTOR_VALUES:
        add_term(
            term_id=f"tcga_gdc.tumor_descriptor.{slugify(value)}",
            source="tcga_gdc",
            bucket="sample_terms",
            term_en=value.lower(),
            term_type="value",
            parent_term="tcga_gdc.field.tumor_descriptor",
            field_name="cases.samples.tumor_descriptor",
            field_value=value,
            entity_scope="samples",
            access_scope="open",
            display_label_en=value,
            notes="High-value TCGA/GDC tumor descriptor value.",
        )

    for value in TCGA_DATA_CATEGORY_VALUES:
        add_term(
            term_id=f"tcga_gdc.data_category.{slugify(value)}",
            source="tcga_gdc",
            bucket="data_terms",
            term_en=value.lower(),
            term_type="value",
            parent_term="tcga_gdc.field.data_category",
            field_name="files.data_category",
            field_value=value,
            entity_scope="files",
            access_scope="mixed",
            display_label_en=value,
            notes="High-value TCGA/GDC file category.",
        )

    for value in TCGA_DATA_TYPE_VALUES:
        add_term(
            term_id=f"tcga_gdc.data_type.{slugify(value)}",
            source="tcga_gdc",
            bucket="data_terms",
            term_en=value if value[0].isupper() else value.lower(),
            term_type="value",
            parent_term="tcga_gdc.field.data_type",
            field_name="files.data_type",
            field_value=value,
            entity_scope="files",
            access_scope="controlled" if "Mutation" in value and "Clinical" not in value and "Biospecimen" not in value else "open",
            display_label_en=value,
            notes="High-value TCGA/GDC file type.",
        )

    for value in TCGA_EXPERIMENTAL_STRATEGY_VALUES:
        add_term(
            term_id=f"tcga_gdc.experimental_strategy.{slugify(value)}",
            source="tcga_gdc",
            bucket="data_terms",
            term_en=value,
            term_type="value",
            parent_term="tcga_gdc.field.experimental_strategy",
            field_name="files.experimental_strategy",
            field_value=value,
            entity_scope="files",
            access_scope="mixed",
            display_label_en=value,
            notes="High-value TCGA/GDC experimental strategy.",
        )

    for value in TCGA_WORKFLOW_TYPE_VALUES:
        add_term(
            term_id=f"tcga_gdc.workflow_type.{slugify(value)}",
            source="tcga_gdc",
            bucket="data_terms",
            term_en=value,
            term_type="value",
            parent_term="tcga_gdc.field.workflow_type",
            field_name="files.analysis.workflow_type",
            field_value=value,
            entity_scope="files",
            access_scope="mixed",
            display_label_en=value,
            notes="High-value TCGA/GDC workflow type.",
        )

    seen_disease_types: set[str] = set()
    seen_primary_sites: set[str] = set()
    for project in TCGA_PROJECTS:
        code_slug = slugify(project["project_id"])
        disease_slug = slugify(project["disease_type"])
        site_slug = slugify(project["primary_site"])

        add_term(
            term_id=f"tcga_gdc.project.{code_slug}",
            source="tcga_gdc",
            bucket="disease_or_project_terms",
            term_en=project["project_id"],
            term_type="value",
            parent_term="tcga_gdc.field.project_id",
            field_name="project.project_id",
            field_value=project["project_id"],
            entity_scope="projects",
            access_scope="open",
            display_label_en=project["project_id"],
            notes=f"TCGA project code for {project['name']}.",
        )

        add_term(
            term_id=f"tcga_gdc.project_name.{code_slug}",
            source="tcga_gdc",
            bucket="disease_or_project_terms",
            term_en=project["name"],
            term_type="value",
            parent_term=f"tcga_gdc.project.{code_slug}",
            field_name="project.name",
            field_value=project["name"],
            entity_scope="projects",
            access_scope="open",
            display_label_en=project["name"],
            notes=f"Official-style project name for {project['project_id']}.",
        )

        if project["disease_type"] not in seen_disease_types:
            add_term(
                term_id=f"tcga_gdc.disease_type.{disease_slug}",
                source="tcga_gdc",
                bucket="disease_or_project_terms",
                term_en=project["disease_type"].lower(),
                term_type="value",
                parent_term="tcga_gdc.field.disease_type",
                field_name="project.disease_type",
                field_value=project["disease_type"],
                entity_scope="projects",
                access_scope="open",
                display_label_en=project["disease_type"],
                notes="TCGA/GDC disease type value derived from the TCGA project catalog.",
            )
            seen_disease_types.add(project["disease_type"])

        if project["primary_site"] not in seen_primary_sites:
            add_term(
                term_id=f"tcga_gdc.primary_site.{site_slug}",
                source="tcga_gdc",
                bucket="disease_or_project_terms",
                term_en=project["primary_site"].lower(),
                term_type="value",
                parent_term="tcga_gdc.field.primary_site",
                field_name="cases.primary_site",
                field_value=project["primary_site"],
                entity_scope="cases",
                access_scope="open",
                display_label_en=project["primary_site"],
                notes="TCGA/GDC primary site value derived from the TCGA project catalog.",
            )
            seen_primary_sites.add(project["primary_site"])

    for field_name, display_label, entity_scope in [
        ("tissue", "Tissue", "samples"),
        ("subregion", "Subregion", "samples"),
        ("sex", "Sex", "samples"),
        ("age", "Age", "samples"),
        ("release", "Release", "dataset"),
    ]:
        add_term(
            term_id=f"gtex.field.{slugify(field_name)}",
            source="gtex",
            bucket="sample_terms" if field_name in {"tissue", "subregion", "sex", "age"} else "data_terms",
            term_en=field_name,
            term_type="field",
            parent_term="gtex.entity.tissue" if field_name in {"tissue", "subregion"} else "gtex.entity.subject_phenotypes" if field_name in {"sex", "age"} else "gtex.entity.dataset",
            field_name=field_name,
            entity_scope=entity_scope,
            access_scope="open",
            display_label_en=display_label,
            notes="Core GTEx field preserved for mapping and routing.",
        )

    for tissue_entry in GTEX_TISSUE_CATALOG:
        tissue = tissue_entry["tissue"]
        add_term(
            term_id=f"gtex.tissue.{slugify(tissue)}",
            source="gtex",
            bucket="sample_terms",
            term_en=tissue.lower(),
            term_type="value",
            parent_term="gtex.field.tissue",
            field_name="tissue",
            field_value=tissue,
            entity_scope="samples",
            access_scope="open",
            display_label_en=tissue,
            notes="GTEx major tissue term.",
        )
        for subregion in tissue_entry["subregions"]:
            add_term(
                term_id=f"gtex.subregion.{slugify(tissue)}_{slugify(subregion)}",
                source="gtex",
                bucket="sample_terms",
                term_en=subregion.lower(),
                term_type="value",
                parent_term=f"gtex.tissue.{slugify(tissue)}",
                field_name="subregion",
                field_value=subregion,
                entity_scope="samples",
                access_scope="open",
                display_label_en=subregion,
                notes=f"GTEx subregion value for {tissue}.",
            )

    for value in ["male", "female", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79"]:
        add_term(
            term_id=f"gtex.sample_attribute.{slugify(value)}",
            source="gtex",
            bucket="sample_terms",
            term_en=value,
            term_type="value",
            parent_term="gtex.field.sex" if value in {"male", "female"} else "gtex.field.age",
            field_name="sex" if value in {"male", "female"} else "age",
            field_value=value,
            entity_scope="samples",
            access_scope="open",
            display_label_en=value.title() if "-" not in value else value,
            notes="Common GTEx phenotype filter value.",
        )

    for value, field_name, parent_term, term_type in [
        ("read count", "expression_unit", "gtex.entity.gene_expression", "display"),
        ("TPM", "expression_unit", "gtex.entity.gene_expression", "display"),
        ("sample attributes", "resource_name", "gtex.entity.sample_attributes", "display"),
        ("subject phenotypes", "resource_name", "gtex.entity.subject_phenotypes", "display"),
        ("gene expression", "resource_name", "gtex.entity.gene_expression", "display"),
        ("eQTL", "resource_name", "gtex.entity.eqtl", "display"),
        ("sQTL", "resource_name", "gtex.entity.sqtl", "display"),
    ]:
        add_term(
            term_id=f"gtex.resource.{slugify(value)}",
            source="gtex",
            bucket="data_terms",
            term_en=value,
            term_type=term_type,
            parent_term=parent_term,
            field_name=field_name,
            field_value=value,
            entity_scope="dataset",
            access_scope="open",
            display_label_en=value if value in {"eQTL", "sQTL", "TPM"} else value.title(),
            notes="Core GTEx analysis or metadata resource.",
        )

    for value in ["clinical", "biospecimen", "mutation", "copy number", "normal tissue", "tumor", "primary tumor"]:
        add_term(
            term_id=f"shared.display.{slugify(value)}",
            source="shared",
            bucket="display_terms",
            term_en=value,
            term_type="display",
            field_name="display_category",
            field_value=value,
            entity_scope="files" if value in {"clinical", "biospecimen", "mutation", "copy number"} else "samples",
            access_scope="controlled" if value == "mutation" else "open",
            display_label_en=value.title(),
            notes="Shared display concept for cross-source navigation.",
        )

    return terms


def build_concept_catalog(full_terms: list[dict[str, str]]) -> list[dict[str, str]]:
    concepts: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    def add_concept(**kwargs: str | list[str]) -> None:
        concept = make_concept(**kwargs)
        if concept["concept_id"] in seen_ids:
            return
        concepts.append(concept)
        seen_ids.add(concept["concept_id"])

    for concept_id, concept_en, concept_category, synonyms, notes in [
        ("database_entity.projects", "projects", "database_entity", [], "Database-agnostic projects collection concept."),
        ("database_entity.cases", "cases", "database_entity", [], "Database-agnostic cases collection concept."),
        ("database_entity.files", "files", "database_entity", [], "Database-agnostic files collection concept."),
        ("database_entity.annotations", "annotations", "database_entity", [], "Database-agnostic annotations collection concept."),
        ("database_entity.dataset", "dataset", "database_entity", [], "Database-agnostic dataset collection concept."),
        ("analysis_resource.gene_expression", "gene expression", "analysis_resource", ["expression profiling"], "Cross-source expression concept."),
        ("analysis_resource.clinical", "clinical", "analysis_resource", ["clinical metadata"], "Clinical metadata concept."),
        ("analysis_resource.biospecimen", "biospecimen", "analysis_resource", ["biospecimen metadata"], "Biospecimen metadata concept."),
        ("analysis_resource.mutation", "mutation", "analysis_resource", ["somatic mutation"], "Mutation-oriented resource concept."),
        ("analysis_resource.copy_number", "copy number", "analysis_resource", ["cnv", "copy number variation"], "Copy-number resource concept."),
        ("analysis_resource.read_count", "read count", "analysis_resource", ["counts"], "Read-count expression unit concept."),
        ("analysis_resource.tpm", "TPM", "analysis_resource", ["transcripts per million", "tpm"], "TPM expression unit concept."),
        ("analysis_resource.sample_attributes", "sample attributes", "analysis_resource", ["sample metadata"], "GTEx sample metadata concept."),
        ("analysis_resource.subject_phenotypes", "subject phenotypes", "analysis_resource", ["subject metadata"], "GTEx subject metadata concept."),
        ("analysis_resource.eqtl", "eQTL", "analysis_resource", ["eqtl"], "Expression QTL concept."),
        ("analysis_resource.sqtl", "sQTL", "analysis_resource", ["sqtl"], "Splicing QTL concept."),
        ("sample_type.primary_tumor", "primary tumor", "sample_type", ["tumor"], "Primary tumor sample concept."),
        ("sample_type.solid_tissue_normal", "solid tissue normal", "sample_type", ["normal tissue"], "Adjacent normal solid tissue concept."),
        ("sample_type.metastatic", "metastatic", "sample_type", [], "Metastatic sample concept."),
        ("sample_type.recurrent_tumor", "recurrent tumor", "sample_type", [], "Recurrent tumor sample concept."),
        ("sample_type.tumor", "tumor", "sample_type", [], "Broad tumor sample concept."),
        ("sample_type.normal", "normal tissue", "sample_type", ["normal"], "Broad normal tissue concept."),
        ("sample_type.tumor_tissue", "tumor tissue", "sample_type", ["tumor sample"], "Umbrella tumor tissue concept for Chinese and GEO reuse."),
        ("access.open", "open", "access", ["open access"], "Broad public-access concept."),
        ("access.controlled", "controlled", "access", [], "Controlled-access concept."),
        ("access.protected", "protected", "access", [], "Protected-access concept."),
        ("access.release", "release", "access", ["released"], "Release-state or release-version concept."),
        ("disease.thyroid_cancer", "thyroid cancer", "disease", ["thyroid carcinoma"], "Broad thyroid cancer concept for cross-source reuse."),
        ("disease.papillary_thyroid_carcinoma", "papillary thyroid carcinoma", "disease", ["ptc"], "More specific thyroid subtype reserved for future GEO expansion."),
        ("disease.cervical_cancer", "cervical cancer", "disease", ["cervical squamous cell carcinoma and endocervical adenocarcinoma"], "Umbrella cervical cancer concept."),
        ("disease.endometrial_cancer", "endometrial cancer", "disease", ["uterine corpus endometrial carcinoma"], "Umbrella endometrial cancer concept."),
        ("disease.bladder_cancer", "bladder cancer", "disease", ["bladder urothelial carcinoma"], "Umbrella bladder cancer concept."),
        ("disease.breast_cancer", "breast cancer", "disease", ["breast invasive carcinoma"], "Umbrella breast cancer concept."),
        ("disease.hepatocellular_carcinoma", "hepatocellular carcinoma", "disease", ["hcc", "liver hepatocellular carcinoma"], "Umbrella hepatocellular carcinoma concept."),
        ("disease.colorectal_cancer", "colorectal cancer", "disease", ["colon adenocarcinoma", "rectum adenocarcinoma"], "Umbrella colorectal cancer concept."),
        ("disease.gastric_cancer", "gastric cancer", "disease", ["stomach adenocarcinoma"], "Umbrella gastric cancer concept."),
        ("disease.prostate_cancer", "prostate cancer", "disease", ["prostate adenocarcinoma"], "Umbrella prostate cancer concept."),
        ("disease.pancreatic_cancer", "pancreatic cancer", "disease", ["pancreatic adenocarcinoma"], "Umbrella pancreatic cancer concept."),
        ("disease.ovarian_cancer", "ovarian cancer", "disease", ["ovarian serous cystadenocarcinoma"], "Umbrella ovarian cancer concept."),
        ("disease.glioblastoma", "glioblastoma", "disease", ["glioblastoma multiforme", "gbm"], "Umbrella glioblastoma concept."),
        ("disease.lower_grade_glioma", "lower grade glioma", "disease", ["brain lower grade glioma", "lgg"], "Umbrella lower-grade glioma concept."),
        ("disease.melanoma", "melanoma", "disease", ["skin cutaneous melanoma"], "Umbrella melanoma concept."),
        ("disease.leukemia", "leukemia", "disease", ["acute myeloid leukemia"], "Umbrella leukemia concept."),
        ("disease.lymphoma", "lymphoma", "disease", ["lymphoid neoplasm diffuse large b-cell lymphoma"], "Umbrella lymphoma concept."),
        ("disease.lymphoid_malignancy", "lymphoid malignancy", "disease", ["lymphoma", "lymphoid neoplasm"], "Umbrella lymphoid malignancy concept."),
        ("disease.lung_cancer", "lung cancer", "disease", ["lung adenocarcinoma", "lung squamous cell carcinoma"], "Umbrella lung cancer concept."),
        ("disease.kidney_cancer", "kidney cancer", "disease", ["kidney chromophobe", "kidney renal clear cell carcinoma", "kidney renal papillary cell carcinoma"], "Umbrella kidney cancer concept."),
        ("disease.brain_tumor", "brain tumor", "disease", ["glioblastoma", "lower grade glioma"], "Umbrella brain tumor concept."),
        ("disease.gynecologic_cancer", "gynecologic cancer", "disease", ["cervical cancer", "endometrial cancer", "ovarian cancer"], "Umbrella gynecologic cancer concept."),
        ("disease.genitourinary_cancer", "genitourinary cancer", "disease", ["bladder cancer", "kidney cancer", "prostate cancer"], "Umbrella genitourinary cancer concept."),
        ("disease.digestive_system_tumor", "digestive system tumor", "disease", ["colorectal cancer", "gastric cancer", "pancreatic cancer", "hepatocellular carcinoma", "cholangiocarcinoma", "esophageal carcinoma"], "Umbrella digestive system tumor concept."),
        ("disease.head_and_neck_tumor", "head and neck tumor", "disease", ["head and neck squamous cell carcinoma"], "Umbrella head and neck tumor concept."),
        ("disease.hematologic_malignancy", "hematologic malignancy", "disease", ["leukemia", "lymphoma"], "Umbrella hematologic malignancy concept."),
        ("disease.endocrine_tumor", "endocrine tumor", "disease", ["thyroid cancer", "adrenocortical carcinoma", "pheochromocytoma and paraganglioma"], "Umbrella endocrine tumor concept."),
        ("disease.neuroendocrine_tumor", "neuroendocrine tumor", "disease", ["pheochromocytoma and paraganglioma"], "Umbrella neuroendocrine tumor concept."),
        ("tissue.thyroid", "thyroid tissue", "tissue", ["thyroid gland", "thyroid"], "Broad thyroid tissue concept for tumor and normal references."),
        ("tissue.colorectal", "colorectal tissue", "tissue", ["colon", "rectum", "colorectal"], "Umbrella colorectal tissue concept."),
        ("tissue.blood_bone_marrow", "blood / bone marrow", "tissue", ["blood", "bone marrow"], "Umbrella blood and bone marrow tissue concept."),
        ("tissue.lymphoid_tissue", "lymphoid tissue", "tissue", ["lymph node", "lymphoid tissue"], "Umbrella lymphoid tissue concept."),
        ("tissue.salivary_gland", "salivary gland", "tissue", ["minor salivary gland"], "Umbrella salivary gland concept."),
    ]:
        add_concept(
            concept_id=concept_id,
            concept_en=concept_en,
            concept_category=concept_category,
            synonyms_en=synonyms,
            notes=notes,
        )

    disease_terms = sorted(
        {
            term["field_value"]
            for term in full_terms
            if term["source"] == "tcga_gdc" and term["field_name"] == "project.disease_type" and term["term_type"] == "value"
        }
    )
    for disease in disease_terms:
        add_concept(
            concept_id=f"disease.{slugify(disease)}",
            concept_en=disease.lower(),
            concept_category="disease",
            synonyms_en=[disease],
            notes="Disease concept derived from the TCGA project catalog.",
        )

    tissue_terms = sorted(
        {
            term["field_value"]
            for term in full_terms
            if term["field_name"] in {"cases.primary_site", "tissue"} and term["term_type"] == "value"
        }
    )
    for tissue in tissue_terms:
        normalized = tissue
        if tissue == "Thyroid Gland":
            continue
        add_concept(
            concept_id=f"tissue.{slugify(normalized)}",
            concept_en=normalized.lower(),
            concept_category="tissue",
            synonyms_en=[normalized],
            notes="Tissue concept derived from source-specific structured tissue terms.",
        )

    return sorted(concepts, key=lambda row: (row["concept_category"], row["concept_en"].lower(), row["concept_id"]))


def build_concept_source_mappings(
    concepts: list[dict[str, str]],
    full_terms: list[dict[str, str]],
) -> list[dict[str, str]]:
    term_by_id = {term["term_id"]: term for term in full_terms}
    mappings: list[dict[str, str]] = []
    seen_mapping_ids: set[str] = set()

    def add_mapping(**kwargs: str) -> None:
        mapping = make_concept_mapping(**kwargs)
        if mapping["mapping_id"] in seen_mapping_ids:
            return
        mappings.append(mapping)
        seen_mapping_ids.add(mapping["mapping_id"])

    def add_term_mapping(concept_id: str, source: str, term_id: str, notes: str) -> None:
        term = term_by_id.get(term_id)
        if term is None:
            return
        add_mapping(
            mapping_id=f"map.{slugify(concept_id)}.{source}.{slugify(term_id)}",
            concept_id=concept_id,
            source=source,
            rule_kind="structured_filter" if source in {"tcga_gdc", "gtex"} else "query_term",
            target_field=term["field_name"],
            target_value=term["field_value"] or term["display_label_en"],
            target_term_id=term_id,
            notes=notes,
        )

    for concept in concepts:
        concept_id = concept["concept_id"]
        concept_en = concept["concept_en"]
        synonyms = [token for token in concept["synonyms_en"].split("|") if token]

        if concept_id == "database_entity.projects":
            add_term_mapping(concept_id, "tcga_gdc", "shared.entity.projects", "Projects entity shared by structured sources.")
        elif concept_id == "database_entity.cases":
            add_term_mapping(concept_id, "tcga_gdc", "shared.entity.cases", "Cases entity shared by structured sources.")
        elif concept_id == "database_entity.files":
            add_term_mapping(concept_id, "tcga_gdc", "shared.entity.files", "Files entity shared by structured sources.")
        elif concept_id == "database_entity.annotations":
            add_term_mapping(concept_id, "tcga_gdc", "tcga_gdc.entity.annotations", "Annotations are currently TCGA/GDC-specific.")
        elif concept_id == "database_entity.dataset":
            add_term_mapping(concept_id, "gtex", "gtex.entity.dataset", "Dataset concept maps to GTEx dataset entity.")
        elif concept_id == "analysis_resource.gene_expression":
            for term_id in ["tcga_gdc.data_type.gene_expression_quantification", "gtex.resource.gene_expression", "shared.display.gene_expression"]:
                add_term_mapping(concept_id, "tcga_gdc" if term_id.startswith("tcga_gdc") or term_id.startswith("shared") else "gtex", term_id, "Gene-expression concept maps to source-specific expression resources.")
        elif concept_id == "analysis_resource.clinical":
            add_term_mapping(concept_id, "tcga_gdc", "tcga_gdc.data_type.clinical_supplement", "Clinical concept maps to TCGA/GDC clinical supplement.")
            add_term_mapping(concept_id, "tcga_gdc", "shared.display.clinical", "Clinical display concept supports UI routing.")
        elif concept_id == "analysis_resource.biospecimen":
            add_term_mapping(concept_id, "tcga_gdc", "tcga_gdc.data_type.biospecimen_supplement", "Biospecimen concept maps to TCGA/GDC biospecimen supplement.")
            add_term_mapping(concept_id, "tcga_gdc", "shared.display.biospecimen", "Biospecimen display concept supports UI routing.")
        elif concept_id == "analysis_resource.mutation":
            add_term_mapping(concept_id, "tcga_gdc", "tcga_gdc.data_type.masked_somatic_mutation", "Mutation concept maps to TCGA/GDC mutation files.")
            add_term_mapping(concept_id, "tcga_gdc", "shared.display.mutation", "Mutation display concept supports UI routing.")
        elif concept_id == "analysis_resource.copy_number":
            add_term_mapping(concept_id, "tcga_gdc", "shared.display.copy_number", "Copy-number concept is reserved through shared display mapping.")
        elif concept_id == "analysis_resource.read_count":
            add_term_mapping(concept_id, "gtex", "gtex.resource.read_count", "Read-count concept maps to GTEx expression-unit resource.")
        elif concept_id == "analysis_resource.tpm":
            add_term_mapping(concept_id, "gtex", "gtex.resource.tpm", "TPM concept maps to GTEx expression-unit resource.")
        elif concept_id == "analysis_resource.sample_attributes":
            add_term_mapping(concept_id, "gtex", "gtex.resource.sample_attributes", "GTEx sample metadata resource.")
        elif concept_id == "analysis_resource.subject_phenotypes":
            add_term_mapping(concept_id, "gtex", "gtex.resource.subject_phenotypes", "GTEx subject metadata resource.")
        elif concept_id == "analysis_resource.eqtl":
            add_term_mapping(concept_id, "gtex", "gtex.resource.eqtl", "GTEx eQTL resource.")
        elif concept_id == "analysis_resource.sqtl":
            add_term_mapping(concept_id, "gtex", "gtex.resource.sqtl", "GTEx sQTL resource.")
        elif concept_id == "sample_type.primary_tumor":
            add_term_mapping(concept_id, "tcga_gdc", "tcga_gdc.sample_type.primary_tumor", "Primary tumor concept maps to TCGA sample type.")
            add_term_mapping(concept_id, "tcga_gdc", "shared.display.primary_tumor", "Primary tumor display concept.")
        elif concept_id == "sample_type.solid_tissue_normal":
            add_term_mapping(concept_id, "tcga_gdc", "tcga_gdc.sample_type.solid_tissue_normal", "Solid tissue normal concept maps to TCGA sample type.")
        elif concept_id == "sample_type.metastatic":
            add_term_mapping(concept_id, "tcga_gdc", "tcga_gdc.sample_type.metastatic", "Metastatic concept maps to TCGA sample type.")
        elif concept_id == "sample_type.recurrent_tumor":
            add_term_mapping(concept_id, "tcga_gdc", "tcga_gdc.sample_type.recurrent_tumor", "Recurrent tumor concept maps to TCGA sample type.")
        elif concept_id == "sample_type.tumor":
            add_term_mapping(concept_id, "tcga_gdc", "shared.display.tumor", "Broad tumor concept maps to shared tumor display term.")
            add_term_mapping(concept_id, "tcga_gdc", "tcga_gdc.tissue_type.tumor", "Broad tumor concept maps to TCGA tissue type.")
        elif concept_id == "sample_type.normal":
            add_term_mapping(concept_id, "tcga_gdc", "shared.display.normal_tissue", "Broad normal concept maps to shared normal-tissue display term.")
            add_term_mapping(concept_id, "tcga_gdc", "tcga_gdc.tissue_type.normal", "Broad normal concept maps to TCGA tissue type.")
        elif concept_id == "sample_type.tumor_tissue":
            add_term_mapping(concept_id, "tcga_gdc", "shared.display.tumor", "Umbrella tumor-tissue concept maps to shared tumor display term.")
            add_term_mapping(concept_id, "tcga_gdc", "tcga_gdc.tissue_type.tumor", "Umbrella tumor-tissue concept maps to TCGA tissue type.")
        elif concept_id == "access.open":
            add_term_mapping(concept_id, "tcga_gdc", "shared.access.open", "Open-access concept for structured routing.")
            add_term_mapping(concept_id, "gtex", "gtex.access.open_access", "Open-access concept for GTEx routing.")
        elif concept_id == "access.controlled":
            add_term_mapping(concept_id, "tcga_gdc", "shared.access.controlled", "Controlled concept for TCGA/GDC routing.")
        elif concept_id == "access.protected":
            add_term_mapping(concept_id, "gtex", "gtex.access.protected", "Protected concept for GTEx routing.")
        elif concept_id == "access.release":
            add_term_mapping(concept_id, "tcga_gdc", "tcga_gdc.mode.released", "Released state concept for TCGA/GDC.")
            add_term_mapping(concept_id, "gtex", "gtex.access.release", "Release concept for GTEx.")
        elif concept_id == "disease.thyroid_cancer":
            for term_id in ["tcga_gdc.disease_type.thyroid_carcinoma", "tcga_gdc.project.tcga_thca", "tcga_gdc.primary_site.thyroid_gland"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Thyroid cancer concept maps to TCGA disease, project, and site terms.")
        elif concept_id == "disease.cervical_cancer":
            for term_id in ["tcga_gdc.disease_type.cervical_squamous_cell_carcinoma_and_endocervical_adenocarcinoma", "tcga_gdc.project.tcga_cesc", "tcga_gdc.primary_site.cervix_uteri"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Cervical cancer concept maps to CESC disease, project, and cervix site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.cervix_uteri", "Cervical cancer concept maps to GTEx cervix tissue reference.")
        elif concept_id == "disease.endometrial_cancer":
            for term_id in ["tcga_gdc.disease_type.uterine_corpus_endometrial_carcinoma", "tcga_gdc.project.tcga_ucec", "tcga_gdc.primary_site.uterus"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Endometrial cancer concept maps to UCEC disease, project, and uterus site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.uterus", "Endometrial cancer concept maps to GTEx uterus tissue reference.")
        elif concept_id == "disease.bladder_cancer":
            for term_id in ["tcga_gdc.disease_type.bladder_urothelial_carcinoma", "tcga_gdc.project.tcga_blca", "tcga_gdc.primary_site.bladder"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Bladder cancer concept maps to BLCA disease, project, and bladder site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.bladder", "Bladder cancer concept maps to GTEx bladder tissue reference.")
        elif concept_id == "disease.breast_cancer":
            for term_id in ["tcga_gdc.disease_type.breast_invasive_carcinoma", "tcga_gdc.project.tcga_brca", "tcga_gdc.primary_site.breast"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Breast cancer concept maps to BRCA disease, project, and primary site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.breast", "Breast cancer concept maps to GTEx breast tissue reference.")
        elif concept_id == "disease.hepatocellular_carcinoma":
            for term_id in ["tcga_gdc.disease_type.liver_hepatocellular_carcinoma", "tcga_gdc.project.tcga_lihc", "tcga_gdc.primary_site.liver"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Hepatocellular carcinoma concept maps to LIHC disease, project, and liver site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.liver", "Hepatocellular carcinoma concept maps to GTEx liver tissue reference.")
        elif concept_id == "disease.colorectal_cancer":
            for term_id in ["tcga_gdc.disease_type.colon_adenocarcinoma", "tcga_gdc.disease_type.rectum_adenocarcinoma", "tcga_gdc.project.tcga_coad", "tcga_gdc.project.tcga_read", "tcga_gdc.primary_site.colon", "tcga_gdc.primary_site.rectum"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Colorectal cancer concept maps to COAD/READ disease, project, and site terms.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.colon", "Colorectal cancer concept maps to GTEx colon tissue reference.")
        elif concept_id == "disease.gastric_cancer":
            for term_id in ["tcga_gdc.disease_type.stomach_adenocarcinoma", "tcga_gdc.project.tcga_stad", "tcga_gdc.primary_site.stomach"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Gastric cancer concept maps to STAD disease, project, and stomach site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.stomach", "Gastric cancer concept maps to GTEx stomach tissue reference.")
        elif concept_id == "disease.prostate_cancer":
            for term_id in ["tcga_gdc.disease_type.prostate_adenocarcinoma", "tcga_gdc.project.tcga_prad", "tcga_gdc.primary_site.prostate_gland"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Prostate cancer concept maps to PRAD disease, project, and site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.prostate", "Prostate cancer concept maps to GTEx prostate tissue reference.")
        elif concept_id == "disease.pancreatic_cancer":
            for term_id in ["tcga_gdc.disease_type.pancreatic_adenocarcinoma", "tcga_gdc.project.tcga_paad", "tcga_gdc.primary_site.pancreas"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Pancreatic cancer concept maps to PAAD disease, project, and pancreas site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.pancreas", "Pancreatic cancer concept maps to GTEx pancreas tissue reference.")
        elif concept_id == "disease.ovarian_cancer":
            for term_id in ["tcga_gdc.disease_type.ovarian_serous_cystadenocarcinoma", "tcga_gdc.project.tcga_ov", "tcga_gdc.primary_site.ovary"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Ovarian cancer concept maps to OV disease, project, and ovary site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.ovary", "Ovarian cancer concept maps to GTEx ovary tissue reference.")
        elif concept_id == "disease.glioblastoma":
            for term_id in ["tcga_gdc.disease_type.glioblastoma_multiforme", "tcga_gdc.project.tcga_gbm", "tcga_gdc.primary_site.brain"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Glioblastoma concept maps to GBM disease, project, and brain site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.brain", "Glioblastoma concept maps to GTEx brain tissue reference.")
        elif concept_id == "disease.lower_grade_glioma":
            for term_id in ["tcga_gdc.disease_type.brain_lower_grade_glioma", "tcga_gdc.project.tcga_lgg", "tcga_gdc.primary_site.brain"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Lower-grade glioma concept maps to LGG disease, project, and brain site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.brain", "Lower-grade glioma concept maps to GTEx brain tissue reference.")
        elif concept_id == "disease.melanoma":
            for term_id in ["tcga_gdc.disease_type.skin_cutaneous_melanoma", "tcga_gdc.project.tcga_skcm", "tcga_gdc.primary_site.skin"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Melanoma concept maps to SKCM disease, project, and skin site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.skin", "Melanoma concept maps to GTEx skin tissue reference.")
        elif concept_id == "disease.leukemia":
            for term_id in ["tcga_gdc.disease_type.acute_myeloid_leukemia", "tcga_gdc.project.tcga_laml", "tcga_gdc.primary_site.hematopoietic_and_reticuloendothelial_systems"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Leukemia concept maps to LAML disease, project, and hematopoietic site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.blood", "Leukemia concept maps to GTEx blood reference.")
        elif concept_id == "disease.lymphoma":
            for term_id in ["tcga_gdc.disease_type.lymphoid_neoplasm_diffuse_large_b_cell_lymphoma", "tcga_gdc.project.tcga_dlbc", "tcga_gdc.primary_site.hematopoietic_and_reticuloendothelial_systems"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Lymphoma concept maps to DLBC disease, project, and hematopoietic site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.spleen", "Lymphoma concept maps to GTEx spleen reference.")
        elif concept_id == "disease.lymphoid_malignancy":
            for term_id in ["tcga_gdc.project.tcga_dlbc", "tcga_gdc.primary_site.hematopoietic_and_reticuloendothelial_systems"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Lymphoid malignancy concept maps to DLBC and lymphoid-related primary site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.spleen", "Lymphoid malignancy concept maps to GTEx spleen reference.")
        elif concept_id == "disease.lung_cancer":
            for term_id in ["tcga_gdc.project.tcga_luad", "tcga_gdc.project.tcga_lusc", "tcga_gdc.primary_site.bronchus_and_lung"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Lung cancer concept maps to LUAD/LUSC and lung primary site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.lung", "Lung cancer concept maps to GTEx lung tissue reference.")
        elif concept_id == "disease.kidney_cancer":
            for term_id in ["tcga_gdc.project.tcga_kich", "tcga_gdc.project.tcga_kirc", "tcga_gdc.project.tcga_kirp", "tcga_gdc.primary_site.kidney"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Kidney cancer concept maps to KICH/KIRC/KIRP and kidney site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.kidney", "Kidney cancer concept maps to GTEx kidney tissue reference.")
        elif concept_id == "disease.brain_tumor":
            for term_id in ["tcga_gdc.project.tcga_gbm", "tcga_gdc.project.tcga_lgg", "tcga_gdc.primary_site.brain"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Brain tumor concept maps to GBM/LGG and brain primary site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.brain", "Brain tumor concept maps to GTEx brain tissue reference.")
        elif concept_id == "disease.gynecologic_cancer":
            for term_id in ["tcga_gdc.project.tcga_cesc", "tcga_gdc.project.tcga_ucec", "tcga_gdc.project.tcga_ov", "tcga_gdc.project.tcga_ucs", "tcga_gdc.primary_site.cervix_uteri", "tcga_gdc.primary_site.uterus", "tcga_gdc.primary_site.ovary"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Gynecologic cancer concept maps to major gynecologic TCGA projects and sites.")
            for term_id in ["gtex.tissue.cervix_uteri", "gtex.tissue.uterus", "gtex.tissue.ovary", "gtex.tissue.fallopian_tube", "gtex.tissue.vagina"]:
                add_term_mapping(concept_id, "gtex", term_id, "Gynecologic cancer concept maps to relevant GTEx reproductive tissues.")
        elif concept_id == "disease.genitourinary_cancer":
            for term_id in ["tcga_gdc.project.tcga_blca", "tcga_gdc.project.tcga_kich", "tcga_gdc.project.tcga_kirc", "tcga_gdc.project.tcga_kirp", "tcga_gdc.project.tcga_prad", "tcga_gdc.project.tcga_tgct", "tcga_gdc.primary_site.bladder", "tcga_gdc.primary_site.kidney", "tcga_gdc.primary_site.prostate_gland", "tcga_gdc.primary_site.testis"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Genitourinary cancer concept maps to GU TCGA projects and sites.")
            for term_id in ["gtex.tissue.bladder", "gtex.tissue.kidney", "gtex.tissue.prostate", "gtex.tissue.testis"]:
                add_term_mapping(concept_id, "gtex", term_id, "Genitourinary cancer concept maps to GU GTEx tissues.")
        elif concept_id == "disease.digestive_system_tumor":
            for term_id in ["tcga_gdc.project.tcga_coad", "tcga_gdc.project.tcga_read", "tcga_gdc.project.tcga_stad", "tcga_gdc.project.tcga_lihc", "tcga_gdc.project.tcga_paad", "tcga_gdc.project.tcga_esca", "tcga_gdc.project.tcga_chol", "tcga_gdc.primary_site.colon", "tcga_gdc.primary_site.rectum", "tcga_gdc.primary_site.stomach", "tcga_gdc.primary_site.liver", "tcga_gdc.primary_site.pancreas", "tcga_gdc.primary_site.esophagus", "tcga_gdc.primary_site.bile_duct"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Digestive system tumor concept maps to major digestive TCGA projects and sites.")
            for term_id in ["gtex.tissue.colon", "gtex.tissue.stomach", "gtex.tissue.liver", "gtex.tissue.pancreas", "gtex.tissue.esophagus", "gtex.tissue.small_intestine"]:
                add_term_mapping(concept_id, "gtex", term_id, "Digestive system tumor concept maps to digestive GTEx tissues.")
        elif concept_id == "disease.head_and_neck_tumor":
            for term_id in ["tcga_gdc.project.tcga_hnsc", "tcga_gdc.primary_site.head_and_neck"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Head and neck tumor concept maps to HNSC and head/neck site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.minor_salivary_gland", "Head and neck tumor concept maps to GTEx minor salivary gland reference.")
        elif concept_id == "disease.hematologic_malignancy":
            for term_id in ["tcga_gdc.project.tcga_laml", "tcga_gdc.project.tcga_dlbc", "tcga_gdc.primary_site.hematopoietic_and_reticuloendothelial_systems"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Hematologic malignancy concept maps to LAML/DLBC and hematopoietic site.")
            for term_id in ["gtex.tissue.blood", "gtex.tissue.spleen"]:
                add_term_mapping(concept_id, "gtex", term_id, "Hematologic malignancy concept maps to GTEx blood and spleen.")
        elif concept_id == "disease.endocrine_tumor":
            for term_id in ["tcga_gdc.project.tcga_thca", "tcga_gdc.project.tcga_acc", "tcga_gdc.project.tcga_pcpg", "tcga_gdc.primary_site.thyroid_gland", "tcga_gdc.primary_site.adrenal_gland"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Endocrine tumor concept maps to THCA/ACC/PCPG and endocrine sites.")
            for term_id in ["gtex.tissue.thyroid", "gtex.tissue.adrenal_gland", "gtex.tissue.pituitary"]:
                add_term_mapping(concept_id, "gtex", term_id, "Endocrine tumor concept maps to GTEx endocrine tissues.")
        elif concept_id == "disease.neuroendocrine_tumor":
            for term_id in ["tcga_gdc.project.tcga_pcpg", "tcga_gdc.primary_site.adrenal_gland"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Neuroendocrine tumor concept maps to PCPG and adrenal primary site.")
            for term_id in ["gtex.tissue.adrenal_gland", "gtex.tissue.pituitary"]:
                add_term_mapping(concept_id, "gtex", term_id, "Neuroendocrine tumor concept maps to adrenal and pituitary references.")
        elif concept_id == "disease.kidney_renal_clear_cell_carcinoma":
            for term_id in ["tcga_gdc.disease_type.kidney_renal_clear_cell_carcinoma", "tcga_gdc.project.tcga_kirc", "tcga_gdc.primary_site.kidney"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "KIRC-specific concept maps to TCGA disease, project, and kidney site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.kidney", "KIRC-specific concept maps to GTEx kidney tissue reference.")
        elif concept_id == "disease.kidney_renal_papillary_cell_carcinoma":
            for term_id in ["tcga_gdc.disease_type.kidney_renal_papillary_cell_carcinoma", "tcga_gdc.project.tcga_kirp", "tcga_gdc.primary_site.kidney"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "KIRP-specific concept maps to TCGA disease, project, and kidney site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.kidney", "KIRP-specific concept maps to GTEx kidney tissue reference.")
        elif concept_id == "disease.head_and_neck_squamous_cell_carcinoma":
            for term_id in ["tcga_gdc.disease_type.head_and_neck_squamous_cell_carcinoma", "tcga_gdc.project.tcga_hnsc", "tcga_gdc.primary_site.head_and_neck"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "HNSC-specific concept maps to TCGA disease, project, and head/neck site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.minor_salivary_gland", "HNSC-specific concept maps to GTEx minor salivary gland reference.")
        elif concept_id == "disease.esophageal_carcinoma":
            for term_id in ["tcga_gdc.disease_type.esophageal_carcinoma", "tcga_gdc.project.tcga_esca", "tcga_gdc.primary_site.esophagus"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "ESCA-specific concept maps to TCGA disease, project, and esophagus site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.esophagus", "ESCA-specific concept maps to GTEx esophagus tissue reference.")
        elif concept_id == "disease.mesothelioma":
            for term_id in ["tcga_gdc.disease_type.mesothelioma", "tcga_gdc.project.tcga_meso", "tcga_gdc.primary_site.pleura"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "Mesothelioma-specific concept maps to TCGA disease, project, and pleura site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.lung", "Mesothelioma concept uses GTEx lung as nearest normal tissue reference.")
        elif concept_id == "disease.testicular_germ_cell_tumors":
            for term_id in ["tcga_gdc.disease_type.testicular_germ_cell_tumors", "tcga_gdc.project.tcga_tgct", "tcga_gdc.primary_site.testis"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "TGCT-specific concept maps to TCGA disease, project, and testis site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.testis", "TGCT-specific concept maps to GTEx testis tissue reference.")
        elif concept_id == "disease.adrenocortical_carcinoma":
            for term_id in ["tcga_gdc.disease_type.adrenocortical_carcinoma", "tcga_gdc.project.tcga_acc", "tcga_gdc.primary_site.adrenal_gland"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "ACC-specific concept maps to TCGA disease, project, and adrenal site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.adrenal_gland", "ACC-specific concept maps to GTEx adrenal gland tissue reference.")
        elif concept_id == "disease.pheochromocytoma_and_paraganglioma":
            for term_id in ["tcga_gdc.disease_type.pheochromocytoma_and_paraganglioma", "tcga_gdc.project.tcga_pcpg", "tcga_gdc.primary_site.adrenal_gland"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "PCPG-specific concept maps to TCGA disease, project, and adrenal site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.adrenal_gland", "PCPG-specific concept maps to GTEx adrenal gland tissue reference.")
        elif concept_id == "disease.brain_lower_grade_glioma":
            for term_id in ["tcga_gdc.disease_type.brain_lower_grade_glioma", "tcga_gdc.project.tcga_lgg", "tcga_gdc.primary_site.brain"]:
                add_term_mapping(concept_id, "tcga_gdc", term_id, "LGG-specific concept maps to TCGA disease, project, and brain site.")
            add_term_mapping(concept_id, "gtex", "gtex.tissue.brain", "LGG-specific concept maps to GTEx brain tissue reference.")
        elif concept_id == "tissue.thyroid":
            for term_id in ["gtex.tissue.thyroid", "tcga_gdc.primary_site.thyroid_gland"]:
                add_term_mapping(concept_id, "gtex" if term_id.startswith("gtex") else "tcga_gdc", term_id, "Thyroid tissue concept maps to GTEx tissue and TCGA primary site.")
        elif concept_id == "tissue.breast":
            for term_id in ["gtex.tissue.breast", "tcga_gdc.primary_site.breast"]:
                add_term_mapping(concept_id, "gtex" if term_id.startswith("gtex") else "tcga_gdc", term_id, "Breast tissue concept maps to GTEx breast tissue and TCGA breast site.")
        elif concept_id == "tissue.lung":
            for term_id in ["gtex.tissue.lung", "tcga_gdc.primary_site.bronchus_and_lung"]:
                add_term_mapping(concept_id, "gtex" if term_id.startswith("gtex") else "tcga_gdc", term_id, "Lung tissue concept maps to GTEx lung tissue and TCGA bronchus/lung site.")
        elif concept_id == "tissue.liver":
            for term_id in ["gtex.tissue.liver", "tcga_gdc.primary_site.liver"]:
                add_term_mapping(concept_id, "gtex" if term_id.startswith("gtex") else "tcga_gdc", term_id, "Liver tissue concept maps to GTEx liver tissue and TCGA liver site.")
        elif concept_id == "tissue.brain":
            for term_id in ["gtex.tissue.brain", "tcga_gdc.primary_site.brain"]:
                add_term_mapping(concept_id, "gtex" if term_id.startswith("gtex") else "tcga_gdc", term_id, "Brain tissue concept maps to GTEx brain tissue and TCGA brain site.")
        elif concept_id == "tissue.stomach":
            for term_id in ["gtex.tissue.stomach", "tcga_gdc.primary_site.stomach"]:
                add_term_mapping(concept_id, "gtex" if term_id.startswith("gtex") else "tcga_gdc", term_id, "Stomach tissue concept maps to GTEx stomach tissue and TCGA stomach site.")
        elif concept_id == "tissue.prostate":
            for term_id in ["gtex.tissue.prostate", "tcga_gdc.primary_site.prostate_gland"]:
                add_term_mapping(concept_id, "gtex" if term_id.startswith("gtex") else "tcga_gdc", term_id, "Prostate tissue concept maps to GTEx prostate tissue and TCGA prostate site.")
        elif concept_id == "tissue.pancreas":
            for term_id in ["gtex.tissue.pancreas", "tcga_gdc.primary_site.pancreas"]:
                add_term_mapping(concept_id, "gtex" if term_id.startswith("gtex") else "tcga_gdc", term_id, "Pancreas tissue concept maps to GTEx pancreas tissue and TCGA pancreas site.")
        elif concept_id == "tissue.ovary":
            for term_id in ["gtex.tissue.ovary", "tcga_gdc.primary_site.ovary"]:
                add_term_mapping(concept_id, "gtex" if term_id.startswith("gtex") else "tcga_gdc", term_id, "Ovary tissue concept maps to GTEx ovary tissue and TCGA ovary site.")
        elif concept_id == "tissue.skin":
            for term_id in ["gtex.tissue.skin", "tcga_gdc.primary_site.skin"]:
                add_term_mapping(concept_id, "gtex" if term_id.startswith("gtex") else "tcga_gdc", term_id, "Skin tissue concept maps to GTEx skin tissue and TCGA skin site.")
        elif concept_id == "tissue.blood":
            for term_id in ["gtex.tissue.blood", "tcga_gdc.primary_site.hematopoietic_and_reticuloendothelial_systems"]:
                add_term_mapping(concept_id, "gtex" if term_id.startswith("gtex") else "tcga_gdc", term_id, "Blood tissue concept maps to GTEx blood tissue and TCGA hematopoietic site.")
        elif concept_id == "tissue.colorectal":
            for term_id in ["gtex.tissue.colon", "tcga_gdc.primary_site.colon", "tcga_gdc.primary_site.rectum"]:
                add_term_mapping(concept_id, "gtex" if term_id.startswith("gtex") else "tcga_gdc", term_id, "Colorectal tissue concept maps to colon and rectum references.")
        elif concept_id == "tissue.blood_bone_marrow":
            for term_id in ["gtex.tissue.blood", "tcga_gdc.primary_site.hematopoietic_and_reticuloendothelial_systems"]:
                add_term_mapping(concept_id, "gtex" if term_id.startswith("gtex") else "tcga_gdc", term_id, "Blood/bone-marrow concept maps to GTEx blood and hematopoietic TCGA site.")
        elif concept_id == "tissue.lymphoid_tissue":
            for term_id in ["gtex.tissue.spleen", "gtex.tissue.blood", "tcga_gdc.primary_site.hematopoietic_and_reticuloendothelial_systems"]:
                add_term_mapping(concept_id, "gtex" if term_id.startswith("gtex") else "tcga_gdc", term_id, "Lymphoid tissue concept maps to spleen, blood, and hematopoietic TCGA site.")
        elif concept_id == "tissue.salivary_gland":
            add_term_mapping(concept_id, "gtex", "gtex.tissue.minor_salivary_gland", "Salivary gland concept maps to GTEx minor salivary gland tissue.")
        elif concept_id.startswith("disease."):
            disease_name = concept["concept_en"]
            disease_title = next((token for token in synonyms if token and token.lower() == disease_name.lower()), concept["concept_en"].title())
            for term in full_terms:
                if term["field_name"] == "project.disease_type" and term["field_value"].lower() == disease_title.lower():
                    add_term_mapping(concept_id, "tcga_gdc", term["term_id"], "Disease concept maps to a TCGA disease type.")
                if term["field_name"] == "project.project_id" and term["notes"].lower().endswith(f"for {disease_title.lower()}."):
                    add_term_mapping(concept_id, "tcga_gdc", term["term_id"], "Disease concept maps to related TCGA project code.")
        elif concept_id.startswith("tissue."):
            target_tokens = {concept_en.lower(), *[token.lower() for token in synonyms]}
            for term in full_terms:
                if term["term_type"] != "value":
                    continue
                if term["field_name"] not in {"cases.primary_site", "tissue"}:
                    continue
                term_tokens = {term["field_value"].lower(), term["display_label_en"].lower(), term["term_en"].lower()}
                if target_tokens & term_tokens:
                    add_term_mapping(concept_id, term["source"], term["term_id"], "Tissue concept maps to structured tissue terms.")

        if concept["concept_category"] in {"disease", "tissue", "sample_type", "analysis_resource", "access"}:
            geo_terms = [concept_en, *synonyms]
            for value in geo_terms:
                add_mapping(
                    mapping_id=f"map.{slugify(concept_id)}.geo.{slugify(value)}",
                    concept_id=concept_id,
                    source="geo",
                    rule_kind="query_term",
                    target_value=value,
                    notes="Reserved GEO query-expansion term derived from the shared concept layer.",
                )

    return sorted(mappings, key=lambda row: (row["concept_id"], row["source"], row["rule_kind"], row["target_value"], row["target_term_id"]))


def build_chinese_concept_terms(concepts: list[dict[str, str]]) -> list[dict[str, str]]:
    concept_ids = {row["concept_id"] for row in concepts}
    rows: list[dict[str, str]] = []

    def add_row(**kwargs: str | int) -> None:
        rows.append(make_chinese_term(**kwargs))

    seed_rows = [
        ("zh.disease.thyroid_cancer.standard", "disease.thyroid_cancer", "甲状腺癌", "疾病", "standard", 10, "甲状腺癌", "最小中文目录链路中的核心疾病词。"),
        ("zh.disease.thyroid_cancer.colloquial", "disease.thyroid_cancer", "甲癌", "疾病", "colloquial", 20, "甲状腺癌", "常见中文口语简称。"),
        ("zh.disease.thyroid_cancer.mixed", "disease.thyroid_cancer", "甲状腺癌 THCA", "疾病", "mixed_variant", 30, "甲状腺癌", "中英混合检索写法。"),
        ("zh.disease.thyroid_cancer.code", "disease.thyroid_cancer", "THCA", "疾病", "mixed_variant", 40, "甲状腺癌", "项目代码常作为中文检索中的混合提示词。"),
        ("zh.disease.ptc.standard", "disease.papillary_thyroid_carcinoma", "甲状腺乳头状癌", "疾病", "standard", 50, "甲状腺乳头状癌", "为后续 GEO subtype 扩展预留。"),
        ("zh.disease.breast_cancer.standard", "disease.breast_cancer", "乳腺癌", "疾病", "standard", 55, "乳腺癌", "高频实体瘤中文入口。"),
        ("zh.disease.breast_cancer.mixed", "disease.breast_cancer", "乳腺癌 BRCA", "疾病", "mixed_variant", 56, "乳腺癌", "中英混合写法。"),
        ("zh.disease.luad.standard", "disease.lung_adenocarcinoma", "肺腺癌", "疾病", "standard", 57, "肺腺癌", "LUAD 的核心中文入口。"),
        ("zh.disease.luad.full", "disease.lung_adenocarcinoma", "肺腺癌 LUAD", "疾病", "mixed_variant", 58, "肺腺癌", "中英混合写法。"),
        ("zh.disease.lusc.standard", "disease.lung_squamous_cell_carcinoma", "肺鳞癌", "疾病", "standard", 59, "肺鳞癌", "LUSC 的核心中文入口。"),
        ("zh.disease.hcc.standard", "disease.hepatocellular_carcinoma", "肝细胞癌", "疾病", "standard", 60, "肝细胞癌", "LIHC/HCC 的高频中文入口。"),
        ("zh.disease.hcc.mixed", "disease.hepatocellular_carcinoma", "肝细胞癌 HCC", "疾病", "mixed_variant", 61, "肝细胞癌", "中英混合写法。"),
        ("zh.disease.crc.standard", "disease.colorectal_cancer", "结直肠癌", "疾病", "standard", 62, "结直肠癌", "结直肠癌 umbrella concept 的中文入口。"),
        ("zh.disease.gastric.standard", "disease.gastric_cancer", "胃癌", "疾病", "standard", 63, "胃癌", "胃癌 umbrella concept 的中文入口。"),
        ("zh.disease.prostate.standard", "disease.prostate_cancer", "前列腺癌", "疾病", "standard", 64, "前列腺癌", "前列腺癌 umbrella concept 的中文入口。"),
        ("zh.disease.pancreatic.standard", "disease.pancreatic_cancer", "胰腺癌", "疾病", "standard", 65, "胰腺癌", "胰腺癌 umbrella concept 的中文入口。"),
        ("zh.disease.ovarian.standard", "disease.ovarian_cancer", "卵巢癌", "疾病", "standard", 66, "卵巢癌", "卵巢癌 umbrella concept 的中文入口。"),
        ("zh.disease.gbm.standard", "disease.glioblastoma", "胶质母细胞瘤", "疾病", "standard", 67, "胶质母细胞瘤", "GBM 的核心中文入口。"),
        ("zh.disease.gbm.short", "disease.glioblastoma", "GBM", "疾病", "mixed_variant", 68, "胶质母细胞瘤", "常见缩写。"),
        ("zh.disease.melanoma.standard", "disease.melanoma", "黑色素瘤", "疾病", "standard", 69, "黑色素瘤", "SKCM 的常见中文入口。"),
        ("zh.disease.leukemia.standard", "disease.leukemia", "白血病", "疾病", "standard", 70, "白血病", "LAML 等血液肿瘤 umbrella 中文入口。"),
        ("zh.disease.lymphoma.standard", "disease.lymphoma", "淋巴瘤", "疾病", "standard", 71, "淋巴瘤", "DLBC 等淋巴瘤 umbrella 中文入口。"),
        ("zh.disease.cervical.standard", "disease.cervical_cancer", "宫颈癌", "疾病", "standard", 72, "宫颈癌", "CESC 的核心中文入口。"),
        ("zh.disease.endometrial.standard", "disease.endometrial_cancer", "子宫内膜癌", "疾病", "standard", 73, "子宫内膜癌", "UCEC 的核心中文入口。"),
        ("zh.disease.bladder.standard", "disease.bladder_cancer", "膀胱癌", "疾病", "standard", 74, "膀胱癌", "BLCA 的核心中文入口。"),
        ("zh.disease.kirc.standard", "disease.kidney_renal_clear_cell_carcinoma", "肾透明细胞癌", "疾病", "standard", 75, "肾透明细胞癌", "KIRC 的核心中文入口。"),
        ("zh.disease.kirp.standard", "disease.kidney_renal_papillary_cell_carcinoma", "肾乳头状癌", "疾病", "standard", 76, "肾乳头状癌", "KIRP 的核心中文入口。"),
        ("zh.disease.hnsc.standard", "disease.head_and_neck_squamous_cell_carcinoma", "头颈鳞癌", "疾病", "standard", 77, "头颈鳞癌", "HNSC 的核心中文入口。"),
        ("zh.disease.esca.standard", "disease.esophageal_carcinoma", "食管癌", "疾病", "standard", 78, "食管癌", "ESCA 的核心中文入口。"),
        ("zh.disease.chol.standard", "disease.cholangiocarcinoma", "胆管癌", "疾病", "standard", 79, "胆管癌", "CHOL 的核心中文入口。"),
        ("zh.disease.meso.standard", "disease.mesothelioma", "间皮瘤", "疾病", "standard", 80, "间皮瘤", "MESO 的核心中文入口。"),
        ("zh.disease.thym.standard", "disease.thymoma", "胸腺瘤", "疾病", "standard", 81, "胸腺瘤", "THYM 的核心中文入口。"),
        ("zh.disease.tgct.standard", "disease.testicular_germ_cell_tumors", "睾丸生殖细胞肿瘤", "疾病", "standard", 82, "睾丸生殖细胞肿瘤", "TGCT 的核心中文入口。"),
        ("zh.disease.sarc.standard", "disease.sarcoma", "肉瘤", "疾病", "standard", 83, "肉瘤", "SARC 的核心中文入口。"),
        ("zh.disease.lgg.standard", "disease.lower_grade_glioma", "低级别胶质瘤", "疾病", "standard", 84, "低级别胶质瘤", "LGG 的核心中文入口。"),
        ("zh.disease.acc.standard", "disease.adrenocortical_carcinoma", "肾上腺皮质癌", "疾病", "standard", 85, "肾上腺皮质癌", "ACC 的核心中文入口。"),
        ("zh.disease.pcpg.standard", "disease.pheochromocytoma_and_paraganglioma", "嗜铬细胞瘤", "疾病", "standard", 86, "嗜铬细胞瘤 / 副神经节瘤", "PCPG 的常见中文入口。"),
        ("zh.disease.pcpg.full", "disease.pheochromocytoma_and_paraganglioma", "嗜铬细胞瘤 / 副神经节瘤", "疾病", "synonym", 87, "嗜铬细胞瘤 / 副神经节瘤", "PCPG 的全称中文入口。"),
        ("zh.disease.lung_umbrella.standard", "disease.lung_cancer", "肺癌", "疾病", "standard", 88, "肺癌", "上位肺癌概念。"),
        ("zh.disease.kidney_umbrella.standard", "disease.kidney_cancer", "肾癌", "疾病", "standard", 89, "肾癌", "上位肾癌概念。"),
        ("zh.disease.brain_umbrella.standard", "disease.brain_tumor", "脑肿瘤", "疾病", "standard", 90, "脑肿瘤", "上位脑肿瘤概念。"),
        ("zh.disease.gyn_umbrella.standard", "disease.gynecologic_cancer", "妇科肿瘤", "疾病", "standard", 91, "妇科肿瘤", "上位妇科肿瘤概念。"),
        ("zh.disease.gu_umbrella.standard", "disease.genitourinary_cancer", "泌尿系统肿瘤", "疾病", "standard", 92, "泌尿系统肿瘤", "上位泌尿系统肿瘤概念。"),
        ("zh.disease.digestive_umbrella.standard", "disease.digestive_system_tumor", "消化系统肿瘤", "疾病", "standard", 93, "消化系统肿瘤", "上位消化系统肿瘤概念。"),
        ("zh.disease.hn_umbrella.standard", "disease.head_and_neck_tumor", "头颈肿瘤", "疾病", "standard", 94, "头颈肿瘤", "上位头颈肿瘤概念。"),
        ("zh.disease.heme_umbrella.standard", "disease.hematologic_malignancy", "血液肿瘤", "疾病", "standard", 95, "血液肿瘤", "上位血液肿瘤概念。"),
        ("zh.disease.endocrine_umbrella.standard", "disease.endocrine_tumor", "内分泌肿瘤", "疾病", "standard", 96, "内分泌肿瘤", "上位内分泌肿瘤概念。"),
        ("zh.disease.neuroendocrine_umbrella.standard", "disease.neuroendocrine_tumor", "神经内分泌肿瘤", "疾病", "standard", 97, "神经内分泌肿瘤", "上位神经内分泌肿瘤概念。"),
        ("zh.tissue.thyroid.standard", "tissue.thyroid", "甲状腺组织", "组织", "standard", 60, "甲状腺组织", "标准组织概念词。"),
        ("zh.tissue.thyroid.short", "tissue.thyroid", "甲状腺", "组织", "synonym", 70, "甲状腺组织", "常见简写。"),
        ("zh.tissue.thyroid.normal", "tissue.thyroid", "正常甲状腺", "组织", "colloquial", 80, "甲状腺组织", "口语化正常组织表达，会与 normal tissue 概念组合使用。"),
        ("zh.tissue.breast.standard", "tissue.breast", "乳腺组织", "组织", "standard", 81, "乳腺组织", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.breast.short", "tissue.breast", "乳腺", "组织", "synonym", 82, "乳腺组织", "常见简写。"),
        ("zh.tissue.lung.standard", "tissue.lung", "肺组织", "组织", "standard", 83, "肺组织", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.lung.short", "tissue.lung", "肺", "组织", "synonym", 84, "肺组织", "常见简写。"),
        ("zh.tissue.liver.standard", "tissue.liver", "肝组织", "组织", "standard", 85, "肝组织", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.liver.short", "tissue.liver", "肝", "组织", "synonym", 86, "肝组织", "常见简写。"),
        ("zh.tissue.brain.standard", "tissue.brain", "脑组织", "组织", "standard", 87, "脑组织", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.brain.short", "tissue.brain", "脑", "组织", "synonym", 88, "脑组织", "常见简写。"),
        ("zh.tissue.colorectal.standard", "tissue.colorectal", "结直肠组织", "组织", "standard", 89, "结直肠组织", "结直肠 umbrella tissue 中文入口。"),
        ("zh.tissue.colorectal.synonym", "tissue.colorectal", "结肠组织", "组织", "synonym", 90, "结直肠组织", "常见中文变体。"),
        ("zh.tissue.stomach.standard", "tissue.stomach", "胃组织", "组织", "standard", 91, "胃组织", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.prostate.standard", "tissue.prostate", "前列腺组织", "组织", "standard", 92, "前列腺组织", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.pancreas.standard", "tissue.pancreas", "胰腺组织", "组织", "standard", 93, "胰腺组织", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.ovary.standard", "tissue.ovary", "卵巢组织", "组织", "standard", 94, "卵巢组织", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.skin.standard", "tissue.skin", "皮肤", "组织", "standard", 95, "皮肤", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.blood_bm.standard", "tissue.blood_bone_marrow", "血液/骨髓", "组织", "standard", 96, "血液/骨髓", "血液与骨髓 umbrella tissue 中文入口。"),
        ("zh.tissue.blood_bm.synonym", "tissue.blood_bone_marrow", "骨髓", "组织", "synonym", 97, "血液/骨髓", "常见中文变体。"),
        ("zh.tissue.blood_bm.short", "tissue.blood_bone_marrow", "血液", "组织", "synonym", 98, "血液/骨髓", "常见中文变体。"),
        ("zh.tissue.lymphoid.standard", "tissue.lymphoid_tissue", "淋巴组织", "组织", "standard", 99, "淋巴组织", "淋巴组织 umbrella tissue 中文入口。"),
        ("zh.tissue.lymphoid.node", "tissue.lymphoid_tissue", "淋巴结", "组织", "synonym", 100, "淋巴组织", "常见中文变体。"),
        ("zh.tissue.kidney.standard", "tissue.kidney", "肾脏", "组织", "standard", 101, "肾脏", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.bladder.standard", "tissue.bladder", "膀胱", "组织", "standard", 102, "膀胱", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.cervix.standard", "tissue.cervix_uteri", "宫颈", "组织", "standard", 103, "宫颈", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.uterus.standard", "tissue.uterus", "子宫", "组织", "standard", 104, "子宫", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.esophagus.standard", "tissue.esophagus", "食管", "组织", "standard", 105, "食管", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.bile_duct.standard", "tissue.bile_duct", "胆管", "组织", "standard", 106, "胆管", "TCGA 常见组织入口。"),
        ("zh.tissue.bile_duct.synonym", "tissue.bile_duct", "胆道", "组织", "synonym", 107, "胆管", "常见中文变体。"),
        ("zh.tissue.small_intestine.standard", "tissue.small_intestine", "小肠", "组织", "standard", 108, "小肠", "GTEx 常见组织入口。"),
        ("zh.tissue.salivary.standard", "tissue.salivary_gland", "唾液腺", "组织", "standard", 109, "唾液腺", "GTEx 唾液腺入口。"),
        ("zh.tissue.pituitary.standard", "tissue.pituitary", "垂体", "组织", "standard", 110, "垂体", "GTEx 常见组织入口。"),
        ("zh.tissue.adrenal.standard", "tissue.adrenal_gland", "肾上腺", "组织", "standard", 111, "肾上腺", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.testis.standard", "tissue.testis", "睾丸", "组织", "standard", 112, "睾丸", "GTEx/TCGA 常见组织入口。"),
        ("zh.tissue.fallopian.standard", "tissue.fallopian_tube", "输卵管", "组织", "standard", 113, "输卵管", "GTEx 常见组织入口。"),
        ("zh.tissue.vagina.standard", "tissue.vagina", "阴道", "组织", "standard", 114, "阴道", "GTEx 常见组织入口。"),
        ("zh.tissue.nerve.standard", "tissue.nerve", "神经", "组织", "standard", 115, "神经", "GTEx 常见组织入口。"),
        ("zh.tissue.vessel.standard", "tissue.blood_vessel", "血管", "组织", "standard", 116, "血管", "GTEx 常见组织入口。"),
        ("zh.tissue.heart.standard", "tissue.heart", "心脏", "组织", "standard", 117, "心脏", "GTEx 常见组织入口。"),
        ("zh.tissue.muscle.standard", "tissue.muscle", "肌肉", "组织", "standard", 118, "肌肉", "GTEx 常见组织入口。"),
        ("zh.sample.primary_tumor.standard", "sample_type.primary_tumor", "原发肿瘤", "样本类型", "standard", 110, "原发肿瘤", "TCGA 样本类型的核心中文入口。"),
        ("zh.sample.primary_tumor.synonym", "sample_type.primary_tumor", "肿瘤样本", "样本类型", "synonym", 120, "原发肿瘤", "用户常见中文泛化写法。"),
        ("zh.sample.normal.standard", "sample_type.normal", "正常组织", "样本类型", "standard", 130, "正常组织", "跨源 normal tissue 上层概念。"),
        ("zh.sample.normal.synonym", "sample_type.normal", "正常样本", "样本类型", "synonym", 140, "正常组织", "中文检索常见变体。"),
        ("zh.sample.normal.thyroid", "sample_type.normal", "正常甲状腺", "样本类型", "colloquial", 145, "正常组织", "让正常甲状腺可同时命中 normal sample 概念。"),
        ("zh.sample.solid_tissue_normal.standard", "sample_type.solid_tissue_normal", "实体正常组织", "样本类型", "standard", 150, "实体正常组织", "对应 TCGA solid tissue normal。"),
        ("zh.sample.tumor_tissue.standard", "sample_type.tumor_tissue", "肿瘤组织", "样本类型", "standard", 160, "肿瘤组织", "上层 tumor tissue 中文入口。"),
        ("zh.analysis.gene_expression.standard", "analysis_resource.gene_expression", "基因表达", "数据类型", "standard", 170, "基因表达", "中文目录中的核心表达概念。"),
        ("zh.analysis.gene_expression.synonym", "analysis_resource.gene_expression", "表达矩阵", "数据类型", "synonym", 180, "基因表达", "用户常见表达数据说法。"),
        ("zh.analysis.clinical.standard", "analysis_resource.clinical", "临床信息", "数据类型", "standard", 190, "临床信息", "中文目录中的临床资源入口。"),
        ("zh.analysis.clinical.synonym", "analysis_resource.clinical", "临床数据", "数据类型", "synonym", 200, "临床信息", "常见中文变体。"),
        ("zh.analysis.biospecimen.standard", "analysis_resource.biospecimen", "样本信息", "数据类型", "standard", 210, "样本信息", "biospecimen 的中文入口。"),
        ("zh.analysis.read_count.standard", "analysis_resource.read_count", "读段计数", "分析资源", "standard", 220, "读段计数", "GTEx/GEO 常见表达单位。"),
        ("zh.analysis.tpm.standard", "analysis_resource.tpm", "TPM", "分析资源", "standard", 230, "TPM", "常见归一化表达单位。"),
        ("zh.analysis.sample_attributes.standard", "analysis_resource.sample_attributes", "样本属性", "分析资源", "standard", 240, "样本属性", "GTEx sample attributes 的中文入口。"),
        ("zh.analysis.subject_phenotypes.standard", "analysis_resource.subject_phenotypes", "受试者表型", "分析资源", "standard", 250, "受试者表型", "GTEx subject phenotypes 的中文入口。"),
        ("zh.access.open.standard", "access.open", "开放访问", "访问级别", "standard", 260, "开放访问", "中文访问模式核心概念。"),
        ("zh.access.open.synonym", "access.open", "开放获取", "访问级别", "synonym", 270, "开放访问", "常见中文同义表达。"),
        ("zh.access.controlled.standard", "access.controlled", "受控访问", "访问级别", "standard", 280, "受控访问", "对应 controlled access。"),
        ("zh.access.protected.standard", "access.protected", "受保护访问", "访问级别", "standard", 290, "受保护访问", "对应 protected access。"),
    ]

    for row in seed_rows:
        zh_term_id, concept_id, term_zh, category_zh, alias_type, priority, display_label_zh, notes = row
        if concept_id not in concept_ids:
            raise ValueError(f"Chinese concept term references unknown concept_id: {concept_id}")
        add_row(
            zh_term_id=zh_term_id,
            concept_id=concept_id,
            term_zh=term_zh,
            category_zh=category_zh,
            alias_type=alias_type,
            priority=priority,
            display_label_zh=display_label_zh,
            notes=notes,
        )

    return sorted(rows, key=lambda row: (int(row["priority"]), row["term_zh"]))


def _curated_category(term: dict[str, str]) -> str | None:
    if term["bucket"] == "source_entities":
        return "database_entity"
    if term["field_name"] == "project.project_id" or term["field_name"] == "project.disease_type":
        return "disease"
    if term["field_name"] in {"cases.primary_site", "tissue", "subregion"}:
        return "tissue"
    if term["field_name"] in {"cases.samples.sample_type", "cases.samples.tissue_type", "cases.samples.tumor_descriptor"}:
        return "sample_type"
    if term["field_name"] in {"files.access", "access", "release"} or term["bucket"] == "access_and_mode_terms":
        return "access"
    if term["field_name"] in {"resource_name", "expression_unit", "display_category"}:
        return "analysis_resource"
    if term["field_name"] in {"files.data_type", "files.data_category"}:
        return "data_type"
    return None


def _is_curated_candidate(term: dict[str, str]) -> bool:
    if term["is_active"] != "true":
        return False
    if term["term_type"] == "field":
        return False
    if term["field_name"] in UI_EXCLUDED_FIELD_NAMES:
        return False
    if term["term_type"] == "value" and term["field_name"] in {"files.experimental_strategy", "files.analysis.workflow_type"}:
        return False
    category = _curated_category(term)
    return category is not None


def build_curated_terms(full_terms: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], dict[str, str]] = {}
    for term in full_terms:
        if not _is_curated_candidate(term):
            continue
        category = _curated_category(term)
        if category is None:
            continue
        title = term["display_label_en"]
        group_key = (category, title.lower())
        entry = grouped.get(group_key)
        if entry is None:
            entry = {
                "ui_term_id": f"ui.{category}.{slugify(title)}",
                "source": term["source"],
                "category": category,
                "title_en": title,
                "display_label_en": title,
                "linked_term_ids": term["term_id"],
                "default_priority": term["priority"],
                "recommended_for_navigation": "true",
                "recommended_for_search_hint": "true" if category != "database_entity" else "false",
                "notes": f"Curated from full lexicon term `{term['term_id']}`.",
                "is_active": term["is_active"],
            }
            grouped[group_key] = entry
            continue

        existing_sources = {entry["source"], term["source"]}
        entry["source"] = entry["source"] if len(existing_sources) == 1 else "shared"
        linked_ids = entry["linked_term_ids"].split("|")
        if term["term_id"] not in linked_ids:
            linked_ids.append(term["term_id"])
            entry["linked_term_ids"] = "|".join(linked_ids)
        entry["default_priority"] = str(min(int(entry["default_priority"]), int(term["priority"])))

    curated_terms = sorted(grouped.values(), key=lambda row: (int(row["default_priority"]), row["category"], row["title_en"].lower()))
    return curated_terms


def build_aliases(full_terms: list[dict[str, str]]) -> list[dict[str, str]]:
    aliases: list[dict[str, str]] = []
    priority = 10

    def add_alias(term_id: str, alias_en: str, alias_kind: str) -> None:
        nonlocal priority
        aliases.append(
            {
                "alias_id": f"alias.{slugify(term_id)}.{slugify(alias_en)}",
                "term_id": term_id,
                "alias_en": alias_en,
                "alias_kind": alias_kind,
                "priority": str(priority),
            }
        )
        priority += 10

    for term in full_terms:
        if term["field_name"] == "project.project_id" and term["field_value"].startswith("TCGA-"):
            add_alias(term["term_id"], term["field_value"].replace("TCGA-", ""), "abbreviation")

    manual_aliases = [
        ("tcga_gdc.data_type.gene_expression_quantification", "gene expression", "synonym"),
        ("gtex.entity.sample_attributes", "sample metadata", "display_variant"),
        ("gtex.resource.sample_attributes", "sample metadata", "display_variant"),
        ("gtex.entity.subject_phenotypes", "subject metadata", "display_variant"),
        ("gtex.resource.subject_phenotypes", "subject metadata", "display_variant"),
        ("tcga_gdc.sample_type.solid_tissue_normal", "normal tissue", "synonym"),
        ("tcga_gdc.sample_type.primary_tumor", "tumor", "synonym"),
        ("gtex.entity.eqtl", "eqtl", "lowercase_variant"),
        ("gtex.entity.sqtl", "sqtl", "lowercase_variant"),
        ("gtex.resource.eqtl", "eqtl", "lowercase_variant"),
        ("gtex.resource.sqtl", "sqtl", "lowercase_variant"),
        ("gtex.resource.tpm", "tpm", "lowercase_variant"),
    ]
    for term_id, alias_en, alias_kind in manual_aliases:
        add_alias(term_id, alias_en, alias_kind)

    return aliases


def _validate_rows(rows: list[dict[str, str]], headers: list[str], id_key: str) -> None:
    seen_ids: set[str] = set()
    for row in rows:
        missing = [header for header in headers if header not in row]
        if missing:
            raise ValueError(f"Row missing columns {missing}: {row}")
        extra = [key for key in row if key not in headers]
        if extra:
            raise ValueError(f"Row contains unexpected columns {extra}: {row}")
        row_id = row[id_key]
        if row_id in seen_ids:
            raise ValueError(f"Duplicate {id_key}: {row_id}")
        seen_ids.add(row_id)


def write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        prefix=f".{path.stem}.",
        suffix=f"{path.suffix}.tmp",
        delete=False,
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def build_english_core_lexicon(output_dir: Path | None = None) -> tuple[Path, Path, Path, Path, Path, Path]:
    repo_root = Path(__file__).resolve().parents[1]
    lexicon_dir = output_dir or repo_root / "tcga_gtex" / "lexicon"

    full_terms = build_full_terms()
    concepts = build_concept_catalog(full_terms)
    concept_source_mappings = build_concept_source_mappings(concepts, full_terms)
    chinese_terms = build_chinese_concept_terms(concepts)
    curated_terms = build_curated_terms(full_terms)
    aliases = build_aliases(full_terms)

    _validate_rows(full_terms, FULL_TERM_HEADERS, "term_id")
    _validate_rows(concepts, CONCEPT_HEADERS, "concept_id")
    _validate_rows(concept_source_mappings, CONCEPT_SOURCE_MAPPING_HEADERS, "mapping_id")
    _validate_rows(chinese_terms, CHINESE_CONCEPT_TERM_HEADERS, "zh_term_id")
    _validate_rows(curated_terms, CURATED_TERM_HEADERS, "ui_term_id")
    _validate_rows(aliases, ALIAS_HEADERS, "alias_id")

    term_ids = {term["term_id"] for term in full_terms}
    unknown_alias_terms = sorted({alias["term_id"] for alias in aliases} - term_ids)
    if unknown_alias_terms:
        raise ValueError(f"Aliases reference unknown term_ids: {unknown_alias_terms}")

    concept_ids = {concept["concept_id"] for concept in concepts}
    unknown_mapping_concepts = sorted({row["concept_id"] for row in concept_source_mappings} - concept_ids)
    if unknown_mapping_concepts:
        raise ValueError(f"Concept source mappings reference unknown concept_ids: {unknown_mapping_concepts}")
    unknown_mapping_terms = sorted(
        {
            row["target_term_id"]
            for row in concept_source_mappings
            if row["target_term_id"] and row["target_term_id"] not in term_ids
        }
    )
    if unknown_mapping_terms:
        raise ValueError(f"Concept source mappings reference unknown term_ids: {unknown_mapping_terms}")

    concepts_path = lexicon_dir / "concept_catalog.csv"
    concept_mappings_path = lexicon_dir / "concept_source_mappings.csv"
    chinese_terms_path = lexicon_dir / "chinese_concept_terms.csv"
    full_path = lexicon_dir / "english_core_terms_full.csv"
    curated_path = lexicon_dir / "english_ui_terms_curated.csv"
    aliases_path = lexicon_dir / "english_term_aliases.csv"
    legacy_path = lexicon_dir / "english_core_terms.csv"

    write_csv(concepts_path, CONCEPT_HEADERS, concepts)
    write_csv(concept_mappings_path, CONCEPT_SOURCE_MAPPING_HEADERS, concept_source_mappings)
    write_csv(chinese_terms_path, CHINESE_CONCEPT_TERM_HEADERS, chinese_terms)
    write_csv(full_path, FULL_TERM_HEADERS, full_terms)
    write_csv(curated_path, CURATED_TERM_HEADERS, curated_terms)
    write_csv(aliases_path, ALIAS_HEADERS, aliases)
    write_csv(legacy_path, FULL_TERM_HEADERS, full_terms)
    return concepts_path, concept_mappings_path, chinese_terms_path, full_path, curated_path, aliases_path


def main() -> None:
    concepts_path, concept_mappings_path, chinese_terms_path, full_path, curated_path, aliases_path = build_english_core_lexicon()
    print(f"Wrote {concepts_path}")
    print(f"Wrote {concept_mappings_path}")
    print(f"Wrote {chinese_terms_path}")
    print(f"Wrote {full_path}")
    print(f"Wrote {curated_path}")
    print(f"Wrote {aliases_path}")


if __name__ == "__main__":
    main()
