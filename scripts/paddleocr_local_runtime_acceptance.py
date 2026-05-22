from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.fulltext_management_service import FullTextManagementService
from app.meta_analysis.services.fulltext_parsing_service import FullTextParsingService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService
from app.meta_analysis.fulltext.ocr_runtime_service import MetaOcrRuntimeService
from app.shared.local_engines.paddleocr_runtime import (
    default_paddleocr_runtime_root,
    load_paddleocr_runtime_manifest,
)


ACCEPTANCE_SCHEMA_VERSION = "biomedpilot_paddleocr_acceptance.v1"


@dataclass(frozen=True)
class WorkerSmokeResult:
    mode: str
    module_root: str
    input_path: str
    stdout_path: str
    stderr_path: str
    status: str
    page_count: int
    text_chars: int
    safety_note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "module_root": self.module_root,
            "input_path": self.input_path,
            "stdout_path": self.stdout_path,
            "stderr_path": self.stderr_path,
            "status": self.status,
            "page_count": self.page_count,
            "text_chars": self.text_chars,
            "safety_note": self.safety_note,
        }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    runtime_root = Path(args.runtime_root).expanduser().resolve()
    runtime_service = MetaOcrRuntimeService(runtime_root=runtime_root)
    runtime_status = runtime_service.status()
    if not runtime_status.available:
        raise SystemExit(f"PaddleOCR runtime is not available: {runtime_status.status} {runtime_status.message}")

    manifest = load_paddleocr_runtime_manifest(runtime_root)
    # Keep the venv interpreter path from the manifest. Resolving it can follow
    # macOS framework symlinks and lose the virtualenv site-packages.
    runtime_python = Path(manifest.python_executable).expanduser()
    if not runtime_python.exists():
        raise SystemExit(f"PaddleOCR runtime Python does not exist: {runtime_python}")

    workdir = Path(args.workdir).expanduser().resolve() if args.workdir else runtime_root / "smoke" / _stamp()
    workdir.mkdir(parents=True, exist_ok=True)
    image_path, pdf_path = _prepare_smoke_inputs(runtime_root, workdir, runtime_python)
    paddleocr_source_root = Path(args.paddleocr_source_root).expanduser().resolve() if args.paddleocr_source_root else None
    if paddleocr_source_root is not None and not (paddleocr_source_root / "paddleocr" / "__init__.py").exists():
        raise SystemExit(f"PaddleOCR source root is invalid: {paddleocr_source_root}")

    source_worker_results = [
        _run_worker_smoke(
            runtime_python,
            REPO_ROOT,
            image_path,
            mode="image",
            record_id="acceptance-source-image",
            workdir=workdir,
            paddleocr_source_root=paddleocr_source_root,
        ),
        _run_worker_smoke(
            runtime_python,
            REPO_ROOT,
            pdf_path,
            mode="pdf",
            record_id="acceptance-source-pdf",
            workdir=workdir,
            paddleocr_source_root=paddleocr_source_root,
        ),
    ]

    packaged_worker_results: list[WorkerSmokeResult] = []
    packaged_resource_root = Path(args.packaged_resource_root).expanduser().resolve() if args.packaged_resource_root else None
    package_boundary: dict[str, Any] = {"checked": False}
    if packaged_resource_root is not None:
        package_boundary = _check_packaged_worker_boundary(packaged_resource_root)
        packaged_worker_results = [
            _run_worker_smoke(
                runtime_python,
                packaged_resource_root,
                image_path,
                mode="image",
                record_id="acceptance-packaged-image",
                workdir=workdir,
                paddleocr_source_root=paddleocr_source_root,
            ),
            _run_worker_smoke(
                runtime_python,
                packaged_resource_root,
                pdf_path,
                mode="pdf",
                record_id="acceptance-packaged-pdf",
                workdir=workdir,
                paddleocr_source_root=paddleocr_source_root,
            ),
        ]

    meta_result = _run_meta_fulltext_ocr_smoke(pdf_path, runtime_root, workdir, paddleocr_source_root=paddleocr_source_root)
    payload = {
        "schema_version": ACCEPTANCE_SCHEMA_VERSION,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "runtime": {
            "root": str(runtime_root),
            "manifest_path": str(runtime_service.manifest_path()),
            "runtime_id": manifest.runtime_id,
            "python_executable": str(runtime_python),
            "python_version": manifest.python_version,
            "packages": dict(manifest.packages),
            "status": runtime_status.status,
            "available": runtime_status.available,
        },
        "paddleocr_source_root": str(paddleocr_source_root) if paddleocr_source_root is not None else "",
        "source_worker_smoke": [item.to_dict() for item in source_worker_results],
        "packaged_worker_smoke": [item.to_dict() for item in packaged_worker_results],
        "packaged_worker_boundary": package_boundary,
        "meta_fulltext_ocr_smoke": meta_result,
        "boundaries": {
            "automatic_pdf_download": False,
            "paywall_or_institutional_access": False,
            "writes_final_extraction": False,
            "writes_screening_decision": False,
            "writes_quality_assessment": False,
            "writes_prisma_counts": False,
        },
    }
    result_path = workdir / "paddleocr_local_runtime_acceptance.json"
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "result_path": str(result_path)}, ensure_ascii=False, indent=2))
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run BioMedPilot PaddleOCR local runtime acceptance checks.")
    parser.add_argument("--runtime-root", default=str(default_paddleocr_runtime_root()), help="Configured PaddleOCR runtime root.")
    parser.add_argument("--packaged-resource-root", help="Optional .app Contents/Resources/app root to validate packaged worker calls.")
    parser.add_argument("--paddleocr-source-root", help="Optional local PaddleOCR source checkout used by worker subprocesses.")
    parser.add_argument("--workdir", help="Optional output directory for smoke artifacts.")
    return parser.parse_args(argv)


