from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.labtools.image_analysis.image_models import utc_timestamp
from app.labtools.image_analysis.macro_registry import MacroTemplate


IMAGE_ANALYSIS_RUN_REQUEST_SCHEMA_VERSION = "labtools_image_analysis_run_request.v1"
IMAGE_ANALYSIS_ENGINE_KEY = "imagej"


@dataclass(frozen=True)
class ImageAnalysisRunRequest:
    task_id: str
    analysis_type: str
    macro_id: str
    macro_path: str
    input_images: tuple[str, ...]
    output_dir: str
    parameters: dict[str, Any]
    created_at: str = field(default_factory=utc_timestamp)
    engine_key: str = IMAGE_ANALYSIS_ENGINE_KEY
    minimum_engine_requirement: str = IMAGE_ANALYSIS_ENGINE_KEY
    request_id: str = field(default_factory=lambda: f"image_run_request_{uuid4().hex[:12]}")
    schema_version: str = IMAGE_ANALYSIS_RUN_REQUEST_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "task_id": self.task_id,
            "analysis_type": self.analysis_type,
            "macro_id": self.macro_id,
            "macro_path": self.macro_path,
            "input_images": list(self.input_images),
            "output_dir": self.output_dir,
            "parameters": dict(self.parameters),
            "created_at": self.created_at,
            "engine_key": self.engine_key,
            "minimum_engine_requirement": self.minimum_engine_requirement,
        }


def create_run_request(
    *,
    task_id: str,
    analysis_type: str,
    macro_template: MacroTemplate,
    input_images: tuple[str, ...] | list[str],
    output_dir: str | Path,
    parameters: dict[str, Any],
) -> ImageAnalysisRunRequest:
    return ImageAnalysisRunRequest(
        task_id=task_id,
        analysis_type=analysis_type,
        macro_id=macro_template.macro_id,
        macro_path=macro_template.macro_file_path,
        input_images=tuple(str(path) for path in input_images),
        output_dir=str(output_dir),
        parameters=dict(parameters),
        minimum_engine_requirement=macro_template.minimum_engine_requirement,
    )


def save_run_request(request: ImageAnalysisRunRequest, path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(request.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved
