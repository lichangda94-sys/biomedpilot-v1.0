from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


LABTOOLS_STORAGE_DIRECTORY_NAMES = ("templates", "records", "exports", "attachments", "diagnostics")


@dataclass(frozen=True)
class LabToolsStoragePaths:
    project_root: Path
    project_storage_root: Path
    labtools_root: Path
    templates: Path
    records: Path
    exports: Path
    attachments: Path
    diagnostics: Path

    @property
    def required_directories(self) -> tuple[Path, ...]:
        return (
            self.project_storage_root,
            self.labtools_root,
            self.templates,
            self.records,
            self.exports,
            self.attachments,
            self.diagnostics,
        )


@dataclass(frozen=True)
class LabToolsStorageAdapterError:
    severity: str
    code: str
    user_message: str
    technical_detail: str = ""
    affected_path: Path | None = None
    suggested_action: str = ""
    blocking: bool = True


@dataclass(frozen=True)
class LabToolsStorageAdapterState:
    status: str
    message: str
    paths: LabToolsStoragePaths | None
    errors: tuple[LabToolsStorageAdapterError, ...] = ()
    save_enabled: bool = False
    export_enabled: bool = False
    history_enabled: bool = False
    created_paths: tuple[Path, ...] = ()


class BioMedPilotLabToolsStorageAdapter:
    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root).expanduser().resolve()

    @classmethod
    def from_project_root(cls, project_root: Path | str) -> "BioMedPilotLabToolsStorageAdapter":
        return cls(Path(project_root))

    def resolve_paths(self) -> LabToolsStoragePaths:
        project_storage_root = self.project_root / "project_storage"
        labtools_root = project_storage_root / "labtools"
        return LabToolsStoragePaths(
            project_root=self.project_root,
            project_storage_root=project_storage_root,
            labtools_root=labtools_root,
            templates=labtools_root / "templates",
            records=labtools_root / "records",
            exports=labtools_root / "exports",
            attachments=labtools_root / "attachments",
            diagnostics=labtools_root / "diagnostics",
        )

    def diagnose(self) -> LabToolsStorageAdapterState:
        paths = self.resolve_paths()
        missing = tuple(path for path in paths.required_directories if not path.exists())
        not_directories = tuple(path for path in paths.required_directories if path.exists() and not path.is_dir())

        if not_directories:
            errors = tuple(
                LabToolsStorageAdapterError(
                    severity="error",
                    code="path_not_directory",
                    user_message="LabTools storage path exists but is not a directory.",
                    technical_detail=f"{path} is not a directory.",
                    affected_path=path,
                    suggested_action="Choose a valid BioMedPilot project or repair the project_storage layout.",
                    blocking=True,
                )
                for path in not_directories
            )
            return self._state(
                status="blocked_invalid_storage_path",
                message="LabTools project_storage contains invalid paths.",
                paths=paths,
                errors=errors,
            )

        if not paths.project_storage_root.exists():
            return self._state(
                status="missing_project_storage",
                message="BioMedPilot project_storage is not present; LabTools save/export/history remain disabled.",
                paths=paths,
                errors=(
                    LabToolsStorageAdapterError(
                        severity="warning",
                        code="missing_project_storage",
                        user_message="Project storage has not been initialized.",
                        technical_detail=str(paths.project_storage_root),
                        affected_path=paths.project_storage_root,
                        suggested_action="Open a BioMedPilot project with initialized project_storage before enabling LabTools persistence.",
                        blocking=True,
                    ),
                ),
            )

        if missing:
            return self._state(
                status="missing_labtools_storage_dirs",
                message="LabTools project_storage directories are missing; save/export/history remain disabled.",
                paths=paths,
                errors=tuple(
                    LabToolsStorageAdapterError(
                        severity="warning",
                        code="missing_labtools_storage_dir",
                        user_message="A LabTools storage directory is missing.",
                        technical_detail=str(path),
                        affected_path=path,
                        suggested_action="Create the LabTools storage layout only through an explicit storage-adapter initialization step.",
                        blocking=True,
                    )
                    for path in missing
                ),
            )

        return self._state(
            status="ready_read_only",
            message="LabTools project_storage layout is present; persistence actions remain disabled until write adapters are enabled.",
            paths=paths,
        )

    def ensure_readiness(self, create_missing: bool = False) -> LabToolsStorageAdapterState:
        if not create_missing:
            return self.diagnose()

        paths = self.resolve_paths()
        created: list[Path] = []
        for path in paths.required_directories:
            if not self._is_within_project_root(path):
                return self._state(
                    status="blocked_path_outside_project_root",
                    message="Refusing to create LabTools storage outside the BioMedPilot project root.",
                    paths=paths,
                    errors=(
                        LabToolsStorageAdapterError(
                            severity="error",
                            code="path_outside_project_root",
                            user_message="Resolved LabTools storage path is outside the project root.",
                            technical_detail=str(path),
                            affected_path=path,
                            suggested_action="Use a valid BioMedPilot project root.",
                            blocking=True,
                        ),
                    ),
                )
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    return self._state(
                        status="blocked_permission_error",
                        message="Unable to initialize LabTools storage directories.",
                        paths=paths,
                        errors=(
                            LabToolsStorageAdapterError(
                                severity="error",
                                code="storage_directory_create_failed",
                                user_message="Could not create LabTools storage directory.",
                                technical_detail=str(exc),
                                affected_path=path,
                                suggested_action="Check filesystem permissions and choose a writable project location.",
                                blocking=True,
                            ),
                        ),
                    )
                created.append(path)

        state = self.diagnose()
        return LabToolsStorageAdapterState(
            status=state.status,
            message=state.message,
            paths=state.paths,
            errors=state.errors,
            save_enabled=False,
            export_enabled=False,
            history_enabled=False,
            created_paths=tuple(created),
        )

    def _is_within_project_root(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.project_root)
        except ValueError:
            return False
        return True

    @staticmethod
    def _state(
        *,
        status: str,
        message: str,
        paths: LabToolsStoragePaths | None,
        errors: tuple[LabToolsStorageAdapterError, ...] = (),
    ) -> LabToolsStorageAdapterState:
        return LabToolsStorageAdapterState(
            status=status,
            message=message,
            paths=paths,
            errors=errors,
            save_enabled=False,
            export_enabled=False,
            history_enabled=False,
        )
