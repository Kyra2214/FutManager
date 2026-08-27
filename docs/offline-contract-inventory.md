# Inventário de contratos para a migração offline

A interface atual utiliza **47 chamadas tRPC** distribuídas em 13 domínios. No APK, elas deverão ser substituídas por métodos de `localDomain` com a mesma semântica de entrada e saída, mas executados contra o GameState SQLite local.

| Domínio | Operações encontradas | Prioridade |
| --- | --- | --- |
| Carreira | `catalog`, `current`, `parallelPreview`, `start`, `worldCountries`, `advanceUntilMatch`, `advanceWeek` | P0 |
| Partidas | `dashboard`, `playerStats`, `playControlled`, `travelPreview`, `travelSummary` | P0 |
| Assets | `resolve` | P0 |
| Eventos | `list`, `markRead` | P0 |
| Clube | `workspace`, `financeAlert`, `financeHistory`, `financeLedger` | P0 |
| Estádio | `bootstrap`, `fanSegments`, `preview`, `socialTimeline`, `summary`, `ticketPrice`, `ticketPricePreview`, `upgrade` | P1 |
| Staff e CT | `catalog`, `departmentOffers`, `health`, `hire`, `summary`, `trainingDepartments`, `trainingDevelopment`, `upgradeDepartment` | P1 |
| Patrocínio | `accept`, `summary` | P1 |
| Operações | `finance`, `snapshots` | P1 |
| Autenticação | `me`, `logout` | Remover do APK |
| IA | `chat` | Remover do modo offline ou tornar opcional |

## Ordem de portabilidade

O primeiro corte funcional deve cobrir criação de carreira, leitura do GameState, catálogo de clubes e ligas, avanço semanal, viagem até a partida, abertura do modo partida, decisões táticas, eventos e retomada. Esses contratos formam o caminho crítico usado pelo jogador e não dependem de recursos externos.

Depois do caminho crítico, a migração deve cobrir finanças, estádio, CT, comissão, saúde, mercado, patrocínios e snapshots. Cada grupo precisa preservar as transações e as validações já aplicadas pelos serviços Python, sem mover regras para componentes React.

Autenticação, IA remota, notificações server-side, S3 e OAuth não farão parte do núcleo offline. O aplicativo deverá apresentar estados honestos para recursos opcionais, sem tentar acessar endpoints remotos.

## Regra de compatibilidade

Durante a transição, os contratos locais devem ser testados contra o gateway Python em cópias temporárias do GameState, com seed explícita e mesma temporada/semana. Divergências devem ser tratadas como falha de portabilidade; não é permitido ajustar o frontend para mascarar diferenças de regra.
