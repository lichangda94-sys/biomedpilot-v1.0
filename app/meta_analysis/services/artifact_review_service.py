from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


TEXT_SUFFIXES = {".csv", ".json", ".jsonl", ".log", ".md", ".txt"}


@dataclass(frozen=True)
class ArtifactPreview:
    requested_path: str
    relative_path: str
    exists: bool
    file_type: str
    size_bytes: int = 0
    preview_text: str = ""
    truncated: bool = False
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResultDetail:
    result_id: str
    result_type: str
    source_path: str
    summary: dict[str, Any]
    linked_artifacts: tuple[ArtifactPreview, ...] = ()
    warnings: tuple[str, ...] = ()


class ArtifactReviewService:
    def preview_project_artifact(self, project_dir: Path, artifact_path: str | Path, *, max_chars: int = 4000) -> ArtifactPreview:
        project_dir = project_dir.expanduser().resolve()
        path, warnings = _resolve_project_path(project_dir, artifact_path)
        relative_path = _relative_or_text(project_dir, path)
        if warnings:
            return ArtifactPreview(
                requested_path=str(artifact_path),
                relative_path=relative_path,
                exists=False,
                file_type=_file_type(path),
                warnings=tuple(warnings),
            )
        if not path.exists():
            return ArtifactPreview(
                requested_path=str(artifact_path),
                relative_path=relative_path,
                exists=False,
                file_type=_file_type(path),
                warnings=("artifact_missing",),
            )
        if path.is_dir():
            return ArtifactPreview(
                requested_path=str(artifact_path),
                relative_path=relative_path,
                exists=True,
                file_type="directory",
                warnings=("artifact_is_directory",),
            )
        size = path.stat().st_size
        suffix = path.suffix.lower()
        if suffix not in TEXT_SUFFIXES:
            return ArtifactPreview(
                requested_path=str(artifact_path),
                relative_path=relative_path,
                exists=True,
                file_type=_file_type(path),
                size_bytes=size,
                warnings=("artifact_preview_unavailable_for_binary",),
            )
        text = path.read_text(encoding="utf-8", errors="replace")
        truncated = len(text) > max_chars
        return ArtifactPreview(
            requested_path=str(artifact_path),
            relative_path=relative_path,
            exists=True,
            file_type=_file_type(path),
            size_bytes=size,
            preview_text=text[:max_chars],
            truncated=truncated,
            warnings=("artifact_preview_truncated",) if truncated else (),
        )

    def get_analysis_result_detail(self, project_dir: Path, result_id: str, *, max_artifact_chars: int = 1200) -> ResultDetail:
        project_dir = project_dir.expanduser().resolve()
        result = self._find_analysis_result(project_dir, result_id)
        if result is None:
            return ResultDetail(
                result_id=result_id,
                result_type="analysis_result",
                source_path=str(project_dir / "analysis" / "analysis_results.json"),
                summary={},
                warnings=("analysis_result_not_found",),
            )
        summary = {
            "dataset_id": str(result.get("dataset_id", "")),
            "profile_type": str(result.get("profile_type", "")),
            "outcome_name": str(result.get("outcome_name", "")),
            "effect_measure": str(result.get("effect_measure", "")),
            "model": str(result.get("model", "")),
            "study_count": len(list(result.get("study_results", []))),
            "pooled_effect": result.get("pooled_effect"),
            "ci_lower": result.get("ci_lower"),
            "ci_upper": result.get("ci_upper"),
            "p_value": result.get("p_value"),
            "warnings": list(result.get("warnings", [])),
        }
        linked_paths = self._linked_artifact_paths(project_dir, result_id)
        linked = tuple(self.preview_project_artifact(project_dir, path, max_chars=max_artifact_chars) for path in linked_paths)
        return ResultDetail(
            result_id=result_id,
            result_type="analysis_result",
            source_path=str(project_dir / "analysis" / "analysis_results.json"),
            summary=summary,
            linked_artifacts=linked,
        )

    def _find_analysis_result(self, project_dir: Path, result_id: str) -> dict[str, Any] | None:
        for path in (project_dir / "analysis" / "analysis_results.json", project_dir / "analysis" / "analysis_result.json"):
            if not path.exists():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            candidates = payload.get("results")
            if not isinstance(candidates, list):
                result = payload.get("result")
                candidates = [result] if isinstance(result, dict) else []
            for item in candidates:
                if isinstance(item, dict) and str(item.get("result_id", "")) == result_id:
                    return item
        return None

    def _linked_artifact_paths(self, project_dir: Path, result_id: str) -> list[str]:
        paths: list[str] = []
        figure_manifest = project_dir / "figures" / "figure_artifacts.json"
        if figure_manifest.exists():
            payload = json.loads(figure_manifest.read_text(encoding="utf-8"))
            for item in payload.get("artifacts", []):
                if isinstance(item, dict) and str(item.get("analysis_result_id", "")) == result_id:
                    file_path = str(item.get("file_path", ""))
                    if file_path:
                        paths.append(file_path)
        for pattern in ("exports/analysis_result_table_*.csv", "figures/forest_plot_*.png", "figures/funnel_plot_*.png"):
            paths.extend(str(path) for path in sorted(project_dir.glob(pattern)))
        return _dedupe(paths)


def _resolve_project_path(project_dir: Path, artifact_path: str | Path) -> tuple[Path, list[str]]:
    raw = Path(artifact_path).expanduser()
    path = raw if raw.is_absolute() else project_dir / raw
    resolved = path.resolve()
    try:
        resolved.relative_to(project_dir)
    except ValueError:
        return resolved, ["artifact_path_outside_project"]
    return resolved, []


def _relative_or_text(project_dir: Path, path: Path) -> str:
    try:
        return str(path.relative_to(project_dir))
    except ValueError:
        return str(path)


def _file_type(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "unknown"


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
