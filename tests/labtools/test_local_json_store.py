from __future__ import annotations

import json
from pathlib import Path

from labtools.local_data.schema_version import LABTOOLS_LOCAL_DATA_STORE_SCHEMA_VERSION
from labtools.local_data.store import LocalLabToolsDataStore


def test_store_initializes_expected_files(tmp_path: Path) -> None:
    store = LocalLabToolsDataStore(tmp_path)
    status = store.initialize_store()

    assert status.status == "ready"
    assert (tmp_path / "labtools_data_store.json").exists()
    assert (tmp_path / "labtools_record_index.json").exists()
    assert (tmp_path / "labtools_audit_log.json").exists()
    assert (tmp_path / "backups").is_dir()
    assert (tmp_path / "exports").is_dir()


def test_store_blocks_corrupt_json_gracefully(tmp_path: Path) -> None:
    store = LocalLabToolsDataStore(tmp_path)
    store.initialize_store()
    (tmp_path / "labtools_data_store.json").write_text("{not-json", encoding="utf-8")

    status = store.get_store_status()

    assert status.status == "blocked_invalid_store"
    assert status.readable is False
    assert "not valid JSON" in status.message


def test_store_blocks_schema_mismatch(tmp_path: Path) -> None:
    store = LocalLabToolsDataStore(tmp_path)
    store.initialize_store()
    path = tmp_path / "labtools_data_store.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["schema_version"] = "wrong"
    path.write_text(json.dumps(payload), encoding="utf-8")

    status = store.get_store_status()

    assert status.status == "blocked_invalid_store"
    assert "schema mismatch" in status.message


def test_store_uses_temp_file_then_atomic_replace(tmp_path: Path) -> None:
    store = LocalLabToolsDataStore(tmp_path)
    store.initialize_store()
    reagent = store.create_reagent({"name": "Tris-HCl"})

    payload = json.loads((tmp_path / "labtools_data_store.json").read_text(encoding="utf-8"))

    assert payload["schema_version"] == LABTOOLS_LOCAL_DATA_STORE_SCHEMA_VERSION
    assert payload["reagents"][0]["id"] == reagent.id
    assert not (tmp_path / ".labtools_data_store.json.tmp").exists()
