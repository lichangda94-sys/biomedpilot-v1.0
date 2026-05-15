from __future__ import annotations

import csv
import json
import struct
import zlib
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.models.analysis_result import AnalysisResult
from app.meta_analysis.models.statistical_result_state import blocks_formal_report_claim, statistical_result_state_label_zh
from app.meta_analysis.models.figures import (
    FigureArtifact,
    figure_artifact_from_dict,
    figure_artifact_to_dict,
    new_figure_id,
    now_utc,
)
from app.meta_analysis.services.analysis_run_service import AnalysisRunService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


class FigureResultService:
    def __init__(
        self,
        *,
        analysis_run_service: AnalysisRunService | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
    ) -> None:
        self._analysis_run_service = analysis_run_service or AnalysisRunService()
        self._task_center = task_center
        self._data_center = data_center

    def generate_forest_plot(self, project_dir: Path, analysis_result_id: str, *, dpi: int = 120) -> FigureArtifact:
        project_dir = project_dir.expanduser().resolve()
        result = self._require_analysis_result(project_dir, analysis_result_id)
        task = self._start_task(
            project_id=result.project_id,
            task_type=TaskType.FOREST_PLOT_EXPORT,
            title="Forest Plot Export",
            summary=f"Generating forest plot for {analysis_result_id}",
        )
        output_path = project_dir / "figures" / f"forest_plot_{result.result_id}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _render_forest_plot_png(result, output_path, dpi=dpi)
        artifact = FigureArtifact(
            figure_id=new_figure_id(),
            project_id=result.project_id,
            analysis_result_id=result.result_id,
            figure_type="forest_plot",
            file_path=str(output_path),
            format="png",
            dpi=dpi,
            created_at=now_utc(),
            source_summary={
                "outcome_name": result.outcome_name,
                "effect_measure": result.effect_measure,
                "model": result.model,
                "study_count": len(result.study_results),
                "i_squared": result.i_squared,
                "tau_squared": result.tau_squared,
                "result_state": result.result_state,
                "result_state_label_zh": statistical_result_state_label_zh(result.result_state),
                "testing_level": result.testing_level,
                "blocks_formal_report_claim": blocks_formal_report_claim(result),
            },
        )
        self.save_figure_artifact(project_dir, artifact)
        self._register_asset(
            project_id=result.project_id,
            data_type="forest_plot",
            source_path=str(project_dir / "analysis" / "analysis_results.json"),
            output_path=str(output_path),
        )
        self._finish_task(task, success=True, summary=f"Forest plot generated: {output_path}")
        return artifact

    def export_result_table_csv(self, project_dir: Path, analysis_result_id: str) -> Path:
        project_dir = project_dir.expanduser().resolve()
        result = self._require_analysis_result(project_dir, analysis_result_id)
        task = self._start_task(
            project_id=result.project_id,
            task_type=TaskType.ANALYSIS_RESULT_TABLE_EXPORT,
            title="Analysis Result Table Export",
            summary=f"Exporting result table for {analysis_result_id}",
        )
        output_path = project_dir / "exports" / f"analysis_result_table_{result.result_id}.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=_result_table_fieldnames())
            writer.writeheader()
            for row in result.study_results:
                writer.writerow(
                    {
                        "row_type": "study",
                        "study_id": row.study_id,
                        "first_author": row.first_author,
                        "year": row.year or "",
                        "effect": row.effect,
                        "ci_lower": row.ci_lower,
                        "ci_upper": row.ci_upper,
                        "standard_error": row.standard_error,
                        "weight": row.weight,
                        "model": result.model,
                        "effect_measure": result.effect_measure,
                    }
                )
            writer.writerow(
                {
                    "row_type": "pooled",
                    "study_id": "pooled",
                    "first_author": "Pooled effect",
                    "year": "",
                    "effect": result.pooled_effect,
                    "ci_lower": result.ci_lower,
                    "ci_upper": result.ci_upper,
                    "standard_error": "",
                    "weight": sum(row.weight for row in result.study_results),
                    "model": result.model,
                    "effect_measure": result.effect_measure,
                }
            )
        self._register_asset(
            project_id=result.project_id,
            data_type="analysis_result_table",
            source_path=str(project_dir / "analysis" / "analysis_results.json"),
            output_path=str(output_path),
        )
        self._finish_task(task, success=True, summary=f"Analysis result table exported: {output_path}")
        return output_path

    def save_figure_artifact(self, project_dir: Path, artifact: FigureArtifact) -> Path:
        project_dir = project_dir.expanduser().resolve()
        output_path = project_dir / "figures" / "figure_artifacts.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        artifacts = [existing for existing in self.list_figure_artifacts(project_dir) if existing.figure_id != artifact.figure_id]
        artifacts.append(artifact)
        payload = {
            "project_id": artifact.project_id,
            "data_type": "figure_artifacts",
            "updated_at": now_utc(),
            "artifacts": [figure_artifact_to_dict(item) for item in artifacts],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def list_figure_artifacts(self, project_dir: Path) -> list[FigureArtifact]:
        path = project_dir.expanduser().resolve() / "figures" / "figure_artifacts.json"
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [figure_artifact_from_dict(item) for item in payload.get("artifacts", [])]

    def _require_analysis_result(self, project_dir: Path, analysis_result_id: str) -> AnalysisResult:
        result = self._analysis_run_service.load_analysis_result(project_dir, analysis_result_id)
        if result is None:
            raise ValueError("analysis_result_not_found")
        return result

    def _register_asset(self, *, project_id: str, data_type: str, source_path: str, output_path: str) -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(
            project_id=project_id,
            module="meta_analysis",
            data_type=data_type,
            source_path=source_path,
            output_path=output_path,
            status="available",
        )

    def _start_task(self, *, project_id: str, task_type: TaskType, title: str, summary: str) -> TaskRecord:
        now = now_utc()
        if self._task_center is None:
            return TaskRecord(
                task_id=f"task-{uuid4().hex[:12]}",
                task_type=task_type,
                status=TaskStatus.RUNNING,
                module="meta_analysis",
                title=title,
                created_at=now,
                updated_at=now,
                project_id=project_id,
                started_at=now,
                summary=summary,
            )
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=task_type,
            module="meta_analysis",
            title=title,
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=summary,
        )

    def _finish_task(self, task: TaskRecord, *, success: bool, summary: str) -> None:
        if self._task_center is None:
            return
        now = now_utc()
        self._task_center.save_task(
            TaskRecord(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED if success else TaskStatus.FAILED,
                module=task.module,
                title=task.title,
                created_at=task.created_at,
                updated_at=now,
                project_id=task.project_id,
                started_at=task.started_at,
                finished_at=now,
                summary=summary,
                error_message="" if success else summary,
            )
        )


