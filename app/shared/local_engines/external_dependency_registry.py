from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
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
PYTHON_STATISTICAL_SNAPSHOT_FILENAME = "python_statistical_snapshot.json"
REPORT_RENDERER_SNAPSHOT_FILENAME = "report_renderer_snapshot.json"
CAPABILITY_REGISTRY_SNAPSHOT_FILENAME = "capability_registry_snapshot.json"

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
