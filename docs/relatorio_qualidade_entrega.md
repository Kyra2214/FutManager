# Relatório de qualidade da entrega

A validação do marco 431–450 foi executada contra o motor Python e o frontend React/tRPC. Os validadores de governança, arquitetura, banco, frontend, partidas, economia, patrocínios, simulação e contratos compartilhados retornaram `VALID`; o `P0_GATE` retornou `OPEN`.

| Verificação | Resultado |
|---|---:|
| Testes Python de simulação/governança | 54 aprovados |
| Testes Python de IA | 52 aprovados |
| Testes Python de mercado | 9 aprovados |
| TypeScript | aprovado |
| Vitest focado | 11 aprovados |
| Build Vite/esbuild | aprovado |
| Integridade SQLite | `ok` |
| Foreign keys | 0 erros |
| Manifesto do banco-base | hash confere |
| ZIP de entrega anterior | `unzip -t` e SHA-256 conferidos |

Avisos não bloqueantes: o build informa um asset `/manus-storage` mantido para resolução em runtime e recomenda atualização do pacote `baseline-browser-mapping`; não houve erro de compilação ou typecheck.
