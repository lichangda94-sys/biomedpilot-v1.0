"""Low-level file scanning and preview helpers."""

from __future__ import annotations

import csv
import gzip
import logging
import re
import zipfile
from pathlib import Path
from typing import Iterable, List
from xml.etree import ElementTree as ET

from .models import ContainerType, FileScanRecord
from .rules import MAX_PREVIEW_BYTES, MAX_PREVIEW_LINES, RAW_EXTENSIONS

LOGGER = logging.getLogger(__name__)
CELL_REF_RE = re.compile(r"([A-Z]+)")


def is_gzip_file(file_path: str) -> bool:
    """Return True when the file appears to be gzipped."""
    path = Path(file_path)
    if path.suffix.lower() == ".gz":
        return True
    try:
        with path.open("rb") as handle:
            return handle.read(2) == b"\x1f\x8b"
    except OSError:
        return False


def normalize_extension(file_path: str) -> str:
    """Normalize single and double extensions such as `.fastq.gz`."""
    path = Path(file_path)
    suffixes = [item.lower() for item in path.suffixes]
    if not suffixes:
        return ""
    if len(suffixes) >= 2 and suffixes[-1] == ".gz":
        return "".join(suffixes[-2:])
    return suffixes[-1]


def _open_text_preview(file_path: str):
    path = Path(file_path)
    if is_gzip_file(str(path)):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("rt", encoding="utf-8", errors="replace")


def read_text_head(file_path: str, max_lines: int = MAX_PREVIEW_LINES, max_bytes: int = MAX_PREVIEW_BYTES) -> List[str]:
    """Read a safe text preview with gzip and encoding tolerance."""
    lines: List[str] = []
    bytes_read = 0
    try:
        with _open_text_preview(file_path) as handle:
            for _ in range(max_lines):
                line = handle.readline()
                if not line:
                    break
                bytes_read += len(line.encode("utf-8", errors="ignore"))
                if bytes_read > max_bytes:
                    break
                lines.append(line.rstrip("\n\r"))
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.warning("Failed to preview text file %s: %s", file_path, exc)
    return lines


def preview_delimited_rows(lines: Iterable[str], max_rows: int = 40) -> List[List[str]]:
    """Parse preview lines with a best-effort CSV/TSV heuristic."""
    clean_lines = [line for line in lines if line.strip()][:max_rows]
    if not clean_lines:
        return []

    tab_hits = sum("\t" in line for line in clean_lines)
    comma_hits = sum("," in line for line in clean_lines)
    delimiter = "\t" if tab_hits >= comma_hits else ","

    rows: List[List[str]] = []
    try:
        reader = csv.reader(clean_lines, delimiter=delimiter)
        for row in reader:
            rows.append([cell.strip() for cell in row])
    except Exception:
        return []
    return rows