def _prepare_smoke_inputs(runtime_root: Path, workdir: Path, runtime_python: Path) -> tuple[Path, Path]:
    smoke_root = runtime_root / "smoke"
    existing_image = smoke_root / "ocr_smoke_multilingual.png"
    existing_pdf = smoke_root / "ocr_smoke_multilingual.pdf"
    image_path = workdir / "acceptance_input.png"
    pdf_path = workdir / "acceptance_input.pdf"
    if existing_image.exists() and existing_pdf.exists():
        shutil.copy2(existing_image, image_path)
        shutil.copy2(existing_pdf, pdf_path)
        return image_path, pdf_path

    generator = workdir / "generate_inputs.py"
    generator.write_text(
        """
from pathlib import Path
import fitz
from PIL import Image, ImageDraw
root = Path(__file__).resolve().parent
text = ["BioMedPilot OCR smoke test", "English OCR 95% CI", "local auxiliary fulltext"]
image = Image.new("RGB", (1000, 360), "white")
draw = ImageDraw.Draw(image)
y = 48
for line in text:
    draw.text((48, y), line, fill="black")
    y += 72
image.save(root / "acceptance_input.png")
doc = fitz.open()
page = doc.new_page(width=1000, height=360)
y = 60
for line in text:
    page.insert_text((48, y), line, fontsize=28)
    y += 72
doc.save(root / "acceptance_input.pdf")
""",
        encoding="utf-8",
    )
    subprocess.run([str(runtime_python), str(generator)], check=True, text=True, capture_output=True)
    return image_path, pdf_path


def _run_worker_smoke(
    runtime_python: Path,
    module_root: Path,
    input_path: Path,
    *,
    mode: str,
    record_id: str,
    workdir: Path,
    paddleocr_source_root: Path | None = None,
) -> WorkerSmokeResult:
    stdout_path = workdir / f"{record_id}.stdout.json"
    stderr_path = workdir / f"{record_id}.stderr.log"
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{module_root}{os.pathsep}{env['PYTHONPATH']}" if env.get("PYTHONPATH") else str(module_root)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if paddleocr_source_root is not None:
        env["BIOMEDPILOT_PADDLEOCR_SOURCE_ROOT"] = str(paddleocr_source_root)
    completed = subprocess.run(
        [
            str(runtime_python),
            "-m",
            "biomedpilot_ocr_worker",
            "--mode",
            mode,
            "--input",
            str(input_path),
            "--record-id",
            record_id,
        ],
        text=True,
        capture_output=True,
        env=env,
        cwd=str(module_root),
    )
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise SystemExit(f"{record_id} failed with exit code {completed.returncode}; see {stderr_path}")
    payload = json.loads(completed.stdout)
    text = "\n".join(str(page.get("text") or "") for page in payload.get("pages", []))
    safety_note = str(payload.get("safety_note") or "")
    if payload.get("status") != "completed" or not text.strip():
        raise SystemExit(f"{record_id} did not produce completed non-empty OCR output")
    if "does not create final Meta extraction" not in safety_note:
        raise SystemExit(f"{record_id} missing OCR safety note")
    return WorkerSmokeResult(
        mode=mode,
        module_root=str(module_root),
        input_path=str(input_path),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        status=str(payload.get("status") or ""),
        page_count=len(payload.get("pages", [])),
        text_chars=len(text.strip()),
        safety_note=safety_note,
    )


