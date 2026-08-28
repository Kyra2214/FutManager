# Política de execução do roadmap FutManager/Brasfoot

## Regra central

> **P1 e P2 permanecem bloqueados até que todos os itens P0 estejam consolidados.**

A consolidação de um P0 exige implementação no módulo correto, migração idempotente quando houver persistência, testes automatizados, `PRAGMA integrity_check = ok`, `PRAGMA foreign_key_check` sem ocorrências, documentação da decisão e evidência registrada no gate. Um P0 parcialmente implementado, apenas desenhado ou validado somente no frontend não é consolidado.

| Nível | Pode iniciar quando | Critério de liberação |
|---|---|---|
| P0 | Imediatamente, respeitando dependências internas. | Cada item precisa atender todos os critérios de consolidação. |
| P1 | Somente após `P0_GATE=OPEN`. | Todos os P0 estão consolidados, o estado SQL está íntegro e o checkpoint foi salvo. |
| P2 | Somente após `P0_GATE=OPEN` e os P1 necessários. | Dependências P0/P1 explícitas, testes e checkpoint aprovados. |

## Fonte única da verdade

O estado de carreira, jogadores, clubes, partidas, calendário, classificação, estádio, torcida, público, caixa, ledger, folha, patrocinadores, missões e eventos deve existir no **SQLite/GameState**. Durante o desenvolvimento, o banco-base canônico é somente leitura e o GameState é o estado mutável de testes. Na distribuição Android híbrida, o GameState sanitizado é publicado no pacote versionado de `Kyra2214/FutManager-data` e baixado na primeira execução; ele não deve ser embutido no APK.

O frontend não deve manter um estado esportivo paralelo, calcular saldo, inventar jogadores, aceitar propostas automaticamente ou escrever diretamente no banco. Leituras seguem `SQL/GameState → serviço → gateway Python → tRPC → React`; mutações seguem `React → tRPC → gateway Python → serviço transacional → SQL/GameState`. Qualquer regra que exista somente no React, em um fixture, em mock de produção ou em uma segunda base é considerada não consolidada.

## Processo obrigatório para cada passo

Antes de iniciar um item, registrar o ID, a prioridade, as dependências e as tabelas/serviços afetados. Durante a implementação, manter uma única unidade transacional para cada comando de domínio. Depois, executar testes de sucesso, erro, rollback, idempotência e determinismo quando aplicável. Por fim, validar as bases de desenvolvimento, o seed sanitizado do pacote remoto e o contrato do APK híbrido, salvar checkpoint e atualizar o gate.

Um item P1/P2 iniciado enquanto o gate estiver fechado deve ser tratado como bloqueado, mesmo que seu código seja tecnicamente independente. A exceção é documentação, análise de dependência ou preparação não executável; ela não pode alterar o estado do jogo nem ser apresentada como funcionalidade concluída.

## Gate inicial

O roadmap atual começa com `P0_GATE=CLOSED`. Os P0 devem ser consolidados em ordem de dependência. O primeiro passo executável é revisar a matriz P0, confirmar cobertura de testes e registrar o primeiro checkpoint de governança. Até essa evidência existir, a equipe não deve iniciar implementação de itens P1 ou P2.

O arquivo `scripts/validate_roadmap_gate.py` valida a presença do gate, a contagem de itens P0/P1/P2 e a inexistência de liberação indevida. Ele não altera banco de jogo e não substitui os testes do motor.

## Exceções de escrita no dispatcher

O `career_gateway.py` **não possui exceções legítimas de escrita mutável direta**. Consultas diretas do dispatcher são somente leituras `SELECT` para montar respostas. Toda escrita — inclusive início de carreira, bootstrap, contratação, evolução, preço de ingresso, avanço semanal e leitura de alertas — deve ser delegada ao serviço de domínio correspondente, que usa a conexão SQLite recebida e aplica suas próprias regras transacionais. Se uma necessidade futura exigir escrita direta no dispatcher, ela deve ser recusada até ser convertida em método de serviço, coberta por teste e aprovada como nova decisão arquitetural.

O validador `scripts/validate_mutation_paths.py` verifica o mapa completo das ações presentes no dispatcher, confirma 27 dispatches autorizados, procura SQL mutável direto no gateway e verifica que o frontend não contém SQLite, comandos SQL de escrita ou operações de arquivo para estado de jogo.
