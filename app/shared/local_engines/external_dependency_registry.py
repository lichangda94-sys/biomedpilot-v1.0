from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from app.shared.local_engines.engine_status import utc_now
from app.shared.storage import default_storage_root


CAPABILITY_STATUS_AVAILABLE = "available"
CAPABILITY_STATUS_MISSING = "missing"
CAPABILITY_STATUS_BLOCKED = "blocked"
CAPABILITY_STATUS_UNKNOWN = "unknown"
CAPABILITY_STATUS_INCOMPATIBLE = "incompatible"

ENGINE_STATUS_AVAILABLE = "available"
ENGINE_STATUS_PARTIALLY_AVAILABLE = "partially_available"
ENGINE_STATUS_MISSING = "missing"
ENGINE_STATUS_ERROR = "error"

R_BIOCONDUCTOR_ENGINE_FAMILY = "r_bioconductor"
PYTHON_STATISTICAL_ENGINE_FAMILY = "python_statistical"
REPORT_RENDERER_ENGINE_FAMILY = "report_renderer"

R_BIOCONDUCTOR_SNAPSHOT_FILENAME = "r_bioconductor_snapshot.json"
R_RUNTIME_SNAPSHOT_FILENAME = "r_runtime_snapshot.json"
R_ENRICHMENT_BACKEND_DETECTION_FILENAME = "r_enrichment_backend_detection.json"
R_ENRICHMENT_ORA_FIXTURE_FILENAME = "r_enrichment_ora_fixture.tsv"
R_ENRICHMENT_GSEA_FIXTURE_FILENAME = "r_enrichment_gsea_fixture.tsv"
PYTHON_STATISTICAL_SNAPSHOT_FILENAME = "python_statistical_snapshot.json"
REPORT_RENDERER_SNAPSHOT_FILENAME = "report_renderer_snapshot.json"
CAPABILITY_REGISTRY_SNAPSHOT_FILENAME = "capability_registry_snapshot.json"

R_ENRICHMENT_BACKEND_DETECTION_SCHEMA_VERSION = "biomedpilot.external_enrichment_r_backend_detection.v1"

CommandFinder = Callable[[str], str | None]
SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]
ModuleChecker = Callable[[str], bool]
DistributionVersionReader = Callable[[str], str | None]


@dataclass(frozen=True)
class PackageRequirement:
    name: str
    capability_key: str
    required_for: tuple[str, ...]
    import_name: str = ""
    minimum_version: str = ""


R_PACKAGE_REQUIREMENTS: tuple[PackageRequirement, ...] = (
    PackageRequirement("BiocManager", "runtime.bioconductor.available", ("bioconductor_runtime",)),
    PackageRequirement("limma", "package.r.limma.available", ("deg_limma",)),
    PackageRequirement("DESeq2", "package.r.deseq2.available", ("deg_deseq2",)),
    PackageRequirement("edgeR", "package.r.edger.available", ("deg_edger",)),
    PackageRequirement("survival", "package.r.survival.available", ("survival_runtime", "cox_runtime", "km_runtime")),
    PackageRequirement("glmnet", "package.r.glmnet.available", ("penalized_regression_runtime",)),
    PackageRequirement("ggplot2", "package.r.ggplot2.available", ("r_plot_runtime",)),
    PackageRequirement("survminer", "package.r.survminer.available", ("survival_plot_runtime",)),
)

R_ENRICHMENT_REQUIRED_PACKAGES: tuple[str, ...] = (
    "clusterProfiler",
    "fgsea",
    "DOSE",
    "enrichplot",
    "ggplot2",
    "AnnotationDbi",
    "org.Hs.eg.db",
    "ReactomePA",
    "msigdbr",
)

R_ENRICHMENT_OPTIONAL_PACKAGES: tuple[str, ...] = (
    "pathview",
    "GO.db",
    "KEGGREST",
)

R_ENRICHMENT_CAPABILITY_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "ora_enricher": ("clusterProfiler",),
    "ora_go": ("clusterProfiler", "AnnotationDbi", "org.Hs.eg.db"),
    "ora_kegg": ("clusterProfiler", "KEGGREST"),
    "ora_reactome": ("ReactomePA",),
    "gsea_preranked_fgsea": ("fgsea",),
    "gsea_preranked_clusterprofiler": ("clusterProfiler",),
    "enrichment_plot_dotplot": ("enrichplot", "ggplot2"),
    "enrichment_plot_barplot": ("enrichplot", "ggplot2"),
    "gsea_plot_curve": ("enrichplot", "ggplot2", "clusterProfiler"),
}

R_ENRICHMENT_ORA_COLUMNS: tuple[str, ...] = (
    "ID",
    "Description",
    "GeneRatio",
    "BgRatio",
    "pvalue",
    "p.adjust",
    "qvalue",
    "geneID",
    "Count",
)

R_ENRICHMENT_GSEA_COLUMNS: tuple[str, ...] = (
    "pathway",
    "ES",
    "NES",
    "pval",
    "padj",
    "leadingEdge",
    "size",
)

PYTHON_PACKAGE_REQUIREMENTS: tuple[PackageRequirement, ...] = (
    PackageRequirement("scipy", "package.python.scipy.available", ("controlled_deg_python_runtime",), "scipy"),
    PackageRequirement("statsmodels", "package.python.statsmodels.available", ("controlled_deg_python_runtime",), "statsmodels"),
    PackageRequirement("lifelines", "package.python.lifelines.available", ("survival_runtime", "cox_runtime", "km_runtime"), "lifelines"),
    PackageRequirement("scikit-survival", "package.python.scikit_survival.available", ("survival_runtime",), "sksurv"),
    PackageRequirement("matplotlib", "package.python.matplotlib.available", ("real_plot_renderer",), "matplotlib"),
)

