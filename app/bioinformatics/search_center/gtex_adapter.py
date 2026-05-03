from __future__ import annotations

from datetime import datetime, timezone
import json
import ssl
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from .models import SourceSearchResult, StructuredBioinformaticsQuery, UnifiedDatasetCandidate


GTEX_API_ROOT = "https://gtexportal.org/api/v2"
GTEX_BATCH_WARNING = "GTEx 是正常组织参考；与 TCGA 联合分析前必须处理 TCGA-GTEx batch effect。"


class GtexSearchAdapter:
    source = "gtex"
    database_source = "GTEx Portal"

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
        tissues = query.gtex_tissues[: max(1, limit)]
        executed_query = ", ".join(tissues)
        search_time = _now()
        if not online_enabled:
            candidates = tuple(_draft_candidate(tissue, query) for tissue in tissues)
            return SourceSearchResult(
                source=self.source,
                search_status="draft_only",
                executed_query=executed_query,
                total_found=None,
                returned_count=0,
                displayed_count=len(candidates),
                candidates=candidates,
                warnings=("仅生成 GTEx 组织映射，未执行在线检索。", GTEX_BATCH_WARNING),
                database_source=self.database_source,
                search_time=search_time,
                query_payload={"gtex_tissues": list(tissues)},
            )
        candidates: list[UnifiedDatasetCandidate] = []
        errors: list[str] = []
        user_warnings: list[str] = []
        raw_errors: list[str] = []
        for tissue in tissues:
            try:
                candidates.append(self._candidate_for_tissue(tissue, query, timeout=timeout))
            except Exception as exc:
                friendly = _friendly_error_message(exc)
                user_warnings.append(friendly)
                errors.append(f"{tissue}:{friendly}")
                raw_errors.append(f"{tissue}:{exc}")
                candidates.append(_fallback_candidate(tissue, query, warning=friendly))
        status = "completed" if candidates else "search_failed"
        warnings = [GTEX_BATCH_WARNING]
        warnings.extend(user_warnings)
        return SourceSearchResult(
            source=self.source,
            search_status=status,
            executed_query=executed_query,
            total_found=len(tissues),
            returned_count=len(candidates),
            displayed_count=len(candidates),
            candidates=tuple(candidates),
            warnings=tuple(dict.fromkeys(warnings)),
            error_message="；".join(dict.fromkeys(errors)),
            database_source=self.database_source,
            search_time=search_time,
            start=start,
            fetched_all=True,
            query_payload={"gtex_tissues": list(tissues), "raw_errors": raw_errors},
        )

    def _candidate_for_tissue(
        self,
        tissue: str,
        query: StructuredBioinformaticsQuery,
        *,
        timeout: int,
    ) -> UnifiedDatasetCandidate:
        payload = self._fetcher(
            f"{GTEX_API_ROOT}/dataset/tissueSiteDetail",
            {"tissueSiteDetailId": tissue, "format": "json"},
            timeout,
        )
        record = _first_record(payload) or {"tissueSiteDetailId": tissue, "tissueSiteDetail": tissue}
        sample_count = _sample_count(record)
        expression_available = sample_count not in (0, "未知")
        metadata = {
            "tissue_name": tissue,
            "normal_reference": True,
            "expression_availability": expression_available,
            "sample_count": sample_count,
            "expression_matrix_version": record.get("datasetId") or record.get("version") or "",
            "recommended_usage": "normal_expression_reference",
            "raw_record": record,
        }
        return UnifiedDatasetCandidate(
            source=self.source,
            accession_or_project=f"GTEX-{_slugify(tissue)}",
            display_title=f"GTEx {record.get('tissueSiteDetail') or tissue}",
            organism="Homo sapiens",
            disease="normal reference",
            tissue=str(record.get("tissueSiteDetail") or tissue),
            data_modality="normal tissue expression reference",
            sample_count=sample_count,
            has_expression_matrix=expression_available,
            has_sample_metadata=True,
            has_clinical_metadata=False,
            has_platform_annotation=False,
            recommended_analyses=("normal_reference", "tcga_gtex_joint_analysis_after_batch_correction"),
            download_plan_available=expression_available,
            score=80 if expression_available else 50,
            warnings=(GTEX_BATCH_WARNING,),
            source_specific_metadata=metadata,
        )


