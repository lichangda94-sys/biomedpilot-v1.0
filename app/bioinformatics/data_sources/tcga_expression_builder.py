from __future__ import annotations

import csv
import gzip
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from app.bioinformatics.acquisition_file_records import build_file_record
from app.bioinformatics.project_workspace_binding import AcquisitionSummary, LATEST_RECORD, register_acquisition
from app.bioinformatics.standard_assets.tcga_assets import (
    TCGA_EXPRESSION_MATRIX,
    TCGA_PREPARE_MANIFEST,
    TCGA_SAMPLE_METADATA,
    build_tcga_asset_paths,
    write_tcga_prepare_manifest,
)
from app.bioinformatics.tcga.barcode import parse_tcga_barcode
from app.bioinformatics.tcga.sample_metadata import build_tcga_sample_metadata


TCGA_EXPRESSION_BUILD_MANIFEST_SCHEMA_VERSION = "biomedpilot.tcga_expression_build_manifest.v1"

_ENSEMBL_VERSION_RE = re.compile(r"^(ENSG[0-9]+)\.[0-9]+$", re.IGNORECASE)
_METRIC_COLUMNS = {
    "raw_counts": ("unstranded", "raw_count", "raw_counts", "count", "counts"),
    "tpm": ("tpm_unstranded", "tpm"),
    "fpkm": ("fpkm_unstranded", "fpkm"),
    "fpkm_uq": ("fpkm_uq_unstranded", "fpkm_uq", "fpkm-uq"),
}


@dataclass(frozen=True)
class TCGAExpressionBuildResult:
    success: bool
    status: str
    message: str
    project_id: str
    build_id: str
    raw_acquisition_record_path: Path
    build_manifest_path: Path
    prepare_manifest_path: Path
    expression_matrix_path: Path
    sample_metadata_path: Path
    sample_mapping_path: Path
    gene_annotation_path: Path
    metric_matrix_paths: dict[str, str]
    source_file_count: int
    parsed_file_count: int
    sample_count: int
    gene_count: int
    warnings: tuple[str, ...]
    acquisition_summary: AcquisitionSummary | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        for key in (
            "raw_acquisition_record_path",
            "build_manifest_path",
            "prepare_manifest_path",
            "expression_matrix_path",
            "sample_metadata_path",
            "sample_mapping_path",
            "gene_annotation_path",
        ):
            payload[key] = str(payload[key])
        if self.acquisition_summary is not None:
            payload["acquisition_summary"] = {
                "acquisition_id": self.acquisition_summary.acquisition_id,
                "source_files": list(self.acquisition_summary.source_files),
                "record_path": str(self.acquisition_summary.record_path),
            }
        return payload


