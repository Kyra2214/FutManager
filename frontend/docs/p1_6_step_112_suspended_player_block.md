# P1-6 / passo 112 — Bloqueio de atleta suspenso

Foi criada a tabela idempotente `player_suspensions` no schema esportivo do GameState, com atleta, data de término, motivo e status ativo. `is_available`, `squad_summary`, `save_formation`, `create_lineup` e `auto_lineup` passam a considerar suspensões vigentes.

A suspensão é escrita pelo serviço autorizado e a escalação rejeita o atleta com o erro compatível `player unavailable or outside club`. O teste usa GameState temporário, confirma a redução de disponibilidade e impede a criação de escalação parcial.