RENDERER_REQUIREMENTS: tuple[PackageRequirement, ...] = (
    PackageRequirement("pandoc", "renderer.pandoc.available", ("export_docx", "export_pdf_full")),
    PackageRequirement("quarto", "renderer.quarto.available", ("export_html_full", "export_pdf_full")),
    PackageRequirement("LaTeX", "renderer.latex.available", ("export_pdf_full",), "latex"),
    PackageRequirement("wkhtmltopdf", "renderer.wkhtmltopdf.available", ("export_pdf_html_renderer",)),
)


def external_engines_storage_root(storage_root: str | Path | None = None) -> Path:
    root = Path(storage_root) if storage_root is not None else default_storage_root()
    return root / "external_engines"


def detect_all_external_dependencies(
    *,
    storage_root: str | Path | None = None,
    command_finder: CommandFinder = shutil.which,
    runner: SubprocessRunner = subprocess.run,
    module_checker: ModuleChecker | None = None,
    distribution_version_reader: DistributionVersionReader | None = None,
    write_snapshots: bool = True,
) -> "ExternalEngineRegistry":
    r_snapshot = detect_r_bioconductor_dependencies(
        storage_root=storage_root,
        command_finder=command_finder,
        runner=runner,
        write_snapshot=write_snapshots,
    )
    python_snapshot = detect_python_statistical_dependencies(
        storage_root=storage_root,
        module_checker=module_checker,
        distribution_version_reader=distribution_version_reader,
        write_snapshot=write_snapshots,
    )
    renderer_snapshot = detect_report_renderer_dependencies(
        storage_root=storage_root,
        command_finder=command_finder,
        runner=runner,
        write_snapshot=write_snapshots,
    )
    registry = ExternalEngineRegistry((r_snapshot, python_snapshot, renderer_snapshot), storage_root=storage_root)
    if write_snapshots:
        registry.write_registry_snapshot()
    return registry


def detect_r_bioconductor_dependencies(
    *,
    storage_root: str | Path | None = None,
    command_finder: CommandFinder = shutil.which,
    runner: SubprocessRunner = subprocess.run,
    rscript_path: str | Path | None = None,
    write_snapshot: bool = True,
) -> dict[str, Any]:
    checked_at = utc_now()
    snapshot_dir = external_engines_storage_root(storage_root)
    snapshot_path = snapshot_dir / R_BIOCONDUCTOR_SNAPSHOT_FILENAME
    r_runtime_snapshot_path = snapshot_dir / R_RUNTIME_SNAPSHOT_FILENAME
    resolved_rscript = str(rscript_path) if rscript_path else (command_finder("Rscript") or "")
    architecture = platform.machine() or "unknown"
    blockers: list[dict[str, Any]] = []
    packages: list[dict[str, Any]] = []
    version = ""

    if not resolved_rscript:
        blockers.append(_blocker("missing_r_runtime", "Rscript is not available", required_by=("runtime.r.available",)))
        packages = [_blocked_package(requirement, "missing_r_runtime", "Rscript is not available") for requirement in R_PACKAGE_REQUIREMENTS]
        snapshot = _snapshot(
            engine_family=R_BIOCONDUCTOR_ENGINE_FAMILY,
            engine_name="R / Bioconductor",
            status=ENGINE_STATUS_MISSING,
            runtime_path="",
            version="",
            architecture=architecture,
            checked_at=checked_at,
            snapshot_path=snapshot_path,
            packages=packages,
            blockers=blockers,
            install_guidance=_r_install_guidance(),
        )
        _write_optional_snapshot(snapshot, snapshot_path, write_snapshot)
        _write_optional_snapshot(_r_runtime_snapshot_from(snapshot), r_runtime_snapshot_path, write_snapshot)
        return snapshot

    runtime_result = _run_checked(
        runner,
        [resolved_rscript, "-e", "cat(paste(R.version.string, R.version$arch, sep='\\n'))"],
        timeout=12,
    )
    if runtime_result["returncode"] != 0:
        message = runtime_result["stderr"] or runtime_result["stdout"] or "Rscript smoke execution failed"
        blockers.append(_blocker("r_runtime_error", message, required_by=("runtime.r.available",)))
        packages = [_blocked_package(requirement, "r_runtime_error", message) for requirement in R_PACKAGE_REQUIREMENTS]
        snapshot = _snapshot(
            engine_family=R_BIOCONDUCTOR_ENGINE_FAMILY,
            engine_name="R / Bioconductor",
            status=ENGINE_STATUS_ERROR,
            runtime_path=resolved_rscript,
            version=version,
            architecture=architecture,
            checked_at=checked_at,
            snapshot_path=snapshot_path,
            packages=packages,
            blockers=blockers,
            install_guidance=_r_install_guidance(),
        )
        _write_optional_snapshot(snapshot, snapshot_path, write_snapshot)
        _write_optional_snapshot(_r_runtime_snapshot_from(snapshot), r_runtime_snapshot_path, write_snapshot)
        return snapshot

    runtime_lines = [line.strip() for line in runtime_result["stdout"].splitlines() if line.strip()]
    version = runtime_lines[0] if runtime_lines else "R version unknown"
    architecture = runtime_lines[1] if len(runtime_lines) > 1 and runtime_lines[1] else architecture
    installed_versions = _detect_r_package_versions(resolved_rscript, runner)
    for requirement in R_PACKAGE_REQUIREMENTS:
        package_version = installed_versions.get(requirement.name)
        if package_version:
            packages.append(_available_package(requirement, package_version))
        else:
            blocker = _blocker(
                "missing_r_package",
                f"{requirement.name} is not installed",
                package=requirement.name,
                required_by=requirement.required_for,
            )
            blockers.append(blocker)
            packages.append(_missing_package(requirement, blocker))

    status = ENGINE_STATUS_AVAILABLE if not blockers else ENGINE_STATUS_PARTIALLY_AVAILABLE
    snapshot = _snapshot(
        engine_family=R_BIOCONDUCTOR_ENGINE_FAMILY,
        engine_name="R / Bioconductor",
        status=status,
        runtime_path=resolved_rscript,
        version=version,
        architecture=architecture,
        checked_at=checked_at,
        snapshot_path=snapshot_path,
        packages=packages,
        blockers=blockers,
        install_guidance=_r_install_guidance(),
    )
    _write_optional_snapshot(snapshot, snapshot_path, write_snapshot)
    _write_optional_snapshot(_r_runtime_snapshot_from(snapshot), r_runtime_snapshot_path, write_snapshot)
    return snapshot


