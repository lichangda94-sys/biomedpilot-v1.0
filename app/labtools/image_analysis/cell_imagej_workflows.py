from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from app.labtools.image_analysis.image_models import ImageAnalysisError


class CellImageJWorkflowError(ImageAnalysisError):
    """Raised when a LabTools cell ImageJ workflow cannot be prepared."""


class CellImageJNotFoundError(CellImageJWorkflowError):
    """Raised when no usable ImageJ/Fiji executable can be resolved."""


@dataclass(frozen=True)
class CellImageJExperimentSpec:
    experiment_id: str
    analysis_type: str
    title: str
    description: str
    result_csv_name: str
    macro_file_name: str
    default_parameters: Mapping[str, str | int | float | bool]
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class CellImageJMacroBundle:
    experiment: CellImageJExperimentSpec
    macro_text: str
    macro_path: Path | None = None
    output_csv_path: Path | None = None


@dataclass(frozen=True)
class CellImageJRunResult:
    experiment: CellImageJExperimentSpec
    macro_path: Path
    output_csv_path: Path
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


CELL_IMAGEJ_EXPERIMENTS: tuple[CellImageJExperimentSpec, ...] = (
    CellImageJExperimentSpec(
        experiment_id="wound_scratch",
        analysis_type="scratch_area",
        aliases=("scratch", "wound", "wound_healing", "划痕", "划痕实验"),
        title="划痕实验图片处理",
        description="批量估算 scratch/wound-healing 图像中的划痕空白区域面积和闭合比例。",
        result_csv_name="wound_scratch_results.csv",
        macro_file_name="wound_scratch_analysis.ijm",
        default_parameters={
            "threshold_method": "Default",
            "gap_polarity": "bright",
            "blur_sigma": 2.0,
            "min_gap_area_px": 500,
            "saturated_percent": 0.35,
        },
    ),
    CellImageJExperimentSpec(
        experiment_id="transwell",
        analysis_type="transwell_count",
        aliases=("transwell_assay", "migration", "invasion", "transwell实验"),
        title="Transwell 实验图片处理",
        description="批量统计 Transwell 染色图像中的迁移/侵袭细胞颗粒数量和颗粒面积。",
        result_csv_name="transwell_results.csv",
        macro_file_name="transwell_particle_count.ijm",
        default_parameters={
            "threshold_method": "Default",
            "cell_polarity": "dark",
            "blur_sigma": 1.0,
            "min_particle_area_px": 30,
            "max_particle_area_px": "Infinity",
            "watershed": True,
        },
    ),
    CellImageJExperimentSpec(
        experiment_id="immunohistochemistry",
        analysis_type="immunohistochemistry",
        aliases=("ihc", "dab", "免疫组化", "免疫组化实验"),
        title="免疫组化实验图片处理",
        description="批量估算 IHC/DAB 图像中的阳性染色面积比例和平均灰度，供人工复核。",
        result_csv_name="ihc_dab_area_results.csv",
        macro_file_name="ihc_dab_area_analysis.ijm",
        default_parameters={
            "threshold_method": "Default",
            "positive_polarity": "dark",
            "blur_sigma": 1.0,
            "min_positive_area_px": 50,
            "saturated_percent": 0.35,
        },
    ),
)

_EXPERIMENTS_BY_KEY: dict[str, CellImageJExperimentSpec] = {}
for _experiment in CELL_IMAGEJ_EXPERIMENTS:
    _EXPERIMENTS_BY_KEY[_experiment.experiment_id] = _experiment
    _EXPERIMENTS_BY_KEY[_experiment.analysis_type] = _experiment
    for _alias in _experiment.aliases:
        _EXPERIMENTS_BY_KEY[_alias.lower()] = _experiment


def list_cell_imagej_experiments() -> tuple[CellImageJExperimentSpec, ...]:
    return CELL_IMAGEJ_EXPERIMENTS


def get_cell_imagej_experiment(experiment_id_or_analysis_type: str) -> CellImageJExperimentSpec:
    key = experiment_id_or_analysis_type.strip().lower()
    try:
        return _EXPERIMENTS_BY_KEY[key]
    except KeyError as exc:
        allowed = ", ".join(spec.experiment_id for spec in CELL_IMAGEJ_EXPERIMENTS)
        raise CellImageJWorkflowError(f"未知细胞图片实验类型：{experiment_id_or_analysis_type}。可用类型：{allowed}") from exc


