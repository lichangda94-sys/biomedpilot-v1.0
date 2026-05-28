from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


MATRIX_SCHEMA_VERSION = "biomedpilot.bioinformatics_release_connection_matrix.v1"
ACTION_SCHEMA_VERSION = "biomedpilot.bioinformatics_release_action_result.v1"


@dataclass(frozen=True)
class BioinformaticsConnectionRow:
    action_id: str
    ui_page: str
    button_label: str
    backend_capability: str
    branch_source: str
    expected_test: str

    def to_dict(self) -> dict[str, str]:
        return {
            "action_id": self.action_id,
            "ui_page": self.ui_page,
            "button_label": self.button_label,
            "backend_capability": self.backend_capability,
            "branch_source": self.branch_source,
            "expected_test": self.expected_test,
        }


CONNECTION_ROWS: tuple[BioinformaticsConnectionRow, ...] = (
    BioinformaticsConnectionRow(
        "formal_deg_gate_run_review_report",
        "Analysis Tasks -> Formal DEG",
        "Formal DEG gate/run/review",
        "parameter confirmation, dependency detection, controlled DEG runner, result review, plot gate, report-ready gate",
        "dev/bioinformatics + dev/release-internal-test",
        "click writes action artifact; calls DEG services; either registers formal result artifacts or records explicit disabled_reason",
    ),
    BioinformaticsConnectionRow(
        "ora_gate_run_review_report",
        "Analysis Tasks -> Enrichment",
        "ORA gate/run/review",
        "ORA input gate, gene set gate, Python/R-capability dependency snapshot, controlled ORA execution, review, plot/report gate",
        "dev/release-internal-test",
        "click writes action artifact; calls ORA services; table/plot/report artifacts or disabled_reason",
    ),
    BioinformaticsConnectionRow(
        "gsea_gate_run_review_report",
        "Analysis Tasks -> Enrichment",
        "GSEA gate/run/review",
        "GSEA preranked input gate, gene set gate, backend dependency snapshot, controlled preranked GSEA, review, plot/report gate",
        "dev/release-internal-test",
        "click writes action artifact; calls GSEA services; table/plot/report artifacts or disabled_reason",
    ),
    BioinformaticsConnectionRow(
        "km_logrank_run_review_report",
        "Analysis Tasks -> Survival/clinical",
        "KM log-rank run/review",
        "survival clinical input resolver, outcome gate, KM parameter/confirmation gate, log-rank runner, review, plot/report gate",
        "dev/bioinformatics + dev/release-internal-test",
        "click writes action artifact; calls KM services; curve/logrank artifacts or disabled_reason",
    ),
    BioinformaticsConnectionRow(
        "cox_run_review_report",
        "Analysis Tasks -> Survival/clinical",
        "Cox run/review",
        "survival clinical input resolver, Cox parameter/confirmation gate, Cox runner, review, plot/report gate",
        "dev/bioinformatics + dev/release-internal-test",
        "click writes action artifact; calls Cox services; cox table/report artifacts or disabled_reason",
    ),
    BioinformaticsConnectionRow(
        "risk_score_run_review_report",
        "Analysis Tasks -> Survival/clinical",
        "Risk score run/review",
        "risk score contract gate, parameter confirmation, runner, review, plot/report gate",
        "dev/release-internal-test",
        "click writes action artifact; calls risk-score services; risk table/report artifacts or disabled_reason",
    ),
    BioinformaticsConnectionRow(
        "legacy_acquisition_bridge",
        "Data Source/Data Check -> Legacy bridge",
        "Legacy acquisition bridge",
        "legacy acquisition manifest adapter and standardized asset candidate bridge",
        "dev/bioinformatics + dev/release-internal-test",
        "click writes legacy acquisition/candidate artifacts or disabled_reason",
    ),
    BioinformaticsConnectionRow(
        "legacy_materialize_merge_select",
        "Data Check -> Legacy bridge",
        "Materialize/merge/select assets",
        "candidate materialization, repository merge, asset selection manifest application",
        "dev/bioinformatics + dev/release-internal-test",
        "click writes materialization/merge/selection artifacts or disabled_reason",
    ),
)