class TCGAExpressionQuantificationBuilder:
    def build_latest(self, project_root: str | Path, *, project_id: str | None = None) -> TCGAExpressionBuildResult:
        record_path = latest_tcga_raw_expression_record_path(project_root, project_id=project_id)
        if record_path is None:
            raise FileNotFoundError("未找到等待 B6.4 构建表达矩阵的 TCGA B6.3 原始文件记录。")
        return self.build_from_record(project_root, record_path=record_path)

    def build_from_record(self, project_root: str | Path, *, record_path: str | Path) -> TCGAExpressionBuildResult:
        root = Path(project_root).expanduser().resolve()
        raw_record_path = Path(record_path).expanduser().resolve()
        raw_record = _read_json(raw_record_path)
        metadata = raw_record.get("metadata") if isinstance(raw_record.get("metadata"), dict) else {}
        if not isinstance(metadata, dict):
            metadata = {}
        project_id = str(metadata.get("project_id") or raw_record.get("source_label") or "").strip().upper()
        if not project_id:
            raise ValueError("TCGA B6.3 记录缺少 project_id。")
        if str(metadata.get("analysis_gate_status") or "") != "waiting_b6_4_expression_matrix_build":
            raise ValueError("该 TCGA 记录不是等待 B6.4 表达矩阵构建的原始文件记录。")

        source_files = [Path(path).expanduser().resolve() for path in _string_list(raw_record.get("source_files"))]
        file_records = _file_records_for_raw_record(raw_record, metadata)
        records_by_path = {str(Path(str(record.get("local_path") or "")).expanduser().resolve()): record for record in file_records if str(record.get("local_path") or "")}

        parsed_samples: list[_ParsedSample] = []
        warnings: list[str] = []
        for path in source_files:
            record = records_by_path.get(str(path), {})
            if not _is_expression_quantification_file(path, record):
                warnings.append(f"non_expression_file_skipped:{path.name}")
                continue
            sample_mapping = _sample_mapping_for_file(path, record, warnings)
            parsed_samples.append(_parse_quantification_file(path, sample_mapping, warnings))

        if not parsed_samples:
            raise ValueError("未识别到可解析的 TCGA RNA-seq gene expression quantification 文件。")

        build_id = f"tcga-b64-{uuid4().hex[:10]}"
        asset_paths = build_tcga_asset_paths(root / "standardized_data", project_id, build_id, layout="data_prepared")
        expression_matrix_path = asset_paths[TCGA_EXPRESSION_MATRIX]
        sample_metadata_path = asset_paths[TCGA_SAMPLE_METADATA]
        prepare_manifest_path = asset_paths[TCGA_PREPARE_MANIFEST]
        base_dir = prepare_manifest_path.parent
        metric_paths = {
            "raw_counts": expression_matrix_path,
            "tpm": base_dir / "expression" / "tcga_tpm_matrix.csv",
            "fpkm": base_dir / "expression" / "tcga_fpkm_matrix.csv",
            "fpkm_uq": base_dir / "expression" / "tcga_fpkm_uq_matrix.csv",
        }
        sample_mapping_path = base_dir / "sample_metadata" / "tcga_sample_file_mapping.csv"
        gene_annotation_path = base_dir / "expression" / "tcga_gene_annotation.csv"
        build_manifest_path = base_dir / "tcga_expression_build_manifest.json"

        sample_names = [sample.sample_barcode for sample in parsed_samples]
        gene_order, annotations, matrices = _build_matrices(parsed_samples, warnings)
        for metric, path in metric_paths.items():
            _write_matrix(path, sample_names, gene_order, matrices[metric])
        _write_gene_annotation(gene_annotation_path, gene_order, annotations)
        _write_sample_mapping(sample_mapping_path, parsed_samples)
        _write_sample_metadata(sample_metadata_path, parsed_samples, warnings)

        prepare_manifest = write_tcga_prepare_manifest(
            prepare_manifest_path,
            project_id=project_id,
            batch_id=build_id,
            source="tcga_gdc_b6_3_source_files",
            asset_paths=asset_paths,
            sample_count=len(sample_names),
            gene_count=len(gene_order),
            normalization="raw_counts_primary_plus_tpm_fpkm_fpkm_uq",
            warnings=warnings,
            parameters={
                "b6_3_acquisition_record_path": str(raw_record_path),
                "download_receipt_path": str(metadata.get("download_receipt_path") or ""),
                "download_manifest_path": str(metadata.get("download_manifest_path") or ""),
                "metric_matrix_paths": {key: str(path) for key, path in metric_paths.items()},
                "sample_mapping_path": str(sample_mapping_path),
                "gene_annotation_path": str(gene_annotation_path),
                "analysis_gate_status": "pending_data_check",
            },
            matrix_orientation="gene_by_sample",
            log_transform=False,
        )
        build_manifest = {
            "schema_version": TCGA_EXPRESSION_BUILD_MANIFEST_SCHEMA_VERSION,
            "build_id": build_id,
            "created_at": _now(),
            "project_id": project_id,
            "status": "tcga_expression_matrix_built",
            "message": f"TCGA 表达矩阵已构建：{len(sample_names)} 个样本，{len(gene_order)} 个基因；等待数据检查与准备。",
            "b6_3_acquisition_record_path": str(raw_record_path),
            "download_receipt_path": str(metadata.get("download_receipt_path") or ""),
            "download_manifest_path": str(metadata.get("download_manifest_path") or ""),
            "source_files": [str(path) for path in source_files],
            "parsed_files": [str(sample.local_path) for sample in parsed_samples],
            "sample_count": len(sample_names),
            "gene_count": len(gene_order),
            "metric_matrix_paths": {key: str(path) for key, path in metric_paths.items()},
            "sample_metadata_path": str(sample_metadata_path),
            "sample_mapping_path": str(sample_mapping_path),
            "gene_annotation_path": str(gene_annotation_path),
            "prepare_manifest_path": str(prepare_manifest_path),
            "prepare_manifest": prepare_manifest,
            "warnings": warnings,
            "ready_for_recognition": "pending_data_check",
            "analysis_gate_status": "pending_data_check",
        }
        _write_json(build_manifest_path, build_manifest)
        acquisition = _register_expression_build(
            root=root,
            project_id=project_id,
            build_id=build_id,
            raw_record_path=raw_record_path,
            build_manifest_path=build_manifest_path,
            prepare_manifest_path=prepare_manifest_path,
            expression_matrix_path=expression_matrix_path,
            sample_metadata_path=sample_metadata_path,
            sample_mapping_path=sample_mapping_path,
            gene_annotation_path=gene_annotation_path,
            metric_paths=metric_paths,
            sample_count=len(sample_names),
            gene_count=len(gene_order),
            parsed_file_count=len(parsed_samples),
            warnings=warnings,
        )
        return TCGAExpressionBuildResult(
            success=True,
            status="tcga_expression_matrix_built",
            message=str(build_manifest["message"]),
            project_id=project_id,
            build_id=build_id,
            raw_acquisition_record_path=raw_record_path,
            build_manifest_path=build_manifest_path,
            prepare_manifest_path=prepare_manifest_path,
            expression_matrix_path=expression_matrix_path,
            sample_metadata_path=sample_metadata_path,
            sample_mapping_path=sample_mapping_path,
            gene_annotation_path=gene_annotation_path,
            metric_matrix_paths={key: str(path) for key, path in metric_paths.items()},
            source_file_count=len(source_files),
            parsed_file_count=len(parsed_samples),
            sample_count=len(sample_names),
            gene_count=len(gene_order),
            warnings=tuple(warnings),
            acquisition_summary=acquisition,
        )


