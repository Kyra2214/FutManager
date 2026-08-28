"""Compatibilidade legada para o contrato canônico de eventos.

A implementação oficial vive em :mod:`p1_event_contract`. Este módulo
preserva apenas os nomes públicos antigos em português; não contém regras,
esquema ou persistência próprios.
"""

from engine.core.p1_event_contract import (
    audit_p1_events,
    ensure_p1_event_registry,
    persist_p1_event,
    protect_p1_event_mutation,
    read_p1_event_state,
    read_p1_events,
    validate_p1_event,
)

ensure_p1_evento_registry = ensure_p1_event_registry
validate_p1_evento = validate_p1_event
read_p1_eventos = read_p1_events
read_p1_evento_state = read_p1_event_state
persist_p1_evento = persist_p1_event
protect_p1_evento_mutation = protect_p1_event_mutation
audit_p1_eventos = audit_p1_events

__all__ = (
    "ensure_p1_evento_registry",
    "validate_p1_evento",
    "read_p1_eventos",
    "read_p1_evento_state",
    "persist_p1_evento",
    "protect_p1_evento_mutation",
    "audit_p1_eventos",
)
