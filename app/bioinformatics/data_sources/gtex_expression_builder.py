from __future__ import annotations

import csv
import gzip
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from app.bioinformatics.acquisition_file_records import build_file_record
from app.bioinformatics.data_sources.gtex_download_executor import latest_gtex_raw_expression_record_path
from app.bioinformatics.project_workspace_binding import AcquisitionSummary, LATEST_RECORD, register_acquisition


GTEX_EXPRESSION_BUILD_MANIFEST_SCHEMA_VERSION = "biomedpilot.gtex_expression_build_manifest.v1"


@dataclass(frozen=True)
class GTExExpressionBuildResult:
    success: bool
    status: str
    message: str
    tissue_id: str
    tissue_site_detail: str
    build_id: str
    raw_acquisition_record_path: Path
    build_manifest_path: Path
    expression_matrix_path: Path
    sample_metadata_path: Path
    donor_metadata_path: Path
    tissue_metadata_path: Path
    gene_annotation_path: Path
    source_file_count: int
    parsed_file_count: int
    sample_count: int
    donor_count: int
    gene_count: int
    warnings: tuple[str, ...]
    acquisition_summary: AcquisitionSummary | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        for key in (
            "raw_acquisition_record_path",
            "build_manifest_path",
            "expression_matrix_path",
            "sample_metadata_path",
            "donor_metadata_path",
            "tissue_metadata_path",
            "gene_annotation_path",
        ):
            payload[key] = str(payload[key])
        return payload


class GTExExpressionMatrixBuilder:
    def build_latest(self, project_root: str | Path) -> GTExExpressionBuildResult:
        record_path = latest_gtex_raw_expression_record_path(project_root)
        if record_path is None:
            raise FileNotFoundError("未找到等待 G6.3 构建表达矩阵的 GTEx 原始文件记录。")
        return self.build_from_record(project_root, record_path=record_path)

    def build_from_record(self, project_root: str | Path, *, record_path: str | Path) -> GTExExpressionBuildResult:
        root = Path(project_root).expanduser().resolve()
        raw_record_path = Path(record_path).expanduser().resolve()
        raw_record = _read_json(raw_record_path)
        metadata = raw_record.get("metadata") if isinstance(raw_record.get("metadata"), dict) else {}
        if not isinstance(metadata, dict):
            metadata = {}
        if str(metadata.get("analysis_gate_status") or "") != "waiting_gtex_expression_matrix_build":
            raise ValueError("该 GTEx 记录不是等待 G6.3 表达矩阵构建的原始文件记录。")
        tissue_id = str(metadata.get("tissue_id") or raw_record.get("source_label") or "gtex_tissue").strip()
        tissue_detail = str(metadata.get("tissue_site_detail") or tissue_id).strip()
        source_files = [Path(path).expanduser().resolve() for path in _string_list(raw_record.get("source_files"))]
        if not source_files:
            raise ValueError("GTEx 记录缺少 source_files。")
        warnings: list[str] = []
        expression_source = _first_expression_file(source_files)
        rows, sample_ids = _read_expression_matrix(expression_source)
        if not rows or not sample_ids:
            raise ValueError(f"GTEx expression matrix is empty or lacks samples: {expression_source}")

        build_id = f"gtex-g63-{uuid4().hex[:10]}"
        base_dir = root / "standardized_data" / "gtex" / _slug(tissue_id) / build_id / "data_prepared" / "gtex"
        expression_matrix_path = base_dir / "expression" / "gtex_expression_matrix.csv"
        sample_metadata_path = base_dir / "sample_metadata" / "gtex_sample_metadata.csv"
        donor_metadata_path = base_dir / "sample_metadata" / "gtex_donor_metadata.csv"
        tissue_metadata_path = base_dir / "sample_metadata" / "gtex_tissue_metadata.csv"
        gene_annotation_path = base_dir / "expression" / "gtex_gene_annotation.csv"
        build_manifest_path = base_dir / "gtex_expression_build_manifest.json"

        _write_expression_matrix(expression_matrix_path, rows, sample_ids)
        _write_gene_annotation(gene_annotation_path, rows)
        sample_rows = _sample_metadata_rows(sample_ids, tissue_id, tissue_detail)
        donor_rows = _donor_metadata_rows(sample_rows)
        _write_dict_rows(sample_metadata_path, sample_rows, ["sample_id", "donor_id", "tissue_id", "tissue_site_detail", "value_type", "tcga_default_control_status"])
        _write_dict_rows(donor_metadata_path, donor_rows, ["donor_id", "sample_count", "tissue_id", "tissue_site_detail"])
        _write_dict_rows(tissue_metadata_path, [{"tissue_id": tissue_id, "tissue_site_detail": tissue_detail, "sample_count": len(sample_ids), "donor_count": len(donor_rows), "tcga_default_control_status": "disabled"}], ["tissue_id", "tissue_site_detail", "sample_count", "donor_count", "tcga_default_control_status"])
        build_manifest = {
            "schema_version": GTEX_EXPRESSION_BUILD_MANIFEST_SCHEMA_VERSION,
            "build_id": build_id,
            "created_at": _now(),
            "tissue_id": tissue_id,
            "tissue_site_detail": tissue_detail,
            "status": "gtex_expression_matrix_built",
            "message": f"GTEx 表达矩阵已构建：{len(sample_ids)} 个样本，{len(rows)} 个基因；等待数据检查与准备。",
            "source_files": [str(path) for path in source_files],
            "parsed_files": [str(expression_source)],
            "sample_count": len(sample_ids),
            "donor_count": len(donor_rows),
            "gene_count": len(rows),
            "expression_matrix_path": str(expression_matrix_path),
            "sample_metadata_path": str(sample_metadata_path),
            "donor_metadata_path": str(donor_metadata_path),
            "tissue_metadata_path": str(tissue_metadata_path),
            "gene_annotation_path": str(gene_annotation_path),
            "value_type_policy": _value_type_policy(),
            "warnings": warnings,
            "ready_for_recognition": "pending_data_check",
            "analysis_gate_status": "pending_data_check",
            "tcga_merge_status": "not_merged",
            "tcga_default_control_status": "disabled",
            "requires_explicit_joint_config": True,
        }
        _write_json(build_manifest_path, build_manifest)
        acquisition = _register_build(
            root=root,
            tissue_id=tissue_id,
            tissue_detail=tissue_detail,
            build_id=build_id,
            build_manifest_path=build_manifest_path,
            expression_matrix_path=expression_matrix_path,
            sample_metadata_path=sample_metadata_path,
            donor_metadata_path=donor_metadata_path,
            tissue_metadata_path=tissue_metadata_path,
            gene_annotation_path=gene_annotation_path,
            sample_count=len(sample_ids),
            donor_count=len(donor_rows),
            gene_count=len(rows),
            warnings=warnings,
        )
        return GTExExpressionBuildResult(
            success=True,
            status="gtex_expression_matrix_built",
            message=str(build_manifest["message"]),
            tissue_id=tissue_id,
            tissue_site_detail=tissue_detail,
            build_id=build_id,
            raw_acquisition_record_path=raw_record_path,
            build_manifest_path=build_manifest_path,
            expression_matrix_path=expression_matrix_path,
            sample_metadata_path=sample_metadata_path,
            donor_metadata_path=donor_metadata_path,
            tissue_metadata_path=tissue_metadata_path,
            gene_annotation_path=gene_annotation_path,
            source_file_count=len(source_files),
            parsed_file_count=1,
            sample_count=len(sample_ids),
            donor_count=len(donor_rows),
            gene_count=len(rows),
            warnings=tuple(warnings),
            acquisition_summary=acquisition,
        )


