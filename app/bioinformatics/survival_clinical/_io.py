from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def asset_path(asset: dict[str, Any] | None) -> Path | None:
    if not isinstance(asset, dict):
        return None
    text = str(asset.get("path") or asset.get("file_path") or "")
    return Path(text).expanduser() if text else None


def read_table(path: str | Path | None) -> list[dict[str, str]]:
    if path is None:
        return []
    table_path = Path(path).expanduser()
    if not table_path.is_file():
        return []
    try:
        first = table_path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except (IndexError, OSError):
        return []
    delimiter = "," if first.count(",") > first.count("\t") else "\t"
    with table_path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter=delimiter)]


def write_table(path: str | Path, rows: list[dict[str, Any]], columns: list[str]) -> Path:
    output = Path(path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    delimiter = "," if output.suffix.lower() == ".csv" else "\t"
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter=delimiter, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
    return output


def sample_id(row: dict[str, Any]) -> str:
    for key in ("sample_id", "barcode", "tcga_barcode", "patient_barcode", "case_id", "participant_barcode"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


def event_observed(value: object, event_coding: dict[str, Any] | None = None) -> bool | None:
    text = str(value or "").strip()
    if text == "":
        return None
    status = str((event_coding or {}).get("status") or "")
    if status == "binary_0_censored_1_event" or text in {"0", "1"}:
        return text == "1"
    lowered = text.lower()
    if lowered in {"dead", "event"}:
        return True
    if lowered in {"alive", "censored"}:
        return False
    return None


def parse_float(value: object) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None
