# Roadmap 5 — Orquestração, tempo e contabilidade integrada

O motor agora possui um relógio lógico independente do relógio do dispositivo. `LogicalClock` mantém data, semana, mês, temporada e último tick processado. `WorldTickContext` é compartilhado por todos os serviços chamados no avanço.

`IntegrationOrchestrator` coordena obrigações sem absorver as regras internas: contratos fornecem salários ou receitas, patrocinadores fornecem receitas e estruturas fornecem manutenção. O ledger registra cada lançamento com clube, data, temporada, semana, categoria, valor, origem e tick.

A operação `advance_week()` cria o contexto, processa obrigações ativas, atualiza caixa, avança o relógio e registra auditoria dentro de uma única transação. Falhas provocam rollback. O ledger usa uma chave única por clube, temporada, semana, categoria, origem e origem específica, impedindo que o mesmo lançamento seja contabilizado novamente ao reprocessar um tick.

## Escopo atual

| Sistema | Situação |
|---|---|
| Relógio lógico | Implementado |
| Contexto temporal | Implementado |
| Ledger financeiro | Implementado |
| Contratos semanais | Implementado como obrigações genéricas |
| Patrocínios semanais | Implementado como contratos de receita |
| Manutenção de departamentos | Implementada como obrigação semanal |
| Idempotência | Implementada no lançamento e no caixa |
| Rollback | Implementado |
| Partidas e campeonatos | Fora do escopo |
| Mercado automático e IA | Fora do escopo |

A fonte `data/database/game.db` continua imutável. Todas as tabelas de orquestração e contabilidade pertencem a `data/state/game.db`.
