from __future__ import annotations


_ORGANISM_ZH: dict[str, str] = {
    "Homo sapiens": "人类",
    "Mus musculus": "小鼠",
    "Rattus norvegicus": "大鼠",
    "Danio rerio": "斑马鱼",
    "Drosophila melanogaster": "果蝇",
    "Caenorhabditis elegans": "秀丽隐杆线虫",
}


def get_organism_zh(raw_name: object) -> str:
    """Return the canonical Chinese organism label without changing raw metadata."""

    normalized = _normalize_organism(raw_name)
    if not normalized:
        return ""
    return _ORGANISM_ZH.get(normalized, "")


def get_organism_display_name(raw_name: object) -> str:
    normalized = _normalize_organism(raw_name)
    if not normalized:
        return "未记录"
    zh = _ORGANISM_ZH.get(normalized)
    if zh:
        return f"{zh}（{normalized}）"
    return f"{normalized}（未映射中文名）"


def _normalize_organism(raw_name: object) -> str:
    text = str(raw_name or "").strip()
    if not text or text in {"未记录", "待确认", "unknown", "Unknown"}:
        return ""
    if ";" in text:
        parts = [part.strip() for part in text.split(";") if part.strip()]
        if len(set(parts)) == 1:
            return parts[0]
    return text
