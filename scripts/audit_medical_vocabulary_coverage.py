#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MEDICAL_TERMS_DIR = REPO_ROOT / "data" / "medical_terms"
CHECKLIST_DIR = MEDICAL_TERMS_DIR / "reference_checklists"
MINI_INDEX_PATH = MEDICAL_TERMS_DIR / "mini_medical_terms_index.json"
ZH_OVERRIDES_PATH = MEDICAL_TERMS_DIR / "zh_term_overrides.json"
JSON_REPORT_PATH = MEDICAL_TERMS_DIR / "coverage_audit_report.json"
MARKDOWN_REPORT_PATH = REPO_ROOT / "docs" / "stage_2_3_medical_vocabulary_reference_audit.md"


@dataclass(frozen=True)
class VocabularyCorpus:
    records: list[dict[str, Any]]
    text_by_field: dict[str, set[str]]
    all_text: set[str]
    tcga_projects: set[str]
    gtex_tissues: set[str]
    gtex_status_by_tissue: dict[str, set[str]]


def main() -> int:
    report = build_coverage_audit_report()
    JSON_REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    MARKDOWN_REPORT_PATH.write_text(render_markdown_report(report), encoding="utf-8")
    print(f"wrote {JSON_REPORT_PATH.relative_to(REPO_ROOT)}")
    print(f"wrote {MARKDOWN_REPORT_PATH.relative_to(REPO_ROOT)}")
    return 0


def build_coverage_audit_report() -> dict[str, Any]:
    corpus = _build_corpus()
    checklists = _load_checklists()
    sections: dict[str, Any] = {}
    for checklist in checklists:
        coverage_type = str(checklist.get("coverage_type") or checklist.get("checklist_id") or "")
        if coverage_type == "tcga_projects":
            section = _audit_tcga_projects(checklist, corpus)
        elif coverage_type == "gtex_tissues":
            section = _audit_gtex_tissues(checklist, corpus)
        elif coverage_type == "meta_terms":
            section = _audit_meta_terms(checklist, corpus)
        elif coverage_type == "oncology_core":
            section = _audit_oncology_core(checklist, corpus)
        else:
            section = _audit_generic_terms(checklist, corpus)
        sections[str(checklist.get("checklist_id"))] = section
    gaps = _prioritized_gaps(sections)
    quality_gates = _quality_gates(sections, gaps)
    return {
        "schema_version": "medical_vocabulary_coverage_audit.v1",
        "generated_at": _now(),
        "inputs": {
            "mini_index": str(MINI_INDEX_PATH.relative_to(REPO_ROOT)),
            "zh_overrides": str(ZH_OVERRIDES_PATH.relative_to(REPO_ROOT)),
            "reference_checklists": str(CHECKLIST_DIR.relative_to(REPO_ROOT)),
        },
        "overall": _overall_summary(sections),
        "sections": sections,
        "prioritized_gaps": gaps,
        "quality_gates": quality_gates,
        "source_notes": _source_notes(checklists),
    }


