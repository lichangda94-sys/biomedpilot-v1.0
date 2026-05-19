from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


REQUEST_INDEX = Path("manifests") / "data_source_requests.json"
REQUEST_DIR = Path("manifests") / "data_source_requests"


@dataclass(frozen=True)
class BioinformaticsDataSourceRequest:
    request_id: str
    source_type: str
    user_title: str
    user_selection_summary: str
    internal_selection: dict[str, object]
    expected_assets: tuple[str, ...]
    actual_assets: tuple[str, ...] = ()
    status: str = "draft"
    warnings: tuple[str, ...] = ()
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["expected_assets"] = list(self.expected_assets)
        payload["actual_assets"] = list(self.actual_assets)
        payload["warnings"] = list(self.warnings)
        return payload


@dataclass(frozen=True)
class DataSourceRequestDraft:
    request: BioinformaticsDataSourceRequest
    request_path: Path
    index_path: Path


def create_data_source_request(
    project_root: str | Path,
    *,
    source_type: str,
    user_title: str,
    user_selection_summary: str,
    internal_selection: dict[str, object],
    expected_assets: tuple[str, ...] | list[str],
    warnings: tuple[str, ...] | list[str] = (),
    status: str = "draft",
) -> DataSourceRequestDraft:
    root = Path(project_root).expanduser().resolve()
    now = _now()
    request = BioinformaticsDataSourceRequest(
        request_id=f"dsr-{uuid4().hex[:10]}",
        source_type=source_type,
        user_title=user_title,
        user_selection_summary=user_selection_summary,
        internal_selection=dict(internal_selection),
        expected_assets=tuple(expected_assets),
        actual_assets=(),
        status=status,
        warnings=tuple(warnings),
        created_at=now,
        updated_at=now,
    )
    request_path = root / REQUEST_DIR / f"{request.request_id}.json"
    index_path = root / REQUEST_INDEX
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(json.dumps(request.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    index = _read_json(index_path) if index_path.exists() else {"schema_version": "biomedpilot.data_source_requests.v1", "requests": []}
    requests = [item for item in index.get("requests", []) if isinstance(item, dict)]
    requests.append({**request.to_dict(), "request_path": str(request_path)})
    index["requests"] = requests
    index["updated_at"] = now
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return DataSourceRequestDraft(request=request, request_path=request_path, index_path=index_path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))
