/*
 * FutManager — Editorial de Arquibancada.
 * Dashboard visual offline-first: apresenta o contrato visual do motor sem inventar
 * jogadores, caixa, resultados ou regras; dados ausentes são mostrados como estados honestos.
 */
import React, { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { trpc } from "@/lib/trpc";
import { getEntityAssetPresentation } from "@/lib/entityAsset";
import { EntityAsset } from "@/components/EntityAsset";
import { TableSkeleton } from "@/components/TableSkeleton";
import { StaffEconomyPanel } from "@/components/StaffEconomyPanel";
import { PlayerCard } from "@/components/PlayerCard";
import { FormationPitch } from "@/components/FormationPitch";
import { ClubHUD } from "@/components/ClubHUD";
import { MatchTimeline } from "@/components/MatchTimeline";
import { PlayerProductionChart, type PlayerProductionDatum } from "@/components/PlayerProductionChart";
import { SponsorshipPanel } from "@/components/SponsorshipPanel";
import { StadiumOperationsPanel } from "@/components/StadiumOperationsPanel";
import { TravelCostsPanel } from "@/components/TravelCostsPanel";
import { InteractiveMatchCenter } from "@/components/InteractiveMatchCenter";
import { OperationsPanel } from "@/components/OperationsPanel";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useFeedback } from "@/contexts/FeedbackContext";
import CareerStart from "@/pages/CareerStart";
import {
  Activity,
  ArrowLeft,
  ArrowUpRight,
  Bell,
  Building2,
  CalendarDays,
  ChevronRight,
  CircleDollarSign,
  ClipboardList,
  Dumbbell,
  Factory,
  Flag,
  Gauge,
  Goal,
  LayoutDashboard,
  Menu,
  Newspaper,
  Search,
  Shield,
  SlidersHorizontal,
  Sparkles,
  Trophy,
  Landmark,
  Users,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import type { AppSection } from "../App";

const ASSETS = {
  mark: "/manus-storage/futmanager-mark_e2de4349.png",
  stadium: "/manus-storage/futmanager-stadium-editorial_daa6aae8.jpg",
  texture: "/manus-storage/futmanager-program-texture_81ce0f48.jpg",
  training: "/manus-storage/futmanager-training_e0636498.jpg",
};

const navItems: { id: AppSection; label: string; short: string; icon: typeof LayoutDashboard }[] = [
  { id: "clube", label: "Seu Clube", short: "01", icon: LayoutDashboard },
  { id: "partidas", label: "Nossas Partidas", short: "02", icon: Goal },
  { id: "estadio", label: "Estádio", short: "03", icon: Landmark },
  { id: "time", label: "Time", short: "04", icon: Shield },
  { id: "ct", label: "CT", short: "05", icon: Dumbbell },
  { id: "mercado", label: "Mercado", short: "06", icon: ArrowUpRight },
  { id: "patrocinadores", label: "Patrocinadores", short: "07", icon: Trophy },
  { id: "transferencias", label: "Transferências", short: "08", icon: ClipboardList },
  { id: "financas", label: "Finanças", short: "09", icon: CircleDollarSign },
  { id: "operacoes", label: "Operações", short: "10", icon: SlidersHorizontal },
];

function formatSection(section: AppSection) {
  return navItems.find((item) => item.id === section)?.label ?? "Início";
}

function formatCash(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(value);
}

function Metric({ label, value, note, accent = "ink", icon: Icon }: { label: string; value: string; note: string; accent?: string; icon: typeof Activity }) {
  return (
    <article className={`metric-card metric-${accent}`}><span className="metric-index">{label.slice(0, 2)}</span>
      <div className="metric-topline"><span>{label}</span><Icon size={16} strokeWidth={1.8} /></div>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  );
}

function Sidebar({ section, onSectionChange, open, onClose }: { section: AppSection; onSectionChange: (section: AppSection) => void; open: boolean; onClose: () => void }) {
  return (
    <aside className={`sidebar ${open ? "is-open" : ""}`}>
      <div className="sidebar-brand">
        <img src={ASSETS.mark} alt="" />
        <div><span>FUT</span><strong>MANAGER</strong></div>
        <button className="mobile-close" onClick={onClose} aria-label="Fechar menu"><X size={18} /></button>
      </div>
      <div className="sidebar-caption">CENTRO DE COMANDO <span>2026</span></div>
      <nav aria-label="Navegação principal">
        {navItems.map(({ id, label, short, icon: Icon }) => (
          <button key={id} className={`nav-item ${section === id ? "active" : ""}`} onClick={() => { onSectionChange(id); onClose(); }}>
            <span className="nav-index">{short}</span><Icon size={17} strokeWidth={1.8} /><span>{label}</span>{section === id && <ChevronRight className="nav-arrow" size={15} />}
          </button>
        ))}
      </nav>
      <div className="sidebar-spacer" />
      <div className="sidebar-source">
        <span className="live-dot" />
        <div><b>FONTE OFICIAL</b><small>ESTADO DO CLUBE</small></div>
      </div>
      <div className="sidebar-footer"><span>FUTMANAGER / LOCAL</span><span>V. 0.1</span></div>
    </aside>
  );
}

function Header({ section, onMenu }: { section: AppSection; onMenu: () => void }) {
  const [alertsOpen, setAlertsOpen] = useState(false);
  const eventInput = useMemo(() => ({ limit: 8, unreadOnly: false }), []);
  const eventsQuery = trpc.events.list.useQuery(eventInput, { retry: 1 });
  const utils = trpc.useUtils();
  const { enabled: feedbackEnabled, toggleFeedback } = useFeedback();
  const markRead = trpc.events.markRead.useMutation({
    onSuccess: () => { utils.events.list.invalidate(); },
    onError: () => toast("Não foi possível atualizar a leitura do alerta."),
  });
  const alerts = eventsQuery.data?.items ?? [];
  const unread = eventsQuery.data?.unread_count ?? 0;
  return (
    <header className="topbar">
      <button className="mobile-menu" onClick={onMenu} aria-label="Abrir menu"><Menu size={22} /></button>
      <div className="crumb"><span>FUTMANAGER</span><ChevronRight size={14} /><b>{formatSection(section).toUpperCase()}</b></div>
      <div className="top-actions"><span className="data-status"><span className="status-pip" /> CARREIRA ATIVA</span><button className="icon-btn" onClick={toggleFeedback} aria-label={feedbackEnabled ? "Desativar som e vibração" : "Ativar som e vibração"} aria-pressed={feedbackEnabled} title={feedbackEnabled ? "Som e vibração ativados" : "Som e vibração desativados"}>{feedbackEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}</button><div className="alerts-control"><button className="icon-btn" onClick={() => setAlertsOpen((open) => !open)} aria-label="Alertas" aria-expanded={alertsOpen}><Bell size={18} />{unread > 0 && <i>{unread > 9 ? "9+" : unread}</i>}</button>{alertsOpen && <section className="alerts-popover" aria-label="Alertas persistidos"><div className="alerts-popover-head"><div><span className="eyebrow">EVENTOS DO CLUBE</span><h2>Alertas</h2></div><button onClick={() => setAlertsOpen(false)} aria-label="Fechar alertas"><X size={16} /></button></div>{eventsQuery.isLoading ? <p className="alerts-state">Consultando os eventos persistidos…</p> : eventsQuery.error ? <p className="alerts-state">Os alertas não puderam ser consultados.</p> : alerts.length ? <div className="alerts-list">{alerts.map((event) => <button key={event.event_id} className={`alert-row ${event.is_read ? "is-read" : "is-open"}`} onClick={() => { if (!event.is_read) markRead.mutate({ eventId: event.event_id }); }}><span className={`alert-severity severity-${event.severity.toLowerCase()}`} /><span><b>{event.title}</b><small>{event.description ?? event.type} · {event.event_date}</small></span></button>)}</div> : <p className="alerts-state">Nenhum alerta foi persistido para este clube.</p>}</section>}</div><button className="avatar" onClick={() => toast("Perfil do manager será conectado na próxima etapa.")} aria-label="Perfil">FM</button></div>
    </header>
  );
}

function Dashboard({ onSectionChange }: { onSectionChange: (section: AppSection) => void }) {
  const matchesQuery = trpc.matches.dashboard.useQuery(undefined, { retry: 1 });
  const workspaceQuery = trpc.club.workspace.useQuery(undefined, { retry: 1 });
  const playerStatsInput = useMemo(() => { const competitionId = matchesQuery.data?.selectedCompetitionId; return competitionId ? { competitionId } : undefined; }, [matchesQuery.data?.selectedCompetitionId]);
  const playerStatsQuery = trpc.matches.playerStats.useQuery(playerStatsInput, { retry: 1 });
  const eventInput = useMemo(() => ({ limit: 8, unreadOnly: false }), []);
  const eventsQuery = trpc.events.list.useQuery(eventInput, { retry: 1 });
  const utils = trpc.useUtils();
  const markRead = trpc.events.markRead.useMutation({ onSuccess: () => { utils.events.list.invalidate(); } });
  const workspace = workspaceQuery.data;
  const controlledClub = workspace?.club ?? matchesQuery.data?.controlledClub ?? null;
  const nextMatch = controlledClub ? matchesQuery.data?.upcomingFixtures.find((match) => match.homeClub.clubId === controlledClub.clubId || match.awayClub.clubId === controlledClub.clubId) ?? null : null;
  const clubName = controlledClub?.name ?? "Seu clube";
  const hasCash = workspace?.finance.cash !== null && workspace?.finance.cash !== undefined;
  const eventPresentation = (event: { type: string; severity: string }) => ({
    tone: event.severity === "CRITICAL" ? "coral" : event.severity === "HIGH" ? "blue" : event.type === "ESTADIO" ? "green" : "ink",
    icon: event.type === "COMPETICAO" ? Trophy : event.type === "TORCIDA" ? Users : event.type === "ESTADIO" ? Landmark : event.type === "PATROCINIO" ? CircleDollarSign : CircleDollarSign,
  });
  const persistedEvents = eventsQuery.data?.items ?? [];
  const productionData = useMemo<PlayerProductionDatum[]>(() => {
    const playerById = new Map((workspace?.squad.players ?? []).map((player) => [player.playerId, player.name]));
    return [...(playerStatsQuery.data?.players ?? [])]
      .sort((a, b) => b.goals + b.assists - (a.goals + a.assists))
      .slice(0, 5)
      .map((player) => ({
        playerId: player.playerId,
        name: playerById.get(player.playerId) ?? `Atleta #${player.playerId}`,
        goals: player.goals,
        assists: player.assists,
        averageRating: player.averageRating,
      }));
  }, [playerStatsQuery.data?.players, workspace?.squad.players]);
  return <><section className="hero-panel"><div className="hero-image"><img src={ASSETS.stadium} alt="Estádio vazio em perspectiva editorial" /><div className="hero-scrim" /><div className="hero-pitch-lines" aria-hidden="true"><span /><span /><span /></div></div><div className="hero-copy"><span className="eyebrow light">{workspace?.career ? `${workspace.career.careerName.toUpperCase()} / CENTRO DE COMANDO` : "SEU CLUBE / CENTRO DE COMANDO"}</span><h1>{clubName}.<br /><em>Sob seu comando.</em></h1><p>Elenco, caixa, estádio e calendário em uma só leitura, acompanhados em uma só leitura da temporada.</p><button className="primary-action" onClick={() => onSectionChange("partidas")}>Ver nossas partidas <ArrowUpRight size={16} /></button></div><div className="hero-stamp"><img src={ASSETS.mark} alt="" /><div><span>FUT</span><strong>MANAGER</strong><small>GESTÃO · CAMPO · FUTURO</small></div></div><div className="hero-meta"><span>ESTÁDIO / VISÃO GERAL</span><span>{workspace?.stadium.name ?? "SEM REGISTRO"}</span></div></section>{workspace && <section className="hud-section"><ClubHUD workspace={workspace} onNavigateToMarket={() => onSectionChange("mercado")} onUpdateInfo={() => { utils.club.workspace.invalidate(); }} /></section>}<div className="metrics-grid"><Metric label="CAIXA" value={workspaceQuery.isLoading ? "…" : formatCash(workspace?.finance.cash)} note={workspace?.finance.cash !== null && workspace?.finance.cash !== undefined ? "Saldo disponível na carreira" : "Saldo ainda não disponível"} accent="green" icon={CircleDollarSign} /><Metric label="REPUTAÇÃO" value={workspaceQuery.isLoading ? "…" : workspace?.reputation.sporting?.toString() ?? "—"} note={workspace?.reputation.sporting !== null && workspace?.reputation.sporting !== undefined ? "Indicador esportivo" : "Indicador ainda não disponível"} accent="blue" icon={Sparkles} /><Metric label="COMPETIÇÃO" value={matchesQuery.isLoading ? "…" : matchesQuery.data?.selectedCompetition?.name ?? "—"} note={matchesQuery.data?.selectedCompetition ? `${matchesQuery.data.selectedCompetition.playedMatches} partidas registradas` : "Nenhuma competição disponível"} accent="coral" icon={Flag} /><Metric label="ELENCO" value={workspaceQuery.isLoading ? "…" : workspace?.squad.total?.toString() ?? "—"} note={workspace?.squad.total ? `${workspace.squad.starters} titulares · ${workspace.squad.reserves} reservas` : "Elenco ainda não disponível"} accent="ink" icon={Users} /></div><section className="standings-panel team-stats-panel"><div className="section-heading compact"><div><span className="eyebrow">PRODUÇÃO INDIVIDUAL</span><h2>Atletas em destaque</h2></div></div>{playerStatsQuery?.isLoading ? <div className="fixture-empty">Atualizando estatísticas individuais…</div> : playerStatsQuery?.error ? <div className="fixture-empty">As estatísticas individuais não puderam ser consultadas.</div> : productionData.length ? <PlayerProductionChart data={productionData} /> : <div className="fixture-empty">Nenhuma estatística individual está disponível para a competição.</div>}</section><section className="content-grid"><div className="main-column"><div className="section-heading"><div><span className="eyebrow">AGENDA DO CLUBE</span><h2>Próxima partida</h2></div><button className="text-action" onClick={() => onSectionChange("time")}>Ver time <ArrowUpRight size={15} /></button></div><article className="fixture-card"><div className="fixture-date"><span>PRÓXIMO COMPROMISSO</span><strong>{nextMatch ? formatMatchDate(nextMatch.scheduledAt) : "—"}</strong><small>{nextMatch ? formatMatchTime(nextMatch.scheduledAt) : "Data a confirmar"}</small></div><div className="fixture-match">{nextMatch ? <><div><EntityAsset className="crest-placeholder" entityType="team" entityId={nextMatch.homeClub.clubId} entityName={nextMatch.homeClub.name} /><b>{nextMatch.homeClub.name}</b><small>MANDANTE</small></div><div className="versus">VS</div><div><EntityAsset className="crest-placeholder away" entityType="team" entityId={nextMatch.awayClub.clubId} entityName={nextMatch.awayClub.name} /><b>{nextMatch.awayClub.name}</b><small>VISITANTE</small></div></> : <div className="fixture-empty">Nenhuma partida futura foi persistida para este clube.</div>}</div><div className="fixture-note"><CalendarDays size={15} /><span>{nextMatch ? "Compromisso confirmado na agenda da temporada." : "O próximo compromisso aparece quando a agenda da temporada for confirmada."}</span></div></article><div className="section-heading news-heading"><div><span className="eyebrow">SINAL DO MUNDO</span><h2>Feed de alertas</h2></div><span className="filter-btn"><Bell size={15} /> {eventsQuery.data?.unread_count ?? 0} não lido(s)</span></div><div className="news-list">{eventsQuery.isLoading ? <div className="fixture-empty">Consultando alertas persistidos…</div> : eventsQuery.error ? <div className="fixture-empty">Os alertas do clube não puderam ser consultados.</div> : persistedEvents.length ? persistedEvents.map((event) => { const presentation = eventPresentation(event); return <EventCard key={event.event_id} type={event.type} tone={presentation.tone} label={event.type} title={event.title} detail={event.description ?? "Evento registrado pelo motor."} time={event.event_date} icon={presentation.icon} read={event.is_read} onClick={() => { if (!event.is_read) markRead.mutate({ eventId: event.event_id }); }} />; }) : <div className="fixture-empty">Nenhum alerta foi persistido para este clube.</div>}</div></div><aside className="side-column"><div className="section-heading compact"><div><span className="eyebrow">SITUAÇÃO ATUAL</span><h2>Seu clube</h2></div><button className="more-btn" aria-label="Mais opções" onClick={() => toast("O retrato do clube vem do estado oficial.")}>···</button></div><article className="club-card"><div className="club-card-top">{controlledClub ? <EntityAsset entityType="team" entityId={controlledClub.clubId} entityName={controlledClub.name} /> : <span className="crest-large">?</span>}<div><span className="eyebrow">CLUBE CONTROLADO</span><h3>{controlledClub?.name ?? "Não conectado"}</h3><p>{controlledClub ? "Você comanda este clube nesta carreira" : "Selecione um clube para começar"}</p></div></div><div className="club-lines"><div><span>ESTÁDIO</span><b>{workspace?.stadium.name ?? "—"}</b></div><div><span>CT</span><b>{workspace?.training.available ? "ATIVO" : "—"}</b></div><div><span>ELENCO</span><b>{workspace?.squad.total ?? "—"}</b></div></div><button className="secondary-action" onClick={() => onSectionChange("estadio")}>Ver estruturas <ChevronRight size={15} /></button></article><button type="button" className="read-card" style={{ backgroundImage: `url(${ASSETS.texture})` }} onClick={() => onSectionChange("partidas")} aria-label="Ler o cenário do Dia do Jogo"><span className="eyebrow">LEITURA DO DIA</span><h3>Leia o cenário<br />antes de mexer<br /><em>no elenco.</em></h3><div className="read-footer"><span>ABRIR DIA DO JOGO</span><ArrowUpRight size={16} /></div></button><div className="integrity-note"><span className="live-dot" /><div><b>CARREIRA EM DIA</b><p>Suas decisões e resultados ficam registrados automaticamente.</p></div></div></aside></section></>;
}

function EventCard({ type, tone, label, title, detail, time, icon: Icon, read, onClick }: { type: string; tone: string; label: string; title: string; detail: string; time: string; icon: typeof Activity; read: boolean; onClick: () => void }) {
  return <button className={`event-card event-${tone} ${read ? "is-read" : "is-open"}`} onClick={onClick}><div className="event-icon"><Icon size={17} /></div><div className="event-content"><div className="event-label"><span>{label}</span><time>{time}</time></div><h3>{title}</h3><p>{detail}</p></div>{!read && <ArrowUpRight className="event-open" size={16} />}</button>;
}

function formatMatchDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short" }).format(date).replace(".", "").toUpperCase();
}

function formatMatchTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime()) || !value.includes("T")) return "horário não informado";
  return new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" }).format(date);
}

type AutoAdvanceSummary = { weeks_advanced: number; target_season: number | null; target_round: number | null; notice: string | null; cycles: Array<{ season: number; week: number; matches: number; world_events: Array<{ event_id: number; type: string; severity: number; title: string; description: string | null }> }> };

function eventDestination(type: string, title: string): AppSection {
  const normalized = `${type} ${title}`.toUpperCase();
  if (normalized.includes("SCOUT") || normalized.includes("OLHEIRO") || normalized.includes("RELATÓRIO")) return "mercado";
  if (normalized.includes("ESTADIO") || normalized.includes("ESTÁDIO") || normalized.includes("REFORMA")) return "estadio";
  if (normalized.includes("CT") || normalized.includes("TREINO") || normalized.includes("CONSTRUÇÃO") || normalized.includes("CONSTRUCAO")) return "ct";
  if (normalized.includes("PATROC")) return "patrocinadores";
  if (normalized.includes("FINANCE") || normalized.includes("CAIXA") || normalized.includes("FOLHA")) return "financas";
  if (normalized.includes("LESÃO") || normalized.includes("LESAO") || normalized.includes("SAÚDE") || normalized.includes("SAUDE")) return "time";
  if (normalized.includes("COMPETIÇÃO") || normalized.includes("COMPETICAO") || normalized.includes("TORCIDA")) return "partidas";
  return "operacoes";
}

