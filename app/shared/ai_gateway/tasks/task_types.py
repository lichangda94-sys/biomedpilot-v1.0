from __future__ import annotations


BIO_TASK_PREFIX = "bio_"
META_TASK_PREFIX = "meta_"

BIO_REPORT_DRAFT = "bio_report_draft"
BIO_QUERY_HELP = "bio_query_help"
BIO_GENERATE_DATASET_QUERY_DRAFT = "bio_generate_dataset_query_draft"
BIO_REFINE_MEDICAL_QUERY_TERMS = "bio_refine_medical_query_terms"
BIO_TRANSLATE_DATASET_DETAIL = "bio_translate_dataset_detail"
BIO_SUMMARIZE_DATASET_DETAIL = "bio_summarize_dataset_detail"

META_EXTRACTION_ASSIST = "meta_extraction_assist"
META_SCREENING_ASSIST = "meta_screening_assist"

DEFAULT_BIO_TASK_TYPES = (
    BIO_REPORT_DRAFT,
    BIO_QUERY_HELP,
    BIO_GENERATE_DATASET_QUERY_DRAFT,
    BIO_REFINE_MEDICAL_QUERY_TERMS,
    BIO_TRANSLATE_DATASET_DETAIL,
    BIO_SUMMARIZE_DATASET_DETAIL,
)
DEFAULT_META_TASK_TYPES = (META_EXTRACTION_ASSIST, META_SCREENING_ASSIST)
