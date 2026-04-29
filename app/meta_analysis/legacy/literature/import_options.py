from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class UIImportOptions:
    source_database: str = ""
    import_format: str = ""
    create_collection_for_batch: bool = False
    dedup_mode: str = "detect_only"
    import_tags: bool = True
    import_notes: bool = True
    import_attachments: bool = False
    file_handling: str = "ignore_attachments"
    only_new_records: bool = False
    strict_validation: bool = False
    charset: str = "utf-8-sig"


@dataclass(frozen=True)
class ExecutionImportOptions:
    project_id: str
    batch_id: str
    adapter_name: str = ""
    parser_profile: str = "generic"
    progress_callback: Callable[[str], None] | None = None
    diagnostics_enabled: bool = True
    save_raw_payload: bool = True
    run_duplicate_detection: bool = True


@dataclass(frozen=True)
class SaveImportOptions:
    generate_record_id: bool = True
    assign_project_id: bool = True
    assign_import_batch_id: bool = True
    initialize_workflow_status: bool = True
    filter_system_fields: bool = True
    write_audit_log: bool = True
    preserve_raw_payload: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

