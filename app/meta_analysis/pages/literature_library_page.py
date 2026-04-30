from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.meta_analysis.ui_text import (
    DEVELOPER_INFO_TITLE_ZH,
    DUPLICATE_RISK_COLOR_ZH,
    DUPLICATE_RISK_LABEL_ZH,
    INTERNAL_BETA_STATUS_ZH,
    LITERATURE_LIBRARY_TITLE_ZH,
    LITERATURE_TABLE_COLUMN_ZH,
)
from app.version import APP_VERSION


DUPLICATE_RISK_HIGH = "high_duplicate_risk"
DUPLICATE_RISK_PROBABLE = "probable_duplicate"
DUPLICATE_RISK_POSSIBLE = "possible_duplicate"
DUPLICATE_RISK_NONE = "no_obvious_duplicate_risk"


@dataclass(frozen=True)
class LiteratureLibraryRow:
    record_id: str
    title: str
    authors_text: str
    first_author: str
    corresponding_author: str
    journal: str
    year: str
    publication_date: str
    doi: str
    pmid: str
    publication_type: str
    abstract_available: bool
    source_database: str
    source_file: str
    import_batch_id: str
    duplicate_risk: str
    duplicate_risk_label: str
    duplicate_risk_label_zh: str
    duplicate_group_ids: tuple[str, ...]
    duplicate_reasons: tuple[str, ...]
    screening_status: str
    fulltext_status: str
    extraction_status: str
    row_status_color: str
    row_status_color_zh: str


@dataclass(frozen=True)
class LiteratureLibraryState:
    title: str
    status_label: str
    description: str
    project_dir: str
    empty_state: str
    input_summary: str
    output_summary: str
    next_step: str
    rows: tuple[LiteratureLibraryRow, ...]
    total_records: int
    high_duplicate_risk_count: int
    probable_duplicate_count: int
    possible_duplicate_count: int
    no_obvious_duplicate_risk_count: int
    table_columns: tuple[str, ...]
    table_column_labels_zh: tuple[str, ...]
    warnings: tuple[str, ...]
    testing_limitations: tuple[str, ...]
    title_zh: str = LITERATURE_LIBRARY_TITLE_ZH
    status_label_zh: str = "内部测试"
    description_zh: str = "中文友好的只读文献库表格，用于查看文献基本信息、重复风险和流程状态。"
    input_summary_zh: str = "输入：导入文献、重复候选组、筛选/全文/提取状态。"
    output_summary_zh: str = "输出：只读表格和重复风险提示；不自动删除、不自动合并。"
    next_step_zh: str = "下一步：处理高风险重复文献，然后进入标题摘要筛选。"
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH


TABLE_COLUMNS = (
    "record_id",
    "title",
    "authors",
    "first_author",
    "corresponding_author",
    "journal",
    "year_or_date",
    "doi",
    "pmid",
    "publication_type",
    "abstract",
    "source_database",
    "source_file",
    "import_batch",
    "duplicate_risk",
    "screening_status",
    "fulltext_status",
    "extraction_status",
)


def initial_literature_library_state(project_dir: Path | None = None) -> LiteratureLibraryState:
    return LiteratureLibraryState(
        title="Literature Library",
        status_label="Testing / Developer Preview",
        description="只读 Zotero-style 文献表格，汇总导入文献、重复风险和 workflow 状态，帮助 reviewer 进入去重和筛选。",
        project_dir=str(project_dir.expanduser().resolve()) if project_dir else "",
        empty_state="暂无 literature records。请先通过 Literature Import Wizard 导入 RIS / NBIB / CSV。",
        input_summary="输入：literature_records、legacy import records、duplicate groups、screening/fulltext/extraction artifacts。",
        output_summary="输出：只读文献表格状态；不删除、不合并、不修改正式 records。",
        next_step="检查 high/probable duplicate risk 后进入 Duplicate Review。",
        rows=(),
        total_records=0,
        high_duplicate_risk_count=0,
        probable_duplicate_count=0,
        possible_duplicate_count=0,
        no_obvious_duplicate_risk_count=0,
        table_columns=TABLE_COLUMNS,
        table_column_labels_zh=tuple(LITERATURE_TABLE_COLUMN_ZH[column] for column in TABLE_COLUMNS),
        warnings=("missing_literature_records",),
        testing_limitations=(
            "Developer Preview：绿色标签只表示未发现明显重复风险，不代表文献可信或质量高。",
            "本页面只读，不自动删除、合并或改变 screening/fulltext/extraction 状态。",
        ),
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
    )


