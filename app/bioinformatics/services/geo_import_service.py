from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.bioinformatics.adapters.legacy_geo import LegacyGeoAdapter
from app.bioinformatics.retrieval import GeoDatasetResult, GeoSearchService, build_bioinformatics_query_strategy
from app.bioinformatics.search_center import BioinformaticsSearchCenterResult, BioinformaticsSourceRouter
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


@dataclass(frozen=True)
class GeoImportPlanResult:
    success: bool
    project_id: str
    query_text: str
    full_geo_query: str
    accessions: list[str]
    max_results: int
    output_path: str
    message: str
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)
    recognized_diseases_zh: list[str] = field(default_factory=list)
    disease_terms_en: list[str] = field(default_factory=list)
    confirmed_geo_queries: list[str] = field(default_factory=list)
    supplemental_geo_queries: list[str] = field(default_factory=list)
    broad_query_guard_triggered: bool = False
    tcga_project_candidates: list[dict[str, str]] = field(default_factory=list)
    gtex_tissue_candidates: list[dict[str, str]] = field(default_factory=list)
    geo_results: list[dict[str, object]] = field(default_factory=list)
    unified_dataset_candidates: list[dict[str, object]] = field(default_factory=list)
    source_search_results: dict[str, dict[str, object]] = field(default_factory=dict)
    search_status: str = "draft_only"


