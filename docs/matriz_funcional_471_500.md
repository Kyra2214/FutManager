# Matriz funcional dos passos 471–500

| Passo | Requisito real | Prova funcional | Saída observada |
|---:|---|---|---|
| 471 | Desfazer somente comando seguro | `tests/test_safe_undo.py` executa registro, undo e repetição | `2 passed`; segunda execução idempotente |
| 472 | Skeleton específico para tabelas | `server/TableSkeleton.ui.test.tsx` renderiza 3×4 células | `1 passed`; 12 skeletons acessíveis |
| 473 | Empty state com próxima ação | `CtHiringShortcuts.ui.test.tsx` e `matchesPage.loading.test.tsx` | estados vazios orientam Mercado/consulta |
| 474 | Erros em português | testes UI de CT e partidas | mensagens de ausência/erro em português |
| 475 | Filtro persistente por seção | `Home.tsx` persiste filtros em `sessionStorage` e usa input tRPC memoizado | filtros restauram após remontagem |
| 476 | Visualização 375px | captura de `/`, `/partidas`, `/financas` em viewport 375 | layout sem overflow crítico observado |
| 477 | Tablet 768px | captura das mesmas rotas em 768×900 | sidebar/conteúdo responsivos |
| 478 | Desktop 1440px | captura das mesmas rotas em 1440×900 | composição ampla validada |
| 479 | Decisões de composição | `docs/checklist_release_371_470.md` e documentação editorial | decisões registradas |
| 480 | Revisão visual por domínio | capturas após alterações e preview WebDev | revisão visual registrada |
| 481 | Suíte Python por checkpoint | `audit_functional_471_500.py` executa `pytest -q` | exit code 0 |
| 482 | Vitest por checkpoint | auditoria executa `vitest run` completo | exit code 0 |
| 483 | TypeScript antes da entrega | auditoria executa `tsc --noEmit` | exit code 0 |
| 484 | Build antes de publicar | auditoria executa `pnpm run build` | exit code 0 |
| 485 | Contratos Python↔TypeScript | `validate_shared_gateway_contracts.py` | exit code 0 |
| 486 | Concorrência SQLite | testes de mercado/economia/contratos | transação vencedora e rollback verificados |
| 487 | Rollback por etapa | testes de ciclo e `test_state_store.py` | estado restaurado sem débito parcial |
| 488 | Idempotência por writer | testes de ticks, mercado, treino, contratos e undo | repetições não duplicam efeitos |
| 489 | Determinismo por seed | testes de simulação/social/IA | mesmo contexto reproduz a saída |
| 490 | Temporada completa | `test_final_roadmap_evidence.py` cria cenário temporário | cenário executável isolado |
| 491 | Múltiplas temporadas | mesmo teste insere 2026 e 2027 | 2 temporadas distintas observadas |
| 492 | Não alteração da base | `validate_mutation_paths.py` e guardas de caminho | exit code 0 |
| 493 | Integridade/foreign keys | `validate_p0_database.py` e benchmark read-only | `integrity=ok`, `foreign_key_errors=0` |
| 494 | Recuperação interrompida | `docs/procedimento_recuperacao_checkpoint.md` e smoke de restauração | `RESTORE_SMOKE=ok` |
| 495 | Cobertura por domínio | `docs/relatorio_qualidade_entrega.md` e auditoria funcional 10/10 | relatório versionado |
| 496 | Bootstrap de 8.399 clubes | `benchmark_final_roadmap.py` consulta GameState em modo `ro` | `count=8399`, 3.176 ms no ensaio |
| 497 | Avanço mundial | mesmo benchmark mede partidas programadas em consulta separada | métrica registrada, 0 pendentes no estado atual |
| 498 | README seguro | `docs/README_operacao_segura.md` | instruções versionadas |
| 499 | Manifesto/hash | `docs/manifesto_marco_371_470.json` e `benchmark_final_471_499.json` | hashes e integridade registrados |
| 500 | Checkpoint antes de publicação | `docs/auditoria_checkpoints_publicacoes.md` + histórico Git | cadeia de marcos até `e0480c91` |

## Comandos funcionais executados

A auditoria funcional executou 10 verificações reais em 26/08/2026: suíte Python, Vitest, TypeScript, build, SafeUndo/temporadas, contratos, mutações, banco, benchmark e auditoria item a item. Todas retornaram exit code 0. A cobertura de UI foi ainda reforçada com `TableSkeleton.ui.test.tsx`, que passou junto dos estados críticos de loading/empty.
