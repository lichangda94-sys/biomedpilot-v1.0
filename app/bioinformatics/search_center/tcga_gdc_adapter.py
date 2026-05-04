from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from .models import SourceSearchResult, StructuredBioinformaticsQuery, UnifiedDatasetCandidate


GDC_API_ROOT = "https://api.gdc.cancer.gov"


class TcgaGdcSearchAdapter:
    source = "tcga_gdc"
    database_source = "GDC TCGA"

    def __init__(self, fetcher: Any | None = None) -> None:
        self._fetcher = fetcher or _fetch_json

    def search(
        self,
        query: StructuredBioinformaticsQuery,
        *,
        online_enabled: bool,
        limit: int = 20,
        start: int = 0,
        timeout: int = 8,
    ) -> SourceSearchResult:
        project_ids = query.tcga_project_ids
        executed_query = ", ".join(project_ids)
        search_time = _now()
        if not online_enabled:
            candidates = tuple(_draft_candidate(project_id, query) for project_id in project_ids[: max(1, limit)])
            return SourceSearchResult(
                source=self.source,
                search_status="draft_only",
                executed_query=executed_query,
                total_found=None,
                returned_count=0,
                displayed_count=len(candidates),
                candidates=candidates,
                warnings=("仅生成 TCGA/GDC 项目映射，未执行在线检索。",) if project_ids else ("未映射到明确 TCGA/GDC 项目。",),
                database_source=self.database_source,
                search_time=search_time,
                query_payload={"tcga_project_ids": list(project_ids)},
            )
        if not project_ids:
            return SourceSearchResult(
                source=self.source,
                search_status="search_failed",
                executed_query="",
                total_found=0,
                returned_count=0,
                displayed_count=0,
                candidates=(),
                warnings=("未映射到明确 TCGA 癌种项目。",),
                error_message="No TCGA project mapping",
                database_source=self.database_source,
                search_time=search_time,
            )
        candidates: list[UnifiedDatasetCandidate] = []
        warnings: list[str] = []
        errors: list[str] = []
        for project_id in project_ids[: max(1, limit)]:
            try:
                candidates.append(self._candidate_for_project(project_id, query, timeout=timeout))
            except Exception as exc:
                errors.append(f"{project_id}:{exc}")
        status = "completed" if candidates else "search_failed"
        if errors:
            warnings.append("部分 TCGA/GDC 在线资产检查失败。")
        return SourceSearchResult(
            source=self.source,
            search_status=status,
            executed_query=executed_query,
            total_found=len(project_ids),
            returned_count=len(candidates),
            displayed_count=len(candidates),
            candidates=tuple(candidates),
            warnings=tuple(dict.fromkeys(warnings)),
            error_message="；".join(errors),
            database_source=self.database_source,
            search_time=search_time,
            start=start,
            fetched_all=True,
            query_payload={"tcga_project_ids": list(project_ids)},
        )

    def _candidate_for_project(
        self,
        project_id: str,
        query: StructuredBioinformaticsQuery,
        *,
        timeout: int,
    ) -> UnifiedDatasetCandidate:
        project_payload = self._fetcher(
            f"{GDC_API_ROOT}/projects/{project_id}",
            {"fields": "project_id,name,primary_site,disease_type,summary"},
            timeout,
        )
        files_payload = self._fetcher(
            f"{GDC_API_ROOT}/files",
            {
                "filters": json.dumps(_project_filter(project_id)),
                "fields": "file_id,file_name,data_category,data_type,workflow_type,cases.samples.sample_type",
                "format": "JSON",
                "size": "100",
            },
            timeout,
        )
        cases_payload = self._fetcher(
            f"{GDC_API_ROOT}/cases",
            {
                "filters": json.dumps(_project_filter(project_id)),
                "fields": "case_id,submitter_id,diagnoses.vital_status,diagnoses.days_to_death,diagnoses.days_to_last_follow_up,samples.sample_type",
                "format": "JSON",
                "size": "100",
            },
            timeout,
        )
        project = _payload_data(project_payload)
        files = _payload_hits(files_payload)
        cases = _payload_hits(cases_payload)
        metadata = _asset_metadata(project_id, files, cases, project)
        metadata["project_id"] = project_id
        metadata["project_name"] = str(project.get("name") or project_id)
        metadata["primary_site"] = str(project.get("primary_site") or "")
        metadata["disease_type"] = str(project.get("disease_type") or "")
        metadata["mapping_status"] = "online_checked_term_mapping"
        warnings = _warnings(metadata)
        return UnifiedDatasetCandidate(
            source=self.source,
            accession_or_project=project_id,
            display_title=str(project.get("name") or project_id),
            organism="Homo sapiens",
            disease=", ".join(query.disease_terms_en) or str(project.get("disease_type") or ""),
            tissue=", ".join(query.tissue_terms) or str(project.get("primary_site") or ""),
            data_modality="; ".join(metadata["data_type"]) or "TCGA/GDC project assets",
            sample_count=metadata["case_count"],
            has_expression_matrix=metadata["expression_file_availability"],
            has_sample_metadata=metadata["biospecimen_availability"],
            has_clinical_metadata=metadata["clinical_availability"],
            has_platform_annotation=False,
            recommended_analyses=_recommended_analyses(metadata),
            download_plan_available=metadata["expression_file_availability"],
            score=_score(metadata),
            warnings=warnings,
            source_specific_metadata=metadata,
        )


def _project_filter(project_id: str) -> dict[str, object]:
    return {"op": "in", "content": {"field": "cases.project.project_id", "value": [project_id]}}


