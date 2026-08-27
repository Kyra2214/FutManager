# Lote P1 1051–1060 — procedures do gateway

Os itens 1051–1060 correspondem ao ciclo completo de `procedure` do domínio 02, Gateway e contratos. O ciclo foi consolidado em `roadmap_p1_procedures`, persistido no mesmo GameState SQLite inicializado pelo `ManagerService`.

Cada item tem ID único, ação canônica, nome `career_gateway`, estado `CONSOLIDATED`, versão de esquema e `source_of_truth = SQL_GAMESTATE`. A leitura é read-only e a mutação passa por proteção explícita: somente `AUTHORIZED_SQL_SERVICE` pode ser aceito; o frontend recebe erro de domínio estável quando tenta escrever.

## Evidências verificadas

| Item | Ação | Evidência |
|---|---|---|
| 1051 | definir contrato | `brasfoot_engine/engine/core/p1_procedure_contract.py` |
| 1052 | validar regras | `brasfoot_engine/tests/test_p1_procedure_contract.py` |
| 1053 | persistir estado | `brasfoot_engine/engine/manager/career.py` |
| 1054 | expor leitura | `brasfoot_engine/scripts/career_gateway.py` |
| 1055 | proteger mutação | `brasfoot_engine/engine/core/p1_procedure_contract.py` |
| 1056 | auditar fluxo | `brasfoot_engine/engine/core/p1_procedure_contract.py` |
| 1057 | otimizar consulta | índices SQL no módulo do contrato |
| 1058 | simular cenário | teste de inicialização idempotente |
| 1059 | documentar ciclo | este documento |
| 1060 | testar integração | teste do gateway real em SQLite temporário |

A auditoria do endpoint `p1_procedure_audit` confirmou dez contratos, IDs 1051–1060, JSON válido, fonte SQL/GameState e leitura somente leitura. O `P0_GLOBAL_GATE` permaneceu aberto e o `P1_GLOBAL_GATE` permaneceu fechado, pois os demais itens P1 ainda não foram consolidados.
