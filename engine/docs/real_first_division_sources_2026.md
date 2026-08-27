# Fontes de primeira divisão usadas como entrada de normalização

A fonte externa é somente uma entrada de membership. O resultado definitivo será escrito no GameState SQLite e o frontend consultará apenas o SQL.

## Fontes consultadas

| País | Competição | Fonte | Quantidade observada |
|---|---|---|---:|
| Brasil | Campeonato Brasileiro Série A 2026 | [CBF — Campeonato Brasileiro](https://www.cbf.com.br/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-a) | 20 |
| Itália | Serie A 2026/27 | [Lega Serie A — Standings](https://en.legaseriea.it/serie-a/standings) | 20 |
| Espanha | LALIGA EA SPORTS 2026/27 | [LALIGA — Clubs](https://www.laliga.com/en-GB/laliga-easports/clubs) | 20 |
| Portugal | Liga Portugal Betclic 2025/26 | [Liga Portugal — competição](https://www.ligaportugal.pt/competition/618/liga-portugal-betclic/round/20252026) | fonte acessível, membership precisa ser reconciliado com o CFG do arquivo-mãe |

## Critério de segurança

O importador deve normalizar nomes e aliases externos contra `times`, restringir pelo `pais_id` canônico e bloquear qualquer correspondência ambígua. Clubes não encontrados ou encontrados em duplicidade não podem ser inseridos silenciosamente; devem aparecer em relatório de auditoria para correção manual.

O CFG do arquivo-mãe continua sendo a referência da quantidade estrutural das divisões: Brasil 20, Itália 20, Espanha 20 e Portugal 18 na primeira divisão. Portanto, enquanto a lista externa de Portugal não for reconciliada com os 18 clubes do CFG, o importador não deve completar ou substituir clubes por conta própria.
