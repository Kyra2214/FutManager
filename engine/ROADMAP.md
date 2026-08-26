# Roadmap oficial do projeto

Este é o roadmap consolidado do motor do jogo. Os itens marcados como concluídos correspondem às funcionalidades implementadas e testadas no projeto atual. Os itens marcados como próximos ou pendentes ainda não foram implementados integralmente.

| Roadmap | Sistema | Situação |
|---:|---|:---:|
| 1 | Esqueleto + DB + estado | ✅ |
| 2 | Jogadores + idade + potencial + carreira | ✅ |
| 3 | Comissão + estrutura | ✅ |
| 4 | Contratos + patrocinadores | ✅ |
| 5 | Orquestração + contabilidade | ✅ |
| 6–7 | Mercado + transferências + scouting | ✅ |
| 8 | Clubes + elenco + base + formação | ✅ |
| 9 | Treinamento + evolução + lesões | ✅ |
| 10 | Competições + calendário + classificação | ✅ |
| 11 | Motor de partidas/resultados | ✅ |
| 12 | IA dos clubes | 🔜 |
| 13 | Economia mundial + falência + SAF | ⬜ |
| 14 | Estádios + torcida + reputação + eventos | ⬜ |
| 15 | Patrocínios avançados + mídia + receitas | ⬜ |
| 16 | Simulação mundial otimizada | ⬜ |
| 17 | Manager/carreira humana | ⬜ |
| 18 | Integração geral + balanceamento | ⬜ |
| 19 | Frontend | ⬜ |
| 20 | Testes de estresse + múltiplas temporadas | ⬜ |

## Próxima etapa

A próxima etapa prioritária é o **Roadmap 12 — IA dos clubes**. Os itens 13 a 20 permanecem pendentes e deverão ser implementados somente após a conclusão e validação das etapas anteriores.

## Observação sobre o estado atual

Os Roadmaps 6 a 11 foram implementados em camadas de motor/backend, com persistência SQLite e testes automatizados. Alguns componentes ainda possuem escopo inicial, sem IA autônoma completa, simulação mundial otimizada, regras econômicas completas ou frontend. Por isso, a conclusão dos itens indica que a fundação funcional foi criada, não que todos os recursos avançados futuros estejam finalizados.

## Arquivos relacionados

- `data/database/game.db`: banco-base preservado.
- `data/state/game.db`: estado mutável do jogo.
- `data/reports/`: relatórios técnicos das etapas.
- `tests/`: testes automatizados do motor.
