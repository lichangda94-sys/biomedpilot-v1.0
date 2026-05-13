from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class LiteratureEdgeCaseAuditItem:
    area: str
    capability: str
    current_status: str
    active_files: tuple[str, ...]
    migration_recommendation: str
    proposed_test: str


class LiteratureEdgeCaseAuditService:
    def build_audit(self) -> list[LiteratureEdgeCaseAuditItem]:
        return [
            LiteratureEdgeCaseAuditItem(
                area="literature_import",
                capability="CSV header aliases",
                current_status="active_runtime_parser_needs_alias_expansion",
                active_files=(
                    "app/meta_analysis/services/literature_batch_import_service.py",
                    "app/meta_analysis/adapters/literature_import_adapter.py",
                ),
                migration_recommendation="add_active_parser_alias_test_before_expanding_headers",
                proposed_test="CSV export with Title, Authors, DOI, PMID, Journal, Year aliases parses into active normalized records.",
            ),
            LiteratureEdgeCaseAuditItem(
                area="literature_import",
                capability="DOI and PMID cleanup",
                current_status="active_runtime_normalizer",
                active_files=(
                    "app/meta_analysis/services/literature_import_service.py",
                    "app/meta_analysis/services/literature_batch_import_service.py",
                ),
                migration_recommendation="keep_active_normalization_guarded_by_contract_tests",
                proposed_test="NBIB/RIS records with DOI suffixes and PMID spacing normalize to stable DOI/PMID values.",
            ),
            LiteratureEdgeCaseAuditItem(
                area="literature_dedup",
                capability="similar-title duplicate detection",
                current_status="active_runtime_identifier_detection",
                active_files=(
                    "app/meta_analysis/services/duplicate_review_service.py",
                    "app/meta_analysis/adapters/duplicate_review_adapter.py",
                ),
                migration_recommendation="add_active_near_title_duplicate_detection_test",
                proposed_test="Two records with near-identical title, adjacent year, same first author, and same journal form one suspected duplicate group.",
            ),
            LiteratureEdgeCaseAuditItem(
                area="literature_dedup",
                capability="completeness-based master candidate",
                current_status="active_runtime_completeness_candidate",
                active_files=("app/meta_analysis/services/dedup_decision_service.py",),
                migration_recommendation="keep_active_master_selection_guarded_by_contract_tests",
                proposed_test="Duplicate group suggests the record with DOI, PMID, abstract, journal, year, and author metadata as master candidate.",
            ),
            LiteratureEdgeCaseAuditItem(
                area="literature_dedup",
                capability="merge field-source trace",
                current_status="partially_active_merge_preview",
                active_files=("app/meta_analysis/services/dedup_decision_service.py",),
                migration_recommendation="add_active_merge_trace_test_before_final_merge_feature",
                proposed_test="Merge preview records which source record supplied DOI, abstract, journal, and year fields.",
            ),
        ]

    def write_audit(self, project_dir: Path) -> Path:
        project_dir = project_dir.expanduser().resolve()
        output_path = project_dir / "audit" / "literature_edge_case_migration_audit.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        items = self.build_audit()
        output_path.write_text(
            json.dumps(
                {
                    "schema_version": "meta_literature_edge_case_migration_audit.v1",
                    "project_id": project_dir.name,
                    "migration_policy": "active_runtime_no_legacy_bridge",
                    "items": [asdict(item) for item in items],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return output_path
