# Auditoria de checkpoints antes de publicação

A cadeia abaixo foi conferida no histórico local versionado do projeto em 26/08/2026. Cada marco publicado possui um commit/checkpoint anterior à publicação seguinte; o checkpoint é o mecanismo de promoção do estado validado.

| Sequência | Checkpoint | Escopo |
|---:|---|---|
| 1 | `3fc90838` | Competições e contratos 391–403 |
| 2 | `b69ca7df` | Renovação, ledger e perfil 404–410 |
| 3 | `0bc6f206` | Treino e scouting 411–420 |
| 4 | `5e214169` | Mercado e transferências 421–430 |
| 5 | `4d9967fb` | Bloco esportivo e calendário 371–390 |
| 6 | `54cecc23` | Evidências 371–500 e UX |
| 7 | `17b8cabd` | Gaps de 471–499 resolvidos |
| 8 | `9d989f08` | Auditoria item a item 471–500 |

O histórico mostra também checkpoints intermediários de viagens, lista das 100 implementações e sincronização GitHub. A regra operacional é: alterar código, executar testes/validadores, revisar `todo.md`, salvar checkpoint e somente então considerar o estado publicável. Nenhum passo de publicação é tratado como concluído sem checkpoint correspondente.

> A auditoria comprova a cadeia dos marcos relevantes registrados no projeto. Ela não substitui os testes do conteúdo; estes estão referenciados em `docs/auditoria_item_a_item_471_500.json` e nos relatórios de qualidade.
