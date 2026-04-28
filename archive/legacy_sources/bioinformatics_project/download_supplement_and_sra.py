#!/usr/bin/env python3
"""Compatibility-only legacy enhancement entrypoint; not part of the frozen GEO mainline.

Download GEO supplementary files and SRA data as enhancement modules.

Mainline GEO access remains full family SOFT -> GSE parsing.
Supplementary files and SRA are optional layers and are intentionally decoupled
from the main expression processing pipeline.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

import GEOparse
from GEOparse.sra_downloader import FastqDumpException, NoSRARelationException


LOGGER = logging.getLogger("download_supplement_and_sra")


class DownloadModuleError(Exception):
    """Base exception for supplementary and SRA module failures."""


class SupplementDownloadError(DownloadModuleError):
    """Raised when supplementary file download fails."""


class SRADownloadError(DownloadModuleError):
    """Raised when SRA download fails."""


class NoSRARelationError(SRADownloadError):
    """Raised when no SRA relation is present in the target samples."""


class FastqDumpError(SRADownloadError):
    """Raised when fastq/fasta conversion fails."""


@dataclass
class SupplementConfig:
    accession: str
    geo_dir: str
    outdir: str
    input_file: Optional[str] = None
    download_supplement: bool = True


@dataclass
class SRAConfig:
    accession: str
    geo_dir: str
    outdir: str
    email: str
    input_file: Optional[str] = None
    filetype: str = "sra"
    aspera: bool = False
    keep_sra: bool = False
    threads: int = 4
    fastq_dump_options: dict[str, Optional[str]] = field(default_factory=dict)
    filterby: Optional[str] = None
    nproc: int = 1


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def save_json(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def normalize_accession(accession: str) -> str:
    accession = accession.strip().upper()
    if not accession.startswith("GSE"):
        raise DownloadModuleError(f"Only GSE accessions are supported, got: {accession}")
    return accession


def is_gse_like(obj: Any) -> bool:
    return (
        obj is not None
        and getattr(obj, "__class__", type(None)).__name__ == "GSE"
        and hasattr(obj, "gsms")
    )


class GeoObjectView:
    """Thin BaseGEO-like view for GEOparse objects."""

    def __init__(self, geo_object: Any):
        self.geo_object = geo_object
        self.name = getattr(geo_object, "name", None)
        self.metadata = getattr(geo_object, "metadata", {}) or {}
        self.relations = getattr(geo_object, "relations", {}) or {}

    def get_accession(self) -> Optional[str]:
        if hasattr(self.geo_object, "get_accession"):
            return self.geo_object.get_accession()
        value = self.metadata.get("geo_accession")
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def get_metadata_attribute(self, metaname: str) -> Any:
        value = self.metadata.get(metaname)
        if value is None:
            return None
        if isinstance(value, list):
            return value if len(value) > 1 else value[0]
        return value


def load_gse_from_input(accession: str, geo_dir: str, input_file: Optional[str]) -> tuple[Any, Path]:
    accession = normalize_accession(accession)
    if input_file:
        soft_path = Path(input_file).expanduser().resolve()
    else:
        soft_path = Path(geo_dir).expanduser().resolve() / f"{accession}_family.soft.gz"

    LOGGER.info("Loading GSE from full family SOFT: %s", soft_path)
    if not soft_path.exists():
        raise DownloadModuleError(f"Full family SOFT file does not exist: {soft_path}")
    if soft_path.name.endswith(".txt"):
        raise DownloadModuleError(
            f"Quick text file is not allowed as supplementary/SRA main input: {soft_path}"
        )

    try:
        gse = GEOparse.get_GEO(filepath=str(soft_path), silent=False)
    except Exception as exc:
        raise DownloadModuleError(f"Failed to parse local family SOFT: {soft_path}") from exc

    if not is_gse_like(gse):
        raise DownloadModuleError(f"Parsed object is not a GSE-like object: {type(gse)!r}")
    return gse, soft_path


def flatten_paths(obj: Any) -> list[str]:
    paths: list[str] = []
    if isinstance(obj, str):
        paths.append(obj)
    elif isinstance(obj, dict):
        for value in obj.values():
            paths.extend(flatten_paths(value))
    elif isinstance(obj, (list, tuple, set)):
        for value in obj:
            paths.extend(flatten_paths(value))
    return sorted(set(paths))


def count_expected_supplement_urls(gse: Any) -> int:
    total = 0
    for gsm in (getattr(gse, "gsms", {}) or {}).values():
        metadata = getattr(gsm, "metadata", {}) or {}
        for key, values in metadata.items():
            if "supplementary_file" not in key.lower():
                continue
            for value in values:
                text = str(value).strip()
                if not text or text.upper() == "NONE" or "sra" in text.lower():
                    continue
                total += 1
    return total


def build_source_manifest(
    gse: Any,
    family_soft_path: Path,
    supplement_downloads: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = [
        {
            "source": "SOFT",
            "accession": gse.get_accession(),
            "local_path": str(family_soft_path),
        }
    ]
    for gpl_name, gpl in (getattr(gse, "gpls", {}) or {}).items():
        gpl_view = GeoObjectView(gpl)
        manifest.append(
            {
                "source": "GPL",
                "accession": gpl_name,
                "title": gpl_view.get_metadata_attribute("title"),
            }
        )
    if supplement_downloads:
        for gsm_name, payload in supplement_downloads.items():
            for remote_or_key, local_value in payload.items():
                if remote_or_key == "SRA":
                    continue
                for local_path in flatten_paths(local_value):
                    manifest.append(
                        {
                            "source": "SUPPLEMENT",
                            "gsm": gsm_name,
                            "remote": remote_or_key,
                            "local_path": local_path,
                        }
                    )
    return manifest


def run_supplement_workflow(config: SupplementConfig) -> dict[str, Any]:
    accession = normalize_accession(config.accession)
    gse, family_soft_path = load_gse_from_input(
        accession=accession,
        geo_dir=config.geo_dir,
        input_file=config.input_file,
    )

    outdir = Path(config.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    supplement_downloads: dict[str, Any] = {}
    expected_count = count_expected_supplement_urls(gse)
    if config.download_supplement:
        LOGGER.info("Downloading supplementary files via GSE.download_supplementary_files")
        try:
            supplement_downloads = gse.download_supplementary_files(
                directory=str(outdir / "supplement"),
                download_sra=False,
                email=None,
                sra_kwargs=None,
                nproc=1,
            )
        except Exception as exc:
            raise SupplementDownloadError("Failed to download supplementary files") from exc

    manifest = build_source_manifest(
        gse=gse,
        family_soft_path=family_soft_path,
        supplement_downloads=supplement_downloads,
    )
    downloaded_paths = flatten_paths(supplement_downloads)
    if expected_count > 0 and not downloaded_paths:
        raise SupplementDownloadError(
            "Supplementary file metadata exists, but no supplementary files were downloaded"
        )
    if expected_count > len(downloaded_paths):
        LOGGER.warning(
            "Only part of the supplementary files were downloaded: expected=%s downloaded=%s",
            expected_count,
            len(downloaded_paths),
        )
    summary = {
        "accession": accession,
        "family_soft_path": str(family_soft_path),
        "outdir": str(outdir),
        "downloaded_files": downloaded_paths,
        "expected_supplementary_files": expected_count,
        "supplementary_download_count": len(downloaded_paths),
        "sources": manifest,
        "status": "success",
    }
    save_json(summary, outdir / "supplement_run_summary.json")
    return summary


def parse_fastq_dump_options(raw: Optional[str]) -> dict[str, Optional[str]]:
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DownloadModuleError(
            "--fastq-dump-options must be a JSON object, for example "
            '\'{"split-files": null, "gzip": null}\''
        ) from exc
    if not isinstance(payload, dict):
        raise DownloadModuleError("--fastq-dump-options must decode to a JSON object")
    normalized: dict[str, Optional[str]] = {}
    for key, value in payload.items():
        normalized[str(key)] = None if value is None else str(value)
    return normalized


def gsm_text_blob(gsm: Any) -> str:
    view = GeoObjectView(gsm)
    text_parts = [str(gsm.name)]
    for key, value in view.metadata.items():
        if isinstance(value, list):
            text_parts.append(" ".join(map(str, value)))
        else:
            text_parts.append(str(value))
    return " ".join(text_parts).lower()


def compile_filterby(filterby: Optional[str]) -> Optional[Callable[[Any], bool]]:
    if not filterby:
        return None

    if filterby.startswith("regex:"):
        pattern = re.compile(filterby[len("regex:") :], flags=re.IGNORECASE)
        return lambda gsm: bool(pattern.search(gsm_text_blob(gsm)))

    if "=" in filterby:
        key, expected = filterby.split("=", 1)
        key = key.strip()
        expected = expected.strip().lower()

        def _filter(gsm: Any) -> bool:
            metadata = getattr(gsm, "metadata", {}) or {}
            values = metadata.get(key)
            if values is None:
                return False
            if isinstance(values, list):
                text = " ".join(map(str, values)).lower()
            else:
                text = str(values).lower()
            return expected in text

        return _filter

    keyword = filterby.strip().lower()
    return lambda gsm: keyword in gsm_text_blob(gsm)


def collect_target_gsms(gse: Any, filter_func: Optional[Callable[[Any], bool]]) -> list[Any]:
    gsms = list((getattr(gse, "gsms", {}) or {}).values())
    if filter_func is None:
        return gsms
    selected = [gsm for gsm in gsms if filter_func(gsm)]
    if not selected:
        raise NoSRARelationError("No GSM matched the provided filterby expression")
    return selected


def ensure_any_sra_relation(gsms: Iterable[Any]) -> None:
    for gsm in gsms:
        relations = getattr(gsm, "relations", {}) or {}
        if relations.get("SRA"):
            return
    raise NoSRARelationError("No SRA relation was found in the target GSM samples")


def normalize_sra_downloads(downloads: dict[str, Any]) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {}
    for gsm_name, payload in downloads.items():
        normalized[gsm_name] = flatten_paths(payload)
    return normalized


def run_sra_workflow(config: SRAConfig) -> dict[str, Any]:
    accession = normalize_accession(config.accession)
    gse, family_soft_path = load_gse_from_input(
        accession=accession,
        geo_dir=config.geo_dir,
        input_file=config.input_file,
    )

    outdir = Path(config.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    filter_func = compile_filterby(config.filterby)
    target_gsms = collect_target_gsms(gse, filter_func)
    ensure_any_sra_relation(target_gsms)

    LOGGER.info("Downloading SRA via GSE.download_SRA")
    try:
        downloads = gse.download_SRA(
            email=config.email,
            directory=str(outdir / "sra"),
            filterby=filter_func,
            nproc=config.nproc,
            filetype=config.filetype,
            aspera=config.aspera,
            keep_sra=config.keep_sra,
            threads=config.threads,
            fastq_dump_options=config.fastq_dump_options,
        )
    except NoSRARelationException as exc:
        raise NoSRARelationError(str(exc)) from exc
    except FastqDumpException as exc:
        raise FastqDumpError(str(exc)) from exc
    except Exception as exc:
        raise SRADownloadError("Failed during SRA download") from exc

    normalized_downloads = normalize_sra_downloads(downloads)
    if not any(normalized_downloads.values()):
        raise NoSRARelationError("SRA download returned no files for the target GSM samples")

    summary = {
        "accession": accession,
        "family_soft_path": str(family_soft_path),
        "outdir": str(outdir),
        "filetype": config.filetype,
        "filterby": config.filterby,
        "nproc": config.nproc,
        "downloads": normalized_downloads,
        "downloaded_files": flatten_paths(normalized_downloads),
        "status": "success",
    }
    save_json(summary, outdir / "sra_run_summary.json")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download GEO supplementary files and SRA data as enhancement modules."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    supp_parser = subparsers.add_parser(
        "supplement",
        help="Download supplementary files from a local full family SOFT input",
    )
    supp_parser.add_argument("accession", help="GSE accession, for example GSE12345")
    supp_parser.add_argument("--geo-dir", default="geo_downloads", help="Directory containing the family SOFT")
    supp_parser.add_argument("--outdir", default="geo_supplement", help="Output directory for supplementary files")
    supp_parser.add_argument("--input-file", default=None, help="Optional explicit family SOFT file path")

    sra_parser = subparsers.add_parser(
        "sra",
        help="Download SRA data from GSM/GSE objects with SRA relation",
    )
    sra_parser.add_argument("accession", help="GSE accession, for example GSE12345")
    sra_parser.add_argument("--geo-dir", default="geo_downloads", help="Directory containing the family SOFT")
    sra_parser.add_argument("--outdir", default="geo_sra", help="Output directory for SRA files")
    sra_parser.add_argument("--input-file", default=None, help="Optional explicit family SOFT file path")
    sra_parser.add_argument("--email", required=True, help="Email used for NCBI Entrez")
    sra_parser.add_argument("--filetype", choices=["sra", "fastq", "fasta"], default="sra")
    sra_parser.add_argument("--aspera", action="store_true", help="Use Aspera transfer")
    sra_parser.add_argument("--keep-sra", action="store_true", help="Keep .sra files after conversion")
    sra_parser.add_argument("--threads", type=int, default=4, help="Thread count for conversion")
    sra_parser.add_argument("--filterby", default=None, help="Sample filter, supports substring, key=value, or regex:pattern")
    sra_parser.add_argument("--nproc", type=int, default=1, help="Parallel processes for GSE.download_SRA")
    sra_parser.add_argument(
        "--fastq-dump-options",
        default=None,
        help='JSON object of extra fastq-dump options, for example \'{"gzip": null}\'',
    )
    return parser.parse_args()


def main() -> int:
    configure_logging()
    args = parse_args()

    try:
        if args.command == "supplement":
            config = SupplementConfig(
                accession=args.accession,
                geo_dir=args.geo_dir,
                outdir=args.outdir,
                input_file=args.input_file,
            )
            LOGGER.info("Supplement config: %s", json.dumps(asdict(config), ensure_ascii=False))
            result = run_supplement_workflow(config)
        else:
            config = SRAConfig(
                accession=args.accession,
                geo_dir=args.geo_dir,
                outdir=args.outdir,
                email=args.email,
                input_file=args.input_file,
                filetype=args.filetype,
                aspera=args.aspera,
                keep_sra=args.keep_sra,
                threads=args.threads,
                fastq_dump_options=parse_fastq_dump_options(args.fastq_dump_options),
                filterby=args.filterby,
                nproc=args.nproc,
            )
            LOGGER.info("SRA config: %s", json.dumps(asdict(config), ensure_ascii=False))
            result = run_sra_workflow(config)
    except DownloadModuleError as exc:
        LOGGER.error("Workflow failed: %s", exc, exc_info=True)
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2, ensure_ascii=False))
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
