from __future__ import annotations

import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTROL_DIR = ROOT / "docs" / "project-control"
OUTPUT_JSON = CONTROL_DIR / "UI_ROUTE_CONTRACT_PHASE1_ROLLUP.json"
OUTPUT_MD = CONTROL_DIR / "UI_ROUTE_CONTRACT_PHASE1_ROLLUP.md"


@dataclass(frozen=True)
class ContractBatch:
    path: Path
    branch: str
    evidence_head: str
    row_count: int
    connected: int
    disabled: int
    broken: int
    modules: tuple[str, ...]
    code_paths: tuple[str, ...]
    changed_code_paths: tuple[str, ...]
    freshness: str


def _git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _git_changed_paths(base: str, paths: tuple[str, ...]) -> tuple[str, ...]:
    if not base or not paths:
        return ()
    try:
        output = _git(["diff", "--name-only", f"{base}..HEAD", "--", *paths])
    except subprocess.CalledProcessError:
        return ("<unresolvable-evidence-head>",)
    return tuple(line for line in output.splitlines() if line.strip())


def _infer_module(path: Path, row: dict[str, Any]) -> str:
    module = str(row.get("module") or "").strip()
    if module:
        return module
    name = path.name
    if "_BIO_" in name:
        return "Bioinformatics"
    if "_META_" in name:
        return "Meta Analysis"
    if "_LABTOOLS_" in name:
        return "LabTools"
    if "_PHASE1_" in name:
        return "Shell"
    return "Unknown"


def _status_counts(rows: list[dict[str, Any]]) -> tuple[int, int, int]:
    connected = disabled = broken = 0
    for row in rows:
        status = str(row.get("status") or "").strip().lower()
        if status == "connected":
            connected += 1
        elif status == "broken":
            broken += 1
        elif status in {"disabled", "placeholder"} or "disabled" in status:
            disabled += 1
        elif row.get("enabled") is False and row.get("disabled_reason"):
            disabled += 1
    return connected, disabled, broken


def _extract_candidate_paths(value: object) -> list[str]:
    if not isinstance(value, str):
        return []
    normalized = value.replace(";", " ").replace(",", " ")
    return [item.strip() for item in normalized.split() if item.strip()]


def _code_paths(rows: list[dict[str, Any]]) -> tuple[str, ...]:
    paths: set[str] = set()
    for row in rows:
        for key in ("current_file", "current_widget"):
            for value in _extract_candidate_paths(row.get(key)):
                if value.startswith(("app/", "tests/")) and (ROOT / value).exists():
                    paths.add(value)
    return tuple(sorted(paths))


def _freshness(evidence_head: str, current_head: str, changed_code_paths: tuple[str, ...]) -> str:
    if not evidence_head:
        return "missing-evidence-head"
    if evidence_head == current_head:
        return "current-head-proof"
    if changed_code_paths:
        return "stale-code-proof"
    return "prior-proof-docs-only-head-drift"


def _load_batches(current_head: str) -> list[ContractBatch]:
    batches: list[ContractBatch] = []
    for path in sorted(CONTROL_DIR.glob("UI_ROUTE_CONTRACT_*.json")):
        if path.name == OUTPUT_JSON.name:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("rows") or []
        if not isinstance(rows, list) or not rows:
            continue
        evidence_head = str(payload.get("head") or "")
        branch = str(payload.get("branch") or "")
        modules = tuple(sorted({_infer_module(path, row) for row in rows}))
        connected, disabled, broken = _status_counts(rows)
        code_paths = _code_paths(rows)
        changed = _git_changed_paths(evidence_head, code_paths)
        freshness = _freshness(evidence_head, current_head, changed)
        if broken:
            freshness = "blocked"
        batches.append(
            ContractBatch(
                path=path,
                branch=branch,
                evidence_head=evidence_head,
                row_count=len(rows),
                connected=connected,
                disabled=disabled,
                broken=broken,
                modules=modules,
                code_paths=code_paths,
                changed_code_paths=changed,
                freshness=freshness,
            )
        )
    return batches


def _payload(branch: str, current_head: str, batches: list[ContractBatch]) -> dict[str, Any]:
    module_totals: dict[str, Counter[str]] = defaultdict(Counter)
    freshness_totals: Counter[str] = Counter()
    for batch in batches:
        freshness_totals[batch.freshness] += 1
        for module in batch.modules:
            module_totals[module]["batches"] += 1
            module_totals[module]["rows"] += batch.row_count
            module_totals[module]["connected"] += batch.connected
            module_totals[module]["disabled"] += batch.disabled
            module_totals[module]["broken"] += batch.broken
            module_totals[module][batch.freshness] += 1
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "branch": branch,
        "head": current_head,
        "summary": {
            "batch_count": len(batches),
            "row_count": sum(batch.row_count for batch in batches),
            "connected": sum(batch.connected for batch in batches),
            "disabled": sum(batch.disabled for batch in batches),
            "broken": sum(batch.broken for batch in batches),
            "freshness": dict(sorted(freshness_totals.items())),
        },
        "modules": {
            module: dict(counter)
            for module, counter in sorted(module_totals.items())
        },
        "batches": [
            {
                "file": str(batch.path.relative_to(ROOT)),
                "branch": batch.branch,
                "evidence_head": batch.evidence_head,
                "freshness": batch.freshness,
                "row_count": batch.row_count,
                "connected": batch.connected,
                "disabled": batch.disabled,
                "broken": batch.broken,
                "modules": list(batch.modules),
                "code_paths": list(batch.code_paths),
                "changed_code_paths": list(batch.changed_code_paths),
            }
            for batch in batches
        ],
    }


