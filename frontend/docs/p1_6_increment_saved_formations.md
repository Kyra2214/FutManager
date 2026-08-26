# Incremento P1-6 — Formações salvas por competição

Este incremento adiciona persistência SQL para formações salvas por clube e competição, usando as tabelas `saved_formations` e `saved_formation_players` no GameState. O contrato é idempotente por clube, competição e nome da formação; atualizar uma formação substitui seus jogadores no mesmo registro lógico, sem criar estado paralelo.

A criação de uma escalação de partida por `create_match_lineup` consulta a formação persistida, valida que o clube possui pelo menos 11 atletas disponíveis e rejeita formações salvas com menos de 11 jogadores. A validação continua separada de `create_lineup`, preservando compatibilidade com fixtures legados de treinamento e testes unitários menores.

A cobertura focada passou em 5 testes, incluindo treinamento/lesão/formação, partidas determinísticas, resumo de elenco, escopo por competição e criação de escalação de partida. Os critérios seguintes do Front P1-6 — escalação automática, substituições planejadas, minutos, estatísticas de partida, entrosamento, moral, capitão e regras completas de competição — continuam pendentes.
