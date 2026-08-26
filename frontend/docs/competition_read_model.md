# Contrato de leitura de competições

O dashboard de partidas lê diretamente o SQLite do GameState em modo somente leitura. Cada competição retorna temporada, status, clubes inscritos, partidas agendadas, partidas jogadas, fase atual e os critérios de desempate persistidos em `competition_config.tiebreakers`.

`matches.dashboard` aceita `competitionId`, `season` e `phaseId` como filtros tRPC estáveis. Fixtures e partidas reais são unidos pelo identificador canônico e preservam status persistido, inclusive `SCHEDULED`, `PLAYED`, `POSTPONED` e `SUSPENDED` quando presentes no estado.

`matches.classificationPreview` recebe uma partida hipotética e retorna a classificação recalculada em memória, com `persisted: false` e versão de fórmula. `matches.competitionComparison` agrega líder, clubes, partidas e pontos por competição sem escrever. `matches.competitionHistory` lê campeões, premiações e alertas das tabelas canônicas, retornando listas vazias honestas quando as tabelas ainda não possuem registros.

A ordenação padrão da tabela respeita pontos, vitórias, saldo de gols, gols pró e nome do clube, em correspondência com o contrato do motor. Nenhuma classificação, pontuação, status ou premiação é calculada no cliente.
