from __future__ import annotations

import re

from app.shared.query_intelligence.meta_seed_terms.models import EvidenceCandidate, OutcomeEffectBinding


SECTION_PATTERN = re.compile(r"(?im)^[ \t]*(abstract|background|methods|results|discussion|conclusion|references)[ \t]*$")
OUTCOME_PATTERN = re.compile(r"\b(OS|PFS|DFS|RFS)\b|\b(overall survival|progression-free survival|disease-free survival|recurrence-free survival)\b", re.I)
EVIDENCE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("effect_measure", re.compile(r"\b(HR|OR|RR)\s*[=:]?\s*\d+(?:\.\d+)?", re.I)),
    ("confidence_interval", re.compile(r"95%\s*CI\s*[=:]?\s*\(?\s*\d+(?:\.\d+)?\s*[-,–]\s*\d+(?:\.\d+)?\s*\)?", re.I)),
    ("p_value", re.compile(r"\bP\s*(?:=|<)\s*0?\.\d+", re.I)),
    ("sample_size", re.compile(r"\b(?:n\s*=\s*\d+|\d+\s+patients?)\b", re.I)),
    ("follow_up", re.compile(r"\bfollow[- ]up\s+(?:was\s+)?\d+(?:\.\d+)?\s+(?:months?|years?)\b", re.I)),
)


def clean_english_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"-\n(?=[a-z])", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def split_sections(text: str) -> dict[str, str]:
    cleaned = clean_english_text(text)
    matches = list(SECTION_PATTERN.finditer(cleaned))
    if not matches:
        return {"body": _strip_references(cleaned)}
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = match.group(1).lower()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(cleaned)
        if name == "references":
            break
        sections[name] = cleaned[start:end].strip()
    return sections


def extract_evidence_candidates(text: str) -> list[EvidenceCandidate]:
    candidates: list[EvidenceCandidate] = []
    for section, section_text in split_sections(text).items():
        for evidence_type, pattern in EVIDENCE_PATTERNS:
            for match in pattern.finditer(section_text):
                candidates.append(
                    EvidenceCandidate(
                        evidence_type=evidence_type,
                        value=match.group(0),
                        section=section,
                        start=match.start(),
                        end=match.end(),
                        context=_context(section_text, match.start(), match.end()),
                    )
                )
    return candidates


def bind_outcome_effect_candidates(text: str, *, window: int = 180) -> list[OutcomeEffectBinding]:
    bindings: list[OutcomeEffectBinding] = []
    for section, section_text in split_sections(text).items():
        outcomes = list(OUTCOME_PATTERN.finditer(section_text))
        if not outcomes:
            continue
        evidence = [
            candidate
            for candidate in extract_evidence_candidates(section_text)
            if candidate.evidence_type in {"effect_measure", "confidence_interval", "p_value"}
        ]
        for outcome in outcomes:
            nearby = [
                candidate
                for candidate in evidence
                if abs(candidate.start - outcome.start()) <= window
            ]
            if nearby:
                bindings.append(
                    OutcomeEffectBinding(
                        outcome=outcome.group(0),
                        effect_measure=next((item.value for item in nearby if item.evidence_type == "effect_measure"), ""),
                        statistics=nearby,
                        section=section,
                    )
                )
    return bindings


def _strip_references(text: str) -> str:
    return re.split(r"(?im)^[ \t]*references[ \t]*$", text, maxsplit=1)[0].strip()


def _context(text: str, start: int, end: int, *, radius: int = 80) -> str:
    return text[max(0, start - radius) : min(len(text), end + radius)].strip()
