from __future__ import annotations

from pathlib import Path

from app.bioinformatics.clinical_analysis import build_survival_package, build_survival_preflight
from app.shared.local_engines import ExternalEngineRegistry


def test_survival_preflight_blocks_missing_event_field(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("case_id\tOS_time\nC1\t10\n", encoding="utf-8")
    package = build_survival_package(
        {
            "input_package_id": "pkg",
            "clinical_asset": {"path": str(clinical)},
            "expression_asset": {"path": "expr.tsv"},
        }
    )

    preflight = build_survival_preflight(package)

    assert "missing_event_field" in preflight["blockers"]
    assert "KM plot" in preflight["forbidden_outputs"]


def test_survival_package_warns_low_event_count_and_requires_grouping(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("case_id\tOS_time\tOS_event\nC1\t10\t1\nC2\t20\t0\n", encoding="utf-8")

    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}}, grouping_policy="")

    assert "low_event_count_for_formal_survival" in package.to_dict()["warnings"]
    assert "expression_grouping_policy_must_be_user_confirmed" in package.to_dict()["blockers"]


def test_survival_preflight_consumes_external_dependency_registry(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("case_id\tOS_time\tOS_event\nC1\t10\t1\nC2\t20\t0\n", encoding="utf-8")
    package = build_survival_package(
        {
            "input_package_id": "pkg",
            "clinical_asset": {"path": str(clinical)},
            "expression_asset": {"path": "expr.tsv"},
        },
        grouping_policy="confirmed",
    )
    registry = ExternalEngineRegistry((_snapshot("python_statistical", "package.python.lifelines.available", "missing"),))

    preflight = build_survival_preflight(package, external_registry=registry)

    assert preflight["dependency_snapshot"]["external_dependency_registry"]["status"] == "checked"
    assert "missing_external_capability:package.python.lifelines.available:missing" in preflight["blockers"]
    assert "Cox hazard ratio" in preflight["forbidden_outputs"]


def _snapshot(engine_family: str, capability_key: str, capability_status: str) -> dict[str, object]:
    return {
        "schema_version": "biomedpilot_external_engine_dependency_snapshot.v1",
        "engine_family": engine_family,
        "engine_name": engine_family,
        "status": "available" if capability_status == "available" else "partially_available",
        "runtime_path": "/usr/bin/env",
        "version": "1.0.0",
        "architecture": "arm64",
        "checked_at": "2026-05-22T00:00:00+00:00",
        "snapshot_path": f"/tmp/{engine_family}_snapshot.json",
        "packages": [
            {
                "name": capability_key,
                "required_for": ["test_runtime"],
                "status": capability_status,
                "version": "1.0.0" if capability_status == "available" else "",
                "minimum_version": "",
                "blocker": None if capability_status == "available" else {"code": "missing_dependency", "message": "missing", "required_by": ["test_runtime"]},
                "capability_key": capability_key,
            }
        ],
        "blockers": [] if capability_status == "available" else [{"code": "missing_dependency", "message": "missing", "required_by": ["test_runtime"]}],
        "install_guidance": {"safe_to_show": True, "commands": [], "manual_steps": []},
    }
