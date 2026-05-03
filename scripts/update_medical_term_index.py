#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlretrieve
from xml.etree import ElementTree


DEFAULT_OUTPUT = Path("data/medical_terms/medical_terms_index.sqlite")
DEFAULT_METADATA = Path("data/medical_terms/source_metadata.json")
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
    disease_group: str = ""
    concept_type: str = "disease"
    parent_terms: list[str] = field(default_factory=list)
    cross_refs: dict[str, list[str]] = field(default_factory=dict)
    license: str = ""
    version: str = ""
    normalized_terms: list[str] = field(default_factory=list)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build BioMedPilot shared medical_terms_index.sqlite from local or downloaded ontology files."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--download-dir", type=Path, default=Path("data/medical_terms/raw"))
    parser.add_argument("--download", action="store_true", help="Download missing MONDO/DOID/NCIt/MeSH/EFO source files.")
    parser.add_argument("--mondo", type=Path)
    parser.add_argument("--doid", type=Path)
    parser.add_argument("--ncit", type=Path)
    parser.add_argument("--mesh", type=Path)
    parser.add_argument("--efo", type=Path)
    args = parser.parse_args()

    source_paths = _resolve_source_paths(args)
    concepts: list[IndexConcept] = []
    records: list[dict[str, object]] = []
    processed_at = _now()
    for vocabulary, path in source_paths.items():
        downloaded_at = processed_at if args.download and path.exists() and path.parent == args.download_dir else None
        if not path.exists():
            records.append(_metadata_record(vocabulary, path, downloaded_at, None, included=False))
            continue
        parsed = _parse_source(vocabulary, path)
        concepts.extend(parsed)
        records.append(_metadata_record(vocabulary, path, downloaded_at, processed_at, included=True))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    _write_sqlite(args.output, concepts)
    _write_source_metadata(args.metadata_output, records, processed_at)
    print(f"wrote {args.output} with {len(concepts)} concepts")
    return 0


def _resolve_source_paths(args: argparse.Namespace) -> dict[str, Path]:
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
        if args.download and not target.exists():
            args.download_dir.mkdir(parents=True, exist_ok=True)
            urlretrieve(DEFAULT_SOURCES[vocabulary], target)
        paths[vocabulary] = target
    return paths


def _download_filename(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def _parse_source(vocabulary: str, path: Path) -> list[IndexConcept]:
    if path.suffix.lower() == ".json":
        return _parse_unified_json(vocabulary, path)
    if path.suffix.lower() == ".jsonl":
        return _parse_unified_jsonl(vocabulary, path)
    if path.suffix.lower() == ".obo":
        return _parse_obo(vocabulary, path)
    if path.suffix.lower() == ".zip":
        return _parse_zip(vocabulary, path)
    if path.suffix.lower() in {".owl", ".xml"}:
        if vocabulary == "MeSH":
            return _parse_mesh_xml(path)
        return _parse_owl_xml(vocabulary, path)
    return []


def _parse_unified_json(vocabulary: str, path: Path) -> list[IndexConcept]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [_concept_from_mapping(vocabulary, item) for item in payload if isinstance(item, dict)]


def _parse_unified_jsonl(vocabulary: str, path: Path) -> list[IndexConcept]:
    concepts: list[IndexConcept] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict):
            concepts.append(_concept_from_mapping(vocabulary, payload))
    return concepts


def _parse_obo(vocabulary: str, path: Path) -> list[IndexConcept]:
    concepts: list[IndexConcept] = []
    current: dict[str, list[str] | str] = {}
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if line == "[Term]":
            _append_obo_concept(concepts, vocabulary, current)
            current = {}
            continue
        if not line or line.startswith("!"):
            continue
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        if key in {"id", "name"}:
            current[key] = value
        elif key in {"synonym", "xref", "is_a"}:
            current.setdefault(key, [])
            assert isinstance(current[key], list)
            current[key].append(value)
    _append_obo_concept(concepts, vocabulary, current)
    return concepts


def _append_obo_concept(concepts: list[IndexConcept], vocabulary: str, current: dict[str, list[str] | str]) -> None:
    source_id = str(current.get("id") or "")
    label = str(current.get("name") or "")
    if not source_id or not label:
        return
    synonyms = [_extract_obo_synonym(value) for value in current.get("synonym", []) if isinstance(value, str)]
    concepts.append(
        IndexConcept(
            concept_id=f"{vocabulary.lower()}:{source_id}",
            source_vocabulary=vocabulary,
            source_id=source_id,
            preferred_label_en=label,
            synonyms_en=_unique(synonyms),
            exact_synonyms_en=_unique(synonyms),
            parent_terms=_unique(str(value).split(" ! ", 1)[-1] for value in current.get("is_a", []) if isinstance(value, str)),
            license=LICENSES.get(vocabulary, ""),
            normalized_terms=_unique([label, *synonyms]),
        )
    )


def _extract_obo_synonym(value: str) -> str:
    if '"' not in value:
        return ""
    return value.split('"', 2)[1]


