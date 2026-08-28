import React from "react";
import { motion, useReducedMotion } from "framer-motion";

/**
 * MatchTimeline — substitui a lista plana de compromissos do calendário
 * (`.calendar-list`, uma linha por partida sem hierarquia entre rodadas)
 * por uma linha do tempo agrupada por rodada: um trilho vertical com um
 * marcador por rodada e as partidas daquela rodada encadeadas abaixo.
 *
 * Ver Submódulo 7 em docs/PLANO_MUDANCA_VISUAL.md.
 *
 * Não depende de nenhum dado novo: agrupa `upcomingFixtures` (mesmo array
 * já consumido pela lista anterior) por `round`, sem nenhuma query
 * adicional. `formatDate`/`formatTime` espelham exatamente as funções já
 * usadas em `pages/Home.tsx` (`formatMatchDate`/`formatMatchTime`) —
 * duplicadas aqui, e não importadas de lá, para manter o componente
 * autossuficiente e sem import circular com a página que o usa, mesmo
 * padrão de auto-suficiência já adotado por `PlayerCard` e `FormationPitch`.
 */
export interface TimelineFixture {
  key: string;
  scheduledAt: string;
  round: number | null;
  homeClub: { clubId: number; name: string };
  awayClub: { clubId: number; name: string };
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short" }).format(date).replace(".", "").toUpperCase();
}

function formatTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime()) || !value.includes("T")) return "horário não informado";
  return new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" }).format(date);
}

export function MatchTimeline({ fixtures, competitionName }: { fixtures: TimelineFixture[]; competitionName: string }) {
  const prefersReducedMotion = useReducedMotion();

  const groups = React.useMemo(() => {
    const order: Array<number | null> = [];
    const byRound = new Map<number | null, TimelineFixture[]>();
    fixtures.forEach((fixture) => {
      const roundKey = fixture.round;
      if (!byRound.has(roundKey)) {
        byRound.set(roundKey, []);
        order.push(roundKey);
      }
      byRound.get(roundKey)!.push(fixture);
    });
    return order.map((round) => ({ round, matches: byRound.get(round)! }));
  }, [fixtures]);

  if (!fixtures.length) return null;

  let entryIndex = 0;

  return (
    <div className="match-timeline">
      {groups.map((group) => (
        <div className="match-timeline-round" key={group.round ?? "sem-rodada"}>
          <div className="match-timeline-round-marker">
            <span className="match-timeline-dot" aria-hidden="true" />
            <b>{group.round !== null ? `RODADA ${group.round}` : "RODADA A DEFINIR"}</b>
          </div>
          <div className="match-timeline-entries">
            {group.matches.map((match) => {
              const delayIndex = entryIndex;
              entryIndex += 1;
              return (
                <motion.div
                  className="match-timeline-entry"
                  key={match.key}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{
                    duration: prefersReducedMotion ? 0 : 0.22,
                    delay: prefersReducedMotion ? 0 : Math.min(delayIndex, 10) * 0.03,
                    ease: "easeOut",
                  }}
                >
                  <span className="match-timeline-date">{formatDate(match.scheduledAt)}</span>
                  <div className="match-timeline-copy">
                    <b>
                      {match.homeClub.name} × {match.awayClub.name}
                    </b>
                    <small>
                      {competitionName} · {formatTime(match.scheduledAt)}
                    </small>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