def build_bioinformatics_connection_matrix() -> dict[str, Any]:
    return {
        "schema_version": MATRIX_SCHEMA_VERSION,
        "rows": [row.to_dict() for row in CONNECTION_ROWS],
    }


def write_bioinformatics_connection_matrix(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    payload = build_bioinformatics_connection_matrix()
    path = root / "manifests" / "bioinformatics_release_connection_matrix.json"
    _write_json(path, payload)
    payload["matrix_path"] = str(path)
    return payload


def execute_bioinformatics_release_action(project_root: str | Path, action_id: str) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    if action_id not in {row.action_id for row in CONNECTION_ROWS}:
        raise ValueError(f"Unknown bioinformatics release action: {action_id}")
    write_bioinformatics_connection_matrix(root)
    handlers: dict[str, Callable[[Path], dict[str, Any]]] = {
        "formal_deg_gate_run_review_report": _formal_deg_gate_run_review_report,
        "ora_gate_run_review_report": _ora_gate_run_review_report,
        "gsea_gate_run_review_report": _gsea_gate_run_review_report,
        "km_logrank_run_review_report": _km_logrank_run_review_report,
        "cox_run_review_report": _cox_run_review_report,
        "risk_score_run_review_report": _risk_score_run_review_report,
        "legacy_acquisition_bridge": _legacy_acquisition_bridge,
        "legacy_materialize_merge_select": _legacy_materialize_merge_select,
    }
    raw = handlers[action_id](root)
    payload = _normalize_action_payload(action_id, raw)
    artifact_path = _write_action_artifact(root, action_id, payload)
    payload["action_artifact_path"] = str(artifact_path)
    return payload


def _formal_deg_gate_run_review_report(root: Path) -> dict[str, Any]:
    services: list[str] = []
    from app.bioinformatics.deg_engine.dependency_check import check_deg_backend_dependencies
    from app.bioinformatics.deg_engine.formal_runner import run_formal_controlled_deg
    from app.bioinformatics.deg_engine.result_review import build_formal_deg_result_review
    from app.bioinformatics.plots.formal_deg import build_formal_deg_plot_gate, create_formal_deg_plot_artifact
    from app.bioinformatics.reports.formal_deg import evaluate_formal_deg_report_ready_gate

    dependency = check_deg_backend_dependencies()
    services.append("check_deg_backend_dependencies")
    r_backend_capability = _formal_deg_r_backend_capability()
    services.append("build_formal_deg_r_backend_capability")
    run = run_formal_controlled_deg(root, dependency_snapshot=dependency)
    services.append("run_formal_controlled_deg")
    review = build_formal_deg_result_review(root, result_id=str(run.get("result_id") or "") or None)
    services.append("build_formal_deg_result_review")
    plot_gate = build_formal_deg_plot_gate(root, result_id=str(run.get("result_id") or "") or None)
    services.append("build_formal_deg_plot_gate")
    plot: dict[str, Any] = {"status": "blocked", "blockers": ["formal_deg_result_missing"]}
    if plot_gate.get("status") == "passed":
        plot = create_formal_deg_plot_artifact(root, result_id=str(run.get("result_id") or ""))
        services.append("create_formal_deg_plot_artifact")
    report_gate = evaluate_formal_deg_report_ready_gate(root, result_id=str(run.get("result_id") or "") or None, allow_table_only_report=True)
    services.append("evaluate_formal_deg_report_ready_gate")
    return {
        "services_called": services,
        "backend_results": {"dependency": dependency, "r_backend_capability": r_backend_capability, "run": run, "review": review, "plot_gate": plot_gate, "plot": plot, "report_gate": report_gate},
        "artifact_paths": _paths_from_payload(run, plot, report_gate),
        "blockers": _collect_blockers(r_backend_capability, run, review, plot_gate, plot, report_gate),
    }


def _ora_gate_run_review_report(root: Path) -> dict[str, Any]:
    services: list[str] = []
    from app.bioinformatics.enrichment import build_ora_result_review, run_controlled_ora
    from app.bioinformatics.plots.ora import build_ora_plot_gate, create_ora_plot_artifact
    from app.bioinformatics.reports.ora import evaluate_ora_report_ready_gate

    r_backend_capability = _enrichment_r_backend_capability(required_packages=("clusterProfiler", "fgsea", "DOSE", "enrichplot", "ggplot2"))
    services.append("detect_enrichment_r_backend_capability")
    run = run_controlled_ora(root, min_gene_set_size=1)
    services.append("run_controlled_ora")
    review = build_ora_result_review(root, result_id=str(run.get("result_id") or "") or None)
    services.append("build_ora_result_review")
    plot_gate = build_ora_plot_gate(root, result_id=str(run.get("result_id") or "") or None)
    services.append("build_ora_plot_gate")
    plot: dict[str, Any] = {"status": "blocked", "blockers": ["ora_result_missing"]}
    if plot_gate.get("status") == "passed":
        plot = create_ora_plot_artifact(root, result_id=str(run.get("result_id") or ""))
        services.append("create_ora_plot_artifact")
    report_gate = evaluate_ora_report_ready_gate(root, result_id=str(run.get("result_id") or "") or None, allow_table_only_report=True)
    services.append("evaluate_ora_report_ready_gate")
    return {"services_called": services, "backend_results": {"r_backend_capability": r_backend_capability, "run": run, "review": review, "plot_gate": plot_gate, "plot": plot, "report_gate": report_gate}, "artifact_paths": _paths_from_payload(run, plot, report_gate), "blockers": _collect_blockers(r_backend_capability, run, review, plot_gate, plot, report_gate)}


def _gsea_gate_run_review_report(root: Path) -> dict[str, Any]:
    services: list[str] = []
    from app.bioinformatics.gsea import build_gsea_result_review, run_controlled_preranked_gsea
    from app.bioinformatics.plots.gsea import build_gsea_plot_gate, create_gsea_plot_artifact
    from app.bioinformatics.reports.gsea import evaluate_gsea_report_ready_gate

    r_backend_capability = _enrichment_r_backend_capability(required_packages=("fgsea", "clusterProfiler", "enrichplot", "ggplot2"))
    services.append("detect_enrichment_r_backend_capability")
    run = run_controlled_preranked_gsea(root, min_gene_set_size=1, max_gene_set_size=500, permutation_count=10)
    services.append("run_controlled_preranked_gsea")
    review = build_gsea_result_review(root, result_id=str(run.get("result_id") or "") or None)
    services.append("build_gsea_result_review")
    plot_gate = build_gsea_plot_gate(root, result_id=str(run.get("result_id") or "") or None)
    services.append("build_gsea_plot_gate")
    plot: dict[str, Any] = {"status": "blocked", "blockers": ["gsea_result_missing"]}
    if plot_gate.get("status") == "passed":
        plot = create_gsea_plot_artifact(root, result_id=str(run.get("result_id") or ""))
        services.append("create_gsea_plot_artifact")
    report_gate = evaluate_gsea_report_ready_gate(root, result_id=str(run.get("result_id") or "") or None, allow_table_only_report=True)
    services.append("evaluate_gsea_report_ready_gate")
    return {"services_called": services, "backend_results": {"r_backend_capability": r_backend_capability, "run": run, "review": review, "plot_gate": plot_gate, "plot": plot, "report_gate": report_gate}, "artifact_paths": _paths_from_payload(run, plot, report_gate), "blockers": _collect_blockers(r_backend_capability, run, review, plot_gate, plot, report_gate)}


def _km_logrank_run_review_report(root: Path) -> dict[str, Any]:
    services: list[str] = []
    from app.bioinformatics.reports.survival_clinical import evaluate_km_logrank_report_ready_gate
    from app.bioinformatics.survival_clinical import build_km_result_review, build_km_logrank_parameter_manifest, build_survival_outcome_gate, confirm_km_logrank_parameters, resolve_survival_clinical_inputs, run_controlled_km_logrank

    inputs = resolve_survival_clinical_inputs(root)
    services.append("resolve_survival_clinical_inputs")
    outcome = build_survival_outcome_gate(root, inputs)
    services.append("build_survival_outcome_gate")
    dependency = _connection_dependency_snapshot("python_builtin_survival")
    parameter = build_km_logrank_parameter_manifest(inputs, outcome_gate=outcome, dependency_snapshot=dependency)
    services.append("build_km_logrank_parameter_manifest")
    confirmation = confirm_km_logrank_parameters(root, parameter, confirmed_by_user=True)
    services.append("confirm_km_logrank_parameters")
    run = run_controlled_km_logrank(root, parameter, confirmation)
    services.append("run_controlled_km_logrank")
    review = build_km_result_review(root, result_id=str(run.get("result_id") or "") or None)
    services.append("build_km_result_review")
    report_gate = evaluate_km_logrank_report_ready_gate(root, result_id=str(run.get("result_id") or "") or None)
    services.append("evaluate_km_logrank_report_ready_gate")
    return {"services_called": services, "backend_results": {"inputs": inputs, "outcome": outcome, "parameter": parameter, "confirmation": confirmation, "run": run, "review": review, "report_gate": report_gate}, "artifact_paths": _paths_from_payload(run, report_gate), "blockers": _collect_blockers(inputs, outcome, parameter, confirmation, run, review, report_gate)}


def _cox_run_review_report(root: Path) -> dict[str, Any]:
    services: list[str] = []
    from app.bioinformatics.reports.survival_clinical import evaluate_cox_report_ready_gate
    from app.bioinformatics.survival_clinical import build_cox_result_review, build_cox_univariate_parameter_manifest, build_survival_outcome_gate, confirm_cox_univariate_parameters, resolve_survival_clinical_inputs, run_controlled_cox_univariate

    inputs = resolve_survival_clinical_inputs(root)
    services.append("resolve_survival_clinical_inputs")
    outcome = build_survival_outcome_gate(root, inputs)
    services.append("build_survival_outcome_gate")
    dependency = _connection_dependency_snapshot("python_builtin_survival")
    parameter = build_cox_univariate_parameter_manifest(inputs, outcome_gate=outcome, dependency_snapshot=dependency)
    services.append("build_cox_univariate_parameter_manifest")
    confirmation = confirm_cox_univariate_parameters(root, parameter, confirmed_by_user=True)
    services.append("confirm_cox_univariate_parameters")
    run = run_controlled_cox_univariate(root, parameter, confirmation)
    services.append("run_controlled_cox_univariate")
    review = build_cox_result_review(root, result_id=str(run.get("result_id") or "") or None)
    services.append("build_cox_result_review")
    report_gate = evaluate_cox_report_ready_gate(root, result_id=str(run.get("result_id") or "") or None)
    services.append("evaluate_cox_report_ready_gate")
    return {"services_called": services, "backend_results": {"inputs": inputs, "outcome": outcome, "parameter": parameter, "confirmation": confirmation, "run": run, "review": review, "report_gate": report_gate}, "artifact_paths": _paths_from_payload(run, report_gate), "blockers": _collect_blockers(inputs, outcome, parameter, confirmation, run, review, report_gate)}


def _risk_score_run_review_report(root: Path) -> dict[str, Any]:
    services: list[str] = []
    from app.bioinformatics.reports.survival_clinical import evaluate_risk_score_report_ready_gate
    from app.bioinformatics.survival_clinical import build_risk_score_nomogram_contract_gate, build_risk_score_result_review, confirm_risk_score_parameters, resolve_survival_clinical_inputs, run_controlled_risk_score

    inputs = resolve_survival_clinical_inputs(root)
    services.append("resolve_survival_clinical_inputs")
    clinical_audit = {
        "schema_version": "biomedpilot.release_connection_clinical_variable_audit.placeholder.v1",
        "status": "blocked",
        "clinical_variable_audit_id": "release-connection-missing-clinical-variable-audit",
        "available_variables": inputs.get("available_clinical_variables", []),
        "blockers": ["clinical_variable_audit_missing"],
    }
    contract = build_risk_score_nomogram_contract_gate(inputs, clinical_audit)
    services.append("build_risk_score_nomogram_contract_gate")
    confirmation = confirm_risk_score_parameters(root, contract, confirmed_by_user=True)
    services.append("confirm_risk_score_parameters")
    run = run_controlled_risk_score(root, contract, confirmation)
    services.append("run_controlled_risk_score")
    review = build_risk_score_result_review(root, result_id=str(run.get("result_id") or "") or None)
    services.append("build_risk_score_result_review")
    report_gate = evaluate_risk_score_report_ready_gate(root, result_id=str(run.get("result_id") or "") or None)
    services.append("evaluate_risk_score_report_ready_gate")
    return {"services_called": services, "backend_results": {"inputs": inputs, "clinical_audit": clinical_audit, "contract": contract, "confirmation": confirmation, "run": run, "review": review, "report_gate": report_gate}, "artifact_paths": _paths_from_payload(run, report_gate), "blockers": _collect_blockers(inputs, clinical_audit, contract, confirmation, run, review, report_gate)}


def _legacy_acquisition_bridge(root: Path) -> dict[str, Any]:
    services: list[str] = []
    from app.bioinformatics.acquisition_adapters import build_legacy_standardized_asset_candidates, write_legacy_standardized_asset_candidates

    candidates = build_legacy_standardized_asset_candidates(root)
    services.append("build_legacy_standardized_asset_candidates")
    written = write_legacy_standardized_asset_candidates(root)
    services.append("write_legacy_standardized_asset_candidates")
    return {"services_called": services, "backend_results": {"candidates": candidates, "written": written}, "artifact_paths": _paths_from_payload(written), "blockers": _collect_blockers(candidates, written)}


def _legacy_materialize_merge_select(root: Path) -> dict[str, Any]:
    services: list[str] = []
    from app.bioinformatics.acquisition_adapters import apply_legacy_asset_selection_to_repository_manifest, build_legacy_asset_selection_manifest, materialize_legacy_standardized_asset_candidates, merge_legacy_materialized_assets_into_repository_manifest

    materialized = materialize_legacy_standardized_asset_candidates(root)
    services.append("materialize_legacy_standardized_asset_candidates")
    merged = merge_legacy_materialized_assets_into_repository_manifest(root)
    services.append("merge_legacy_materialized_assets_into_repository_manifest")
    selection = build_legacy_asset_selection_manifest(root)
    services.append("build_legacy_asset_selection_manifest")
    applied = apply_legacy_asset_selection_to_repository_manifest(root, selection)
    services.append("apply_legacy_asset_selection_to_repository_manifest")
    return {"services_called": services, "backend_results": {"materialized": materialized, "merged": merged, "selection": selection, "applied": applied}, "artifact_paths": _paths_from_payload(materialized, merged, selection, applied), "blockers": _collect_blockers(materialized, merged, selection, applied)}


def _normalize_action_payload(action_id: str, raw: dict[str, Any]) -> dict[str, Any]:
    blockers = [str(item) for item in raw.get("blockers", []) or [] if str(item)]
    status = "blocked" if blockers else "passed"
    return {
        "schema_version": ACTION_SCHEMA_VERSION,
        "created_at": _now(),
        "action_id": action_id,
        "status": status,
        "services_called": list(raw.get("services_called", []) or []),
        "artifact_paths": list(dict.fromkeys(str(path) for path in raw.get("artifact_paths", []) or [] if str(path))),
        "disabled_reason": ";".join(blockers) if blockers else "",
        "blockers": blockers,
        "backend_results": raw.get("backend_results", {}),
    }


def _connection_dependency_snapshot(runtime: str) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.release_connection_dependency_snapshot.v1",
        "status": "passed",
        "runtime": runtime,
        "blockers": [],
        "warnings": [],
    }


