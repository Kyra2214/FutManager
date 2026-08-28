import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import type { PlayerCardData } from "@/components/PlayerCard";

/**
 * FormationPitch — substitui a grade plana de titulares por uma leitura de
 * formação tática: cada titular ocupa uma linha de campo (ataque / meio-campo
 * / defesa / goleiro) em vez de aparecer como mais um cartão igual aos
 * demais na grade.
 *
 * Ver Submódulo 5 em docs/PLANO_MUDANCA_VISUAL.md.
 *
 * Não depende de nenhum dado novo: usa apenas `position`, `side` e `status`,
 * já presentes em `PlayerCardData` (mesmo contrato do Submódulo 2). O
 * agrupamento em linhas e a ordem esquerda→direita dentro de cada linha são
 * puramente heurísticos e client-side — não existe "posição tática" ou
 * "escalação" persistida no motor, então nada aqui inventa um dado que o
 * motor não fornece.
 */

type FormationRowKey = "ataque" | "meio" | "defesa" | "goleiro";

const ROW_LABELS: Record<FormationRowKey, string> = {
  ataque: "ATAQUE",
  meio: "MEIO-CAMPO",
  defesa: "DEFESA",
  goleiro: "GOLEIRO",
};

// Ordem de exibição de cima (mais adiantado) para baixo (mais recuado),
// espelhando a leitura visual de um campo de futebol.
const ROW_ORDER: FormationRowKey[] = ["ataque", "meio", "defesa", "goleiro"];

// Posições canônicas do motor (engine/players/domain.py): Goleiro, Lateral,
// Zagueiro, Meia, Atacante. Lateral e Zagueiro compõem a mesma linha de
// defesa — a distinção entre eles já aparece no rótulo de posição do token.
function rowForPosition(position: string): FormationRowKey {
  switch (position) {
    case "Goleiro":
      return "goleiro";
    case "Lateral":
    case "Zagueiro":
      return "defesa";
    case "Atacante":
      return "ataque";
    case "Meia":
    default:
      return "meio";
  }
}

// `side` não tem um enum documentado no contrato — heurística tolerante por
// prefixo (Esquerdo/Esquerda → esquerda, Direito/Direita → direita), com
// qualquer outro valor (ou ausência) mantido ao centro da linha.
function sideRank(side: string | null): number {
  if (!side) return 1;
  const normalized = side.trim().toLowerCase();
  if (normalized.startsWith("esq")) return 0;
  if (normalized.startsWith("dir")) return 2;
  return 1;
}

export function FormationPitch({ players }: { players: PlayerCardData[] }) {
  const prefersReducedMotion = useReducedMotion();

  const rows = React.useMemo(() => {
    const buckets: Record<FormationRowKey, PlayerCardData[]> = { ataque: [], meio: [], defesa: [], goleiro: [] };
    players.forEach((player) => {
      buckets[rowForPosition(player.position)].push(player);
    });
    (Object.keys(buckets) as FormationRowKey[]).forEach((key) => {
      buckets[key] = [...buckets[key]].sort((a, b) => sideRank(a.side) - sideRank(b.side));
    });
    return buckets;
  }, [players]);

  if (!players.length) return null;

  let tokenIndex = 0;

  return (
    <div className="formation-pitch">
      <div className="formation-pitch-lines" aria-hidden="true" />
      {ROW_ORDER.map((rowKey) => {
        const rowPlayers = rows[rowKey];
        if (!rowPlayers.length) return null;
        return (
          <div className="formation-row" key={rowKey}>
            <span className="formation-row-label">{ROW_LABELS[rowKey]}</span>
            <div className="formation-row-players">
              {rowPlayers.map((player) => {
                const delayIndex = tokenIndex;
                tokenIndex += 1;
                return (
                  <motion.div
                    className="formation-token"
                    key={player.playerId}
                    initial={{ opacity: 0, scale: 0.85 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{
                      duration: prefersReducedMotion ? 0 : 0.25,
                      delay: prefersReducedMotion ? 0 : Math.min(delayIndex, 12) * 0.03,
                      ease: "easeOut",
                    }}
                  >
                    <span className="formation-token-cr">{player.cr1}</span>
                    <b className="formation-token-name">{player.name}</b>
                    <small className="formation-token-position">{player.position}</small>
                  </motion.div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
