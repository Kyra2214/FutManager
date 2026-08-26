# Evidência individual dos passos 471–499

| Passo | Evidência verificável |
|---:|---|
| 471 | Rollback seguro no motor, `assert_mutable_state_path` e procedimento de recuperação; cobertura em `tests/test_state_store.py` e `tests/test_validate_delivery.py`. |
| 472 | `client/src/components/DashboardLayoutSkeleton.tsx` usa `Skeleton` por blocos de navegação, perfil, conteúdo e cards. |
| 473 | `Home.tsx` apresenta estados vazios com próxima ação; testes de loading/empty/error/sucesso em `server/matchesPage.loading.test.tsx` e testes de CT. |
| 474 | Mensagens de erro e estados de ausência estão em português em Home, CT, partidas e gateway; cobertura UI aprovada. |
| 475 | Filtros de atleta e competição são persistidos por seção via `sessionStorage` em `Home.tsx`, com consultas tRPC estáveis. |
| 476 | Captura visual em 375×812 nas rotas `/`, `/partidas` e `/financas`, sem overflow crítico observado. |
| 477 | Captura visual em 768×900 nas rotas principais, com sidebar e conteúdo responsivos. |
| 478 | Captura visual em 1440×900 nas rotas principais, com composição ampla e sem overflow crítico. |
| 479 | Decisões visuais registradas em `docs/roadmap_registered_steps.md`, `docs/checklist_release_371_470.md` e documentação de domínio. |
| 480 | Revisão visual executada junto das capturas responsivas e validação do build. |
| 481 | Suíte Python completa executada e aprovada na validação final do marco. |
| 482 | Suíte Vitest completa: 14 arquivos e 52 testes aprovados; typecheck também aprovado. |
| 483 | `pnpm exec tsc --noEmit` aprovado após o ajuste de persistência de filtros. |
| 484 | `pnpm run build` aprovado com Vite/esbuild; somente avisos não bloqueantes de asset/runtime e chunk size. |
| 485 | `validate_shared_gateway_contracts.py`, `validate_mutation_paths.py` e testes de gateway aprovados. |
| 486 | Testes de concorrência/idempotência em mercado, economia, contratos e ticks aprovados; writers usam transações SQL. |
| 487 | Rollback por etapa coberto pelos testes de ciclo, economia, mercado, contrato e simulação; validadores P0 retornaram `VALID`. |
| 488 | Idempotência coberta por writers de ticks, mercado, contratos, treino, simulação e serviços econômicos. |
| 489 | Seeds persistidas em decisões/partidas/simulação; testes de IA e simulação aprovados. |
| 490 | GameState temporário usado nos cenários de partida, simulação e integração do gateway; banco-base protegido. |
| 491 | Transição e histórico de temporadas cobertos pelos serviços de calendário, contratos e competições; validação de schema passou. |
| 492 | `validate_mutation_paths.py` e `validate_p0_database.py` confirmam que a base imutável não recebe writes. |
| 493 | `PRAGMA integrity_check` retornou `ok` e `foreign_key_check` retornou zero erros para base e estado. |
| 494 | `scripts/export_state_manifest.py` e `docs/procedimento_recuperacao_checkpoint.md`; `RESTORE_SMOKE=ok` em cópia temporária. |
| 495 | Relatório agregado em `docs/relatorio_qualidade_entrega.md`, com resultados e hashes. |
| 496 | Benchmark do serviço de simulação e contagem de entidades persistidas documentados; consulta é read-only e reproduzível. |
| 497 | `WorldSimulationService.benchmark` registra temporada, nível, amostra, duração e transações por partida. |
| 498 | Instalação e operação segura em `docs/README_operacao_segura.md`. |
| 499 | `docs/manifesto_marco_371_470.json` contém hashes reais do ZIP, base imutável e GameState, sem segredos. |

## Evidência de execução

A validação final foi executada em 26/08/2026: Python completo e compilação passaram; Vitest completo passou com 14 arquivos/52 testes; TypeScript e build passaram; `P0_GATE=OPEN`; validadores de gateway, banco, entrega e frontend retornaram `ok`/`VALID`; exportação e smoke de restauração passaram; capturas foram feitas em 375, 768 e 1440 pixels.
