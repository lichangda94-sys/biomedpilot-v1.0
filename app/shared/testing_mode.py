from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.shared.feature_availability import FeatureAvailabilityStatus, features_by_status
from app.shared.storage import default_storage_root


def testing_mode_summary() -> dict[str, list[str] | str]:
    open_or_testing = [
        feature.display_label()
        for status in (FeatureAvailabilityStatus.OPEN, FeatureAvailabilityStatus.TESTING)
        for feature in features_by_status(status)
    ]
    unavailable = [
        feature.display_label()
        for status in (FeatureAvailabilityStatus.PLACEHOLDER, FeatureAvailabilityStatus.UNAVAILABLE)
        for feature in features_by_status(status)
    ]
    return {
        "goal": "验证 BioMedPilot Dashboard、项目创建、两个工作台入口、功能状态说明和反馈流程是否清楚可用。",
        "recommended_flow": [
            "启动软件并查看 Dashboard。",
            "新建一个生信分析项目，确认进入生信分析工作台。",
            "返回 Dashboard，新建一个 Meta 分析项目，确认进入 Meta 分析工作台。",
            "查看各步骤的状态、legacy 来源和下一步说明。",
            "打开测试模式页面并生成反馈模板。",
        ],
        "testable_features": open_or_testing,
        "unavailable_features": unavailable,
        "known_limitations": [
            "当前不测试正式差异分析、富集分析、相关性分析、生存分析和完整 Meta 统计执行。",
            "legacy 功能先以状态入口和 adapter 形式接入，尚未全部嵌入统一界面。",
            "打包入口仍是占位。",
        ],
        "feedback_location": str(default_storage_root() / "test_feedback"),
    }


def generate_feedback_template(output_dir: Path | None = None) -> Path:
    output_dir = output_dir or default_storage_root() / "test_feedback"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = output_dir / f"biomedpilot_feedback_{timestamp}.md"
    path.write_text(
        "\n".join(
            [
                "# BioMedPilot Test Feedback",
                "",
                "## Tester",
                "",
                "- Name:",
                "- Date:",
                "- Operating system:",
                "",
                "## Startup",
                "",
                "- Startup command:",
                "- Did the Dashboard open:",
                "- Error message, if any:",
                "",
                "## Project Creation",
                "",
                "- Bioinformatics project created:",
                "- Meta Analysis project created:",
                "- Recent projects shown correctly:",
                "",
                "## Workspace Review",
                "",
                "- Bioinformatics steps were clear:",
                "- Meta Analysis steps were clear:",
                "- Feature status labels were clear:",
                "",
                "## Issues",
                "",
                "- What happened:",
                "- What you expected:",
                "- Steps to reproduce:",
                "",
                "## Screenshots or Files",
                "",
                "- Attach paths or notes:",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path

