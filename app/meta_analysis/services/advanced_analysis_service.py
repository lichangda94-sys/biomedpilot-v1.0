from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist
from uuid import uuid4

from app.meta_analysis.models.advanced_analysis import (
    LeaveOneOutResult,
    PublicationBiasResult,
    SubgroupAnalysisResult,
    leave_one_out_result_from_dict,
    leave_one_out_result_to_dict,
    new_bias_result_id,
    new_sensitivity_result_id,
    new_subgroup_result_id,
    now_utc,
    publication_bias_result_from_dict,
    publication_bias_result_to_dict,
    subgroup_result_from_dict,
    subgroup_result_to_dict,
)
from app.meta_analysis.models.analysis_dataset import AnalysisReadyDataset, StudyAnalysisRow
from app.meta_analysis.models.analysis_result import AnalysisResult, StudyMetaAnalysisResult
from app.meta_analysis.models.figures import FigureArtifact, figure_artifact_to_dict, new_figure_id
from app.meta_analysis.services.analysis_dataset_service import AnalysisDatasetService
from app.meta_analysis.services.analysis_run_service import AnalysisRunService
from app.meta_analysis.services.figure_result_service import FigureResultService
from app.meta_analysis.stats.meta_effects import StudyEffectEstimate, study_effect_from_row
from app.meta_analysis.stats.meta_models import pool_effects
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


SMALL_STUDY_BIAS_WARNING = "Publication bias tests are unreliable when the number of studies is small."