def is_cell_imagej_analysis(analysis_type: str) -> bool:
    return analysis_type.strip().lower() in _EXPERIMENTS_BY_KEY


def render_cell_imagej_macro(
    experiment_id_or_analysis_type: str,
    input_dir: str | Path,
    output_dir: str | Path,
    *,
    parameters: Mapping[str, Any] | None = None,
) -> CellImageJMacroBundle:
    experiment = get_cell_imagej_experiment(experiment_id_or_analysis_type)
    merged_parameters = _normalize_parameters(experiment, parameters or {})
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if experiment.experiment_id == "wound_scratch":
        macro_text = _render_wound_scratch_macro(input_path, output_path, merged_parameters, experiment.result_csv_name)
    elif experiment.experiment_id == "transwell":
        macro_text = _render_transwell_macro(input_path, output_path, merged_parameters, experiment.result_csv_name)
    elif experiment.experiment_id == "immunohistochemistry":
        macro_text = _render_ihc_macro(input_path, output_path, merged_parameters, experiment.result_csv_name)
    else:  # pragma: no cover
        raise CellImageJWorkflowError(f"未实现的实验类型：{experiment.experiment_id}")
    return CellImageJMacroBundle(experiment=experiment, macro_text=macro_text, output_csv_path=output_path / experiment.result_csv_name)


def write_cell_imagej_macro(
    experiment_id_or_analysis_type: str,
    input_dir: str | Path,
    output_dir: str | Path,
    *,
    macro_path: str | Path | None = None,
    parameters: Mapping[str, Any] | None = None,
) -> CellImageJMacroBundle:
    bundle = render_cell_imagej_macro(experiment_id_or_analysis_type, input_dir, output_dir, parameters=parameters)
    target = Path(macro_path) if macro_path is not None else Path(output_dir) / "macros" / bundle.experiment.macro_file_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(bundle.macro_text, encoding="utf-8")
    return CellImageJMacroBundle(
        experiment=bundle.experiment,
        macro_text=bundle.macro_text,
        macro_path=target,
        output_csv_path=bundle.output_csv_path,
    )


def resolve_imagej_executable(explicit_path: str | Path | None = None) -> Path:
    candidates: list[str | Path] = []
    if explicit_path is not None:
        candidates.append(explicit_path)
    for env_name in ("FIJI_EXECUTABLE", "IMAGEJ_EXECUTABLE", "IMAGEJ_PATH"):
        env_value = os.environ.get(env_name)
        if env_value:
            candidates.append(env_value)

    for candidate in candidates:
        resolved = _resolve_imagej_candidate(Path(candidate).expanduser())
        if resolved is not None:
            return resolved

    for executable_name in ("ImageJ-macosx", "ImageJ-linux64", "ImageJ-win64.exe", "fiji", "Fiji", "ImageJ", "imagej"):
        found = shutil.which(executable_name)
        if found:
            return Path(found)
    raise CellImageJNotFoundError("未找到 ImageJ/Fiji 可执行文件。请传入 imagej_executable，或设置 FIJI_EXECUTABLE / IMAGEJ_EXECUTABLE / IMAGEJ_PATH。")


def build_imagej_run_command(imagej_executable: str | Path, macro_path: str | Path) -> tuple[str, ...]:
    return (str(Path(imagej_executable)), "--headless", "--console", "--run", str(Path(macro_path)))


