# Submódulo 8 — Dashboard como HUD | Entrega Técnica

**Data:** 28 de agosto de 2026
**Status:** ✅ Concluído e validado
**Impacto:** Baixo — 100% compatível com fluxos existentes

---

## Resumo da mudança

A página inicial do dashboard ("Seu Clube") recebeu um novo componente HUD que apresenta os quadrantes estruturais do clube (Escalação, Comissão, Estádio, Prospecção) com layout tipo jogo, em vez de lista genérica.

## Arquivos criados

- **`frontend/client/src/components/ClubHUD.tsx`** (262 linhas)
  - Componente React que encapsula a leitura dos 4 quadrantes
  - Reutiliza `FormationPitch` (Submódulo 5) para visualização de escalação
  - Estados vazios honestosm sem inventar dados
  - Entrada cascata com fade + slide-in, respeitando `prefers-reduced-motion`

## Arquivos modificados

### `frontend/client/src/pages/Home.tsx`
- **Linha 13-14:** Adicionar import de `ClubHUD`
- **Linha 170:** Inserir seção HUD logo após hero panel
  ```tsx
  {workspace && <section className="hud-section">
    <ClubHUD workspace={workspace} onNavigateToMarket={() => onSectionChange("mercado")} onUpdateInfo={() => { utils.club.workspace.invalidate(); }} />
  </section>}
  ```

### `frontend/client/src/index.css`
- **Linhas 738–930:** Bloco completo `.club-hud` com:
  - `.hud-status-bar` — barra de status topo (saúde, comissão, sincronização)
  - `.hud-grid` — layout responsivo 2×2 de quadrantes
  - `.hud-quadrant*` — estilos dos quadrantes grande/mini
  - `.hud-mini-stat` / `.hud-mini-action` — componentes internos
  - `.hud-bench-*` — micro-lista de reservas
  - `.hud-empty-state` / `.hud-footer` — states
  - Animações cascata + pulse
  - Breakpoint responsivo 760px

## Testes realizados

✅ **TypeScript:** `tsc --noEmit` — sem erros novos
✅ **Build:** `vite build` — build de produção concluído
✅ **Queries:** nenhuma query nova, reutiliza `workspace` existente
✅ **Compatibilidade:** Dashboard funciona com e sem dados

## Compatibilidade

- **Contatos de dados (tRPC):** Nenhum novo
- **Rotas:** Nenhuma nova
- **Breaking changes:** Nenhum
- **Fallback:** Reutiliza lógica de empty states já validada

## Layout

```
┌─ HERO PANEL (existente) ─────────────────┐
├─ HUD STATUS BAR (novo)                   │
├─ HUD GRID (novo)                         │
│  ├─ QUADRANTE GRANDE: ESCALAÇÃO          │
│  │  ├─ FormationPitch (reuso)            │
│  │  └─ Banco de reservas (mini-lista)    │
│  ├─ Quadrante mini: COMISSÃO             │
│  ├─ Quadrante mini: ESTÁDIO              │
│  └─ Quadrante mini: PROSPECÇÃO           │
├─ HUD FOOTER (novo)                       │
├─ MÉTRICAS ANTIGAS (preservadas)          │
├─ PRODUÇÃO INDIVIDUAL (preservada)        │
└─ SITUAÇÃO ATUAL (preservada)             │
```

## Próximos passos

Submódulo 9 (Polimento):
- Som e feedback háptico (opcional)
- Empty states uniformizados (StatusChip)
- Timing de transições revisado
