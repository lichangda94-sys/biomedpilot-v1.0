"""Minimal local bundle builder for TCGA/GTEx runtime pre-integration work."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any

from tcga_gtex.models import AnalysisBundle


BUNDLE_FILE_NAME = "analysis_bundle.json"
MANIFEST_FILE_NAME = "bundle_manifest.json"
SUMMARY_FILE_NAME = "bundle_summary.json"
_GENERATED_FILES = {BUNDLE_FILE_NAME, MANIFEST_FILE_NAME, SUMMARY_FILE_NAME}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _guess_source(relative_path: str) -> str:
    value = relative_path.lower()
    if "tcga" in value:
        return "tcga_gdc"
    if "gtex" in value:
        return "gtex"
    return "unknown"


def _guess_study_id(relative_path: str) -> str:
    value = relative_path.upper().replace("_", "-")
    tcga_matches = re.findall(r"(TCGA-[A-Z0-9]+)", value)
    tcga_matches = [match for match in tcga_matches if match != "TCGA-GDC"]
    if tcga_matches:
        return tcga_matches[-1]
    gtex_matches = re.findall(r"(GTEX-[A-Z0-9-]+)", value)
    if gtex_matches:
        return gtex_matches[-1]
    return "unknown"


def _guess_role(file_name: str) -> str:
    value = file_name.lower()
    if "clinical" in value:
        return "clinical"
    if "biospecimen" in value:
        return "biospecimen"
    if "mutation" in value or value.endswith(".maf.gz"):
        return "mutation"
    if "sample_attributes" in value:
        return "sample_metadata"
    if "subject_phenotypes" in value:
        return "subject_metadata"
    if "eqtl" in value:
        return "eqtl"
    if "sqtl" in value:
        return "sqtl"
    if "read_count" in value:
        return "expression_counts"
    if "tpm" in value:
        return "expression_tpm"
    if "expression" in value or "counts" in value:
        return "expression"
    return "data"


def _collect_input_files(local_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(candidate for candidate in local_dir.rglob("*") if candidate.is_file()):
        if path.name in _GENERATED_FILES:
            continue
        relative_path = path.relative_to(local_dir).as_posix()
        records.append(
            {
                "relative_path": relative_path,
                "file_name": path.name,
                "size_bytes": path.stat().st_size,
                "source_guess": _guess_source(relative_path),
                "study_id_guess": _guess_study_id(relative_path),
                "guessed_role": _guess_role(path.name),
            }
        )
    return records


def _analysis_compatible(roles: list[str]) -> list[str]:
    compatible: list[str] = []
    if any(role.startswith("expression") or role == "expression" for role in roles):
        compatible.append("expression_matrix_ready")
    if "clinical" in roles or "sample_metadata" in roles or "subject_metadata" in roles:
        compatible.append("metadata_ready")
    if "mutation" in roles:
        compatible.append("mutation_ready")
    return compatible


def build_local_analysis_bundle(local_dir: str) -> dict[str, Any]:
    bundle_dir = Path(local_dir).expanduser().resolve()
    bundle_path = bundle_dir / BUNDLE_FILE_NAME
    manifest_path = bundle_dir / MANIFEST_FILE_NAME
    summary_path = bundle_dir / SUMMARY_FILE_NAME

    if not bundle_dir.exists():
        return {
            "status": "failed",
            "message": "Local bundle directory does not exist.",
            "output_dir": str(bundle_dir),
            "bundle_path": str(bundle_path),
            "warnings": [],
            "data": {"local_dir": str(bundle_dir)},
        }
    if not bundle_dir.is_dir():
        return {
            "status": "failed",
            "message": "Local bundle path must be a directory.",
            "output_dir": str(bundle_dir),
            "bundle_path": str(bundle_path),
            "warnings": [],
            "data": {"local_dir": str(bundle_dir)},
        }

    input_files = _collect_input_files(bundle_dir)
    if not input_files:
        return {
            "status": "failed",
            "message": "No local TCGA/GTEx input files were found to build a bundle.",
            "output_dir": str(bundle_dir),
            "bundle_path": str(bundle_path),
            "warnings": [],
            "data": {"local_dir": str(bundle_dir)},
        }

    sources = sorted({record["source_guess"] for record in input_files if record["source_guess"] != "unknown"})
    study_ids = sorted({record["study_id_guess"] for record in input_files if record["study_id_guess"] != "unknown"})
    roles = sorted({record["guessed_role"] for record in input_files})

    manifest_payload = {
        "bundle_kind": "tcga_gtex_local_bundle",
        "generated_at": _now_iso(),
        "bundle_dir": str(bundle_dir),
        "input_file_count": len(input_files),
        "sources": sources,
        "study_ids": study_ids,
        "input_files": input_files,
    }

    bundle = AnalysisBundle(
        source=sources[0] if len(sources) == 1 else ("mixed" if sources else "unknown"),
        study_id=study_ids[0] if len(study_ids) == 1 else ("multiple" if study_ids else "unknown"),
        bundle_dir=str(bundle_dir),
        matrix_kind="expression" if "expression" in roles or "expression_counts" in roles or "expression_tpm" in roles else "unknown",
        source_mode="local_fixture",
        analysis_compatible=_analysis_compatible(roles),
        cross_source_safe=len(sources) <= 1,
        warning_messages=[] if sources else ["Source could not be inferred from local file names."],
        metadata={
            "manifest_path": MANIFEST_FILE_NAME,
            "summary_path": SUMMARY_FILE_NAME,
            "input_file_count": len(input_files),
            "sources": sources,
            "study_ids": study_ids,
            "guessed_roles": roles,
        },
    )
    bundle_payload = bundle.to_dict()

    summary_payload = {
        "bundle_dir": str(bundle_dir),
        "bundle_path": str(bundle_path),
        "manifest_path": str(manifest_path),
        "summary_path": str(summary_path),
        "source": bundle.source,
        "study_id": bundle.study_id,
        "sources": sources,
        "study_ids": study_ids,
        "input_file_count": len(input_files),
        "guessed_roles": roles,
        "analysis_compatible": bundle.analysis_compatible,
        "cross_source_safe": bundle.cross_source_safe,
        "status": "success",
        "generated_at": manifest_payload["generated_at"],
    }

    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    bundle_path.write_text(json.dumps(bundle_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "status": "success",
        "message": f"Built TCGA/GTEx analysis bundle from {len(input_files)} local input files.",
        "output_dir": str(bundle_dir),
        "bundle_path": str(bundle_path),
        "warnings": bundle.warning_messages,
        "data": {
            "bundle": bundle_payload,
            "manifest": manifest_payload,
            "summary": summary_payload,
        },
    }


def read_local_bundle_summary(bundle_dir: str) -> dict[str, Any]:
    resolved_dir = Path(bundle_dir).expanduser().resolve()
    bundle_path = resolved_dir / BUNDLE_FILE_NAME
    manifest_path = resolved_dir / MANIFEST_FILE_NAME
    summary_path = resolved_dir / SUMMARY_FILE_NAME

    if not bundle_path.exists():
        return {
            "status": "failed",
            "message": "TCGA/GTEx analysis bundle file does not exist.",
            "output_dir": str(resolved_dir),
            "bundle_path": str(bundle_path),
            "warnings": [],
            "data": {"bundle_dir": str(resolved_dir)},
        }
    if not summary_path.exists():
        return {
            "status": "failed",
            "message": "TCGA/GTEx bundle summary file does not exist.",
            "output_dir": str(resolved_dir),
            "bundle_path": str(bundle_path),
            "warnings": [],
            "data": {"bundle_dir": str(resolved_dir)},
        }
    if not manifest_path.exists():
        return {
            "status": "failed",
            "message": "TCGA/GTEx bundle manifest file does not exist.",
            "output_dir": str(resolved_dir),
            "bundle_path": str(bundle_path),
            "warnings": [],
            "data": {"bundle_dir": str(resolved_dir)},
        }

    bundle_payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    if summary_payload.get("status") != "success":
        return {
            "status": "failed",
            "message": "TCGA/GTEx bundle summary is not marked as success.",
            "output_dir": str(resolved_dir),
            "bundle_path": str(bundle_path),
            "warnings": [],
            "data": {
                "bundle_dir": str(resolved_dir),
                "bundle": bundle_payload,
                "summary": summary_payload,
                "manifest": manifest_payload,
            },
        }

    return {
        "status": "success",
        "message": "Loaded TCGA/GTEx analysis bundle summary.",
        "output_dir": str(resolved_dir),
        "bundle_path": str(bundle_path),
        "warnings": bundle_payload.get("warning_messages", []),
        "data": {
            "bundle": bundle_payload,
            "summary": summary_payload,
            "manifest": manifest_payload,
        },
    }


__all__ = [
    "BUNDLE_FILE_NAME",
    "MANIFEST_FILE_NAME",
    "SUMMARY_FILE_NAME",
    "build_local_analysis_bundle",
    "read_local_bundle_summary",
]
