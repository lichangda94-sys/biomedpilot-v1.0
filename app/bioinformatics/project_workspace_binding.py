from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from app.bioinformatics.acquisition_file_records import build_file_record, write_source_manifest
from app.bioinformatics.legacy.geo_processing.module1_contracts import build_download_plan_payload


AcquisitionStrategy = Literal["copy", "reference", "plan_only"]

LATEST_PLAN = "latest_acquisition_plan.json"
LATEST_RECORD = "latest_acquisition_record.json"
LATEST_HANDOFF = "latest_acquisition_handoff.json"


@dataclass(frozen=True)
class AcquisitionSummary:
    acquisition_id: str
    project_root: Path
    source_type: str
    source_label: str
    strategy: AcquisitionStrategy
    created_at: str
    status: str
    plan_path: Path
    record_path: Path
    handoff_path: Path
    source_files: tuple[str, ...]
    registered_files: tuple[str, ...]
    copied_files: tuple[str, ...]
    referenced_paths: tuple[str, ...]
    warnings: tuple[str, ...]


def register_acquisition(
    project_root: str | Path,
    *,
    source_type: str,
    source_label: str,
    strategy: AcquisitionStrategy,
    selected_paths: list[str | Path] | None = None,
    metadata: dict[str, object] | None = None,
    file_records: list[dict[str, object]] | None = None,
) -> AcquisitionSummary:
    root = Path(project_root).expanduser().resolve()
    _ensure_acquisition_dirs(root)
    acquisition_id = f"acq-{uuid4().hex[:8]}"
    created_at = _now()
    selected = [Path(path).expanduser().resolve() for path in selected_paths or []]
    warnings: list[str] = []
    copied_files: list[str] = []
    referenced_paths: list[str] = []
    registered_files: list[str] = []

    if strategy == "copy":
        target_root = _raw_target_root(root, source_type) / acquisition_id
        target_root.mkdir(parents=True, exist_ok=True)
        for source in selected:
            if not source.exists():
                warnings.append(f"missing_selected_path:{source}")
                continue
            registered_files.append(str(source))
            copied_files.extend(_copy_selected_path(source, target_root))
    elif strategy == "reference":
        for source in selected:
            if not source.exists():
                warnings.append(f"missing_selected_path:{source}")
            registered_files.append(str(source))
            referenced_paths.append(str(source))
    elif strategy == "plan_only":
        registered_files = [str(path) for path in selected]
    else:
        raise ValueError(f"Unsupported acquisition strategy: {strategy}")

    metadata = dict(metadata or {})
    file_record_paths = copied_files if strategy == "copy" else referenced_paths if strategy == "reference" else []
    normalized_file_records = list(file_records or [])
    if not normalized_file_records:
        normalized_file_records = [
            build_file_record(
                path,
                source=source_type,
                role=_file_role_from_source_type(source_type),
                status="copied" if strategy == "copy" else "referenced",
                source_path=_source_path_for_record(path, selected),
            )
            for path in file_record_paths
        ]
    if normalized_file_records and not metadata.get("source_manifest_path"):
        manifest_path = root / "acquisition" / "source_manifests" / f"{acquisition_id}_source_manifest.json"
        manifest = write_source_manifest(
            manifest_path,
            acquisition_id=acquisition_id,
            source_type=source_type,
            source_label=source_label,
            source=source_type,
            file_records=normalized_file_records,
            receipt_path=str(metadata.get("download_receipt_path") or ""),
            request_path=str(metadata.get("download_request_path") or ""),
        )
        metadata["source_manifest_path"] = str(manifest_path)
        metadata["file_records_summary"] = manifest.get("summary", {})
    elif normalized_file_records and metadata.get("file_records_summary") is None:
        metadata["file_records_summary"] = {
            "file_count": len(normalized_file_records),
            "real_file_count": len(normalized_file_records),
        }

    plan = _build_plan(root, acquisition_id, source_type, source_label, strategy, selected, metadata)
    record = {
        "schema_version": "biomedpilot.acquisition_record.v1",
        "acquisition_id": acquisition_id,
        "source_type": source_type,
        "source_label": source_label,
        "strategy": strategy,
        "created_at": created_at,
        "status": "planned" if strategy == "plan_only" else "registered",
        "source_files": registered_files,
        "registered_files": registered_files,
        "copied_files": copied_files,
        "referenced_paths": referenced_paths,
        "warnings": warnings,
        "metadata": metadata,
    }
    handoff = {
        "schema_version": "biomedpilot.acquisition_handoff.v1",
        "acquisition_id": acquisition_id,
        "source_type": source_type,
        "source_label": source_label,
        "strategy": strategy,
        "created_at": created_at,
        "next_stage": "data_recognition" if strategy != "plan_only" and not warnings else "complete_acquisition_inputs",
        "raw_data_locations": _raw_locations(root),
        "source_files": registered_files,
        "registered_files": registered_files,
        "copied_files": copied_files,
        "referenced_paths": referenced_paths,
        "warnings": warnings,
        "requires_user_files": strategy == "plan_only",
    }

    plan_path = root / "acquisition" / "plans" / LATEST_PLAN
    record_path = root / "acquisition" / "records" / LATEST_RECORD
    handoff_path = root / "acquisition" / "handoffs" / LATEST_HANDOFF
    _write_json(plan_path, plan)
    _write_json(record_path, record)
    _write_json(handoff_path, handoff)
    _write_json(root / "acquisition" / "plans" / f"{acquisition_id}.json", plan)
    _write_json(root / "acquisition" / "records" / f"{acquisition_id}.json", record)
    _write_json(root / "acquisition" / "handoffs" / f"{acquisition_id}.json", handoff)
    return acquisition_summary_from_payload(root, plan_path, record_path, handoff_path, record)


