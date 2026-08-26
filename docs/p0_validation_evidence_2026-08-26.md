# Evidência de validação P0 — 2026-08-26

## Resultado

A validação governada executada após a consolidação do Front P0-1 retornou sucesso nos três validadores: `validate_roadmap_gate.py`, `validate_mutation_paths.py` e `validate_p0_governance.py`. O gate global permanece `P0_GATE=CLOSED`, a consolidação incremental é aceita e P1/P2 continuam bloqueados.

| Verificação | Resultado |
|---|---|
| Roadmap | 500 itens, 25 fronts, 11 fronts P0, 12 fronts P1 e 2 fronts P2 |
| Fonte única | SQL/GameState declarada e validada |
| Caminhos de mutação | 5 routers, 27 dispatches autorizados, sem escrita paralela no frontend |
| Charter P0-1 | 20 critérios e 20 linhas item→evidência válidos |
| Testes frontend | 47 testes aprovados em 14 arquivos |
| TypeScript | `tsc --noEmit` aprovado |
| Build | Vite/esbuild aprovado; apenas avisos não bloqueantes de asset runtime e tamanho de chunk |
| Testes do motor | 141 testes Python aprovados |

## Decisão de gate

O Front P0-1 está `CONSOLIDATED` no `roadmap_gate.json`. Os fronts P0 restantes continuam `PENDING`; portanto, não há autorização para abrir P0 nem iniciar itens P1/P2.

## Auditoria P0-3 — banco e migrações

A auditoria read-only `scripts/validate_p0_database.py` verificou os dois bancos oficiais. O banco-base possui 7 tabelas e hash SHA-256 conferido contra o manifesto; o GameState possui 97 tabelas, `schema_version=2` e os índices de ledger esperados disponíveis. Ambos retornaram `integrity_check=ok` e zero erros em `foreign_key_check`. Índices específicos do ciclo não são exigidos no banco-base imutável quando suas tabelas não existem.

## Auditoria P0-4 — jogadores canônicos

A auditoria read-only `scripts/audit_canonical_players.py` confirmou **231.911 jogadores**, com **231.911 chaves canônicas distintas**, nenhum campo obrigatório nulo, nenhuma posição desconhecida e nenhum vínculo duplicado jogador–time–categoria. As posições e status foram agregados diretamente do SQL: goleiros 27.078, laterais 38.881, zagueiros 41.236, meias 76.224 e atacantes 48.492; titulares 89.707 e reservas 146.015; 224 países com jogadores registrados. O relatório completo foi gravado em `brasfoot_engine/docs/canonical_players_audit.json`.

## Auditoria P0-5 — clubes, seleções e identidades

A auditoria read-only `scripts/audit_canonical_clubs.py` confirmou **8.399 clubes**, **86 seleções** e **224 países**, com zero duplicidade de `arquivo_origem` de clubes, zero duplicidade de códigos/nomes de seleções e zero vínculos de país órfãos. Foram observadas 140 colisões de nomes de clubes; elas são colisões de rótulo, não de identidade, pois a chave canônica continua sendo o identificador de origem/ID oficial. O resultado final foi `VALID`.

## Auditoria P0-11 — motor de partidas

A auditoria `scripts/validate_p0_match_engine.py` confirmou a implementação de `CompetitionService.play`, seed determinístico, transição para `PLAYED`, commits controlados e testes existentes para partida inválida, partida já jogada, seed, rollback e idempotência. O resultado foi `VALID`; a cobertura estrutural foi registrada sem iniciar P1/P2.

## Auditoria P0-12/P0-13 — competições, classificação, calendário e temporadas

A auditoria `scripts/validate_p0_competitions_calendar.py` confirmou, em cinco arquivos reais, contratos de criação de competições, geração de fixtures, calendário, classificação em `team_competition_stats`, prevenção de encerramento com fixtures pendentes e idempotência/rollback da integração. O resultado foi `VALID`. A auditoria comprova a presença dos contratos e testes, mas não altera o status dos fronts no gate sem uma matriz integral item a item.

## Auditoria P0-14 — torcida, reputação, público e bilheteria

A auditoria `scripts/validate_p0_social_revenue.py` confirmou os serviços de presença, torcida/reputação e receita de dia de jogo, além dos testes de seed, limite por capacidade, ledger, idempotência e rollback do ciclo semanal. O resultado foi `VALID`; a nomenclatura real `SocialService` foi preservada e nenhuma regra paralela foi criada.

## Auditoria P0-15 — patrocínios e overall institucional

A auditoria `scripts/validate_p0_sponsorships.py` confirmou os contratos reais de estrelas, overall institucional, conjuntos de ofertas, missões, progresso por eventos e lançamentos `SPONSOR_MISSION`, além dos testes de seed, ofertas, missões e idempotência. A fórmula institucional usa `squad_score`, `ct_score` e `stadium_score`; o resultado foi `VALID`.

## Bateria consolidada de regressão

As auditorias governadas P0-2, P0-3, P0-4, P0-5, P0-11, P0-12/P0-13, P0-14 e P0-15 retornaram `VALID`. A regressão completa permaneceu aprovada com **143 testes Python** e **47 testes frontend**. O gate continua fechado por desenho: evidência de um front não equivale à consolidação integral dos 11 fronts P0.

## Auditoria P0-16 — simulação mundial

A auditoria `scripts/validate_p0_world_simulation.py` confirmou os níveis de simulação, seleção prioritária de clube, seed determinístico, auditoria persistida, cancelamento cooperativo e retorno idempotente `ALREADY_PROCESSED`. O resultado foi `VALID`; nenhum tick foi executado nos bancos oficiais durante a auditoria.