def _run_meta_fulltext_ocr_smoke(pdf_path: Path, runtime_root: Path, workdir: Path, *, paddleocr_source_root: Path | None = None) -> dict[str, Any]:
    previous_source_root = os.environ.get("BIOMEDPILOT_PADDLEOCR_SOURCE_ROOT")
    if paddleocr_source_root is not None:
        os.environ["BIOMEDPILOT_PADDLEOCR_SOURCE_ROOT"] = str(paddleocr_source_root)
    project_dir = workdir / "meta_project"
    try:
        management = FullTextManagementService()
        management.attach_pdf(
            project_dir,
            record_id="paddleocr-acceptance",
            source_file_path=str(pdf_path),
            actor="acceptance",
            notes="Local PaddleOCR acceptance smoke; user-provided local file only.",
        )
        service = FullTextParsingService(
            fulltext_management=management,
            ocr_runtime_service=MetaOcrRuntimeService(runtime_root=runtime_root),
        )
        result = service.parse_record(project_dir, record_id="paddleocr-acceptance", use_ocr=True)
    finally:
        if previous_source_root is None:
            os.environ.pop("BIOMEDPILOT_PADDLEOCR_SOURCE_ROOT", None)
        else:
            os.environ["BIOMEDPILOT_PADDLEOCR_SOURCE_ROOT"] = previous_source_root
    output_payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    extracted_text = Path(result.extracted_text_path).read_text(encoding="utf-8") if Path(result.extracted_text_path).exists() else ""
    audit = MetaAuditLogService().list_events(project_dir)
    governance = MetaResearchGovernanceService().list_events(project_dir)
    prisma = PRISMAService().collect_prisma_numbers(project_dir)
    final_extraction_exists = (project_dir / "extraction" / "extraction_records.json").exists()
    quality_exists = (project_dir / "quality" / "quality_assessments.json").exists()
    screening_exists = (project_dir / "screening").exists() or (project_dir / "screening_decisions.json").exists()
    if not result.success:
        raise SystemExit(f"Meta fulltext OCR smoke failed: {result.diagnostics}")
    if output_payload.get("parser_level") != "ocr_testing":
        raise SystemExit("Meta fulltext OCR parser_level must remain ocr_testing")
    if final_extraction_exists or quality_exists or screening_exists:
        raise SystemExit("Meta fulltext OCR wrote final downstream artifacts")
    if prisma.studies_included or prisma.full_text_reports_excluded:
        raise SystemExit("Meta fulltext OCR changed PRISMA counts")
    return {
        "project_dir": str(project_dir),
        "parse_status": result.parse_status,
        "parser_level": output_payload.get("parser_level"),
        "output_path": result.output_path,
        "extracted_text_path": result.extracted_text_path,
        "extracted_text_chars": len(extracted_text.strip()),
        "diagnostics": output_payload.get("diagnostics", {}),
        "audit_record_parsed": any(event.event_type == "record_parsed" and event.target_type == "fulltext_parse_result" for event in audit),
        "governance_draft_created": any(event.action == "draft_created" and event.target_type == "fulltext_parsing" for event in governance),
        "final_extraction_exists": final_extraction_exists,
        "quality_assessment_exists": quality_exists,
        "screening_decision_exists": screening_exists,
        "prisma_studies_included": prisma.studies_included,
        "prisma_full_text_reports_excluded": prisma.full_text_reports_excluded,
        "safety_note": output_payload.get("safety_note", ""),
    }


def _check_packaged_worker_boundary(packaged_resource_root: Path) -> dict[str, Any]:
    worker_path = packaged_resource_root / "biomedpilot_ocr_worker" / "__main__.py"
    if not worker_path.exists():
        raise SystemExit(f"Packaged OCR worker is missing: {worker_path}")
    disallowed_paths = [
        packaged_resource_root / "paddleocr",
        packaged_resource_root / "paddlepaddle",
        packaged_resource_root / "venv",
        packaged_resource_root / ".paddlex",
        packaged_resource_root / "runtime_manifest.json",
    ]
    bundled_runtime_hits = [str(path) for path in disallowed_paths if path.exists()]
    if bundled_runtime_hits:
        raise SystemExit(f"PaddleOCR runtime appears bundled in app resources: {bundled_runtime_hits}")
    return {
        "checked": True,
        "packaged_resource_root": str(packaged_resource_root),
        "worker_module_path": str(worker_path),
        "bundles_paddleocr_runtime": False,
        "bundled_runtime_hits": bundled_runtime_hits,
    }


def _stamp() -> str:
    return "acceptance_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


if __name__ == "__main__":
    raise SystemExit(main())
