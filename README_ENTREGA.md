# FutManager — pacote completo do estado atual

Este pacote reúne o estado atual do motor Python, frontend React/tRPC, bancos SQLite, ativos visuais e documentação do FutManager.

## Estrutura

- `engine/`: motor Python, gateway, scripts, testes, documentação e os bancos `data/database/game.db` (base) e `data/state/game.db` (GameState).
- `frontend/`: aplicação React 19 + TypeScript + tRPC, testes Vitest, configuração e roadmap persistido.
- `assets/`: ativos visuais usados pelo projeto.
- `metadata/`: manifestos e informações desta entrega.

## Execução do motor

Use Python 3.11 ou superior. O banco-base deve ser tratado como imutável; operações mutáveis devem usar uma cópia do GameState.

```bash
cd engine
python3 -m pytest -q
python3 scripts/career_gateway.py current --database data/state/game.db
```

## Execução do frontend

Use Node.js 22 e pnpm. O diretório de dependências não está incluído no ZIP; instale-as antes de executar.

```bash
cd frontend
pnpm install
pnpm test
pnpm exec tsc --noEmit
pnpm run build
```

## Fonte única da verdade

O estado de jogo e as regras mutáveis pertencem ao SQL/GameState e aos serviços Python autorizados. O frontend consulta por tRPC/read models e não deve calcular ou persistir saldos, escalações, resultados ou níveis de infraestrutura.

## Situação do roadmap

O roadmap persistido está em `frontend/todo.md`. Os passos detalhados chegam ao 370; os passos 371–500 ainda precisam ser definidos oficialmente antes de sua execução para preservar a ordem rigorosa.
