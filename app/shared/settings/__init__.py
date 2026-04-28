from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SettingsProfile:
    default_project_path: str = "project_storage/projects"
    language: str = "zh-CN"
    python_environment: str = "current"
    r_environment: str = "not configured"
    local_ai_model: str = "not configured"
    database_settings: str = "local"
    chart_style: str = "default"
    export_format: str = "docx,pdf,csv"
    cache_cleanup: str = "manual"

