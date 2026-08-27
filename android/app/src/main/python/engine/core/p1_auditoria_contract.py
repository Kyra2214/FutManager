"""Compatibilidade de importação para consumidores legados da auditoria.
A implementação canônica do lote atual está em p2_auditoria_contract.
"""
from .p2_auditoria_contract import *
from .p2_auditoria_contract import (
    ensure_p2_auditoria_registry as ensure_p1_auditoria_registry,
    validate_p1_auditoria as validate_p1_auditoria,
    read_p1_auditorias as read_p1_auditorias,
    protect_p1_auditoria_mutation as protect_p1_auditoria_mutation,
    audit_p2_auditorias as audit_p1_auditorias,
)