def _formal_deg_r_backend_capability() -> dict[str, Any]:
    from app.bioinformatics.deg_engine.r_adapter_contract import build_r_deg_runtime_gate_matrix

    capabilities = _r_capability_snapshot(("limma", "DESeq2", "edgeR"))
    preflight = {
        "status": "blocked",
        "method": "limma",
        "method_family": "limma_linear_model",
        "blockers": ["formal_deg_multifactor_preflight_not_selected"],
        "warnings": [],
    }
    return build_r_deg_runtime_gate_matrix(preflight, external_capabilities=capabilities["external_capabilities"], dependency_snapshot=capabilities["dependency_snapshot"]) | {
        "schema_version": "biomedpilot.release_formal_deg_r_backend_capability.v1",
        "detect_first_only": True,
        "install_action": "none_detect_first_only",
        "capability_snapshot": capabilities,
    }


def _enrichment_r_backend_capability(*, required_packages: tuple[str, ...]) -> dict[str, Any]:
    snapshot = _r_capability_snapshot(required_packages)
    blockers: list[str] = []
    if not snapshot["rscript"]["available"]:
        blockers.append("r_enrichment_backend_rscript_missing")
    for package in required_packages:
        status = snapshot["packages"].get(package, {})
        if not status.get("available"):
            blockers.append(f"r_enrichment_backend_package_missing:{package}")
    return {
        "schema_version": "biomedpilot.release_enrichment_r_backend_capability.v1",
        "status": "passed" if not blockers else "blocked",
        "required_packages": list(required_packages),
        "rscript": snapshot["rscript"],
        "packages": snapshot["packages"],
        "capabilities": {
            "ora_clusterprofiler_enricher": _package_available(snapshot, "clusterProfiler"),
            "gsea_preranked_fgsea": _package_available(snapshot, "fgsea"),
            "enrichment_plot_enrichplot": _package_available(snapshot, "enrichplot") and _package_available(snapshot, "ggplot2"),
        },
        "blockers": blockers,
        "warnings": [],
        "install_action": "none_detect_first_only",
        "packaging_policy": "external_r_runtime_not_bundled",
    }