def literature_library_state_from_project(project_dir: Path) -> LiteratureLibraryState:
    project_dir = project_dir.expanduser().resolve()
    records, record_warnings = _load_literature_records(project_dir)
    duplicate_lookup = _duplicate_lookup(project_dir)
    screening_lookup = _screening_lookup(project_dir)
    fulltext_lookup = _fulltext_lookup(project_dir)
    extraction_lookup = _extraction_lookup(project_dir)
    rows = tuple(
        _row_from_record(
            record,
            duplicate_lookup=duplicate_lookup,
            screening_lookup=screening_lookup,
            fulltext_lookup=fulltext_lookup,
            extraction_lookup=extraction_lookup,
        )
        for record in records
    )
    counts = {
        DUPLICATE_RISK_HIGH: len([row for row in rows if row.duplicate_risk == DUPLICATE_RISK_HIGH]),
        DUPLICATE_RISK_PROBABLE: len([row for row in rows if row.duplicate_risk == DUPLICATE_RISK_PROBABLE]),
        DUPLICATE_RISK_POSSIBLE: len([row for row in rows if row.duplicate_risk == DUPLICATE_RISK_POSSIBLE]),
        DUPLICATE_RISK_NONE: len([row for row in rows if row.duplicate_risk == DUPLICATE_RISK_NONE]),
    }
    warnings = list(record_warnings)
    if counts[DUPLICATE_RISK_HIGH]:
        warnings.append(f"high_duplicate_risk_records:{counts[DUPLICATE_RISK_HIGH]}")
    if counts[DUPLICATE_RISK_PROBABLE]:
        warnings.append(f"probable_duplicate_records:{counts[DUPLICATE_RISK_PROBABLE]}")
    return LiteratureLibraryState(
        title="Literature Library",
        status_label="Testing / Developer Preview",
        description="只读文献库表格：显示 title、authors、journal、DOI/PMID、来源、重复风险和当前 workflow 状态。",
        project_dir=str(project_dir),
        empty_state="" if rows else "暂无 literature records。请先通过 Literature Import Wizard 导入 RIS / NBIB / CSV。",
        input_summary="读取 literature/literature_records.json、literature_import/*_records.json、deduplication duplicate groups 和 workflow artifacts。",
        output_summary="输出只读表格状态；Duplicate Review 负责真正记录 reviewer decision。",
        next_step="先处理 high/probable duplicate risk，再进入 Title / Abstract Screening。",
        rows=rows,
        total_records=len(rows),
        high_duplicate_risk_count=counts[DUPLICATE_RISK_HIGH],
        probable_duplicate_count=counts[DUPLICATE_RISK_PROBABLE],
        possible_duplicate_count=counts[DUPLICATE_RISK_POSSIBLE],
        no_obvious_duplicate_risk_count=counts[DUPLICATE_RISK_NONE],
        table_columns=TABLE_COLUMNS,
        table_column_labels_zh=tuple(LITERATURE_TABLE_COLUMN_ZH[column] for column in TABLE_COLUMNS),
        warnings=tuple(warnings),
        testing_limitations=(
            "绿色标签含义是 no obvious duplicate risk，不代表文献质量或可信度。",
            "本阶段不做复杂批量编辑、不自动 merge、不自动 exclude。",
        ),
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh="显示题名、作者、期刊、DOI/PMID、来源、重复风险和当前流程状态。",
    )


