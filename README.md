# FutManager/Brasfoot

O projeto é composto pelo frontend React/tRPC em `futmanager_frontend` e pelo motor Python/SQLite em `brasfoot_engine`. O estado mutável do jogo reside exclusivamente no GameState SQL; o banco-base canônico é somente leitura para serviços mutáveis.

## Operação segura

Use Python 3.11 no motor e Node.js com pnpm no frontend. Os writers devem receber uma cópia temporária ou o GameState autorizado; o guard de caminho rejeita escrita em `data/database/game.db`. Antes de qualquer entrega, execute os validadores P0, a suíte Python, `pnpm exec tsc --noEmit`, `pnpm test` e `pnpm run build`.

O frontend consulta o gateway por tRPC. Não introduza regras esportivas, placares, caixa, elenco ou calendário em estado React permanente. Estados de loading, vazio e erro devem refletir a leitura persistida do motor. Consulte `roadmap_gate.json` antes de iniciar qualquer frente P1/P2.

## Validação

Os relatórios em `docs/` registram matrizes, hashes, inventários e limitações. O pacote final deve conter frontend, motor, bancos autorizados, ativos e documentação, acompanhado de manifesto e SHA-256. Nunca execute migrations destrutivas no banco-base.
