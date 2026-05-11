#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlretrieve
from xml.etree import ElementTree


SCHEMA_VERSION = "biomedpilot.medical_terms.sqlite.v6"
DEFAULT_OUTPUT = Path("data/medical_terms/medical_terms_index.sqlite")
DEFAULT_BUILD_REPORT = Path("data/medical_terms/medical_terms_index_build_report.json")
DEFAULT_METADATA = Path("data/medical_terms/source_metadata.json")
DEFAULT_MINI_INDEX = Path("data/medical_terms/mini_medical_terms_index.json")
DEFAULT_SOURCES = {
    "MONDO": "https://purl.obolibrary.org/obo/mondo.owl",
    "DOID": "https://purl.obolibrary.org/obo/doid.obo",
    "NCIt": "https://evs.nci.nih.gov/ftp1/NCI_Thesaurus/Thesaurus.owl.zip",
    "MeSH": "https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2024.xml",
    "EFO": "https://www.ebi.ac.uk/efo/efo.owl",
}
LICENSES = {
    "MONDO": "CC BY 4.0",
    "DOID": "CC0 1.0",
    "NCIt": "CC BY 4.0",
    "MeSH": "NLM terms apply",
    "EFO": "Apache 2.0",
    "mini": "project-local-curated",
}


@dataclass
class IndexConcept:
    concept_id: str
    source_vocabulary: str
    source_id: str
    preferred_label_en: str
    synonyms_en: list[str] = field(default_factory=list)
    exact_synonyms_en: list[str] = field(default_factory=list)
    related_synonyms_en: list[str] = field(default_factory=list)
    abbreviations: list[str] = field(default_factory=list)
    mesh_terms: list[str] = field(default_factory=list)
    tissue_terms: list[str] = field(default_factory=list)
    tcga_primary_site_candidates: list[str] = field(default_factory=list)
    data_modality_terms: list[str] = field(default_factory=list)
    assay_terms: list[str] = field(default_factory=list)
    platform_candidates: list[str] = field(default_factory=list)
    modifier_terms_en: list[str] = field(default_factory=list)
    exposure_terms: list[str] = field(default_factory=list)
    intervention_terms: list[str] = field(default_factory=list)
    outcome_terms: list[str] = field(default_factory=list)
    study_design_terms: list[str] = field(default_factory=list)
    publication_type_terms: list[str] = field(default_factory=list)
    pico_terms: list[str] = field(default_factory=list)
    effect_measures: list[str] = field(default_factory=list)
    diagnostic_accuracy_terms: list[str] = field(default_factory=list)
    exclusion_type_terms: list[str] = field(default_factory=list)
    quality_assessment_terms: list[str] = field(default_factory=list)
    pubmed_query_terms: list[str] = field(default_factory=list)
    disease_group: str = ""
    concept_type: str = "unknown"
    category: str = ""
    subcategory: str = ""
    contexts: list[str] = field(default_factory=list)
    parent_terms: list[str] = field(default_factory=list)
    cross_refs: dict[str, list[str]] = field(default_factory=dict)
    license: str = ""
    version: str = ""
    normalized_terms: list[str] = field(default_factory=list)
    definition: str = ""
    source_reference: str = ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build optional BioMedPilot medical_terms_index.sqlite with safe mini JSON fallback."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--build-report-output", type=Path, default=DEFAULT_BUILD_REPORT)
    parser.add_argument("--metadata-output", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--mini-index", type=Path, default=DEFAULT_MINI_INDEX)
    parser.add_argument("--download-dir", type=Path, default=Path("data/medical_terms/raw"))
    parser.add_argument("--download-sources", action="store_true", help="Explicitly download missing ontology source files.")
    parser.add_argument("--download", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--mondo", type=Path)
    parser.add_argument("--doid", type=Path)
    parser.add_argument("--ncit", type=Path)
    parser.add_argument("--mesh", type=Path)
    parser.add_argument("--efo", type=Path)
    args = parser.parse_args()

    processed_at = _now()
    download_sources = bool(args.download_sources or args.download)
    source_paths = _resolve_source_paths(args, download_sources=download_sources)
    source_records: list[dict[str, object]] = []
    warnings: list[str] = []
    ontology_concepts: list[IndexConcept] = []
    for vocabulary, path in source_paths.items():
        record = _source_record(vocabulary, path, processed_at if download_sources and path.exists() else None)
        if not path.exists():
            record["source_available"] = False
            warnings.append(f"{vocabulary} source missing: {path}")
            source_records.append(record)
            continue
        try:
            parsed = _parse_source(vocabulary, path)
        except Exception as exc:  # defensive: one source must not poison the build
            parsed = []
            warnings.append(f"{vocabulary} parse failed: {exc}")
        record["source_available"] = True
        record["parsed_terms_count"] = len(parsed)
        record["included_in_optional_index"] = bool(parsed)
        ontology_concepts.extend(parsed)
        source_records.append(record)

    mini_concepts = _load_mini_concepts(args.mini_index)
    if ontology_concepts:
        concepts = _dedupe_concepts([*ontology_concepts, *mini_concepts])
        fallback_mode = "partial_sources" if len(ontology_concepts) < len(source_paths) else "ontology_sources_available"
        index_kind = "ontology_plus_mini"
    else:
        concepts = mini_concepts
        fallback_mode = "mini_vocabulary_only"
        index_kind = "mini-derived sqlite index"
        warnings.append("No local ontology source files were parsed; built a mini-derived sqlite index for optional runtime validation.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    counts = _write_sqlite(args.output, concepts, source_records=source_records, fallback_mode=fallback_mode, index_kind=index_kind)
    report = _build_report(
        output=args.output,
        build_report=args.build_report_output,
        processed_at=processed_at,
        source_records=source_records,
        counts=counts,
        fallback_mode=fallback_mode,
        index_kind=index_kind,
        warnings=warnings,
    )
    args.build_report_output.parent.mkdir(parents=True, exist_ok=True)
    args.build_report_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _append_source_metadata(args.metadata_output, report)
    print(f"wrote {args.output} with {counts['terms_count']} terms")
    print(f"wrote {args.build_report_output}")
    return 0


def _resolve_source_paths(args: argparse.Namespace, *, download_sources: bool) -> dict[str, Path]:
    explicit = {
        "MONDO": args.mondo,
        "DOID": args.doid,
        "NCIt": args.ncit,
        "MeSH": args.mesh,
        "EFO": args.efo,
    }
    paths: dict[str, Path] = {}
    for vocabulary, path in explicit.items():
        if path is not None:
            paths[vocabulary] = path
            continue
        target = args.download_dir / _download_filename(DEFAULT_SOURCES[vocabulary])
        if download_sources and not target.exists():
            args.download_dir.mkdir(parents=True, exist_ok=True)
            urlretrieve(DEFAULT_SOURCES[vocabulary], target)
        paths[vocabulary] = target
    return paths


def _load_mini_concepts(path: Path) -> list[IndexConcept]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return []
    return [_concept_from_mapping("mini", item, source_reference=str(path)) for item in payload if isinstance(item, dict)]


def _parse_source(vocabulary: str, path: Path) -> list[IndexConcept]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _parse_unified_json(vocabulary, path)
    if suffix == ".jsonl":
        return _parse_unified_jsonl(vocabulary, path)
    if suffix == ".obo":
        return _parse_obo(vocabulary, path)
    if suffix == ".zip":
        return _parse_zip(vocabulary, path)
    if suffix in {".owl", ".xml"}:
        if vocabulary == "MeSH":
            return _parse_mesh_xml(path)
        return _parse_owl_xml(vocabulary, path)
    return []


def _parse_unified_json(vocabulary: str, path: Path) -> list[IndexConcept]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return []
    return [_concept_from_mapping(vocabulary, item, source_reference=str(path)) for item in payload if isinstance(item, dict)]


def _parse_unified_jsonl(vocabulary: str, path: Path) -> list[IndexConcept]:
    concepts: list[IndexConcept] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            concepts.append(_concept_from_mapping(vocabulary, payload, source_reference=str(path)))
    return concepts


def _parse_obo(vocabulary: str, path: Path) -> list[IndexConcept]:
    concepts: list[IndexConcept] = []
    current: dict[str, list[str] | str] = {}
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if line == "[Term]":
            _append_obo_concept(concepts, vocabulary, current, source_reference=str(path))
            current = {}
            continue
        if not line or line.startswith("!") or ": " not in line:
            continue
        key, value = line.split(": ", 1)
        if key in {"id", "name", "def"}:
            current[key] = value
        elif key in {"synonym", "xref", "is_a"}:
            current.setdefault(key, [])
            assert isinstance(current[key], list)
            current[key].append(value)
    _append_obo_concept(concepts, vocabulary, current, source_reference=str(path))
    return concepts


def _append_obo_concept(
    concepts: list[IndexConcept],
    vocabulary: str,
    current: dict[str, list[str] | str],
    *,
    source_reference: str,
) -> None:
    source_id = str(current.get("id") or "")
    label = str(current.get("name") or "")
    if not source_id or not label:
        return
    synonyms = [_extract_obo_synonym(value) for value in current.get("synonym", []) if isinstance(value, str)]
    crossrefs = [str(value).split(" ", 1)[0] for value in current.get("xref", []) if isinstance(value, str)]
    concepts.append(
        IndexConcept(
            concept_id=f"{vocabulary.lower()}:{source_id}",
            source_vocabulary=vocabulary,
            source_id=source_id,
            preferred_label_en=label,
            synonyms_en=_unique(synonyms),
            exact_synonyms_en=_unique(synonyms),
            parent_terms=_unique(str(value).split(" ! ", 1)[-1] for value in current.get("is_a", []) if isinstance(value, str)),
            cross_refs={vocabulary: crossrefs} if crossrefs else {},
            license=LICENSES.get(vocabulary, ""),
            version="local-source",
            normalized_terms=_unique([label, *synonyms]),
            definition=str(current.get("def") or "").strip('"'),
            source_reference=source_reference,
        )
    )


def _parse_zip(vocabulary: str, path: Path) -> list[IndexConcept]:
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith((".owl", ".xml", ".obo", ".json", ".jsonl")):
                continue
            temp = path.parent / f".{path.stem}-{Path(name).name}"
            temp.write_bytes(archive.read(name))
            try:
                return _parse_source(vocabulary, temp)
            finally:
                temp.unlink(missing_ok=True)
    return []


def _parse_owl_xml(vocabulary: str, path: Path) -> list[IndexConcept]:
    concepts: list[IndexConcept] = []
    for _event, elem in ElementTree.iterparse(path, events=("end",)):
        tag = _local_name(elem.tag)
        if tag not in {"Class", "Description"}:
            elem.clear()
            continue
        source_id = elem.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about", "")
        label = _first_child_text(elem, {"label", "prefLabel"})
        if source_id and label:
            synonyms = _child_texts(elem, {"hasExactSynonym", "hasRelatedSynonym", "altLabel"})
            concepts.append(
                IndexConcept(
                    concept_id=f"{vocabulary.lower()}:{source_id.rsplit('/', 1)[-1].replace('#', '')}",
                    source_vocabulary=vocabulary,
                    source_id=source_id,
                    preferred_label_en=label,
                    synonyms_en=_unique(synonyms),
                    exact_synonyms_en=_unique(synonyms),
                    license=LICENSES.get(vocabulary, ""),
                    version="local-source",
                    normalized_terms=_unique([label, *synonyms]),
                    source_reference=str(path),
                )
            )
        elem.clear()
    return concepts


def _parse_mesh_xml(path: Path) -> list[IndexConcept]:
    concepts: list[IndexConcept] = []
    for _event, elem in ElementTree.iterparse(path, events=("end",)):
        if _local_name(elem.tag) != "DescriptorRecord":
            elem.clear()
            continue
        source_id = _first_child_text(elem, {"DescriptorUI"})
        label = _first_child_text(elem, {"String"})
        if source_id and label:
            synonyms = _unique(_child_texts(elem, {"String"}))
            concepts.append(
                IndexConcept(
                    concept_id=f"mesh:{source_id}",
                    source_vocabulary="MeSH",
                    source_id=source_id,
                    preferred_label_en=label,
                    synonyms_en=synonyms,
                    mesh_terms=[label],
                    license=LICENSES["MeSH"],
                    version="local-source",
                    normalized_terms=_unique([label, *synonyms]),
                    source_reference=str(path),
                )
            )
        elem.clear()
    return concepts


def _concept_from_mapping(vocabulary: str, payload: dict[str, object], *, source_reference: str = "") -> IndexConcept:
    data = dict(payload)
    data.setdefault("source_vocabulary", vocabulary)
    data.setdefault("source_id", data.get("concept_id", ""))
    data.setdefault("preferred_label_en", data.get("canonical_name", ""))
    data.setdefault("license", LICENSES.get(vocabulary, ""))
    data.setdefault("version", "stage_v6_mini_derived" if vocabulary == "mini" else "local-source")
    data.setdefault("normalized_terms", _unique([data.get("preferred_label_en", ""), *(_list(data.get("synonyms_en")))]))
    data["source_reference"] = str(data.get("source_reference") or source_reference)
    return IndexConcept(**{key: data.get(key, default) for key, default in _defaults().items()})


def _write_sqlite(
    path: Path,
    concepts: list[IndexConcept],
    *,
    source_records: list[dict[str, object]],
    fallback_mode: str,
    index_kind: str,
) -> dict[str, int]:
    if path.exists():
        path.unlink()
    deduped = _dedupe_concepts(concepts)
    build_time = _now()
    with sqlite3.connect(str(path)) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            """
            CREATE TABLE ontology_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_id TEXT UNIQUE NOT NULL,
                ontology_source TEXT NOT NULL,
                ontology_id TEXT,
                canonical_name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                term_type TEXT NOT NULL,
                definition TEXT,
                source_reference TEXT,
                payload_json TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE ontology_synonyms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term_id INTEGER NOT NULL,
                synonym TEXT NOT NULL,
                normalized_synonym TEXT NOT NULL,
                synonym_type TEXT NOT NULL,
                language TEXT NOT NULL,
                source TEXT NOT NULL,
                UNIQUE(term_id, normalized_synonym, synonym_type, language),
                FOREIGN KEY(term_id) REFERENCES ontology_terms(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE ontology_crossrefs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term_id INTEGER NOT NULL,
                crossref_source TEXT NOT NULL,
                crossref_id TEXT NOT NULL,
                UNIQUE(term_id, crossref_source, crossref_id),
                FOREIGN KEY(term_id) REFERENCES ontology_terms(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE ontology_search_index (
                term_id INTEGER NOT NULL,
                normalized_value TEXT NOT NULL,
                value_type TEXT NOT NULL,
                UNIQUE(term_id, normalized_value, value_type),
                FOREIGN KEY(term_id) REFERENCES ontology_terms(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE ontology_build_metadata (
                build_id TEXT PRIMARY KEY,
                build_time TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                source_versions TEXT NOT NULL,
                source_files TEXT NOT NULL,
                entry_counts TEXT NOT NULL,
                warnings TEXT NOT NULL,
                fallback_mode TEXT NOT NULL,
                index_kind TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX idx_ontology_terms_normalized_name ON ontology_terms(normalized_name)")
        conn.execute("CREATE INDEX idx_ontology_synonyms_normalized ON ontology_synonyms(normalized_synonym)")
        conn.execute("CREATE INDEX idx_ontology_search_index_value ON ontology_search_index(normalized_value)")
        for concept in deduped:
            payload = _concept_payload(concept)
            cursor = conn.execute(
                """
                INSERT INTO ontology_terms (
                    concept_id, ontology_source, ontology_id, canonical_name,
                    normalized_name, term_type, definition, source_reference,
                    payload_json, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    concept.concept_id,
                    concept.source_vocabulary,
                    concept.source_id,
                    concept.preferred_label_en,
                    _norm(concept.preferred_label_en),
                    concept.concept_type or "unknown",
                    concept.definition,
                    concept.source_reference,
                    json.dumps(payload, ensure_ascii=False),
                    build_time,
                ),
            )
            term_id = int(cursor.lastrowid)
            _insert_synonyms(conn, term_id, concept)
            _insert_crossrefs(conn, term_id, concept)
            _insert_search_values(conn, term_id, concept)
        counts = _counts(conn)
        conn.execute(
            "INSERT INTO ontology_build_metadata VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"medical-terms-{build_time}",
                build_time,
                SCHEMA_VERSION,
                json.dumps({record["vocabulary_name"]: record.get("version", "") for record in source_records}, ensure_ascii=False),
                json.dumps(source_records, ensure_ascii=False),
                json.dumps(counts, ensure_ascii=False),
                json.dumps([], ensure_ascii=False),
                fallback_mode,
                index_kind,
            ),
        )
        conn.commit()
    return counts


def _insert_synonyms(conn: sqlite3.Connection, term_id: int, concept: IndexConcept) -> None:
    groups = (
        ("exact", concept.exact_synonyms_en, "en"),
        ("related", concept.related_synonyms_en, "en"),
        ("synonym", concept.synonyms_en, "en"),
        ("abbreviation", concept.abbreviations, "en"),
        ("mesh", concept.mesh_terms, "en"),
        ("tissue", concept.tissue_terms, "en"),
        ("data_modality", concept.data_modality_terms, "en"),
        ("assay", concept.assay_terms, "en"),
        ("platform", concept.platform_candidates, "en"),
        ("modifier", concept.modifier_terms_en, "en"),
        ("exposure", concept.exposure_terms, "en"),
        ("intervention", concept.intervention_terms, "en"),
        ("outcome", concept.outcome_terms, "en"),
        ("study_design", concept.study_design_terms, "en"),
        ("publication_type", concept.publication_type_terms, "en"),
        ("pico", concept.pico_terms, "en"),
        ("effect_measure", concept.effect_measures, "en"),
        ("diagnostic_accuracy", concept.diagnostic_accuracy_terms, "en"),
        ("exclusion_type", concept.exclusion_type_terms, "en"),
        ("quality_assessment", concept.quality_assessment_terms, "en"),
        ("pubmed_query", concept.pubmed_query_terms, "en"),
    )
    for synonym_type, values, language in groups:
        for value in values:
            conn.execute(
                """
                INSERT OR IGNORE INTO ontology_synonyms (
                    term_id, synonym, normalized_synonym, synonym_type, language, source
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (term_id, value, _norm(value), synonym_type, language, concept.source_vocabulary),
            )
    for value in concept.normalized_terms:
        language = "zh" if not str(value).isascii() else "en"
        conn.execute(
            """
            INSERT OR IGNORE INTO ontology_synonyms (
                term_id, synonym, normalized_synonym, synonym_type, language, source
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (term_id, value, _norm(value), "normalized_term", language, concept.source_vocabulary),
        )


def _insert_crossrefs(conn: sqlite3.Connection, term_id: int, concept: IndexConcept) -> None:
    for source, values in concept.cross_refs.items():
        for value in values:
            conn.execute(
                "INSERT OR IGNORE INTO ontology_crossrefs (term_id, crossref_source, crossref_id) VALUES (?, ?, ?)",
                (term_id, source, value),
            )


def _insert_search_values(conn: sqlite3.Connection, term_id: int, concept: IndexConcept) -> None:
    values = _unique(
        [
            concept.preferred_label_en,
            *concept.normalized_terms,
            *concept.synonyms_en,
            *concept.exact_synonyms_en,
            *concept.related_synonyms_en,
            *concept.abbreviations,
            *concept.mesh_terms,
            *concept.tissue_terms,
            *concept.data_modality_terms,
            *concept.assay_terms,
            *concept.platform_candidates,
            *concept.exposure_terms,
            *concept.intervention_terms,
            *concept.outcome_terms,
            *concept.study_design_terms,
            *concept.publication_type_terms,
            *concept.pico_terms,
            *concept.effect_measures,
            *concept.diagnostic_accuracy_terms,
            *concept.exclusion_type_terms,
            *concept.quality_assessment_terms,
            *concept.pubmed_query_terms,
        ]
    )
    for value in values:
        conn.execute(
            "INSERT OR IGNORE INTO ontology_search_index (term_id, normalized_value, value_type) VALUES (?, ?, ?)",
            (term_id, _norm(value), "term"),
        )


def _counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        "terms_count": conn.execute("SELECT COUNT(*) FROM ontology_terms").fetchone()[0],
        "synonyms_count": conn.execute("SELECT COUNT(*) FROM ontology_synonyms").fetchone()[0],
        "crossrefs_count": conn.execute("SELECT COUNT(*) FROM ontology_crossrefs").fetchone()[0],
    }


def _build_report(
    *,
    output: Path,
    build_report: Path,
    processed_at: str,
    source_records: list[dict[str, object]],
    counts: dict[str, int],
    fallback_mode: str,
    index_kind: str,
    warnings: list[str],
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "build_status": "success",
        "build_time": processed_at,
        "input_sources": source_records,
        "source_available": {record["vocabulary_name"]: bool(record.get("source_available")) for record in source_records},
        "source_missing": [record["vocabulary_name"] for record in source_records if not record.get("source_available")],
        "terms_count": counts["terms_count"],
        "synonyms_count": counts["synonyms_count"],
        "crossrefs_count": counts["crossrefs_count"],
        "warnings": warnings,
        "fallback_mode": fallback_mode,
        "index_kind": index_kind,
        "generated_files": [str(output), str(build_report)],
        "runtime_contract": "sqlite-first optional enhancement; JSON mini vocabulary remains fallback",
    }


def _append_source_metadata(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
    else:
        payload = {}
    payload.setdefault("schema_version", "biomedpilot.medical_terms.source_metadata.v2")
    payload.setdefault("medical_terms_index_scope", "BioMedPilot shared medical vocabulary")
    payload["runtime_strategy"] = "sqlite_first_optional_with_json_mini_fallback"
    payload["stage_v6_optional_sqlite_index"] = {
        "processed_at": report["build_time"],
        "schema_version": report["schema_version"],
        "generated_files": report["generated_files"],
        "fallback_mode": report["fallback_mode"],
        "index_kind": report["index_kind"],
        "terms_count": report["terms_count"],
        "synonyms_count": report["synonyms_count"],
        "crossrefs_count": report["crossrefs_count"],
        "note": "Optional sqlite enhancement only; mini_medical_terms_index.json and zh_term_overrides.json remain stable fallback inputs.",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _source_record(vocabulary: str, path: Path, downloaded_at: str | None) -> dict[str, object]:
    return {
        "vocabulary_name": vocabulary,
        "source_url": DEFAULT_SOURCES.get(vocabulary, str(path)),
        "local_path": str(path),
        "version": "local-source-if-present",
        "license": LICENSES.get(vocabulary, ""),
        "downloaded_at": downloaded_at,
        "processed_at": _now() if path.exists() else None,
        "source_available": path.exists(),
        "included_in_package": False,
        "included_in_optional_full_index": False,
        "parsed_terms_count": 0,
    }


def _concept_payload(concept: IndexConcept) -> dict[str, object]:
    payload = asdict(concept)
    payload.pop("definition", None)
    payload.pop("source_reference", None)
    return payload


def _dedupe_concepts(concepts: list[IndexConcept]) -> list[IndexConcept]:
    deduped: dict[str, IndexConcept] = {}
    for concept in concepts:
        if concept.concept_id and concept.preferred_label_en:
            deduped[concept.concept_id] = concept
    return list(deduped.values())


def _extract_obo_synonym(value: str) -> str:
    if '"' not in value:
        return ""
    return value.split('"', 2)[1]


def _download_filename(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def _first_child_text(elem: ElementTree.Element, names: set[str]) -> str:
    values = _child_texts(elem, names)
    return values[0] if values else ""


def _child_texts(elem: ElementTree.Element, names: set[str]) -> list[str]:
    values: list[str] = []
    for child in elem.iter():
        if _local_name(child.tag) in names and child.text and child.text.strip():
            values.append(child.text.strip())
    return _unique(values)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _defaults() -> dict[str, object]:
    return {
        "concept_id": "",
        "source_vocabulary": "",
        "source_id": "",
        "preferred_label_en": "",
        "synonyms_en": [],
        "exact_synonyms_en": [],
        "related_synonyms_en": [],
        "abbreviations": [],
        "mesh_terms": [],
        "tissue_terms": [],
        "tcga_primary_site_candidates": [],
        "data_modality_terms": [],
        "assay_terms": [],
        "platform_candidates": [],
        "modifier_terms_en": [],
        "exposure_terms": [],
        "intervention_terms": [],
        "outcome_terms": [],
        "study_design_terms": [],
        "publication_type_terms": [],
        "pico_terms": [],
        "effect_measures": [],
        "diagnostic_accuracy_terms": [],
        "exclusion_type_terms": [],
        "quality_assessment_terms": [],
        "pubmed_query_terms": [],
        "disease_group": "",
        "concept_type": "unknown",
        "category": "",
        "subcategory": "",
        "contexts": [],
        "parent_terms": [],
        "cross_refs": {},
        "license": "",
        "version": "",
        "normalized_terms": [],
        "definition": "",
        "source_reference": "",
    }


def _list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _unique(values: object) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:  # type: ignore[union-attr]
        text = str(value).strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            items.append(text)
    return items


def _norm(value: str) -> str:
    return " ".join(str(value).strip().lower().replace("_", " ").split())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
