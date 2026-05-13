from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_SAMPLE_PROJECTS_DIR = Path("examples/meta_analysis_internal_beta_samples")


@dataclass(frozen=True)
class InternalBetaSampleProject:
    sample_id: str
    title: str
    meta_analysis_type: str
    input_files: list[str]
    expected_import_count: int
    expected_duplicate_count: int
    expected_screening_status: dict[str, int]
    expected_extraction: dict[str, Any]
    expected_analysis_result: dict[str, Any]
    known_limitations: list[str] = field(default_factory=list)
    sample_dir: str = ""


@dataclass(frozen=True)
class SampleProjectValidationResult:
    sample_id: str
    valid: bool
    warnings: list[str]
    errors: list[str]


class InternalBetaSampleProjectService:
    def __init__(self, *, samples_root: Path | None = None) -> None:
        self._samples_root = samples_root or DEFAULT_SAMPLE_PROJECTS_DIR

    def list_sample_projects(self, repo_root: Path) -> list[InternalBetaSampleProject]:
        root = (repo_root / self._samples_root).expanduser().resolve()
        samples: list[InternalBetaSampleProject] = []
        if not root.exists():
            return []
        for manifest_path in sorted(root.glob("*/expected_manifest.json")):
            samples.append(self._sample_from_manifest(manifest_path))
        return samples

    def validate_sample_project(self, repo_root: Path, sample_id: str) -> SampleProjectValidationResult:
        samples = {sample.sample_id: sample for sample in self.list_sample_projects(repo_root)}
        sample = samples.get(sample_id)
        if sample is None:
            return SampleProjectValidationResult(sample_id=sample_id, valid=False, warnings=[], errors=["sample_project_missing"])
        sample_dir = Path(sample.sample_dir)
        warnings: list[str] = []
        errors: list[str] = []
        for relative in sample.input_files:
            if not (sample_dir / relative).exists():
                errors.append(f"sample_input_missing:{relative}")
        if sample.expected_import_count <= 0:
            errors.append("expected_import_count_must_be_positive")
        if sample.expected_duplicate_count < 0:
            errors.append("expected_duplicate_count_cannot_be_negative")
        if not sample.expected_extraction:
            warnings.append("expected_extraction_seed_missing")
        if not sample.expected_analysis_result:
            warnings.append("expected_analysis_result_missing")
        if _contains_generated_output_reference(sample):
            errors.append("sample_manifest_references_generated_output")
        return SampleProjectValidationResult(sample_id=sample.sample_id, valid=not errors, warnings=warnings, errors=errors)

    def _sample_from_manifest(self, manifest_path: Path) -> InternalBetaSampleProject:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        return InternalBetaSampleProject(
            sample_id=str(payload.get("sample_id", manifest_path.parent.name)),
            title=str(payload.get("title", "")),
            meta_analysis_type=str(payload.get("meta_analysis_type", "")),
            input_files=[str(item) for item in payload.get("input_files", [])],
            expected_import_count=int(payload.get("expected_import_count", 0)),
            expected_duplicate_count=int(payload.get("expected_duplicate_count", 0)),
            expected_screening_status={str(key): int(value) for key, value in dict(payload.get("expected_screening_status", {})).items()},
            expected_extraction=dict(payload.get("expected_extraction", {})),
            expected_analysis_result=dict(payload.get("expected_analysis_result", {})),
            known_limitations=[str(item) for item in payload.get("known_limitations", [])],
            sample_dir=str(manifest_path.parent),
        )


def _contains_generated_output_reference(sample: InternalBetaSampleProject) -> bool:
    generated_markers = (".zip", "formal_meta_report", "forest_plot_", "funnel_plot_", "reproducibility_package")
    values = [*sample.input_files, *sample.known_limitations]
    values.extend(str(value) for value in sample.expected_analysis_result.values())
    return any(marker in value for value in values for marker in generated_markers)
