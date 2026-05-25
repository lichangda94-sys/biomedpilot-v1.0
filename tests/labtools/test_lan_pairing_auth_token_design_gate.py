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
        "## LT9 Runtime Prototype",
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


def test_pairing_auth_token_runtime_prototype_implements_controlled_readonly_auth() -> None:
    source_paths = [
        Path("labtools/lan_server/auth.py"),
        Path("labtools/lan_server/runtime.py"),
        Path("labtools/lan_client/readonly.py"),
        Path("labtools/lan_server/__main__.py"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in source_paths)

    assert "Authorization" in combined
    assert "Bearer" in combined
    assert "token_hash" in combined
    assert "secrets." in combined
    assert "pairing_code" in combined
    assert "allow_unauthenticated_readonly" in combined
    assert "viewer" in combined


def test_pairing_auth_token_design_keeps_lan_writes_out_of_scope() -> None:
    design = DESIGN_PATH.read_text(encoding="utf-8")
    server = Path("labtools/lan_server/runtime.py").read_text(encoding="utf-8")

    assert "No LAN write endpoints in this phase." in design
    assert 'status="blocked_write_disabled"' in server
    assert "def do_POST" in server
    assert "def do_PUT" in server
    assert "def do_PATCH" in server
    assert "def do_DELETE" in server
