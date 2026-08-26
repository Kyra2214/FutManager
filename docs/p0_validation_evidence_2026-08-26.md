# Evidência de validação P0 — 2026-08-26

## Resultado

A validação governada executada após a consolidação do Front P0-1 retornou sucesso nos três validadores: `validate_roadmap_gate.py`, `validate_mutation_paths.py` e `validate_p0_governance.py`. O gate global permanece `P0_GATE=CLOSED`, a consolidação incremental é aceita e P1/P2 continuam bloqueados.

| Verificação | Resultado |
|---|---|
| Roadmap | 500 itens, 25 fronts, 11 fronts P0, 12 fronts P1 e 2 fronts P2 |
| Fonte única | SQL/GameState declarada e validada |
| Caminhos de mutação | 5 routers, 27 dispatches autorizados, sem escrita paralela no frontend |
| Charter P0-1 | 20 critérios e 20 linhas item→evidência válidos |
| Testes frontend | 47 testes aprovados em 14 arquivos |
| TypeScript | `tsc --noEmit` aprovado |
| Build | Vite/esbuild aprovado; apenas avisos não bloqueantes de asset runtime e tamanho de chunk |
| Testes do motor | 141 testes Python aprovados |

## Decisão de gate

O Front P0-1 está `CONSOLIDATED` no `roadmap_gate.json`. Os fronts P0 restantes continuam `PENDING`; portanto, não há autorização para abrir P0 nem iniciar itens P1/P2.

## Auditoria P0-3 — banco e migrações

A auditoria read-only `scripts/validate_p0_database.py` verificou os dois bancos oficiais. O banco-base possui 7 tabelas e hash SHA-256 conferido contra o manifesto; o GameState possui 97 tabelas, `schema_version=2` e os índices de ledger esperados disponíveis. Ambos retornaram `integrity_check=ok` e zero erros em `foreign_key_check`. Índices específicos do ciclo não são exigidos no banco-base imutável quando suas tabelas não existem.
