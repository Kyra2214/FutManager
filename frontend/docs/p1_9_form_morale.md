# P1-9 — Treinamento, forma e moral

O GameState agora separa forma técnica e física em colunas compatíveis com estados anteriores, mantendo `form` como fallback de migração. A forma é atualizada após partidas e sessões semanais com variação determinística baseada em seed e ID canônico do atleta.

A moral individual é persistida em `player_morale`; a moral coletiva é sempre agregada dos atletas vinculados ao clube. Vitórias, empates e derrotas geram deltas documentados no histórico de moral, enquanto sequência de jogos permanece identificável por temporada e semana.

O serviço suporta planos técnico, tático, físico, bola parada, geral e descanso. A carga efetiva considera idade, partidas internacionais e descanso; o relatório semanal agrega carga e aderência. Preparação de adversário, recomendações de descanso/recuperação e forma técnica são persistidas ou derivadas do mesmo estado.

O gateway e tRPC expõem resumo de moral, atualização pós-partida, treino semanal, preparação, relatório de carga e recomendações. Os testes cobrem determinismo, resultado esportivo, descanso, limite etário, calendário internacional e recomendações.