function eventDestinationLabel(section: AppSection) {
  const labels: Partial<Record<AppSection, string>> = { mercado: "Abrir relatório de olheiro", estadio: "Abrir estádio", ct: "Abrir CT", patrocinadores: "Abrir patrocínios", financas: "Abrir finanças", time: "Abrir elenco e saúde", partidas: "Abrir partidas", operacoes: "Abrir operações" };
  return labels[section] ?? "Abrir detalhes";
}

function eventGlyph(type: string) {
  if (type === "ESTADIO") return <Building2 size={16} />;
  if (type === "FINANCEIRO") return <CircleDollarSign size={16} />;
  if (type === "COMPETICAO") return <Trophy size={16} />;
  if (type === "PATROCINIO") return <Landmark size={16} />;
  if (type === "LESAO" || type === "NOTICIA_SAUDE") return <Activity size={16} />;
  if (type.includes("SCOUT") || type.includes("CONTRAT")) return <ClipboardList size={16} />;
  return <Bell size={16} />;
}

export function MatchesPage({ initialView = "competicoes", onOpenMatch, onNavigate }: { initialView?: "competicoes" | "tabela" | "calendario" | "resultados"; onOpenMatch?: () => void; onNavigate?: (section: AppSection) => void }) {
  const [view, setView] = useState<"competicoes" | "tabela" | "calendario" | "resultados">(initialView);
  const [competitionId, setCompetitionId] = useState<number | undefined>();
  const [weekSummary, setWeekSummary] = useState<AutoAdvanceSummary | null>(null);
  const { notify } = useFeedback();
  const goToMatch = trpc.career.advanceUntilMatch.useMutation({
    onSuccess: async (result) => {
      await Promise.all([utils.career.current.invalidate(), utils.matches.dashboard.invalidate(), utils.events.list.invalidate()]);
      setWeekSummary(result as AutoAdvanceSummary);
      notify("success");
    },
    onError: () => { toast.error("Não foi possível chegar à partida pelo calendário atual."); notify("error"); },
  });
  const queryInput = useMemo(() => (competitionId ? { competitionId } : undefined), [competitionId]);
  const dashboardQuery = trpc.matches.dashboard.useQuery(queryInput, { retry: 1 });
  const workspaceQuery = trpc.club.workspace.useQuery(undefined, { retry: 1 });
  const matchdayEventsInput = useMemo(() => ({ limit: 6, unreadOnly: false }), []);
  const matchdayEventsQuery = trpc.events.list.useQuery(matchdayEventsInput, { retry: 1 });
  const utils = trpc.useUtils();
  const advanceWeek = trpc.career.advanceWeek.useMutation({
    onSuccess: async (result) => {
      await Promise.all([utils.career.current.invalidate(), utils.matches.dashboard.invalidate(), utils.events.list.invalidate()]);
      toast.success(`Semana ${result.week} concluída. O próximo jogo do seu clube continua aguardando sua ação.`);
      notify("success");
    },
    onError: () => { toast.error("Não foi possível avançar a semana da carreira."); notify("error"); }
  });
  const dashboard = dashboardQuery.data;
  const matchdayEvents = matchdayEventsQuery.data?.items ?? [];
  const selectedCompetition = dashboard?.selectedCompetition ?? null;
  const controlledClub = dashboard?.controlledClub ?? null;
  const filteredFixtures = controlledClub
    ? dashboard?.upcomingFixtures.filter((match) => match.homeClub.clubId === controlledClub.clubId || match.awayClub.clubId === controlledClub.clubId) ?? []
    : dashboard?.upcomingFixtures ?? [];
  const filteredResults = controlledClub
    ? dashboard?.recentResults.filter((match) => match.homeClub.clubId === controlledClub.clubId || match.awayClub.clubId === controlledClub.clubId) ?? []
    : dashboard?.recentResults ?? [];
  const nextMatch = filteredFixtures[0] ?? null;
  const handleGoToMatch = () => {
    if (!nextMatch?.matchId) {
      toast.info("Esta partida ainda está sendo confirmada pelo calendário. Tente novamente em instantes.");
      return;
    }
    goToMatch.mutate({ matchId: nextMatch.matchId });
  };
  const totalMatches = (dashboard?.upcomingFixtures.length ?? 0) + (dashboard?.recentResults.length ?? 0);
  const tabs = [
    ["competicoes", "Competições"],
    ["tabela", "Tabela"],
    ["calendario", "Calendário"],
    ["resultados", "Resultados"],
  ] as const;
  const waitingMessage = dashboardQuery.isLoading
    ? "Atualizando a temporada…"
    : dashboardQuery.error
      ? "Não foi possível atualizar a temporada neste momento."
      : dashboard?.source.message ?? "Aguardando a atualização da temporada.";

  return <>
    <section className="page-intro match-intro"><div><span className="eyebrow">SEU CLUBE / CICLO ESPORTIVO</span><h1>Dia do jogo</h1><p>Prepare a rodada, acompanhe o calendário e assuma o controle do próximo compromisso.</p></div><div className="match-score-mark"><span>JOGOS NA TEMPORADA</span><strong>{dashboardQuery.isLoading ? "—" : totalMatches}</strong><small>{selectedCompetition?.seasonYear ? `temporada ${selectedCompetition.seasonYear}` : "calendário atual"}</small></div></section>
    <section className="matches-command"><div className="matches-heading"><div><span className="eyebrow">PAINEL DE COMPETIÇÃO</span><h2>{selectedCompetition ? selectedCompetition.name : "Leia o jogo antes da rodada."}</h2></div><span className="match-state"><span className="status-pip" /> {dashboard?.source.available ? "calendário atualizado" : dashboardQuery.isLoading ? "atualizando calendário" : "calendário indisponível"}</span></div><div className="match-tabs" role="tablist" aria-label="Visões de partidas">{tabs.map(([id, label]) => <button key={id} className={view === id ? "selected" : ""} onClick={() => setView(id)} role="tab" aria-selected={view === id}>{label}</button>)}</div></section>
    {view === "competicoes" && <section className="competition-layout"><article className="competition-main"><div className="section-heading compact"><div><span className="eyebrow">COMPETIÇÕES DA TEMPORADA</span><h2>{selectedCompetition ? `${dashboard?.competitions.length ?? 0} competição(ões) disponível(is)` : "Nenhuma competição disponível"}</h2></div><Flag size={18} /></div>{dashboard?.competitions.length ? <div className="competition-select-list">{dashboard.competitions.map((competition) => <button key={competition.competitionId} className={`competition-select ${competition.competitionId === dashboard.selectedCompetitionId ? "is-selected" : ""}`} onClick={() => setCompetitionId(competition.competitionId)}><span className="competition-badge">{competition.seasonYear ?? "—"}</span><span><b>{competition.name}</b><small>{competition.type} · {competition.format} · {competition.status}</small></span><em>{competition.playedMatches} realizados · {competition.scheduledFixtures} agendados</em></button>)}</div> : <div className="competition-empty"><span className="competition-badge">—</span><div><b>{dashboardQuery.isLoading ? "Atualizando a temporada" : "Nenhuma competição foi criada na carreira."}</b><p>{waitingMessage}</p></div></div>}</article><aside className="competition-side"><span className="eyebrow">PRÓXIMO JOGO</span>{nextMatch ? <><h3>{nextMatch.homeClub.name}<br />× {nextMatch.awayClub.name}</h3><p>{selectedCompetition?.name} · rodada {nextMatch.round ?? "—"}</p><div className="side-rule" /><span className="mini-label">AGENDA</span><b>{formatMatchDate(nextMatch.scheduledAt)}</b>{controlledClub && nextMatch.matchId && <TravelCostsPanel matchId={nextMatch.matchId} clubId={controlledClub.clubId} season={selectedCompetition?.seasonYear ?? undefined} />}</> : <><h3>Sem compromisso<br />confirmado.</h3><p>{controlledClub ? "Não há partida futura para o clube controlado nesta competição." : "A carreira ainda não possui clube controlado ou partida registrada."}</p><div className="side-rule" /><span className="mini-label">CONTEXTO</span><b>—</b></>}</aside></section>}
    <section className="matchday-command" aria-labelledby="matchday-title"><div className="matchday-simulation-head"><div><span className="eyebrow">CENTRAL DO DIA</span><h2 id="matchday-title">A próxima partida está pronta.</h2><p>{nextMatch ? `${nextMatch.homeClub.name} × ${nextMatch.awayClub.name} · rodada ${nextMatch.round ?? "—"}` : "Aguardando uma partida real no calendário."}</p></div><div className="matchday-actions"><button className="outline-action compact" type="button" onClick={() => advanceWeek.mutate({})} disabled={advanceWeek.isPending}>{advanceWeek.isPending ? "Avançando…" : "Avançar semana"}</button>{nextMatch && <button className="primary-action compact" type="button" onClick={handleGoToMatch} disabled={goToMatch.isPending}>{goToMatch.isPending ? "Indo para a partida…" : "Ir para partida"} <ArrowUpRight size={15} /></button>}</div></div>{nextMatch ? <div className="matchday-launch-body"><span className="launch-kicker">MODO PARTIDA</span><strong>Campo, placar e decisões. Só isso.</strong><p>Entre na transmissão exclusiva para acompanhar os lances e comandar sua equipe sem distrações.</p><button className="primary-action" type="button" onClick={handleGoToMatch} disabled={goToMatch.isPending}><Sparkles size={15} /> {goToMatch.isPending ? "Preparando partida…" : "Ir para partida"}</button></div> : <div className="matchday-empty">Nenhuma partida controlada está disponível para iniciar.</div>}</section>
    {view === "tabela" && <section className="standings-panel"><div className="section-heading compact"><div><span className="eyebrow">CLASSIFICAÇÃO</span><h2>{selectedCompetition ? selectedCompetition.name : "Tabela da competição"}</h2></div><span className="table-legend">P · J · V · E · D · SG</span></div><div className="table-scroll"><table><thead><tr><th>#</th><th>CLUBE</th><th>P</th><th>J</th><th>V</th><th>E</th><th>D</th><th>SG</th></tr></thead><tbody>{dashboard?.standings.length ? dashboard.standings.map((row) => <tr key={row.clubId} className={row.isControlledClub ? "controlled-row" : ""}><td>{row.position}</td><td>{row.clubName}</td><td>{row.points}</td><td>{row.played}</td><td>{row.wins}</td><td>{row.draws}</td><td>{row.losses}</td><td>{row.goalDifference > 0 ? `+${row.goalDifference}` : row.goalDifference}</td></tr>) : <tr className="waiting-row"><td>—</td><td colSpan={7}>{waitingMessage}</td></tr>}</tbody></table></div></section>}
    {view === "calendario" && <section className="calendar-layout"><article className="calendar-main"><span className="eyebrow">{controlledClub ? `CALENDÁRIO DE ${controlledClub.name.toUpperCase()}` : "CALENDÁRIO DA COMPETIÇÃO"}</span><h2>{selectedCompetition ? "Próximos compromissos" : "Agenda esportiva"}</h2><div className="calendar-list">{filteredFixtures.length ? <MatchTimeline fixtures={filteredFixtures} competitionName={selectedCompetition?.name ?? "Competição"} /> : <EmptyState icon={CalendarDays} title="Nenhuma partida agendada" description={waitingMessage} />}</div></article><aside className="calendar-aside"><CalendarDays size={26} /><h3>O calendário<br />decide o ritmo.</h3><p>{controlledClub ? "Os compromissos exibidos pertencem ao clube controlado no estado da carreira." : "Sem clube controlado, a agenda mostra a competição selecionada assim que houver fixtures."}</p></aside></section>}
    {view === "resultados" && <section className="results-layout"><article className="results-main"><div className="section-heading compact"><div><span className="eyebrow">ÚLTIMOS RESULTADOS</span><h2>{selectedCompetition ? selectedCompetition.name : "Histórico de partidas"}</h2></div><Goal size={18} /></div>{filteredResults.length ? <div className="result-list">{filteredResults.map((match) => <div className="result-row" key={match.key}><span>{formatMatchDate(match.scheduledAt)}</span><b>{match.homeClub.name}</b><strong>{match.homeGoals} — {match.awayGoals}</strong><b>{match.awayClub.name}</b><small>rodada {match.round ?? "—"}</small></div>)}</div> : <div className="result-empty"><span>—</span><h3>Ainda não há resultado registrado.</h3><p>{waitingMessage}</p></div>}</article><aside className="form-aside"><span className="eyebrow">PLACARES RECENTES</span><div className="form-slots">{filteredResults.slice(0, 5).map((match) => <i key={match.key}>{match.homeGoals}-{match.awayGoals}</i>)}{Array.from({ length: Math.max(0, 5 - filteredResults.slice(0, 5).length) }).map((_, index) => <i key={`empty-${index}`}>—</i>)}</div><p>Resultados confirmados aparecem nesta sequência.</p></aside></section>}
    {weekSummary && <div className="week-summary-backdrop" role="presentation"><section className="week-summary-modal" role="dialog" aria-modal="true" aria-labelledby="week-summary-title"><button className="week-summary-close" type="button" aria-label="Fechar resumo" onClick={() => setWeekSummary(null)}><X size={17} /></button><span className="eyebrow">RESUMO DA VIAGEM</span><h2 id="week-summary-title">A caminho da partida.</h2><p className="week-summary-lead">{weekSummary.weeks_advanced === 0 ? "O jogo já está na semana atual." : `${weekSummary.weeks_advanced} semana(s) foram concluídas até o compromisso.`}</p>{weekSummary.notice && <div className="week-summary-notice"><Bell size={16} /><span>{weekSummary.notice}</span></div>}<div className="week-summary-timeline">{weekSummary.cycles.length ? weekSummary.cycles.map((cycle) => <article className="week-summary-week" key={`${cycle.season}-${cycle.week}`}><div className="week-summary-marker"><span>SEMANA {cycle.week}</span><b>TEMPORADA {cycle.season}</b></div><div className="week-summary-events">{cycle.world_events.length ? cycle.world_events.map((event) => { const destination = eventDestination(event.type, event.title); return <button className="week-summary-event" type="button" key={event.event_id} onClick={() => { setWeekSummary(null); onNavigate?.(destination); }}><span className={`summary-event-icon severity-${event.severity}`}>{eventGlyph(event.type)}</span><span className="week-summary-event-copy"><strong>{event.title}</strong><p>{event.description || "Um acontecimento da carreira foi registrado."}</p><small>{eventDestinationLabel(destination)} <ArrowUpRight size={11} /></small></span></button>; }) : <div className="week-summary-empty">Nenhum alerta importante nesta semana.</div>}</div></article>) : <div className="week-summary-empty large">Nenhuma semana precisou ser percorrida.</div>}</div><button className="primary-action week-summary-continue" type="button" onClick={() => { setWeekSummary(null); onOpenMatch?.(); }}>Continuar para a partida <ArrowUpRight size={15} /></button></section></div>}
  </>;
}

function EntityLookupPanel() {
  const [entityType, setEntityType] = useState<"team" | "selection">("team");
  const [rawEntityId, setRawEntityId] = useState("");
  const entityId = Number(rawEntityId);
  const hasValidId = Number.isSafeInteger(entityId) && entityId > 0;
  const queryInput = useMemo(() => ({ entityType, entityId: hasValidId ? entityId : 1 }), [entityId, entityType, hasValidId]);
  const assetQuery = trpc.assets.resolve.useQuery(queryInput, { enabled: hasValidId });
  const asset = assetQuery.data;
  const presentation = getEntityAssetPresentation(asset?.mappingStatus, entityType);
  const selectedName = asset?.entityName ?? (entityType === "team" ? "Clube" : "Seleção");

  return <section className="entity-lookup" aria-labelledby="entity-lookup-title"><div className="section-heading compact"><div><span className="eyebrow">IDENTIDADE OFICIAL</span><h2 id="entity-lookup-title">Consultar escudo ou seleção</h2></div><Search size={18} /></div><p>Escolha uma entidade para consultar seu escudo ou seleção. Esta área apenas apresenta os dados disponíveis.</p><div className="entity-lookup-controls"><label><span>TIPO</span><select value={entityType} onChange={(event) => setEntityType(event.target.value as "team" | "selection")}><option value="team">Clube</option><option value="selection">Seleção</option></select></label><label><span>IDENTIFICAÇÃO</span><input value={rawEntityId} onChange={(event) => setRawEntityId(event.target.value.replace(/\D/g, ""))} inputMode="numeric" placeholder={entityType === "team" ? "Ex.: 1" : "Ex.: 6"} /></label></div>{!rawEntityId && <div className="entity-lookup-empty">Informe uma identificação para consultar o escudo ou ativo disponível.</div>}{hasValidId && <div className={`entity-asset-preview asset-${presentation.tone}`}>{assetQuery.isLoading ? <span className="crest-large">…</span> : <EntityAsset entityType={entityType} entityId={entityId} entityName={selectedName} />}<div><span className="eyebrow">{entityType === "team" ? "CLUBE" : "SELEÇÃO"} · ID {entityId}</span><h3>{assetQuery.isLoading ? "Consultando identificação" : selectedName}</h3><p>{assetQuery.isLoading ? "Consultando os dados do clube…" : presentation.label}</p>{asset?.primaryKitUrl && <small>Camisa primária original disponível.</small>}</div></div>}</section>;
}

export function StructurePage({ section, onSectionChange }: { section: AppSection; onSectionChange: (section: AppSection) => void }) {
  const isStadium = section === "estadio";
  const isTeam = section === "time";
  const isCt = section === "ct";
  const isMarket = section === "mercado" || section === "transferencias";
  const isFinance = section === "financas";
  const workspaceQuery = trpc.club.workspace.useQuery(undefined, { retry: 1 });
  const [financeCategory, setFinanceCategory] = useState("");
  const [financeSeason, setFinanceSeason] = useState("");
  const financeLedgerInput = useMemo(() => financeSeason || financeCategory ? { season: financeSeason ? Number(financeSeason) : undefined, category: financeCategory || undefined } : undefined, [financeSeason, financeCategory]);
  const financeLedgerQuery = trpc.club.financeLedger.useQuery(financeLedgerInput, { enabled: isFinance, retry: 1 });
  const financeAlertQuery = trpc.club.financeAlert.useQuery({ thresholdWeeks: 4 }, { enabled: isFinance, retry: 1 });
  const financeHistoryQuery = trpc.club.financeHistory.useQuery({ season: financeSeason ? Number(financeSeason) : 2026 }, { enabled: isFinance, retry: 1 });
  const [playerFilter, setPlayerFilter] = useState(() => sessionStorage.getItem("futmanager:filter:player") ?? "");
  const [competitionFilter, setCompetitionFilter] = useState(() => sessionStorage.getItem("futmanager:filter:competition") ?? "");
  useEffect(() => { sessionStorage.setItem("futmanager:filter:player", playerFilter); }, [playerFilter]);
  useEffect(() => { sessionStorage.setItem("futmanager:filter:competition", competitionFilter); }, [competitionFilter]);
  const competitionsQuery = trpc.matches.dashboard.useQuery(undefined, { enabled: isTeam, retry: 1 });
  const statsFilterInput = useMemo(() => competitionFilter ? { competitionId: Number(competitionFilter) } : undefined, [competitionFilter]);
  const playerStatsQuery = trpc.matches.playerStats.useQuery(statsFilterInput, { enabled: isTeam, retry: 1 });
  const workspace = workspaceQuery.data;
  const visiblePlayerStats = (playerStatsQuery?.data?.players ?? []).filter((player) => !playerFilter.trim() || String(player.playerId) === playerFilter.trim());
  const playerById = useMemo(() => new Map((workspace?.squad.players ?? []).map((player) => [player.playerId, player])), [workspace?.squad.players]);
  const starterPlayers = useMemo(() => (workspace?.squad.players ?? []).filter((player) => player.status === "Titular"), [workspace?.squad.players]);
  const benchPlayers = useMemo(() => (workspace?.squad.players ?? []).filter((player) => player.status !== "Titular"), [workspace?.squad.players]);
  const title = isStadium ? "Estádio" : isTeam ? "Time" : isCt ? "Centro de treinamento" : isFinance ? "Finanças" : section === "transferencias" ? "Transferências" : "Mercado";
  const intro = isStadium ? "O palco é uma operação. Capacidade, experiência e receita em camadas separadas." : isTeam ? "O elenco é uma fotografia viva — identidade, condição e contrato sem atalhos." : isCt ? "Desenvolvimento com contexto: comissão, carga e recuperação em uma mesma leitura." : isFinance ? "O caixa é uma leitura do ledger. O frontend não calcula nem altera o saldo." : "Leia a oportunidade antes de mover o mercado. Toda decisão passa pelo motor.";
  const structureRows = isFinance
    ? [{ label: "Caixa atual", value: workspace?.finance.cash !== null && workspace?.finance.cash !== undefined ? formatCash(workspace.finance.cash) : "sem registro" }, { label: "Caixa projetado · 39 sem.", value: workspace?.finance.projectedCash39Weeks !== null && workspace?.finance.projectedCash39Weeks !== undefined ? formatCash(workspace.finance.projectedCash39Weeks) : "sem registro" }, { label: "Orçamento", value: workspace?.finance.budget !== null && workspace?.finance.budget !== undefined ? formatCash(workspace.finance.budget) : "sem registro" }, { label: "Folha atletas", value: workspace?.finance.weeklyPlayerPayroll !== null && workspace?.finance.weeklyPlayerPayroll !== undefined ? formatCash(workspace.finance.weeklyPlayerPayroll) : "sem registro" }, { label: "Folha comissão", value: workspace?.finance.weeklyStaffPayroll !== null && workspace?.finance.weeklyStaffPayroll !== undefined ? formatCash(workspace.finance.weeklyStaffPayroll) : "sem registro" }, { label: "Manutenção CT", value: workspace?.finance.weeklyDepartmentMaintenance !== null && workspace?.finance.weeklyDepartmentMaintenance !== undefined ? formatCash(workspace.finance.weeklyDepartmentMaintenance) : "sem registro" }, { label: "Receitas ledger", value: workspace?.finance.ledgerIncome !== null && workspace?.finance.ledgerIncome !== undefined ? formatCash(workspace.finance.ledgerIncome) : "sem registro" }, { label: "Despesas ledger", value: workspace?.finance.ledgerExpense !== null && workspace?.finance.ledgerExpense !== undefined ? formatCash(workspace.finance.ledgerExpense) : "sem registro" }, { label: "Patrocínios", value: workspace?.finance.sponsorshipIncome !== null && workspace?.finance.sponsorshipIncome !== undefined ? formatCash(workspace.finance.sponsorshipIncome) : "sem registro" }, { label: "Bilheteria", value: workspace?.finance.ticketIncome !== null && workspace?.finance.ticketIncome !== undefined ? formatCash(workspace.finance.ticketIncome) : "sem registro" }, { label: "Premiações", value: workspace?.finance.prizeIncome !== null && workspace?.finance.prizeIncome !== undefined ? formatCash(workspace.finance.prizeIncome) : "sem registro" }, { label: "Fonte", value: workspace?.finance.source ?? "UNAVAILABLE" }]
    : isStadium
    ? [{ label: "Nome", value: workspace?.stadium.name ?? "sem registro" }, { label: "Capacidade", value: workspace?.stadium.capacity?.toLocaleString("pt-BR") ?? "sem registro" }, { label: "Nível", value: workspace?.stadium.level?.toString() ?? "sem registro" }, { label: "Status", value: workspace?.stadium.status ?? workspace?.stadium.source ?? "sem registro" }]
    : isCt
      ? [
          { label: "Comissão técnica", value: (workspace?.staff.members ?? []).length ? `${(workspace?.staff.members ?? []).length} profissional(is) no clube` : "nenhum profissional contratado", missing: !(workspace?.staff.members ?? []).length },
          { label: "Médicos", value: workspace?.staff.roleCounts.medico ? `${workspace.staff.roleCounts.medico} médico(s) no clube` : "nenhum médico contratado", missing: !workspace?.staff.roleCounts.medico },
          { label: "Auxiliares", value: workspace?.staff.roleCounts.auxiliar ? `${workspace.staff.roleCounts.auxiliar} auxiliar(es) no clube` : "nenhum auxiliar contratado", missing: !workspace?.staff.roleCounts.auxiliar },
          { label: "Departamentos", value: (workspace?.staff.departments ?? []).length ? `${(workspace?.staff.departments ?? []).length} disponível(is)` : "nenhum departamento disponível", missing: !(workspace?.staff.departments ?? []).length },
        ]
      : (workspace?.scouting.missions ?? []).length
        ? (workspace?.scouting.missions ?? []).map((mission) => ({ label: `${mission.scoutName ?? "Scout"} · ${mission.status}`, value: `${mission.region ?? "região não informada"} · ${mission.opportunities} oportunidade(s)` }))
        : [{ label: "Missões", value: "nenhuma missão disponível" }, { label: "Oportunidades", value: `${workspace?.scouting.opportunities ?? 0} disponível(is)` }, { label: "Relatórios", value: `${workspace?.scouting.reports ?? 0} disponível(is)` }, { label: "Scouts", value: `${workspace?.staff.roleCounts.scout ?? 0} profissional(is) ativo(s)` }];
  return <>
    <section className="page-intro"><div><span className="eyebrow">FUTMANAGER / {formatSection(section).toUpperCase()}</span><h1>{title}</h1><p>{intro}</p></div></section>
    <section className="feature-banner"><img src={isCt ? ASSETS.training : ASSETS.stadium} alt="" /><div className="banner-overlay" /><div className="banner-copy"><span className="eyebrow light">VISÃO DO CLUBE</span><h2>{isStadium ? "Construído para o dia de jogo." : isTeam ? "Uma só identidade por jogador." : isCt ? "Treino não é força. É processo." : "Toda proposta deixa um rastro."}</h2><p>Acompanhe a evolução do clube nesta temporada.</p></div></section>
    {isStadium && <StadiumOperationsPanel />}
    {isFinance && <section className="detail-panel finance-source-panel"><span className="eyebrow">FINANÇAS DA CARREIRA</span><h2>O saldo acompanha sua carreira.</h2><p>Caixa, orçamento e folha são atualizados conforme as decisões da sua carreira.</p><small>Última atualização: {workspace?.finance.updatedAt ?? "sem registro"}</small><div className={`finance-alert ${financeAlertQuery?.data?.status === "LOW_BALANCE" ? "is-warning" : "is-ok"}`}>{financeAlertQuery?.isLoading ? "Verificando reserva de caixa…" : financeAlertQuery?.data?.status === "LOW_BALANCE" ? "Alerta: caixa abaixo da reserva calculada." : "Reserva de caixa dentro do planejado."}</div><small>{financeHistoryQuery?.isLoading ? "Atualizando histórico da temporada…" : financeHistoryQuery?.data ? `Histórico da temporada ${financeSeason || 2026} disponível.` : "Histórico da temporada indisponível."}</small><div className="finance-ledger-toolbar"><b>Movimentações financeiras</b><label>Temporada <input value={financeSeason} onChange={(event) => setFinanceSeason(event.target.value.replace(/\D/g, ""))} inputMode="numeric" placeholder="todas" /></label><label>Categoria <input value={financeCategory} onChange={(event) => setFinanceCategory(event.target.value)} placeholder="todas" /></label><button className="outline-action" type="button" onClick={() => { const rows = financeLedgerQuery?.data ?? []; const header = "data;temporada;semana;tipo;categoria;valor;descrição\n"; const csv = header + rows.map((row) => [row.date, row.season, row.week, row.type, row.category, row.amount, row.description].map((value) => `\"${String(value).replaceAll('\\\"', '\\\"\\\"')}\"`).join(';')).join('\n'); const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" })); const anchor = document.createElement("a"); anchor.href = url; anchor.download = "futmanager-ledger.csv"; anchor.click(); URL.revokeObjectURL(url); }}>Exportar CSV</button></div>{financeLedgerQuery?.isLoading ? <LoadingState label="Atualizando movimentações…" /> : financeLedgerQuery?.data?.length ? <div className="finance-ledger-list">{financeLedgerQuery.data.slice(0, 12).map((row) => <div className="layer-row" key={row.ledgerId}><span>{row.date}</span><b>{row.category}</b><em>{formatCash(row.amount)} · {row.description}</em></div>)}</div> : <EmptyState icon={CircleDollarSign} title="Nenhum lançamento financeiro" description="Ainda não há movimentações registradas no ledger do clube." />}</section>}
    {(isCt || isMarket) && <StaffEconomyPanel mode={isCt ? "ct" : "market"} onNavigateToMarket={() => onSectionChange("mercado")} />}
    {isTeam && !workspace?.club && <EntityLookupPanel />}
    <div className="detail-grid">
      <article className="detail-panel"><div className="section-heading compact"><div><span className="eyebrow">{isTeam ? "ELENCO" : isStadium ? "ESTÁDIO" : isCt ? "COMISSÃO" : "SCOUTING"}</span><h2>{isTeam ? `${workspace?.club?.name ?? "Clube"} · elenco` : isStadium ? "Estrutura do estádio" : isCt ? "Comissão e saúde" : "Missões e oportunidades"}</h2></div>{isTeam ? <label className="table-legend">COMPETIÇÃO <select aria-label="Filtrar estatísticas por competição" value={competitionFilter} onChange={(event) => setCompetitionFilter(event.target.value)}><option value="">TODAS</option>{(competitionsQuery?.data?.competitions ?? []).map((competition) => <option key={competition.competitionId} value={String(competition.competitionId)}>{competition.name}</option>)}</select> · ATLETA <select aria-label="Filtrar estatísticas por atleta" value={playerFilter} onChange={(event) => setPlayerFilter(event.target.value)}><option value="">TODOS</option>{(workspace?.squad.players ?? []).map((player) => <option key={player.playerId} value={String(player.playerId)}>{player.name}</option>)}</select></label> : <Gauge size={18} />}</div>{isTeam ? workspaceQuery.isLoading ? <LoadingState label="Atualizando elenco…" /> : (workspace?.squad.players ?? []).length ? <>{starterPlayers.length ? <FormationPitch players={starterPlayers} /> : null}{benchPlayers.length ? <><span className="formation-bench-label">BANCO · {benchPlayers.length} reserva(s)</span><div className="player-grid">{benchPlayers.map((player, index) => <PlayerCard key={player.playerId} player={player} index={index} />)}</div></> : null}</> : <EmptyState icon={Users} title="Nenhum jogador está disponível" description="O elenco do clube controlado ainda não tem atletas persistidos." actionLabel="Ir para o Mercado" onAction={() => onSectionChange("mercado")} /> : <div className="layer-list">{structureRows.map((item, index) => isCt ? <button type="button" className="layer-row layer-row-button" key={`${item.label}-${index}`} onClick={() => { if ("missing" in item && item.missing) { toast(`${item.label} ainda não possui registros. Vá ao Mercado para contratar.`); onSectionChange("mercado"); return; } toast(`${item.label} já está disponível no clube.`); }}><span>{String(index + 1).padStart(2, "0")}</span><b>{item.label}</b><em>{item.value}</em><ChevronRight size={15} /></button> : <div className="layer-row" key={`${item.label}-${index}`}><span>{String(index + 1).padStart(2, "0")}</span><b>{item.label}</b><em>{item.value}</em><ChevronRight size={15} /></div>)}</div>}<button className="outline-action" onClick={() => toast(workspace?.source.message ?? "Atualizando as informações do clube.")}>Atualizar informações <ArrowUpRight size={15} /></button></article>
      <aside className="detail-side"><div className="empty-panel"><span className="empty-mark">{isTeam ? workspace?.squad.total ?? "—" : isStadium ? workspace?.stadium.capacity?.toLocaleString("pt-BR") ?? "—" : isCt ? (workspace?.staff.members ?? []).length || "—" : (workspace?.scouting.missions ?? []).length || "—"}</span><span className="eyebrow">{workspace?.source.available ? "INFORMAÇÕES ATUALIZADAS" : "INFORMAÇÕES INDISPONÍVEIS"}</span><h3>{isTeam ? `${workspace?.squad.starters ?? 0} titulares · ${workspace?.squad.reserves ?? 0} reservas` : isStadium ? workspace?.stadium.name ?? "Estádio sem registro" : isCt ? (workspace?.staff.members ?? []).length ? `${(workspace?.staff.members ?? []).length} profissional(is) ativo(s)` : "Ainda não há comissão contratada." : (workspace?.scouting.missions ?? []).length ? `${(workspace?.scouting.missions ?? []).length} missão(ões) de scouting` : "Ainda não há missões de scouting."}</h3><p>{isTeam ? `${workspace?.squad.injured ?? 0} lesão(ões) ativa(s) no elenco.` : isCt ? `${workspace?.health.count ?? 0} lesão(ões) ativa(s) · ${workspace?.staff.roleCounts.medico ?? 0} médico(s) registrado(s).` : `${workspace?.scouting.opportunities ?? 0} oportunidade(s) · ${workspace?.scouting.reports ?? 0} relatório(s).`}</p><button className="primary-action dark" onClick={() => onSectionChange("clube")}>Voltar ao clube <ArrowUpRight size={16} /></button></div></aside>
        </div>
    {isTeam && <section className="standings-panel team-stats-panel"><div className="section-heading compact"><div><span className="eyebrow">ESTATÍSTICAS DA TEMPORADA</span><h2>Produção por atleta</h2></div><span className="table-legend">G · A · MIN</span></div>{playerStatsQuery?.isLoading ? <TableSkeleton rows={4} columns={4} /> : playerStatsQuery?.error ? <div className="fixture-empty">As estatísticas não puderam ser consultadas.</div> : visiblePlayerStats.length ? <div className="layer-list">{visiblePlayerStats.slice(0, 12).map((stat) => { const player = playerById.get(stat.playerId); return <div className="layer-row" key={stat.playerId}><span>#{stat.playerId}</span><b>{player?.name ?? "Atleta não localizado"} · {player?.position ?? "posição não informada"}</b><em>{stat.goals} G · {stat.assists} A · {stat.minutes} min · {stat.cards} cartões</em></div>; })}</div> : <div className="fixture-empty">Nenhuma estatística individual está disponível para os filtros atuais.</div>}</section>}
  </>;
}
function MatchdayPage({ onBack }: { onBack: () => void }) {
  const dashboardQuery = trpc.matches.dashboard.useQuery(undefined, { retry: 1 });
  const workspaceQuery = trpc.club.workspace.useQuery(undefined, { retry: 1 });
  const dashboard = dashboardQuery.data;
  const controlledClub = dashboard?.controlledClub ?? null;
  const nextMatch = dashboard?.upcomingFixtures.find((match) => controlledClub && (match.homeClub.clubId === controlledClub.clubId || match.awayClub.clubId === controlledClub.clubId)) ?? null;

  if (dashboardQuery.isLoading) {
    return <section className="match-only-page"><div className="match-only-loading">Preparando o campo…</div></section>;
  }

  return <section className="match-only-page" aria-labelledby="match-only-title">
    <header className="match-only-header"><button className="match-back-button" type="button" onClick={onBack}><ArrowLeft size={18} /> Nossas Partidas</button><div className="match-only-brand"><span className="live-badge pre"><Sparkles size={13} /> MODO PARTIDA</span><span>FUTMANAGER</span></div><span className="match-only-round">{nextMatch ? `RODADA ${nextMatch.round ?? "—"}` : "PRÉ-JOGO"}</span></header>
    <div className="match-only-heading"><span className="eyebrow">CAMPO EXCLUSIVO</span><h1 id="match-only-title">Agora é só o jogo.</h1><p>{nextMatch ? "Acompanhe os lances e tome as decisões nos momentos certos." : "Nenhuma partida controlada está pronta no calendário."}</p></div>
    {nextMatch ? <InteractiveMatchCenter match={nextMatch} players={workspaceQuery.data?.squad.players ?? []} /> : <div className="match-only-empty"><Goal size={24} /><h2>Sem partida para iniciar</h2><p>Volte ao calendário para conferir o próximo compromisso do seu clube.</p><button className="primary-action" type="button" onClick={onBack}>Voltar ao calendário <ArrowUpRight size={15} /></button></div>}
  </section>;
}

function SponsorshipPage() {
  return <><section className="page-intro sponsorship-intro"><div><span className="eyebrow">SEU CLUBE / VALOR DE MARCA</span><h1>Patrocinadores</h1><p>O elenco, o CT e o estádio definem o overall institucional. Esse valor abre propostas melhores, mas cada janela exige decisão antes de expirar.</p></div></section><SponsorshipPanel /></>;
}

export default function Home({ section = "inicio", onSectionChange = () => undefined }: { section?: AppSection; onSectionChange?: (section: AppSection) => void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const careerQuery = trpc.career.current.useQuery(undefined, { retry: 1 });
  const main = useMemo(() => section === "clube" ? <Dashboard onSectionChange={onSectionChange} /> : section === "partidas" ? <MatchesPage onOpenMatch={() => onSectionChange("partida")} onNavigate={onSectionChange} /> : section === "partida" ? <MatchdayPage onBack={() => onSectionChange("partidas")} /> : section === "patrocinadores" ? <SponsorshipPage /> : section === "operacoes" ? <OperationsPanel /> : <StructurePage section={section} onSectionChange={onSectionChange} />, [section, onSectionChange]);

  if (section === "inicio" || (!careerQuery.isLoading && careerQuery.data?.started === false)) {
    return <CareerStart onStarted={() => onSectionChange("clube")} onContinue={() => onSectionChange("clube")} />;
  }
  if (section === "partida") {
    return <MatchdayPage onBack={() => onSectionChange("partidas")} />;
  }
  return <div className="app-shell"><Sidebar section={section} onSectionChange={onSectionChange} open={menuOpen} onClose={() => setMenuOpen(false)} /><main className="app-main"><Header section={section} onMenu={() => setMenuOpen(true)} /><div className="page-wrap">{main}</div><footer className="page-footer"><span>FUTMANAGER / EDITORIAL DE ARQUIBANCADA</span><span>GESTÃO · CAMPO · FUTURO</span></footer></main></div>;
}
