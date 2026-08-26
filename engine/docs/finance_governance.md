# Governança financeira do FutManager

O saldo oficial do clube é o campo `club_economic_state.cash`, movimentado por serviços transacionais do motor e refletido no `FinanceLedger`. O frontend e os read models não gravam saldos; apenas consultam dados persistidos. A tabela `club_finances` pode existir em bancos legados exclusivamente como espelho de compatibilidade.

## Histórico sazonal

`FinanceLedger.report_club(club_id, season)` e `EconomyService.audit_season(season)` são as consultas canônicas para histórico por temporada. O contrato tRPC `club.financeHistory` expõe a auditoria persistida, enquanto `club.financeLedger` expõe os lançamentos brutos filtráveis por temporada e categoria.

## Arredondamento

Valores monetários são persistidos como inteiros na unidade monetária do jogo. Projeções que exigem divisão usam arredondamento explícito no read model (`Math.round` no frontend apenas para apresentação não é permitido; o valor já chega derivado do backend). O motor usa conversão inteira determinística e registra a versão da fórmula nas prévias (`transfer-impact-v1`, `expense-preview-v1` e `post-match-preview-v1`).

## Concorrência e idempotência

Operações mutáveis do ciclo semanal e transferências usam transações SQLite e chaves naturais de referência no ledger. Reprocessamentos do mesmo tick não duplicam lançamentos. Pré-visualizações são deliberadamente não persistentes e não reservam caixa; a confirmação deve revalidar saldo dentro da transação autorizada.

## Auditoria

A suíte Python cobre ledger, economia mundial, ciclo semanal, idempotência, rollback e transferências. A suíte Vitest cobre gateway, read model, router e interface. Alterações na política econômica devem atualizar primeiro o motor e seus testes, depois os contratos de leitura e por último a interface.
