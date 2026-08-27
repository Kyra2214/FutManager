# Lote P1 1111–1120 — Telemetria

O lote implementa telemetria do domínio 02 no GameState SQLite, sem criar estado paralelo no frontend ou no dispatcher.

| Itens | Contrato | Evidência |
|---|---|---|
| 1111–1112 | Registro canônico e regras de validação | `engine/core/p1_telemetry_contract.py`, `tests/test_p1_telemetry_contract.py` |
| 1113–1114 | Persistência idempotente e leitura limitada | Tabelas `roadmap_p1_telemetry_contracts` e `roadmap_p1_telemetry_events` |
| 1115–1116 | Proteção de mutação e auditoria read-only | `AUTHORIZED_SQL_SERVICE`, auditoria SQL e `audit_p1_telemetry` |
| 1117–1118 | Índice por evento/carreira/ciclo e cenário idempotente | `idx_p1_telemetry_events_lookup`, teste `tick-1` |
| 1119–1120 | Documentação e integração no gateway | `scripts/career_gateway.py`, este documento e testes focados |

A telemetria aceita apenas payload JSON-objeto, exige `event_key` e `event_name`, calcula SHA-256 do payload e usa `INSERT OR IGNORE` para impedir duplicidade. A leitura é somente consulta SQL e limita o volume retornado a 500 eventos. Mutações sem o ator `AUTHORIZED_SQL_SERVICE` geram o erro de autorização de domínio.

Validação executada: 8 testes Python focados, compilação Python, typecheck TypeScript e build do frontend aprovados. O gate P1 continua governado pelo manifesto; o lote só é marcado como concluído após a atualização de evidências dos dez itens.
