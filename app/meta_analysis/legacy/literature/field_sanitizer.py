from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from literature.schema import IMPORTABLE_FIELDS, SYSTEM_CONTROLLED_FIELDS


@dataclass(frozen=True)
class FieldSanitizationResult:
    sanitized: dict[str, Any]
    removed_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class LiteratureFieldSanitizer:
    def sanitize_import_payload(self, payload: dict[str, Any]) -> FieldSanitizationResult:
        sanitized: dict[str, Any] = {}
        removed: list[str] = []
        warnings: list[str] = []
        for key, value in payload.items():
            normalized_key = str(key).strip()
            if normalized_key in SYSTEM_CONTROLLED_FIELDS or normalized_key.startswith("attachment_"):
                removed.append(normalized_key)
                warnings.append(f"system_field_removed:{normalized_key}")
                continue
            if normalized_key not in IMPORTABLE_FIELDS:
                removed.append(normalized_key)
                warnings.append(f"unsupported_field_removed:{normalized_key}")
                continue
            sanitized[normalized_key] = value
        return FieldSanitizationResult(sanitized=sanitized, removed_fields=removed, warnings=warnings)