def _md(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract Phase 1 Rollup",
        "",
        f"- created_at: `{payload['created_at']}`",
        f"- branch: `{payload['branch']}`",
        f"- head: `{payload['head']}`",
        "- scope: Shell, Bioinformatics, Meta Analysis, and LabTools route-contract evidence freshness.",
        "",
        "## Summary",
        "",
        f"- batch_count: `{summary['batch_count']}`",
        f"- row_count: `{summary['row_count']}`",
        f"- connected: `{summary['connected']}`",
        f"- disabled_with_reason: `{summary['disabled']}`",
        f"- broken: `{summary['broken']}`",
        "",
        "## Freshness Classification",
        "",
        "| Freshness | Batch count | Meaning |",
        "| --- | ---: | --- |",
    ]
    meanings = {
        "current-head-proof": "Evidence was generated at the current HEAD.",
        "prior-proof-docs-only-head-drift": "Evidence HEAD differs, but recorded app/test implementation paths did not change since that evidence.",
        "stale-code-proof": "Recorded implementation paths changed after the evidence HEAD; rerun before release claim.",
        "missing-evidence-head": "Contract is missing an evidence head.",
        "blocked": "Contract contains broken rows.",
    }
    for key, count in sorted(summary["freshness"].items()):
        lines.append(f"| `{key}` | {count} | {meanings.get(key, '')} |")
    lines.extend(
        [
            "",
            "## Module Totals",
            "",
            "| Module | Batches | Rows | Connected | Disabled | Broken | Current | Docs-only drift | Stale code | Blocked |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for module, data in payload["modules"].items():
        lines.append(
            "| {module} | {batches} | {rows} | {connected} | {disabled} | {broken} | {current} | {drift} | {stale} | {blocked} |".format(
                module=module,
                batches=data.get("batches", 0),
                rows=data.get("rows", 0),
                connected=data.get("connected", 0),
                disabled=data.get("disabled", 0),
                broken=data.get("broken", 0),
                current=data.get("current-head-proof", 0),
                drift=data.get("prior-proof-docs-only-head-drift", 0),
                stale=data.get("stale-code-proof", 0),
                blocked=data.get("blocked", 0),
            )
        )
    lines.extend(
        [
            "",
            "## Batch Details",
            "",
            "| Contract file | Modules | Evidence head | Freshness | Rows | Connected | Disabled | Broken | Changed code paths |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for batch in payload["batches"]:
        changed = ", ".join(batch["changed_code_paths"]) if batch["changed_code_paths"] else "-"
        lines.append(
            "| `{file}` | {modules} | `{head}` | `{freshness}` | {rows} | {connected} | {disabled} | {broken} | {changed} |".format(
                file=batch["file"],
                modules=", ".join(batch["modules"]),
                head=(batch["evidence_head"][:12] if batch["evidence_head"] else "-"),
                freshness=batch["freshness"],
                rows=batch["row_count"],
                connected=batch["connected"],
                disabled=batch["disabled"],
                broken=batch["broken"],
                changed=changed,
            )
        )
    lines.extend(
        [
            "",
            "## Release Interpretation",
            "",
            "- `current-head-proof` and `prior-proof-docs-only-head-drift` can support Phase 1 release planning if their screenshots and tests remain present.",
            "- `stale-code-proof` must be rerun before the route is claimed as current release evidence.",
            "- `blocked` is a release blocker until the broken rows are fixed or explicitly disabled with reason.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    branch = _git(["branch", "--show-current"])
    current_head = _git(["rev-parse", "HEAD"])
    batches = _load_batches(current_head)
    payload = _payload(branch, current_head, batches)
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(_md(payload), encoding="utf-8")
    summary = payload["summary"]
    print(
        "Phase1 rollup: "
        f"{summary['batch_count']} batches, "
        f"{summary['row_count']} rows, "
        f"{summary['connected']} connected, "
        f"{summary['disabled']} disabled, "
        f"{summary['broken']} broken"
    )
    print("Freshness:", ", ".join(f"{k}={v}" for k, v in sorted(summary["freshness"].items())))
    return 0 if summary["broken"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
