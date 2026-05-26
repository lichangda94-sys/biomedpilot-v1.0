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
        "lan_feedback_location": str(default_storage_root() / "test_feedback" / "lan"),
    }


def lan_real_world_feedback_summary() -> dict[str, list[str] | str]:
    return {
        "goal": "在界面完成后，由真实用户在同一局域网内验证 LabTools LAN 只读 Host/Client、pairing/token、revoke 和边界提示。",
        "recommended_flow": [
            "Host 端在 LabTools 首页启动只读 LAN Host，默认使用 Auth required。",
            "Host 端创建 pairing code，并记录 server URL、端口和过期时间。",
            "Client 端手动输入 LAN URL，未配对时应 graceful block。",
            "Client 端输入 pairing code 保存本机只读 token。",
            "Client 端读取 reagent、sample、cell、freeze vial、record summary counts。",
            "Host 端查看 paired clients，并 revoke 该 client。",
            "Client 端再次连接，应提示 auth failed 并要求重新 pairing。",
            "显式切换 compatibility mode，确认风险提示可见且不是默认路径。",
        ],
        "boundary_checks": [
            "LAN 只读，不允许 reagent/sample/record 写入。",
            "不启用 LAN sync、cloud sync 或 automatic discovery。",
            "不自动扣减库存或样本体积。",
            "不生成 PDF/DOCX 或正式实验报告。",
            "测试报告只保存为本机 Markdown 文件，不自动发送网络请求。",
        ],
        "feedback_location": str(default_storage_root() / "test_feedback" / "lan"),
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


def generate_lan_feedback_template(output_dir: Path | None = None) -> Path:
    output_dir = output_dir or default_storage_root() / "test_feedback" / "lan"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = output_dir / f"biomedpilot_labtools_lan_feedback_{timestamp}.md"
    path.write_text(
        "\n".join(
            [
                "# BioMedPilot LabTools LAN Real-Use Feedback",
                "",
                "## Scope",
                "",
                "- Stage: post-UI real local-network user check",
                "- Mode: LabTools LAN read-only Host/Client",
                "- Boundary: no LAN writes, no sync, no cloud, no auto-discovery, no inventory/sample deduction",
                "- Delivery: attach this Markdown file plus screenshots/log paths to the development feedback thread",
                "",
                "## Tester And Environment",
                "",
                "- Tester name:",
                "- Test date:",
                "- Host device / OS:",
                "- Client device / OS:",
                "- App build or commit:",
                "- Network name or subnet:",
                "- Host LAN URL shown in UI:",
                "- Firewall or permission prompts:",
                "",
                "## Host Setup",
                "",
                "- Server mode used: Auth required / Compatibility mode",
                "- Pairing code created:",
                "- Pairing code expiry shown:",
                "- Paired clients list visible:",
                "- Revoke button visible:",
                "- Host boundary text visible: read-only / no sync / no writes",
                "",
                "## Client Connection",
                "",
                "- Saved token before test:",
                "- Unpaired read blocked gracefully:",
                "- Pairing succeeded:",
                "- Saved token role:",
                "- Saved token expires_at:",
                "- Clear saved token works:",
                "- Auth failed prompt asks user to pair again:",
                "",
                "## Read-only Data Check",
                "",
                "- Reagent count:",
                "- Sample count:",
                "- Cell profile count:",
                "- Freeze vial count:",
                "- Record summary count:",
                "- WB-compatible sample concentration visible:",
                "- Any page crashed or froze:",
                "",
                "## Revoke Check",
                "",
                "- Client selected on Host:",
                "- Revoke succeeded:",
                "- Revoked client read blocked gracefully:",
                "- Other paired client still readable, if tested:",
                "- Re-pairing after revoke succeeded:",
                "",
                "## Compatibility Mode Check",
                "",
                "- Compatibility mode was explicitly enabled:",
                "- Risk warning visible:",
                "- Compatibility mode was not the default:",
                "- Read-only data still visible:",
                "",
                "## Disabled Boundary Check",
                "",
                "- LAN write attempted:",
                "- LAN write result:",
                "- Sync/discovery controls present:",
                "- Any automatic inventory or sample deduction observed:",
                "- PDF/DOCX/formal report generated:",
                "",
                "## Issues",
                "",
                "- Severity:",
                "- What happened:",
                "- What you expected:",
                "- Steps to reproduce:",
                "- Screenshots or log paths:",
                "",
                "## Overall Result",
                "",
                "- Pass / Blocked / Needs redesign:",
                "- Must-fix before next LAN development:",
                "- Suggested UI wording changes:",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path
