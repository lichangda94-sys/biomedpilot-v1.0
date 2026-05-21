from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "data" / "medical_terms" / "review_reports"
DOCS = ROOT / "docs" / "medical_terms"

MATCHED_PATHS = (
    "mini_medical_terms_index.json",
    "zh_term_overrides.json",
    "meta_seed_terms.json",
    "bioinformatics_species_terms.json",
    "bioinformatics_data_type_terms.json",
    "bioinformatics_tissue_terms.json",
    "meta_migrated_from_shared_terms.json",
    "legacy_meta_compatibility_map.json",
)

SCAN_ROOTS = ("app", "scripts", "tests")
TEXT_SUFFIXES = {".py", ".md", ".json", ".jsonl", ".toml", ".yaml", ".yml"}


@dataclass(frozen=True)
class ConsumerFinding:
    file: str
    line: int
    matched_path: str
    consumer_type: str
    classification: str
    recommended_scope_loader: str
    risk_level: str
    manual_review_required: bool
    notes: str


def main() -> None:
    findings = sorted(_scan(), key=lambda item: (item.file, item.line, item.matched_path))
    payload = _build_payload(findings)
    REPORTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "vocabulary_consumer_adoption_audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (DOCS / "vocabulary_consumer_adoption_audit_20260520.md").write_text(
        _markdown(payload),
        encoding="utf-8",
    )
    print(f"findings={len(findings)}")
    print(f"classifications={dict(payload['summary']['classification_counts'])}")


def _scan() -> list[ConsumerFinding]:
    findings: list[ConsumerFinding] = []
    for root_name in SCAN_ROOTS:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
                continue
            if "__pycache__" in path.parts or path == Path(__file__).resolve():
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            rel = path.relative_to(ROOT).as_posix()
            for index, line in enumerate(lines, start=1):
                for matched in MATCHED_PATHS:
                    if matched not in line:
                        continue
                    findings.append(_classify(rel, index, matched, line))
    return findings


def _classify(file: str, line: int, matched_path: str, line_text: str) -> ConsumerFinding:
    consumer_type = _consumer_type(line_text)
    recommended = _recommended_loader(matched_path)

    if file.startswith("tests/"):
        return ConsumerFinding(
            file=file,
            line=line,
            matched_path=matched_path,
            consumer_type=consumer_type,
            classification="safe_test_fixture",
            recommended_scope_loader=(
                "No migration required for tests; use load_terms(scope=...) in new runtime-facing tests."
            ),
            risk_level="low",
            manual_review_required=False,
            notes="Test fixture or boundary assertion, not production runtime consumption.",
        )

    if file in {
        "app/shared/query_intelligence/medical_terms/scope_loader.py",
        "app/shared/query_intelligence/medical_terms/term_index_loader.py",
        "app/shared/query_intelligence/medical_terms/zh_overrides_loader.py",
        "app/shared/query_intelligence/meta_seed_terms/loader.py",
    }:
        classification = "approved_loader_internal"
        if matched_path in {"meta_migrated_from_shared_terms.json", "legacy_meta_compatibility_map.json"}:
            classification = "legacy_meta_compatibility_allowed"
        return ConsumerFinding(
            file=file,
            line=line,
            matched_path=matched_path,
            consumer_type=consumer_type,
            classification=classification,
            recommended_scope_loader="Already part of the approved loader layer.",
            risk_level="low",
            manual_review_required=False,
            notes="Loader internals are allowed to read source files directly.",
        )

    if file.startswith("scripts/"):
        classification = "manual_review_required"
        risk = "medium"
        note = "Script reads vocabulary files directly; keep allowed for audits/builders, but review before runtime reuse."
        if "audit" in file or "prepare" in file or "inventory" in file:
            classification = "bioinformatics_scoped_allowed" if matched_path.startswith("bioinformatics_") else "manual_review_required"
            risk = "low" if classification == "bioinformatics_scoped_allowed" else "medium"
            note = "Audit or review-batch script; direct reads are acceptable as reporting inputs but should not become runtime lookup paths."
        return ConsumerFinding(
            file=file,
            line=line,
            matched_path=matched_path,
            consumer_type=consumer_type,
            classification=classification,
            recommended_scope_loader=recommended,
            risk_level=risk,
            manual_review_required=classification == "manual_review_required",
            notes=note,
        )

    return ConsumerFinding(
        file=file,
        line=line,
        matched_path=matched_path,
        consumer_type=consumer_type,
        classification="needs_scope_loader_migration",
        recommended_scope_loader=recommended,
        risk_level="high",
        manual_review_required=True,
        notes="Runtime-adjacent path references vocabulary source file outside the approved loader layer.",
    )


