# Incremento P1-6 — Agregados de temporada por atleta

O `SportStateStore` expõe `player_season_totals`, uma leitura derivada diretamente de `player_match_stats`. O método soma minutos, gols, assistências e cartões, calcula aparições e média de avaliação, podendo filtrar por atleta e por conjunto de partidas.

A ordenação é determinística por gols, assistências, minutos e ID do atleta. Nenhuma tabela de ranking ou cache paralelo é criado. A cobertura passou em 11 testes focados, incluindo filtros, agregações e média de avaliação.

A associação formal de partidas a temporadas/competições e a exposição desses agregados no contrato tRPC permanecem como próximos incrementos.
