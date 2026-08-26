# P1-6 / passo 111 — Bloqueio de atleta lesionado

A criação de formações usa a disponibilidade persistida de `player_sport_state`. Quando `available=0` ou `recovery_days>0`, `save_formation` rejeita o atleta e não cria uma formação parcial. O mesmo guarda é reutilizado por `create_lineup` e pelas escalações automáticas.

O teste focado cobre uma lesão real em GameState temporário e confirma que o atleta não é aceito na formação. O erro permanece determinístico (`player unavailable or outside club`) para compatibilidade com os contratos atuais.
