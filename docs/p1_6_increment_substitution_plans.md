# Incremento P1-6 — Substituições planejadas

O GameState agora persiste substituições planejadas em `substitution_plans`, vinculadas à escalação por `lineup_id`. Cada plano contém minuto-alvo, jogador de saída, jogador de entrada e status. A chave natural `(lineup_id, minute_target, outgoing_player_id)` impede duplicidade e torna a atualização idempotente.

A operação valida minuto entre 1 e 120, exige que o atleta de saída esteja na escalação titular e exige que o atleta de entrada pertença ao mesmo clube, esteja disponível e não esteja em recuperação. A leitura ocorre por `planned_substitutions`, sempre ordenada por minuto e ID do plano.

A cobertura focada passou em 7 testes, incluindo persistência, idempotência e rejeição de saída inválida. A execução da substituição durante uma partida e o registro de minutos jogados permanecem como próximos incrementos do Front P1-6.