def detect_external_enrichment_r_backend(
    *,
    storage_root: str | Path | None = None,
    command_finder: CommandFinder = shutil.which,
    runner: SubprocessRunner = subprocess.run,
    rscript_path: str | Path | None = None,
    write_snapshot: bool = True,
) -> dict[str, Any]:
    created_at = utc_now()
    snapshot_path = external_engines_storage_root(storage_root) / R_ENRICHMENT_BACKEND_DETECTION_FILENAME
    resolved_rscript = str(rscript_path) if rscript_path else (command_finder("Rscript") or "")
    rscript = {
        "available": bool(resolved_rscript),
        "path": resolved_rscript,
        "version": "",
        "architecture": "unknown",
        "library_paths": [],
    }
    package_names = R_ENRICHMENT_REQUIRED_PACKAGES + R_ENRICHMENT_OPTIONAL_PACKAGES
    package_statuses = {name: _r_enrichment_missing_package(name, "missing_r_runtime", "Rscript is not available") for name in package_names}
    blockers: list[dict[str, Any]] = []
    warnings: list[str] = []

    if not resolved_rscript:
        blockers.append(_blocker("missing_r_runtime", "Rscript is not available", required_by=("external_enrichment_r_backend",)))
        detection = _r_enrichment_detection_payload(
            created_at=created_at,
            rscript=rscript,
            package_statuses=package_statuses,
            blockers=blockers,
            warnings=warnings,
        )
        _write_optional_snapshot(detection, snapshot_path, write_snapshot)
        return detection

    runtime_result = _run_checked(
        runner,
        [resolved_rscript, "-e", "cat(R.version.string, '\\n'); cat(R.version$arch, '\\n'); cat(paste(.libPaths(), collapse='\\n'))"],
        timeout=12,
    )
    if runtime_result["returncode"] != 0:
        message = runtime_result["stderr"] or runtime_result["stdout"] or "Rscript runtime detection failed"
        rscript["available"] = False
        blockers.append(_blocker("r_runtime_error", message, required_by=("external_enrichment_r_backend",)))
        package_statuses = {name: _r_enrichment_missing_package(name, "r_runtime_error", message) for name in package_names}
        detection = _r_enrichment_detection_payload(
            created_at=created_at,
            rscript=rscript,
            package_statuses=package_statuses,
            blockers=blockers,
            warnings=warnings,
        )
        _write_optional_snapshot(detection, snapshot_path, write_snapshot)
        return detection

    runtime_lines = [line.strip() for line in runtime_result["stdout"].splitlines() if line.strip()]
    rscript["version"] = runtime_lines[0] if runtime_lines else "R version unknown"
    rscript["architecture"] = _normalize_r_arch(runtime_lines[1] if len(runtime_lines) > 1 else "")
    rscript["library_paths"] = runtime_lines[2:] if len(runtime_lines) > 2 else []

    package_statuses = _detect_r_enrichment_package_statuses(resolved_rscript, runner, package_names)
    for name in R_ENRICHMENT_REQUIRED_PACKAGES:
        status = package_statuses[name]
        if not status["available"] or not status["importable"]:
            blockers.append(
                _blocker(
                    "missing_required_r_package",
                    str(status.get("missing_reason") or f"{name} is not importable"),
                    package=name,
                    required_by=_r_enrichment_required_by(name),
                )
            )
    for name in R_ENRICHMENT_OPTIONAL_PACKAGES:
        status = package_statuses[name]
        if not status["available"] or not status["importable"]:
            warnings.append(f"optional_r_package_missing:{name}:{status.get('missing_reason') or 'not_importable'}")

    detection = _r_enrichment_detection_payload(
        created_at=created_at,
        rscript=rscript,
        package_statuses=package_statuses,
        blockers=blockers,
        warnings=warnings,
    )
    _write_optional_snapshot(detection, snapshot_path, write_snapshot)
    return detection


