from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from labtools.cell_culture.imagej import ImageJError, build_imagej_run_command, resolve_imagej_executable


@dataclass(frozen=True)
class ProteinImageJWorkflowSpec:
    workflow_id: str
    title: str
    description: str
    result_csv_name: str
    macro_file_name: str
    default_parameters: Mapping[str, str | int | float | bool]
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProteinImageJMacroBundle:
    workflow: ProteinImageJWorkflowSpec
    macro_text: str
    macro_path: Path | None = None
    output_csv_path: Path | None = None


@dataclass(frozen=True)
class ProteinImageJRunResult:
    workflow: ProteinImageJWorkflowSpec
    macro_path: Path
    output_csv_path: Path
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


PROTEIN_IMAGEJ_WORKFLOWS: tuple[ProteinImageJWorkflowSpec, ...] = (
    ProteinImageJWorkflowSpec(
        workflow_id="dot_blot_grid",
        aliases=("dot_blot", "protein_array", "spot_array", "dotblot", "点杂交"),
        title="Dot blot 固定网格强度测量",
        description="按固定点阵生成圆形 ROI，批量测量 dot blot / protein array 的平均灰度和积分强度。",
        result_csv_name="dot_blot_grid_results.csv",
        macro_file_name="dot_blot_grid_analysis.ijm",
        default_parameters={
            "rows": 8,
            "columns": 12,
            "grid_origin_x_px": 20,
            "grid_origin_y_px": 20,
            "grid_spacing_x_px": 20,
            "grid_spacing_y_px": 20,
            "spot_diameter_px": 14,
            "background_rolling_px": 42,
            "invert_image": True,
        },
    ),
)

_WORKFLOWS_BY_ID: dict[str, ProteinImageJWorkflowSpec] = {}
for _workflow in PROTEIN_IMAGEJ_WORKFLOWS:
    _WORKFLOWS_BY_ID[_workflow.workflow_id] = _workflow
    for _alias in _workflow.aliases:
        _WORKFLOWS_BY_ID[_alias.lower()] = _workflow


def list_protein_imagej_workflows() -> tuple[ProteinImageJWorkflowSpec, ...]:
    return PROTEIN_IMAGEJ_WORKFLOWS


def get_protein_imagej_workflow(workflow_id: str) -> ProteinImageJWorkflowSpec:
    key = workflow_id.strip().lower()
    try:
        return _WORKFLOWS_BY_ID[key]
    except KeyError as exc:
        allowed = ", ".join(spec.workflow_id for spec in PROTEIN_IMAGEJ_WORKFLOWS)
        raise ImageJError(f"未知蛋白图像工作流：{workflow_id}。可用类型：{allowed}") from exc


def render_protein_imagej_macro(
    workflow_id: str,
    input_dir: str | Path,
    output_dir: str | Path,
    *,
    parameters: Mapping[str, str | int | float | bool] | None = None,
) -> ProteinImageJMacroBundle:
    workflow = get_protein_imagej_workflow(workflow_id)
    merged_parameters = {**workflow.default_parameters, **(parameters or {})}
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if workflow.workflow_id == "dot_blot_grid":
        macro_text = _render_dot_blot_grid_macro(input_path, output_path, merged_parameters, workflow.result_csv_name)
    else:  # pragma: no cover - guarded by get_protein_imagej_workflow.
        raise ImageJError(f"未实现的蛋白图像工作流：{workflow.workflow_id}")

    return ProteinImageJMacroBundle(workflow=workflow, macro_text=macro_text, output_csv_path=output_path / workflow.result_csv_name)


def write_protein_imagej_macro(
    workflow_id: str,
    input_dir: str | Path,
    output_dir: str | Path,
    *,
    macro_path: str | Path | None = None,
    parameters: Mapping[str, str | int | float | bool] | None = None,
) -> ProteinImageJMacroBundle:
    bundle = render_protein_imagej_macro(workflow_id, input_dir, output_dir, parameters=parameters)
    target = Path(macro_path) if macro_path is not None else Path(output_dir) / "macros" / bundle.workflow.macro_file_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(bundle.macro_text, encoding="utf-8")
    return ProteinImageJMacroBundle(
        workflow=bundle.workflow,
        macro_text=bundle.macro_text,
        macro_path=target,
        output_csv_path=bundle.output_csv_path,
    )


def run_protein_imagej_macro(
    workflow_id: str,
    input_dir: str | Path,
    output_dir: str | Path,
    *,
    imagej_executable: str | Path | None = None,
    macro_path: str | Path | None = None,
    parameters: Mapping[str, str | int | float | bool] | None = None,
    timeout_seconds: int = 600,
) -> ProteinImageJRunResult:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    bundle = write_protein_imagej_macro(workflow_id, input_dir, output_path, macro_path=macro_path, parameters=parameters)
    if bundle.macro_path is None or bundle.output_csv_path is None:  # pragma: no cover - write_protein_imagej_macro always sets both.
        raise ImageJError("ImageJ macro 写入失败。")

    executable = resolve_imagej_executable(imagej_executable)
    command = build_imagej_run_command(executable, bundle.macro_path)
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout_seconds)
    return ProteinImageJRunResult(
        workflow=bundle.workflow,
        macro_path=bundle.macro_path,
        output_csv_path=bundle.output_csv_path,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _render_dot_blot_grid_macro(
    input_dir: Path,
    output_dir: Path,
    parameters: Mapping[str, str | int | float | bool],
    result_csv_name: str,
) -> str:
    return _macro_header(input_dir, output_dir, result_csv_name, parameters) + """
File.saveString("image,row,column,spot_id,center_x_px,center_y_px,area_px,mean_gray,integrated_density\\n", outputCsv);
for (i = 0; i < list.length; i++) {
    if (!isImageFile(list[i])) continue;
    imagePath = inputDir + list[i];
    open(imagePath);
    run("8-bit");
    if (invert_image == "true")
        run("Invert");
    if (background_rolling_px > 0)
        run("Subtract Background...", "rolling=" + background_rolling_px);
    for (row = 0; row < rows; row++) {
        for (column = 0; column < columns; column++) {
            centerX = grid_origin_x_px + column * grid_spacing_x_px;
            centerY = grid_origin_y_px + row * grid_spacing_y_px;
            run("Specify...", "width=" + spot_diameter_px + " height=" + spot_diameter_px + " x=" + centerX + " y=" + centerY + " oval centered");
            getStatistics(area, meanGray);
            integratedDensity = area * meanGray;
            spotId = "R" + (row + 1) + "C" + (column + 1);
            File.append(csvEscape(list[i]) + "," + (row + 1) + "," + (column + 1) + "," + csvEscape(spotId) + "," + centerX + "," + centerY + "," + area + "," + meanGray + "," + integratedDensity + "\\n", outputCsv);
        }
    }
    close("*");
}
"""


def _macro_header(
    input_dir: Path,
    output_dir: Path,
    result_csv_name: str,
    parameters: Mapping[str, str | int | float | bool],
) -> str:
    lines = [
        "// Generated by BioMedPilot LabTools. Review dot positions and intensity results before scientific use.",
        "setBatchMode(true);",
        f'inputDir = "{_ij_path(input_dir)}";',
        f'outputDir = "{_ij_path(output_dir)}";',
        "File.makeDirectory(outputDir);",
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
    if not text.endswith("/"):
        text += "/"
    return _ij_string(text)


def _ij_literal(value: str | int | float | bool) -> str:
    if isinstance(value, bool):
        return '"true"' if value else '"false"'
    if isinstance(value, int | float):
        return str(value)
    return f'"{_ij_string(value)}"'


def _ij_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
