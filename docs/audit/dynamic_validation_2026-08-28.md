# Log de validação dinâmica — 2026-08-28

## Backend Python

Com `engine/data/database/game.db` e `engine/data/state/game.db` descompactados a partir dos arquivos versionados, o comando `PYTHONPATH=.:engine:engine/tests python3 -m pytest --import-mode=importlib -q engine/tests` terminou com **366 passed**.

O contador estático `engine/scripts/count_tests.py` registra **315 declarações Python**. A diferença para o total executado decorre de parametrizações e de casos expandidos pelo pytest; o relatório executivo publica a métrica estática com sua fonte explícita, e este log preserva o resultado real da execução.

## Frontend com root arbitrário

Com uma cópia temporária completa de `engine/`, `FUTMANAGER_ENGINE_ROOT` e `FUTMANAGER_ENGINE_STATE_PATH` apontando para essa cópia fora do caminho original, `pnpm check`, `pnpm test` e `pnpm build` terminaram com sucesso. A execução Vitest reportou **19 arquivos e 67 testes executados**.

## Simulações

A simulação de temporada e a simulação competitiva terminaram com `PASS`. A temporada competitiva confirmou **1.520 fixtures** e **1.520 resultados**.

## Performance

A nova medição da simulação competitiva, executada com timestamps do shell no mesmo ambiente, foi de **75 segundos**. O baseline registrado no roadmap era de aproximadamente 124 segundos; a medição atual não indica regressão e deve ser tratada como novo ponto de comparação.

## Integridade do pacote

`release_seed.py validate engine/data/state/game.db.gz` confirmou contagem zero em `manager_selection_assignments`, `manager_careers` e `managers`. `validate_delivery.py` confirmou `integrity_check = ok` e `manifest_matches = true` para os dois arquivos `.gz` versionados.

## Android

Na branch `android-roadmap-corrections`, `pnpm android:sync` foi executado com `FUTMANAGER_ENGINE_ROOT` e `FUTMANAGER_ASSET_ROOT` configurados para o checkout. O APK release foi montado com Gradle 8.14.3, API 36 e JDK 21. `pnpm android:validate-apk` encontrou `assets/public/assets/databases/game.db`, confirmou `integrity_check = ok` e contagem zero nas três tabelas de carreira.
