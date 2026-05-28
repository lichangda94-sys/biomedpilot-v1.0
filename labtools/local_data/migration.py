from __future__ import annotations

from typing import Mapping

from labtools.local_data.models import LabToolsLocalDataError
from labtools.local_data.schema_version import (
    LABTOOLS_AUDIT_LOG_SCHEMA_VERSION,
    LABTOOLS_LOCAL_DATA_STORE_SCHEMA_VERSION,
    LABTOOLS_RECORD_INDEX_SCHEMA_VERSION,
)


def ensure_supported_store_schema(payload: Mapping[str, object], expected_schema_version: str) -> None:
    found = payload.get("schema_version")
    if found != expected_schema_version:
        raise LabToolsLocalDataError(f"LabTools local data schema mismatch: expected {expected_schema_version}, found {found}.")


SUPPORTED_SCHEMA_VERSIONS = frozenset(
    {
        LABTOOLS_LOCAL_DATA_STORE_SCHEMA_VERSION,
        LABTOOLS_RECORD_INDEX_SCHEMA_VERSION,
        LABTOOLS_AUDIT_LOG_SCHEMA_VERSION,
    }
)
