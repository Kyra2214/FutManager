"""Compatibilidade de importação para consumidores legados do replay.
A implementação canônica do lote atual está em p2_replay_contract.
"""
from .p2_replay_contract import *
from .p2_replay_contract import (
    ensure_p2_replay_registry as ensure_p1_replay_registry,
    validate_p1_replay as validate_p1_replay,
    read_p1_replays as read_p1_replays,
    persist_p1_replay as persist_p1_replay,
    read_p1_replay_state as read_p1_replay_state,
    audit_p2_replays as audit_p1_replays,
    protect_p1_replay_mutation as protect_p1_replay_mutation,
    audit_p2_replay_flow as audit_p1_replay_flow,
)