def _r_capability_snapshot(packages: tuple[str, ...]) -> dict[str, Any]:
    rscript = shutil.which("Rscript") or ""
    rscript_status = {"available": bool(rscript), "path": rscript, "version": "", "missing_reason": "" if rscript else "Rscript_not_found_on_PATH"}
    package_status: dict[str, dict[str, Any]] = {package: {"available": False, "version": "", "missing_reason": "Rscript_not_found_on_PATH"} for package in packages}
    if rscript:
        rscript_status["version"] = _rscript_version(rscript)
        for package in packages:
            package_status[package] = _r_package_status(rscript, package)
    external_capabilities = {
        "runtime.r.available": {"available": rscript_status["available"], "path": rscript_status["path"], "version": rscript_status["version"], "missing_reason": rscript_status["missing_reason"]},
        "runtime.bioconductor.available": package_status.get("BiocManager", {"available": False, "version": "", "missing_reason": "BiocManager_not_checked"}),
        "package.r.limma.available": package_status.get("limma", {"available": False, "version": "", "missing_reason": "limma_not_checked"}),
        "package.r.deseq2.available": package_status.get("DESeq2", {"available": False, "version": "", "missing_reason": "DESeq2_not_checked"}),
        "package.r.edger.available": package_status.get("edgeR", {"available": False, "version": "", "missing_reason": "edgeR_not_checked"}),
    }
    blockers = []
    if not rscript_status["available"]:
        blockers.append("Rscript_not_found_on_PATH")
    blockers.extend(f"r_package_not_available:{name}" for name, status in package_status.items() if not status.get("available"))
    return {
        "schema_version": "biomedpilot.release_r_capability_snapshot.v1",
        "status": "passed" if not blockers else "blocked",
        "rscript": rscript_status,
        "packages": package_status,
        "external_capabilities": external_capabilities,
        "dependency_snapshot": {
            "status": "passed" if not blockers else "blocked",
            "runtime": "system_rscript_detect_only",
            "dependencies": {"R": rscript_status, **package_status},
            "blockers": blockers,
            "warnings": [],
        },
        "blockers": blockers,
        "warnings": [],
    }


