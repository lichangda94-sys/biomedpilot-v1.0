"""Literature input-side models and persistence."""

from literature.batch_service import ImportBatchService
from literature.dedup_service import NormalizationDedupService
from literature.merge_service import DedupMergeService
from literature.models import (
    DedupMergeResult,
    DuplicateCandidateGroup,
    ExclusionReason,
    ImportBatch,
    ImportBatchStatus,
    ImportFormatHint,
    ImportRecord,
    ImportRecordStatus,
    ImportSourceKind,
    LiteratureProject,
    LiteratureProjectStatus,
    NormalizedLiteratureRecord,
    ParsedLiteratureRecord,
    ScreeningDecision,
    ScreeningRecord,
    ScreeningStage,
)
from literature.parser import ImportParseContext, LiteratureParser, UnsupportedParserError
from literature.screening_service import ScreeningService
from literature.service import LiteratureProjectService
from literature.store import LiteratureStore

__all__ = [
    "DedupMergeResult",
    "DedupMergeService",
    "DuplicateCandidateGroup",
    "ExclusionReason",
    "ImportBatch",
    "ImportBatchService",
    "ImportBatchStatus",
    "ImportFormatHint",
    "ImportParseContext",
    "LiteratureParser",
    "ImportRecord",
    "ImportRecordStatus",
    "ImportSourceKind",
    "LiteratureProject",
    "LiteratureProjectService",
    "LiteratureProjectStatus",
    "LiteratureStore",
    "NormalizationDedupService",
    "NormalizedLiteratureRecord",
    "ParsedLiteratureRecord",
    "ScreeningDecision",
    "ScreeningRecord",
    "ScreeningService",
    "ScreeningStage",
    "UnsupportedParserError",
]