def generate_gse_acquisition_plan(project_root: str | Path, gse_id: str) -> AcquisitionSummary:
    cleaned = gse_id.strip().upper()
    return register_acquisition(
        project_root,
        source_type="geo_gse",
        source_label=cleaned or "GSE 未填写",
        strategy="plan_only",
        selected_paths=[],
        metadata={"gse_id": cleaned},
    )


def load_latest_acquisition_summary(project_root: str | Path) -> AcquisitionSummary | None:
    root = Path(project_root).expanduser().resolve()
    plan_path = root / "acquisition" / "plans" / LATEST_PLAN
    record_path = root / "acquisition" / "records" / LATEST_RECORD
    handoff_path = root / "acquisition" / "handoffs" / LATEST_HANDOFF
    if not record_path.exists():
        return None
    record = _read_json(record_path)
    return acquisition_summary_from_payload(root, plan_path, record_path, handoff_path, record)


def read_acquisition_artifacts(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    artifacts = {}
    for key, path in {
        "plan": root / "acquisition" / "plans" / LATEST_PLAN,
        "record": root / "acquisition" / "records" / LATEST_RECORD,
        "handoff": root / "acquisition" / "handoffs" / LATEST_HANDOFF,
    }.items():
        artifacts[key] = _read_json(path) if path.exists() else None
        artifacts[f"{key}_path"] = str(path)
    return artifacts


def acquisition_summary_from_payload(
    root: Path,
    plan_path: Path,
    record_path: Path,
    handoff_path: Path,
    record: dict[str, object],
) -> AcquisitionSummary:
    return AcquisitionSummary(
        acquisition_id=str(record.get("acquisition_id") or "unknown"),
        project_root=root,
        source_type=str(record.get("source_type") or "unknown"),
        source_label=str(record.get("source_label") or "未知数据来源"),
        strategy=str(record.get("strategy") or "plan_only"),  # type: ignore[arg-type]
        created_at=str(record.get("created_at") or "未记录"),
        status=str(record.get("status") or "unknown"),
        plan_path=plan_path,
        record_path=record_path,
        handoff_path=handoff_path,
        source_files=tuple(str(item) for item in record.get("source_files", record.get("registered_files", [])) or []),
        registered_files=tuple(str(item) for item in record.get("registered_files", []) or []),
        copied_files=tuple(str(item) for item in record.get("copied_files", []) or []),
        referenced_paths=tuple(str(item) for item in record.get("referenced_paths", []) or []),
        warnings=tuple(str(item) for item in record.get("warnings", []) or []),
    )


def _build_plan(
    root: Path,
    acquisition_id: str,
    source_type: str,
    source_label: str,
    strategy: AcquisitionStrategy,
    selected: list[Path],
    metadata: dict[str, object],
) -> dict[str, object]:
    if source_type == "geo_gse":
        gse_id = str(metadata.get("gse_id") or source_label).strip().upper()
        plan = build_download_plan_payload(
            gse_id,
            str(_raw_target_root(root, "geo")),
            [
                {
                    "step": "manual_or_future_download",
                    "gse_id": gse_id,
                    "note": "Developer Preview 仅生成 acquisition plan，不强制联网下载。",
                }
            ],
        )
        plan["acquisition_id"] = acquisition_id
        plan["strategy"] = strategy
        return plan
    return {
        "schema_version": "biomedpilot.acquisition_plan.v1",
        "acquisition_id": acquisition_id,
        "source_type": source_type,
        "source_label": source_label,
        "strategy": strategy,
        "generated_at": _now(),
        "selected_paths": [str(path) for path in selected],
        "planned_actions": ["register_local_inputs"],
        "requires_network": False,
        "metadata": metadata,
    }


def _copy_selected_path(source: Path, target_root: Path) -> list[str]:
    copied: list[str] = []
    if source.is_file():
        target = target_root / source.name
        shutil.copy2(source, target)
        copied.append(str(target))
    elif source.is_dir():
        target = target_root / source.name
        if target.exists():
            target = target_root / f"{source.name}-{uuid4().hex[:6]}"
        shutil.copytree(source, target)
        copied.extend(str(path) for path in target.rglob("*") if path.is_file())
    return copied


def _ensure_acquisition_dirs(root: Path) -> None:
    for relative in ("acquisition/plans", "acquisition/handoffs", "acquisition/records", "acquisition/source_manifests"):
        (root / relative).mkdir(parents=True, exist_ok=True)
    for relative in ("raw_data/local_import", "raw_data/geo", "raw_data/tcga", "raw_data/gtex"):
        (root / relative).mkdir(parents=True, exist_ok=True)


def _raw_target_root(root: Path, source_type: str) -> Path:
    if "tcga" in source_type and "gtex" not in source_type:
        return root / "raw_data" / "tcga"
    if "gtex" in source_type and "tcga" not in source_type:
        return root / "raw_data" / "gtex"
    if "geo" in source_type:
        return root / "raw_data" / "geo"
    return root / "raw_data" / "local_import"


def _raw_locations(root: Path) -> dict[str, str]:
    return {
        "local_import": str(root / "raw_data" / "local_import"),
        "geo": str(root / "raw_data" / "geo"),
        "tcga": str(root / "raw_data" / "tcga"),
        "gtex": str(root / "raw_data" / "gtex"),
    }


def _file_role_from_source_type(source_type: str) -> str:
    if "geo" in source_type:
        return "geo_acquisition_file"
    if "tcga" in source_type:
        return "tcga_acquisition_file"
    if "gtex" in source_type:
        return "gtex_acquisition_file"
    return "local_import_file"


def _source_path_for_record(local_path: str, selected: list[Path]) -> str:
    path = Path(local_path)
    for source in selected:
        if source.is_file() and source.name == path.name:
            return str(source)
        if source.is_dir() and path.name:
            return str(source)
    return str(path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
