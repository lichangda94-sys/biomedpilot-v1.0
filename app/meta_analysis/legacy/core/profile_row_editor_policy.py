from __future__ import annotations

from dataclasses import dataclass

from core.profile_row_templates import ProfileTemplateType
from core.profile_row_validation import validate_profile_rows


@dataclass(frozen=True)
class ProfileRowEditorActionDecision:
    action: str
    allowed: bool
    requires_confirmation: bool
    message: str
    issue_count: int = 0


def evaluate_profile_row_save(
    profile_type: ProfileTemplateType,
    rows: list[dict[str, str]],
) -> ProfileRowEditorActionDecision:
    issues = validate_profile_rows(profile_type, rows)
    if issues:
        return ProfileRowEditorActionDecision(
            action="save",
            allowed=False,
            requires_confirmation=False,
            issue_count=len(issues),
            message=(
                "Save blocked: fix structural validation issues before writing "
                "project row CSV."
            ),
        )
    return ProfileRowEditorActionDecision(
        action="save",
        allowed=True,
        requires_confirmation=False,
        issue_count=0,
        message="Save allowed: rows passed structural validation.",
    )


def evaluate_profile_row_load(is_dirty: bool) -> ProfileRowEditorActionDecision:
    if is_dirty:
        return ProfileRowEditorActionDecision(
            action="load",
            allowed=False,
            requires_confirmation=True,
            message=(
                "Load requires confirmation: current table has unsaved changes "
                "that would be discarded."
            ),
        )
    return ProfileRowEditorActionDecision(
        action="load",
        allowed=True,
        requires_confirmation=False,
        message="Load allowed: no unsaved table changes.",
    )


def evaluate_profile_row_switch(is_dirty: bool) -> ProfileRowEditorActionDecision:
    if is_dirty:
        return ProfileRowEditorActionDecision(
            action="switch_profile",
            allowed=False,
            requires_confirmation=True,
            message=(
                "Profile switch requires confirmation: current table has unsaved "
                "changes that would be discarded."
            ),
        )
    return ProfileRowEditorActionDecision(
        action="switch_profile",
        allowed=True,
        requires_confirmation=False,
        message="Profile switch allowed: no unsaved table changes.",
    )
