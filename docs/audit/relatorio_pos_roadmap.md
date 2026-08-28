# Relatório pós-roadmap do FutManager

> Este arquivo é gerado por `engine/scripts/generate_audit_report.py`. Os números abaixo não são digitados manualmente: o auditor estrutural é lido de `docs/audit/roadmap_3000_final.json` e os testes são contados diretamente no código versionado.

## Escopo

Esta rodada consolida a auditoria do manifesto, a integração frontend–gateway–GameState, o isolamento de fixtures e os gates de entrega. A regra arquitetural permanece: **SQL/GameState é a fonte única da verdade**.

## Resultado executivo

| Área | Resultado | Evidência gerada |
|---|---:|---|
| Manifesto | 3000 itens `DONE`, 0 pendentes de 3000 | `frontend/docs/roadmap_3000_execucao.json` |
| Auditor estrutural | 2389 aprovados, 611 em revisão de 3000 | `docs/audit/roadmap_3000_final.json` |
| Testes Python | 315 casos em 160 arquivos | `docs/audit/test_counts.json` |
| Testes Vitest | 42 casos em 19 arquivos | `docs/audit/test_counts.json` |
| Total de testes descobertos | 357 casos | `engine/scripts/count_tests.py` |
| Fonte da verdade | `SQL_GAMESTATE` | Manifesto estrutural |
| Itens em revisão estrutural | 611 | Manifesto estrutural |

## Leitura correta da auditoria

O status `REVIEW` do auditor estrutural não significa que o manifesto tenha itens pendentes. Ele representa a quantidade de itens cuja evidência estrutural ainda não prova algum vínculo específico de módulo, serviço ou gateway. O manifesto bruto e a auditoria estrutural são visões diferentes do mesmo escopo e permanecem publicados separadamente.

## Integridade do pacote

O pipeline valida os manifestos `.sha256` contra seus arquivos `.gz` correspondentes, verifica a integridade SQLite dos bancos descompactados e rejeita o banco-semente de release quando as tabelas `manager_careers`, `managers` ou `manager_selection_assignments` contêm qualquer linha. A validação ocorre antes das suítes de testes e das simulações demoradas.

## Portabilidade do backend web

Os leitores de estado e assets usam `FUTMANAGER_ENGINE_ROOT` e `FUTMANAGER_ENGINE_STATE_PATH`, com fallback relativo ao checkout quando aplicável. O teste de integração de carreira usa um banco temporário derivado da configuração do ambiente, permitindo reproduzir o fluxo fora da máquina que originou o pacote.

## Validação e limitações

Os resultados de execução do CI devem ser lidos nos artefatos do workflow correspondente; este documento não transforma uma contagem de testes em alegação de aprovação. A auditoria estrutural continua registrando 611 itens em revisão, e a validação Android depende do projeto da branch `offline-android-release`, que é auditado e integrado separadamente do backend web.

## Fonte de geração

Para regenerar este relatório e os contadores após qualquer alteração no código, execute:

```bash
python3 engine/scripts/generate_audit_report.py
```
