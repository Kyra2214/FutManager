# Incremento P1-6 — Escalação automática por posição

O GameState agora mantém `player_positions` e permite gerar uma escalação automática determinística. O algoritmo seleciona primeiro um atleta disponível por cada código de posição, ordenando por forma decrescente e ID crescente; caso uma posição não tenha cobertura, completa a escalação com os demais atletas disponíveis até o mínimo de 11.

A operação `auto_lineup` valida o mínimo de 11 atletas antes da seleção e delega a gravação final a `create_lineup`. Lesões, indisponibilidade e jogadores de outro clube não entram na escalação. O teste focado comprovou seleção sem duplicidade e ordem determinística para 11 posições.

Ainda permanecem pendentes os incrementos de substituições planejadas, minutos jogados, estatísticas individuais, entrosamento, moral, capitão, cobradores, histórico tático, fadiga por calendário e validação completa por regras de competição.