def _draft_candidate(project_id: str, query: StructuredBioinformaticsQuery) -> UnifiedDatasetCandidate:
    metadata = {
        "project_id": project_id,
        "project_name": _project_name(project_id),
        "primary_site": _primary_site(project_id),
        "disease_type": _disease_type(project_id),
        "mapping_status": "mapped_not_online_checked",
        "record_shape": "tcga_gdc_project_mapping_candidate",
        "expression_file_availability": False,
        "clinical_availability": False,
        "survival_field_availability": False,
        "biospecimen_availability": False,
    }
    return UnifiedDatasetCandidate(
        source="tcga_gdc",
        accession_or_project=project_id,
        display_title=metadata["project_name"],
        organism="Homo sapiens",
        disease=", ".join(query.disease_terms_en) or metadata["disease_type"],
        tissue=", ".join(query.tissue_terms) or metadata["primary_site"],
        data_modality="TCGA/GDC project mapping candidate",
        sample_count="未在线检查",
        has_expression_matrix=False,
        has_sample_metadata=False,
        has_clinical_metadata=False,
        has_platform_annotation=False,
        recommended_analyses=("tcga_project_asset_preflight",),
        download_plan_available=False,
        score=55,
        warnings=("仅项目映射，表达文件、临床和 biospecimen 可用性尚未在线检查。",),
        source_specific_metadata=metadata,
    )


def _project_name(project_id: str) -> str:
    names = {
        "TCGA-GBM": "Glioblastoma Multiforme",
        "TCGA-LGG": "Brain Lower Grade Glioma",
        "TCGA-THCA": "Thyroid Carcinoma",
        "TCGA-ESCA": "Esophageal Carcinoma",
    }
    return names.get(project_id, project_id)


def _primary_site(project_id: str) -> str:
    sites = {"TCGA-GBM": "Brain", "TCGA-LGG": "Brain", "TCGA-THCA": "Thyroid", "TCGA-ESCA": "Esophagus"}
    return sites.get(project_id, "")


def _disease_type(project_id: str) -> str:
    diseases = {
        "TCGA-GBM": "Glioblastoma",
        "TCGA-LGG": "Lower grade glioma",
        "TCGA-THCA": "Thyroid carcinoma",
        "TCGA-ESCA": "Esophageal carcinoma",
    }
    return diseases.get(project_id, "")


def _payload_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data", payload)
    return data if isinstance(data, dict) else {}


def _payload_hits(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data", payload)
    hits = data.get("hits", []) if isinstance(data, dict) else []
    return [item for item in hits if isinstance(item, dict)]


def _asset_metadata(project_id: str, files: list[dict[str, Any]], cases: list[dict[str, Any]], project: dict[str, Any]) -> dict[str, Any]:
    data_categories = _unique(str(file.get("data_category") or "") for file in files)
    data_types = _unique(str(file.get("data_type") or "") for file in files)
    workflow_types = _unique(str(file.get("workflow_type") or "") for file in files)
    sample_types = _unique(_iter_sample_types(files, cases))
    expression_available = any("Gene Expression Quantification" in value or "Expression" in value for value in data_types)
    clinical_available = bool(cases) or any("Clinical" in value for value in data_categories)
    survival_available = any(_case_has_survival(case) for case in cases)
    biospecimen_available = bool(sample_types)
    return {
        "project_id": project_id,
        "data_category": data_categories,
        "data_type": data_types,
        "workflow_type": workflow_types,
        "sample_type": sample_types,
        "expression_file_availability": expression_available,
        "clinical_availability": clinical_available,
        "survival_field_availability": survival_available,
        "biospecimen_availability": biospecimen_available,
        "case_count": len(cases) if cases else str(project.get("summary", {}).get("case_count", "未知")),
        "file_count": len(files),
        "project": project,
        "record_shape": "tcga_gdc_project_asset_inventory",
    }


def _iter_sample_types(files: list[dict[str, Any]], cases: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for file in files:
        for case in file.get("cases", []) or []:
            for sample in case.get("samples", []) or []:
                values.append(str(sample.get("sample_type") or ""))
    for case in cases:
        for sample in case.get("samples", []) or []:
            values.append(str(sample.get("sample_type") or ""))
    return values


def _case_has_survival(case: dict[str, Any]) -> bool:
    for diagnosis in case.get("diagnoses", []) or []:
        if any(diagnosis.get(key) not in (None, "") for key in ("vital_status", "days_to_death", "days_to_last_follow_up")):
            return True
    return False


def _recommended_analyses(metadata: dict[str, Any]) -> tuple[str, ...]:
    analyses = ["tcga_asset_preflight"]
    if metadata["expression_file_availability"]:
        analyses.append("differential_expression")
    if metadata["clinical_availability"] and metadata["survival_field_availability"]:
        analyses.append("survival_analysis")
    return tuple(analyses)


def _warnings(metadata: dict[str, Any]) -> tuple[str, ...]:
    warnings: list[str] = []
    if not metadata["expression_file_availability"]:
        warnings.append("GDC files 查询未确认表达矩阵可用。")
    if not metadata["clinical_availability"]:
        warnings.append("GDC cases 查询未确认临床 metadata 可用。")
    if not metadata["survival_field_availability"]:
        warnings.append("未确认可用生存字段，生存分析前需复核 clinical 数据。")
    return tuple(warnings)


def _score(metadata: dict[str, Any]) -> int:
    score = 35
    for key in ("expression_file_availability", "clinical_availability", "survival_field_availability", "biospecimen_availability"):
        if metadata[key]:
            score += 15
    return min(score, 100)


def _unique(values: object) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:  # type: ignore[union-attr]
        text = str(value).strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            items.append(text)
    return items


def _fetch_json(url: str, params: dict[str, str], timeout: int) -> dict[str, Any]:
    full_url = f"{url}?{urlencode(params)}" if params else url
    with urlopen(full_url, timeout=timeout) as handle:
        return json.loads(handle.read().decode("utf-8"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
