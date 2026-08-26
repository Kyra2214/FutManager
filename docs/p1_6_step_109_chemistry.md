# P1-6 / passo 109 — Entrosamento do elenco

Foi adicionado `SportStateStore.calculate_chemistry(club_id, lineup_id=None)`. O método lê a escalação e as posições canônicas de `player_positions`, verifica disponibilidade em `player_sport_state` e retorna um score determinístico de 0 a 100.

A fórmula atual pondera disponibilidade dos 11 atletas (55%) e cobertura de posições distintas (45%). O retorno é derivado, não é persistido como ranking ou estado paralelo. Sem escalação válida, o método retorna `valid: false` e score zero. O teste focado passou após confirmar que `player_positions` é a fonte correta quando o vínculo da escalação usa posição de fallback.
