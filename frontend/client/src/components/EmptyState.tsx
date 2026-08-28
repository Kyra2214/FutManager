import React from "react";
import type { LucideIcon } from "lucide-react";

/**
 * EmptyState — Submódulo 9 (Polimento), ver docs/PLANO_MUDANCA_VISUAL.md.
 *
 * Generaliza o padrão já usado em `.hud-empty-state` (Submódulo 8: ícone
 * apagado + título + frase + ação) para uso fora do HUD, com o mesmo visual
 * (mesma classe-base `.empty-state`, reaproveitada — nenhuma cor nova).
 *
 * Este componente NÃO substitui todo estado vazio do app: painéis com
 * tratamento editorial próprio (`.empty-panel` do dashboard escuro,
 * `.competition-empty`, `.sponsor-empty`, `.stadium-operations.empty`, o
 * placar de `.result-empty`) continuam como estão — cada um já tem
 * identidade visual pensada para o contexto específico (ver decisões de
 * escopo dos Submódulos 3, 6 e 7). `EmptyState` é para os textos soltos que
 * reaproveitavam `.entity-lookup-empty`/`.ct-state-empty` apenas como frase
 * cinza sem ícone nem ação — esses são os "estados vazios genéricos" que o
 * plano descreve como pendência do Submódulo 9.
 */
export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
}: {
  icon: LucideIcon;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="empty-state">
      <Icon size={28} />
      <h3>{title}</h3>
      {description ? <p>{description}</p> : null}
      {actionLabel && onAction ? (
        <button type="button" className="outline-action" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
