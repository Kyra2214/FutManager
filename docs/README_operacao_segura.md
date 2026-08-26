# FutManager — instalação e operação segura

O projeto é composto por frontend React/tRPC e motor Python com SQLite. O frontend deve ser iniciado com `pnpm install` e `pnpm dev`; o motor deve ser executado usando uma cópia de `data/state/game.db`. O arquivo `data/database/game.db` é somente leitura e não pode ser utilizado como destino de writers.

Antes de publicar, executar `pnpm exec tsc --noEmit`, `pnpm test`, `pnpm run build`, a suíte Python e os validadores P0. Antes de uma mutação, confirmar que o caminho do banco passa por `assert_mutable_state_path`, que `PRAGMA foreign_keys=ON` está ativo e que `PRAGMA integrity_check` retorna `ok`.

Segredos são fornecidos por variáveis de ambiente do ambiente Manus; arquivos `.env`, tokens, cookies e credenciais não devem ser versionados. Exportações devem usar `scripts/export_state_manifest.py`, que produz uma cópia SQLite, hash e manifesto sem segredos. Recuperações seguem `docs/procedimento_recuperacao_checkpoint.md`.

O frontend não calcula saldos, resultados, regras esportivas ou estados contratuais. Toda escrita percorre tRPC, gateway, serviço Python e SQL/GameState.