def _rscript_version(rscript: str) -> str:
    try:
        result = subprocess.run([rscript, "--version"], check=False, capture_output=True, text=True, timeout=5)
    except Exception as exc:  # pragma: no cover - depends on local R install.
        return f"{exc.__class__.__name__}: {exc}"
    return (result.stdout or result.stderr).strip().splitlines()[0] if (result.stdout or result.stderr).strip() else ""


def _r_package_status(rscript: str, package: str) -> dict[str, Any]:
    script = f"if (!requireNamespace('{package}', quietly=TRUE)) quit(status=2); cat(as.character(utils::packageVersion('{package}')))"
    try:
        result = subprocess.run([rscript, "-e", script], check=False, capture_output=True, text=True, timeout=10)
    except Exception as exc:  # pragma: no cover - depends on local R install.
        return {"available": False, "version": "", "missing_reason": f"{exc.__class__.__name__}: {exc}"}
    version = result.stdout.strip()
    return {
        "available": result.returncode == 0,
        "version": version if result.returncode == 0 else "",
        "missing_reason": "" if result.returncode == 0 else (result.stderr.strip() or f"{package}_not_available"),
    }


def _package_available(snapshot: dict[str, Any], package: str) -> bool:
    status = snapshot.get("packages", {}).get(package, {})
    return bool(isinstance(status, dict) and status.get("available"))


