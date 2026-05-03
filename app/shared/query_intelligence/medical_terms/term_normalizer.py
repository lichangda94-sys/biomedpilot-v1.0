from __future__ import annotations

import re
import unicodedata


_SPACE_RE = re.compile(r"\s+")


def normalize_zh_term(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = _SPACE_RE.sub("", text)
    return text.strip().lower()


def normalize_en_term(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = _SPACE_RE.sub(" ", text)
    return text.strip().lower()