def _load_literature_records(project_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    paths: list[Path] = []
    canonical = project_dir / "literature" / "literature_records.json"
    if canonical.exists():
        paths.append(canonical)
    paths.extend(sorted((project_dir / "literature_import").glob("*_records.json")))
    paths.extend(sorted((project_dir / "literature").glob("*_literature_records.json")))
    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for path in paths:
        payload = _load_json(path)
        for record in _records_from_payload(payload):
            record = dict(record)
            record.setdefault("source_file", str(path))
            record_id = str(record.get("record_id") or record.get("id") or record.get("pmid") or record.get("doi") or f"record-{len(records)+1}")
            record["record_id"] = record_id
            if record_id in seen:
                continue
            seen.add(record_id)
            records.append(record)
    if not records:
        warnings.append("missing_literature_records")
    return records, warnings


def _records_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("records", "literature_records", "imported_records"):
        value = payload.get(key)
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, dict)]
    return []


def _duplicate_lookup(project_dir: Path) -> dict[str, list[dict[str, Any]]]:
    lookup: dict[str, list[dict[str, Any]]] = {}
    for path in sorted((project_dir / "deduplication").glob("*duplicate*.json")):
        payload = _load_json(path)
        groups = payload.get("duplicate_groups") or payload.get("groups") or payload.get("candidate_groups") or []
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            record_ids = group.get("record_ids") or group.get("candidate_record_ids") or []
            if not isinstance(record_ids, list):
                continue
            for record_id in record_ids:
                lookup.setdefault(str(record_id), []).append(group)
    return lookup


def _screening_lookup(project_dir: Path) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for path in (project_dir / "screening").glob("*decisions*.json"):
        for item in _records_from_payload(_load_json(path)):
            record_id = str(item.get("record_id", ""))
            decision = str(item.get("decision") or item.get("screening_status") or item.get("status") or "")
            if record_id and decision:
                lookup[record_id] = decision
    return lookup


def _fulltext_lookup(project_dir: Path) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for path in (project_dir / "fulltext").glob("*.json"):
        payload = _load_json(path)
        items = payload.get("fulltext_files") or payload.get("records") or payload.get("decisions") or []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            record_id = str(item.get("record_id", ""))
            status = str(item.get("availability_status") or item.get("status") or item.get("decision") or "")
            if record_id and status:
                lookup[record_id] = status
    return lookup


def _extraction_lookup(project_dir: Path) -> dict[str, str]:
    lookup: dict[str, str] = {}
    payload = _load_json(project_dir / "extraction" / "extraction_records.json")
    records = payload.get("records") or payload.get("extraction_records") or []
    if isinstance(records, list):
        for item in records:
            if not isinstance(item, dict):
                continue
            record_id = str(item.get("record_id", ""))
            status = str(item.get("validation_status") or item.get("extraction_status") or "saved")
            if record_id:
                lookup[record_id] = status
    return lookup


def _row_from_record(
    record: dict[str, Any],
    *,
    duplicate_lookup: dict[str, list[dict[str, Any]]],
    screening_lookup: dict[str, str],
    fulltext_lookup: dict[str, str],
    extraction_lookup: dict[str, str],
) -> LiteratureLibraryRow:
    record_id = str(record.get("record_id", ""))
    duplicate_groups = duplicate_lookup.get(record_id, [])
    risk = _duplicate_risk(duplicate_groups)
    creators = record.get("creators", [])
    return LiteratureLibraryRow(
        record_id=record_id,
        title=_first_text(record, "title"),
        authors_text=_authors_text(record),
        first_author=_first_text(record, "first_author") or _first_author(creators),
        corresponding_author=_corresponding_author(creators),
        journal=_first_text(record, "journal", "publication_title"),
        year=_first_text(record, "year"),
        publication_date=_first_text(record, "date", "publication_date"),
        doi=_first_text(record, "doi"),
        pmid=_first_text(record, "pmid"),
        publication_type=_first_text(record, "publication_type") or "unknown",
        abstract_available=bool(_first_text(record, "abstract")),
        source_database=_first_text(record, "source_database", "source"),
        source_file=_first_text(record, "source_file"),
        import_batch_id=_first_text(record, "import_batch_id", "batch_id"),
        duplicate_risk=risk,
        duplicate_risk_label=_duplicate_risk_label(risk),
        duplicate_risk_label_zh=_duplicate_risk_label_zh(risk),
        duplicate_group_ids=tuple(str(group.get("group_id") or group.get("duplicate_group_id") or "") for group in duplicate_groups),
        duplicate_reasons=tuple(str(group.get("reason") or group.get("match_reason") or "") for group in duplicate_groups),
        screening_status=screening_lookup.get(record_id, _first_text(record, "screening_status") or "not_started"),
        fulltext_status=fulltext_lookup.get(record_id, _first_text(record, "fulltext_status") or "not_checked"),
        extraction_status=extraction_lookup.get(record_id, _first_text(record, "extraction_status") or "not_started"),
        row_status_color=_duplicate_risk_color(risk),
        row_status_color_zh=DUPLICATE_RISK_COLOR_ZH[_duplicate_risk_color(risk)],
    )


