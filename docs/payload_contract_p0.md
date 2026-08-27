# Contrato de payload do gateway

O `career_gateway.py` recebe um objeto JSON como envelope de entrada. Antes do dispatch, `engine/core/payload_contract.py` normaliza chaves e valores em JSON determinístico, rejeita ações vazias, payloads que não sejam objetos, valores não serializáveis e envelopes acima de 128 KiB. A impressão digital SHA-256 cobre ação e payload normalizado e é retornada no envelope de sucesso.

A validação acontece no único ponto de entrada do gateway. Nenhuma regra de domínio ou escrita é movida para o frontend: o dispatcher continua encaminhando operações ao `ManagerService` e aos serviços autorizados que persistem no GameState SQLite.

A leitura do journal de carreira usa sequência por save e payload JSON, com auditoria read-only de ordem, escopo de carreira, escopo de manager e validade do JSON. Eventos repetidos com os mesmos campos são idempotentes e não criam uma segunda entrada.

## Evidências

| Controle | Evidência |
|---|---|
| Contrato e normalização | `brasfoot_engine/engine/core/payload_contract.py` |
| Validação no gateway | `brasfoot_engine/scripts/career_gateway.py:515-522` |
| Persistência do journal | `brasfoot_engine/engine/manager/career.py:39-40,131-171` |
| Testes P0 | `brasfoot_engine/tests/test_payload_contract_p0.py` |
| Testes de journal | `brasfoot_engine/tests/test_parallel_career_league.py:test_journal_is_sequenced_scoped_and_idempotent` |
| Validação executada | `3 testes de payload + 9 testes de governança/gateway; typecheck e Vitest do gateway aprovados` |

O gate permanece fechado enquanto existirem itens P0 pendentes. Portanto, este lote não libera P1 ou P2 por conta própria.
