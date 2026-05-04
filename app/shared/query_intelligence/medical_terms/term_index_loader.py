from __future__ import annotations

import json
import sqlite3
from functools import lru_cache
from pathlib import Path

from .term_index_models import TermConcept

SQLITE_SCHEMA_VERSION = "biomedpilot.medical_terms.sqlite.v6"


def default_mini_index_path() -> Path:
    return Path(__file__).resolve().parents[4] / "data" / "medical_terms" / "mini_medical_terms_index.json"


def default_full_index_path() -> Path:
    return Path(__file__).resolve().parents[4] / "data" / "medical_terms" / "medical_terms_index.sqlite"


@lru_cache(maxsize=4)
def load_mini_term_index(path: str | None = None) -> tuple[TermConcept, ...]:
    resolved = Path(path) if path else default_mini_index_path()
    if not resolved.exists():
        return ()
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except Exception:
        return ()
    if not isinstance(payload, list):
        return ()
    return tuple(TermConcept.from_dict(item) for item in payload if isinstance(item, dict))


@lru_cache(maxsize=4)
def load_full_term_index(path: str | None = None) -> tuple[TermConcept, ...]:
    resolved = Path(path) if path else default_full_index_path()
    if not resolved.exists():
        return ()
    try:
        with sqlite3.connect(str(resolved)) as conn:
            conn.row_factory = sqlite3.Row
            if not _schema_is_supported(conn):
                return ()
            rows = conn.execute("SELECT payload_json FROM ontology_terms WHERE is_active = 1").fetchall()
    except Exception:
        return ()
    concepts: list[TermConcept] = []
    for row in rows:
        try:
            payload = json.loads(str(row["payload_json"]))
        except Exception:
            continue
        if isinstance(payload, dict):
            concepts.append(TermConcept.from_dict(payload))
    return tuple(concepts)


def active_index_status() -> dict[str, object]:
    full_path = default_full_index_path()
    mini_path = default_mini_index_path()
    return {
        "medical_terms_index_scope": "BioMedPilot shared medical vocabulary",
        "full_index_path": str(full_path),
        "full_index_available": full_path.exists(),
        "full_index_schema_version": SQLITE_SCHEMA_VERSION if full_path.exists() else "",
        "mini_index_path": str(mini_path),
        "mini_index_available": mini_path.exists(),
        "runtime_load_order": [
            "zh_term_overrides.json",
            "medical_terms_index.sqlite if present",
            "mini_medical_terms_index.json",
            "biomedical_term_registry",
        ],
    }


def _schema_is_supported(conn: sqlite3.Connection) -> bool:
    try:
        row = conn.execute(
            """
            SELECT schema_version
            FROM ontology_build_metadata
            ORDER BY build_time DESC
            LIMIT 1
            """
        ).fetchone()
    except Exception:
        return False
    return bool(row and row["schema_version"] == SQLITE_SCHEMA_VERSION)


def _row_payload(row: sqlite3.Row) -> dict[str, object]:
    payload = dict(row)
    for key in (
        "synonyms_en",
        "exact_synonyms_en",
        "related_synonyms_en",
        "abbreviations",
        "mesh_terms",
        "parent_terms",
        "normalized_terms",
    ):
        payload[key] = _json_list(payload.get(key))
    payload["cross_refs"] = _json_dict(payload.get("cross_refs"))
    return payload


def _json_list(value: object) -> list[str]:
    if value in (None, ""):
        return []
    try:
        payload = json.loads(str(value))
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [str(item) for item in payload if str(item).strip()]


def _json_dict(value: object) -> dict[str, list[str]]:
    if value in (None, ""):
        return {}
    try:
        payload = json.loads(str(value))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {str(key): _json_list(json.dumps(items)) for key, items in payload.items()}
