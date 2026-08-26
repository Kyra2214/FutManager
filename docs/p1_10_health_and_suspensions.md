# P1-10 — Lesões, saúde e suspensões

O serviço `HealthService` usa as tabelas canônicas de `injuries`, `player_sport_state` e `player_suspensions`, acrescentando apenas histórico médico e alertas persistidos. O diagnóstico registra tipo, gravidade, início, dias estimados e data de retorno; a estimativa é determinística por seed e explicitamente representa um modelo de jogo, não prognóstico clínico.

A recuperação reduz dias diariamente ou semanalmente e considera o nível de médicos ativos. Ao concluir, libera o atleta no estado esportivo e emite alerta de retorno. Lesões ativas continuam bloqueando escalações pelo contrato já existente do ciclo esportivo. Cartões e expulsões geram suspensões persistidas com duração determinística e histórico.

O gateway e tRPC expõem lista médica, filtros por gravidade/prazo, alertas, registro de lesão, recuperação e suspensão. O painel CT mostra o estado oficial das lesões ativas. Jogadores fora do elenco são rejeitados sem criação de registro. A cobertura inclui diagnóstico, filtro, alerta de lesão, recuperação com bônus médico, suspensão e rejeição de identidade inexistente.