def run_external_enrichment_r_backend_validation(
    *,
    storage_root: str | Path | None = None,
    command_finder: CommandFinder = shutil.which,
    runner: SubprocessRunner = subprocess.run,
    rscript_path: str | Path | None = None,
    write_outputs: bool = True,
    timeout_seconds: int = 90,
) -> dict[str, Any]:
    output_root = external_engines_storage_root(storage_root)
    detection_path = output_root / R_ENRICHMENT_BACKEND_DETECTION_FILENAME
    ora_path = output_root / R_ENRICHMENT_ORA_FIXTURE_FILENAME
    gsea_path = output_root / R_ENRICHMENT_GSEA_FIXTURE_FILENAME
    detection = detect_external_enrichment_r_backend(
        storage_root=storage_root,
        command_finder=command_finder,
        runner=runner,
        rscript_path=rscript_path,
        write_snapshot=False,
    )
    detection["fixture_outputs"] = {
        "ora_fixture_tsv": "",
        "gsea_fixture_tsv": "",
    }
    detection["plot_smoke"] = []
    if detection["status"] != "passed" and not _can_run_r_enrichment_fixtures(detection):
        if write_outputs:
            _write_json(detection_path, detection)
        return detection

    resolved_rscript = str(detection["rscript"]["path"])
    output_root.mkdir(parents=True, exist_ok=True)
    fixture_result = _run_checked(
        runner,
        [resolved_rscript, "--vanilla", "-e", _r_enrichment_fixture_script(), str(ora_path), str(gsea_path)],
        timeout=timeout_seconds,
    )
    if fixture_result["returncode"] != 0:
        message = fixture_result["stderr"] or fixture_result["stdout"] or "R enrichment fixture execution failed"
        detection["status"] = "blocked"
        detection["blockers"].append(_blocker("r_enrichment_fixture_failed", message, required_by=("external_enrichment_r_backend_validation",)))
        if write_outputs:
            _write_json(detection_path, detection)
        return detection

    ora_gate = _validate_tsv_columns(ora_path, R_ENRICHMENT_ORA_COLUMNS)
    gsea_gate = _validate_tsv_columns(gsea_path, R_ENRICHMENT_GSEA_COLUMNS)
    detection["plot_smoke"] = _parse_plot_smoke(fixture_result["stdout"])
    detection["fixture_outputs"] = {
        "ora_fixture_tsv": str(ora_path) if ora_gate["status"] == "passed" else "",
        "gsea_fixture_tsv": str(gsea_path) if gsea_gate["status"] == "passed" else "",
    }
    detection["fixture_validation"] = {
        "ora": ora_gate,
        "gsea": gsea_gate,
    }
    fixture_blockers = [item for gate in (ora_gate, gsea_gate) for item in gate.get("blockers", [])]
    if fixture_blockers:
        detection["status"] = "blocked"
        detection["blockers"].extend(fixture_blockers)
    if write_outputs:
        _write_json(detection_path, detection)
    return detection


def detect_python_statistical_dependencies(
    *,
    storage_root: str | Path | None = None,
    module_checker: ModuleChecker | None = None,
    distribution_version_reader: DistributionVersionReader | None = None,
    write_snapshot: bool = True,
) -> dict[str, Any]:
    checked_at = utc_now()
    snapshot_path = external_engines_storage_root(storage_root) / PYTHON_STATISTICAL_SNAPSHOT_FILENAME
    module_checker = module_checker or _module_available
    distribution_version_reader = distribution_version_reader or _distribution_version
    blockers: list[dict[str, Any]] = []
    packages: list[dict[str, Any]] = []

    for requirement in PYTHON_PACKAGE_REQUIREMENTS:
        if module_checker(requirement.import_name or requirement.name):
            packages.append(_available_package(requirement, distribution_version_reader(requirement.name) or "unknown_version"))
        else:
            blocker = _blocker(
                "missing_python_package",
                f"{requirement.name} is not installed",
                package=requirement.name,
                required_by=requirement.required_for,
            )
            blockers.append(blocker)
            packages.append(_missing_package(requirement, blocker))

    snapshot = _snapshot(
        engine_family=PYTHON_STATISTICAL_ENGINE_FAMILY,
        engine_name="Python statistical runtime",
        status=ENGINE_STATUS_AVAILABLE if not blockers else ENGINE_STATUS_PARTIALLY_AVAILABLE,
        runtime_path=sys.executable,
        version=platform.python_version(),
        architecture=platform.machine() or "unknown",
        checked_at=checked_at,
        snapshot_path=snapshot_path,
        packages=packages,
        blockers=blockers,
        install_guidance=_python_install_guidance(),
    )
    _write_optional_snapshot(snapshot, snapshot_path, write_snapshot)
    return snapshot


def detect_report_renderer_dependencies(
    *,
    storage_root: str | Path | None = None,
    command_finder: CommandFinder = shutil.which,
    runner: SubprocessRunner = subprocess.run,
    write_snapshot: bool = True,
) -> dict[str, Any]:
    checked_at = utc_now()
    snapshot_path = external_engines_storage_root(storage_root) / REPORT_RENDERER_SNAPSHOT_FILENAME
    blockers: list[dict[str, Any]] = []
    packages: list[dict[str, Any]] = []
    for requirement in RENDERER_REQUIREMENTS:
        command_names = ("latexmk", "pdflatex", "xelatex") if requirement.capability_key == "renderer.latex.available" else (requirement.name,)
        command_path = next((path for name in command_names if (path := command_finder(name))), "")
        if command_path:
            packages.append(
                {
                    "name": requirement.name,
                    "required_for": list(requirement.required_for),
                    "status": CAPABILITY_STATUS_AVAILABLE,
                    "version": _command_version(command_path, runner),
                    "minimum_version": requirement.minimum_version,
                    "runtime_path": command_path,
                    "blocker": None,
                    "capability_key": requirement.capability_key,
                }
            )
        else:
            blocker = _blocker(
                "missing_renderer",
                f"{requirement.name} is not installed",
                package=requirement.name,
                required_by=requirement.required_for,
            )
            blockers.append(blocker)
            packages.append(_missing_package(requirement, blocker))
    snapshot = _snapshot(
        engine_family=REPORT_RENDERER_ENGINE_FAMILY,
        engine_name="Report renderer toolchain",
        status=ENGINE_STATUS_AVAILABLE if not blockers else ENGINE_STATUS_PARTIALLY_AVAILABLE,
        runtime_path="",
        version="",
        architecture=platform.machine() or "unknown",
        checked_at=checked_at,
        snapshot_path=snapshot_path,
        packages=packages,
        blockers=blockers,
        install_guidance=_renderer_install_guidance(),
    )
    snapshot["export_capabilities"] = {
        "markdown": {"status": CAPABILITY_STATUS_AVAILABLE, "blockers": []},
        "html": _export_capability(packages, required_keys=("renderer.quarto.available",)),
        "docx": _export_capability(packages, required_keys=("renderer.pandoc.available",)),
        "pdf": _export_capability(packages, required_keys=("renderer.pandoc.available", "renderer.latex.available")),
    }
    _write_optional_snapshot(snapshot, snapshot_path, write_snapshot)
    return snapshot


