# Protocolo de confirmação do mercado

O mercado possui dois contratos distintos: **prévia** e **confirmação**. A prévia `transfer_preview` é read-only e retorna caixa antes/depois, folha semanal projetada, custos imediatos e suficiência financeira. Ela não reserva caixa e não cria proposta.

A confirmação começa com `transfer_offer`, que persiste uma proposta vinculada à janela. A contraproposta `transfer_counter` cria um novo evento na mesma negociação e incrementa sua versão de negociação; somente a proposta em estado `PENDING` pode receber contraproposta. A aceitação não conclui o negócio: `transfer_approve` registra a aprovação do manager, e `transfer_complete` executa a mutação financeira e esportiva.

| Etapa | Escrita permitida | Fonte canônica |
|---|---|---|
| Prévia | Nenhuma | `club_economic_state`, folha e parâmetros persistidos |
| Oferta/contraproposta | Proposta e evento | `transfer_offers`, `transfer_events` |
| Aprovação | Aprovação vigente | `transfer_approvals` |
| Conclusão | Ledger, caixa, elenco e histórico | `FinanceLedger`, `club_economic_state`, `player_market_state`, `transfer_history` |

Propostas vencidas são marcadas `EXPIRED` pelo writer idempotente `expire_offers`. O histórico cronológico pode ser consultado por oferta e alertas expostos pelo gateway distinguem propostas pendentes e expiradas. Filtros de idade, posição, força e orçamento apenas restringem a leitura do catálogo.

A conclusão utiliza transação SQLite. A proposta é conferida novamente dentro da transação, a aprovação do manager é obrigatória, a janela e o clube atual são validados e os lançamentos financeiros são gravados antes da alteração do elenco. Qualquer falha provoca rollback integral; duas decisões concorrentes não podem concluir a mesma oferta porque o estado `COMPLETED` é verificado no writer.

> SQL/GameState é a única fonte da verdade. O frontend não calcula caixa, custos, regras de janela, comissão ou estado final da transferência.