def preview_xlsx_rows(file_path: str, max_rows: int = 30, max_columns: int = 30) -> List[List[str]]:
    """Preview a small part of an Excel file using pandas when available."""
    def _stringify_block(frame) -> List[List[str]]:
        rows: List[List[str]] = []
        for row in frame.fillna("").astype(str).values.tolist():
            cleaned = [str(value).strip() for value in row[:max_columns]]
            if any(cell for cell in cleaned):
                rows.append(cleaned)
        return rows

    def _score_block(rows: List[List[str]]) -> tuple[float, int, int]:
        if not rows:
            return (0.0, 0, 0)
        width = max((len(row) for row in rows), default=0)
        numeric = 0
        total = 0
        for row in rows[1:]:
            for cell in row[1:]:
                value = str(cell).strip()
                if not value:
                    continue
                total += 1
                try:
                    float(value)
                except ValueError:
                    continue
                numeric += 1
        numeric_ratio = numeric / total if total else 0.0
        return (numeric_ratio + min(width / 10.0, 1.0), width, len(rows))

    def _column_index(cell_ref: str) -> int:
        match = CELL_REF_RE.match(cell_ref or "")
        if not match:
            return 0
        letters = match.group(1)
        index = 0
        for char in letters:
            index = index * 26 + (ord(char.upper()) - ord("A") + 1)
        return max(0, index - 1)

    def _xlsx_fallback_rows(path: str) -> List[List[str]]:
        try:
            with zipfile.ZipFile(path) as archive:
                shared_strings: List[str] = []
                if "xl/sharedStrings.xml" in archive.namelist():
                    with archive.open("xl/sharedStrings.xml") as handle:
                        for event, elem in ET.iterparse(handle, events=("end",)):
                            if elem.tag.endswith("si"):
                                text = "".join(node.text or "" for node in elem.findall(".//{*}t"))
                                shared_strings.append(text)
                                elem.clear()

                best_rows: List[List[str]] = []
                best_score: tuple[float, int, int] = (0.0, 0, 0)
                sheet_names = sorted(name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"))
                for sheet_name in sheet_names[:5]:
                    collected: List[List[str]] = []
                    with archive.open(sheet_name) as handle:
                        for event, row in ET.iterparse(handle, events=("end",)):
                            if not row.tag.endswith("row"):
                                continue
                            values: List[str] = [""] * max_columns
                            for cell in row.findall("{*}c"):
                                column = _column_index(cell.attrib.get("r", ""))
                                if column >= max_columns:
                                    continue
                                cell_type = cell.attrib.get("t", "")
                                value = ""
                                if cell_type == "inlineStr":
                                    value = "".join(node.text or "" for node in cell.findall(".//{*}t"))
                                else:
                                    v = cell.find("{*}v")
                                    if v is not None and v.text is not None:
                                        raw = v.text
                                        if cell_type == "s":
                                            try:
                                                value = shared_strings[int(raw)]
                                            except Exception:
                                                value = raw
                                        else:
                                            value = raw
                                values[column] = str(value).strip()
                            if any(values):
                                collected.append(values)
                            row.clear()
                            if len(collected) >= max_rows * 4:
                                break
                    for start in range(0, min(len(collected), max_rows * 2)):
                        window = [row[:max_columns] for row in collected[start : start + max_rows]]
                        score = _score_block(window)
                        if score > best_score:
                            best_rows = window
                            best_score = score
                return best_rows[:max_rows]
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("Failed fallback Excel preview for %s: %s", path, exc)
            return []

    try:
        import pandas as pd
    except Exception:  # pragma: no cover - dependency optional
        return _xlsx_fallback_rows(file_path)

    try:
        workbook = pd.ExcelFile(file_path)
        best_rows: List[List[str]] = []
        best_score: tuple[float, int, int] = (0.0, 0, 0)
        for sheet_name in workbook.sheet_names[:5]:
            frame = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=max_rows * 4)
            if frame.empty:
                continue
            for start in range(0, min(len(frame), max_rows * 2)):
                window = frame.iloc[start : start + max_rows, :max_columns]
                rows = _stringify_block(window)
                score = _score_block(rows)
                if score > best_score:
                    best_rows = rows
                    best_score = score
        return best_rows[:max_rows]
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.warning("Failed to preview Excel file %s: %s", file_path, exc)
        return _xlsx_fallback_rows(file_path)


def guess_initial_container(file_path: str) -> str:
    """Estimate container type from filename and extension only."""
    name = Path(file_path).name.lower()
    ext = normalize_extension(file_path)
    if "series_matrix" in name:
        return ContainerType.SERIES_MATRIX.value
    if "family.soft" in name or ext == ".soft":
        return ContainerType.FAMILY_SOFT.value
    if ext == ".xml":
        return ContainerType.MINIML.value
    if ext in RAW_EXTENSIONS:
        return ContainerType.RAW_FILE.value
    if any(token in name for token in ("gpl", "platform", "annot")):
        return ContainerType.PLATFORM_ANNOTATION.value
    return ContainerType.SUPPLEMENTARY.value


def scan_dataset_files(root_dir: str) -> list[FileScanRecord]:
    """Recursively scan dataset files and record basic filesystem attributes."""
    root = Path(root_dir).expanduser().resolve()
    records: list[FileScanRecord] = []
    if not root.exists():
        return records

    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        try:
            stat = path.stat()
        except OSError as exc:
            LOGGER.warning("Skipping file with stat failure %s: %s", path, exc)
            continue
        records.append(
            FileScanRecord(
                path=str(path),
                relative_path=str(path.relative_to(root)),
                name=path.name,
                extension=normalize_extension(str(path)),
                is_gzip=is_gzip_file(str(path)),
                size_bytes=stat.st_size,
                initial_container_guess=guess_initial_container(str(path)),
            )
        )
    return records
