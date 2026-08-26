# Charter de Governança — Front P0-1

## Objetivo

Conduzir a evolução do FutManager/Brasfoot por três temporadas simuladas sem quebrar a cadeia **ARQUIVO-MÃE → SQL/GameState → serviços de domínio → gateway Python → tRPC → frontend**. O roadmap orienta a execução, mas nunca substitui o estado persistido do jogo.

## Critérios de aceite

O Front P0-1 somente é consolidado quando cada iniciativa possui implementação ou decisão documentada, teste automatizado quando aplicável, `PRAGMA integrity_check = ok`, `PRAGMA foreign_key_check` vazio, documentação versionada e evidência de checkpoint. P1 e P2 permanecem bloqueados enquanto qualquer front P0 estiver pendente.

| Dimensão | Regra verificável |
|---|---|
| Fonte de verdade | Dados esportivos, financeiros, sociais e de carreira vêm exclusivamente do GameState SQLite; o banco-base é imutável. |
| Dados fictícios | Nenhum jogador, clube, saldo, resultado, avaliação ou depoimento é inventado em produção. |
| Reprodutibilidade | Toda simulação que dependa de aleatoriedade recebe seed persistida no contexto e no audit trail. |
| Migrações | Migrações são idempotentes, monotônicas e executadas somente no estado mutável. |
| Transações | Writers aceitam contexto transacional externo e não fazem commit implícito durante o tick. |
| Apresentação | O frontend apenas consulta ou solicita comandos via tRPC/Gateway; não grava nem calcula estado de jogo. |
| Arquivo-mãe | Alterações no dataset original exigem revisão, hash e evidência antes de qualquer uso. |

## Responsabilidades

| Área | Responsabilidade |
|---|---|
| Motor | Regras, simulação, transações, erros de domínio e auditoria. |
| Dados | Integridade canônica, hashes, migrações e reconciliação sem duplicidade. |
| Gateway/tRPC | Contratos serializáveis, autorização dos comandos e nenhuma escrita SQL paralela. |
| Frontend | Leitura fiel, estados vazios honestos, acessibilidade e confirmação de mutações. |
| Testes/operação | Suítes, cenários temporários, hashes, logs, rollback e checkpoints. |

## Riscos e respostas

O risco de divergência entre banco-base e GameState é tratado por hash imutável e comparação read-only. O risco de dupla aplicação é tratado por chaves naturais, ledger e runs idempotentes. O risco de commit intermediário é tratado por `managed_transaction`, testes de falha tardia e rollback. O risco de avanço prematuro é tratado pelo `RoadmapGate`, pela matriz de dependências e pela revisão do checklist.

## Cadência e marcos

A revisão técnica deve ocorrer a cada checkpoint relevante; o ciclo mínimo de validação é: testes focados, suíte completa Python, testes frontend, typecheck, build, integridade SQLite, foreign keys, hash do banco-base e registro da evidência. O primeiro marco funcional é uma temporada completa em GameState temporário; somente depois são avaliados itens P1.

## Decisões de balanceamento

Toda fórmula econômica, social ou esportiva deve registrar versão, entradas, seed quando aplicável, unidade, faixa válida e justificativa. O saldo real do clube, elenco e resultados não podem ser substituídos por valores de demonstração no frontend.

## Gate

O estado inicial permanece `P0_GATE=CLOSED`, `P1_GATE=CLOSED` e `P2_BLOCKED=true`. A abertura exige consolidar todos os fronts P0 e anexar as evidências listadas no manifesto `roadmap_gate.json`; a aprovação não pode ser inferida apenas pela existência do código.

## Matriz item→evidência dos 20 passos P0-1

| Item | Entrega verificável | Evidência |
|---:|---|---|
| 1 | Visão para três temporadas | Objetivo deste charter e marco de temporada completa. |
| 2 | Épicos e aceite | Critérios de aceite e checklist versionado em `todo.md`. |
| 3 | Valor, risco, dependência e esforço | Matriz de dependências e seção de riscos. |
| 4 | Estados descoberta, construção, validação e concluída | Gate versionado e checklist com estados pendente/concluído. |
| 5 | Decisões arquiteturais versionadas | Este charter e `roadmap_execution_policy.md`. |
| 6 | Responsáveis por área | Tabela de responsabilidades deste documento. |
| 7 | Cadência de revisão | Regra de revisão a cada checkpoint e cadência quinzenal. |
| 8 | Registro de riscos | Seção de riscos e respostas deste documento. |
| 9 | Métricas de carreira, economia e partidas | Critérios de integridade, seed, ledger, público e temporada completa. |
| 10 | Escopo essencial/avançado/experimental | O roadmap separa explicitamente escopo essencial, avançado e experimental, refletidos nos níveis P0, P1 e P2. |
| 11 | Rejeição de dados fictícios | Regra explícita de dados fictícios e auditoria canônica. |
| 12 | Fontes de verdade por domínio | Cadeia ARQUIVO-MÃE → SQL/GameState → serviços → gateway → tRPC. |
| 13 | Compatibilidade de migrações SQLite | Migrações idempotentes, monotônicas e schema versionado. |
| 14 | Revisão do arquivo-mãe | Regra de hash, revisão e evidência antes de alterações. |
| 15 | Balanceamento com fórmula | Seção de decisões de balanceamento com versão, entradas e faixa. |
| 16 | Reprodutibilidade por seed | Campo seed persistido no contexto e audit trail. |
| 17 | Calendário de temporada | Marco de temporada completa em GameState temporário. |
| 18 | Prioridade do ciclo semanal | Primeiro marco funcional definido como ciclo semanal jogável. |
| 19 | Medição de dívida técnica | Revisão técnica e medição a cada checkpoint. |
| 20 | Matriz das 500 dependências | `roadmap_500_proximos_passos.md`, `roadmap_gate.json` e este charter. |
