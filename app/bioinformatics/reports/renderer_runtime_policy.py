from __future__ import annotations

from typing import Any


FULL_INTEGRATED_RENDERER_RUNTIME_PACKAGING_POLICY_SCHEMA_VERSION = "biomedpilot.full_integrated_renderer_runtime_packaging_policy.v1"
FULL_INTEGRATED_RENDERER_RUNTIME_POLICY_ID = "b24_3_system_path_no_bundled_renderers"
DEFAULT_RENDERER_SEARCH_PATHS = ("/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin")


def build_full_integrated_renderer_runtime_packaging_policy() -> dict[str, Any]:
    return {
        "schema_version": FULL_INTEGRATED_RENDERER_RUNTIME_PACKAGING_POLICY_SCHEMA_VERSION,
        "policy_id": FULL_INTEGRATED_RENDERER_RUNTIME_POLICY_ID,
        "releasebuild_policy": {
            "bundles_external_renderers": False,
            "network_downloads": False,
            "auto_install": False,
            "codesign_scope": "BioMedPilot app bundle only; no third-party renderer binaries are redistributed.",
            "license_scope": "External renderer licenses remain with the user's system installation because ReleaseBuild does not redistribute Pandoc, TeX, wkhtmltopdf, or Quarto.",
            "package_size_impact": "No bundled Pandoc/TeX/wkhtmltopdf payload is added.",
        },
        "startup_path_policy": {
            "environment_variable": "BIOMEDPILOT_RENDERER_SEARCH_PATHS",
            "default_search_paths": list(DEFAULT_RENDERER_SEARCH_PATHS),
            "open_w_policy": "Launcher exports stable Homebrew/system command search paths so Finder/open -W uses the same detect-first policy as source runs.",
            "override_policy": "Users may still provide commands through PATH; BioMedPilot does not install or download missing renderer tools.",
        },
        "docx": {
            "activation_status": "disabled_until_docx_renderer_activation_stage",
            "runtime_provider": "user_system_pandoc_on_search_path",
            "required_dependencies": ["pandoc"],
            "bundled": False,
            "missing_behavior": "graceful_blocked:renderer_dependency_missing:pandoc",
            "renderer": "pandoc_docx",
        },
        "pdf": {
            "activation_status": "disabled_until_pdf_renderer_activation_stage",
            "runtime_provider": "disabled_detect_only",
            "selected_engine": "pandoc_xelatex_when_pdf_activation_is_explicitly_approved",
            "required_dependencies_when_activated": ["pandoc", "xelatex"],
            "wkhtmltopdf_policy": "detect_only_not_formal_full_integrated_report_backend",
            "bundled": False,
            "missing_behavior": "graceful_blocked:renderer_dependency_missing:pandoc_or_xelatex",
        },
        "quarto": {
            "activation_status": "disabled",
            "runtime_provider": "detect_only_not_used_for_full_integrated_report_export",
            "bundled": False,
        },
    }
