from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from labtools.local_data.paths import resolve_labtools_local_data_paths


LAN_AUTH_SCHEMA_VERSION = "labtools_lan_auth.v1"
PAIRING_CODE_DIGITS = 8
PAIRING_EXPIRY_MINUTES = 10
TOKEN_EXPIRY_DAYS = 30
VIEWER_ROLE = "viewer"


@dataclass(frozen=True)
class LabToolsLanPairingSession:
    pairing_code: str
    client_label: str
    expires_at: str
    role: str = VIEWER_ROLE


@dataclass(frozen=True)
class LabToolsLanTokenIssueResult:
    ok: bool
    status: str
    reason: str
    token: str = ""
    token_id: str = ""
    client_label: str = ""
    role: str = VIEWER_ROLE
    expires_at: str = ""


@dataclass(frozen=True)
class LabToolsLanAuthResult:
    ok: bool
    status: str
    reason: str
    token_id: str = ""
    client_label: str = ""
    role: str = VIEWER_ROLE


@dataclass(frozen=True)
class LabToolsLanPairedClient:
    token_id: str
    client_label: str
    role: str
    created_at: str
    expires_at: str
    last_seen_at: str = ""
    revoked_at: str = ""

    @property
    def revoked(self) -> bool:
        return bool(self.revoked_at.strip())

    @property
    def expired(self) -> bool:
        return _parse_iso(self.expires_at) <= _utc_now()


