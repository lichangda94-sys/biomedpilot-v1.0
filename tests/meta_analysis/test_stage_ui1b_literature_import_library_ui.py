from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.literature_import_page import (
    import_diagnostics_visual_summary,
    initial_literature_import_wizard_state,
    preview_literature_import_files,
)
from app.meta_analysis.pages.literature_library_page import (
    DUPLICATE_RISK_HIGH,
    DUPLICATE_RISK_NONE,
    initial_literature_library_state,
    literature_library_state_from_project,
)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_ui1b_import_wizard_initial_state_is_chinese_friendly() -> None:
    state = initial_literature_import_wizard_state()

    assert state.title == "Literature Import Wizard"
    assert state.title_zh == "文献导入向导"
    assert "0.1.0-internal-beta" in state.status_label_zh
    assert state.current_step_zh == "选择来源"
    assert state.step_labels_zh == ("选择来源", "选择文件", "导入预览", "导入诊断", "进入去重审核")
    assert "Zotero 导出文件" in state.source_option_labels_zh
    assert "导入后人工审核" in state.dedup_mode_labels_zh
    assert state.next_step_zh == "导入成功后进入去重审核。"


def test_ui1b_import_preview_updates_chinese_step(tmp_path: Path) -> None:
    source = tmp_path / "records.csv"
    source.write_text("title,year\nA,2024\n", encoding="utf-8")

    state = preview_literature_import_files([str(source)])

    assert state.current_step == "import_preview"
    assert state.current_step_zh == "导入预览"
    assert state.previews[0].detected_format == "csv"


def test_ui1b_diagnostics_rows_keep_english_and_add_chinese_labels(tmp_path: Path) -> None:
    diagnostics_path = tmp_path / "batch_import_diagnostics.json"
    diagnostics_path.write_text(
        json.dumps(
            {
                "missing_title_count": 1,
                "missing_doi_count": 2,
                "duplicate_identifier_count": 1,
            }
        ),
        encoding="utf-8",
    )

    summary = import_diagnostics_visual_summary(str(diagnostics_path))
    cards = {card.key: card for card in summary.summary_cards}
    rows = {row.key: row for row in summary.warning_rows}

    assert cards["missing_title_count"].label == "Missing title"
    assert cards["missing_title_count"].label_zh == "缺标题"
    assert rows["missing_doi_count"].message
    assert rows["missing_doi_count"].message_zh.startswith("缺少 DOI")
    assert rows["duplicate_identifier_count"].label_zh == "重复标识符"


def test_ui1b_literature_library_initial_state_is_chinese_friendly(tmp_path: Path) -> None:
    state = initial_literature_library_state(tmp_path)

    assert state.title == "Literature Library"
    assert state.title_zh == "文献库表格"
    assert "0.1.0-internal-beta" in state.status_label_zh
    assert "中文友好" in state.description_zh
    assert "题名" in state.table_column_labels_zh
    assert "重复风险" in state.table_column_labels_zh
    assert state.next_step_zh.startswith("下一步")


def test_ui1b_literature_library_duplicate_risk_chinese_labels(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    write_json(
        project_dir / "literature" / "literature_records.json",
        {
            "records": [
                {"record_id": "rec-1", "title": "A", "authors_text": "Smith", "year": "2024"},
                {"record_id": "rec-2", "title": "B", "authors_text": "Lee", "year": "2023"},
            ]
        },
    )
    write_json(
        project_dir / "deduplication" / "duplicate_candidate_groups.json",
        {"duplicate_groups": [{"group_id": "dup-1", "record_ids": ["rec-1"], "reason": "doi_exact", "confidence": 0.99}]},
    )

    state = literature_library_state_from_project(project_dir)
    rows = {row.record_id: row for row in state.rows}

    assert rows["rec-1"].duplicate_risk == DUPLICATE_RISK_HIGH
    assert rows["rec-1"].duplicate_risk_label_zh == "高重复风险"
    assert rows["rec-1"].row_status_color_zh == "红色"
    assert rows["rec-2"].duplicate_risk == DUPLICATE_RISK_NONE
    assert rows["rec-2"].duplicate_risk_label_zh == "未发现明显重复风险"
    assert "可信" not in rows["rec-2"].duplicate_risk_label_zh
    assert state.description_zh.startswith("显示题名")