def _first_record(payload: dict[str, Any]) -> dict[str, Any] | None:
    data = payload.get("data", payload)
    if isinstance(data, list) and data:
        first = data[0]
        return first if isinstance(first, dict) else None
    if isinstance(data, dict):
        for key in ("tissueSiteDetail", "tissueSiteDetails", "items", "results"):
            value = data.get(key)
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value[0]
        return data
    return None


def _sample_count(record: dict[str, Any]) -> int | str:
    for key in ("rnaSeqSampleCount", "sampleCount", "samples", "count"):
        value = record.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return "未知"


def _slugify(value: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in value.upper()).strip("-")


def _friendly_error_message(exc: Exception) -> str:
    text = str(exc)
    if isinstance(exc, ssl.SSLError) or "CERTIFICATE_VERIFY_FAILED" in text or "certificate verify failed" in text.lower():
        return "GTEx 在线检查失败：证书验证失败；已保留候选正常组织参考。"
    return "GTEx 在线检查失败；已保留候选正常组织参考。"


def _fallback_candidate(tissue: str, query: StructuredBioinformaticsQuery, *, warning: str) -> UnifiedDatasetCandidate:
    return UnifiedDatasetCandidate(
        source="gtex",
        accession_or_project=f"GTEX-{_slugify(tissue)}",
        display_title=f"GTEx {tissue} normal reference",
        organism="Homo sapiens",
        disease="normal reference",
        tissue=tissue,
        data_modality="normal tissue expression reference",
        sample_count="未知",
        has_expression_matrix=False,
        has_sample_metadata=False,
        has_clinical_metadata=False,
        has_platform_annotation=False,
        recommended_analyses=("normal_reference", "tcga_gtex_joint_analysis_after_batch_correction"),
        download_plan_available=False,
        score=45,
        warnings=(warning, GTEX_BATCH_WARNING),
        source_specific_metadata={
            "tissue_name": tissue,
            "normal_reference": True,
            "expression_availability": False,
            "recommended_usage": "normal_reference_candidate_pending_online_check",
            "query_disease_terms": list(query.disease_terms_en),
        },
    )


def _draft_candidate(tissue: str, query: StructuredBioinformaticsQuery) -> UnifiedDatasetCandidate:
    return UnifiedDatasetCandidate(
        source="gtex",
        accession_or_project=f"GTEX-{_slugify(tissue)}",
        display_title=f"GTEx {tissue} normal reference",
        organism="Homo sapiens",
        disease="normal reference",
        tissue=tissue,
        data_modality="normal tissue expression reference",
        sample_count="未在线检查",
        has_expression_matrix=False,
        has_sample_metadata=False,
        has_clinical_metadata=False,
        has_platform_annotation=False,
        recommended_analyses=("normal_reference", "tcga_gtex_joint_analysis_after_batch_correction"),
        download_plan_available=False,
        score=50,
        warnings=(GTEX_BATCH_WARNING,),
        source_specific_metadata={
            "tissue_name": tissue,
            "normal_reference": True,
            "mapping_status": "mapped_not_online_checked",
            "recommended_usage": "normal_reference_candidate",
            "query_disease_terms": list(query.disease_terms_en),
        },
    )


def _fetch_json(url: str, params: dict[str, str], timeout: int) -> dict[str, Any]:
    full_url = f"{url}?{urlencode(params)}" if params else url
    with urlopen(full_url, timeout=timeout) as handle:
        return json.loads(handle.read().decode("utf-8"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
