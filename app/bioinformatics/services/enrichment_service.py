from __future__ import annotations

import json
import csv
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.bioinformatics.adapters.enrichment_adapter import EnrichmentAdapter
from app.bioinformatics.deg_task_plan import DEG_PREFLIGHT_MANIFEST
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


@dataclass(frozen=True)
class EnrichmentPreflightResult:
    success: bool
    project_id: str
    source_path: str
    dataset_count: int
    ready_for_enrichment_count: int
    output_path: str
    message: str
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class REnrichmentBackendDetection:
    status: str
    rscript: str
    packages: dict[str, dict[str, object]]
    capabilities: dict[str, bool]
    blockers: list[dict[str, str]]
    message: str


@dataclass(frozen=True)
class FormalOraResult:
    success: bool
    project_id: str
    differential_expression_path: str
    gene_set_path: str
    output_path: str
    csv_path: str
    result_id: str
    significant_gene_count: int
    universe_gene_count: int
    term_count: int
    top_terms: list[dict[str, object]] = field(default_factory=list)
    result_index_path: str = ""
    message: str = ""
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)


class EnrichmentService:
    def __init__(
        self,
        *,
        adapter: EnrichmentAdapter | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._adapter = adapter or EnrichmentAdapter()
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def create_preflight(self, *, project_id: str, differential_expression_path: str) -> EnrichmentPreflightResult:
        task = self._start_task(project_id=project_id, source_path=differential_expression_path)
        validation_error = self._validate(differential_expression_path)
        if validation_error is not None:
            result = EnrichmentPreflightResult(
                success=False,
                project_id=project_id,
                source_path=differential_expression_path,
                dataset_count=0,
                ready_for_enrichment_count=0,
                output_path="",
                message=validation_error,
                error_count=1,
            )
            self._finish_task(task, result)
            return result

        source_path = Path(differential_expression_path).expanduser().resolve()
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            if "preflight_items" not in payload:
                raise ValueError("富集分析预检需要差异表达分析预检输出。")
            items = self._adapter.build_preflight(payload)
            ready_count = sum(1 for item in items if item.status == "ready_for_enrichment_runner")
            output_path = self._write_output(project_id, source_path, items)
            result = EnrichmentPreflightResult(
                success=True,
                project_id=project_id,
                source_path=str(source_path),
                dataset_count=len(items),
                ready_for_enrichment_count=ready_count,
                output_path=str(output_path),
                message=f"富集分析预检已生成：{ready_count}/{len(items)} 个数据集具备富集分析前置条件。",
                details={
                    "enrichment_executed": False,
                    "network_used": False,
                    "database_download_executed": False,
                },
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="bioinformatics",
                data_type="geo_enrichment_preflight",
                source_path=str(source_path),
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = EnrichmentPreflightResult(
                success=False,
                project_id=project_id,
                source_path=str(source_path),
                dataset_count=0,
                ready_for_enrichment_count=0,
                output_path="",
                message="富集分析预检失败，请确认输入来自差异表达分析预检。",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def detect_r_backend(self) -> REnrichmentBackendDetection:
        rscript = shutil.which("Rscript") or ""
        packages: dict[str, dict[str, object]] = {}
        blockers: list[dict[str, str]] = []
        package_names = ("ReactomePA", "msigdbr", "fgsea", "clusterProfiler")

        if not rscript:
            blockers.append({"code": "missing_rscript", "message": "Rscript is not available on PATH."})
            for package_name in package_names:
                packages[package_name] = {"available": False, "version": "", "missing_reason": "missing_rscript"}
        else:
            for package_name in package_names:
                probe = (
                    "pkg <- commandArgs(TRUE)[1]; "
                    "ok <- requireNamespace(pkg, quietly=TRUE); "
                    "if (ok) { cat(as.character(utils::packageVersion(pkg))) } else { quit(status=2) }"
                )
                try:
                    result = subprocess.run(
                        [rscript, "-e", probe, package_name],
                        capture_output=True,
                        text=True,
                        timeout=8,
                        check=False,
                    )
                except Exception as exc:
                    packages[package_name] = {"available": False, "version": "", "missing_reason": exc.__class__.__name__}
                    continue
                packages[package_name] = {
                    "available": result.returncode == 0,
                    "version": result.stdout.strip() if result.returncode == 0 else "",
                    "missing_reason": "none" if result.returncode == 0 else "package_not_installed_or_unavailable",
                }

        capabilities = {
            "ora_reactome": bool(packages.get("ReactomePA", {}).get("available")),
            "msigdb_metadata": bool(packages.get("msigdbr", {}).get("available")),
            "gsea_preranked_fgsea": bool(packages.get("fgsea", {}).get("available")),
            "gsea_preranked_clusterprofiler": bool(packages.get("clusterProfiler", {}).get("available")),
        }
        status = "available" if capabilities["ora_reactome"] and capabilities["msigdb_metadata"] else "blocked_missing_dependency"
        return REnrichmentBackendDetection(
            status=status,
            rscript=rscript,
            packages=packages,
            capabilities=capabilities,
            blockers=blockers,
            message="R enrichment backend is detect-only; no install, download, ORA, or GSEA execution was started.",
        )

    def run_formal_ora(
        self,
        *,
        project_id: str,
        differential_expression_path: str,
        gene_set_path: str,
        padj_threshold: float = 0.05,
        log2fc_threshold: float = 1.0,
    ) -> FormalOraResult:
        task = self._start_formal_ora_task(
            project_id=project_id,
            source_path=differential_expression_path,
            gene_set_path=gene_set_path,
        )
        validation_error = self._validate_formal_ora(differential_expression_path, gene_set_path)
        if validation_error is not None:
            result = FormalOraResult(
                success=False,
                project_id=project_id,
                differential_expression_path=differential_expression_path,
                gene_set_path=gene_set_path,
                output_path="",
                csv_path="",
                result_id="",
                significant_gene_count=0,
                universe_gene_count=0,
                term_count=0,
                message=validation_error,
                error_count=1,
            )
            self._finish_formal_ora_task(task, result)
            return result

        source_path = Path(differential_expression_path).expanduser().resolve()
        gmt_path = Path(gene_set_path).expanduser().resolve()
        try:
            preflight = json.loads(source_path.read_text(encoding="utf-8"))
            if "preflight_items" not in preflight:
                raise ValueError("正式 ORA 需要 DEG preflight JSON。")
            project_root = _infer_project_root(source_path)
            deg_files = _resolve_deg_result_files(preflight, source_path=source_path, project_root=project_root)
            if not deg_files:
                raise ValueError("DEG preflight 中没有可读取的 deg_result_files。")
            deg_summary = _collect_deg_gene_sets(
                deg_files,
                padj_threshold=padj_threshold,
                log2fc_threshold=log2fc_threshold,
            )
            gene_sets = _read_gmt(gmt_path)
            if not gene_sets:
                raise ValueError("GMT 文件中没有可读取的 gene set。")
            rows = _calculate_ora(
                significant_genes=deg_summary["significant_genes"],
                universe_genes=deg_summary["universe_genes"],
                gene_sets=gene_sets,
            )
            result_id = f"formal-ora-{uuid4().hex[:10]}"
            output_dir = _formal_ora_output_dir(
                project_id=project_id,
                project_root=project_root,
                storage_root=self._storage_root,
            )
            output_dir.mkdir(parents=True, exist_ok=True)
            csv_path = output_dir / f"{result_id}.csv"
            json_path = output_dir / f"{result_id}.json"
            _write_ora_csv(csv_path, rows)
            result_index_path = ""
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            payload = {
                "schema_version": "biomedpilot.formal_ora_result.v1",
                "status": "passed",
                "result_id": result_id,
                "project_id": project_id,
                "created_at": now,
                "differential_expression_path": str(source_path),
                "gene_set_path": str(gmt_path),
                "deg_result_files": [str(path) for path in deg_files],
                "parameters": {
                    "padj_threshold": padj_threshold,
                    "log2fc_threshold": log2fc_threshold,
                    "method": "hypergeometric_over_representation",
                    "p_adjust_method": "benjamini_hochberg",
                },
                "formal_ora_executed": True,
                "formal_gsea_executed": False,
                "network_used": False,
                "database_download_executed": False,
                "universe_gene_count": len(deg_summary["universe_genes"]),
                "significant_gene_count": len(deg_summary["significant_genes"]),
                "term_count": len(rows),
                "top_terms": rows[:20],
                "csv_path": str(csv_path),
            }
            json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if project_root is not None:
                result_index_path = self._register_formal_ora_result(
                    project_root=project_root,
                    result_id=result_id,
                    json_path=json_path,
                    csv_path=csv_path,
                    source_path=source_path,
                    gmt_path=gmt_path,
                    parameters=payload["parameters"],
                )
                payload["result_index_path"] = result_index_path
                json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self._data_center.register_asset(
                project_id=project_id,
                module="bioinformatics",
                data_type="formal_ora_result",
                source_path=str(source_path),
                output_path=str(json_path),
                status="available",
            )
            result = FormalOraResult(
                success=True,
                project_id=project_id,
                differential_expression_path=str(source_path),
                gene_set_path=str(gmt_path),
                output_path=str(json_path),
                csv_path=str(csv_path),
                result_id=result_id,
                significant_gene_count=len(deg_summary["significant_genes"]),
                universe_gene_count=len(deg_summary["universe_genes"]),
                term_count=len(rows),
                top_terms=rows[:5],
                result_index_path=result_index_path,
                message=f"正式 ORA 已完成：{len(rows)} 个 gene set，显著基因 {len(deg_summary['significant_genes'])} 个。",
                details={
                    "formal_ora_executed": True,
                    "formal_gsea_executed": False,
                    "network_used": False,
                    "database_download_executed": False,
                },
            )
            self._finish_formal_ora_task(task, result)
            return result
        except Exception as exc:
            result = FormalOraResult(
                success=False,
                project_id=project_id,
                differential_expression_path=str(source_path),
                gene_set_path=str(gmt_path),
                output_path="",
                csv_path="",
                result_id="",
                significant_gene_count=0,
                universe_gene_count=0,
                term_count=0,
                message="正式 ORA 失败，请确认 DEG 结果表、阈值列和 GMT 基因集输入。",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_formal_ora_task(task, result)
            return result

    def _validate(self, differential_expression_path: str) -> str | None:
        if not differential_expression_path.strip():
            return "请选择差异表达分析预检 JSON 文件。"
        path = Path(differential_expression_path).expanduser()
        if not path.exists():
            return "差异表达分析预检文件不存在，请检查路径。"
        if path.suffix.lower() != ".json":
            return "富集分析预检需要 JSON 输入。"
        return None

    def _validate_formal_ora(self, differential_expression_path: str, gene_set_path: str) -> str | None:
        preflight_error = self._validate(differential_expression_path)
        if preflight_error is not None:
            return preflight_error
        if not gene_set_path.strip():
            return "请选择 GMT gene set 文件。"
        path = Path(gene_set_path).expanduser()
        if not path.exists():
            return "GMT gene set 文件不存在，请检查路径。"
        if path.suffix.lower() != ".gmt":
            return "正式 ORA 当前只接受 GMT gene set 输入。"
        return None

    def _start_task(self, *, project_id: str, source_path: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.ANALYSIS,
            module="bioinformatics",
            title="Enrichment Preflight",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Creating enrichment preflight from {source_path}" if source_path else "Waiting for differential expression preflight",
        )

    def _finish_task(self, task: TaskRecord, result: EnrichmentPreflightResult) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._task_center.save_task(
            TaskRecord(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED if result.success else TaskStatus.FAILED,
                module=task.module,
                title=task.title,
                created_at=task.created_at,
                updated_at=now,
                project_id=task.project_id,
                started_at=task.started_at,
                finished_at=now,
                summary=result.message,
                error_message="" if result.success else result.message,
            )
        )

    def _start_formal_ora_task(self, *, project_id: str, source_path: str, gene_set_path: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        summary = f"Running formal ORA from {source_path} with gene set {gene_set_path}" if source_path else "Waiting for formal ORA inputs"
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.ANALYSIS,
            module="bioinformatics",
            title="Formal ORA",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=summary,
        )

    def _finish_formal_ora_task(self, task: TaskRecord, result: FormalOraResult) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._task_center.save_task(
            TaskRecord(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED if result.success else TaskStatus.FAILED,
                module=task.module,
                title=task.title,
                created_at=task.created_at,
                updated_at=now,
                project_id=task.project_id,
                started_at=task.started_at,
                finished_at=now,
                summary=result.message,
                error_message="" if result.success else result.message,
            )
        )

    def _register_formal_ora_result(
        self,
        *,
        project_root: Path,
        result_id: str,
        json_path: Path,
        csv_path: Path,
        source_path: Path,
        gmt_path: Path,
        parameters: dict[str, object],
    ) -> str:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        entry = ResultIndexEntry(
            result_id=result_id,
            task_run_id=f"task-run-{uuid4().hex[:10]}",
            task_type="ora",
            result_semantics="formal_computed_result",
            input_package_id=f"formal-ora-input-{uuid4().hex[:8]}",
            source_dataset_id=project_root.name,
            source_repository_manifest=str(source_path),
            parameters_manifest=parameters,
            engine_name="BioMedPilot local ORA",
            engine_version="1.0",
            dependency_snapshot={"scipy": "required", "backend": "scipy.stats.hypergeom"},
            output_artifacts=(
                {"artifact_type": "formal_ora_result_json", "path": _relative_or_absolute(json_path, project_root), "schema": "biomedpilot.formal_ora_result.v1"},
                {"artifact_type": "formal_ora_result_csv", "path": _relative_or_absolute(csv_path, project_root), "schema": "biomedpilot.formal_ora_result_table.v1"},
            ),
            plot_artifacts=(),
            report_artifacts=(),
            validation_status="passed",
            warnings=("formal_gsea_not_executed", "ora_report_ready_gate_not_enabled"),
            blockers=(),
            log_artifacts=({"artifact_type": "formal_ora_gene_set_input", "path": str(gmt_path)},),
            failure_reason="",
            created_at=now,
            updated_at=now,
            report_ready_eligible=False,
        )
        register_result(project_root, entry)
        return str(project_root / "results" / "summaries" / "result_index.json")

    def _write_output(self, project_id: str, source_path: Path, items: list[object]) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "bioinformatics" / "enrichment"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"geo_enrichment_preflight_{uuid4().hex[:12]}.json"
        payload = {
            "project_id": project_id,
            "source_path": str(source_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "enrichment_executed": False,
            "network_used": False,
            "database_download_executed": False,
            "preflight_items": [asdict(item) for item in items],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


def _infer_project_root(source_path: Path) -> Path | None:
    marker_parts = DEG_PREFLIGHT_MANIFEST.parts
    source_parts = source_path.parts
    if len(source_parts) >= len(marker_parts) and source_parts[-len(marker_parts) :] == marker_parts:
        return Path(*source_parts[: -len(marker_parts)]).resolve()
    return None


def _resolve_deg_result_files(preflight: dict[str, object], *, source_path: Path, project_root: Path | None) -> list[Path]:
    files: list[Path] = []
    for item in preflight.get("preflight_items", []) or []:
        if not isinstance(item, dict):
            continue
        for raw in item.get("deg_result_files", []) or []:
            path = _resolve_input_path(str(raw), source_path=source_path, project_root=project_root)
            if path is not None and path.is_file():
                files.append(path)
    return list(dict.fromkeys(files))


def _resolve_input_path(raw: str, *, source_path: Path, project_root: Path | None) -> Path | None:
    if not raw.strip():
        return None
    direct = Path(raw).expanduser()
    candidates = [direct]
    if not direct.is_absolute():
        candidates.append(source_path.parent / direct)
        if project_root is not None:
            candidates.append(project_root / direct)
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.exists():
            return resolved
    return candidates[-1].resolve() if candidates else None


def _collect_deg_gene_sets(deg_files: list[Path], *, padj_threshold: float, log2fc_threshold: float) -> dict[str, set[str]]:
    universe: set[str] = set()
    significant: set[str] = set()
    for path in deg_files:
        rows = _read_table(path)
        if not rows:
            continue
        columns = _deg_columns(rows[0].keys())
        if not columns["gene"] or not columns["log2fc"] or not columns["pvalue"]:
            continue
        for row in rows:
            gene = _normalize_gene(row.get(columns["gene"], ""))
            if not gene:
                continue
            universe.add(gene)
            log2fc = _to_float(row.get(columns["log2fc"], ""))
            pvalue = _to_float(row.get(columns["pvalue"], ""))
            if log2fc is None or pvalue is None:
                continue
            if pvalue <= padj_threshold and abs(log2fc) >= log2fc_threshold:
                significant.add(gene)
    if not universe:
        raise ValueError("DEG 结果表没有可读取的 gene universe。")
    if not significant:
        raise ValueError("按当前阈值没有显著基因，无法运行正式 ORA。")
    return {"universe_genes": universe, "significant_genes": significant}


def _read_table(path: Path) -> list[dict[str, str]]:
    delimiter = "\t" if path.suffix.lower() in {".tsv", ".txt"} or ".tsv" in path.name.lower() else ","
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        return [{str(key or "").strip(): str(value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle, delimiter=delimiter)]


def _deg_columns(columns: object) -> dict[str, str]:
    normalized = {_normalize_column(str(column)): str(column) for column in columns}
    return {
        "gene": (
            normalized.get("gene")
            or normalized.get("geneid")
            or normalized.get("genesymbol")
            or normalized.get("symbol")
            or normalized.get("genename")
            or normalized.get("ensemblgeneid")
            or ""
        ),
        "log2fc": (
            normalized.get("log2foldchange")
            or normalized.get("log2fc")
            or normalized.get("logfc")
            or normalized.get("log2_fold_change")
            or ""
        ),
        "pvalue": (
            normalized.get("padj")
            or normalized.get("fdr")
            or normalized.get("qvalue")
            or normalized.get("qvalue")
            or normalized.get("padj")
            or normalized.get("adjpvalue")
            or normalized.get("pvalue")
            or ""
        ),
    }


def _normalize_column(value: str) -> str:
    return "".join(character.lower() for character in value if character.isalnum())


def _normalize_gene(value: object) -> str:
    return str(value or "").strip().upper()


def _read_gmt(path: Path) -> dict[str, set[str]]:
    gene_sets: dict[str, set[str]] = {}
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            parts = [part.strip() for part in line.rstrip("\n").split("\t")]
            if len(parts) < 3:
                continue
            term = parts[0]
            genes = {_normalize_gene(gene) for gene in parts[2:] if _normalize_gene(gene)}
            if term and genes:
                gene_sets[term] = genes
    return gene_sets


def _calculate_ora(*, significant_genes: set[str], universe_genes: set[str], gene_sets: dict[str, set[str]]) -> list[dict[str, object]]:
    from scipy.stats import hypergeom

    universe_count = len(universe_genes)
    hit_count = len(significant_genes)
    rows: list[dict[str, object]] = []
    for term, raw_genes in gene_sets.items():
        term_genes = raw_genes & universe_genes
        overlap = sorted(term_genes & significant_genes)
        if not term_genes:
            continue
        pvalue = float(hypergeom.sf(len(overlap) - 1, universe_count, len(term_genes), hit_count)) if overlap else 1.0
        rows.append(
            {
                "term": term,
                "overlap_count": len(overlap),
                "term_gene_count": len(term_genes),
                "significant_gene_count": hit_count,
                "universe_gene_count": universe_count,
                "p_value": pvalue,
                "overlap_genes": overlap,
            }
        )
    adjusted = _benjamini_hochberg([float(row["p_value"]) for row in rows])
    for row, padj in zip(rows, adjusted, strict=True):
        row["adjusted_p_value"] = padj
        row["gene_ratio"] = f"{row['overlap_count']}/{hit_count}"
        row["background_ratio"] = f"{row['term_gene_count']}/{universe_count}"
    return sorted(rows, key=lambda item: (float(item["adjusted_p_value"]), float(item["p_value"]), -int(item["overlap_count"])))


def _benjamini_hochberg(pvalues: list[float]) -> list[float]:
    count = len(pvalues)
    if count == 0:
        return []
    ordered = sorted(enumerate(pvalues), key=lambda item: item[1])
    adjusted = [1.0] * count
    running = 1.0
    for rank, (index, pvalue) in reversed(list(enumerate(ordered, start=1))):
        running = min(running, pvalue * count / rank)
        adjusted[index] = min(running, 1.0)
    return adjusted


def _write_ora_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "term",
        "overlap_count",
        "term_gene_count",
        "significant_gene_count",
        "universe_gene_count",
        "gene_ratio",
        "background_ratio",
        "p_value",
        "adjusted_p_value",
        "overlap_genes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: ";".join(row[key]) if key == "overlap_genes" else row.get(key, "") for key in fieldnames})


def _formal_ora_output_dir(*, project_id: str, project_root: Path | None, storage_root: Path) -> Path:
    if project_root is not None:
        return project_root / "results" / "enrichment"
    return storage_root / "projects" / project_id / "bioinformatics" / "enrichment"


def _relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _to_float(value: object) -> float | None:
    try:
        text = str(value).strip()
        return float(text) if text else None
    except (TypeError, ValueError):
        return None
