from __future__ import annotations

import json
from typing import Any


MAX_PAYLOAD_BYTES = 128 * 1024


def validate_payload(action: str, payload: Any) -> dict[str, Any]:
    """Normaliza e valida o envelope recebido pelo gateway antes do dispatch."""
    if not isinstance(action, str) or not action.strip():
        raise ValueError("PAYLOAD_ACTION_REQUIRED")
    if not isinstance(payload, dict):
        raise ValueError("PAYLOAD_OBJECT_REQUIRED")
    try:
        normalized = json.loads(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    except (TypeError, ValueError) as error:
        raise ValueError("PAYLOAD_JSON_INVALID") from error
    encoded = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_PAYLOAD_BYTES:
        raise ValueError("PAYLOAD_TOO_LARGE")
    return normalized


def payload_fingerprint(action: str, payload: dict[str, Any]) -> str:
    import hashlib

    normalized = validate_payload(action, payload)
    canonical = json.dumps({"action": action, "payload": normalized}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
