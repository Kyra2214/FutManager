# Relatório pós-roadmap — FutManager

## Escopo

Esta rodada consolidou a auditoria dos 3.000 itens do manifesto, a simulação persistente de uma carreira, a integração frontend–gateway–GameState, o isolamento de fixtures e o workflow obrigatório do GitHub Actions.

A regra arquitetural foi preservada: **SQL/GameState permanece como fonte única da verdade**. Os bancos usados no CI são fixtures comprimidas e são descompactados somente no runner; nenhuma regra foi criada no frontend para substituir o motor Python.

## Resultado executivo

| Área | Resultado | Evidência |
|---|---:|---|
| Manifesto | 3.000 itens `DONE`, 0 pendentes | `frontend/docs/roadmap_3000_execucao.json` |
| Auditor estrutural | 2.389 aprovados, 611 em revisão | `docs/audit/roadmap_3000_final.json` |
| Simulação de temporada | `PASS`, 16 etapas, 4 invariantes | `docs/audit/season_simulation_final.json` |
| Backend e contratos | 365 testes aprovados | Job `Backend and engine` |
| Frontend e full-stack | 63 testes aprovados | Job `Frontend` |
| TypeScript | Aprovado | `pnpm check` |
| Build frontend | Aprovado | `pnpm build` |
| GitHub Actions | **Sucesso** | [run 33106220338](https://github.com/Kyra2214/FutManager/actions/runs/33106220338) |

## Auditoria do manifesto

O auditor percorreu todos os itens e verificou status, política de fonte da verdade, existência do módulo quando indicado e indícios de integração no `ManagerService` e no gateway. Os itens legados sem `source_of_truth` explícito herdaram a política global do manifesto, que documenta SQL/GameState.

O resultado de 611 itens em revisão não significa que o manifesto tenha itens pendentes. Significa que a evidência disponível para esses itens não prova, pela heurística estrutural, algum vínculo específico de módulo, serviço ou gateway. Esses casos permanecem transparentemente registrados no JSON para revisão posterior, sem serem transformados em aprovação artificial.

## Simulação persistente

A simulação criou uma carreira em banco temporário e percorreu operações reais do gateway. O fluxo validado incluiu criação da carreira, leitura de economia, leitura de elenco/estado, bootstrap do estádio, bootstrap de patrocínio, leitura de ofertas, treino, moral, saúde, resumo financeiro e avanço semanal.

As invariantes verificadas incluíram persistência da carreira, consistência do GameState temporário, não negatividade de valores econômicos e preservação da leitura canônica após mutações. A simulação não inventa placares nem cria resultados esportivos artificiais; ela falha explicitamente quando uma operação de temporada não está conectada.

## Correções aplicadas

Foram corrigidos os caminhos absolutos que impediam a reprodução no clone GitHub, o fallback do adaptador frontend para localizar o motor, a preparação isolada do GameState, a ausência do banco-base completo no CI, a ativação do pnpm no runner e a colisão entre duas árvores Python concorrentes.

Também foram corrigidos os testes de governança e de integração tRPC para usar caminhos relativos ao repositório. A árvore Python legada aninhada foi removida do clone, mantendo uma única árvore atual em `engine/`.

## CI e isolamento

O workflow `.github/workflows/ci.yml` executa em `push` e `pull_request`, sem `continue-on-error`. O job backend prepara os bancos comprimidos, executa compilação, testes Python, simulação e auditoria. O job frontend instala dependências, prepara uma cópia própria do GameState, executa typecheck, testes Vitest e build.

O banco original não é alterado pelo CI: cada job usa cópia descompactada no workspace efêmero. O teste tRPC cria ainda um banco temporário próprio e limpa as tabelas de carreira antes da execução.

## Limitações conhecidas

A auditoria estrutural ainda registra 611 itens em revisão por insuficiência ou heterogeneidade de evidência histórica. O próximo endurecimento recomendado é substituir heurísticas textuais por um registro explícito de contrato, módulo, método do `ManagerService`, ação do gateway e teste associado para cada item.

A simulação validada cobre 16 etapas reais, mas não constitui ainda uma temporada competitiva completa com todos os calendários, resultados e transições esportivas. Essa expansão deve ser feita somente após confirmar quais operações de calendário e resultados estão disponíveis no GameState, sem fabricar partidas.

## Próximos passos recomendados

1. Criar uma matriz de rastreabilidade para os 611 itens em revisão, apontando evidência canônica ou registrando a lacuna de forma individual.
2. Expandir a simulação para múltiplas semanas e uma temporada competitiva completa usando exclusivamente fixtures e ações existentes.
3. Adicionar execução periódica do CI e um relatório de regressão de schema, contratos e invariantes econômicas.
