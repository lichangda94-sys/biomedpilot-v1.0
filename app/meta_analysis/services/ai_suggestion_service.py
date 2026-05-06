from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.models.ai_suggestion import (
    AISuggestion,
    AISuggestionActionResult,
    AISuggestionStatus,
    SUGGESTION_TYPES,
    TARGET_TYPES,
    ai_suggestion_from_dict,
    ai_suggestion_to_dict,
    new_ai_suggestion_id,
    now_utc,
)
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


class AISuggestionService:
    def __init__(
        self,
        *,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
    ) -> None:
        self._task_center = task_center
        self._data_center = data_center
        self._research_governance = research_governance or MetaResearchGovernanceService()

    def create_ai_suggestion(
        self,
        project_dir: Path,
        *,
        project_id: str,
        target_type: str,
        target_id: str,
        suggestion_type: str,
        suggested_value: object,
        rationale: str,
        confidence: float,
    ) -> AISuggestion:
        project_dir = project_dir.expanduser().resolve()
        _validate_kind(target_type, TARGET_TYPES, "target_type")
        _validate_kind(suggestion_type, SUGGESTION_TYPES, "suggestion_type")
        task = self._start_task(
            project_id=project_id,
            task_type=TaskType.AI_SUGGESTION_CREATE,
            title="AI Suggestion Create",
            summary=f"Creating AI suggestion for {target_type}:{target_id}",
        )
        now = now_utc()
        suggestion = AISuggestion(
            suggestion_id=new_ai_suggestion_id(),
            project_id=project_id,
            target_type=target_type,
            target_id=target_id,
            suggestion_type=suggestion_type,
            suggested_value=suggested_value,
            rationale=rationale,
            confidence=max(0.0, min(1.0, float(confidence))),
            status=AISuggestionStatus.PENDING.value,
            reviewer_action="",
            created_at=now,
            updated_at=now,
        )
        self._append_or_update(project_dir, suggestion)
        self._research_governance.record_suggestion_created(
            project_dir,
            project_id=project_id,
            target_type=target_type,
            target_id=target_id,
            source_suggestion_id=suggestion.suggestion_id,
            after=ai_suggestion_to_dict(suggestion),
            metadata={"suggestion_type": suggestion_type, "confidence": suggestion.confidence},
        )
        self._register_asset(project_id, project_dir)
        self._finish_task(task, success=True, summary=f"AI suggestion created: {suggestion.suggestion_id}")
        return suggestion

    def create_mock_suggestion(
        self,
        project_dir: Path,
        *,
        project_id: str,
        target_type: str,
        target_id: str,
        suggestion_type: str,
    ) -> AISuggestion:
        return self.create_ai_suggestion(
            project_dir,
            project_id=project_id,
            target_type=target_type,
            target_id=target_id,
            suggestion_type=suggestion_type,
            suggested_value={"mock": True, "target_id": target_id},
            rationale="Local mock suggestion provider for Developer Preview testing.",
            confidence=0.5,
        )

    def list_ai_suggestions(self, project_dir: Path, *, status: str | None = None) -> list[AISuggestion]:
        suggestions = self._load(project_dir.expanduser().resolve())
        if status is not None:
            suggestions = [suggestion for suggestion in suggestions if suggestion.status == status]
        return suggestions

    def accept_ai_suggestion(self, project_dir: Path, suggestion_id: str, reviewer_action: str = "accepted") -> AISuggestionActionResult:
        return self._transition(
            project_dir,
            suggestion_id,
            status=AISuggestionStatus.ACCEPTED.value,
            reviewer_action=reviewer_action,
            task_type=TaskType.AI_SUGGESTION_ACCEPT,
            title="AI Suggestion Accept",
        )

    def reject_ai_suggestion(self, project_dir: Path, suggestion_id: str, reviewer_action: str = "rejected") -> AISuggestionActionResult:
        return self._transition(
            project_dir,
            suggestion_id,
            status=AISuggestionStatus.REJECTED.value,
            reviewer_action=reviewer_action,
            task_type=TaskType.AI_SUGGESTION_REJECT,
            title="AI Suggestion Reject",
        )

    def edit_ai_suggestion(
        self,
        project_dir: Path,
        suggestion_id: str,
        *,
        suggested_value: object,
        reviewer_action: str = "edited",
    ) -> AISuggestionActionResult:
        project_dir = project_dir.expanduser().resolve()
        suggestion = self._require(project_dir, suggestion_id)
        task = self._start_task(
            project_id=suggestion.project_id,
            task_type=TaskType.AI_SUGGESTION_EDIT,
            title="AI Suggestion Edit",
            summary=f"Editing AI suggestion {suggestion_id}",
        )
        updated = replace(
            suggestion,
            suggested_value=suggested_value,
            status=AISuggestionStatus.EDITED.value,
            reviewer_action=reviewer_action,
            updated_at=now_utc(),
        )
        self._append_or_update(project_dir, updated)
        self._research_governance.record_user_confirmation(
            project_dir,
            project_id=suggestion.project_id,
            action="edit",
            actor="reviewer",
            target_type=suggestion.target_type,
            target_id=suggestion.target_id,
            before=ai_suggestion_to_dict(suggestion),
            after=ai_suggestion_to_dict(updated),
            source_suggestion_id=suggestion_id,
            metadata={"reviewer_action": reviewer_action},
        )
        self._finish_task(task, success=True, summary=f"AI suggestion edited: {suggestion_id}")
        return AISuggestionActionResult(
            success=True,
            suggestion_id=suggestion_id,
            status=updated.status,
            message="AI suggestion edited. It still requires accept and explicit apply before any target write.",
            output_path=str(self._suggestions_path(project_dir)),
        )

    def apply_accepted_suggestion(self, project_dir: Path, suggestion_id: str) -> AISuggestionActionResult:
        project_dir = project_dir.expanduser().resolve()
        suggestion = self._require(project_dir, suggestion_id)
        task = self._start_task(
            project_id=suggestion.project_id,
            task_type=TaskType.AI_SUGGESTION_APPLY,
            title="AI Suggestion Apply",
            summary=f"Applying accepted AI suggestion {suggestion_id}",
        )
        if suggestion.status != AISuggestionStatus.ACCEPTED.value:
            message = "Only accepted AI suggestions can be applied. Pending, rejected, and edited suggestions are not applied."
            self._finish_task(task, success=False, summary=message)
            return AISuggestionActionResult(
                success=False,
                suggestion_id=suggestion_id,
                status=suggestion.status,
                message=message,
            )
        output_path = self._append_application(project_dir, suggestion)
        updated = replace(suggestion, reviewer_action="applied", updated_at=now_utc())
        self._append_or_update(project_dir, updated)
        self._finish_task(task, success=True, summary=f"AI suggestion applied via non-overwrite application log: {suggestion_id}")
        return AISuggestionActionResult(
            success=True,
            suggestion_id=suggestion_id,
            status=updated.status,
            message="Accepted AI suggestion applied to the AI application log without overwriting formal data.",
            output_path=str(output_path),
            details={"target_type": suggestion.target_type, "target_id": suggestion.target_id},
        )

    def _transition(
        self,
        project_dir: Path,
        suggestion_id: str,
        *,
        status: str,
        reviewer_action: str,
        task_type: TaskType,
        title: str,
    ) -> AISuggestionActionResult:
        project_dir = project_dir.expanduser().resolve()
        suggestion = self._require(project_dir, suggestion_id)
        task = self._start_task(
            project_id=suggestion.project_id,
            task_type=task_type,
            title=title,
            summary=f"Updating AI suggestion {suggestion_id} to {status}",
        )
        updated = replace(suggestion, status=status, reviewer_action=reviewer_action, updated_at=now_utc())
        self._append_or_update(project_dir, updated)
        action = "accept" if status == AISuggestionStatus.ACCEPTED.value else "reject"
        self._research_governance.record_user_confirmation(
            project_dir,
            project_id=suggestion.project_id,
            action=action,
            actor="reviewer",
            target_type=suggestion.target_type,
            target_id=suggestion.target_id,
            before=ai_suggestion_to_dict(suggestion),
            after=ai_suggestion_to_dict(updated),
            source_suggestion_id=suggestion_id,
            metadata={"reviewer_action": reviewer_action},
        )
        self._finish_task(task, success=True, summary=f"AI suggestion {status}: {suggestion_id}")
        return AISuggestionActionResult(
            success=True,
            suggestion_id=suggestion_id,
            status=status,
            message=f"AI suggestion {status}.",
            output_path=str(self._suggestions_path(project_dir)),
        )

    def _require(self, project_dir: Path, suggestion_id: str) -> AISuggestion:
        for suggestion in self._load(project_dir):
            if suggestion.suggestion_id == suggestion_id:
                return suggestion
        raise ValueError("ai_suggestion_not_found")

    def _append_or_update(self, project_dir: Path, suggestion: AISuggestion) -> Path:
        suggestions = [existing for existing in self._load(project_dir) if existing.suggestion_id != suggestion.suggestion_id]
        suggestions.append(suggestion)
        path = self._suggestions_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "project_id": suggestion.project_id,
                    "data_type": "ai_suggestions",
                    "updated_at": now_utc(),
                    "suggestions": [ai_suggestion_to_dict(item) for item in suggestions],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return path

    def _append_application(self, project_dir: Path, suggestion: AISuggestion) -> Path:
        path = project_dir / "ai" / "applied_suggestions.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = _load_json_dict(path)
        applications = [dict(item) for item in payload.get("applications", []) if isinstance(item, dict)]
        applications.append(
            {
                "application_id": f"aiapply-{uuid4().hex[:12]}",
                "suggestion_id": suggestion.suggestion_id,
                "project_id": suggestion.project_id,
                "target_type": suggestion.target_type,
                "target_id": suggestion.target_id,
                "suggestion_type": suggestion.suggestion_type,
                "suggested_value": suggestion.suggested_value,
                "applied_at": now_utc(),
                "safety_note": "Stored in AI application log only; formal screening/extraction/analysis artifacts are not overwritten.",
            }
        )
        path.write_text(
            json.dumps(
                {
                    "project_id": suggestion.project_id,
                    "data_type": "ai_suggestion_applications",
                    "updated_at": now_utc(),
                    "applications": applications,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return path

    def _load(self, project_dir: Path) -> list[AISuggestion]:
        path = self._suggestions_path(project_dir)
        payload = _load_json_dict(path)
        return [ai_suggestion_from_dict(item) for item in payload.get("suggestions", []) if isinstance(item, dict)]

    def _suggestions_path(self, project_dir: Path) -> Path:
        return project_dir / "ai" / "ai_suggestions.json"

    def _register_asset(self, project_id: str, project_dir: Path) -> None:
        if self._data_center is None:
            return
        path = self._suggestions_path(project_dir)
        self._data_center.register_asset(
            project_id=project_id,
            module="meta_analysis",
            data_type="ai_suggestions",
            source_path=str(project_dir),
            output_path=str(path),
            status="available",
        )

    def _start_task(self, *, project_id: str, task_type: TaskType, title: str, summary: str) -> TaskRecord:
        now = now_utc()
        if self._task_center is None:
            return TaskRecord(
                task_id=f"task-{uuid4().hex[:12]}",
                task_type=task_type,
                status=TaskStatus.RUNNING,
                module="meta_analysis",
                title=title,
                created_at=now,
                updated_at=now,
                project_id=project_id,
                started_at=now,
                summary=summary,
            )
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=task_type,
            module="meta_analysis",
            title=title,
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=summary,
        )

    def _finish_task(self, task: TaskRecord, *, success: bool, summary: str) -> None:
        if self._task_center is None:
            return
        now = now_utc()
        self._task_center.save_task(
            TaskRecord(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED if success else TaskStatus.FAILED,
                module=task.module,
                title=task.title,
                created_at=task.created_at,
                updated_at=now,
                project_id=task.project_id,
                started_at=task.started_at,
                finished_at=now,
                summary=summary,
                error_message="" if success else summary,
            )
        )


def _validate_kind(value: str, allowed: tuple[str, ...], field_name: str) -> None:
    if value not in allowed:
        raise ValueError(f"unsupported_{field_name}:{value}")


def _load_json_dict(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}
