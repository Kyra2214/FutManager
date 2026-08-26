# P0-17 — Economia mundial

O `FinanceLedger` é a fonte única para lançamentos financeiros. O motor usa uma única moeda e referências naturais para impedir duplicidade. O fechamento mundial coordena patrocínios e folha semanal com chaves próprias de idempotência.

O `EconomyService` expõe receitas, despesas, orçamento, projeção de 39 semanas, reserva de segurança, alertas de caixa, obrigações, dívidas, saúde financeira e insolvência. Obrigações vencidas não são pagas sem saldo; ficam marcadas como `OVERDUE`. Investimentos e mudanças de controle são registrados no histórico financeiro, enquanto a auditoria de temporada persiste o relatório e a versão monetária.

A validação focada aprovou 17 testes sobre ledger, economia mundial, orquestração, patrocínios, integração financeira, idempotência, insolvência, rollback e limites do modelo. Não foram criados dados financeiros fictícios no GameState de produção.