def render_markdown_report(report: dict[str, Any]) -> str:
    sections = report["sections"]
    lines = [
        "# Stage 2.3 Medical Vocabulary Reference Checklist Audit",
        "",
        "## Overall Coverage",
        "",
        _summary_table({"overall": report["overall"]}),
        "",
        "## TCGA Projects Covered/Missing",
        "",
        _details_table(sections["tcga_projects"], label_key="id", extra_keys=("expected_tcga_projects", "matched_tcga_projects")),
        "",
        "## Common Cancers Covered/Missing",
        "",
        _details_table(sections["common_cancers"], label_key="label", extra_keys=("matched_terms", "matched_tcga_projects")),
        "",
        "## Common Diseases Covered/Missing",
        "",
        _details_table(sections["common_diseases"], label_key="label", extra_keys=("matched_terms",)),
        "",
        "## GTEx Tissues Exact/Approximate/Missing",
        "",
        _details_table(sections["gtex_tissues"], label_key="label", extra_keys=("matched_gtex_tissues", "mapping_status")),
        "",
        "## Meta Terms Covered/Missing",
        "",
        _details_table(sections["meta_terms"], label_key="label", extra_keys=("matched_terms", "coverage_fraction")),
        "",
    ]
    if "oncology_core" in sections:
        lines.extend(
            [
                "## Oncology Core Covered/Missing",
                "",
                _details_table(
                    sections["oncology_core"],
                    label_key="label",
                    extra_keys=("matched_terms", "matched_tcga_projects", "matched_gtex_tissues"),
                ),
                "",
                "## Oncology Core Summary",
                "",
                _oncology_summary_lines(sections["oncology_core"]),
                "",
            ]
        )
    lines.extend(
        [
            "## P0 Gaps",
            "",
            _gap_list(report["prioritized_gaps"]["P0"], "No P0 gaps detected."),
            "",
            "## P1 Gaps",
            "",
            _gap_list(report["prioritized_gaps"]["P1"], "No P1 gaps detected."),
            "",
            "## P2 Gaps",
            "",
            _gap_list(report["prioritized_gaps"]["P2"], "No P2 gaps detected."),
            "",
            "## Quality Gates",
            "",
            _quality_gate_table(report["quality_gates"]),
            "",
            "## External Resource Sources And Version Notes",
            "",
        ]
    )
    for note in report["source_notes"]:
        lines.append(f"- {note['checklist_id']}: {note['source']} ({note['source_version']})")
    lines.extend(
        [
            "",
            "## Boundary Notes",
            "",
            "- The audit reads shared vocabulary JSON files and reference checklist JSON files only.",
            "- It does not call GEO, TCGA/GDC, GTEx, PubMed, Web of Science, Embase, or CNKI retrieval services.",
            "- TCGA and GTEx candidates are evaluated for Bioinformatics coverage; Meta terms are evaluated only from literature-search fields.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _audit_tcga_projects(checklist: dict[str, Any], corpus: VocabularyCorpus) -> dict[str, Any]:
    details = []
    for item in checklist["items"]:
        expected = _list(item.get("expected_tcga_projects"))
        matched_projects = [project for project in expected if _norm(project) in corpus.tcga_projects]
        matched_terms = _matched_terms(_list(item.get("expected_terms")), corpus.all_text)
        if set(map(_norm, expected)) <= corpus.tcga_projects:
            status = "covered"
        elif matched_projects or matched_terms:
            status = "partially_covered"
        else:
            status = "missing"
        details.append(_detail(item, status, matched_terms=matched_terms, matched_tcga_projects=matched_projects))
    return _section(checklist, details)


def _audit_gtex_tissues(checklist: dict[str, Any], corpus: VocabularyCorpus) -> dict[str, Any]:
    details = []
    for item in checklist["items"]:
        expected = _list(item.get("expected_gtex_tissues"))
        matched_tissues = [tissue for tissue in expected if _norm(tissue) in corpus.gtex_tissues]
        matched_terms = _matched_terms(_list(item.get("expected_terms")), corpus.all_text)
        statuses = sorted({status for tissue in matched_tissues for status in corpus.gtex_status_by_tissue.get(_norm(tissue), set()) if status})
        expected_status = str(item.get("expected_mapping_status") or "exact")
        if matched_tissues and expected_status != "approximate" and _has_exact_gtex_status(statuses):
            status = "covered"
            mapping_status = "exact"
        elif matched_tissues or matched_terms:
            status = "partially_covered"
            mapping_status = "approximate" if expected_status == "approximate" or "approximate" in statuses else "term_only"
        else:
            status = "missing"
            mapping_status = "missing"
        details.append(
            _detail(
                item,
                status,
                matched_terms=matched_terms,
                matched_gtex_tissues=matched_tissues,
                mapping_status=mapping_status,
            )
        )
    section = _section(checklist, details)
    section["exact"] = sum(1 for item in details if item.get("mapping_status") == "exact")
    section["approximate"] = sum(1 for item in details if item.get("mapping_status") == "approximate")
    return section


def _audit_meta_terms(checklist: dict[str, Any], corpus: VocabularyCorpus) -> dict[str, Any]:
    literature_fields = {
        "mesh_terms",
        "outcome_terms",
        "study_design_terms",
        "publication_type_terms",
        "abbreviations",
        "synonyms_en",
        "exposure_terms",
        "intervention_terms",
    }
    literature_text = set()
    for field in literature_fields:
        literature_text.update(corpus.text_by_field.get(field, set()))
    details = []
    for item in checklist["items"]:
        expected_terms = _list(item.get("expected_terms"))
        matched = _matched_terms(expected_terms, literature_text)
        fraction = len(matched) / len(expected_terms) if expected_terms else 0
        if fraction >= 0.8:
            status = "covered"
        elif matched:
            status = "partially_covered"
        else:
            status = "missing"
        details.append(_detail(item, status, matched_terms=matched, coverage_fraction=round(fraction, 3)))
    return _section(checklist, details)


def _audit_generic_terms(checklist: dict[str, Any], corpus: VocabularyCorpus) -> dict[str, Any]:
    details = []
    for item in checklist["items"]:
        expected_terms = _list(item.get("expected_terms"))
        expected_projects = _list(item.get("expected_tcga_projects"))
        matched_terms = _matched_terms(expected_terms, corpus.all_text)
        matched_projects = [project for project in expected_projects if _norm(project) in corpus.tcga_projects]
        expected_count = len(expected_terms) + len(expected_projects)
        matched_count = len(matched_terms) + len(matched_projects)
        if expected_count and matched_count >= expected_count:
            status = "covered"
        elif matched_count:
            status = "partially_covered"
        else:
            status = "missing"
        details.append(_detail(item, status, matched_terms=matched_terms, matched_tcga_projects=matched_projects))
    return _section(checklist, details)


def _audit_oncology_core(checklist: dict[str, Any], corpus: VocabularyCorpus) -> dict[str, Any]:
    details = []
    expected_tcga_all: set[str] = set()
    matched_tcga_all: set[str] = set()
    missing_common: list[dict[str, str]] = []
    for item in checklist["items"]:
        expected_terms = _list(item.get("expected_terms"))
        expected_projects = _list(item.get("expected_tcga_projects"))
        expected_tissues = _list(item.get("expected_gtex_tissues"))
        matched_terms = _matched_terms(expected_terms, corpus.all_text)
        matched_projects = [project for project in expected_projects if _norm(project) in corpus.tcga_projects]
        matched_tissues = [tissue for tissue in expected_tissues if _norm(tissue) in corpus.gtex_tissues]
        expected_tcga_all.update(expected_projects)
        matched_tcga_all.update(matched_projects)
        term_requirement_met = not expected_terms or bool(matched_terms)
        project_requirement_met = not expected_projects or set(map(_norm, expected_projects)) <= set(map(_norm, matched_projects))
        if term_requirement_met and project_requirement_met:
            status = "covered"
        elif matched_terms or matched_projects:
            status = "partially_covered"
        else:
            status = "missing"
        detail = _detail(
            item,
            status,
            matched_terms=matched_terms,
            matched_tcga_projects=matched_projects,
            matched_gtex_tissues=matched_tissues,
            group=str(item.get("group") or ""),
            parent_concept=str(item.get("parent_concept") or ""),
            subtype_of=str(item.get("subtype_of") or ""),
            avoid_expansion_to=_list(item.get("avoid_expansion_to")),
            confusion_notes=str(item.get("confusion_notes") or ""),
        )
        details.append(detail)
        if status == "missing" and detail["priority"] in {"P0", "P1"}:
            missing_common.append({"id": detail["id"], "label": detail["label"], "priority": detail["priority"]})
    section = _section(checklist, details)
    missing_tcga = sorted(project for project in expected_tcga_all if project not in matched_tcga_all)
    section["tcga_project_coverage"] = {
        "expected_count": len(expected_tcga_all),
        "covered_count": len(matched_tcga_all),
        "missing_count": len(missing_tcga),
        "coverage_rate": round(len(matched_tcga_all) / len(expected_tcga_all), 3) if expected_tcga_all else 0,
        "missing_projects": missing_tcga,
    }
    section["missing_common_oncology_concepts"] = missing_common
    section["high_risk_ambiguity_terms"] = checklist.get("ambiguity_terms", [])
    return section


def _section(checklist: dict[str, Any], details: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(details)
    covered = sum(1 for item in details if item["status"] == "covered")
    partial = sum(1 for item in details if item["status"] == "partially_covered")
    missing = sum(1 for item in details if item["status"] == "missing")
    return {
        "checklist_id": checklist["checklist_id"],
        "title": checklist["title"],
        "source": checklist["source"],
        "source_version": checklist["source_version"],
        "total_checklist_items": total,
        "covered": covered,
        "partially_covered": partial,
        "missing": missing,
        "coverage_rate": round(covered / total, 3) if total else 0,
        "weighted_coverage_rate": round((covered + partial * 0.5) / total, 3) if total else 0,
        "details": details,
    }


def _detail(item: dict[str, Any], status: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "id": str(item.get("id") or item.get("label") or ""),
        "label": str(item.get("label") or item.get("id") or ""),
        "priority": str(item.get("priority") or "P2"),
        "status": status,
        "expected_terms": _list(item.get("expected_terms")),
        "expected_tcga_projects": _list(item.get("expected_tcga_projects")),
        "expected_gtex_tissues": _list(item.get("expected_gtex_tissues")),
    }
    payload.update(extra)
    return payload


def _overall_summary(sections: dict[str, Any]) -> dict[str, Any]:
    total = sum(section["total_checklist_items"] for section in sections.values())
    covered = sum(section["covered"] for section in sections.values())
    partial = sum(section["partially_covered"] for section in sections.values())
    missing = sum(section["missing"] for section in sections.values())
    return {
        "total_checklist_items": total,
        "covered": covered,
        "partially_covered": partial,
        "missing": missing,
        "coverage_rate": round(covered / total, 3) if total else 0,
        "weighted_coverage_rate": round((covered + partial * 0.5) / total, 3) if total else 0,
    }


def _prioritized_gaps(sections: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    gaps: dict[str, list[dict[str, str]]] = {"P0": [], "P1": [], "P2": []}
    for section_id, section in sections.items():
        for item in section["details"]:
            if item["status"] == "covered":
                continue
            priority = item.get("priority", "P2")
            if priority not in gaps:
                priority = "P2"
            gaps[priority].append(
                {
                    "checklist": section_id,
                    "id": str(item["id"]),
                    "label": str(item["label"]),
                    "status": str(item["status"]),
                }
            )
    return gaps


def _quality_gates(sections: dict[str, Any], gaps: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    gates = [
        _threshold_gate(
            "core_cancers_coverage",
            "Common cancer checklist coverage must stay >= 95%.",
            sections["common_cancers"]["coverage_rate"],
            0.95,
        ),
        _threshold_gate(
            "tcga_project_mapping",
            "TCGA project checklist coverage must stay >= 90%.",
            sections["tcga_projects"]["coverage_rate"],
            0.90,
        ),
        _threshold_gate(
            "gtex_tissue_mapping",
            "GTEx tissue weighted coverage must stay >= 95%.",
            sections["gtex_tissues"]["weighted_coverage_rate"],
            0.95,
        ),
        _threshold_gate(
            "meta_retrieval_terms",
            "Meta outcome, design, effect-size, and publication filter terms must stay >= 90%.",
            sections["meta_terms"]["coverage_rate"],
            0.90,
        ),
        _threshold_gate(
            "oncology_core_coverage",
            "Oncology core checklist coverage must stay >= 95%.",
            sections["oncology_core"]["coverage_rate"],
            0.95,
        ),
        _zero_gate(
            "oncology_core_missing_tcga_projects",
            "Oncology core must cover all TCGA 33 project candidates.",
            sections["oncology_core"]["tcga_project_coverage"]["missing_count"],
        ),
        _zero_gate(
            "missing_items",
            "Reference checklist missing count must remain zero.",
            sum(section["missing"] for section in sections.values()),
        ),
        _zero_gate(
            "p0_gaps",
            "P0 gaps must remain zero.",
            len(gaps["P0"]),
        ),
        _zero_gate(
            "audit_cross_context_pollution",
            "Meta audit details must not report TCGA or GTEx matches.",
            _audit_cross_context_pollution_count(sections),
        ),
    ]
    return {
        "status": "pass" if all(gate["status"] == "pass" for gate in gates) else "fail",
        "gates": gates,
    }


def _threshold_gate(gate_id: str, description: str, observed: float, minimum: float) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "description": description,
        "metric": "coverage_rate",
        "minimum": minimum,
        "observed": observed,
        "status": "pass" if observed >= minimum else "fail",
    }


def _zero_gate(gate_id: str, description: str, observed: int) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "description": description,
        "metric": "count",
        "maximum": 0,
        "observed": observed,
        "status": "pass" if observed == 0 else "fail",
    }


def _audit_cross_context_pollution_count(sections: dict[str, Any]) -> int:
    count = 0
    for item in sections["meta_terms"]["details"]:
        count += len(item.get("matched_tcga_projects", []))
        count += len(item.get("matched_gtex_tissues", []))
    return count


def _source_notes(checklists: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "checklist_id": str(checklist["checklist_id"]),
            "source": str(checklist["source"]),
            "source_version": str(checklist["source_version"]),
        }
        for checklist in checklists
    ]


def _build_corpus() -> VocabularyCorpus:
    records = [*_load_json_list(MINI_INDEX_PATH), *_load_json_list(ZH_OVERRIDES_PATH)]
    text_by_field: dict[str, set[str]] = {}
    all_text: set[str] = set()
    tcga_projects: set[str] = set()
    gtex_tissues: set[str] = set()
    gtex_status_by_tissue: dict[str, set[str]] = {}
    for record in records:
        for field, values in _field_values(record).items():
            bucket = text_by_field.setdefault(field, set())
            for value in values:
                normalized = _norm(value)
                bucket.add(normalized)
                all_text.add(normalized)
        for project in _nested_values(record.get("tcga_project_candidates")):
            tcga_projects.add(_norm(project))
        cross_refs = record.get("cross_refs")
        if isinstance(cross_refs, dict):
            for project in _nested_values(cross_refs.get("tcga")):
                tcga_projects.add(_norm(project))
            for tissue in _nested_values(cross_refs.get("gtex")):
                gtex_tissues.add(_norm(tissue))
                gtex_status_by_tissue.setdefault(_norm(tissue), set()).update(_gtex_statuses_for(record, tissue))
        for tissue in _nested_values(record.get("gtex_tissue_candidates")):
            gtex_tissues.add(_norm(tissue))
            gtex_status_by_tissue.setdefault(_norm(tissue), set()).update(_gtex_statuses_for(record, tissue))
    return VocabularyCorpus(records, text_by_field, all_text, tcga_projects, gtex_tissues, gtex_status_by_tissue)


def _field_values(record: dict[str, Any]) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for key, value in record.items():
        if isinstance(value, dict):
            values[key] = [*_nested_values(value)]
        else:
            values[key] = [*_nested_values(value)]
    return values


def _matched_terms(expected_terms: list[str], corpus_terms: set[str]) -> list[str]:
    matched = []
    for term in expected_terms:
        normalized = _norm(term)
        if normalized in corpus_terms or any(normalized and normalized in value for value in corpus_terms):
            matched.append(term)
    return matched


def _has_exact_gtex_status(statuses: list[str]) -> bool:
    if not statuses:
        return True
    return any("exact" in status and "approximate" not in status for status in statuses)


def _gtex_statuses_for(record: dict[str, Any], tissue: str) -> set[str]:
    status = record.get("gtex_mapping_status")
    if isinstance(status, dict):
        value = status.get(tissue) or status.get(_norm(tissue)) or status.get(str(tissue).title())
        return {str(value or "exact")}
    if isinstance(status, str) and status:
        return {status}
    return {"exact"}


def _load_checklists() -> list[dict[str, Any]]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(CHECKLIST_DIR.glob("*.json"))]


def _load_json_list(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [item for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []


def _nested_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float)):
        return [str(value)]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_nested_values(item))
        return result
    if isinstance(value, dict):
        result: list[str] = []
        for item in value.values():
            result.extend(_nested_values(item))
        return result
    return []


