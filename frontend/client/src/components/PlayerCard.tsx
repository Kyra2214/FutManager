import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Star, Trophy } from "lucide-react";
import { StatBar } from "@/components/StatBar";
import { StatusChip } from "@/components/StatusChip";

/**
 * PlayerCard — substitui a linha de tabela do elenco (`.roster-row`) por um
 * "componente de jogo": badge de posição, CR em destaque (número grande,
 * estilo cartão), StatBar para o potencial (CR2, 0..99) e selos de
 * estrela / topo mundial quando aplicável.
 *
 * Reaproveitável fora da view de elenco (scouting, seletor de substituições)
 * — ver Submódulo 2 em docs/PLANO_MUDANCA_VISUAL.md.
 *
 * Submódulo 4 (micro-motion): o cartão entra com fade + leve subida ao
 * montar. `index` (opcional, posição do cartão na grade) gera um atraso
 * escalonado para o efeito de "cascata" — o componente fica autossuficiente
 * (não depende de um container orquestrador do framer-motion no lugar onde
 * é usado), então continua reaproveitável em telas futuras sem exigir
 * nenhum wrapper extra. Respeita `prefers-reduced-motion`.
 *
 * Submódulo 9 (polimento): o status (Titular/Reserva) trocou de texto puro
 * (`.muted-status`) para `StatusChip`, uniformizando com o restante do
 * polimento de estados/rótulos descrito em docs/PLANO_MUDANCA_VISUAL.md.
 */
export interface PlayerCardData {
  playerId: number;
  name: string;
  age: number;
  position: string;
  status: string;
  category: string;
  cr1: number;
  cr2: number;
  side: string | null;
  star: boolean;
  topWorld: boolean;
}

export function PlayerCard({
  player,
  onClick,
  index = 0,
}: {
  player: PlayerCardData;
  onClick?: () => void;
  index?: number;
}) {
  const isStarter = player.status === "Titular";
  const hasBadges = player.star || player.topWorld;
  const prefersReducedMotion = useReducedMotion();
  const motionProps = {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    transition: {
      duration: prefersReducedMotion ? 0 : 0.28,
      delay: prefersReducedMotion ? 0 : Math.min(index, 12) * 0.035,
      ease: "easeOut" as const,
    },
  };

  const content = (
    <>
      <div className="player-card-top">
        <span className="player-card-position">{player.position}</span>
        <StatusChip tone={isStarter ? "grass" : "neutral"} label={player.status} compact />
      </div>
      <div className="player-card-cr">
        <b>{player.cr1}</b>
        <small>CR</small>
      </div>
      <div className="player-card-name">
        <b>{player.name}</b>
        <small>
          {player.age} anos{player.side ? ` · ${player.side}` : ""} · {player.category}
        </small>
      </div>
      {hasBadges ? (
        <div className="player-card-badges">
          {player.star ? (
            <span className="player-card-badge">
              <Star size={11} /> Estrela
            </span>
          ) : null}
          {player.topWorld ? (
            <span className="player-card-badge">
              <Trophy size={11} /> Topo mundial
            </span>
          ) : null}
        </div>
      ) : null}
      <StatBar label="POTENCIAL" value={player.cr2} max={99} compact />
    </>
  );

  if (onClick) {
    return (
      <motion.button type="button" className="player-card player-card-button" onClick={onClick} {...motionProps}>
        {content}
      </motion.button>
    );
  }

  return (
    <motion.div className="player-card" {...motionProps}>
      {content}
    </motion.div>
  );
}
