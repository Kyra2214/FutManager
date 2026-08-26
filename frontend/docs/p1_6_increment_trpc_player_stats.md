# Incremento P1-6 — Estatísticas individuais via tRPC

O router `matches` ganhou a procedure somente leitura `playerStats`. Ela aceita filtro opcional por competição e por IDs de partida, delega ao adaptador `engineState` e retorna a origem, os filtros aplicados e os agregados de atletas.

O adaptador abre o GameState em modo `readOnly`, valida a existência da tabela canônica `player_match_stats`, aplica filtros parametrizados e mantém a ordenação por produção e ID. Quando não há estatísticas, retorna estado conectado porém vazio; quando o arquivo não está disponível, retorna indisponibilidade honesta.

Os testes de engineState e integração tRPC passaram em 3 casos focados. A ligação visual desses dados à aba Time permanece como próximo incremento.
