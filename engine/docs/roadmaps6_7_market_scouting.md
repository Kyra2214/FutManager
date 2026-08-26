# Roadmaps 6 e 7 — Mercado, transferências e scouting

Esta etapa adiciona mercado persistente e scouting ao motor, sem frontend, partidas ou simulação global.

## Mercado

`TransferMarketService` mantém janelas de transferência, estado negociável do jogador, propostas, contrapropostas, termômetro, eventos e histórico. O valor de mercado é uma política configurável e não interpreta `rating_hash`, `cr1` ou `cr2`.

Uma proposta percorre interesse, oferta, contraproposta, aceite e conclusão. A transferência concluída valida janela, vendedor, disponibilidade e caixa, registra lançamentos no `FinanceLedger`, atualiza o clube do jogador, encerra o estado da oferta e grava histórico dentro de uma operação transacional.

A chave financeira da operação usa a transferência como origem. A conclusão é idempotente: uma oferta concluída retorna `ALREADY_COMPLETED` e não realiza novo pagamento. O estado do jogador não é alterado diretamente fora do serviço.

## Scouting

`ScoutService` cria missões de 1, 2, 3 ou 6 meses, valida a existência de um scout, inicia/cancela missões e consulta o catálogo persistente quando a data de retorno é atingida. A consulta aplica posição e faixa etária, embaralha candidatos com seed opcional e gera oportunidades parciais.

As oportunidades preservam jogador, clube, posição, idade, confiança, prioridade, nível de conhecimento e observação. Campos não disponíveis na fonte não são inventados. O relatório não compra nem transfere jogador automaticamente; ele apenas cria informação para o clube analisar.

## Persistência

As tabelas ficam no banco mutável `data/state/game.db`: `transfer_windows`, `player_market_state`, `transfer_offers`, `transfer_history`, `transfer_events`, `scout_missions`, `scout_opportunities` e `scout_reports`. O banco-base continua sem alteração.

## Fora do escopo

Não foram implementados mercado automático mundial, IA autônoma, campeonatos, partidas, economia mundial, scouting físico, transferência automática baseada em relatório ou simulação de milhões de jogadores.
