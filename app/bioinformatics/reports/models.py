from __future__ import annotations

REPORT_READY_SCHEMA_VERSION = "biomedpilot.report_ready_gate.v1"
REPORT_PACKAGE_SCHEMA_VERSION = "biomedpilot.report_export_package.v1"
REPORT_STATUSES = {"draft_only", "blocked", "eligible_for_internal_report", "report_ready_package_created", "test_report_only"}
