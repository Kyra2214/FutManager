import React from "react";
import { motion, useReducedMotion } from "framer-motion";

/**
 * StatBar — substitui pares "label → número" por uma barra preenchida,
 * com cor por faixa de valor. Uso: reputação, potencial, custo-benefício,
 * eficiência de departamento, ou qualquer métrica limitada (0..max).
 *
 * Faixas de cor (sobre a paleta editorial existente):
 *   < 40%  → --coral      (atenção / abaixo do esperado)
 *   40–70% → --cobalt      (padrão / estável)
 *   > 70%  → --grass       (destaque / forte)
 *
 * Submódulo 4 (micro-motion): o preenchimento agora anima de 0 até o valor
 * real ao montar, em vez de aparecer já cheio. Ver
 * docs/PLANO_MUDANCA_VISUAL.md — respeita `prefers-reduced-motion` via
 * `useReducedMotion` do framer-motion (duração cai para 0, sem reflow
 * extra: a barra some direto para a largura final).
 */
export type StatBarTone = "auto" | "coral" | "cobalt" | "grass" | "ink";

function toneForRatio(ratio: number): Exclude<StatBarTone, "auto"> {
  if (ratio >= 0.7) return "grass";
  if (ratio >= 0.4) return "cobalt";
  return "coral";
}

export function StatBar({
  label,
  value,
  max = 100,
  suffix = "",
  tone = "auto",
  compact = false,
}: {
  label: string;
  value: number;
  max?: number;
  suffix?: string;
  tone?: StatBarTone;
  compact?: boolean;
}) {
  const ratio = max > 0 ? Math.min(1, Math.max(0, value / max)) : 0;
  const resolvedTone = tone === "auto" ? toneForRatio(ratio) : tone;
  const display = Number.isInteger(value) ? String(value) : value.toFixed(1);
  const prefersReducedMotion = useReducedMotion();

  return (
    <div className={compact ? "stat-bar stat-bar-compact" : "stat-bar"}>
      <div className="stat-bar-head">
        <span>{label}</span>
        <b>{display}{suffix}</b>
      </div>
      <div className="stat-bar-track">
        <motion.div
          className={`stat-bar-fill stat-bar-fill-${resolvedTone}`}
          initial={{ width: 0 }}
          animate={{ width: `${ratio * 100}%` }}
          transition={{ duration: prefersReducedMotion ? 0 : 0.7, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}
