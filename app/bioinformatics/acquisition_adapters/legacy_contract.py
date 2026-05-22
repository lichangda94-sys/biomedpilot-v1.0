from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LEGACY_ACQUISITION_SCHEMA_VERSION = "biomedpilot.legacy_acquisition_adapter.v1"
LEGACY_ADAPTER_MANIFEST_DIR = Path("acquisition") / "legacy_adapter_manifests"

FORMAL_RESULT_SEMANTICS = {"formal_computed_result", "report_ready_result"}
FORMAL_OUTPUT_ASSET_TYPES = {
    "formal_deg_result",
    "formal_ora_result",
    "formal_gsea_result",
    "survival_km_logrank",
    "cox_univariate",
    "formal_plot_artifact",
    "report_ready_package",
}


@dataclass(frozen=True)
class LegacyAcquisitionManifest:
    source: str
    source_version: str
    legacy_module_reference: str
    input_path_or_query: str
    output_asset_type: str
    provenance: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    checksum: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    adapter_id: str = ""
    status: str = "blocked"
    schema_version: str = LEGACY_ACQUISITION_SCHEMA_VERSION
    downstream_contract: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["warnings"] = list(self.warnings)
        payload["blockers"] = list(self.blockers)
        payload["adapter_id"] = self.adapter_id or _adapter_id(payload)
        payload["status"] = self.status or ("blocked" if self.blockers else "manifest_only")
        payload["downstream_contract"] = _downstream_contract(self.downstream_contract)
        return payload


