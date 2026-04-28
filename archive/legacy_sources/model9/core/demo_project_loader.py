from __future__ import annotations

import json
from pathlib import Path

from core.project_workspace import ProjectWorkspaceState, ProjectWorkspaceStore
from reporting.profile_readiness import PROFILE_READINESS_FILENAME


def create_demo_meta_readiness_project(projects_root: Path) -> ProjectWorkspaceState:
    store = ProjectWorkspaceStore(projects_root)
    state = store.create_project(
        project_type="meta_analysis",
        name="Demo Profile Readiness Project",
        project_id="demo-profile-readiness",
    )
    readiness = {
        "rows": [
            {
                "profile": "TREATMENT_EFFECT_META",
                "support_status": "supported",
                "supported_now": True,
                "policy_ready": True,
                "unsupported": "",
                "unimplemented": "external comparator harmonization",
                "warnings": "",
                "recommended_next_action": "Use supported binary or HR rows before advanced comparator policies.",
            },
            {
                "profile": "DIAGNOSTIC_ACCURACY_META",
                "support_status": "policy_ready",
                "supported_now": False,
                "policy_ready": True,
                "unsupported": "HSROC; SROC; bivariate pooling",
                "unimplemented": "reported sensitivity/specificity-only recalculation",
                "warnings": "reported metric only rows need explicit marking",
                "recommended_next_action": "Keep TP/FP/FN/TN rows separate from reported metric-only rows.",
            },
            {
                "profile": "BIOMARKER_PREVALENCE_ASSOCIATION_META",
                "support_status": "mixed",
                "supported_now": False,
                "policy_ready": True,
                "unsupported": "pooled prevalence runner",
                "unimplemented": "Freeman-Tukey transformation; logit transformation",
                "warnings": "prevalence-only rows are stored but not pooled",
                "recommended_next_action": "Keep numerator, denominator, assay, and threshold metadata structured.",
            },
        ]
    }
    (state.project_dir / PROFILE_READINESS_FILENAME).write_text(
        json.dumps(readiness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return state
