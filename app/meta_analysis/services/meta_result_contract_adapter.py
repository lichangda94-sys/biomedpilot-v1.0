from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from app.meta_analysis.models.analysis_result import AnalysisResult, StudyMetaAnalysisResult, now_utc
from app.meta_analysis.services.figure_result_service import _render_forest_plot_png
from app.meta_analysis.services.meta_statistics_engine_service import MetaStatisticsEngineService


META_RESULT_CONTRACT_SCHEMA_VERSION = "meta_result_contract.v1"
META_RESULT_CONTRACT_ARTIFACT_SCHEMA_VERSION = "meta_result_contract_artifact.v1"


class MetaResultContractAdapter:
    """Bridge v2 Meta statistics results to table/figure/export artifacts."""

    def __init__(self, *, statistics_service: MetaStatisticsEngineService | None = None) -> None:
        self._statistics_service = statistics_service or MetaStatisticsEngineService()

    def contract_root(self, project_dir: Path, analysis_run_id: str) -> Path:
        return project_dir.expanduser().resolve() / "analysis" / "meta_result_contracts" / analysis_run_id

    def contract_path(self, project_dir: Path, analysis_run_id: str) -> Path:
        return self.contract_root(project_dir, analysis_run_id) / "meta_result_contract.json"

    def build_contract(self, project_dir: Path, analysis_run_id: str | None = None) -> dict[str, Any]:
        context = self._load_context(project_dir, analysis_run_id)
        contract_path = self.contract_path(context["project_dir"], context["analysis_run_id"])
        existing = _load_json(contract_path)
        artifacts = existing.get("artifacts", []) if isinstance(existing.get("artifacts"), list) else []
        payload = self._base_contract(context, artifacts=artifacts)
        _write_json(contract_path, payload)
        return payload

    def export_result_table(self, project_dir: Path, analysis_run_id: str | None = None) -> dict[str, Any]:
        context = self._load_context(project_dir, analysis_run_id)
        run_id = context["analysis_run_id"]
        output_path = self.contract_root(context["project_dir"], run_id) / "tables" / "meta_result_table.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result = context["standardized_result"]
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=_result_table_fieldnames())
            writer.writeheader()
            for row in result.get("study_results", []):
                if not isinstance(row, dict):
                    continue
                writer.writerow(
                    {
                        "row_type": "study",
                        "analysis_run_id": run_id,
                        "study_id": row.get("study_id", ""),
                        "record_id": row.get("record_id", ""),
                        "first_author": row.get("first_author", ""),
                        "year": row.get("year", ""),
                        "effect": row.get("effect", ""),
                        "ci_low": row.get("ci_low", ""),
                        "ci_high": row.get("ci_high", ""),
                        "standard_error": row.get("standard_error", ""),
                        "weight": row.get("weight", ""),
                        "model": result.get("model", ""),
                        "effect_measure": result.get("effect_measure", ""),
                    }
                )
            writer.writerow(
                {
                    "row_type": "pooled",
                    "analysis_run_id": run_id,
                    "study_id": "pooled",
                    "record_id": "",
                    "first_author": "Pooled effect",
                    "year": "",
                    "effect": result.get("pooled_effect", ""),
                    "ci_low": result.get("ci_low", ""),
                    "ci_high": result.get("ci_high", ""),
                    "standard_error": "",
                    "weight": "",
                    "model": result.get("model", ""),
                    "effect_measure": result.get("effect_measure", ""),
                }
            )
        return self._register_artifact(
            context,
            artifact_type="result_table",
            path=output_path,
            format="csv",
            status="available",
        )

    def generate_forest_plot(self, project_dir: Path, analysis_run_id: str | None = None) -> dict[str, Any]:
        context = self._load_context(project_dir, analysis_run_id)
        run_id = context["analysis_run_id"]
        output_path = self.contract_root(context["project_dir"], run_id) / "figures" / f"forest_plot_{run_id}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _render_forest_plot_png(_analysis_result_from_standardized(context["standardized_result"]), output_path, dpi=120)
        return self._register_artifact(
            context,
            artifact_type="forest_plot",
            path=output_path,
            format="png",
            status="available",
        )

    def export_report_artifact(self, project_dir: Path, analysis_run_id: str | None = None) -> dict[str, Any]:
        context = self._load_context(project_dir, analysis_run_id)
        run_id = context["analysis_run_id"]
        result = context["standardized_result"]
        output_path = self.contract_root(context["project_dir"], run_id) / "reports" / f"meta_result_export_{run_id}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        diagnostics = result.get("diagnostics", {}) if isinstance(result.get("diagnostics"), dict) else {}
        lines = [
            "# Meta Analysis Result Export",
            "",
            "This export is generated from one Meta statistics v2 run for internal testing and review.",
            "It is not production-grade statistical software and does not contain medical conclusions.",
            "",
            "## Provenance",
            "",
            f"- analysis_run_id: {run_id}",
            f"- analysis_result_id: {result.get('analysis_result_id', '')}",
            f"- source_statistics_result_hash: {context['statistics_result_hash']}",
            f"- source_statistics_result_path: {context['statistics_result_relative_path']}",
            "",
            "## Result Summary",
            "",
            f"- effect_measure: {result.get('effect_measure', '')}",
            f"- model: {result.get('model', '')}",
            f"- pooled_effect: {result.get('pooled_effect', '')}",
            f"- 95% CI: {result.get('ci_low', '')} to {result.get('ci_high', '')}",
            f"- p_value: {result.get('p_value', '')}",
            f"- i_squared: {result.get('i_squared', '')}",
            f"- tau_squared: {result.get('tau_squared', '')}",
            "",
            "## Warnings",
            "",
        ]
        warnings = [str(item) for item in diagnostics.get("warnings", []) if item]
        lines.extend([f"- {item}" for item in warnings] or ["- none"])
        lines.extend(
            [
                "",
                "## Limitations",
                "",
                "- Developer Preview / testing-level output.",
                "- No clinical diagnosis, prognosis, treatment recommendation, or production-grade conclusion is generated.",
            ]
        )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return self._register_artifact(
            context,
            artifact_type="report_export",
            path=output_path,
            format="markdown",
            status="available",
        )

    def discover_contracts(self, project_dir: Path) -> list[dict[str, Any]]:
        root = project_dir.expanduser().resolve() / "analysis" / "meta_result_contracts"
        contracts: list[dict[str, Any]] = []
        for path in sorted(root.glob("*/meta_result_contract.json")):
            payload = _load_json(path)
            if payload:
                contracts.append(payload)
        return contracts

    def _load_context(self, project_dir: Path, analysis_run_id: str | None) -> dict[str, Any]:
        project_dir = project_dir.expanduser().resolve()
        run_id = analysis_run_id or _latest_run_id(self._statistics_service, project_dir)
        if not run_id:
            raise ValueError("meta_statistics_run_missing")
        result_path = self._statistics_service.results_dir(project_dir) / f"{run_id}_result.json"
        run_path = self._statistics_service.runs_dir(project_dir) / f"{run_id}.json"
        if not result_path.exists():
            raise ValueError("meta_statistics_result_missing")
        if not run_path.exists():
            raise ValueError("meta_statistics_run_manifest_missing")
        standardized = _load_json(result_path)
        if standardized.get("analysis_run_id") != run_id:
            raise ValueError("meta_statistics_result_run_id_mismatch")
        return {
            "project_dir": project_dir,
            "analysis_run_id": run_id,
            "run_path": run_path,
            "run_relative_path": _relative_path(project_dir, run_path),
            "statistics_result_path": result_path,
            "statistics_result_relative_path": _relative_path(project_dir, result_path),
            "statistics_result_hash": _sha256(result_path),
            "standardized_result": standardized,
        }

    def _base_contract(self, context: dict[str, Any], *, artifacts: list[dict[str, Any]]) -> dict[str, Any]:
        result = context["standardized_result"]
        return {
            "schema_version": META_RESULT_CONTRACT_SCHEMA_VERSION,
            "project_id": context["project_dir"].name,
            "analysis_run_id": context["analysis_run_id"],
            "analysis_result_id": str(result.get("analysis_result_id", "")),
            "statistics_run_manifest_path": context["run_relative_path"],
            "statistics_result_path": context["statistics_result_relative_path"],
            "statistics_result_hash": context["statistics_result_hash"],
            "source_statistics_result_hash": context["statistics_result_hash"],
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
            "testing_level": True,
            "production_grade": False,
            "medical_conclusion_status": "not_generated",
            "updated_at": now_utc(),
        }

    def _register_artifact(
        self,
        context: dict[str, Any],
        *,
        artifact_type: str,
        path: Path,
        format: str,
        status: str,
    ) -> dict[str, Any]:
        contract = self.build_contract(context["project_dir"], context["analysis_run_id"])
        rel_path = _relative_path(context["project_dir"], path)
        artifact = {
            "schema_version": META_RESULT_CONTRACT_ARTIFACT_SCHEMA_VERSION,
            "artifact_id": f"{artifact_type}-{context['analysis_run_id']}",
            "artifact_type": artifact_type,
            "path": rel_path,
            "format": format,
            "status": status,
            "source_analysis_run_id": context["analysis_run_id"],
            "source_statistics_result_path": context["statistics_result_relative_path"],
            "source_statistics_result_hash": context["statistics_result_hash"],
            "testing_level": True,
            "production_grade": False,
            "medical_conclusion_status": "not_generated",
            "created_at": now_utc(),
        }
        artifacts = [
            item
            for item in contract.get("artifacts", [])
            if isinstance(item, dict) and item.get("artifact_type") != artifact_type
        ]
        artifacts.append(artifact)
        _write_json(self.contract_path(context["project_dir"], context["analysis_run_id"]), self._base_contract(context, artifacts=artifacts))
        return artifact


