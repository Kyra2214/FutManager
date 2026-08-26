# Ticks 8 e 9 — Ciclo esportivo, competições e partidas

Esta etapa transforma jogadores em entidades esportivas persistentes e cria competições offline com calendário e partidas executáveis.

## Tick 8

`SportStateStore` mantém condição, fadiga, forma, treinamento, disponibilidade, lesão, recuperação, minutos e partidas recentes. `SquadCategory` separa `FIRST_TEAM`, `RESERVE` e `YOUTH`; promoção é explícita e registra histórico.

`TrainingService` está representado pelas operações de treino do estado esportivo, com categorias configuráveis e carga limitada. Treino altera fadiga e forma, mas não reinterpreta nem sobrescreve o potencial do Rules Engine. Lesões possuem duração, gravidade e estados ativo, recuperação e recuperado. A disponibilidade verifica vínculo, recuperação e bloqueios.

`create_lineup` valida clube, disponibilidade, duplicidade, formação e jogadores da escalação. `team_strength` considera forma, fadiga e disponibilidade da escalação efetiva; não é média fixa de ratings.

## Tick 9

`CompetitionService` mantém temporadas, competições, inscrições, fixtures, partidas e estatísticas. O calendário gera partidas finitas entre clubes inscritos. `play` produz resultado seedável, persiste gols e evento de resultado e atualiza vitórias, empates, derrotas, gols e pontos.

A classificação usa pontos, vitórias, saldo e gols pró. Partidas jogadas são idempotentes: uma segunda execução retorna `ALREADY_PLAYED` e não altera o resultado. O motor está preparado para estatísticas individuais, cartões, substituições e lesões, mas implementa nesta fase apenas o evento básico do resultado.

## Integridade

Todos os dados mutáveis pertencem a `data/state/game.db`. O banco-base `data/database/game.db` permanece intacto. O funcionamento é local e offline; não depende de API, servidor ou autenticação.

## Fora do escopo

Não foram implementados frontend, IA autônoma completa, simulação mundial, campeonatos complexos, prorrogação, pênaltis, calendário universal, classificação por país, artilharia detalhada, mídia ou economia mundial.
