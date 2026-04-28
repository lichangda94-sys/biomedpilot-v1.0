from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class AppConfig:
    app_name: str = "BioMedPilot"
    app_slug: str = "model9"
    organization_name: str = "BioMedPilot"
    debug: bool = False
    startup_test_ms: int = 0

    @classmethod
    def load(cls) -> "AppConfig":
        defaults = cls()
        return cls(
            app_name=os.getenv("MODEL9_APP_NAME", defaults.app_name),
            app_slug=os.getenv("MODEL9_APP_SLUG", defaults.app_slug),
            organization_name=os.getenv("MODEL9_ORG_NAME", defaults.organization_name),
            debug=os.getenv("MODEL9_DEBUG", "").lower() in {"1", "true", "yes", "on"},
            startup_test_ms=int(os.getenv("MODEL9_STARTUP_TEST_MS", "0")),
        )
