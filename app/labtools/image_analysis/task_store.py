from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.labtools.image_analysis.analysis_task import ImageAnalysisTask, create_experiment_image_analysis_task
from app.labtools.image_analysis.image_io import create_image_record
from app.labtools.image_analysis.image_models import ImageAnalysisError, LabImageRecord, utc_timestamp
from app.labtools.image_analysis.macro_registry import MacroTemplate, default_macro_for_analysis
from app.labtools.image_analysis.run_request import ImageAnalysisRunRequest, create_run_request, save_run_request
from app.shared.storage import default_storage_root


IMAGE_IMPORT_MODES = ("reference_original_path", "copy_to_task_workspace")
TASK_MANIFEST_SCHEMA_VERSION = "labtools_image_analysis_task_manifest.v1"


@dataclass(frozen=True)
class ImageManifestEntry:
    image_id: str
    file_name: str
    original_path: str
    task_path: str
    file_format: str
    image_width: int | None = None
    image_height: int | None = None
    group: str = ""
    time_point: str = ""
    notes: str = ""
    imported_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id,
            "file_name": self.file_name,
            "original_path": self.original_path,
            "task_path": self.task_path,
            "file_format": self.file_format,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "group": self.group,
            "time_point": self.time_point,
            "notes": self.notes,
            "imported_at": self.imported_at,
        }


@dataclass(frozen=True)
class ImageAnalysisTaskWorkspace:
    task: ImageAnalysisTask
    macro_template: MacroTemplate
    task_dir: Path
    image_manifest_path: Path
    task_manifest_path: Path
    selected_macro_path: Path
    generated_parameters_path: Path
    run_request_path: Path
    output_dir: Path
    log_dir: Path
    review_dir: Path
    image_manifest_entries: tuple[ImageManifestEntry, ...]
    run_request: ImageAnalysisRunRequest | None = None


def default_image_analysis_tasks_root() -> Path:
    return default_storage_root() / "labtools" / "image_analysis_tasks"


class ImageAnalysisTaskStore:
    def __init__(self, root: str | Path | None = None) -> None:
        self._root = Path(root) if root is not None else default_image_analysis_tasks_root()

    @property
    def root(self) -> Path:
        return self._root

    def create_workspace(
        self,
        *,
        task_name: str,
        experiment_module: str,
        analysis_type: str,
        image_paths: tuple[str, ...] | list[str],
        import_mode: str = "reference_original_path",
        parameters: dict[str, Any] | None = None,
        notes: str = "",
    ) -> ImageAnalysisTaskWorkspace:
        if import_mode not in IMAGE_IMPORT_MODES:
            raise ImageAnalysisError(f"暂不支持该图片导入模式：{import_mode}")
        macro_template = default_macro_for_analysis(experiment_module, analysis_type)
        records = tuple(create_image_record(path, image_role=analysis_type) for path in image_paths)
        task = create_experiment_image_analysis_task(
            task_name=task_name,
            experiment_module=experiment_module,
            analysis_type=analysis_type,
            image_records=records,
            import_mode=import_mode,
            parameters=parameters or {},
            selected_macro_id=macro_template.macro_id,
            macro_template_path=macro_template.macro_file_path,
            notes=notes,
        )
        task_dir = self._root / task.task_id
        inputs_dir = task_dir / "inputs"
        macros_dir = task_dir / "macros"
        output_dir = task_dir / "outputs"
        log_dir = task_dir / "logs"
        review_dir = task_dir / "review"
        for directory in (inputs_dir, macros_dir, output_dir / "processed_images", log_dir, review_dir):
            directory.mkdir(parents=True, exist_ok=True)
        entries = self._write_image_manifest(records, inputs_dir, import_mode)
        selected_macro_path = macros_dir / "selected_macro.ijm"
        shutil.copyfile(macro_template.path, selected_macro_path)
        generated_parameters_path = macros_dir / "generated_parameters.json"
        generated_parameters_path.write_text(json.dumps(parameters or {}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        task = task.with_workspace(
            task_workspace=str(task_dir),
            output_dir=str(output_dir),
            source_image_paths=tuple(entry.task_path or entry.original_path for entry in entries),
            macro_template_path=str(selected_macro_path),
            status="ready_to_run",
        )
        task_manifest_path = task_dir / "task_manifest.json"
        self._write_task_manifest(task, task_manifest_path)
        return ImageAnalysisTaskWorkspace(
            task=task,
            macro_template=macro_template,
            task_dir=task_dir,
            image_manifest_path=inputs_dir / "image_manifest.json",
            task_manifest_path=task_manifest_path,
            selected_macro_path=selected_macro_path,
            generated_parameters_path=generated_parameters_path,
            run_request_path=log_dir / "run_request.json",
            output_dir=output_dir,
            log_dir=log_dir,
            review_dir=review_dir,
            image_manifest_entries=entries,
        )

    def create_run_request(self, workspace: ImageAnalysisTaskWorkspace) -> ImageAnalysisTaskWorkspace:
        request = create_run_request(
            task_id=workspace.task.task_id,
            analysis_type=workspace.task.analysis_type,
            macro_template=workspace.macro_template,
            input_images=workspace.task.source_image_paths,
            output_dir=workspace.output_dir,
            parameters=workspace.task.parameters,
        )
        save_run_request(request, workspace.run_request_path)
        task = workspace.task.with_workspace(status="run_request_created")
        self._write_task_manifest(task, workspace.task_manifest_path)
        return ImageAnalysisTaskWorkspace(
            task=task,
            macro_template=workspace.macro_template,
            task_dir=workspace.task_dir,
            image_manifest_path=workspace.image_manifest_path,
            task_manifest_path=workspace.task_manifest_path,
            selected_macro_path=workspace.selected_macro_path,
            generated_parameters_path=workspace.generated_parameters_path,
            run_request_path=workspace.run_request_path,
            output_dir=workspace.output_dir,
            log_dir=workspace.log_dir,
            review_dir=workspace.review_dir,
            image_manifest_entries=workspace.image_manifest_entries,
            run_request=request,
        )

    def _write_image_manifest(
        self,
        records: tuple[LabImageRecord, ...],
        inputs_dir: Path,
        import_mode: str,
    ) -> tuple[ImageManifestEntry, ...]:
        entries: list[ImageManifestEntry] = []
        for record in records:
            original = Path(record.source_path)
            task_path = ""
            if import_mode == "copy_to_task_workspace":
                destination = inputs_dir / record.filename
                shutil.copyfile(original, destination)
                task_path = str(destination)
            entries.append(
                ImageManifestEntry(
                    image_id=record.image_id,
                    file_name=record.filename,
                    original_path=record.source_path,
                    task_path=task_path,
                    file_format=record.file_extension,
                    notes=record.notes,
                    imported_at=record.imported_at or utc_timestamp(),
                )
            )
        manifest_path = inputs_dir / "image_manifest.json"
        manifest_path.write_text(
            json.dumps({"schema_version": TASK_MANIFEST_SCHEMA_VERSION, "images": [entry.to_dict() for entry in entries]}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return tuple(entries)

    def _write_task_manifest(self, task: ImageAnalysisTask, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"schema_version": TASK_MANIFEST_SCHEMA_VERSION, "task": task.to_dict()}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path
