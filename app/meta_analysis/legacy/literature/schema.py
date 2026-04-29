from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LiteratureField:
    name: str
    category: str
    importable: bool = True
    system_controlled: bool = False


METADATA_FIELDS = (
    "title",
    "creators",
    "authors",
    "authors_text",
    "first_author",
    "year",
    "date",
    "journal",
    "publication_title",
    "volume",
    "issue",
    "pages",
    "doi",
    "pmid",
    "isbn",
    "issn",
    "url",
    "abstract",
    "language",
    "keywords",
    "publication_type",
    "clinical_trials_ids",
    "external_key",
)

SOURCE_PROVENANCE_FIELDS = (
    "source_database",
    "source_file",
    "source_format",
    "source_record_id",
    "import_batch_id",
    "parser_profile",
    "raw_payload",
)

WORKFLOW_FIELDS = (
    "duplicate_status",
    "screening_status",
    "fulltext_status",
    "extraction_status",
    "risk_of_bias_status",
    "analysis_ready_status",
)

ORGANIZATION_FIELDS = (
    "tags",
    "notes",
    "collections",
    "attachments",
    "relations",
)

SYSTEM_FIELDS = (
    "record_id",
    "project_id",
    "created_at",
    "updated_at",
    "version",
    "checksum",
    "audit_log_id",
    "file_path",
    "attachment_id",
)

CREATOR_TYPES = (
    "author",
    "editor",
    "translator",
    "contributor",
    "group_author",
    "corresponding_author",
    "unknown",
)

PUBLICATION_TYPES = (
    "journal_article",
    "clinical_trial",
    "randomized_trial",
    "observational_study",
    "cohort_study",
    "case_control_study",
    "cross_sectional_study",
    "case_report",
    "conference_abstract",
    "preprint",
    "review",
    "systematic_review",
    "meta_analysis",
    "editorial",
    "letter",
    "thesis",
    "report",
    "guideline",
    "dataset",
    "unknown",
)

IMPORTABLE_FIELDS = frozenset(
    {
        "title",
        "creators",
        "authors",
        "authors_text",
        "year",
        "date",
        "journal",
        "publication_title",
        "volume",
        "issue",
        "pages",
        "doi",
        "pmid",
        "isbn",
        "issn",
        "url",
        "abstract",
        "language",
        "keywords",
        "publication_type",
        "tags",
        "notes",
        "clinical_trials_ids",
        "external_key",
        "source_database",
        "source_file",
        "source_format",
        "source_record_id",
        "parser_profile",
        "raw_payload",
    }
)

SYSTEM_CONTROLLED_FIELDS = frozenset(SYSTEM_FIELDS + WORKFLOW_FIELDS + ("import_batch_id",))

FIELD_NORMALIZATION_RULES = {
    "doi": "strip doi prefix and lowercase",
    "pmid": "digits only",
    "title": "collapse whitespace and trim trailing terminal punctuation",
    "year": "extract 4-digit publication year",
    "journal": "collapse source journal aliases",
    "abstract": "join sections and collapse whitespace",
    "creators": "preserve order and normalize creator_type",
    "publication_type": "map to BioMedPilot publication type registry",
}

LITERATURE_FIELDS = {
    **{name: LiteratureField(name, "metadata", name in IMPORTABLE_FIELDS) for name in METADATA_FIELDS},
    **{name: LiteratureField(name, "source_provenance", name in IMPORTABLE_FIELDS, name == "import_batch_id") for name in SOURCE_PROVENANCE_FIELDS},
    **{name: LiteratureField(name, "workflow", False, True) for name in WORKFLOW_FIELDS},
    **{name: LiteratureField(name, "organization", name in IMPORTABLE_FIELDS, name == "attachments") for name in ORGANIZATION_FIELDS},
    **{name: LiteratureField(name, "system", False, True) for name in SYSTEM_FIELDS},
}