def _result_table_fieldnames() -> list[str]:
    return [
        "row_type",
        "study_id",
        "first_author",
        "year",
        "effect",
        "ci_lower",
        "ci_upper",
        "standard_error",
        "weight",
        "model",
        "effect_measure",
    ]


def _render_forest_plot_png(result: AnalysisResult, output_path: Path, *, dpi: int) -> None:
    row_count = max(1, len(result.study_results))
    width = 1100
    height = max(360, 150 + (row_count * 44))
    canvas = _Canvas(width, height)
    plot_left = 360
    plot_right = width - 80
    top = 82
    row_gap = 44
    values = [result.ci_lower, result.ci_upper, result.pooled_effect]
    for study in result.study_results:
        values.extend([study.ci_lower, study.ci_upper, study.effect])
    min_value = min(values)
    max_value = max(values)
    if result.effect_measure in {"OR", "RR", "HR"}:
        min_value = min(min_value, 1.0)
        max_value = max(max_value, 1.0)
    padding = (max_value - min_value) * 0.12 if max_value > min_value else 1.0
    axis_min = min_value - padding
    axis_max = max_value + padding

    def x_pos(value: float) -> int:
        return int(plot_left + ((value - axis_min) / (axis_max - axis_min)) * (plot_right - plot_left))

    # Header bands encode title/summary visually without font dependencies.
    canvas.rect(40, 26, 620, 18, (17, 24, 39), fill=True)
    canvas.rect(40, 52, int(160 + min(320, result.i_squared * 3)), 8, (249, 115, 22), fill=True)
    canvas.rect(plot_left, 52, plot_right - plot_left, 2, (17, 24, 39), fill=True)

    axis_y = top + (row_count * row_gap) + 32
    canvas.line(plot_left, axis_y, plot_right, axis_y, (156, 163, 175))
    for tick in (axis_min, result.pooled_effect, axis_max):
        x = x_pos(tick)
        canvas.line(x, axis_y - 5, x, axis_y + 5, (156, 163, 175))
    if result.effect_measure in {"OR", "RR", "HR"} and axis_min < 1 < axis_max:
        null_x = x_pos(1.0)
        canvas.line(null_x, top - 24, null_x, axis_y, (203, 213, 225))

    max_weight = max((study.weight for study in result.study_results), default=1.0)
    for index, study in enumerate(result.study_results):
        y = top + (index * row_gap)
        canvas.rect(40, y - 7, 220, 12, (17, 24, 39), fill=True)
        canvas.line(x_pos(study.ci_lower), y, x_pos(study.ci_upper), y, (37, 99, 235), width=3)
        box = max(6, int(16 * (study.weight / max_weight) ** 0.5))
        x = x_pos(study.effect)
        canvas.rect(x - box // 2, y - box // 2, box, box, (37, 99, 235), fill=True)

    pooled_y = top + (row_count * row_gap) + 8
    canvas.rect(40, pooled_y - 8, 250, 14, (17, 24, 39), fill=True)
    canvas.diamond(
        x_pos(result.pooled_effect),
        pooled_y,
        max(8, abs(x_pos(result.ci_upper) - x_pos(result.ci_lower)) // 2),
        11,
        (249, 115, 22),
        (180, 35, 24),
    )
    canvas.write_png(output_path)


class _Canvas:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.pixels = bytearray([255, 255, 255] * width * height)

    def set_pixel(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = (y * self.width + x) * 3
            self.pixels[offset : offset + 3] = bytes(color)

    def line(self, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int], *, width: int = 1) -> None:
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy
        x = x1
        y = y1
        while True:
            self.rect(x - width // 2, y - width // 2, width, width, color, fill=True)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def rect(self, x: int, y: int, width: int, height: int, color: tuple[int, int, int], *, fill: bool) -> None:
        for yy in range(y, y + height):
            for xx in range(x, x + width):
                if fill or yy in {y, y + height - 1} or xx in {x, x + width - 1}:
                    self.set_pixel(xx, yy, color)

    def diamond(
        self,
        cx: int,
        cy: int,
        half_width: int,
        half_height: int,
        fill_color: tuple[int, int, int],
        outline_color: tuple[int, int, int],
    ) -> None:
        for yy in range(cy - half_height, cy + half_height + 1):
            span = int(half_width * (1 - abs(yy - cy) / max(1, half_height)))
            self.line(cx - span, yy, cx + span, yy, fill_color)
        self.line(cx - half_width, cy, cx, cy - half_height, outline_color, width=2)
        self.line(cx, cy - half_height, cx + half_width, cy, outline_color, width=2)
        self.line(cx + half_width, cy, cx, cy + half_height, outline_color, width=2)
        self.line(cx, cy + half_height, cx - half_width, cy, outline_color, width=2)

    def write_png(self, path: Path) -> None:
        def chunk(tag: bytes, data: bytes) -> bytes:
            return (
                struct.pack(">I", len(data))
                + tag
                + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            )

        rows = [
            b"\x00" + bytes(self.pixels[y * self.width * 3 : (y + 1) * self.width * 3])
            for y in range(self.height)
        ]
        raw = b"".join(rows)
        payload = b"".join(
            [
                b"\x89PNG\r\n\x1a\n",
                chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)),
                chunk(b"IDAT", zlib.compress(raw, 9)),
                chunk(b"IEND", b""),
            ]
        )
        path.write_bytes(payload)
