from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.bioinformatics.models.expression_import import ExpressionImportResult
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


GENE_COLUMN_KEYWORDS = ("gene_symbol", "genesymbol", "probe_id", "gene", "symbol", "probe", "id", "ensembl")
SAMPLE_COLUMN_KEYWORDS = ("gsm", "tcga", "srr", "sample", "control", "tumor", "normal", "treat", "drug")
SUPPORTED_EXTENSIONS = {".csv", ".tsv", ".txt", ".xlsx"}
MISSING_VALUES = {"", "na", "n/a", "nan", "null", "none"}


class LocalExpressionImportService:
    def __init__(
        self,
        *,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def import_expression_matrix(self, *, project_id: str, source_path: str) -> ExpressionImportResult:
        task = self._start_task(project_id=project_id, source_path=source_path)
        validation_error = self._validate(source_path)
        if validation_error is not None:
            result = ExpressionImportResult(
                success=False,
                source_path=source_path,
                source_type="",
                row_count=0,
                column_count=0,
                candidate_gene_columns=[],
                candidate_sample_columns=[],
                numeric_sample_column_count=0,
                missing_value_rate=0.0,
                output_path="",
                warnings=[],
                message=validation_error,
            )
            self._finish_task(task, result)
            return result

        path = Path(source_path).expanduser().resolve()
        source_type = path.suffix.lower().lstrip(".")
        try:
            headers, rows = self._read_table(path)
            summary = self._summarize(headers, rows)
            output_path = self._write_output(project_id=project_id, source_path=path, source_type=source_type, result=summary)
            result = ExpressionImportResult(
                success=True,
                source_path=str(path),
                source_type=source_type,
                row_count=summary.row_count,
                column_count=summary.column_count,
                candidate_gene_columns=summary.candidate_gene_columns,
                candidate_sample_columns=summary.candidate_sample_columns,
                numeric_sample_column_count=summary.numeric_sample_column_count,
                missing_value_rate=summary.missing_value_rate,
                output_path=str(output_path),
                warnings=summary.warnings,
                message=(
                    f"本地表达矩阵导入预检完成：{summary.row_count} 行，"
                    f"{summary.column_count} 列，识别 {summary.numeric_sample_column_count} 个数值样本列。"
                ),
                details={"raw_file_modified": False, "normalization_executed": False},
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="bioinformatics",
                data_type="expression_matrix",
                source_path=str(path),
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except ImportError as exc:
            result = self._failure(path, source_type, "读取 XLSX 需要安装 openpyxl，请安装后重试。", {"error": str(exc)})
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = self._failure(path, source_type, "表达矩阵导入失败，请确认文件是带表头的表格文件。", {"error": str(exc)})
            self._finish_task(task, result)
            return result

    def _validate(self, source_path: str) -> str | None:
        if not source_path.strip():
            return "请输入本地表达矩阵文件路径。"
        path = Path(source_path).expanduser()
        if not path.exists():
            return "表达矩阵文件不存在，请检查路径。"
        if not path.is_file():
            return "表达矩阵路径需要指向一个文件。"
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return "暂不支持该文件格式，请使用 CSV、TSV、TXT 或 XLSX 文件。"
        return None

    def _read_table(self, path: Path) -> tuple[list[str], list[list[object]]]:
        if path.suffix.lower() == ".xlsx":
            return self._read_xlsx(path)
        delimiter = "," if path.suffix.lower() == ".csv" else "\t"
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            rows = [row for row in reader]
        if not rows:
            raise ValueError("empty_table")
        headers = [str(value).strip() for value in rows[0]]
        return headers, rows[1:]

    def _read_xlsx(self, path: Path) -> tuple[list[str], list[list[object]]]:
        try:
            from openpyxl import load_workbook
        except Exception as exc:  # pragma: no cover - covered when dependency is absent.
            raise ImportError("openpyxl is required for XLSX expression matrix import") from exc
        workbook = load_workbook(path, read_only=True, data_only=True)
        worksheet = workbook.active
        rows = list(worksheet.iter_rows(values_only=True))
        workbook.close()
        if not rows:
            raise ValueError("empty_table")
        headers = ["" if value is None else str(value).strip() for value in rows[0]]
        data_rows = [list(row) for row in rows[1:]]
        return headers, data_rows

    def _summarize(self, headers: list[str], rows: list[list[object]]) -> ExpressionImportResult:
        normalized_headers = [header.strip() or f"column_{index + 1}" for index, header in enumerate(headers)]
        row_count = len(rows)
        column_count = len(normalized_headers)
        gene_columns = [
            header
            for header in normalized_headers
            if any(keyword in _normalize_name(header) for keyword in GENE_COLUMN_KEYWORDS)
        ]
        numeric_columns = [
            header
            for index, header in enumerate(normalized_headers)
            if header not in gene_columns and self._is_numeric_column(rows, index)
        ]
        pattern_columns = [
            header
            for header in normalized_headers
            if header not in gene_columns
            and any(keyword in _normalize_name(header) for keyword in SAMPLE_COLUMN_KEYWORDS)
        ]
        sample_columns = _dedupe([*numeric_columns, *pattern_columns])
        missing_value_rate = self._missing_value_rate(rows, normalized_headers, sample_columns)
        warnings = self._warnings(
            row_count=row_count,
            column_count=column_count,
            gene_columns=gene_columns,
            numeric_sample_column_count=len(numeric_columns),
            missing_value_rate=missing_value_rate,
        )
        return ExpressionImportResult(
            success=True,
            source_path="",
            source_type="",
            row_count=row_count,
            column_count=column_count,
            candidate_gene_columns=gene_columns,
            candidate_sample_columns=sample_columns,
            numeric_sample_column_count=len(numeric_columns),
            missing_value_rate=missing_value_rate,
            output_path="",
            warnings=warnings,
            message="summary",
        )

    def _is_numeric_column(self, rows: list[list[object]], column_index: int) -> bool:
        seen_value = False
        for row in rows:
            value = row[column_index] if column_index < len(row) else ""
            if _is_missing(value):
                continue
            try:
                float(str(value).strip())
            except ValueError:
                return False
            seen_value = True
        return seen_value

    def _missing_value_rate(self, rows: list[list[object]], headers: list[str], sample_columns: list[str]) -> float:
        if not rows or not sample_columns:
            return 0.0
        indexes = [headers.index(column) for column in sample_columns]
        total = len(rows) * len(indexes)
        missing = 0
        for row in rows:
            for index in indexes:
                value = row[index] if index < len(row) else ""
                if _is_missing(value):
                    missing += 1
        return round(missing / total, 4) if total else 0.0

    def _warnings(
        self,
        *,
        row_count: int,
        column_count: int,
        gene_columns: list[str],
        numeric_sample_column_count: int,
        missing_value_rate: float,
    ) -> list[str]:
        warnings: list[str] = []
        if not gene_columns:
            warnings.append("没有识别到 gene/probe 列，请在数据资产确认步骤手动选择。")
        if numeric_sample_column_count < 2:
            warnings.append("数值样本列太少，后续分组和差异分析可能无法运行。")
        if missing_value_rate >= 0.2:
            warnings.append("缺失值比例较高，后续需要清洗或过滤。")
        if row_count < 1 or column_count < 2:
            warnings.append("文件行列数异常，请确认表格包含基因列和样本列。")
        return warnings

    def _write_output(
        self,
        *,
        project_id: str,
        source_path: Path,
        source_type: str,
        result: ExpressionImportResult,
    ) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "bioinformatics" / "expression_import"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"expression_matrix_import_{uuid4().hex[:12]}.json"
        payload = {
            "project_id": project_id,
            "module": "bioinformatics",
            "data_type": "expression_matrix",
            "source_path": str(source_path),
            "source_type": source_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "ready_for_asset_confirmation",
            "raw_file_modified": False,
            "normalization_executed": False,
            "summary": asdict(result) | {"source_path": str(source_path), "source_type": source_type},
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def _failure(self, path: Path, source_type: str, message: str, details: dict[str, object]) -> ExpressionImportResult:
        return ExpressionImportResult(
            success=False,
            source_path=str(path),
            source_type=source_type,
            row_count=0,
            column_count=0,
            candidate_gene_columns=[],
            candidate_sample_columns=[],
            numeric_sample_column_count=0,
            missing_value_rate=0.0,
            output_path="",
            warnings=[],
            message=message,
            details=details,
        )

    def _start_task(self, *, project_id: str, source_path: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.IMPORT,
            module="bioinformatics",
            title="Local Expression Matrix Import",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"local_expression_import: {source_path}" if source_path else "local_expression_import: waiting for file path",
        )

    def _finish_task(self, task: TaskRecord, result: ExpressionImportResult) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._task_center.save_task(
            TaskRecord(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED if result.success else TaskStatus.FAILED,
                module=task.module,
                title=task.title,
                created_at=task.created_at,
                updated_at=now,
                project_id=task.project_id,
                started_at=task.started_at,
                finished_at=now,
                summary=f"local_expression_import: {result.message}",
                error_message="" if result.success else result.message,
            )
        )


def _normalize_name(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _is_missing(value: object) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in MISSING_VALUES


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
