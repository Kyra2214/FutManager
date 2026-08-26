# Simulação mundial e recuperação

A simulação mundial é executada no GameState SQLite por lotes determinísticos. O nível (`FULL`, `STANDARD`, `FAST` ou `ABSTRACT`) e a seed ficam persistidos em `simulation_configs` por temporada. Cada lote cria um registro em `simulation_ticks`, enfileira partidas na ordem `match_date, match_id` e audita cada resultado em `simulation_audit`.

O cancelamento cooperativo encerra o lote com estado `CANCELLED` antes de iniciar a próxima partida. Após cada partida, `simulation_checkpoints` registra a quantidade processada e o último jogo; a consulta `progress` é read-only e não controla o worker. A repetição do mesmo `simulation_tick_id` retorna `ALREADY_PROCESSED`, evitando eventos duplicados.

`divergence_report` compara resultados auditados de dois ticks por partida. `benchmark` registra o nível, o volume agendado, o tamanho da amostra e o custo de consulta. O lote usa `CompetitionService` para aplicar partidas e transações SQLite; falhas restauram o lote e gravam `ROLLED_BACK`.

> O writer exige um GameState mutável e rejeita o banco-base por `assert_mutable_state_path`. O frontend apenas consulta progresso e envia comandos pelo gateway; não executa partidas nem calcula resultados.
