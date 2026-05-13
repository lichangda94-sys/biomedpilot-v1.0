from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.screening_page import (
    export_title_abstract_screening_artifacts,
    title_abstract_screening_state_from_queue,
)
from app.meta_analysis.services.criteria_service import CriteriaBuilderService


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_queue(path: Path) -> None:
    write_json(
        path,
        {
            "project_id": "project",
            "stage": "title_abstract_screening",
            "screening_records": [
                {
                    "screening_record_id": "screen-1",
                    "normalized_record_id": "rec-1",
                    "title": "Trial A",
                    "abstract": "Abstract A",
                    "authors": ["Smith J"],
                    "journal": "Journal A",
                    "year": "2024",
                    "doi": "10.1000/a",
                    "pmid": "111",
                    "decision": "pending",
                },
                {
                    "screening_record_id": "screen-2",
                    "normalized_record_id": "rec-2",
                    "title": "Trial B",
                    "abstract": "Abstract B",
                    "authors_text": "Lee K",
                    "decision": "maybe",
                    "notes": "Needs full text",
                },
                {
                    "screening_record_id": "screen-3",
                    "normalized_record_id": "rec-3",
                    "title": "Review C",
                    "abstract": "",
                    "decision": "excluded",
                    "exclusion_reason_text": "review",
                },
            ],
        },
    )


def test_ab6_title_abstract_state_loads_current_record_progress_and_links(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    queue_path = project_dir / "screening" / "batch_screening_queue.json"
    write_queue(queue_path)

    state = title_abstract_screening_state_from_queue(queue_path, project_dir=project_dir, current_index=0)

    assert state.status_label == "Testing / Developer Preview"
    assert state.current_record is not None
    assert state.current_record.title == "Trial A"
    assert "https://doi.org/10.1000/a" in state.current_record.source_links
    assert "https://pubmed.ncbi.nlm.nih.gov/111/" in state.current_record.source_links
    assert state.next_record_id == "screen-2"
    assert state.progress_summary["total"] == 3
    assert state.progress_summary["pending"] == 1
    assert state.progress_summary["maybe"] == 1
    assert state.progress_summary["needs_review"] == 1
    assert "needs_review" in state.decision_options
    assert "maybe" in state.filter_views


def test_ab6_title_abstract_state_uses_criteria_hints(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    queue_path = project_dir / "screening" / "batch_screening_queue.json"
    write_queue(queue_path)
    (project_dir / "protocol").mkdir(parents=True)
    (project_dir / "protocol" / "review_protocol.json").write_text("{}", encoding="utf-8")
    criteria_service = CriteriaBuilderService()
    criteria_service.save_criteria(project_dir, inclusion_labels=["target population"], exclusion_labels=["wrong population", "wrong outcome"])

    state = title_abstract_screening_state_from_queue(queue_path, project_dir=project_dir, criteria_service=criteria_service)

    assert "Include if: target population" in state.criteria_hints
    assert "wrong population" in state.exclusion_reason_options
    assert state.output_paths["title_abstract_decisions_json"].endswith("screening/title_abstract_decisions.json")


def test_ab6_missing_queue_does_not_crash(tmp_path: Path) -> None:
    queue_path = tmp_path / "project" / "screening" / "missing.json"

    state = title_abstract_screening_state_from_queue(queue_path, project_dir=tmp_path / "project")

    assert state.current_record is None
    assert "missing_screening_queue" in state.warnings
    assert "empty_screening_queue" in state.warnings
    assert state.empty_state


def test_ab6_export_title_abstract_outputs_json_csv_and_summary(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    queue_path = project_dir / "screening" / "batch_screening_queue.json"
    write_queue(queue_path)

    outputs = export_title_abstract_screening_artifacts(queue_path, project_dir)

    assert Path(outputs["title_abstract_decisions_json"]).exists()
    assert Path(outputs["title_abstract_decisions_csv"]).exists()
    assert Path(outputs["screening_summary_json"]).exists()
    summary = json.loads(Path(outputs["screening_summary_json"]).read_text(encoding="utf-8"))
    assert summary["progress_summary"]["total"] == 3
    assert "screen-1" in Path(outputs["title_abstract_decisions_csv"]).read_text(encoding="utf-8")


def test_ab6_previous_next_navigation_bounds(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    queue_path = project_dir / "screening" / "batch_screening_queue.json"
    write_queue(queue_path)

    last = title_abstract_screening_state_from_queue(queue_path, project_dir=project_dir, current_index=99)

    assert last.current_index == 2
    assert last.previous_record_id == "screen-2"
    assert last.next_record_id == ""
