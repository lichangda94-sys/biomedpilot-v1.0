from __future__ import annotations

from app.labtools.image_analysis import IMAGE_REVIEW_NOTICE
from app.labtools.image_analysis.audit_models import ImageAnalysisAuditRecord
from app.labtools.image_analysis.image_models import LabImageRecord
from app.labtools.image_analysis.roi_models import ROIRecord, empty_roi_placeholder


def test_lab_image_record_exports_json_compatible_dict(tmp_path) -> None:
    image_path = tmp_path / "sample.png"
    image_path.write_bytes(b"png")

    record = LabImageRecord.from_path(image_path, notes="manual import")
    payload = record.to_dict()

    assert payload["filename"] == "sample.png"
    assert payload["file_extension"] == ".png"
    assert payload["file_size_bytes"] == 3
    assert payload["source_path"].endswith("sample.png")
    assert payload["warnings"] == []


def test_roi_and_audit_records_export_dicts() -> None:
    roi = ROIRecord(roi_type="polygon", label="手动 ROI", coordinates=((0, 0), (1.5, 2.0)))
    audit = ImageAnalysisAuditRecord(event_type="created", message="创建草稿", details={"review": True})

    assert roi.to_dict()["coordinates"] == [[0, 0], [1.5, 2.0]]
    assert audit.to_dict()["details"] == {"review": True}
    assert "尚未执行自动定量" in IMAGE_REVIEW_NOTICE


def test_empty_roi_placeholder_has_no_coordinates() -> None:
    roi = empty_roi_placeholder("cell_counting")

    assert roi.roi_type == "not_configured"
    assert roi.coordinates == ()
    assert roi.user_defined is False