class ExternalEngineRegistry:
    def __init__(self, snapshots: Iterable[dict[str, Any]], *, storage_root: str | Path | None = None) -> None:
        self._snapshots = {str(snapshot.get("engine_family") or ""): dict(snapshot) for snapshot in snapshots if isinstance(snapshot, dict)}
        self._storage_root = storage_root
        self._capabilities = self._build_capabilities()

    @property
    def capabilities(self) -> dict[str, dict[str, Any]]:
        return {key: dict(value) for key, value in self._capabilities.items()}

    @property
    def snapshots(self) -> dict[str, dict[str, Any]]:
        return {key: dict(value) for key, value in self._snapshots.items()}

    def get_capability(self, capability_key: str) -> dict[str, Any]:
        capability = self._capabilities.get(capability_key)
        if capability is None:
            return {
                "capability_key": capability_key,
                "status": CAPABILITY_STATUS_UNKNOWN,
                "version": "",
                "runtime_path": "",
                "architecture": "",
                "checked_at": "",
                "snapshot_path": "",
                "blockers": [
                    _blocker(
                        "unknown_capability_key",
                        f"Unknown external engine capability: {capability_key}",
                        required_by=(capability_key,),
                    )
                ],
            }
        return dict(capability)

    def query_engine_family(self, engine_family: str) -> dict[str, Any] | None:
        snapshot = self._snapshots.get(engine_family)
        return dict(snapshot) if snapshot is not None else None

    def query_required_by(self, required_by: str) -> tuple[dict[str, Any], ...]:
        rows: list[dict[str, Any]] = []
        for capability in self._capabilities.values():
            if required_by in capability.get("required_for", []):
                rows.append(dict(capability))
                continue
            blockers = capability.get("blockers") if isinstance(capability.get("blockers"), list) else []
            if any(required_by in (blocker.get("required_by") or []) for blocker in blockers if isinstance(blocker, dict)):
                rows.append(dict(capability))
        return tuple(rows)

    def snapshot_lookup(self, engine_family: str) -> str:
        snapshot = self._snapshots.get(engine_family) or {}
        return str(snapshot.get("snapshot_path") or "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "biomedpilot_external_engine_capability_registry.v1",
            "checked_at": utc_now(),
            "capabilities": self.capabilities,
            "snapshots": self.snapshots,
        }

    def write_registry_snapshot(self) -> Path:
        path = external_engines_storage_root(self._storage_root) / CAPABILITY_REGISTRY_SNAPSHOT_FILENAME
        _write_json(path, self.to_dict())
        return path

    def _build_capabilities(self) -> dict[str, dict[str, Any]]:
        capabilities: dict[str, dict[str, Any]] = {}
        r_snapshot = self._snapshots.get(R_BIOCONDUCTOR_ENGINE_FAMILY)
        if r_snapshot is not None:
            capabilities["runtime.r.available"] = _runtime_capability("runtime.r.available", r_snapshot)
            for package in r_snapshot.get("packages", []):
                if isinstance(package, dict) and package.get("capability_key"):
                    capabilities[str(package["capability_key"])] = _package_capability(package, r_snapshot)
        python_snapshot = self._snapshots.get(PYTHON_STATISTICAL_ENGINE_FAMILY)
        if python_snapshot is not None:
            for package in python_snapshot.get("packages", []):
                if isinstance(package, dict) and package.get("capability_key"):
                    capabilities[str(package["capability_key"])] = _package_capability(package, python_snapshot)
        renderer_snapshot = self._snapshots.get(REPORT_RENDERER_ENGINE_FAMILY)
        if renderer_snapshot is not None:
            for package in renderer_snapshot.get("packages", []):
                if isinstance(package, dict) and package.get("capability_key"):
                    capabilities[str(package["capability_key"])] = _package_capability(package, renderer_snapshot)
        return capabilities


def load_external_engine_registry(storage_root: str | Path | None = None) -> ExternalEngineRegistry:
    root = external_engines_storage_root(storage_root)
    snapshots = []
    for filename in (R_BIOCONDUCTOR_SNAPSHOT_FILENAME, PYTHON_STATISTICAL_SNAPSHOT_FILENAME, REPORT_RENDERER_SNAPSHOT_FILENAME):
        path = root / filename
        if path.exists():
            try:
                snapshots.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError, ValueError):
                continue
    return ExternalEngineRegistry(snapshots, storage_root=storage_root)


def dependency_snapshot_handoff(
    registry: ExternalEngineRegistry,
    *,
    engine_family: str,
    required_capabilities: Iterable[str],
) -> dict[str, Any]:
    required = tuple(required_capabilities)
    capability_rows = [registry.get_capability(key) for key in required]
    return {
        "engine_family": engine_family,
        "snapshot_path": registry.snapshot_lookup(engine_family),
        "required_capabilities": list(required),
        "all_required_available": all(row.get("status") == CAPABILITY_STATUS_AVAILABLE for row in capability_rows),
        "capabilities": capability_rows,
    }


def _snapshot(
    *,
    engine_family: str,
    engine_name: str,
    status: str,
    runtime_path: str,
    version: str,
    architecture: str,
    checked_at: str,
    snapshot_path: Path,
    packages: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    install_guidance: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot_external_engine_dependency_snapshot.v1",
        "engine_family": engine_family,
        "engine_name": engine_name,
        "status": status,
        "runtime_path": runtime_path,
        "version": version,
        "architecture": architecture,
        "checked_at": checked_at,
        "snapshot_path": str(snapshot_path),
        "packages": packages,
        "blockers": blockers,
        "install_guidance": install_guidance,
        "notes": ["dependency_detection_only_no_formal_analysis_execution"],
    }


def _r_runtime_snapshot_from(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        key: snapshot.get(key, "")
        for key in ("schema_version", "engine_family", "engine_name", "status", "runtime_path", "version", "architecture", "checked_at", "snapshot_path", "blockers", "install_guidance")
    } | {"snapshot_path": str(external_engines_storage_root(Path(snapshot.get("snapshot_path", "")).parents[1] if snapshot.get("snapshot_path") else None) / R_RUNTIME_SNAPSHOT_FILENAME)}


