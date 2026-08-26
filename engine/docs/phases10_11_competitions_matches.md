# Fases 10 e 11 — Competições, calendário, classificação e partidas

As competições agora possuem estrutura separada para temporadas, competições, inscrições, fases, rodadas e fixtures. O calendário é derivado dos fixtures persistidos, evitando uma segunda fonte de verdade.

A classificação usa estatísticas persistidas de clubes e critérios configuráveis de pontos, vitórias, saldo e gols pró. A consulta de artilharia utiliza `player_match_stats`, sem criar ranking duplicado. O encerramento de competição verifica fixtures pendentes e é idempotente.

O motor de partidas executa resultados offline com seed, persiste placar, evento básico de resultado, estatísticas de clubes e classificação. Uma partida `PLAYED` não pode ser executada novamente.

A arquitetura preserva a separação entre força base, forma e estado esportivo. O resultado não altera permanentemente o potencial nem transforma avaliação de partida em força definitiva.

Os próximos incrementos naturais são eventos detalhados de gol/assistência/cartão/substituição/lesão, estatísticas individuais completas, integração automática de forma e fadiga pós-jogo e vínculo obrigatório entre cada fixture e seu Match.
