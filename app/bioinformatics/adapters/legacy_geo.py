from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import subprocess
import sys
from pathlib import Path
import re


LEGACY_ROOT = Path(__file__).resolve().parents[1] / "legacy"
LEGACY_GEO_TOOL_ROOT = LEGACY_ROOT / "geo_tool"


@dataclass(frozen=True)
class GeoQueryPlan:
    query_text: str
    full_geo_query: str
    accessions: list[str]
    max_results: int
    legacy_source: str


def geo_check_command() -> list[str]:
    return [sys.executable, str(LEGACY_ROOT / "geo_tool" / "run_geo_tool.py"), "--check"]


def run_geo_environment_check() -> subprocess.CompletedProcess[str]:
    return subprocess.run(geo_check_command(), cwd=LEGACY_ROOT, text=True, capture_output=True, check=False)


class LegacyGeoAdapter:
    def build_query_plan(self, *, query_text: str, accession_text: str = "", max_results: int = 20) -> GeoQueryPlan:
        accessions = self.parse_accessions(f"{query_text}\n{accession_text}")
        clean_query = query_text.strip()
        with _legacy_geo_path():
            try:
                from geo_info_fetcher import GeoInfoFetcher

                full_geo_query = GeoInfoFetcher.build_series_query(clean_query)
            except Exception:
                full_geo_query = _fallback_series_query(clean_query)
        return GeoQueryPlan(
            query_text=clean_query,
            full_geo_query=full_geo_query,
            accessions=accessions,
            max_results=max_results,
            legacy_source="app/bioinformatics/legacy/geo_tool/geo_info_fetcher.py",
        )

    def parse_accessions(self, value: str) -> list[str]:
        seen: set[str] = set()
        accessions: list[str] = []
        for match in re.findall(r"\bGSE\d+\b", value.upper()):
            if match in seen:
                continue
            seen.add(match)
            accessions.append(match)
        return accessions


@contextmanager
def _legacy_geo_path():
    inserted: list[str] = []
    for path in (str(LEGACY_GEO_TOOL_ROOT), str(LEGACY_ROOT)):
        if path not in sys.path:
            sys.path.insert(0, path)
            inserted.append(path)
    try:
        yield
    finally:
        for path in inserted:
            try:
                sys.path.remove(path)
            except ValueError:
                pass


def _fallback_series_query(query_text: str) -> str:
    organism_filter = "(Homo sapiens[Organism] OR Mus musculus[Organism] OR Rattus norvegicus[Organism])"
    if any(token in query_text for token in ("GSE[ETYP]", "[Organism]")):
        return query_text
    if query_text:
        return f"({query_text}) AND GSE[ETYP] AND {organism_filter}"
    return f"GSE[ETYP] AND {organism_filter}"
