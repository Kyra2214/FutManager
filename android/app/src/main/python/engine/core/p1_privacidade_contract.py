"""Compatibilidade de importação para consumidores legados da privacidade.
A implementação canônica está em p2_privacidade_contract.
"""
from .p2_privacidade_contract import *
from .p2_privacidade_contract import (
    ensure_p2_privacidade_registry as ensure_p1_privacidade_registry,
    validate_p1_privacidade as validate_p1_privacidade,
    read_p1_privacidades as read_p1_privacidades,
    persist_p1_privacidade as persist_p1_privacidade,
    read_p1_privacidade_state as read_p1_privacidade_state,
    protect_p1_privacidade_mutation as protect_p1_privacidade_mutation,
    audit_p2_privacidades as audit_p1_privacidades,
)
