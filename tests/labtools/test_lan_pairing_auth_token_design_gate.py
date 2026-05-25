from __future__ import annotations

from pathlib import Path


DESIGN_PATH = Path("docs/labtools/LabTools_LAN_Pairing_Auth_Token_Design.md")


def test_pairing_auth_token_design_gate_exists_and_covers_required_decisions() -> None:
    text = DESIGN_PATH.read_text(encoding="utf-8")

    required_sections = [
        "## Pairing Model",
        "## Token Model",
        "## Token Storage",
        "## Future Request Auth",
        "## Auth Response Envelope",
        "## Audit Identity Mapping",
        "## UIShell Pairing UX",
        "## Migration Policy",
        "## Manual Checkpoint Before Runtime Auth",
    ]
    for section in required_sections:
        assert section in text
    for required_state in (
        "auth_required",
        "auth_invalid",
        "auth_expired",
        "auth_revoked",
        "pairing_required",
        "pairing_expired",
        "permission_denied",
        "auth_store_unavailable",
    ):
        assert required_state in text
    assert "No LAN write endpoints in this phase" in text
    assert "Server stores only a token hash" in text
    assert "UI pages must not import" in text


def test_pairing_auth_token_design_gate_does_not_implement_runtime_auth_yet() -> None:
    source_paths = [
        Path("labtools/lan_server/runtime.py"),
        Path("labtools/lan_client/readonly.py"),
        Path("labtools/lan_server/__main__.py"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in source_paths)

    assert "Authorization" not in combined
    assert "Bearer" not in combined
    assert "token_hash" not in combined
    assert "secrets." not in combined
    assert "pairing_code" not in combined


def test_pairing_auth_token_design_keeps_lan_writes_out_of_scope() -> None:
    design = DESIGN_PATH.read_text(encoding="utf-8")
    server = Path("labtools/lan_server/runtime.py").read_text(encoding="utf-8")

    assert "No LAN write endpoints in this phase." in design
    assert 'status="blocked_write_disabled"' in server
    assert "def do_POST" in server
    assert "def do_PUT" in server
    assert "def do_PATCH" in server
    assert "def do_DELETE" in server