def _duplicate_risk(groups: list[dict[str, Any]]) -> str:
    if not groups:
        return DUPLICATE_RISK_NONE
    confidence = max((_float_value(group.get("confidence", 0)) for group in groups), default=0.0)
    reason_text = " ".join(str(group.get("reason") or group.get("match_reason") or "").lower() for group in groups)
    if any(token in reason_text for token in ("pmid", "doi", "clinicaltrials", "clinical_trials", "exact")) or confidence >= 0.95:
        return DUPLICATE_RISK_HIGH
    if confidence >= 0.75 or any(token in reason_text for token in ("title", "author", "year", "journal", "suspected")):
        return DUPLICATE_RISK_PROBABLE
    return DUPLICATE_RISK_POSSIBLE


def _duplicate_risk_label(risk: str) -> str:
    return {
        DUPLICATE_RISK_HIGH: "High duplicate risk",
        DUPLICATE_RISK_PROBABLE: "Probable duplicate / conflicting identifier",
        DUPLICATE_RISK_POSSIBLE: "Possible duplicate",
        DUPLICATE_RISK_NONE: "No obvious duplicate risk",
    }[risk]


def _duplicate_risk_label_zh(risk: str) -> str:
    return DUPLICATE_RISK_LABEL_ZH[risk]


def _duplicate_risk_color(risk: str) -> str:
    return {
        DUPLICATE_RISK_HIGH: "red",
        DUPLICATE_RISK_PROBABLE: "yellow",
        DUPLICATE_RISK_POSSIBLE: "gray",
        DUPLICATE_RISK_NONE: "green",
    }[risk]


def _authors_text(record: dict[str, Any]) -> str:
    authors_text = _first_text(record, "authors_text", "authors")
    if authors_text:
        if isinstance(record.get("authors"), list):
            return "; ".join(str(item) for item in record["authors"])
        return authors_text
    creators = record.get("creators", [])
    if isinstance(creators, list):
        return "; ".join(str(item.get("full_name") or item.get("raw") or "") for item in creators if isinstance(item, dict))
    return ""


def _first_author(creators: Any) -> str:
    if isinstance(creators, list):
        for creator in creators:
            if isinstance(creator, dict) and str(creator.get("creator_type", "author")) in {"author", "group_author"}:
                return str(creator.get("full_name") or creator.get("last_name") or creator.get("raw") or "")
    return ""


def _corresponding_author(creators: Any) -> str:
    if isinstance(creators, list):
        for creator in creators:
            if isinstance(creator, dict) and str(creator.get("creator_type", "")) == "corresponding_author":
                return str(creator.get("full_name") or creator.get("raw") or "")
    return ""


def _first_text(record: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, list):
            return "; ".join(str(item) for item in value if str(item).strip())
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


try:
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QLabel = QVBoxLayout = QWidget = None


if QWidget is not None:

    class LiteratureLibraryPage(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._state = initial_literature_library_state()
            root = QVBoxLayout(self)
            title = QLabel(f"{self._state.title_zh} · {self._state.status_label_zh}")
            title.setStyleSheet("font-size: 18px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(self._state.description_zh)
            description.setWordWrap(True)
            root.addWidget(description)
            note = QLabel(f"{self._state.empty_state}\n下一步：{self._state.next_step_zh}")
            note.setWordWrap(True)
            root.addWidget(note)

else:

    class LiteratureLibraryPage:  # type: ignore[no-redef]
        pass
