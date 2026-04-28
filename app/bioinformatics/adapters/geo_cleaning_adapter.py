from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeoCleaningPlanItem:
    accession: str
    expression_files: list[str]
    metadata_files: list[str]
    status: str
    next_action: str


class GeoCleaningAdapter:
    def build_cleaning_plan(self, asset_detection_payload: dict[str, object]) -> list[GeoCleaningPlanItem]:
        detections = list(asset_detection_payload.get("detections", []))
        items: list[GeoCleaningPlanItem] = []
        for detection in detections:
            detection_payload = detection if isinstance(detection, dict) else {}
            expression_files = list(detection_payload.get("candidate_expression_files", []))
            metadata_files = list(detection_payload.get("candidate_metadata_files", []))
            status = "ready_for_cleaning" if expression_files else "blocked_no_expression_payload"
            next_action = (
                "Run controlled normalization after confirming matrix format."
                if expression_files
                else "Provide local expression matrix files or run a confirmed download first."
            )
            items.append(
                GeoCleaningPlanItem(
                    accession=str(detection_payload.get("accession", "")),
                    expression_files=expression_files,
                    metadata_files=metadata_files,
                    status=status,
                    next_action=next_action,
                )
            )
        return items
