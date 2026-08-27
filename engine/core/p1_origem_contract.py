"""Compatibilidade de importação para consumidores legados da origem.
A implementação canônica está em p2_origem_contract.
"""
from .p2_origem_contract import *
from .p2_origem_contract import (
    ensure_p2_origem_registry as ensure_p1_origem_registry,
    validate_p1_origem as validate_p1_origem,
    read_p1_identities as read_p1_origens,
    persist_p1_origem as persist_p1_origem,
    read_p1_origem_state as read_p1_origem_state,
    protect_p1_origem_mutation as protect_p1_origem_mutation,
    audit_p1_identities as audit_p1_origens,
)
