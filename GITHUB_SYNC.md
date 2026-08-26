# Sincronização do FutManager com GitHub

O repositório `Kyra2214/FutManager` é o destino oficial do código do projeto a partir de 26 de agosto de 2026.

## Conteúdo versionado

O primeiro commit reúne o motor Python, o frontend React/tRPC, testes, scripts, documentação, roadmap e ativos visuais. Dependências instaladas, builds gerados, caches, logs, metadados Git e configurações locais não fazem parte do commit.

## Bancos SQLite

Os bancos oficiais são entregues no ZIP completo gerado pelo projeto, porque os arquivos têm dezenas de megabytes e não devem ser versionados diretamente no primeiro commit. O pacote inclui `engine/data/database/game.db` como base imutável e `engine/data/state/game.db` como GameState. Operações mutáveis devem usar o GameState ou uma cópia temporária.

## Fluxo futuro

Alterações do motor e do frontend devem ser feitas nas árvores de trabalho correspondentes, validadas com os testes Python/Vitest, typecheck e build, e então sincronizadas para este repositório em commits pequenos e descritivos. Nunca adicionar credenciais, arquivos de configuração local ou dumps contendo dados sensíveis.

## Estado inicial

O primeiro commit deve ser criado na branch `main`, com uma mensagem que identifique a entrega inicial do FutManager e o estado do roadmap. Após o push, a árvore remota deve ser conferida pela API do GitHub.
