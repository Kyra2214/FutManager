import React from "react";
import type { LucideIcon } from "lucide-react";

/**
 * StatusChip — Submódulo 9 (Polimento), ver docs/PLANO_MUDANCA_VISUAL.md.
 *
 * Uniformiza os vários rótulos de status soltos pelo app (texto puro em
 * `.muted-status`, classes ad hoc como `.asset-ready`/`.asset-warning`, `em`
 * verde em `.stadium-component`, etc.) num único componente: ícone opcional
 * + label + tom semântico, com badge numérico opcional.
 *
 * Não substitui esses usos automaticamente — cada um tem contexto e leiaute
 * próprio (ver Submódulo 9 no plano para o que foi migrado nesta etapa e o
 * que fica para depois). É aditivo: os componentes que já funcionam
 * continuam como estavam até serem tocados deliberadamente.
 *
 * Tons reaproveitam os tokens já existentes em `:root` — nenhuma cor nova:
 *   grass  → positivo / ativo / pronto
 *   cobalt → neutro-informativo / em andamento
 *   coral  → atenção / alerta
 *   ink    → neutro forte (texto padrão, sem conotação)
 *   neutral→ neutro fraco (estado padrão sem destaque, ex.: "Reserva")
 */
export type StatusChipTone = "grass" | "cobalt" | "coral" | "ink" | "neutral";

export function StatusChip({
  label,
  tone = "neutral",
  icon: Icon,
  badge,
  compact = false,
}: {
  label: string;
  tone?: StatusChipTone;
  icon?: LucideIcon;
  badge?: string | number;
  compact?: boolean;
}) {
  return (
    <span className={`status-chip status-chip-${tone}${compact ? " status-chip-compact" : ""}`}>
      {Icon ? <Icon size={compact ? 10 : 12} /> : null}
      <em>{label}</em>
      {badge !== undefined ? <b>{badge}</b> : null}
    </span>
  );
}
