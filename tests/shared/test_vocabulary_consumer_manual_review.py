from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "data" / "medical_terms" / "review_reports"
DOCS = ROOT / "docs" / "medical_terms"


def test_vocabulary_consumer_manual_review_decisions_are_recorded() -> None:
    report = json.loads((REPORTS / "vocabulary_consumer_manual_review.json").read_text(encoding="utf-8"))

    assert report["report_name"] == "vocabulary_consumer_manual_review"
    assert report["source_manual_review_count"] == 15
    assert report["business_runtime_bypass_found"] is False
    assert report["business_runtime_refactor_executed"] is False
    assert report["loader_modified"] is False
    assert report["mini_medical_terms_index_modified"] is False
    assert report["zh_term_overrides_modified"] is False
    assert report["summary"] == {
        "reviewed_count": 15,
        "classification_counts": {
            "approved_script_internal": 13,
            "needs_scope_loader_migration": 2,
        },
        "manual_fix_required_count": 0,
        "needs_scope_loader_migration_count": 2,
        "approved_script_internal_count": 13,
        "safe_test_fixture_count": 0,
    }
    assert len(report["items"]) == 15
    assert all(item["final_classification"] != "manual_fix_required" for item in report["items"])
    assert all(item["runtime_business_path"] is False for item in report["items"])
    assert (DOCS / "vocabulary_consumer_manual_review_20260520.md").exists()


def test_bioinformatics_coverage_audit_is_only_scope_migration_follow_up() -> None:
    report = json.loads((REPORTS / "vocabulary_consumer_manual_review.json").read_text(encoding="utf-8"))
    needs_migration = [item for item in report["items"] if item["final_classification"] == "needs_scope_loader_migration"]

    assert {item["file"] for item in needs_migration} == {"scripts/audit_bioinformatics_vocabulary_coverage.py"}
    assert {item["matched_path"] for item in needs_migration} == {
        "mini_medical_terms_index.json",
        "zh_term_overrides.json",
    }
    assert report["follow_up_actions"] == [
        {
            "id": "script_audit_bioinformatics_vocabulary_coverage_scope_migration",
            "priority": "low_medium",
            "reason": "Script can regenerate old pre-scoped Bioinformatics coverage reports if reused.",
            "recommended_action": "Retire or update scripts/audit_bioinformatics_vocabulary_coverage.py to use current Bioinformatics scoped audit files/load_terms(scope='bioinformatics') in a separate maintenance patch.",
            "business_runtime_blocker": False,
        }
    ]


def test_manual_review_stage_does_not_modify_runtime_or_loader_files() -> None:
    changed = set(_git_changed_files())

    assert "data/medical_terms/mini_medical_terms_index.json" not in changed
    assert "data/medical_terms/zh_term_overrides.json" not in changed
    assert "data/medical_terms/meta_analysis/meta_seed_terms.json" not in changed
    assert not any(path.startswith("data/medical_terms/bioinformatics/bioinformatics_") for path in changed)
    assert not any(path.startswith("app/shared/query_intelligence/medical_terms/") for path in changed)


def _git_changed_files() -> list[str]:
    unstaged = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    return sorted({line for output in (unstaged, staged) for line in output.splitlines() if line})
