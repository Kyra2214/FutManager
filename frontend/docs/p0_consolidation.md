# Consolidação dos P0 do roadmap 941–3940

A consolidação P0 transforma os 300 itens P0 em contratos verificáveis no próprio GameState SQLite. Cada domínio possui dez ações canônicas: definir contrato, validar regras, persistir estado, expor leitura, proteger mutação, auditar fluxo, otimizar consulta, simular cenário, documentar ciclo e testar integração.

O registro é criado idempotentemente por `ManagerService` em `roadmap_p0_contracts`, com `item_id` único, domínio, ação, versão de esquema, estado `CONSOLIDATED` e `source_of_truth = SQL_GAMESTATE`. As auditorias ficam em `roadmap_p0_contract_audit`. Índices cobrem consultas por domínio/ação/status e por item/auditoria.

A consolidação não cria jogadores, clubes, resultados, saldos ou avaliações artificiais. Ela governa o contrato e o caminho de persistência; as regras específicas continuam nos serviços existentes do motor. O frontend permanece editorial e não recebe autorização para mutar esses contratos: `protect_p0_mutation` aceita somente o ator explícito `AUTHORIZED_SQL_SERVICE`.

O gateway expõe leitura (`p0_contracts`), validação (`p0_contract_validate`), proteção (`p0_contract_protect`) e auditoria (`p0_contract_audit`). A auditoria exige 300 itens, IDs únicos, estado consolidado, JSON íntegro, domínio conhecido, ação conhecida e fonte SQL/GameState.

## Evidências

| Controle | Evidência |
|---|---|
| Registro persistido e idempotente | `brasfoot_engine/engine/core/p0_contracts.py` |
| Inicialização no GameState | `brasfoot_engine/engine/manager/career.py` |
| Exposição pelo gateway | `brasfoot_engine/scripts/career_gateway.py` |
| Testes de contrato e proteção | `brasfoot_engine/tests/test_p0_contracts.py` |
| Manifesto de execução | `docs/roadmap_3000_execucao.json` |
| Guard P0/P1/P2 | `brasfoot_engine/scripts/career_gateway.py:_roadmap_3000_guard` |

O `P0_GLOBAL_GATE` somente é aberto no manifesto após todos os 300 itens P0 terem status `DONE`, com evidências apontando para este contrato, seus testes e a auditoria do GameState.