@dataclass(frozen=True)
class _SampleMapping:
    file_id: str
    file_name: str
    local_path: Path
    sample_barcode: str
    case_id: str
    case_submitter_id: str
    sample_id: str
    sample_type: str


@dataclass(frozen=True)
class _ParsedSample:
    mapping: _SampleMapping
    rows: dict[str, dict[str, str]]
    gene_annotations: dict[str, dict[str, str]]

    @property
    def sample_barcode(self) -> str:
        return self.mapping.sample_barcode

    @property
    def local_path(self) -> Path:
        return self.mapping.local_path


def latest_tcga_raw_expression_record_path(project_root: str | Path, *, project_id: str | None = None) -> Path | None:
    root = Path(project_root).expanduser().resolve()
    selected_project = str(project_id or "").strip().upper()
    records_dir = root / "acquisition" / "records"
    if not records_dir.exists():
        return None
    candidates: list[Path] = []
    for path in records_dir.glob("*.json"):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if not isinstance(metadata, dict):
            continue
        record_project = str(metadata.get("project_id") or payload.get("source_label") or "").strip().upper()
        if selected_project and record_project and record_project != selected_project:
            continue
        if str(metadata.get("analysis_gate_status") or "") != "waiting_b6_4_expression_matrix_build":
            continue
        if str(metadata.get("source") or "") == "tcga_gdc" and _string_list(payload.get("source_files")):
            candidates.append(path)
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _file_records_for_raw_record(raw_record: dict[str, Any], metadata: dict[str, object]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    manifest_path = str(metadata.get("source_manifest_path") or "")
    if manifest_path:
        try:
            manifest = _read_json(Path(manifest_path))
            records.extend(record for record in manifest.get("file_records", []) or [] if isinstance(record, dict))
        except (OSError, json.JSONDecodeError):
            pass
    receipt_path = str(metadata.get("download_receipt_path") or "")
    if receipt_path:
        try:
            receipt = _read_json(Path(receipt_path))
            records.extend(record for record in receipt.get("file_records", []) or [] if isinstance(record, dict))
        except (OSError, json.JSONDecodeError):
            pass
    if records:
        return records
    return [
        {"local_path": path, "role": "tcga_gdc_gene_expression_quantification"}
        for path in _string_list(raw_record.get("source_files"))
    ]


def _is_expression_quantification_file(path: Path, record: dict[str, Any]) -> bool:
    role = str(record.get("role") or "").lower()
    text = " ".join(
        str(record.get(key) or "").lower()
        for key in ("file_name", "source_path", "data_type", "data_format", "workflow_type", "message")
    )
    name = path.name.lower()
    if "gene_expression_quantification" in role or "gene expression quantification" in text:
        return True
    if "star - counts" in text:
        return True
    if any(token in name for token in (".bam", ".cram", ".bai", ".crai")):
        return False
    return path.suffix.lower() in {".tsv", ".txt", ".gz"} and any(token in name for token in ("count", "quant", "rna", "expression", ".tsv"))


def _sample_mapping_for_file(path: Path, record: dict[str, Any], warnings: list[str]) -> _SampleMapping:
    submitters = _string_list(record.get("sample_submitter_ids"))
    sample_barcode = _first_valid_tcga_barcode(submitters)
    if not sample_barcode:
        sample_barcode = _first_valid_tcga_barcode([path.stem, str(record.get("file_name") or "")])
    if not sample_barcode:
        sample_barcode = str(record.get("file_id") or path.stem).strip()
        warnings.append(f"sample_barcode_missing_for_file:{path.name}")
    case_submitters = _string_list(record.get("case_submitter_ids"))
    case_ids = _string_list(record.get("case_ids"))
    sample_ids = _string_list(record.get("sample_ids"))
    sample_types = _string_list(record.get("sample_types"))
    return _SampleMapping(
        file_id=str(record.get("file_id") or ""),
        file_name=str(record.get("file_name") or path.name),
        local_path=path,
        sample_barcode=sample_barcode,
        case_id=case_ids[0] if case_ids else "",
        case_submitter_id=case_submitters[0] if case_submitters else "",
        sample_id=sample_ids[0] if sample_ids else "",
        sample_type=sample_types[0] if sample_types else "",
    )


def _parse_quantification_file(path: Path, mapping: _SampleMapping, warnings: list[str]) -> _ParsedSample:
    rows = _read_table(path)
    if not rows:
        raise ValueError(f"TCGA expression quantification file is empty: {path}")
    metric_columns = _resolve_metric_columns(rows[0].keys())
    if "raw_counts" not in metric_columns:
        raise ValueError(f"TCGA expression quantification file lacks raw count column: {path}")
    sample_rows: dict[str, dict[str, str]] = {}
    annotations: dict[str, dict[str, str]] = {}
    skipped_summary = 0
    duplicate_genes = 0
    for row in rows:
        gene_id = _clean_gene_id(_field(row, "gene_id"))
        if not gene_id:
            continue
        if gene_id.upper().startswith("N_"):
            skipped_summary += 1
            continue
        if gene_id in sample_rows:
            duplicate_genes += 1
            continue
        values = {metric: _field(row, column) for metric, column in metric_columns.items()}
        sample_rows[gene_id] = values
        annotations[gene_id] = {
            "gene_id": gene_id,
            "gene_name": _field(row, "gene_name"),
            "gene_type": _field(row, "gene_type"),
        }
    if skipped_summary:
        warnings.append(f"gdc_summary_rows_skipped:{path.name}:{skipped_summary}")
    if duplicate_genes:
        warnings.append(f"duplicate_gene_rows_skipped:{path.name}:{duplicate_genes}")
    if not sample_rows:
        raise ValueError(f"TCGA expression quantification file has no gene rows: {path}")
    return _ParsedSample(mapping=mapping, rows=sample_rows, gene_annotations=annotations)


def _read_table(path: Path) -> list[dict[str, str]]:
    opener = gzip.open if path.name.lower().endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as handle:  # type: ignore[arg-type]
        lines = [line for line in handle if line.strip() and not line.startswith("#")]
    if not lines:
        return []
    header_index = 0
    for index, line in enumerate(lines):
        if "gene_id" in line.lower():
            header_index = index
            break
    reader = csv.DictReader(lines[header_index:], delimiter="\t")
    return [{str(key or "").strip(): str(value or "").strip() for key, value in row.items()} for row in reader]


def _resolve_metric_columns(columns: Iterable[str]) -> dict[str, str]:
    normalized = {_normalize_header(column): column for column in columns}
    resolved: dict[str, str] = {}
    for metric, candidates in _METRIC_COLUMNS.items():
        for candidate in candidates:
            if _normalize_header(candidate) in normalized:
                resolved[metric] = normalized[_normalize_header(candidate)]
                break
    return resolved


def _build_matrices(
    parsed_samples: list[_ParsedSample],
    warnings: list[str],
) -> tuple[list[str], dict[str, dict[str, str]], dict[str, dict[str, dict[str, str]]]]:
    gene_order: list[str] = []
    annotations: dict[str, dict[str, str]] = {}
    matrices: dict[str, dict[str, dict[str, str]]] = {metric: {} for metric in _METRIC_COLUMNS}
    seen_genes: set[str] = set()
    for sample in parsed_samples:
        for gene_id, values in sample.rows.items():
            if gene_id not in seen_genes:
                seen_genes.add(gene_id)
                gene_order.append(gene_id)
            annotations.setdefault(gene_id, sample.gene_annotations.get(gene_id, {"gene_id": gene_id}))
            for metric in _METRIC_COLUMNS:
                matrices[metric].setdefault(gene_id, {})[sample.sample_barcode] = values.get(metric, "")
    for gene_id in gene_order:
        missing_samples = [
            sample.sample_barcode
            for sample in parsed_samples
            if gene_id not in sample.rows
        ]
        if missing_samples:
            warnings.append(f"gene_missing_in_samples:{gene_id}:{','.join(missing_samples)}")
    return gene_order, annotations, matrices


def _write_matrix(path: Path, sample_names: list[str], gene_order: list[str], values: dict[str, dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["gene_id", *sample_names])
        for gene_id in gene_order:
            row_values = values.get(gene_id, {})
            writer.writerow([gene_id, *[row_values.get(sample, "") for sample in sample_names]])


def _write_gene_annotation(path: Path, gene_order: list[str], annotations: dict[str, dict[str, str]]) -> None:
    _write_dict_rows(
        path,
        (annotations.get(gene_id, {"gene_id": gene_id}) for gene_id in gene_order),
        ["gene_id", "gene_name", "gene_type"],
    )


def _write_sample_mapping(path: Path, parsed_samples: list[_ParsedSample]) -> None:
    _write_dict_rows(
        path,
        (
            {
                "sample_barcode": sample.mapping.sample_barcode,
                "case_id": sample.mapping.case_id,
                "case_submitter_id": sample.mapping.case_submitter_id,
                "sample_id": sample.mapping.sample_id,
                "sample_type": sample.mapping.sample_type,
                "file_id": sample.mapping.file_id,
                "file_name": sample.mapping.file_name,
                "local_path": str(sample.mapping.local_path),
            }
            for sample in parsed_samples
        ),
        ["sample_barcode", "case_id", "case_submitter_id", "sample_id", "sample_type", "file_id", "file_name", "local_path"],
    )


def _write_sample_metadata(path: Path, parsed_samples: list[_ParsedSample], warnings: list[str]) -> None:
    valid_barcodes: list[str] = []
    invalid_barcodes: list[str] = []
    for sample in parsed_samples:
        try:
            parse_tcga_barcode(sample.sample_barcode)
        except ValueError:
            invalid_barcodes.append(sample.sample_barcode)
        else:
            valid_barcodes.append(sample.sample_barcode)
    rows = build_tcga_sample_metadata(valid_barcodes)
    by_barcode = {sample.mapping.sample_barcode: sample.mapping for sample in parsed_samples}
    for row in rows:
        mapping = by_barcode.get(str(row.get("sample_id") or ""))
        if mapping is not None:
            row["case_id"] = mapping.case_id
            row["case_submitter_id"] = mapping.case_submitter_id
            row["sample_type_gdc"] = mapping.sample_type
            row["file_id"] = mapping.file_id
            row["local_path"] = str(mapping.local_path)
    for barcode in invalid_barcodes:
        mapping = by_barcode.get(barcode)
        warnings.append(f"invalid_sample_barcode_in_matrix:{barcode}")
        rows.append(
            {
                "sample_id": barcode,
                "barcode": barcode,
                "tcga_barcode": barcode,
                "patient_barcode": "",
                "participant_barcode": "",
                "project_prefix": "",
                "sample_type_code": "",
                "sample_type_label": mapping.sample_type if mapping else "",
                "is_tumor": "",
                "is_normal": "",
                "case_id": mapping.case_id if mapping else "",
                "case_submitter_id": mapping.case_submitter_id if mapping else "",
                "sample_type_gdc": mapping.sample_type if mapping else "",
                "file_id": mapping.file_id if mapping else "",
                "local_path": str(mapping.local_path) if mapping else "",
            }
        )
    _write_dict_rows(
        path,
        rows,
        [
            "sample_id",
            "barcode",
            "tcga_barcode",
            "patient_barcode",
            "participant_barcode",
            "project_prefix",
            "sample_type_code",
            "sample_type_label",
            "is_tumor",
            "is_normal",
            "case_id",
            "case_submitter_id",
            "sample_type_gdc",
            "file_id",
            "local_path",
        ],
    )


def _register_expression_build(
    *,
    root: Path,
    project_id: str,
    build_id: str,
    raw_record_path: Path,
    build_manifest_path: Path,
    prepare_manifest_path: Path,
    expression_matrix_path: Path,
    sample_metadata_path: Path,
    sample_mapping_path: Path,
    gene_annotation_path: Path,
    metric_paths: dict[str, Path],
    sample_count: int,
    gene_count: int,
    parsed_file_count: int,
    warnings: list[str],
) -> AcquisitionSummary:
    selected_paths = [
        expression_matrix_path,
        sample_metadata_path,
        sample_mapping_path,
        gene_annotation_path,
        build_manifest_path,
        prepare_manifest_path,
        *[path for metric, path in metric_paths.items() if metric != "raw_counts"],
    ]
    file_records = [
        build_file_record(expression_matrix_path, source="tcga_gdc", role="tcga_expression_matrix", status="available", message="B6.4 primary raw counts expression matrix."),
        build_file_record(sample_metadata_path, source="tcga_gdc", role="tcga_sample_metadata", status="available", message="B6.4 TCGA sample metadata."),
        build_file_record(sample_mapping_path, source="tcga_gdc", role="tcga_sample_file_mapping", status="available", message="B6.4 sample barcode/case/file mapping."),
        build_file_record(gene_annotation_path, source="tcga_gdc", role="tcga_gene_annotation", status="available", message="B6.4 gene annotation parsed from GDC quantification files."),
        build_file_record(build_manifest_path, source="tcga_gdc", role="tcga_expression_build_manifest", status="available", message="B6.4 local expression build manifest."),
        build_file_record(prepare_manifest_path, source="tcga_gdc", role="tcga_prepare_manifest", status="available", message="TCGA standard prepare manifest."),
    ]
    for metric, path in metric_paths.items():
        if metric == "raw_counts":
            continue
        file_records.append(
            build_file_record(path, source="tcga_gdc", role=f"tcga_{metric}_matrix", status="available", message=f"B6.4 {metric} expression matrix.")
        )
    return register_acquisition(
        root,
        source_type="tcga_project",
        source_label=project_id,
        strategy="reference",
        selected_paths=selected_paths,
        metadata={
            "source": "tcga_gdc",
            "ui_source": "tcga_database_page",
            "registration_status": "registered_tcga_expression_matrix_waiting_data_check",
            "download_status": "tcga_expression_matrix_built",
            "ready_for_recognition": "pending_data_check",
            "recognition_scope": "tcga_expression_matrix_waiting_data_check",
            "analysis_gate_status": "pending_data_check",
            "analysis_gate_message": "TCGA 表达矩阵已构建，等待统一数据检查与准备。",
            "project_id": project_id,
            "build_id": build_id,
            "display_title_zh": f"TCGA {project_id}",
            "b6_3_acquisition_record_path": str(raw_record_path),
            "tcga_expression_build_manifest_path": str(build_manifest_path),
            "tcga_prepare_manifest_path": str(prepare_manifest_path),
            "tcga_expression_matrix_path": str(expression_matrix_path),
            "tcga_sample_metadata_path": str(sample_metadata_path),
            "tcga_sample_mapping_path": str(sample_mapping_path),
            "tcga_gene_annotation_path": str(gene_annotation_path),
            "tcga_metric_matrix_paths": {key: str(path) for key, path in metric_paths.items()},
            "tcga_expression_build_summary": {
                "sample_count": sample_count,
                "gene_count": gene_count,
                "parsed_file_count": parsed_file_count,
            },
            "expected_assets": ["rna_seq_expression", "sample_metadata", "case_sample_mapping"],
            "warnings": list(warnings),
        },
        file_records=file_records,
    )


def _write_dict_rows(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _field(row: dict[str, str], name: str) -> str:
    target = _normalize_header(name)
    for key, value in row.items():
        if _normalize_header(key) == target:
            return str(value or "").strip()
    return ""


def _normalize_header(value: str) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _clean_gene_id(value: str) -> str:
    stripped = str(value or "").strip()
    match = _ENSEMBL_VERSION_RE.match(stripped)
    return match.group(1).upper() if match else stripped


def _first_valid_tcga_barcode(values: Iterable[str]) -> str:
    for value in values:
        try:
            return str(parse_tcga_barcode(str(value))["barcode"])
        except ValueError:
            continue
    return ""


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


__all__ = [
    "TCGA_EXPRESSION_BUILD_MANIFEST_SCHEMA_VERSION",
    "TCGAExpressionBuildResult",
    "TCGAExpressionQuantificationBuilder",
    "latest_tcga_raw_expression_record_path",
]