def _consumer_type(line_text: str) -> str:
    lowered = line_text.lower()
    if "read_text" in lowered or "json.loads" in lowered or "open(" in lowered:
        return "direct_json_read"
    if "path(" in lowered or "/" in line_text or "_PATH" in line_text:
        return "path_reference"
    return "string_reference"


def _recommended_loader(matched_path: str) -> str:
    if matched_path in {"meta_seed_terms.json", "meta_migrated_from_shared_terms.json", "legacy_meta_compatibility_map.json"}:
        return "load_terms(scope='meta_analysis')"
    if matched_path.startswith("bioinformatics_"):
        return "load_terms(scope='bioinformatics')"
    if matched_path == "mini_medical_terms_index.json":
        return "load_terms(scope='<shared_core|meta_analysis|bioinformatics>') based on caller context"
    if matched_path == "zh_term_overrides.json":
        return "Use approved zh override loader or load_terms(scope=...) based on caller context"
    return "load_terms(scope=...)"


def _build_payload(findings: list[ConsumerFinding]) -> dict[str, object]:
    classification_counts = Counter(item.classification for item in findings)
    matched_path_counts = Counter(item.matched_path for item in findings)
    manual_review = [item for item in findings if item.manual_review_required]
    return {
        "audit_name": "vocabulary_consumer_adoption_audit",
        "audit_date": "2026-05-20",
        "phase": "handoff_gap_remediation",
        "scan_roots": list(SCAN_ROOTS),
        "matched_paths": list(MATCHED_PATHS),
        "runtime_refactor_executed": False,
        "loader_behavior_modified": False,
        "summary": {
            "finding_count": len(findings),
            "manual_review_required_count": len(manual_review),
            "classification_counts": dict(sorted(classification_counts.items())),
            "matched_path_counts": dict(sorted(matched_path_counts.items())),
        },
        "findings": [asdict(item) for item in findings],
    }


def _markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]  # type: ignore[index]
    findings = payload["findings"]  # type: ignore[index]
    lines = [
        "# Vocabulary Consumer Adoption Audit",
        "",
        "Date: 2026-05-20",
        "",
        "## Scope",
        "",
        "This audit scans code and test paths for direct references to medical vocabulary source files. It reports potential bypasses of the scope-aware loader but does not refactor runtime code.",
        "",
        "Scanned roots: `app/`, `scripts/`, `tests/`.",
        "",
        "## Summary",
        "",
        f"- Findings: `{summary['finding_count']}`",
        f"- Manual review required: `{summary['manual_review_required_count']}`",
        f"- Runtime refactor executed: `{str(payload['runtime_refactor_executed']).lower()}`",
        f"- Loader behavior modified: `{str(payload['loader_behavior_modified']).lower()}`",
        "",
        "Classification counts:",
        "",
    ]
    for key, count in summary["classification_counts"].items():  # type: ignore[index]
        lines.append(f"- `{key}`: {count}")
    lines.extend(["", "## Findings", ""])
    for item in findings:
        lines.append(
            f"- `{item['file']}:{item['line']}` references `{item['matched_path']}`; "
            f"classification=`{item['classification']}`; risk=`{item['risk_level']}`; "
            f"recommendation={item['recommended_scope_loader']}."
        )
    lines.extend(
        [
            "",
            "## Remediation Guidance",
            "",
            "- Approved loader internals may continue direct file reads.",
            "- Tests may continue direct reads when asserting file-level boundaries.",
            "- Audit/build scripts may keep direct reads as reporting inputs, but must not become runtime lookup paths.",
            "- Any runtime-adjacent direct consumer should migrate to `load_terms(scope=...)` in a separate implementation phase.",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
