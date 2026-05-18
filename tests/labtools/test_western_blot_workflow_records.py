from __future__ import annotations


def test_western_blot_workflow_steps_match_requested_order() -> None:
    from app.labtools.western_blot import WB_WORKFLOW_STEPS

    assert [label for _step_id, label in WB_WORKFLOW_STEPS] == [
        "蛋白样品准备",
        "BCA 蛋白浓度测定",
        "蛋白上样计算",
        "配胶与 Lane 布局",
        "电泳记录",
        "电转记录",
        "封闭记录",
        "一抗孵育记录",
        "一抗后洗膜记录",
        "二抗孵育记录",
        "二抗后洗膜记录",
        "显影/成像记录",
        "结果与灰度分析",
    ]


def test_western_blot_workflow_record_store_round_trips_structured_sop_and_free_text(tmp_path) -> None:
    from app.labtools.western_blot import WB_REVIEW_NOTICE, WBWorkflowRecord, WBWorkflowRecordStore

    store = WBWorkflowRecordStore(tmp_path / "wb_workflow_records.json")
    saved = store.save_record(
        WBWorkflowRecord(
            step_id="primary_antibody",
            step_label="一抗孵育记录",
            fields={"靶蛋白名称": "GAPDH", "抗体稀释比例": "1:5000"},
            sop_text="按实验室 SOP 孵育。",
            free_text="本次 4C overnight。",
        )
    )

    loaded = store.latest_for_step("primary_antibody")

    assert loaded is not None
    assert loaded.record_id == saved.record_id
    assert loaded.fields["靶蛋白名称"] == "GAPDH"
    assert "按实验室 SOP 孵育" in loaded.sop_text
    assert "4C overnight" in loaded.free_text
    assert WB_REVIEW_NOTICE in loaded.as_text()
