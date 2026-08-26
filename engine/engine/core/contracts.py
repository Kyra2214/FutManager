from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class ReadRepository(Protocol):
    """Contrato de leitura: consultas não iniciam transações nem alteram o GameState."""

    def fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> Any: ...
    def fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[Any]: ...


class CommandService(Protocol):
    """Contrato de comando: mutações delegadas a serviço com contexto transacional."""

    def execute(self, context: Any, managed_transaction: bool = True) -> Any: ...


@dataclass(frozen=True)
class ContractBoundary:
    read_side: str = 'ReadRepository'
    command_side: str = 'CommandService'
    source_of_truth: str = 'SQL/GameState'
    frontend_boundary: str = 'tRPC/Gateway'
