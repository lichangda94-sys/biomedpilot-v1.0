from __future__ import annotations

import pytest

from app.labtools.image_analysis.image_io import create_image_record, validate_image_path
from app.labtools.image_analysis.image_models import ImageAnalysisError


def test_create_image_record_validates_local_path_without_copying(tmp_path) -> None:
    image_path = tmp_path / "cells.tif"
    image_path.write_bytes(b"image-bytes")

    record = create_image_record(str(image_path), notes="primary")

    assert record.filename == "cells.tif"
    assert record.file_extension == ".tif"
    assert record.file_size_bytes == len(b"image-bytes")
    assert record.notes == "primary"
    assert record.validation_status == "valid"


def test_image_path_validation_rejects_missing_or_unknown_files(tmp_path) -> None:
    with pytest.raises(ImageAnalysisError, match="图片路径不存在"):
        validate_image_path(tmp_path / "missing.png")

    text_path = tmp_path / "notes.txt"
    text_path.write_text("not an image")
    with pytest.raises(ImageAnalysisError, match="暂不支持该图片格式"):
        validate_image_path(text_path)


def test_empty_image_file_creates_warning_record(tmp_path) -> None:
    image_path = tmp_path / "empty.jpg"
    image_path.write_bytes(b"")

    record = create_image_record(image_path)

    assert record.validation_status == "valid_with_warnings"
    assert "大小为 0" in record.warnings[0]
