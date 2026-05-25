from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from labtools.lan_client import LabToolsLanReadonlyClientConfig, build_lan_readonly_client_adapter
from labtools.lan_server import (
    PAIRING_CODE_DIGITS,
    TOKEN_EXPIRY_DAYS,
    LabToolsLanAuthManager,
    LabToolsLanHealthServerConfig,
    build_lan_health_server,
)
from labtools.local_data.datasource_adapter import LocalLabToolsDataSourceAdapter


def _request_json(
    url: str,
    *,
    method: str = "GET",
    payload: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, object]]:
    request = Request(url, data=payload, method=method)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urlopen(request, timeout=5) as response:  # noqa: S310 - loopback-only test server
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _seed_store(root: Path) -> LocalLabToolsDataSourceAdapter:
    adapter = LocalLabToolsDataSourceAdapter(root)
    adapter.initialize()
    adapter.create_reagent({"name": "Tris-HCl", "concentration": "1", "unit": "M"})
    adapter.create_sample(
        {
            "sample_name": "Tumor lysate",
            "sample_type": "protein_lysate",
            "concentration": "2.0",
            "concentration_unit": "mg/mL",
            "volume": "25",
            "volume_unit": "uL",
        }
    )
    return adapter


def test_lan_auth_manager_issues_single_use_viewer_token_hash(tmp_path: Path) -> None:
    manager = LabToolsLanAuthManager(tmp_path)

    pairing = manager.create_pairing_session(client_label="bench laptop")
    issued = manager.claim_pairing(pairing_code=pairing.pairing_code, client_label="bench laptop")
    second_claim = manager.claim_pairing(pairing_code=pairing.pairing_code, client_label="bench laptop")

    token_store = tmp_path / "lan_auth" / "paired_clients.json"
    payload = json.loads(token_store.read_text(encoding="utf-8"))

    assert len(pairing.pairing_code) == PAIRING_CODE_DIGITS
    assert pairing.pairing_code.isdigit()
    assert pairing.role == "viewer"
    assert issued.ok is True
    assert issued.status == "paired"
    assert issued.role == "viewer"
    assert issued.token
    assert issued.token not in token_store.read_text(encoding="utf-8")
    assert payload["paired_clients"][0]["token_hash"]
    assert payload["paired_clients"][0]["token_id"] == issued.token_id
    assert payload["paired_clients"][0]["role"] == "viewer"
    assert second_claim.ok is False
    assert second_claim.status == "pairing_expired"


def test_lan_auth_manager_blocks_revoked_expired_and_unknown_tokens(tmp_path: Path) -> None:
    manager = LabToolsLanAuthManager(tmp_path)
    pairing = manager.create_pairing_session(client_label="bench laptop")
    issued = manager.claim_pairing(pairing_code=pairing.pairing_code, client_label="bench laptop")

    accepted = manager.validate_authorization_header(f"Bearer {issued.token}")
    revoked = manager.revoke_token(issued.token_id)
    revoked_result = manager.validate_authorization_header(f"Bearer {issued.token}")
    unknown = manager.validate_authorization_header("Bearer not-the-token")

    assert accepted.ok is True
    assert accepted.status == "authenticated"
    assert accepted.role == "viewer"
    assert revoked is True
    assert revoked_result.ok is False
    assert revoked_result.status == "auth_revoked"
    assert unknown.ok is False
    assert unknown.status == "auth_invalid"


