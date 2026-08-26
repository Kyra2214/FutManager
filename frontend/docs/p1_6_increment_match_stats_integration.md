# Incremento P1-6 — Integração de estatísticas ao resultado

O `CompetitionService.apply_result` agora registra estatísticas individuais quando recebe `home_lineup_id` e `away_lineup_id`. Cada atleta da escalação recebe 90 minutos e avaliação base persistida; os gols são distribuídos de forma determinística pela ordem estável da escalação, e a primeira participação recebe uma assistência quando há gol.

A gravação usa a tabela canônica `player_match_stats` e `INSERT ... WHERE NOT EXISTS`, preservando a idempotência do resultado aplicado. Partidas sem escalação continuam compatíveis e não inventam estatísticas individuais.

Os testes de partidas, bilheteria e esporte passaram em 12 casos. A integração de substituições efetivamente durante o jogo, cartões derivados de eventos e atualização de minutos por atleta substituído permanecem como próximos incrementos.
