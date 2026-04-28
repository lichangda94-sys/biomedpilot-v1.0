from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sys


LEGACY_ROOT = Path(__file__).resolve().parents[1] / "legacy"


@dataclass(frozen=True)
class GeoAssetDetectionItem:
    accession: str
    scan_root: str
    validation_status: str
    recommended_strategy: str
    has_expression_payload: bool
    has_sample_annotation: bool
    candidate_expression_files: list[str]
    candidate_metadata_files: list[str]
    warnings: list[str]
    errors: list[str]
    next_action: str


class GeoAssetDetectionAdapter:
    def detect_from_download_plan(self, payload: dict[str, object]) -> list[GeoAssetDetectionItem]:
        items = list(payload.get("download_items", []))
        results: list[GeoAssetDetectionItem] = []
        with _legacy_geo_processing_path():
            from geo_processing import detect_dataset

            for item in items:
                item_payload = item if isinstance(item, dict) else {}
                accession = str(item_payload.get("accession", "")).strip().upper()
                target_dir = str(item_payload.get("target_dir", "")).strip()
                if not accession or not target_dir:
                    continue
                detection = detect_dataset(accession, target_dir)
                detection_payload = detection.to_dict()
                results.append(
                    GeoAssetDetectionItem(
                        accession=accession,
                        scan_root=str(detection_payload.get("scan_root", target_dir)),
                        validation_status=str(detection_payload.get("extra", {}).get("validation_status", "")),
                        recommended_strategy=str(detection_payload.get("recommended_strategy", "")),
                        has_expression_payload=bool(detection_payload.get("has_expression_payload", False)),
                        has_sample_annotation=bool(detection_payload.get("has_sample_annotation", False)),
                        candidate_expression_files=list(detection_payload.get("candidate_expression_files", [])),
                        candidate_metadata_files=list(detection_payload.get("candidate_metadata_files", [])),
                        warnings=list(detection_payload.get("warnings", [])),
                        errors=list(detection_payload.get("extra", {}).get("validation_errors", [])),
                        next_action=str(detection_payload.get("next_action", "")),
                    )
                )
        return results


@contextmanager
def _legacy_geo_processing_path():
    inserted: list[str] = []
    for path in (str(LEGACY_ROOT),):
        if path not in sys.path:
            sys.path.insert(0, path)
            inserted.append(path)
    try:
        yield
    finally:
        for path in inserted:
            try:
                sys.path.remove(path)
            except ValueError:
                pass
