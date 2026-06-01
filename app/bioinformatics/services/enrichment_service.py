from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.bioinformatics.adapters.enrichment_adapter import EnrichmentAdapter
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


@dataclass(frozen=True)
class EnrichmentPreflightResult:
    success: bool
    project_id: str
    source_path: str
    dataset_count: int
    ready_for_enrichment_count: int
    output_path: str
    message: str
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class REnrichmentBackendDetection:
    status: str
    rscript: str
    packages: dict[str, dict[str, object]]
    capabilities: dict[str, bool]
    blockers: list[dict[str, str]]
    message: str


class EnrichmentService:
    def __init__(
        self,
        *,
        adapter: EnrichmentAdapter | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._adapter = adapter or EnrichmentAdapter()
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def create_preflight(self, *, project_id: str, differential_expression_path: str) -> EnrichmentPreflightResult:
        task = self._start_task(project_id=project_id, source_path=differential_expression_path)
        validation_error = self._validate(differential_expression_path)
        if validation_error is not None:
            result = EnrichmentPreflightResult(
                success=False,
                project_id=project_id,
                source_path=differential_expression_path,
                dataset_count=0,
                ready_for_enrichment_count=0,
                output_path="",
                message=validation_error,
                error_count=1,
            )
            self._finish_task(task, result)
            return result

        source_path = Path(differential_expression_path).expanduser().resolve()
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            if "preflight_items" not in payload:
                raise ValueError("富集分析预检需要差异表达分析预检输出。")
            items = self._adapter.build_preflight(payload)
            ready_count = sum(1 for item in items if item.status == "ready_for_enrichment_runner")
            output_path = self._write_output(project_id, source_path, items)
            result = EnrichmentPreflightResult(
                success=True,
                project_id=project_id,
                source_path=str(source_path),
                dataset_count=len(items),
                ready_for_enrichment_count=ready_count,
                output_path=str(output_path),
                message=f"富集分析预检已生成：{ready_count}/{len(items)} 个数据集具备富集分析前置条件。",
                details={
                    "enrichment_executed": False,
                    "network_used": False,
                    "database_download_executed": False,
                },
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="bioinformatics",
                data_type="geo_enrichment_preflight",
                source_path=str(source_path),
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = EnrichmentPreflightResult(
                success=False,
                project_id=project_id,
                source_path=str(source_path),
                dataset_count=0,
                ready_for_enrichment_count=0,
                output_path="",
                message="富集分析预检失败，请确认输入来自差异表达分析预检。",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def detect_r_backend(self) -> REnrichmentBackendDetection:
        rscript = shutil.which("Rscript") or ""
        packages: dict[str, dict[str, object]] = {}
        blockers: list[dict[str, str]] = []
        package_names = ("ReactomePA", "msigdbr", "fgsea", "clusterProfiler")

        if not rscript:
            blockers.append({"code": "missing_rscript", "message": "Rscript is not available on PATH."})
            for package_name in package_names:
                packages[package_name] = {"available": False, "version": "", "missing_reason": "missing_rscript"}
        else:
            for package_name in package_names:
                probe = (
                    "pkg <- commandArgs(TRUE)[1]; "
                    "ok <- requireNamespace(pkg, quietly=TRUE); "
                    "if (ok) { cat(as.character(utils::packageVersion(pkg))) } else { quit(status=2) }"
                )
                try:
                    result = subprocess.run(
                        [rscript, "-e", probe, package_name],
                        capture_output=True,
                        text=True,
                        timeout=8,
                        check=False,
                    )
                except Exception as exc:
                    packages[package_name] = {"available": False, "version": "", "missing_reason": exc.__class__.__name__}
                    continue
                packages[package_name] = {
                    "available": result.returncode == 0,
                    "version": result.stdout.strip() if result.returncode == 0 else "",
                    "missing_reason": "none" if result.returncode == 0 else "package_not_installed_or_unavailable",
                }

        capabilities = {
            "ora_reactome": bool(packages.get("ReactomePA", {}).get("available")),
            "msigdb_metadata": bool(packages.get("msigdbr", {}).get("available")),
            "gsea_preranked_fgsea": bool(packages.get("fgsea", {}).get("available")),
            "gsea_preranked_clusterprofiler": bool(packages.get("clusterProfiler", {}).get("available")),
        }
        status = "available" if capabilities["ora_reactome"] and capabilities["msigdb_metadata"] else "blocked_missing_dependency"
        return REnrichmentBackendDetection(
            status=status,
            rscript=rscript,
            packages=packages,
            capabilities=capabilities,
            blockers=blockers,
            message="R enrichment backend is detect-only; no install, download, ORA, or GSEA execution was started.",
        )

    def _validate(self, differential_expression_path: str) -> str | None:
        if not differential_expression_path.strip():
            return "请选择差异表达分析预检 JSON 文件。"
        path = Path(differential_expression_path).expanduser()
        if not path.exists():
            return "差异表达分析预检文件不存在，请检查路径。"
        if path.suffix.lower() != ".json":
            return "富集分析预检需要 JSON 输入。"
        return None

    def _start_task(self, *, project_id: str, source_path: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.ANALYSIS,
            module="bioinformatics",
            title="Enrichment Preflight",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Creating enrichment preflight from {source_path}" if source_path else "Waiting for differential expression preflight",
        )

    def _finish_task(self, task: TaskRecord, result: EnrichmentPreflightResult) -> None:
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
                summary=result.message,
                error_message="" if result.success else result.message,
            )
        )

    def _write_output(self, project_id: str, source_path: Path, items: list[object]) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "bioinformatics" / "enrichment"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"geo_enrichment_preflight_{uuid4().hex[:12]}.json"
        payload = {
            "project_id": project_id,
            "source_path": str(source_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "enrichment_executed": False,
            "network_used": False,
            "database_download_executed": False,
            "preflight_items": [asdict(item) for item in items],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path
