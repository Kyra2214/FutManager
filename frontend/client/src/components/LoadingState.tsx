import React from "react";
import { Loader2 } from "lucide-react";

/**
 * LoadingState — Submódulo 9 (Polimento), continuação.
 *
 * Fecha a lacuna registrada em docs/PLANO_MUDANCA_VISUAL.md (Submódulo 9b):
 * vários pontos do app reaproveitavam `.entity-lookup-empty`/`.ct-state-empty`
 * tanto para "carregando" quanto para "vazio de verdade" — mesmo texto cinza
 * sem nenhuma pista visual de qual dos dois estados é. `LoadingState` dá ao
 * carregamento um tratamento distinto (ícone girando, sem borda tracejada),
 * para que só o `EmptyState` (borda tracejada, ícone parado) signifique
 * "não há dados" e o carregamento pareça obviamente transitório.
 *
 * Reaproveita `.spin`/`animate-spin`, já usados em `InteractiveMatchCenter`
 * e `AIChatBox` — nenhuma animação nova.
 */
export function LoadingState({ label }: { label: string }) {
  return (
    <div className="loading-state">
      <Loader2 size={16} className="spin" />
      <span>{label}</span>
    </div>
  );
}
