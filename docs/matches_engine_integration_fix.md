# Correção da integração do motor de partidas

A inconsistência foi reproduzida no GameState real. Após iniciar uma carreira paralela, o motor Python persistia a liga em `career_parallel_leagues`, a classificação em `career_parallel_standings` e 2.360 partidas em `career_parallel_fixtures`. As tabelas canônicas `competitions`, `competition_entries` e `fixtures` permaneciam vazias, mas o dashboard React consultava somente o modelo canônico; por isso a aba Nossas Partidas mostrava estado vazio.

A correção foi aplicada em `server/engineState.ts`: quando o catálogo canônico está vazio ou ausente, o leitor resolve a carreira ativa, cria uma identificação de competição somente de leitura, lê a liga, a classificação e os fixtures de `career_parallel_*`, e converte os registros para o mesmo `CompetitionSummary`, `StandingRow` e `MatchCard` usado pela interface. Não há dados fictícios, gravações no frontend ou duplicação de regras.

Validação real: a carreira ativa passou a retornar competição `Minha carreira · Liga Mundial`, 80 clubes, 1.520 fixtures agendados e 80 linhas de classificação. O teste de regressão com banco paralelo sem tabelas canônicas passou, assim como os testes canônicos existentes e o typecheck.