def _parse_zip(vocabulary: str, path: Path) -> list[IndexConcept]:
    concepts: list[IndexConcept] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith((".owl", ".xml", ".obo", ".json", ".jsonl")):
                continue
            temp = path.parent / f".{path.stem}-{Path(name).name}"
            temp.write_bytes(archive.read(name))
            concepts.extend(_parse_source(vocabulary, temp))
            temp.unlink(missing_ok=True)
            break
    return concepts


def _parse_owl_xml(vocabulary: str, path: Path) -> list[IndexConcept]:
    concepts: list[IndexConcept] = []
    try:
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
                        normalized_terms=_unique([label, *synonyms]),
                    )
                )
            elem.clear()
    except Exception:
        return concepts
    return concepts


def _parse_mesh_xml(path: Path) -> list[IndexConcept]:
    concepts: list[IndexConcept] = []
    try:
        for _event, elem in ElementTree.iterparse(path, events=("end",)):
            if _local_name(elem.tag) != "DescriptorRecord":
                elem.clear()
                continue
            source_id = _first_child_text(elem, {"DescriptorUI"})
            label = _first_child_text(elem, {"String"})
            if source_id and label:
                concepts.append(
                    IndexConcept(
                        concept_id=f"mesh:{source_id}",
                        source_vocabulary="MeSH",
                        source_id=source_id,
                        preferred_label_en=label,
                        synonyms_en=_unique(_child_texts(elem, {"String"})),
                        mesh_terms=[label],
                        license=LICENSES["MeSH"],
                        normalized_terms=_unique([label, *_child_texts(elem, {"String"})]),
                    )
                )
            elem.clear()
    except Exception:
        return concepts
    return concepts


def _concept_from_mapping(vocabulary: str, payload: dict[str, object]) -> IndexConcept:
    data = dict(payload)
    data.setdefault("source_vocabulary", vocabulary)
    data.setdefault("license", LICENSES.get(vocabulary, ""))
    return IndexConcept(**{key: data.get(key, default) for key, default in _defaults().items()})


def _write_sqlite(path: Path, concepts: list[IndexConcept]) -> None:
    if path.exists():
        path.unlink()
    with sqlite3.connect(str(path)) as conn:
        conn.execute(
            """
            CREATE TABLE term_concepts (
                concept_id TEXT PRIMARY KEY,
                source_vocabulary TEXT,
                source_id TEXT,
                preferred_label_en TEXT,
                synonyms_en TEXT,
                exact_synonyms_en TEXT,
                related_synonyms_en TEXT,
                abbreviations TEXT,
                mesh_terms TEXT,
                disease_group TEXT,
                concept_type TEXT,
                parent_terms TEXT,
                cross_refs TEXT,
                license TEXT,
                version TEXT,
                normalized_terms TEXT
            )
            """
        )
        conn.execute("CREATE INDEX idx_term_concepts_source ON term_concepts(source_vocabulary)")
        conn.executemany(
            """
            INSERT OR REPLACE INTO term_concepts VALUES (
                :concept_id, :source_vocabulary, :source_id, :preferred_label_en,
                :synonyms_en, :exact_synonyms_en, :related_synonyms_en,
                :abbreviations, :mesh_terms, :disease_group, :concept_type,
                :parent_terms, :cross_refs, :license, :version, :normalized_terms
            )
            """,
            [_sqlite_row(concept) for concept in concepts if concept.concept_id and concept.preferred_label_en],
        )
        conn.execute(
            """
            CREATE TABLE index_manifest (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        conn.execute("INSERT INTO index_manifest VALUES (?, ?)", ("scope", "BioMedPilot shared medical vocabulary"))
        conn.execute("INSERT INTO index_manifest VALUES (?, ?)", ("created_at", _now()))
        conn.commit()


def _sqlite_row(concept: IndexConcept) -> dict[str, object]:
    payload = asdict(concept)
    for key, value in payload.items():
        if isinstance(value, (list, dict)):
            payload[key] = json.dumps(value, ensure_ascii=False)
    return payload


def _write_source_metadata(path: Path, records: list[dict[str, object]], processed_at: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "biomedpilot.medical_terms.source_metadata.v2",
        "medical_terms_index_scope": "BioMedPilot shared medical vocabulary",
        "runtime_strategy": "preprocessed_sqlite_optional_plus_builtin_mini_index",
        "processed_at": processed_at,
        "vocabularies": records,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _metadata_record(vocabulary: str, path: Path, downloaded_at: str | None, processed_at: str | None, *, included: bool) -> dict[str, object]:
    return {
        "vocabulary_name": vocabulary,
        "source_url": DEFAULT_SOURCES.get(vocabulary, str(path)),
        "local_path": str(path),
        "version": "developer-generated",
        "license": LICENSES.get(vocabulary, ""),
        "downloaded_at": downloaded_at,
        "processed_at": processed_at,
        "included_in_package": False,
        "included_in_optional_full_index": included,
    }


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
        "disease_group": "",
        "concept_type": "disease",
        "parent_terms": [],
        "cross_refs": {},
        "license": "",
        "version": "",
        "normalized_terms": [],
    }


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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
