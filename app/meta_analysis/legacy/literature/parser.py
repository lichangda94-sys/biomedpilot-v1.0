from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from literature.models import ImportFormatHint, ImportSourceKind, ParsedLiteratureRecord


@dataclass(slots=True)
class ImportParseContext:
    batch_id: str
    project_id: str
    input_path: str
    format_hint: ImportFormatHint
    source_type: ImportSourceKind
    metadata: dict[str, Any] = field(default_factory=dict)


class LiteratureParser(Protocol):
    supported_format: ImportFormatHint

    def parse(
        self,
        file_path: Path,
        context: ImportParseContext,
    ) -> list[ParsedLiteratureRecord]:
        ...


class UnsupportedParserError(ValueError):
    """Raised when no parser adapter is registered for the requested format."""