def _r_enrichment_detection_payload(
    *,
    created_at: str,
    rscript: dict[str, Any],
    package_statuses: dict[str, dict[str, Any]],
    blockers: list[dict[str, Any]],
    warnings: list[str],
) -> dict[str, Any]:
    packages = {name: package_statuses.get(name, _r_enrichment_missing_package(name, "not_checked", "Package was not checked")) for name in R_ENRICHMENT_REQUIRED_PACKAGES}
    optional_packages = {
        name: package_statuses.get(name, _r_enrichment_missing_package(name, "not_checked", "Package was not checked"))
        for name in R_ENRICHMENT_OPTIONAL_PACKAGES
    }
    all_packages = packages | optional_packages
    return {
        "schema_version": R_ENRICHMENT_BACKEND_DETECTION_SCHEMA_VERSION,
        "created_at": created_at,
        "status": "blocked" if blockers else "passed",
        "rscript": rscript,
        "packages": packages,
        "optional_packages": optional_packages,
        "capabilities": _r_enrichment_capabilities(all_packages),
        "blockers": blockers,
        "warnings": list(dict.fromkeys(warnings)),
        "install_action": "none_detect_first_only",
        "packaging_policy": "external_runtime_not_bundled",
    }


def _detect_r_enrichment_package_statuses(rscript_path: str, runner: SubprocessRunner, package_names: Iterable[str]) -> dict[str, dict[str, Any]]:
    names = tuple(dict.fromkeys(package_names))
    script = (
        "pkgs <- c("
        + ", ".join(json.dumps(name) for name in names)
        + ")\n"
        "cat('package\\tavailable\\tversion\\timportable\\tmissing_reason\\n')\n"
        "for (pkg in pkgs) {\n"
        "  available <- requireNamespace(pkg, quietly=TRUE)\n"
        "  version <- ''\n"
        "  reason <- ''\n"
        "  if (available) {\n"
        "    version <- as.character(utils::packageVersion(pkg))\n"
        "  } else {\n"
        "    reason <- paste0('package_not_installed_or_not_on_libpaths:', pkg)\n"
        "  }\n"
        "  cat(pkg, available, version, available, reason, sep='\\t')\n"
        "  cat('\\n')\n"
        "}\n"
    )
    result = _run_checked(runner, [rscript_path, "-e", script], timeout=30)
    if result["returncode"] != 0:
        message = result["stderr"] or result["stdout"] or "R package detection failed"
        return {name: _r_enrichment_missing_package(name, "r_package_detection_error", message) for name in names}
    rows: dict[str, dict[str, Any]] = {}
    for line in result["stdout"].splitlines():
        if not line.strip() or line.startswith("package\t"):
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        name, available, version, importable, missing_reason = parts[:5]
        rows[name] = {
            "available": available.upper() == "TRUE",
            "version": version,
            "importable": importable.upper() == "TRUE",
            "missing_reason": missing_reason,
        }
    return {name: rows.get(name, _r_enrichment_missing_package(name, "package_not_reported", f"{name} was not returned by R package detection")) for name in names}


def _r_enrichment_missing_package(name: str, code: str, message: str) -> dict[str, Any]:
    reason = message if code in {"missing_r_runtime", "r_runtime_error", "r_package_detection_error"} else f"{code}:{name}"
    return {
        "available": False,
        "version": "",
        "importable": False,
        "missing_reason": reason,
    }


def _r_enrichment_required_by(package_name: str) -> tuple[str, ...]:
    return tuple(key for key, package_names in R_ENRICHMENT_CAPABILITY_REQUIREMENTS.items() if package_name in package_names)


def _r_enrichment_capabilities(package_statuses: dict[str, dict[str, Any]]) -> dict[str, bool]:
    return {
        capability: all(package_statuses.get(package, {}).get("available") and package_statuses.get(package, {}).get("importable") for package in packages)
        for capability, packages in R_ENRICHMENT_CAPABILITY_REQUIREMENTS.items()
    }


def _can_run_r_enrichment_fixtures(detection: dict[str, Any]) -> bool:
    if not (isinstance(detection.get("rscript"), dict) and detection["rscript"].get("available") and detection["rscript"].get("path")):
        return False
    packages = detection.get("packages") if isinstance(detection.get("packages"), dict) else {}
    required = ("clusterProfiler", "fgsea", "enrichplot", "ggplot2")
    return all(isinstance(packages.get(name), dict) and packages[name].get("available") and packages[name].get("importable") for name in required)


def _normalize_r_arch(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"aarch64", "arm64"}:
        return "arm64"
    if normalized in {"x86_64", "amd64"}:
        return "x86_64"
    return normalized or "unknown"


def _validate_tsv_columns(path: Path, required_columns: Iterable[str]) -> dict[str, Any]:
    if not path.exists():
        return {"status": "blocked", "columns": [], "blockers": [_blocker("fixture_output_missing", f"{path.name} was not created")]}
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle, delimiter="\t")
            columns = next(reader, [])
    except OSError as exc:
        return {"status": "blocked", "columns": [], "blockers": [_blocker("fixture_output_read_error", f"{exc.__class__.__name__}: {exc}")]}
    missing = [column for column in required_columns if column not in columns]
    blockers = [_blocker("fixture_output_missing_columns", f"{path.name} missing required columns: {', '.join(missing)}")] if missing else []
    return {"status": "blocked" if blockers else "passed", "columns": columns, "blockers": blockers}