def run_cell_imagej_macro(
    experiment_id_or_analysis_type: str,
    input_dir: str | Path,
    output_dir: str | Path,
    *,
    imagej_executable: str | Path | None = None,
    macro_path: str | Path | None = None,
    parameters: Mapping[str, Any] | None = None,
    timeout_seconds: int = 600,
) -> CellImageJRunResult:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    bundle = write_cell_imagej_macro(
        experiment_id_or_analysis_type,
        input_dir,
        output_path,
        macro_path=macro_path,
        parameters=parameters,
    )
    if bundle.macro_path is None or bundle.output_csv_path is None:  # pragma: no cover
        raise CellImageJWorkflowError("ImageJ macro 写入失败。")
    executable = resolve_imagej_executable(imagej_executable)
    command = build_imagej_run_command(executable, bundle.macro_path)
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout_seconds)
    return CellImageJRunResult(
        experiment=bundle.experiment,
        macro_path=bundle.macro_path,
        output_csv_path=bundle.output_csv_path,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _normalize_parameters(experiment: CellImageJExperimentSpec, parameters: Mapping[str, Any]) -> dict[str, str | int | float | bool]:
    merged: dict[str, str | int | float | bool] = dict(experiment.default_parameters)
    aliases = {
        "阈值模式": "threshold_method",
        "最小划痕区域面积": "min_gap_area_px",
        "最小颗粒面积": "min_particle_area_px",
        "最大颗粒面积": "max_particle_area_px",
        "是否 Watershed": "watershed",
        "是否分水岭": "watershed",
        "最小阳性面积": "min_positive_area_px",
    }
    for key, value in parameters.items():
        normalized_key = aliases.get(str(key), str(key))
        if normalized_key not in merged:
            continue
        merged[normalized_key] = _coerce_like(value, merged[normalized_key])
    return merged


def _coerce_like(value: Any, default: str | int | float | bool) -> str | int | float | bool:
    if value is None or str(value).strip() in {"", "占位", "用户阈值，占位"}:
        return default
    if isinstance(default, bool):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "y", "是"}
    if isinstance(default, int):
        try:
            return int(str(value).strip())
        except ValueError:
            return default
    if isinstance(default, float):
        try:
            return float(str(value).strip())
        except ValueError:
            return default
    return str(value).strip()


def _resolve_imagej_candidate(candidate: Path) -> Path | None:
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return candidate
    if candidate.is_dir():
        app_executable = candidate / "Contents" / "MacOS" / "ImageJ-macosx"
        if candidate.suffix == ".app" and app_executable.is_file() and os.access(app_executable, os.X_OK):
            return app_executable
        for child in ("ImageJ-macosx", "ImageJ-linux64", "ImageJ-win64.exe", "ImageJ", "imagej"):
            nested = candidate / child
            if nested.is_file() and os.access(nested, os.X_OK):
                return nested
    return None


def _render_wound_scratch_macro(input_dir: Path, output_dir: Path, parameters: Mapping[str, str | int | float | bool], result_csv_name: str) -> str:
    return _macro_header(input_dir, output_dir, result_csv_name, parameters) + """
File.saveString("image,gap_area_px,total_area_px,gap_fraction\\n", outputCsv);
for (i = 0; i < list.length; i++) {
    if (!isImageFile(list[i])) continue;
    imagePath = inputDir + list[i];
    open(imagePath);
    width = getWidth();
    height = getHeight();
    totalArea = width * height;
    run("Duplicate...", "title=analysis");
    selectWindow("analysis");
    run("8-bit");
    run("Enhance Contrast", "saturated=" + saturated_percent);
    run("Gaussian Blur...", "sigma=" + blur_sigma);
    if (gap_polarity == "bright")
        setAutoThreshold(threshold_method + " light");
    else
        setAutoThreshold(threshold_method + " dark");
    run("Convert to Mask");
    run("Clear Results");
    run("Analyze Particles...", "size=" + min_gap_area_px + "-Infinity display clear");
    gapArea = 0;
    for (row = 0; row < nResults; row++)
        gapArea = gapArea + getResult("Area", row);
    gapFraction = gapArea / totalArea;
    File.append(csvEscape(list[i]) + "," + gapArea + "," + totalArea + "," + gapFraction + "\\n", outputCsv);
    close("*");
}
"""


