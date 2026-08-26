# P1-6 / passo 115 — Capitão e cobradores

Foi criada a tabela única `club_player_roles` no GameState, com uma função por clube e papéis explícitos: `CAPTAIN`, `PENALTY_TAKER`, `FREE_KICK_TAKER` e `CORNER_TAKER`. `set_player_role` valida vínculo ao clube e disponibilidade vigente; novas atribuições substituem a anterior de forma idempotente.

A leitura `player_roles` retorna somente o estado persistido. O teste temporário confirma unicidade do capitão, atualização do papel e rejeição de atleta lesionado.
