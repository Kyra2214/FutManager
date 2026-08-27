# Lote P1 1081–1090 — migração

O domínio 02 ganhou o registro `roadmap_p1_migrations` no GameState SQLite. O contrato define migração, versão, ação, estado consolidado e fonte `SQL_GAMESTATE`; a inicialização é idempotente e cria índices de consulta e auditoria.

A leitura, validação e auditoria são read-only. A proteção de mutação exige `AUTHORIZED_SQL_SERVICE` e rejeita o frontend com `DomainError`. Evidências: `brasfoot_engine/engine/core/p1_migration_contract.py`, `engine/manager/career.py`, `scripts/career_gateway.py` e `tests/test_p1_migration_contract.py`.