class LabToolsLanAuthManager:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = resolve_labtools_local_data_paths(root).root
        self.auth_root = self.root / "lan_auth"
        self.token_store = self.auth_root / "paired_clients.json"
        self._pairing_sessions: dict[str, dict[str, Any]] = {}

    def create_pairing_session(self, *, client_label: str = "manual-client") -> LabToolsLanPairingSession:
        now = _utc_now()
        pairing_code = _new_pairing_code()
        expires_at = _iso(now + timedelta(minutes=PAIRING_EXPIRY_MINUTES))
        self._pairing_sessions[pairing_code] = {
            "client_label": _clean_label(client_label),
            "expires_at": expires_at,
            "role": VIEWER_ROLE,
            "used": False,
        }
        return LabToolsLanPairingSession(
            pairing_code=pairing_code,
            client_label=_clean_label(client_label),
            expires_at=expires_at,
        )

    def claim_pairing(self, *, pairing_code: str, client_label: str = "manual-client") -> LabToolsLanTokenIssueResult:
        code = str(pairing_code or "").strip()
        session = self._pairing_sessions.get(code)
        if session is None:
            return LabToolsLanTokenIssueResult(False, "pairing_required", "Pairing code is unknown or has not been created.")
        if bool(session.get("used")):
            return LabToolsLanTokenIssueResult(False, "pairing_expired", "Pairing code has already been used.")
        if _parse_iso(str(session.get("expires_at", ""))) <= _utc_now():
            return LabToolsLanTokenIssueResult(False, "pairing_expired", "Pairing code has expired.")
        token = secrets.token_urlsafe(32)
        token_id = f"lan_token_{secrets.token_hex(8)}"
        expires_at = _iso(_utc_now() + timedelta(days=TOKEN_EXPIRY_DAYS))
        label = _clean_label(client_label) or str(session.get("client_label") or "manual-client")
        record = {
            "token_id": token_id,
            "token_hash": _hash_token(token),
            "client_label": label,
            "role": VIEWER_ROLE,
            "created_at": _iso(_utc_now()),
            "expires_at": expires_at,
            "last_seen_at": "",
            "revoked_at": "",
            "created_by": "local_host",
            "notes": "LAN read-only viewer token.",
        }
        payload = self._load_payload(create_missing=True)
        records = [item for item in payload.get("paired_clients", []) if isinstance(item, dict)]
        records.append(record)
        payload["paired_clients"] = records
        self._save_payload(payload)
        session["used"] = True
        return LabToolsLanTokenIssueResult(
            ok=True,
            status="paired",
            reason="LAN read-only viewer token issued.",
            token=token,
            token_id=token_id,
            client_label=label,
            role=VIEWER_ROLE,
            expires_at=expires_at,
        )

    def validate_authorization_header(self, header_value: str | None) -> LabToolsLanAuthResult:
        header = str(header_value or "").strip()
        if not header:
            return LabToolsLanAuthResult(False, "auth_required", "LAN read summaries require a paired client token.")
        if not header.startswith("Bearer "):
            return LabToolsLanAuthResult(False, "auth_invalid", "LAN auth header must use Bearer token format.")
        token = header.removeprefix("Bearer ").strip()
        if not token:
            return LabToolsLanAuthResult(False, "auth_invalid", "LAN bearer token is empty.")
        try:
            payload = self._load_payload(create_missing=False)
        except Exception:
            return LabToolsLanAuthResult(False, "auth_store_unavailable", "LAN auth token store is unavailable.")
        token_hash = _hash_token(token)
        for record in payload.get("paired_clients", []):
            if not isinstance(record, Mapping) or record.get("token_hash") != token_hash:
                continue
            if str(record.get("revoked_at") or "").strip():
                return LabToolsLanAuthResult(False, "auth_revoked", "LAN token has been revoked.")
            if _parse_iso(str(record.get("expires_at") or "")) <= _utc_now():
                return LabToolsLanAuthResult(False, "auth_expired", "LAN token has expired.")
            role = str(record.get("role") or VIEWER_ROLE)
            if role != VIEWER_ROLE:
                return LabToolsLanAuthResult(False, "permission_denied", "LAN token role is not allowed for read-only summaries.")
            return LabToolsLanAuthResult(
                True,
                "authenticated",
                "LAN read-only viewer token accepted.",
                token_id=str(record.get("token_id") or ""),
                client_label=str(record.get("client_label") or ""),
                role=role,
            )
        return LabToolsLanAuthResult(False, "auth_invalid", "LAN token is unknown.")

    def list_paired_clients(self, *, include_revoked: bool = True) -> tuple[LabToolsLanPairedClient, ...]:
        payload = self._load_payload(create_missing=False)
        clients: list[LabToolsLanPairedClient] = []
        for record in payload.get("paired_clients", []):
            if not isinstance(record, Mapping):
                continue
            client = LabToolsLanPairedClient(
                token_id=str(record.get("token_id") or ""),
                client_label=str(record.get("client_label") or ""),
                role=str(record.get("role") or VIEWER_ROLE),
                created_at=str(record.get("created_at") or ""),
                expires_at=str(record.get("expires_at") or ""),
                last_seen_at=str(record.get("last_seen_at") or ""),
                revoked_at=str(record.get("revoked_at") or ""),
            )
            if client.token_id and (include_revoked or not client.revoked):
                clients.append(client)
        return tuple(clients)

    def revoke_token(self, token_id: str) -> bool:
        payload = self._load_payload(create_missing=False)
        updated = False
        records = []
        for record in payload.get("paired_clients", []):
            if not isinstance(record, dict):
                continue
            if record.get("token_id") == token_id and not record.get("revoked_at"):
                record = {**record, "revoked_at": _iso(_utc_now())}
                updated = True
            records.append(record)
        if updated:
            payload["paired_clients"] = records
            self._save_payload(payload)
        return updated

    def _load_payload(self, *, create_missing: bool) -> dict[str, Any]:
        if not self.token_store.exists():
            if not create_missing:
                return {"schema_version": LAN_AUTH_SCHEMA_VERSION, "paired_clients": []}
            return {"schema_version": LAN_AUTH_SCHEMA_VERSION, "paired_clients": []}
        payload = json.loads(self.token_store.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("LAN auth token store must contain a JSON object.")
        if payload.get("schema_version") != LAN_AUTH_SCHEMA_VERSION:
            raise ValueError("LAN auth token store schema mismatch.")
        clients = payload.get("paired_clients")
        if not isinstance(clients, list):
            raise ValueError("LAN auth token store missing paired_clients list.")
        return payload

    def _save_payload(self, payload: dict[str, Any]) -> None:
        self.auth_root.mkdir(parents=True, exist_ok=True)
        tmp_path = self.token_store.with_name(f".{self.token_store.name}.tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp_path.replace(self.token_store)


def _new_pairing_code() -> str:
    return f"{secrets.randbelow(10 ** PAIRING_CODE_DIGITS):0{PAIRING_CODE_DIGITS}d}"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_iso(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.fromtimestamp(0, tz=timezone.utc)


def _clean_label(value: str) -> str:
    return str(value or "manual-client").strip()[:80] or "manual-client"
