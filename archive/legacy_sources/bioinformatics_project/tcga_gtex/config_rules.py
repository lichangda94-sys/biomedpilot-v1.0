"""Rule loading foundation for Module 4 configs and generated resources."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = REPO_ROOT / "configs" / "rules"
COMPARISONS_DIR = REPO_ROOT / "configs" / "comparisons"
GENE_PANELS_DIR = REPO_ROOT / "configs" / "gene_panels"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class Module4RuleConfigError(ValueError):
    """Raised when a Module 4 rule bundle is missing required structure."""


RULE_BUNDLE_SCHEMAS: dict[str, dict[str, type]] = {
    "lexicon_builder_inputs.json": {
        "tcga_projects": list,
        "gtex_tissue_catalog": list,
        "tcga_sample_type_values": list,
        "tcga_tissue_type_values": list,
        "tcga_tumor_descriptor_values": list,
        "tcga_data_category_values": list,
        "tcga_data_type_values": list,
        "tcga_experimental_strategy_values": list,
        "tcga_workflow_type_values": list,
        "ui_excluded_field_names": list,
    },
    "tcga_gtex_resources.json": {
        "default_tcga_data_types": list,
        "default_gtex_resources": list,
        "tcga_file_templates": dict,
        "gtex_file_templates": dict,
    },
    "coverage_audit_rules.json": {
        "high_frequency_cancers": list,
        "high_frequency_tissues": list,
    },
}

RULE_BUNDLE_FILES = tuple(RULE_BUNDLE_SCHEMAS)


@dataclass
class Module4RuleService:
    """Small injectable service for Module 4 rule/config access.

    The existing function loaders stay as compatibility shims. New Module 4
    code should prefer this service so rule access remains testable and can be
    pointed at fixture directories without mutating module globals.
    """

    rules_dir: Path = RULES_DIR
    comparisons_dir: Path = COMPARISONS_DIR
    gene_panels_dir: Path = GENE_PANELS_DIR
    _cache: dict[Path, dict[str, Any]] = field(default_factory=dict, init=False, repr=False)

    def _json_path(self, directory: Path, file_name: str) -> Path:
        return directory / file_name

    def load_json(self, path: Path) -> dict[str, Any]:
        resolved = path.expanduser().resolve()
        if resolved not in self._cache:
            self._cache[resolved] = _load_json(resolved)
        return self._cache[resolved]

    def load_rule_bundle(self, file_name: str) -> dict[str, Any]:
        bundle = self.load_json(self._json_path(self.rules_dir, file_name))
        self.validate_rule_bundle(file_name, bundle)
        return bundle

    def rule_section(self, file_name: str, section: str, default: Any = None) -> Any:
        bundle = self.load_rule_bundle(file_name)
        return bundle.get(section, default)

    def validate_rule_bundle(self, file_name: str, bundle: dict[str, Any]) -> None:
        schema = RULE_BUNDLE_SCHEMAS.get(file_name)
        if schema is None:
            return
        for section, expected_type in schema.items():
            if section not in bundle:
                raise Module4RuleConfigError(f"{file_name} is missing required section: {section}")
            if not isinstance(bundle[section], expected_type):
                raise Module4RuleConfigError(
                    f"{file_name}.{section} must be {expected_type.__name__}, "
                    f"got {type(bundle[section]).__name__}"
                )

    def inspect_rule_bundle(self, file_name: str) -> dict[str, Any]:
        path = self._json_path(self.rules_dir, file_name).expanduser().resolve()
        if not path.exists():
            return {
                "file_name": file_name,
                "path": str(path),
                "status": "missing",
                "loaded": False,
                "message": "Rule bundle file does not exist.",
                "missing_sections": list(RULE_BUNDLE_SCHEMAS.get(file_name, {})),
                "invalid_sections": {},
            }

        try:
            bundle = self.load_json(path)
            self.validate_rule_bundle(file_name, bundle)
        except Module4RuleConfigError as exc:
            schema = RULE_BUNDLE_SCHEMAS.get(file_name, {})
            raw_bundle = self._cache.get(path, {})
            missing_sections = [section for section in schema if section not in raw_bundle]
            invalid_sections = {
                section: {
                    "expected": expected_type.__name__,
                    "actual": type(raw_bundle[section]).__name__,
                }
                for section, expected_type in schema.items()
                if section in raw_bundle and not isinstance(raw_bundle[section], expected_type)
            }
            return {
                "file_name": file_name,
                "path": str(path),
                "status": "invalid",
                "loaded": True,
                "message": str(exc),
                "missing_sections": missing_sections,
                "invalid_sections": invalid_sections,
            }
        except Exception as exc:
            return {
                "file_name": file_name,
                "path": str(path),
                "status": "invalid",
                "loaded": False,
                "message": str(exc),
                "missing_sections": [],
                "invalid_sections": {},
            }

        return {
            "file_name": file_name,
            "path": str(path),
            "status": "loaded",
            "loaded": True,
            "message": "Rule bundle loaded and validated.",
            "missing_sections": [],
            "invalid_sections": {},
        }

    def inspect_rule_bundles(self, file_names: list[str] | tuple[str, ...] | None = None) -> dict[str, Any]:
        selected_files = tuple(file_names or RULE_BUNDLE_FILES)
        bundles = [self.inspect_rule_bundle(file_name) for file_name in selected_files]
        status_counts: dict[str, int] = {}
        for bundle in bundles:
            status = bundle["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        return {
            "status": "success" if all(bundle["status"] == "loaded" for bundle in bundles) else "failed",
            "bundle_count": len(bundles),
            "status_counts": status_counts,
            "bundles": bundles,
        }

    def load_lexicon_builder_inputs(self) -> dict[str, Any]:
        return self.load_rule_bundle("lexicon_builder_inputs.json")

    def load_tcga_gtex_resource_rules(self) -> dict[str, Any]:
        return self.load_rule_bundle("tcga_gtex_resources.json")

    def load_coverage_audit_rules(self) -> dict[str, Any]:
        return self.load_rule_bundle("coverage_audit_rules.json")

    def load_comparison_config(self, dataset_id: str) -> dict[str, Any] | None:
        path = self._json_path(self.comparisons_dir, f"{dataset_id}.json")
        if not path.exists():
            return None
        return self.load_json(path)

    def load_gene_panel(self, panel_id: str) -> dict[str, Any] | None:
        path = self._json_path(self.gene_panels_dir, f"{panel_id}.json")
        if not path.exists():
            return None
        return self.load_json(path)

    def clear_cache(self) -> None:
        self._cache.clear()


def get_default_rule_service() -> Module4RuleService:
    return Module4RuleService()


def inspect_rule_bundles() -> dict[str, Any]:
    return get_default_rule_service().inspect_rule_bundles()


@lru_cache(maxsize=None)
def load_lexicon_builder_inputs() -> dict[str, Any]:
    return get_default_rule_service().load_lexicon_builder_inputs()


@lru_cache(maxsize=None)
def load_tcga_gtex_resource_rules() -> dict[str, Any]:
    return get_default_rule_service().load_tcga_gtex_resource_rules()


@lru_cache(maxsize=None)
def load_coverage_audit_rules() -> dict[str, Any]:
    return get_default_rule_service().load_coverage_audit_rules()


def load_comparison_config(dataset_id: str) -> dict[str, Any] | None:
    return get_default_rule_service().load_comparison_config(dataset_id)


def load_gene_panel(panel_id: str) -> dict[str, Any] | None:
    return get_default_rule_service().load_gene_panel(panel_id)


__all__ = [
    "COMPARISONS_DIR",
    "GENE_PANELS_DIR",
    "Module4RuleConfigError",
    "Module4RuleService",
    "RULE_BUNDLE_FILES",
    "RULE_BUNDLE_SCHEMAS",
    "RULES_DIR",
    "get_default_rule_service",
    "inspect_rule_bundles",
    "load_comparison_config",
    "load_coverage_audit_rules",
    "load_gene_panel",
    "load_lexicon_builder_inputs",
    "load_tcga_gtex_resource_rules",
]
