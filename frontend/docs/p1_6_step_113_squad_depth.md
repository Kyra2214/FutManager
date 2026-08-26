# P1-6 / passo 113 — Profundidade por posição

Foi adicionado `SportStateStore.squad_depth_report(club_id)`, uma leitura derivada de `player_sport_state` e `player_positions`. O relatório agrupa por posição canônica e informa total, primeiro time, reservas, base, disponíveis, indisponíveis, suspensos e IDs dos atletas.

Lesões, recuperação e suspensões são contabilizadas pela mesma guarda de disponibilidade usada nas escalações. Nenhum ranking ou snapshot paralelo é persistido. O teste temporário confirma agrupamento, categorias e estados disciplinares.