def adapt_geo_detection_manifest(
    *,
    accession: str,
    scan_root: str | Path,
    detection_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(scan_root).expanduser()
    detection = dict(detection_result or {})
    if not detection:
        from app.bioinformatics.legacy.geo_processing.detector import detect_dataset

        detection = detect_dataset(accession, str(root)).to_dict()
    warnings = _strings(detection.get("warnings"))
    blockers: list[str] = []
    if not bool(detection.get("has_expression_payload")):
        blockers.append("geo_legacy_detection_missing_expression_payload")
    if str(detection.get("matrix_level") or "").lower() in {"probe", "id_ref", "unknown"}:
        warnings.append("geo_probe_or_unknown_mapping_requires_later_standardization_gate")
    manifest = LegacyAcquisitionManifest(
        source="geo",
        source_version="legacy_geo_processing_detector",
        legacy_module_reference="app.bioinformatics.legacy.geo_processing.detector.detect_dataset",
        input_path_or_query=f"{accession}:{root}",
        output_asset_type="geo_detection_acquisition_candidate",
        provenance={
            "accession": accession,
            "accession_type": detection.get("accession_type", ""),
            "recommended_strategy": detection.get("recommended_strategy", ""),
            "technology_type": detection.get("technology_type", ""),
            "matrix_level": detection.get("matrix_level", ""),
            "value_semantic": detection.get("value_semantic", ""),
            "candidate_expression_files": list(detection.get("candidate_expression_files") or []),
            "candidate_metadata_files": list(detection.get("candidate_metadata_files") or []),
            "candidate_annotation_files": list(detection.get("candidate_annotation_files") or []),
            "payload_type": detection.get("payload_type", ""),
            "legacy_detection": detection,
        },
        warnings=tuple(_dedupe(warnings)),
        blockers=tuple(_dedupe(blockers)),
        checksum=_file_or_text_checksum(root if root.exists() and root.is_file() else f"{accession}:{root}"),
        status="blocked" if blockers else "manifest_only",
    )
    return manifest.to_dict()


def adapt_tcga_preview_manifest(*, preview_summary: dict[str, Any], input_query: str = "") -> dict[str, Any]:
    summary = dict(preview_summary)
    request = summary.get("request") if isinstance(summary.get("request"), dict) else {}
    warnings = _strings(summary.get("warnings"))
    blockers: list[str] = []
    if str(summary.get("status") or "") not in {"ready", "warning", "completed"}:
        blockers.append("tcga_preview_not_ready_for_acquisition_manifest")
    if not summary.get("file_manifest_entries"):
        warnings.append("tcga_preview_has_no_file_manifest_entries")
    manifest = LegacyAcquisitionManifest(
        source="tcga_gdc",
        source_version="current_tcga_preview_or_legacy_tcga_gtex_adapter",
        legacy_module_reference="app.bioinformatics.data_sources.tcga_preview",
        input_path_or_query=input_query or str(request.get("project_id") or ""),
        output_asset_type="tcga_gdc_acquisition_manifest_candidate",
        provenance={
            "project_id": request.get("project_id", summary.get("project_id", "")),
            "analysis_purpose": request.get("analysis_purpose", summary.get("analysis_purpose", "")),
            "sample_scope": request.get("sample_scope", summary.get("sample_scope", "")),
            "file_count": summary.get("file_count", 0),
            "case_count": summary.get("case_count", 0),
            "sample_count": summary.get("sample_count", 0),
            "gdc_filters": summary.get("gdc_filters", {}),
            "case_filters": summary.get("case_filters", {}),
            "file_manifest_entries": list(summary.get("file_manifest_entries") or []),
        },
        warnings=tuple(_dedupe(warnings)),
        blockers=tuple(_dedupe(blockers)),
        checksum=_text_checksum(json.dumps(summary, sort_keys=True, default=str)),
        status="blocked" if blockers else "manifest_only",
    )
    return manifest.to_dict()


def adapt_gtex_preview_manifest(*, preview_summary: dict[str, Any], input_query: str = "") -> dict[str, Any]:
    summary = dict(preview_summary)
    request = summary.get("request") if isinstance(summary.get("request"), dict) else {}
    warnings = _strings(summary.get("warnings"))
    blockers: list[str] = []
    if str(summary.get("status") or "") not in {"ready", "warning", "completed"}:
        blockers.append("gtex_preview_not_ready_for_acquisition_manifest")
    warnings.append("gtex_must_remain_independent_not_tcga_normal_control")
    manifest = LegacyAcquisitionManifest(
        source="gtex",
        source_version="current_gtex_preview_or_legacy_tcga_gtex_adapter",
        legacy_module_reference="app.bioinformatics.data_sources.gtex_preview",
        input_path_or_query=input_query or str(request.get("tissue_site_detail") or request.get("tissue_id") or ""),
        output_asset_type="gtex_acquisition_manifest_candidate",
        provenance={
            "tissue_id": request.get("tissue_id", summary.get("tissue_id", "")),
            "tissue_site_detail": request.get("tissue_site_detail", summary.get("tissue_site_detail", "")),
            "use_purpose": request.get("use_purpose", summary.get("use_purpose", "")),
            "donor_count": summary.get("donor_count", 0),
            "sample_count": summary.get("sample_count", 0),
            "file_count": summary.get("file_count", 0),
            "file_manifest_entries": list(summary.get("file_manifest_entries") or []),
            "tissue_metadata": summary.get("tissue_metadata", {}),
        },
        warnings=tuple(_dedupe(warnings)),
        blockers=tuple(_dedupe(blockers)),
        checksum=_text_checksum(json.dumps(summary, sort_keys=True, default=str)),
        status="blocked" if blockers else "manifest_only",
    )
    return manifest.to_dict()


def validate_legacy_acquisition_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    for field_name in (
        "schema_version",
        "source",
        "source_version",
        "legacy_module_reference",
        "input_path_or_query",
        "output_asset_type",
        "provenance",
        "warnings",
        "blockers",
        "created_at",
        "downstream_contract",
    ):
        if field_name not in manifest:
            blockers.append(f"missing_required_field:{field_name}")
    if manifest.get("schema_version") != LEGACY_ACQUISITION_SCHEMA_VERSION:
        blockers.append("legacy_acquisition_schema_version_mismatch")
    if manifest.get("output_asset_type") in FORMAL_OUTPUT_ASSET_TYPES:
        blockers.append("legacy_adapter_output_must_not_be_formal_result")
    semantics = str(manifest.get("result_semantics") or manifest.get("canonical_result_semantics") or "")
    if semantics in FORMAL_RESULT_SEMANTICS:
        blockers.append("legacy_adapter_must_not_set_formal_result_semantics")
    if manifest.get("report_ready_eligible") is True:
        blockers.append("legacy_adapter_report_ready_forbidden")
    contract = manifest.get("downstream_contract") if isinstance(manifest.get("downstream_contract"), dict) else {}
    if contract.get("writes_formal_result") is not False:
        blockers.append("legacy_adapter_must_not_write_formal_result")
    if contract.get("ready_for_formal_analysis") is not False:
        blockers.append("legacy_adapter_must_not_be_formal_analysis_ready")
    if contract.get("must_pass_b8_resolver") is not True:
        blockers.append("legacy_adapter_must_require_b8_resolver")
    if contract.get("must_pass_standardization") is not True:
        blockers.append("legacy_adapter_must_require_standardization")
    if str(manifest.get("source") or "") == "gtex" and contract.get("can_fill_tcga_normal_control") is not False:
        blockers.append("gtex_adapter_must_not_fill_tcga_normal_control")
    if manifest.get("status") == "manifest_only" and manifest.get("blockers"):
        warnings.append("manifest_status_should_reflect_blockers")
    status = "blocked" if blockers else "passed"
    return {
        "schema_version": "biomedpilot.legacy_acquisition_adapter_validation.v1",
        "status": status,
        "blockers": _dedupe(blockers),
        "warnings": _dedupe(warnings),
        "adapter_id": manifest.get("adapter_id", ""),
        "source": manifest.get("source", ""),
    }


def write_legacy_acquisition_manifest(project_root: str | Path, manifest: dict[str, Any]) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    payload = dict(manifest)
    payload.setdefault("adapter_id", _adapter_id(payload))
    validation = validate_legacy_acquisition_manifest(payload)
    payload["validation_status"] = validation["status"]
    payload["validation_blockers"] = validation["blockers"]
    target = root / LEGACY_ADAPTER_MANIFEST_DIR / f"{payload['adapter_id']}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "status": validation["status"],
        "manifest_path": str(target),
        "manifest": payload,
        "validation": validation,
    }


def _downstream_contract(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(contract or {})
    payload.update(
        {
            "writes_formal_result": False,
            "ready_for_formal_analysis": False,
            "must_pass_standardization": True,
            "must_pass_b8_resolver": True,
            "allowed_next_layers": ["acquisition_manifest", "standardized_asset_candidate", "analysis_input_resolver"],
            "forbidden_next_layers": ["formal_result_index", "formal_plot", "report_ready_package"],
            "can_fill_tcga_normal_control": False,
        }
    )
    return payload


def _adapter_id(payload: dict[str, Any]) -> str:
    seed = "|".join(
        [
            str(payload.get("source") or ""),
            str(payload.get("legacy_module_reference") or ""),
            str(payload.get("input_path_or_query") or ""),
            str(payload.get("output_asset_type") or ""),
        ]
    )
    return f"legacy-adapter-{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"


def _file_or_text_checksum(value: str | Path) -> str:
    path = Path(value) if not isinstance(value, Path) else value
    if path.exists() and path.is_file():
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return f"sha256:{digest.hexdigest()}"
    return _text_checksum(str(value))


def _text_checksum(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _strings(value: object) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item)]
    if value:
        return [str(value)]
    return []


def _dedupe(values: list[str] | tuple[str, ...]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
