from __future__ import annotations

from app.bioinformatics.results.migration import migrate_legacy_result_entry


def test_formal_legacy_result_requires_input_package_for_upgrade() -> None:
    migrated = migrate_legacy_result_entry({"result_id": "old", "formal_deg_executed": True})

    assert migrated["result_semantics"] == "testing_level"
    assert migrated["migration_status"] == "legacy_unverified"
