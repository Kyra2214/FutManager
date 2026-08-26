# Incremento P1-6 — Estado honesto para atleta sem vínculo

Quando `player_match_stats` contém um atleta que não aparece no elenco persistido atual, a aba Time não tenta inferir nome, posição ou identidade. Ela exibe `Atleta não localizado` e `posição não informada`, mantendo o ID estatístico visível para auditoria.

Esse comportamento preserva a separação entre identidade canônica e estatística de partida. Nenhum vínculo é criado no frontend e nenhum dado é inventado.
