from __future__ import annotations

from enum import StrEnum


class DomainError(ValueError):
    def __init__(self, code: str | "DomainErrorCode", detail: str | None = None):
        self.code = code.value if isinstance(code, DomainErrorCode) else str(code)
        self.detail = detail
        super().__init__(self.code if detail is None else f"{self.code}:{detail}")


class DomainErrorCode(StrEnum):
    IMMUTABLE_BASE_DATABASE = "IMMUTABLE_BASE_DATABASE"
    SQL_GAMESTATE_SOURCE_OF_TRUTH_REQUIRED = "SQL_GAMESTATE_SOURCE_OF_TRUTH_REQUIRED"
    ROADMAP_GATE_CLOSED = "ROADMAP_GATE_CLOSED"
    ROADMAP_FRONT_NOT_FOUND = "ROADMAP_FRONT_NOT_FOUND"
    WEEK_OUT_OF_SEQUENCE = "WEEK_OUT_OF_SEQUENCE"
    ALREADY_PROCESSED = "ALREADY_PROCESSED"
    CLUB_NOT_FOUND = "CLUB_NOT_FOUND"
    PLAYER_NOT_FOUND = "PLAYER_NOT_FOUND"
    STADIUM_NOT_INITIALIZED = "STADIUM_NOT_INITIALIZED"
    INSUFFICIENT_CASH = "INSUFFICIENT_CASH"
    INVALID_TICKET_PRICE = "INVALID_TICKET_PRICE"
    INVALID_STADIUM_LEVEL = "INVALID_STADIUM_LEVEL"
    INSTITUTIONAL_PROFILE_NOT_INITIALIZED = "INSTITUTIONAL_PROFILE_NOT_INITIALIZED"
    MATCH_NOT_FOUND = "MATCH_NOT_FOUND"
    MATCH_NOT_PLAYED = "MATCH_NOT_PLAYED"
    SPONSOR_OFFER_NOT_FOUND = "SPONSOR_OFFER_NOT_FOUND"
    SPONSOR_OFFER_UNAVAILABLE = "SPONSOR_OFFER_UNAVAILABLE"
    SPONSOR_CONTRACT_ACTIVE = "SPONSOR_CONTRACT_ACTIVE"
    SPONSOR_REQUIREMENT_NOT_MET = "SPONSOR_REQUIREMENT_NOT_MET"


def error_code(value: object) -> str:
    """Normalize enum/string/domain exceptions for stable gateway serialization."""
    if isinstance(value, DomainError):
        return value.code if value.detail is None else f"{value.code}:{value.detail}"
    return value.value if isinstance(value, DomainErrorCode) else str(value)
