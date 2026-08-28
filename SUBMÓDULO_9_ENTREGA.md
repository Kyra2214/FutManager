# Submódulo 9 — Polimento | Entrega Técnica

**Data:** 28 de agosto de 2026 (revisão final na mesma data)
**Status:** ✅ Concluído (9a StatusChip, 9b Empty/Loading states, 9c timing — auditoria; 9d som/háptico deliberadamente fora de escopo)
**Impacto:** Baixo — 100% compatível com fluxos existentes, nenhum contrato de dados alterado

---

## Resumo da mudança

Fase 3 do plano visual ("Polimento") tinha quatro frentes com risco e escopo
bem diferentes. Cada uma foi tratada separadamente em vez de forçar um único
"concluído": duas viraram componentes novos e reutilizáveis (StatusChip,
EmptyState), uma foi só uma auditoria documentada (timing de transições) e a
última (som/feedback háptico) foi deliberadamente adiada, com a justificativa
registrada em `docs/PLANO_MUDANCA_VISUAL.md`.

## Arquivos criados

- **`frontend/client/src/components/StatusChip.tsx`** — rótulo de status com
  ícone opcional, tom semântico (grass/cobalt/coral/ink/neutral) e badge
  opcional. Usa somente tokens de cor já existentes em `:root`.
- **`frontend/client/src/components/EmptyState.tsx`** — estado vazio
  genérico (ícone + título + descrição + ação opcional), generalizando o
  padrão visual que já existia em `.hud-empty-state` (Submódulo 8).
- **`frontend/client/src/components/LoadingState.tsx`** — estado de
  carregamento (ícone `Loader2` girando + rótulo), criado na continuação
  desta etapa para distinguir visualmente "carregando" de "vazio de
  verdade" — os dois compartilhavam a mesma classe/aparência antes.

## Arquivos modificados

- **`frontend/client/src/components/PlayerCard.tsx`** — status
  Titular/Reserva trocado de texto puro para `StatusChip`.
- **`frontend/client/src/components/StaffEconomyPanel.tsx`** — dois estados
  vazios (equipe ativa, departamentos) trocados de `<p className="ct-state-empty">`
  para `EmptyState`, um deles com ação "Ir para o Mercado".
- **`frontend/client/src/pages/Home.tsx`** — estado vazio do elenco e do
  calendário trocados de `.entity-lookup-empty` para `EmptyState`; estado de
  carregamento do elenco e o par carregando/vazio do ledger financeiro
  migrados para `LoadingState`/`EmptyState`, separando os dois.
- **`frontend/client/src/components/OperationsPanel.tsx`** — os dois pares
  carregando/vazio (snapshots, auditoria de restauração) migrados da mesma
  forma.
- **`frontend/client/src/index.css`** — blocos `.status-chip*`,
  `.empty-state` e `.loading-state` adicionados ao final do arquivo.

## O que NÃO foi alterado (decisão de escopo)

- `.muted-status` (usada em `.layer-row`), `.asset-ready/.asset-warning/
  .asset-missing/.asset-pending` (prévia de identidade), o `em` de
  `.stadium-component` e `.finance-alert.is-warning/.is-ok` continuam como
  estavam — cada um já tem tratamento visual próprio adequado ao seu painel.
- A única dica de formulário que ainda usa `.entity-lookup-empty` ("Informe
  uma identificação...") não é carregamento nem vazio — é instrução de
  preenchimento, então ficou como texto simples.
- `.competition-empty`, `.result-empty`, `.sponsor-empty`,
  `.stadium-operations.empty`, `.economy-empty` e `.empty-panel` mantidos
  como estão — têm identidade editorial própria por painel.
- Som e feedback háptico não implementados — ver justificativa detalhada em
  `docs/PLANO_MUDANCA_VISUAL.md`, seção 9d.

## Testes realizados

✅ **TypeScript (parcial):** build oficial (`vite build`) não executado —
ambiente sem `node_modules`/rede (`npm ping` → 403). Como validação
alternativa, rodei o `tsc` global do ambiente (`--noEmit --jsx react-jsx
--skipLibCheck`, sem o `tsconfig`/`node_modules` reais do projeto) sobre
todos os arquivos criados/alterados. Todos os erros retornados são
explicados por rodar fora do projeto real (tipos de `react/jsx-runtime`
ausentes, `lib` sem `es2021` para `replaceAll`) ou são pré-existentes em
arquivos não tocados (`App.tsx`, `ErrorBoundary.tsx`, `ThemeContext.tsx`) —
nenhum erro nos arquivos desta etapa. Recomenda-se rodar `pnpm install &&
pnpm exec tsc --noEmit && pnpm exec vite build` assim que houver rede, para
a validação oficial completa.
✅ **Queries:** nenhuma query nova, nenhum contrato tRPC alterado.
✅ **Compatibilidade:** nenhuma classe CSS existente foi removida; toda
mudança é substituição de JSX de apresentação por componentes equivalentes
ou aditivos.

## Compatibilidade

- **Contratos de dados (tRPC):** Nenhum novo
- **Rotas:** Nenhuma nova
- **Breaking changes:** Nenhum
- **Reversível:** sim — as trocas de JSX podem ser revertidas linha a linha
  sem tocar em nenhum outro sistema

## Próximos passos

- Rodar `tsc --noEmit`/`vite build` num ambiente com `node_modules` para
  confirmar a validação automática que os Submódulos 1–8 tiveram.
- Se o Submódulo 9 for retomado: migrar os estados de carregamento restantes
  para um tratamento visual próprio (distinto de "vazio"), e decidir se vale
  a pena introduzir som/feedback háptico como funcionalidade de produto
  (fora do escopo puramente visual deste plano).
