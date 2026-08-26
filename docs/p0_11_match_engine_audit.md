# P0-11 — Auditoria do Motor de Partidas

O `CompetitionService` mantém a separação entre `generate_result` e `apply_result`. A geração usa seed persistida, mando de campo e os modificadores de força, forma, moral e tática; a aplicação executa a transação e grava placar, evento canônico, estatísticas de partida, estatísticas individuais e classificação.

As tabelas canônicas são `matches`, `match_events`, `match_stats`, `player_match_stats` e `team_competition_stats`. O motor valida competição existente, impede partida sem competição, rejeita replay, rejeita placar negativo e limita o número de eventos. Posse, finalizações e xG são métricas do modelo de jogo e não substituem dados reais não persistidos.

Adiamento e remarcação alteram somente o fixture persistido e preservam a guarda contra partida já jogada. A distribuição de placares é uma leitura agregada por temporada. Os testes focados de competição, estrutura, fases 10/11, ciclo esportivo e receita de dia de jogo passaram com 32 casos.