class AdvancedAnalysisService:
    def __init__(
        self,
        *,
        dataset_service: AnalysisDatasetService | None = None,
        analysis_run_service: AnalysisRunService | None = None,
        figure_service: FigureResultService | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
    ) -> None:
        self._dataset_service = dataset_service or AnalysisDatasetService()
        self._analysis_run_service = analysis_run_service or AnalysisRunService(dataset_service=self._dataset_service)
        self._figure_service = figure_service or FigureResultService(analysis_run_service=self._analysis_run_service)
        self._task_center = task_center
        self._data_center = data_center

    def run_subgroup_analysis(
        self,
        project_dir: Path,
        dataset_id: str,
        subgroup_variable: str,
        model: str,
    ) -> SubgroupAnalysisResult:
        project_dir = project_dir.expanduser().resolve()
        dataset = self._require_dataset(project_dir, dataset_id)
        task = self._start_task(
            project_id=dataset.project_id,
            task_type=TaskType.SUBGROUP_ANALYSIS_RUN,
            title="Subgroup Analysis Run",
            summary=f"Running subgroup analysis by {subgroup_variable}.",
        )
        rows = [row for row in dataset.study_rows if row.analysis_status == "included"]
        grouped: dict[str, list[StudyAnalysisRow]] = {}
        warnings: list[str] = []
        for row in rows:
            value = _row_value(row, subgroup_variable)
            if not value:
                warnings.append(f"subgroup_variable_missing:{subgroup_variable}")
                value = "missing"
            grouped.setdefault(value, []).append(row)
        subgroup_results: list[dict[str, object]] = []
        for subgroup_value, subgroup_rows in sorted(grouped.items()):
            effects = [study_effect_from_row(row) for row in subgroup_rows]
            pooled = pool_effects(effects, effect_measure=dataset.effect_measure, model=model)
            subgroup_results.append(
                {
                    "subgroup_value": subgroup_value,
                    "study_count": len(effects),
                    "model": pooled.model,
                    "pooled_effect": pooled.pooled_effect,
                    "ci_lower": pooled.ci_lower,
                    "ci_upper": pooled.ci_upper,
                    "q_statistic": pooled.q_statistic,
                    "i_squared": pooled.i_squared,
                    "tau_squared": pooled.tau_squared,
                }
            )
        result = SubgroupAnalysisResult(
            subgroup_result_id=new_subgroup_result_id(),
            analysis_result_id="",
            dataset_id=dataset.dataset_id,
            project_id=dataset.project_id,
            subgroup_variable=subgroup_variable,
            subgroup_results=subgroup_results,
            between_group_heterogeneity=_between_group_summary(subgroup_results),
            warnings=_dedupe(warnings),
            created_at=now_utc(),
        )
        self._finish_task(task, success=True, summary=f"Subgroup analysis completed: {len(subgroup_results)} groups.")
        return result

    def save_subgroup_result(self, project_dir: Path, result: SubgroupAnalysisResult) -> Path:
        project_dir = project_dir.expanduser().resolve()
        path = project_dir / "analysis" / "subgroup_analysis_results.json"
        payload = _load_payload(path, "subgroup_results")
        results = [
            item
            for item in payload.get("subgroup_results", [])
            if isinstance(item, dict) and item.get("subgroup_result_id") != result.subgroup_result_id
        ]
        results.append(subgroup_result_to_dict(result))
        _write_payload(path, "subgroup_analysis_result", "subgroup_results", results)
        self._register_asset(result.project_id, "subgroup_analysis_result", project_dir / "analysis" / "analysis_ready_datasets.json", path)
        return path

    def load_subgroup_result(self, project_dir: Path, subgroup_result_id: str) -> SubgroupAnalysisResult | None:
        path = project_dir.expanduser().resolve() / "analysis" / "subgroup_analysis_results.json"
        payload = _load_payload(path, "subgroup_results")
        for item in payload.get("subgroup_results", []):
            if isinstance(item, dict) and item.get("subgroup_result_id") == subgroup_result_id:
                return subgroup_result_from_dict(item)
        return None

    def run_leave_one_out(self, project_dir: Path, analysis_result_id: str) -> LeaveOneOutResult:
        project_dir = project_dir.expanduser().resolve()
        analysis_result = self._require_analysis_result(project_dir, analysis_result_id)
        task = self._start_task(
            project_id=analysis_result.project_id,
            task_type=TaskType.LEAVE_ONE_OUT_RUN,
            title="Leave-one-out Run",
            summary=f"Running leave-one-out for {analysis_result_id}.",
        )
        warnings: list[str] = []
        if len(analysis_result.study_results) < 3:
            warnings.append("leave_one_out_has_fewer_than_three_studies")
        omitted_results: list[dict[str, object]] = []
        influential_studies: list[str] = []
        original_width = abs(analysis_result.ci_upper - analysis_result.ci_lower)
        change_threshold = max(original_width, abs(analysis_result.pooled_effect) * 0.25, 1e-9)
        for omitted in analysis_result.study_results:
            remaining = [row for row in analysis_result.study_results if row.study_id != omitted.study_id or row.record_id != omitted.record_id]
            if not remaining:
                continue
            pooled = pool_effects(_effects_from_study_results(remaining), effect_measure=analysis_result.effect_measure, model=analysis_result.model)
            delta = pooled.pooled_effect - analysis_result.pooled_effect
            is_influential = abs(delta) > change_threshold or not (analysis_result.ci_lower <= pooled.pooled_effect <= analysis_result.ci_upper)
            if is_influential:
                influential_studies.append(omitted.study_id)
            omitted_results.append(
                {
                    "omitted_study_id": omitted.study_id,
                    "omitted_record_id": omitted.record_id,
                    "pooled_effect": pooled.pooled_effect,
                    "ci_lower": pooled.ci_lower,
                    "ci_upper": pooled.ci_upper,
                    "delta_from_original": delta,
                    "is_influential": is_influential,
                }
            )
        result = LeaveOneOutResult(
            sensitivity_result_id=new_sensitivity_result_id(),
            analysis_result_id=analysis_result.result_id,
            project_id=analysis_result.project_id,
            omitted_study_results=omitted_results,
            influential_studies=_dedupe(influential_studies),
            warnings=warnings,
            created_at=now_utc(),
        )
        self._finish_task(task, success=True, summary=f"Leave-one-out completed: {len(omitted_results)} omitted-study results.")
        return result

    def save_leave_one_out_result(self, project_dir: Path, result: LeaveOneOutResult) -> Path:
        project_dir = project_dir.expanduser().resolve()
        path = project_dir / "analysis" / "leave_one_out_results.json"
        payload = _load_payload(path, "leave_one_out_results")
        results = [
            item
            for item in payload.get("leave_one_out_results", [])
            if isinstance(item, dict) and item.get("sensitivity_result_id") != result.sensitivity_result_id
        ]
        results.append(leave_one_out_result_to_dict(result))
        _write_payload(path, "leave_one_out_result", "leave_one_out_results", results)
        self._register_asset(result.project_id, "leave_one_out_result", project_dir / "analysis" / "analysis_results.json", path)
        return path

    def run_publication_bias_test(self, project_dir: Path, analysis_result_id: str) -> PublicationBiasResult:
        project_dir = project_dir.expanduser().resolve()
        analysis_result = self._require_analysis_result(project_dir, analysis_result_id)
        task = self._start_task(
            project_id=analysis_result.project_id,
            task_type=TaskType.PUBLICATION_BIAS_TEST,
            title="Publication Bias Test",
            summary=f"Running publication bias test for {analysis_result_id}.",
        )
        warnings: list[str] = []
        if len(analysis_result.study_results) < 10:
            warnings.append(SMALL_STUDY_BIAS_WARNING)
        egger = _egger_test(analysis_result.study_results)
        begg = {
            "implemented": False,
            "message": "Begg test is not implemented in current testing version.",
        }
        result = PublicationBiasResult(
            bias_result_id=new_bias_result_id(),
            analysis_result_id=analysis_result.result_id,
            project_id=analysis_result.project_id,
            egger_test=egger,
            begg_test=begg,
            funnel_plot_artifact_id="",
            warnings=warnings,
            created_at=now_utc(),
        )
        self._finish_task(task, success=True, summary="Publication bias test completed.")
        return result

    def save_publication_bias_result(self, project_dir: Path, result: PublicationBiasResult) -> Path:
        project_dir = project_dir.expanduser().resolve()
        path = project_dir / "analysis" / "publication_bias_results.json"
        payload = _load_payload(path, "publication_bias_results")
        results = [
            item
            for item in payload.get("publication_bias_results", [])
            if isinstance(item, dict) and item.get("bias_result_id") != result.bias_result_id
        ]
        results.append(publication_bias_result_to_dict(result))
        _write_payload(path, "publication_bias_result", "publication_bias_results", results)
        self._register_asset(result.project_id, "publication_bias_result", project_dir / "analysis" / "analysis_results.json", path)
        return path

    def load_publication_bias_result(self, project_dir: Path, bias_result_id: str) -> PublicationBiasResult | None:
        path = project_dir.expanduser().resolve() / "analysis" / "publication_bias_results.json"
        payload = _load_payload(path, "publication_bias_results")
        for item in payload.get("publication_bias_results", []):
            if isinstance(item, dict) and item.get("bias_result_id") == bias_result_id:
                return publication_bias_result_from_dict(item)
        return None

    def generate_funnel_plot(self, project_dir: Path, analysis_result_id: str, *, dpi: int = 120) -> FigureArtifact:
        project_dir = project_dir.expanduser().resolve()
        analysis_result = self._require_analysis_result(project_dir, analysis_result_id)
        task = self._start_task(
            project_id=analysis_result.project_id,
            task_type=TaskType.FUNNEL_PLOT_EXPORT,
            title="Funnel Plot Export",
            summary=f"Generating funnel plot for {analysis_result_id}.",
        )
        output_path = project_dir / "figures" / f"funnel_plot_{analysis_result.result_id}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _render_funnel_plot_png(analysis_result, output_path)
        artifact = FigureArtifact(
            figure_id=new_figure_id(),
            project_id=analysis_result.project_id,
            analysis_result_id=analysis_result.result_id,
            figure_type="funnel_plot",
            file_path=str(output_path),
            format="png",
            dpi=dpi,
            created_at=now_utc(),
            source_summary={
                "effect_measure": analysis_result.effect_measure,
                "model": analysis_result.model,
                "study_count": len(analysis_result.study_results),
                "pooled_effect": analysis_result.pooled_effect,
            },
        )
        self._figure_service.save_figure_artifact(project_dir, artifact)
        self._register_asset(analysis_result.project_id, "funnel_plot", project_dir / "analysis" / "analysis_results.json", output_path)
        self._finish_task(task, success=True, summary=f"Funnel plot generated: {output_path}")
        return artifact

    def _require_dataset(self, project_dir: Path, dataset_id: str) -> AnalysisReadyDataset:
        dataset = self._dataset_service.load_analysis_ready_dataset(project_dir, dataset_id)
        if dataset is None:
            raise ValueError("analysis_ready_dataset_not_found")
        if dataset.validation_errors:
            raise ValueError("analysis_ready_dataset_has_validation_errors")
        return dataset

    def _require_analysis_result(self, project_dir: Path, analysis_result_id: str) -> AnalysisResult:
        result = self._analysis_run_service.load_analysis_result(project_dir, analysis_result_id)
        if result is None:
            raise ValueError("analysis_result_not_found")
        return result

    def _register_asset(self, project_id: str, data_type: str, source_path: Path, output_path: Path) -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(
            project_id=project_id,
            module="meta_analysis",
            data_type=data_type,
            source_path=str(source_path),
            output_path=str(output_path),
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


def _row_value(row: StudyAnalysisRow, variable: str) -> str:
    if hasattr(row, variable):
        return str(getattr(row, variable) or "")
    for container in (row.normalized_data, row.raw_data):
        if variable in container:
            return str(container.get(variable) or "")
    return ""


def _between_group_summary(subgroup_results: list[dict[str, object]]) -> dict[str, object]:
    if len(subgroup_results) < 2:
        return {"q_between": 0.0, "df": 0, "p_value": None, "message": "between-group test requires at least two subgroups"}
    effects = [float(item["pooled_effect"]) for item in subgroup_results]
    mean_effect = sum(effects) / len(effects)
    q_between = sum((effect - mean_effect) ** 2 for effect in effects)
    return {"q_between": q_between, "df": len(effects) - 1, "p_value": None, "message": "testing descriptive between-group heterogeneity"}


def _effects_from_study_results(rows: list[StudyMetaAnalysisResult]) -> list[StudyEffectEstimate]:
    return [
        StudyEffectEstimate(
            study_id=row.study_id,
            record_id=row.record_id,
            first_author=row.first_author,
            year=row.year,
            effect_measure="",
            effect=row.effect,
            ci_lower=row.ci_lower,
            ci_upper=row.ci_upper,
            standard_error=row.standard_error,
            variance=row.variance,
            transformed_effect=row.transformed_effect,
            adjusted=row.adjusted,
            covariates=row.covariates,
            warnings=row.warnings,
        )
        for row in rows
    ]


def _egger_test(rows: list[StudyMetaAnalysisResult]) -> dict[str, object]:
    if len(rows) < 3:
        return {"implemented": True, "intercept": None, "slope": None, "p_value": None, "message": "egger_test_requires_at_least_three_studies"}
    precision = [1 / row.standard_error for row in rows if row.standard_error > 0]
    standardized = [row.transformed_effect / row.standard_error for row in rows if row.standard_error > 0]
    if len(precision) < 3:
        return {"implemented": True, "intercept": None, "slope": None, "p_value": None, "message": "egger_test_requires_positive_standard_errors"}
    mean_x = sum(precision) / len(precision)
    mean_y = sum(standardized) / len(standardized)
    ss_xx = sum((x - mean_x) ** 2 for x in precision)
    if ss_xx <= 0:
        return {"implemented": True, "intercept": None, "slope": None, "p_value": None, "message": "egger_test_precision_has_no_variation"}
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(precision, standardized, strict=True)) / ss_xx
    intercept = mean_y - (slope * mean_x)
    residuals = [y - (intercept + slope * x) for x, y in zip(precision, standardized, strict=True)]
    df = len(precision) - 2
    mse = sum(residual**2 for residual in residuals) / df if df > 0 else 0
    intercept_se = math.sqrt(mse * ((1 / len(precision)) + (mean_x**2 / ss_xx))) if mse > 0 else None
    if intercept_se is None or intercept_se <= 0:
        p_value = None
    else:
        z_value = intercept / intercept_se
        p_value = 2 * (1 - NormalDist().cdf(abs(z_value)))
    return {
        "implemented": True,
        "intercept": intercept,
        "slope": slope,
        "p_value": p_value,
        "study_count": len(precision),
        "message": "testing_egger_linear_regression",
    }