class GeoImportService:
    def __init__(
        self,
        *,
        adapter: LegacyGeoAdapter | None = None,
        geo_search_service: GeoSearchService | None = None,
        source_router: BioinformaticsSourceRouter | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._adapter = adapter or LegacyGeoAdapter()
        self._geo_search_service = geo_search_service or GeoSearchService()
        self._source_router = source_router or BioinformaticsSourceRouter()
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def create_geo_import_plan(
        self,
        *,
        project_id: str,
        query_text: str,
        accession_text: str = "",
        max_results: int = 20,
        execute_online: bool = False,
        include_supplemental: bool = False,
    ) -> GeoImportPlanResult:
        task = self._start_task(project_id=project_id, query_text=query_text)
        validation_error = self._validate(query_text=query_text, accession_text=accession_text, max_results=max_results)
        if validation_error is not None:
            result = GeoImportPlanResult(
                success=False,
                project_id=project_id,
                query_text=query_text,
                full_geo_query="",
                accessions=[],
                max_results=max_results,
                output_path="",
                message=validation_error,
                error_count=1,
            )
            self._finish_task(task, result)
            return result

        try:
            strategy = build_bioinformatics_query_strategy(query_text)
            source_center_result = self._build_source_center_result(
                query_text,
                max_results=max_results,
                confirmed_geo_queries=strategy.confirmed_geo_queries,
                allow_broad_geo_query=include_supplemental,
            )
            geo_response = None
            if execute_online:
                geo_response = self._geo_search_service.search(
                    query_text,
                    max_results=max_results,
                    include_supplemental=include_supplemental,
                )
            plan = self._adapter.build_query_plan(
                query_text=strategy.confirmed_geo_queries[0] if strategy.confirmed_geo_queries else query_text,
                accession_text=accession_text,
                max_results=max_results,
            )
            output_path = self._write_output(
                project_id,
                plan,
                strategy=strategy,
                source_center_result=source_center_result,
                geo_results=geo_response.results if geo_response else (),
                execute_online=execute_online,
            )
            search_accessions = [item.accession for item in geo_response.results] if geo_response else []
            result = GeoImportPlanResult(
                success=True,
                project_id=project_id,
                query_text=query_text.strip(),
                full_geo_query=plan.full_geo_query,
                accessions=list(dict.fromkeys([*plan.accessions, *search_accessions])),
                max_results=plan.max_results,
                output_path=str(output_path),
                message=_success_message(plan_accessions=plan.accessions, geo_results=geo_response.results if geo_response else (), max_results=plan.max_results, execute_online=execute_online),
                details={
                    "legacy_source": plan.legacy_source,
                    "online_search_executed": execute_online,
                    "executed_queries": list(geo_response.executed_queries) if geo_response else [],
                    "warnings": list(geo_response.warnings) if geo_response else list(strategy.warnings),
                    "error_message": geo_response.error_message if geo_response else "",
                },
                recognized_diseases_zh=list(strategy.recognized_diseases_zh),
                disease_terms_en=list(strategy.disease_terms),
                confirmed_geo_queries=list(strategy.confirmed_geo_queries),
                supplemental_geo_queries=list(strategy.supplemental_geo_queries),
                broad_query_guard_triggered=strategy.broad_query_guard_triggered,
                tcga_project_candidates=[asdict(item) for item in strategy.tcga_project_candidates],
                gtex_tissue_candidates=[asdict(item) for item in strategy.gtex_tissue_candidates],
                geo_results=[asdict(item) for item in geo_response.results] if geo_response else [],
                unified_dataset_candidates=_source_candidates(source_center_result),
                source_search_results=_source_results(source_center_result),
                search_status=geo_response.search_status if geo_response else "draft_only",
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="bioinformatics",
                data_type="geo_query_plan",
                source_path="manual_input",
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = GeoImportPlanResult(
                success=False,
                project_id=project_id,
                query_text=query_text,
                full_geo_query="",
                accessions=[],
                max_results=max_results,
                output_path="",
                message="GEO 查询计划生成失败，请检查输入内容。",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def _validate(self, *, query_text: str, accession_text: str, max_results: int) -> str | None:
        if not query_text.strip() and not accession_text.strip():
            return "请输入 GEO 检索词或 GSE accession。"
        if max_results < 1 or max_results > 1000:
            return "max_results 必须在 1 到 1000 之间。"
        return None

    def _start_task(self, *, project_id: str, query_text: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.IMPORT,
            module="bioinformatics",
            title="GEO Query Import",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Creating GEO query plan for {query_text}" if query_text else "Creating GEO accession import plan",
        )

    def _finish_task(self, task: TaskRecord, result: GeoImportPlanResult) -> None:
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

    def register_geo_result_as_source(self, *, project_id: str, result: GeoDatasetResult | dict[str, object]) -> Path:
        payload = asdict(result) if isinstance(result, GeoDatasetResult) else dict(result)
        accession = str(payload.get("accession") or "GSE")
        output_dir = self._storage_root / "projects" / project_id / "bioinformatics" / "acquisition_sources"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"geo_source_{accession}_{uuid4().hex[:8]}.json"
        source_record = {
            "project_id": project_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "GEO",
            "accession": accession,
            "status": "registered_for_recognition",
            "analysis_ready": "unknown",
            "note": "已登记为数据来源；后续仍需资产识别和标准化判断是否可分析。",
            "geo_result": payload,
        }
        output_path.write_text(json.dumps(source_record, ensure_ascii=False, indent=2), encoding="utf-8")
        self._data_center.register_asset(
            project_id=project_id,
            module="bioinformatics",
            data_type="geo_dataset_source",
            source_path=accession,
            output_path=str(output_path),
            status="registered_for_recognition",
        )
        return output_path

    def _build_source_center_result(
        self,
        query_text: str,
        *,
        max_results: int,
        confirmed_geo_queries: tuple[str, ...],
        allow_broad_geo_query: bool,
    ) -> BioinformaticsSearchCenterResult | None:
        if not query_text.strip():
            return None
        try:
            return self._source_router.search(
                query_text,
                online_enabled=False,
                limit=max_results,
                confirmed_geo_queries=confirmed_geo_queries,
                allow_broad_geo_query=allow_broad_geo_query,
            )
        except Exception:
            return None

    def _write_output(
        self,
        project_id: str,
        plan: object,
        *,
        strategy: object,
        source_center_result: BioinformaticsSearchCenterResult | None,
        geo_results: object,
        execute_online: bool,
    ) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "bioinformatics" / "geo_import"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"geo_query_plan_{uuid4().hex[:12]}.json"
        payload = {
            "project_id": project_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "geo",
            "status": "ready_for_download_step",
            "online_search_executed": execute_online,
            "plan": asdict(plan),
            "recognized_diseases_zh": list(getattr(strategy, "recognized_diseases_zh", ())),
            "disease_terms_en": list(getattr(strategy, "disease_terms", ())),
            "confirmed_geo_queries": list(getattr(strategy, "confirmed_geo_queries", ())),
            "supplemental_geo_queries": list(getattr(strategy, "supplemental_geo_queries", ())),
            "broad_query_guard_triggered": bool(getattr(strategy, "broad_query_guard_triggered", False)),
            "tcga_project_candidates": [asdict(item) for item in getattr(strategy, "tcga_project_candidates", ())],
            "gtex_tissue_candidates": [asdict(item) for item in getattr(strategy, "gtex_tissue_candidates", ())],
            "geo_results": [asdict(item) for item in geo_results],  # type: ignore[union-attr]
            "bioinformatics_search_center": source_center_result.to_dict() if source_center_result is not None else None,
            "unified_dataset_candidates": _source_candidates(source_center_result),
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


def _success_message(*, plan_accessions: list[str], geo_results: object, max_results: int, execute_online: bool) -> str:
    result_count = len(list(geo_results))  # type: ignore[arg-type]
    if execute_online:
        return f"GEO/GSE 检索完成：返回 {result_count} 条结果，最多 {max_results} 条。"
    return f"GEO 查询草稿已生成：{len(plan_accessions)} 个手动 accession，最多检索 {max_results} 条。"


def _source_candidates(result: BioinformaticsSearchCenterResult | None) -> list[dict[str, object]]:
    if result is None:
        return []
    return [candidate.to_dict() for candidate in result.candidates]


def _source_results(result: BioinformaticsSearchCenterResult | None) -> dict[str, dict[str, object]]:
    if result is None:
        return {}
    return {source: source_result.to_dict() for source, source_result in result.source_results.items()}