def latest_gtex_expression_build_manifest_path(project_root: str | Path) -> Path | None:
    root = Path(project_root).expanduser().resolve()
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
        if str(metadata.get("download_status") or "") != "gtex_expression_matrix_built":
            continue
        manifest_path = Path(str(metadata.get("gtex_expression_build_manifest_path") or ""))
        if manifest_path.is_file():
            candidates.append(manifest_path)
    return max(candidates, key=lambda item: item.stat().st_mtime) if candidates else None


def _first_expression_file(paths: list[Path]) -> Path:
    for path in paths:
        lowered = path.name.lower()
        if lowered.endswith((".tsv", ".tsv.gz", ".csv", ".txt", ".txt.gz")) and any(token in lowered for token in ("gtex", "expression", "tpm", "matrix")):
            return path
    return paths[0]


def _read_expression_matrix(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    opener = gzip.open if path.name.lower().endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as handle:  # type: ignore[arg-type]
        sample = handle.readline()
        delimiter = "," if sample.count(",") > sample.count("\t") else "\t"
        handle.seek(0)
        reader = csv.DictReader(handle, delimiter=delimiter)
        fieldnames = [str(item or "").strip() for item in reader.fieldnames or []]
        gene_col = fieldnames[0] if fieldnames else "gene_id"
        samples = [field for field in fieldnames[1:] if field]
        rows = []
        for row in reader:
            gene_id = str(row.get(gene_col) or "").strip()
            if not gene_id:
                continue
            rows.append({"gene_id": gene_id, **{sample_id: str(row.get(sample_id) or "").strip() for sample_id in samples}})
    return rows, samples


def _write_expression_matrix(path: Path, rows: list[dict[str, str]], sample_ids: list[str]) -> None:
    _write_dict_rows(path, rows, ["gene_id", *sample_ids])


def _write_gene_annotation(path: Path, rows: list[dict[str, str]]) -> None:
    _write_dict_rows(path, ({"gene_id": row.get("gene_id", ""), "gene_name": row.get("gene_id", ""), "gene_id_type": "gene_symbol_or_ensembl"} for row in rows), ["gene_id", "gene_name", "gene_id_type"])


def _sample_metadata_rows(sample_ids: list[str], tissue_id: str, tissue_detail: str) -> list[dict[str, str]]:
    return [
        {
            "sample_id": sample_id,
            "donor_id": _donor_id(sample_id),
            "tissue_id": tissue_id,
            "tissue_site_detail": tissue_detail,
            "value_type": "TPM",
            "tcga_default_control_status": "disabled",
        }
        for sample_id in sample_ids
    ]


def _donor_metadata_rows(sample_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    counts: dict[str, int] = {}
    tissue_by_donor: dict[str, tuple[str, str]] = {}
    for row in sample_rows:
        donor = str(row.get("donor_id") or "")
        counts[donor] = counts.get(donor, 0) + 1
        tissue_by_donor[donor] = (str(row.get("tissue_id") or ""), str(row.get("tissue_site_detail") or ""))
    return [{"donor_id": donor, "sample_count": str(count), "tissue_id": tissue_by_donor[donor][0], "tissue_site_detail": tissue_by_donor[donor][1]} for donor, count in sorted(counts.items())]


def _donor_id(sample_id: str) -> str:
    parts = str(sample_id or "").split("-")
    return "-".join(parts[:2]) if len(parts) >= 2 and parts[0].upper() == "GTEX" else str(sample_id or "")


def _register_build(
    *,
    root: Path,
    tissue_id: str,
    tissue_detail: str,
    build_id: str,
    build_manifest_path: Path,
    expression_matrix_path: Path,
    sample_metadata_path: Path,
    donor_metadata_path: Path,
    tissue_metadata_path: Path,
    gene_annotation_path: Path,
    sample_count: int,
    donor_count: int,
    gene_count: int,
    warnings: list[str],
) -> AcquisitionSummary:
    selected_paths = [expression_matrix_path, sample_metadata_path, donor_metadata_path, tissue_metadata_path, gene_annotation_path, build_manifest_path]
    file_records = [
        build_file_record(expression_matrix_path, source="gtex", role="gtex_expression_matrix", status="available", message="G6.3 GTEx expression matrix."),
        build_file_record(sample_metadata_path, source="gtex", role="gtex_sample_metadata", status="available", message="G6.3 GTEx sample metadata."),
        build_file_record(donor_metadata_path, source="gtex", role="gtex_donor_metadata", status="available", message="G6.3 GTEx donor metadata."),
        build_file_record(tissue_metadata_path, source="gtex", role="gtex_tissue_metadata", status="available", message="G6.3 GTEx tissue metadata."),
        build_file_record(gene_annotation_path, source="gtex", role="gtex_gene_annotation", status="available", message="G6.3 GTEx gene annotation."),
        build_file_record(build_manifest_path, source="gtex", role="gtex_expression_build_manifest", status="available", message="G6.3 GTEx build manifest."),
    ]
    return register_acquisition(
        root,
        source_type="gtex_tissue",
        source_label=tissue_id,
        strategy="reference",
        selected_paths=selected_paths,
        metadata={
            "source": "gtex",
            "ui_source": "gtex_database_page",
            "registration_status": "registered_gtex_expression_matrix_waiting_data_check",
            "download_status": "gtex_expression_matrix_built",
            "ready_for_recognition": "pending_data_check",
            "analysis_gate_status": "pending_data_check",
            "tissue_id": tissue_id,
            "tissue_site_detail": tissue_detail,
            "build_id": build_id,
            "display_title_zh": f"GTEx {tissue_detail}",
            "gtex_expression_build_manifest_path": str(build_manifest_path),
            "gtex_expression_matrix_path": str(expression_matrix_path),
            "gtex_sample_metadata_path": str(sample_metadata_path),
            "gtex_donor_metadata_path": str(donor_metadata_path),
            "gtex_tissue_metadata_path": str(tissue_metadata_path),
            "gtex_gene_annotation_path": str(gene_annotation_path),
            "gtex_expression_build_summary": {"sample_count": sample_count, "donor_count": donor_count, "gene_count": gene_count},
            "tcga_merge_status": "not_merged",
            "tcga_default_control_status": "disabled",
            "requires_explicit_joint_config": True,
            "warnings": [*warnings, "GTEx 不自动作为 TCGA normal control；TCGA+GTEx 需要显式联合配置和批次校正。"],
        },
        file_records=file_records,
    )


def _value_type_policy() -> dict[str, object]:
    return {"TPM": {"value_type": "TPM", "default_for_deg": False, "default_for_display": True, "tcga_default_control": False}}


def _write_dict_rows(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _string_list(value: object) -> list[str]:
    return [str(item).strip() for item in value if str(item).strip()] if isinstance(value, list) else ([str(value).strip()] if str(value or "").strip() else [])


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in str(value or "")).strip("_") or "gtex"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


__all__ = [
    "GTEX_EXPRESSION_BUILD_MANIFEST_SCHEMA_VERSION",
    "GTExExpressionBuildResult",
    "GTExExpressionMatrixBuilder",
    "latest_gtex_expression_build_manifest_path",
]