def _render_transwell_macro(input_dir: Path, output_dir: Path, parameters: Mapping[str, str | int | float | bool], result_csv_name: str) -> str:
    return _macro_header(input_dir, output_dir, result_csv_name, parameters) + """
File.saveString("image,particle_count,total_particle_area_px,mean_particle_area_px\\n", outputCsv);
for (i = 0; i < list.length; i++) {
    if (!isImageFile(list[i])) continue;
    imagePath = inputDir + list[i];
    open(imagePath);
    run("Duplicate...", "title=analysis");
    selectWindow("analysis");
    run("8-bit");
    run("Gaussian Blur...", "sigma=" + blur_sigma);
    if (cell_polarity == "dark")
        setAutoThreshold(threshold_method + " dark");
    else
        setAutoThreshold(threshold_method + " light");
    run("Convert to Mask");
    if (watershed == "true")
        run("Watershed");
    run("Clear Results");
    run("Analyze Particles...", "size=" + min_particle_area_px + "-" + max_particle_area_px + " display clear");
    totalParticleArea = 0;
    for (row = 0; row < nResults; row++)
        totalParticleArea = totalParticleArea + getResult("Area", row);
    particleCount = nResults;
    meanParticleArea = 0;
    if (particleCount > 0)
        meanParticleArea = totalParticleArea / particleCount;
    File.append(csvEscape(list[i]) + "," + particleCount + "," + totalParticleArea + "," + meanParticleArea + "\\n", outputCsv);
    close("*");
}
"""


def _render_ihc_macro(input_dir: Path, output_dir: Path, parameters: Mapping[str, str | int | float | bool], result_csv_name: str) -> str:
    return _macro_header(input_dir, output_dir, result_csv_name, parameters) + """
File.saveString("image,positive_area_px,total_area_px,positive_fraction,mean_gray\\n", outputCsv);
for (i = 0; i < list.length; i++) {
    if (!isImageFile(list[i])) continue;
    imagePath = inputDir + list[i];
    open(imagePath);
    width = getWidth();
    height = getHeight();
    totalArea = width * height;
    run("Duplicate...", "title=analysis");
    selectWindow("analysis");
    run("8-bit");
    run("Enhance Contrast", "saturated=" + saturated_percent);
    run("Gaussian Blur...", "sigma=" + blur_sigma);
    getStatistics(area, meanGray);
    if (positive_polarity == "dark")
        setAutoThreshold(threshold_method + " dark");
    else
        setAutoThreshold(threshold_method + " light");
    run("Convert to Mask");
    run("Clear Results");
    run("Analyze Particles...", "size=" + min_positive_area_px + "-Infinity display clear");
    positiveArea = 0;
    for (row = 0; row < nResults; row++)
        positiveArea = positiveArea + getResult("Area", row);
    positiveFraction = positiveArea / totalArea;
    File.append(csvEscape(list[i]) + "," + positiveArea + "," + totalArea + "," + positiveFraction + "," + meanGray + "\\n", outputCsv);
    close("*");
}
"""


def _macro_header(input_dir: Path, output_dir: Path, result_csv_name: str, parameters: Mapping[str, str | int | float | bool]) -> str:
    lines = [
        "// Generated by BioMedPilot LabTools from dev/labtools@0bd04b2 cell ImageJ workflows.",
        "// Review thresholds, ROIs, masks and CSV results before scientific use.",
        "setBatchMode(true);",
        f'inputDir = "{_ij_path(input_dir)}";',
        f'outputDir = "{_ij_path(output_dir)}";',
        'File.makeDirectory(outputDir);',
        f'outputCsv = outputDir + "{_ij_string(result_csv_name)}";',
    ]
    for key, value in parameters.items():
        lines.append(f"{key} = {_ij_literal(value)};")
    lines.extend(
        [
            "list = getFileList(inputDir);",
            "",
            "function isImageFile(name) {",
            "    lower = toLowerCase(name);",
            '    return endsWith(lower, ".tif") || endsWith(lower, ".tiff") || endsWith(lower, ".jpg") || endsWith(lower, ".jpeg") || endsWith(lower, ".png");',
            "}",
            "",
            "function csvEscape(value) {",
            '    escaped = replace(value, "\\\"", "\\\"\\\"");',
            '    return "\\"" + escaped + "\\"";',
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def _ij_path(path: Path) -> str:
    text = str(path.expanduser())
    if not text.endswith(os.sep):
        text += os.sep
    return _ij_string(text)


def _ij_literal(value: str | int | float | bool) -> str:
    if isinstance(value, bool):
        return '"true"' if value else '"false"'
    if isinstance(value, int | float):
        return str(value)
    return f'"{_ij_string(value)}"'


def _ij_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