def _parse_plot_smoke(stdout: str) -> list[dict[str, Any]]:
    lines = stdout.splitlines()
    try:
        start = lines.index("PLOT_SMOKE_BEGIN") + 1
        end = lines.index("PLOT_SMOKE_END")
    except ValueError:
        return []
    rows: list[dict[str, Any]] = []
    for line in lines[start:end]:
        if not line.strip() or line.startswith("check\t"):
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        rows.append({"check": parts[0], "ok": parts[1].upper() == "TRUE", "class": parts[2], "error": parts[3]})
    return rows


def _r_enrichment_fixture_script() -> str:
    return r"""
args <- commandArgs(trailingOnly=TRUE)
ora_path <- args[[1]]
gsea_path <- args[[2]]
suppressPackageStartupMessages({
  library(clusterProfiler)
  library(fgsea)
})
term2gene <- data.frame(
  term = c(rep("Pathway_A", 5), rep("Pathway_B", 4), rep("Pathway_C", 4)),
  gene = c("G1", "G2", "G3", "G4", "G5", "G1", "G6", "G7", "G8", "G9", "G10", "G11", "G12"),
  stringsAsFactors = FALSE
)
ora <- clusterProfiler::enricher(
  gene = c("G1", "G2", "G3"),
  TERM2GENE = term2gene,
  pvalueCutoff = 1,
  qvalueCutoff = 1,
  minGSSize = 1,
  maxGSSize = 500
)
ora_df <- as.data.frame(ora)
ora_cols <- c("ID", "Description", "GeneRatio", "BgRatio", "pvalue", "p.adjust", "qvalue", "geneID", "Count")
missing_ora <- setdiff(ora_cols, colnames(ora_df))
if (length(missing_ora) > 0) stop(paste("ORA fixture missing columns", paste(missing_ora, collapse=",")))
write.table(ora_df[, ora_cols, drop=FALSE], file=ora_path, sep="\t", quote=FALSE, row.names=FALSE)

stats <- c(G1=4.0, G2=3.2, G3=2.5, G4=1.6, G5=0.9, G6=-0.2, G7=-0.8, G8=-1.4, G9=-2.1, G10=-3.5)
pathways <- list(Pathway_A=c("G1","G2","G3","G4"), Pathway_B=c("G7","G8","G9","G10"), Pathway_C=c("G2","G5","G8"))
set.seed(20260528)
gsea <- fgsea::fgsea(pathways=pathways, stats=stats, minSize=1, maxSize=500, eps=0)
gsea_df <- as.data.frame(gsea)
gsea_df$leadingEdge <- vapply(gsea$leadingEdge, paste, character(1), collapse="/")
gsea_cols <- c("pathway", "ES", "NES", "pval", "padj", "leadingEdge", "size")
missing_gsea <- setdiff(gsea_cols, colnames(gsea_df))
if (length(missing_gsea) > 0) stop(paste("GSEA fixture missing columns", paste(missing_gsea, collapse=",")))
write.table(gsea_df[, gsea_cols, drop=FALSE], file=gsea_path, sep="\t", quote=FALSE, row.names=FALSE)

plot_rows <- data.frame(check=character(), ok=logical(), class=character(), error=character(), stringsAsFactors=FALSE)
if (requireNamespace("enrichplot", quietly=TRUE) && requireNamespace("ggplot2", quietly=TRUE)) {
  suppressPackageStartupMessages({
    library(enrichplot)
    library(ggplot2)
  })
  plot_checks <- list(
    ora_dotplot = function() enrichplot::dotplot(ora),
    ora_barplot = function() barplot(ora),
    gsea_curve = function() {
      cp_gsea <- clusterProfiler::GSEA(
        geneList = sort(stats, decreasing=TRUE),
        TERM2GENE = term2gene,
        pvalueCutoff = 1,
        minGSSize = 1,
        maxGSSize = 500,
        verbose = FALSE,
        seed = TRUE
      )
      enrichplot::gseaplot2(cp_gsea, geneSetID=1)
    }
  )
  for (name in names(plot_checks)) {
    result <- tryCatch(plot_checks[[name]](), error=function(e) e)
    if (inherits(result, "error")) {
      plot_rows <- rbind(plot_rows, data.frame(check=name, ok=FALSE, class="", error=conditionMessage(result), stringsAsFactors=FALSE))
    } else {
      ok <- inherits(result, "ggplot") || inherits(result, "gglist") || inherits(result, "gtable")
      plot_rows <- rbind(plot_rows, data.frame(check=name, ok=ok, class=paste(class(result), collapse="/"), error="", stringsAsFactors=FALSE))
    }
  }
}
cat("PLOT_SMOKE_BEGIN\n")
write.table(plot_rows, file=stdout(), sep="\t", quote=FALSE, row.names=FALSE)
cat("PLOT_SMOKE_END\n")
"""


def _detect_r_package_versions(rscript_path: str, runner: SubprocessRunner) -> dict[str, str]:
    package_names = ",".join(f'"{requirement.name}"' for requirement in R_PACKAGE_REQUIREMENTS)
    script = (
        f"pkgs <- c({package_names}); "
        "installed <- installed.packages()[, c('Package', 'Version'), drop=FALSE]; "
        "for (pkg in pkgs) { "
        "match <- installed[installed[, 'Package'] == pkg, , drop=FALSE]; "
        "if (nrow(match) > 0) cat(pkg, match[1, 'Version'], sep='\\t'); "
        "cat('\\n'); "
        "}"
    )
    result = _run_checked(runner, [rscript_path, "-e", script], timeout=20)
    if result["returncode"] != 0:
        return {}
    versions: dict[str, str] = {}
    for line in result["stdout"].splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[0] and parts[1]:
            versions[parts[0]] = parts[1]
    return versions


def _run_checked(runner: SubprocessRunner, command: list[str], *, timeout: int) -> dict[str, Any]:
    try:
        completed = runner(command, capture_output=True, text=True, timeout=timeout, check=False)
    except Exception as exc:
        return {"returncode": 1, "stdout": "", "stderr": f"{exc.__class__.__name__}: {exc}"}
    return {
        "returncode": int(getattr(completed, "returncode", 1)),
        "stdout": str(getattr(completed, "stdout", "") or ""),
        "stderr": str(getattr(completed, "stderr", "") or ""),
    }


