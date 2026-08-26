# P1-6 / passo 110 — Impacto de moral na escalação

Foi adicionado `SportStateStore.calculate_morale_impact`. O retorno é derivado de forma e fadiga persistidas em `player_sport_state`, disponibilidade e entrosamento calculado da escalação. O modificador é limitado a `-0,25..+0,25`, evitando efeitos econômicos ou esportivos sem limite.

Não foi criada coluna paralela de moral. O contrato informa `average_form`, `average_fatigue`, `modifier`, `lineup_id` e `valid`, permitindo que camadas superiores exibam o efeito sem duplicar a fonte de dados. O teste focado confirma variação determinística entre estados persistidos.