def _summary_table(summaries: dict[str, dict[str, Any]]) -> str:
    rows = ["| Section | Total | Covered | Partial | Missing | Coverage | Weighted |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, summary in summaries.items():
        rows.append(
            f"| {name} | {summary['total_checklist_items']} | {summary['covered']} | {summary['partially_covered']} | "
            f"{summary['missing']} | {summary['coverage_rate']:.3f} | {summary['weighted_coverage_rate']:.3f} |"
        )
    return "\n".join(rows)


def _details_table(section: dict[str, Any], *, label_key: str, extra_keys: tuple[str, ...]) -> str:
    rows = ["| Item | Priority | Status | Evidence |", "| --- | --- | --- | --- |"]
    for item in section["details"]:
        evidence_parts = []
        for key in extra_keys:
            value = item.get(key)
            if isinstance(value, list):
                rendered = ", ".join(str(part) for part in value)
            else:
                rendered = str(value or "")
            if rendered:
                evidence_parts.append(f"{key}: {rendered}")
        rows.append(f"| {item[label_key]} | {item['priority']} | {item['status']} | {'; '.join(evidence_parts) or '-'} |")
    return "\n".join(rows)


def _gap_list(items: list[dict[str, str]], empty: str) -> str:
    if not items:
        return empty
    return "\n".join(f"- {item['checklist']}::{item['id']} ({item['label']}): {item['status']}" for item in items)


def _oncology_summary_lines(section: dict[str, Any]) -> str:
    tcga = section.get("tcga_project_coverage", {})
    ambiguity_terms = section.get("high_risk_ambiguity_terms", [])
    lines = [
        f"- oncology checklist total count: {section['total_checklist_items']}",
        f"- covered count: {section['covered']}",
        f"- missing count: {section['missing']}",
        f"- coverage percentage: {section['coverage_rate']:.3f}",
        f"- TCGA 33 project coverage: {tcga.get('covered_count', 0)}/{tcga.get('expected_count', 0)} ({tcga.get('coverage_rate', 0):.3f})",
        f"- missing TCGA projects: {', '.join(tcga.get('missing_projects', [])) or 'none'}",
    ]
    missing_common = section.get("missing_common_oncology_concepts", [])
    if missing_common:
        rendered = ", ".join(f"{item['id']} ({item['priority']})" for item in missing_common)
        lines.append(f"- missing common oncology concepts: {rendered}")
    else:
        lines.append("- missing common oncology concepts: none")
    if ambiguity_terms:
        rendered_terms = ", ".join(str(item.get("term") or item.get("id") or "") for item in ambiguity_terms)
        lines.append(f"- high-risk ambiguity terms: {rendered_terms}")
    else:
        lines.append("- high-risk ambiguity terms: none")
    return "\n".join(lines)


def _quality_gate_table(quality_gates: dict[str, Any]) -> str:
    rows = ["| Gate | Observed | Threshold | Status |", "| --- | ---: | ---: | --- |"]
    for gate in quality_gates["gates"]:
        threshold = gate.get("minimum", gate.get("maximum", ""))
        rows.append(f"| {gate['gate_id']} | {gate['observed']} | {threshold} | {gate['status']} |")
    rows.append(f"| overall_quality_gate_status | - | - | {quality_gates['status']} |")
    return "\n".join(rows)


def _list(value: Any) -> list[str]:
    return [str(item).strip() for item in _nested_values(value) if str(item).strip()]


def _norm(value: str) -> str:
    return " ".join(str(value).strip().lower().replace("_", " ").split())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
