from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AI_DRAFT_STATUSES = {"suggested", "user_accepted", "user_rejected", "user_edited", "confirmed"}


@dataclass(frozen=True)
class AIDraftRecord:
    module: str
    task_type: str
    status: str
    provider: str
    model: str
    input_hash: str
    output_hash: str
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["warnings"] = list(self.warnings)
        return payload


def create_ai_draft_record(
    *,
    module: str,
    task_type: str,
    provider: str,
    model: str,
    input_text: str,
    output_text: str,
    warnings: tuple[str, ...] | list[str] = (),
    summary: dict[str, Any] | None = None,
    status: str = "suggested",
) -> AIDraftRecord:
    return AIDraftRecord(
        module=module,
        task_type=task_type,
        status=_valid_status(status),
        provider=provider,
        model=model,
        input_hash=_sha256(input_text),
        output_hash=_sha256(output_text),
        warnings=tuple(str(warning) for warning in warnings if str(warning).strip()),
        summary=_safe_summary(summary or {}),
    )


def mark_ai_draft_status(record: AIDraftRecord, status: str, *, output_text: str | None = None, summary: dict[str, Any] | None = None) -> AIDraftRecord:
    updates: dict[str, object] = {"status": _valid_status(status)}
    if output_text is not None:
        updates["output_hash"] = _sha256(output_text)
    if summary is not None:
        updates["summary"] = _safe_summary(summary)
    return replace(record, **updates)


def save_ai_draft_record(project_root: str | Path, record: AIDraftRecord, *, filename_hint: str = "ai_draft") -> Path:
    root = Path(project_root)
    directory = root / "ai_drafts"
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"{timestamp}_{_safe_filename(filename_hint)}.json"
    path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _valid_status(status: str) -> str:
    clean = status.strip()
    if clean not in AI_DRAFT_STATUSES:
        raise ValueError(f"Unsupported AI draft status: {status}")
    return clean


def _safe_summary(value: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, item in value.items():
        clean_key = str(key)
        if clean_key in {"raw_prompt", "raw_response", "prompt", "response", "raw_output"}:
            continue
        safe[clean_key] = _safe_json_value(item)
    return safe


def _safe_json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, tuple):
        return [_safe_json_value(item) for item in value]
    if isinstance(value, list):
        return [_safe_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _safe_json_value(item) for key, item in value.items()}
    return str(value)


def _safe_filename(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())[:80].strip("._")
    return clean or "ai_draft"
