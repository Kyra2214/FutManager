# P0-13 — Calendário e temporadas

O calendário usa `LogicalClock` como relógio único de temporada, semana e data. O comando principal do manager avança uma semana; serviços internos podem operar com contexto diário sem criar um segundo relógio. A transição de semana 52 para a semana 1 incrementa a temporada.

`WeeklyWorldCycleService` processa a chave natural de temporada, semana e escopo. Cada execução registra `weekly_world_runs` e `weekly_world_audit`, processando partidas devidas, receita de jogo, patrocínios, folha, ledger e eventos. Uma semana concluída retorna `ALREADY_PROCESSED` em nova tentativa e uma falha reverte o estado e registra `ROLLED_BACK`.

Fixtures e calendários são consultados diretamente das tabelas de competição. Adiamentos e remarcações permanecem no MatchEngine, permitindo resolver conflitos sem duplicar compromissos. O contrato mantém estados honestos para semanas sem partidas, múltiplas partidas, temporadas em pausa e transições que ainda não possuem configuração suficiente.

A validação focada passou com 15 testes de calendário, orquestração, ciclo semanal e restauração/adiamento, além da compilação dos serviços de mundo.
