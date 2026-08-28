import React, { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { AlertTriangle, ChevronRight, CirclePause, Flag, Goal, Pause, Play, RotateCcw, ShieldAlert, Shuffle, Sparkles, Swords, Target, Timer, Zap } from "lucide-react";
import { trpc } from "@/lib/trpc";
import { useFeedback } from "@/contexts/FeedbackContext";
import type { MatchControlDecisions } from "../../../server/careerGateway";

type Match = {
  matchId: number | null;
  round: number | null;
  scheduledAt: string;
  homeClub: { clubId: number; name: string };
  awayClub: { clubId: number; name: string };
};

type Player = { playerId: number; name: string; position: string; status: string; category: string };
type Tactics = NonNullable<MatchControlDecisions["tactics"]>;
type MatchEvent = { minute: number; title: string; detail: string; tone: "neutral" | "green" | "yellow" | "red" };

const defaultTactics: Tactics = { mentality: "NEUTRAL", attackLane: "MIXED", passing: "SHORT", pressure: "MEDIUM", crossing: false };

const timeline = [
  { minute: 0, title: "Apito inicial", detail: "As equipes se posicionam para a primeira disputa.", tone: "neutral" as const },
  { minute: 14, title: "Primeira chegada", detail: "O jogo ganha velocidade e as linhas começam a se abrir.", tone: "green" as const },
  { minute: 31, title: "Pressão no corredor", detail: "A torcida empurra o clube em uma sequência de ataques.", tone: "green" as const },
  { minute: 45, title: "Intervalo tático", detail: "Pausa para ajustar formação, pressão e substituições.", tone: "yellow" as const, pause: true, kind: "substitution" as const },
  { minute: 57, title: "Pênalti marcado", detail: "O árbitro aponta a marca da cal após a revisão do lance.", tone: "yellow" as const, pause: true, kind: "penalty" as const },
  { minute: 70, title: "Expulsão", detail: "Uma entrada dura deixa o adversário com um jogador a menos.", tone: "red" as const, pause: true, kind: "red" as const },
  { minute: 82, title: "Reta final", detail: "As duas equipes aceleram em busca do resultado.", tone: "green" as const },
  { minute: 90, title: "Apito final", detail: "O resultado oficial será registrado na carreira.", tone: "neutral" as const, final: true },
];

function eventIcon(tone: MatchEvent["tone"]) {
  if (tone === "red") return ShieldAlert;
  if (tone === "yellow") return AlertTriangle;
  if (tone === "green") return Zap;
  return Timer;
}

export function InteractiveMatchCenter({ match, players, onAfterPlay }: { match: Match; players: Player[]; onAfterPlay?: () => void }) {
  const utils = trpc.useUtils();
  const { notify } = useFeedback();
  const [isLive, setIsLive] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [step, setStep] = useState(-1);
  const [events, setEvents] = useState<MatchEvent[]>([]);
  const [tactics, setTactics] = useState<Tactics>(defaultTactics);
  const [substitutions, setSubstitutions] = useState<Array<{ playerOutId: number; playerInId: number }>>([]);
  const [penaltyTakerId, setPenaltyTakerId] = useState<number | undefined>();
  const [redCardResponse, setRedCardResponse] = useState({ formation: "4-4-2", mentality: "NEUTRAL" });
  const [tacticalPanel, setTacticalPanel] = useState<"strategy" | "attack" | "pressure">("strategy");
  const [activePause, setActivePause] = useState<"substitution" | "penalty" | "red" | null>(null);
  const playMatch = trpc.matches.playControlled.useMutation({
    onSuccess: async (result) => {
      setEvents((current) => [...current, { minute: 90, title: "Resultado oficial", detail: `${result.home_goals} × ${result.away_goals} registrado na carreira.`, tone: "neutral" }]);
      await Promise.all([utils.matches.dashboard.invalidate(), utils.career.current.invalidate(), utils.events.list.invalidate()]);
      toast.success(`Resultado oficial: ${result.home_goals} × ${result.away_goals}.`);
      notify("success");
      onAfterPlay?.();
    },
    onError: () => {
      setIsLive(false);
      setIsPaused(false);
      toast.error("A partida não pôde ser registrada. Nenhum resultado foi alterado.");
      notify("error");
    },
  });

  const starters = useMemo(() => players.filter((player) => player.status.toLowerCase().includes("titular")), [players]);
  const bench = useMemo(() => players.filter((player) => !player.status.toLowerCase().includes("titular")), [players]);

  useEffect(() => {
    if (!isLive || isPaused || playMatch.isPending || step >= timeline.length - 1) return;
    const timer = window.setTimeout(() => setStep((current) => current + 1), 850);
    return () => window.clearTimeout(timer);
  }, [isLive, isPaused, playMatch.isPending, step]);

  useEffect(() => {
    if (!isLive || step < 0) return;
    const current = timeline[step];
    setEvents((previous) => previous.some((event) => event.minute === current.minute && event.title === current.title) ? previous : [...previous, current]);
    if (current.pause) {
      setActivePause(current.kind ?? null);
      setIsPaused(true);
    }
    if (current.final && match.matchId && !playMatch.isPending) {
      setIsLive(false);
      playMatch.mutate({
        matchId: match.matchId,
        decisions: { tactics, substitutions, penalty_taker_id: penaltyTakerId, red_card_response: redCardResponse },
      });
    }
  }, [isLive, step]);

  const start = () => {
    if (!match.matchId) return;
    setEvents([]);
    setStep(0);
    setIsPaused(false);
    setActivePause(null);
    setIsLive(true);
  };
  const continueMatch = () => {
    setActivePause(null);
    setIsPaused(false);
    setStep((current) => current + 1);
  };
  const setTactic = <K extends keyof Tactics>(key: K, value: Tactics[K]) => setTactics((current) => ({ ...current, [key]: value }));
  const addSubstitution = () => {
    if (!starters[0] || !bench[0]) return;
    setSubstitutions((current) => current.length >= 3 ? current : [...current, { playerOutId: starters[Math.min(current.length, starters.length - 1)].playerId, playerInId: bench[Math.min(current.length, bench.length - 1)].playerId }]);
  };

  return <section className={`interactive-match-center ${isLive ? "is-live" : ""} ${isPaused ? "is-paused" : ""}`} aria-labelledby="interactive-match-title">
    <div className="interactive-match-topline"><div><span className="eyebrow"><Sparkles size={13} /> TRANSMISSÃO INTERATIVA</span><h2 id="interactive-match-title">{match.homeClub.name} <strong>×</strong> {match.awayClub.name}</h2><p>Você decide os momentos-chave. O placar oficial é calculado e persistido pela engine.</p></div><div className="interactive-score"><span>{isLive ? `${timeline[Math.max(step, 0)].minute}'` : "PRÉ-JOGO"}</span><b>{isLive ? "—  —" : "0  —  0"}</b></div></div>
    <div className="interactive-stage"><div className="pitch-orbit" aria-hidden="true"><span className="pitch-ball"><Goal size={18} /></span><i /><i /><i /><i /></div><div className="match-status-card">{isLive ? <><span className="live-badge"><i /> AO VIVO</span><h3>{timeline[Math.max(step, 0)].title}</h3><p>{timeline[Math.max(step, 0)].detail}</p></> : <><span className="live-badge pre"><Timer size={13} /> PRÉ-JOGO</span><h3>Entre no ritmo da partida</h3><p>Prepare as instruções e acompanhe cada momento antes de confirmar o resultado.</p></>}</div></div>
    <div className="interactive-actions">{!isLive && !playMatch.isPending && (match.matchId ? <button className="primary-action" type="button" onPointerDown={start} data-testid="start-match-button"><Play size={16} /> Iniciar partida</button> : <span className="match-not-ready"><Timer size={15} /> Aguardando confirmação do calendário</span>)}{isLive && !isPaused && <button className="outline-action" type="button" onClick={() => setIsPaused(true)}><Pause size={16} /> Pausar jogo</button>}{isPaused && <button className="primary-action" type="button" onClick={continueMatch}><Play size={16} /> Retomar jogo</button>}{playMatch.isPending && <span className="match-saving"><RotateCcw size={15} className="spin" /> Registrando resultado oficial…</span>}</div>
    <div className="interactive-grid"><article className="live-feed"><div className="section-heading compact"><div><span className="eyebrow">LANCES DA PARTIDA</span><h3>O jogo acontece aqui</h3></div><Flag size={17} /></div><div className="live-feed-list">{events.length ? events.map((event) => { const Icon = eventIcon(event.tone); return <div className={`live-event tone-${event.tone}`} key={`${event.minute}-${event.title}`}><span className="event-minute">{event.minute}'</span><span className="event-icon"><Icon size={15} /></span><div><b>{event.title}</b><p>{event.detail}</p></div></div>; }) : <div className="live-feed-empty"><Swords size={20} /><p>Os lances aparecerão conforme a partida avançar.</p></div>}</div></article><aside className="tactical-console"><div className="section-heading compact"><div><span className="eyebrow">CONSOLE TÁTICO</span><h3>Comandos do manager</h3></div><Target size={17} /></div><div className="tactical-window-tabs" role="tablist" aria-label="Grupos de comandos táticos"><button type="button" className={tacticalPanel === "strategy" ? "selected" : ""} onClick={() => setTacticalPanel("strategy")} role="tab" aria-selected={tacticalPanel === "strategy"}>Estratégia</button><button type="button" className={tacticalPanel === "attack" ? "selected" : ""} onClick={() => setTacticalPanel("attack")} role="tab" aria-selected={tacticalPanel === "attack"}>Ataque</button><button type="button" className={tacticalPanel === "pressure" ? "selected" : ""} onClick={() => setTacticalPanel("pressure")} role="tab" aria-selected={tacticalPanel === "pressure"}>Pressão</button></div>{tacticalPanel === "strategy" && <div className="tactical-window" role="tabpanel"><label>MENTALIDADE<select value={tactics.mentality} onChange={(event) => setTactic("mentality", event.target.value)} disabled={isLive && !isPaused}><option value="DEFENSIVE">Defensivo</option><option value="NEUTRAL">Neutro</option><option value="OFFENSIVE">Ofensivo</option></select></label><label>FORMAÇÃO<select value={redCardResponse.formation} onChange={(event) => setRedCardResponse((current) => ({ ...current, formation: event.target.value }))} disabled={isLive && !isPaused}><option>4-4-2</option><option>4-3-3</option><option>3-5-2</option><option>5-3-2</option></select></label></div>}{tacticalPanel === "attack" && <div className="tactical-window" role="tabpanel"><label>ATAQUE<select value={tactics.attackLane} onChange={(event) => setTactic("attackLane", event.target.value)} disabled={isLive && !isPaused}><option value="MIXED">Misto</option><option value="WINGS">Pelas laterais</option><option value="CENTER">Pelo meio</option></select></label><label>PASSES<select value={tactics.passing} onChange={(event) => setTactic("passing", event.target.value)} disabled={isLive && !isPaused}><option value="SHORT">Curtos</option><option value="LONG">Longos</option><option value="SIDEWAYS">De lado</option></select></label><label className="tactic-check"><input type="checkbox" checked={tactics.crossing} onChange={(event) => setTactic("crossing", event.target.checked)} disabled={isLive && !isPaused} /> Cruzar mais bolas</label></div>}{tacticalPanel === "pressure" && <div className="tactical-window" role="tabpanel"><label>PRESSÃO<select value={tactics.pressure} onChange={(event) => setTactic("pressure", event.target.value)} disabled={isLive && !isPaused}><option value="LOW">Bloco baixo</option><option value="MEDIUM">Equilibrada</option><option value="HIGH">Alta</option><option value="LINE">Marcação em linha</option></select></label><p className="tactical-window-note">As escolhas ficam disponíveis nas pausas de decisão.</p></div>}</aside></div>
    {isPaused && <div className="decision-popover" role="dialog" aria-live="assertive"><div className="decision-popover-head"><span className="live-badge pause"><CirclePause size={13} /> PAUSA DE DECISÃO</span><b>{activePause === "penalty" ? "Escolha o cobrador do pênalti" : activePause === "red" ? "Reorganize o time após a expulsão" : "Ajuste sua equipe no intervalo"}</b></div>{activePause === "penalty" && <label>COBRADOR<select value={penaltyTakerId ?? ""} onChange={(event) => setPenaltyTakerId(Number(event.target.value) || undefined)}><option value="">Escolha um atleta</option>{starters.map((player) => <option key={player.playerId} value={player.playerId}>{player.name} · {player.position}</option>)}</select></label>}{activePause === "substitution" && <div className="decision-substitution"><button type="button" className="outline-action" onClick={addSubstitution}><Shuffle size={15} /> Adicionar substituição</button>{substitutions.map((substitution, index) => <div className="substitution-row" key={`${substitution.playerOutId}-${index}`}><span>{starters.find((player) => player.playerId === substitution.playerOutId)?.name ?? "Titular"}</span><ChevronRight size={14} /><span>{bench.find((player) => player.playerId === substitution.playerInId)?.name ?? "Reserva"}</span></div>)}</div>}{activePause === "red" && <p className="decision-note"><ShieldAlert size={16} /> A formação escolhida no console será aplicada à reorganização defensiva.</p>}<button className="primary-action" type="button" onClick={continueMatch}><Play size={15} /> Continuar partida</button></div>}
  </section>;
}