def _render_funnel_plot_png(result: AnalysisResult, output_path: Path) -> None:
    width = 900
    height = 650
    margin_left = 90
    margin_right = 70
    margin_top = 70
    margin_bottom = 80
    canvas = _SimpleCanvas(width, height)
    effects = [row.effect for row in result.study_results] + [result.pooled_effect]
    standard_errors = [row.standard_error for row in result.study_results]
    min_effect = min(effects)
    max_effect = max(effects)
    max_se = max(standard_errors) if standard_errors else 1.0
    effect_pad = (max_effect - min_effect) * 0.2 if max_effect > min_effect else 1.0
    axis_min = min_effect - effect_pad
    axis_max = max_effect + effect_pad

    def x_pos(effect: float) -> int:
        return int(margin_left + ((effect - axis_min) / (axis_max - axis_min)) * (width - margin_left - margin_right))

    def y_pos(se: float) -> int:
        return int(margin_top + (se / max_se) * (height - margin_top - margin_bottom))

    canvas.line(margin_left, margin_top, margin_left, height - margin_bottom, (31, 41, 55), width=2)
    canvas.line(margin_left, height - margin_bottom, width - margin_right, height - margin_bottom, (31, 41, 55), width=2)
    pooled_x = x_pos(result.pooled_effect)
    canvas.line(pooled_x, margin_top, pooled_x, height - margin_bottom, (249, 115, 22), width=2)
    canvas.rect(40, 28, 430, 16, (17, 24, 39), fill=True)
    for row in result.study_results:
        x = x_pos(row.effect)
        y = y_pos(row.standard_error)
        canvas.rect(x - 5, y - 5, 10, 10, (37, 99, 235), fill=True)
    canvas.write_png(output_path)


class _SimpleCanvas:
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

    def write_png(self, path: Path) -> None:
        import struct
        import zlib

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
        payload = b"".join(
            [
                b"\x89PNG\r\n\x1a\n",
                chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)),
                chunk(b"IDAT", zlib.compress(b"".join(rows), 9)),
                chunk(b"IEND", b""),
            ]
        )
        path.write_bytes(payload)


def _load_payload(path: Path, key: str) -> dict[str, object]:
    if not path.exists():
        return {key: []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {key: []}
    return payload if isinstance(payload, dict) else {key: []}


def _write_payload(path: Path, data_type: str, key: str, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "data_type": data_type,
                "updated_at": now_utc(),
                key: rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _dedupe(items: list[str]) -> list[str]:
    deduped: list[str] = []
    for item in items:
        if item and item not in deduped:
            deduped.append(item)
    return deduped