def discover_meta_result_contracts(project_dir: Path) -> list[dict[str, Any]]:
    return MetaResultContractAdapter().discover_contracts(project_dir)


def _analysis_result_from_standardized(payload: dict[str, Any]) -> AnalysisResult:
    studies: list[StudyMetaAnalysisResult] = []
    for row in payload.get("study_results", []):
        if not isinstance(row, dict):
            continue
        studies.append(
            StudyMetaAnalysisResult(
                study_id=str(row.get("study_id", "")),
                record_id=str(row.get("record_id", "")),
                first_author=str(row.get("first_author", "")),
                year=_optional_int(row.get("year")),
                effect=float(row.get("effect", 0.0)),
                ci_lower=float(row.get("ci_low", 0.0)),
                ci_upper=float(row.get("ci_high", 0.0)),
                standard_error=float(row.get("standard_error", 0.0)),
                variance=float(row.get("variance", 0.0)),
                weight=float(row.get("weight", 0.0)),
                transformed_effect=float(row.get("transformed_effect", 0.0)),
                adjusted=bool(row.get("adjusted", False)),
                warnings=[str(item) for item in row.get("warnings", [])] if isinstance(row.get("warnings"), list) else [],
            )
        )
    return AnalysisResult(
        result_id=str(payload.get("analysis_result_id", "")),
        dataset_id=str(payload.get("source_confirmed_analysis_plan_id", "")),
        project_id=str(payload.get("project_id", "")),
        profile_type=str(payload.get("meta_type", "")),
        outcome_name=_outcome_name(payload),
        effect_measure=str(payload.get("effect_measure", "")),
        model=str(payload.get("model", "")),
        pooled_effect=float(payload.get("pooled_effect", 0.0)),
        ci_lower=float(payload.get("ci_low", 0.0)),
        ci_upper=float(payload.get("ci_high", 0.0)),
        p_value=float(payload.get("p_value", 0.0)),
        q_statistic=float(payload.get("heterogeneity_q", 0.0)),
        i_squared=float(payload.get("i_squared", 0.0)),
        tau_squared=float(payload.get("tau_squared", 0.0)),
        study_results=studies,
        warnings=[str(item) for item in payload.get("diagnostics", {}).get("warnings", [])]
        if isinstance(payload.get("diagnostics"), dict)
        else [],
        created_at=str(payload.get("created_at", "")),
    )


def _outcome_name(payload: dict[str, Any]) -> str:
    for row in payload.get("study_results", []):
        if isinstance(row, dict) and str(row.get("outcome_name", "")).strip():
            return str(row.get("outcome_name", ""))
    return ""


def _optional_int(value: Any) -> int | None:
    if value is None or not str(value).strip():
        return None
    return int(value)


def _latest_run_id(service: MetaStatisticsEngineService, project_dir: Path) -> str:
    manifest = _load_json(service.manifest_path(project_dir))
    return str(manifest.get("latest_analysis_run_id", ""))


def _result_table_fieldnames() -> list[str]:
    return [
        "row_type",
        "analysis_run_id",
        "study_id",
        "record_id",
        "first_author",
        "year",
        "effect",
        "ci_low",
        "ci_high",
        "standard_error",
        "weight",
        "model",
        "effect_measure",
    ]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_path(root: Path, path: Path) -> str:
    return str(path.relative_to(root.expanduser().resolve()))