def _collect_blockers(*payloads: Any) -> list[str]:
    blockers: list[str] = []
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("status") or "")
        if status in {"blocked", "failed"}:
            blockers.append(str(payload.get("failure_reason") or status))
        blockers.extend(str(item) for item in payload.get("blockers", []) or [] if str(item))
    return list(dict.fromkeys(blockers))


def _paths_from_payload(*payloads: Any) -> list[str]:
    paths: list[str] = []
    keys = {
        "result_table_path",
        "km_curve_table",
        "logrank_result_table",
        "cox_result_table",
        "risk_score_result_table",
        "task_run_log_path",
        "export_path",
        "package_path",
        "user_visible_package_path",
        "matrix_path",
        "manifest_path",
        "candidate_manifest_path",
        "materialization_manifest_path",
        "repository_manifest_path",
        "selection_manifest_path",
    }
    for payload in payloads:
        if isinstance(payload, dict):
            for key, value in payload.items():
                if key in keys and value:
                    paths.append(str(value))
            for value in payload.values():
                if isinstance(value, dict):
                    paths.extend(_paths_from_payload(value))
                elif isinstance(value, list):
                    for item in value:
                        paths.extend(_paths_from_payload(item))
    return paths


def _write_action_artifact(root: Path, action_id: str, payload: dict[str, Any]) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    path = root / "analysis" / "connection_runs" / f"{action_id}_{stamp}.json"
    _write_json(path, payload)
    latest = root / "analysis" / "connection_runs" / f"{action_id}_latest.json"
    _write_json(latest, payload | {"action_artifact_path": str(path)})
    return path


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
