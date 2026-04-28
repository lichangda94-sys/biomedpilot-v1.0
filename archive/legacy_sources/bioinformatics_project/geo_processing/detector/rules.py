"""Shared rule constants for GEO detection heuristics."""

from __future__ import annotations

from .models import MatrixLevel

TEXT_EXTENSIONS = {
    ".txt",
    ".tsv",
    ".csv",
    ".soft",
    ".xml",
    ".annot",
}
TABULAR_EXTENSIONS = {
    ".txt",
    ".tsv",
    ".csv",
    ".xls",
    ".xlsx",
    ".txt.gz",
    ".tsv.gz",
    ".csv.gz",
}
RAW_EXTENSIONS = {
    ".cel",
    ".fastq",
    ".fq",
    ".bam",
    ".sra",
    ".cel.gz",
    ".fastq.gz",
    ".fq.gz",
    ".bam.gz",
    ".sra.gz",
}
PLATFORM_HINTS = ("gpl", "platform", "annotation", "annot", "probe", "feature")
METADATA_HINTS = (
    "sample",
    "metadata",
    "design",
    "phenotype",
    "clinical",
    "traits",
    "characteristics",
    "annotation",
)
EXPRESSION_HINTS = (
    "matrix",
    "expression",
    "normalized",
    "counts",
    "fpkm",
    "tpm",
    "rpkm",
    "abundance",
)
EXPRESSION_NEGATIVE_HINTS = (
    "deg",
    "degs",
    "volcano",
    "results",
    "limma",
    "deseq",
    "edgeR".lower(),
    "contrast",
    "comparison",
)
DIFF_RESULT_COLUMNS = {
    "logfc",
    "adj.p.val",
    "p.value",
    "padj",
    "pvalue",
    "qvalue",
    "basemean",
    "statistic",
    "stat",
    "t",
    "b",
    "lfcse",
}
METADATA_COLUMNS = {
    "title",
    "source_name",
    "characteristics",
    "disease",
    "treatment",
    "phenotype",
    "group",
    "condition",
    "sample",
}
MICROARRAY_KEYWORDS = {
    "affymetrix",
    "agilent",
    "beadchip",
    "probe",
    "cel",
    "gpl",
    "array",
    "hybridization",
    "intensit",
    "scan",
}
BULK_RNASEQ_KEYWORDS = {
    "rnaseq",
    "rna-seq",
    "htseq",
    "featurecounts",
    "counts",
    "fpkm",
    "tpm",
    "read count",
    "gene counts",
    "transcript counts",
}
SINGLE_CELL_KEYWORDS = {
    "single cell",
    "single-cell",
    "scrna",
    "10x",
    "seurat",
    "cell barcode",
    "umi",
    "droplets",
}
SPATIAL_KEYWORDS = {"spatial", "visium", "spot", "tissue position"}
MULTIOMICS_KEYWORDS = {"multi-omics", "multiomics", "atac", "chip", "proteogenomic"}

PROBE_PATTERNS = ("_at", "_s_at", "_x_at", "_a_at", "ILMN_", "A_23_P")
GENE_PREFIXES = ("ENSG",)
TRANSCRIPT_PREFIXES = ("ENST",)

MAX_PREVIEW_LINES = 80
MAX_PREVIEW_BYTES = 65536
MAX_TABLE_ROWS = 40
MAX_TABLE_COLUMNS = 30

FAILURE_MATRIX_NOT_FOUND = "MATRIX_NOT_FOUND"
FAILURE_MATRIX_PARSE_FAILED = "MATRIX_PARSE_FAILED"
FAILURE_DIFF_RESULT = "MATRIX_IS_DIFF_RESULT_NOT_EXPRESSION"
FAILURE_SAMPLE_TABLE_MISSING = "SAMPLE_TABLE_MISSING"
FAILURE_METADATA_PARSE_FAILED = "METADATA_PARSE_FAILED"
FAILURE_RAW_ONLY = "RAW_ONLY_DATASET"
FAILURE_UNSUPPORTED = "UNSUPPORTED_TECHNOLOGY"
FAILURE_GPL_MISSING = "GPL_ANNOTATION_MISSING"
FAILURE_PROBE_TO_GENE_FAILED = "PROBE_TO_GENE_FAILED"
FAILURE_AMBIGUOUS = "AMBIGUOUS_FILE_SELECTION"

MATRIX_PRIORITY_ORDER = [
    MatrixLevel.GENE.value,
    MatrixLevel.TRANSCRIPT.value,
    MatrixLevel.PROBE.value,
]
