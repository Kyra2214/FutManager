# P1-6 / passos 117–118 — Condição física e risco de fadiga

Foi criada a leitura `physical_condition`, derivada exclusivamente de `player_sport_state`. Ela expõe condição, fadiga, forma, disponibilidade, recuperação, suspensão e uma faixa determinística de risco: `LOW`, `MEDIUM`, `HIGH` ou `CRITICAL`.

Lesão ativa, fadiga igual ou superior a 90 ou condição igual ou inferior a 20 levam a risco crítico. A consulta por atleta exige que o atleta pertença ao clube informado. Nenhum campo de risco é persistido, evitando estado paralelo.

O teste focado confirmou os níveis alto, baixo e crítico, além da rejeição de atleta fora do clube.