def _command_version(command_path: str, runner: SubprocessRunner) -> str:
    for args in ((command_path, "--version"), (command_path, "-version")):
        result = _run_checked(runner, list(args), timeout=8)
        output = (result["stdout"] or result["stderr"]).strip().splitlines()
        if result["returncode"] == 0 and output:
            return output[0][:160]
    return "unknown_version"


def _blocker(code: str, message: str, *, package: str = "", required_by: Iterable[str] = ()) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message, "required_by": list(required_by)}
    if package:
        payload["package"] = package
    return payload


def _available_package(requirement: PackageRequirement, version: str) -> dict[str, Any]:
    return {
        "name": requirement.name,
        "required_for": list(requirement.required_for),
        "status": CAPABILITY_STATUS_AVAILABLE,
        "version": version,
        "minimum_version": requirement.minimum_version,
        "blocker": None,
        "capability_key": requirement.capability_key,
    }


def _missing_package(requirement: PackageRequirement, blocker: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": requirement.name,
        "required_for": list(requirement.required_for),
        "status": CAPABILITY_STATUS_MISSING,
        "version": "",
        "minimum_version": requirement.minimum_version,
        "blocker": blocker,
        "capability_key": requirement.capability_key,
    }


def _blocked_package(requirement: PackageRequirement, code: str, message: str) -> dict[str, Any]:
    blocker = _blocker(code, message, package=requirement.name, required_by=requirement.required_for)
    package = _missing_package(requirement, blocker)
    package["status"] = CAPABILITY_STATUS_BLOCKED
    return package


def _package_capability(package: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    blocker = package.get("blocker")
    return {
        "capability_key": str(package.get("capability_key") or ""),
        "status": str(package.get("status") or CAPABILITY_STATUS_UNKNOWN),
        "version": str(package.get("version") or ""),
        "runtime_path": str(package.get("runtime_path") or snapshot.get("runtime_path") or ""),
        "architecture": str(snapshot.get("architecture") or ""),
        "checked_at": str(snapshot.get("checked_at") or ""),
        "snapshot_path": str(snapshot.get("snapshot_path") or ""),
        "required_for": list(package.get("required_for") if isinstance(package.get("required_for"), list) else []),
        "blockers": [blocker] if isinstance(blocker, dict) else [],
    }


def _runtime_capability(capability_key: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    snapshot_status = str(snapshot.get("status") or "")
    if snapshot_status in {ENGINE_STATUS_AVAILABLE, ENGINE_STATUS_PARTIALLY_AVAILABLE}:
        status = CAPABILITY_STATUS_AVAILABLE
        blockers: list[dict[str, Any]] = []
    elif snapshot_status == ENGINE_STATUS_MISSING:
        status = CAPABILITY_STATUS_MISSING
        blockers = [item for item in snapshot.get("blockers", []) if isinstance(item, dict)]
    elif snapshot_status == ENGINE_STATUS_ERROR:
        status = CAPABILITY_STATUS_BLOCKED
        blockers = [item for item in snapshot.get("blockers", []) if isinstance(item, dict)]
    else:
        status = CAPABILITY_STATUS_UNKNOWN
        blockers = []
    return {
        "capability_key": capability_key,
        "status": status,
        "version": str(snapshot.get("version") or ""),
        "runtime_path": str(snapshot.get("runtime_path") or ""),
        "architecture": str(snapshot.get("architecture") or ""),
        "checked_at": str(snapshot.get("checked_at") or ""),
        "snapshot_path": str(snapshot.get("snapshot_path") or ""),
        "blockers": blockers,
    }


def _export_capability(packages: list[dict[str, Any]], *, required_keys: Iterable[str]) -> dict[str, Any]:
    by_key = {str(package.get("capability_key")): package for package in packages}
    blockers = [by_key[key].get("blocker") for key in required_keys if isinstance(by_key.get(key), dict) and by_key[key].get("status") != CAPABILITY_STATUS_AVAILABLE]
    return {
        "status": CAPABILITY_STATUS_AVAILABLE if not blockers else CAPABILITY_STATUS_BLOCKED,
        "blockers": [blocker for blocker in blockers if isinstance(blocker, dict)],
    }


def _module_available(import_name: str) -> bool:
    return importlib.util.find_spec(import_name) is not None


def _distribution_version(distribution_name: str) -> str | None:
    try:
        return importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _r_install_guidance() -> dict[str, Any]:
    return {
        "safe_to_show": True,
        "commands": [
            'Rscript -e \'install.packages("BiocManager")\'',
            'Rscript -e \'BiocManager::install(c("limma", "DESeq2", "edgeR"))\'',
            'Rscript -e \'install.packages(c("survival", "glmnet", "ggplot2", "survminer"))\'',
        ],
        "manual_steps": ["Install R first if Rscript is missing, then rerun external engine detection."],
    }


def _python_install_guidance() -> dict[str, Any]:
    return {
        "safe_to_show": True,
        "commands": [
            f"{sys.executable} -m pip install scipy statsmodels lifelines matplotlib scikit-survival",
        ],
        "manual_steps": ["Install packages into the same Python environment used by BioMedPilot."],
    }


def _renderer_install_guidance() -> dict[str, Any]:
    return {
        "safe_to_show": True,
        "commands": [],
        "manual_steps": [
            "Install pandoc for DOCX and full Markdown conversions.",
            "Install Quarto and a LaTeX distribution for full PDF export.",
            "Install wkhtmltopdf if HTML-to-PDF rendering is selected.",
        ],
    }


def _write_optional_snapshot(payload: dict[str, Any], path: Path, write_snapshot: bool) -> None:
    if write_snapshot:
        _write_json(path, payload)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