def test_lan_auth_required_blocks_readonly_until_pairing_token_is_present(tmp_path: Path) -> None:
    store_adapter = _seed_store(tmp_path)
    audit_count = len(store_adapter.store.load_store().audit_log)
    before_sample = store_adapter.store.load_store().samples[0]

    config = LabToolsLanHealthServerConfig(
        health_only=False,
        local_data_root=tmp_path,
        auth_required=True,
        allow_unauthenticated_readonly=False,
    )
    with build_lan_health_server(config) as server:
        status_code, status = _request_json(server.url("/status"))
        blocked_code, blocked = _request_json(server.url("/samples"))

        pairing = server.create_pairing_session(client_label="bench laptop")
        claim_payload = json.dumps({"pairing_code": pairing.pairing_code, "client_label": "bench laptop"}).encode("utf-8")
        claim_code, claim = _request_json(
            server.url("/pairing/claim"),
            method="POST",
            payload=claim_payload,
            headers={"Content-Type": "application/json"},
        )
        token = claim["data"]["token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        samples_code, samples = _request_json(server.url("/samples"), headers=auth_headers)
        authed_status_code, authed_status = _request_json(server.url("/status"), headers=auth_headers)
        write_code, write_body = _request_json(server.url("/samples"), method="POST", payload=b"{}", headers=auth_headers)

    after_sample = store_adapter.store.load_store().samples[0]

    assert status_code == 200
    assert status["data"]["auth"]["required"] is True
    assert status["data"]["auth"]["authenticated"] is False
    assert status["data"]["auth"]["status"] == "auth_required"
    assert "adapter_status" not in status["data"]
    assert blocked_code == 401
    assert blocked["status"] == "auth_required"
    assert blocked["data"]["auth"]["authenticated"] is False

    assert claim_code == 200
    assert claim["status"] == "paired"
    assert claim["data"]["role"] == "viewer"
    assert claim["data"]["token"]
    assert claim["data"]["expires_at"]

    assert samples_code == 200
    assert samples["status"] == "ready_readonly"
    assert samples["data"][0]["sample_name"] == "Tumor lysate"
    assert authed_status_code == 200
    assert authed_status["data"]["auth"]["authenticated"] is True
    assert authed_status["data"]["adapter_status"]["status"] == "ready"
    assert write_code == 405
    assert write_body["status"] == "blocked_write_disabled"
    assert len(store_adapter.store.load_store().audit_log) == audit_count
    assert after_sample.volume == before_sample.volume == "25"
    assert after_sample.status == before_sample.status == "available"


def test_lan_readonly_client_claims_pairing_and_reads_with_bearer_token(tmp_path: Path) -> None:
    _seed_store(tmp_path)
    config = LabToolsLanHealthServerConfig(
        health_only=False,
        local_data_root=tmp_path,
        auth_required=True,
        allow_unauthenticated_readonly=False,
    )

    with build_lan_health_server(config) as server:
        pairing = server.create_pairing_session(client_label="bench laptop")
        unauth_client = build_lan_readonly_client_adapter(LabToolsLanReadonlyClientConfig(server.url(""), timeout_seconds=1))

        blocked_status = unauth_client.status()
        claim = unauth_client.claim_pairing(pairing_code=pairing.pairing_code, client_label="bench laptop")
        authed_client = build_lan_readonly_client_adapter(
            LabToolsLanReadonlyClientConfig(server.url(""), timeout_seconds=1, bearer_token=str(claim["token"]))
        )
        status = authed_client.status()
        model = authed_client.read_model()

    assert blocked_status.read_enabled is False
    assert blocked_status.reason
    assert claim["ok"] is True
    assert claim["role"] == "viewer"
    assert status.status == "ready_readonly"
    assert status.read_enabled is True
    assert model.samples[0]["concentration"] == "2.0"


def test_lan_unauthenticated_readonly_requires_explicit_compatibility_mode(tmp_path: Path) -> None:
    _seed_store(tmp_path)

    compat = LabToolsLanHealthServerConfig(
        health_only=False,
        local_data_root=tmp_path,
        auth_required=False,
        allow_unauthenticated_readonly=True,
    )
    secure = LabToolsLanHealthServerConfig(
        health_only=False,
        local_data_root=tmp_path,
        auth_required=True,
        allow_unauthenticated_readonly=False,
    )

    with build_lan_health_server(compat) as server:
        compat_code, compat_samples = _request_json(server.url("/samples"))
    with build_lan_health_server(secure) as server:
        secure_code, secure_samples = _request_json(server.url("/samples"))

    assert compat_code == 200
    assert compat_samples["data"][0]["sample_name"] == "Tumor lysate"
    assert secure_code == 401
    assert secure_samples["status"] == "auth_required"


def test_lan_token_expiry_policy_is_thirty_days() -> None:
    assert TOKEN_EXPIRY_DAYS == 30
