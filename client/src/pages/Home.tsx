/*
 * FutManager — Editorial de Arquibancada.
 * Dashboard visual offline-first: apresenta o contrato visual do motor sem inventar
 * jogadores, caixa, resultados ou regras; dados ausentes são mostrados como estados honestos.
 */
import React, { useMemo, useState } from "react";
import { toast } from "sonner";
import { trpc } from "@/lib/trpc";
import { getEntityAssetPresentation } from "@/lib/entityAsset";
import { EntityAsset } from "@/components/EntityAsset";
import CareerStart from "@/pages/CareerStart";
import {
  Activity,
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
  Landmark,
  Users,
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
  { id: "transferencias", label: "Transferências", short: "07", icon: ClipboardList },
];

const events = [
  { type: "WORLD", tone: "blue", label: "MOTOR", title: "Estado do mundo carregado", detail: "Aguardando o estado oficial do clube", time: "agora", icon: Activity },
  { type: "MATCH", tone: "green", label: "PRÓXIMA PARTIDA", title: "Calendário em preparação", detail: "O próximo compromisso aparece quando o calendário for carregado", time: "—", icon: Goal },
  { type: "FINANCE", tone: "coral", label: "FINANÇAS", title: "Caixa em preparação", detail: "O saldo oficial vem do caixa do clube", time: "—", icon: CircleDollarSign },
  { type: "TRAINING", tone: "ink", label: "TREINAMENTO", title: "Nenhum relatório novo", detail: "A evolução será lida a partir da comissão técnica", time: "—", icon: Dumbbell },
];

const rosterRows = [
  { number: "—", name: "Elenco principal", position: "FIRST_TEAM", status: "AGUARDANDO DADOS", tone: "muted" },
  { number: "—", name: "Reservas", position: "RESERVE", status: "AGUARDANDO DADOS", tone: "muted" },
  { number: "—", name: "Base", position: "YOUTH", status: "AGUARDANDO DADOS", tone: "muted" },
];

function formatSection(section: AppSection) {
  return navItems.find((item) => item.id === section)?.label ?? "Início";
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
  return (
    <header className="topbar">
      <button className="mobile-menu" onClick={onMenu} aria-label="Abrir menu"><Menu size={22} /></button>
      <div className="crumb"><span>FUTMANAGER</span><ChevronRight size={14} /><b>{formatSection(section).toUpperCase()}</b></div>
      <div className="top-actions"><span className="data-status"><span className="status-pip" /> MODO VISUAL · ESTADO OFICIAL</span><button className="icon-btn" onClick={() => toast("Alertas virão dos eventos persistidos pelo motor.")} aria-label="Alertas"><Bell size={18} /><i>0</i></button><button className="avatar" onClick={() => toast("Perfil do manager será conectado na próxima etapa.")} aria-label="Perfil">FM</button></div>
    </header>
  );
}

function Dashboard({ onSectionChange }: { onSectionChange: (section: AppSection) => void }) {
  const clubStateQuery = trpc.matches.dashboard.useQuery(undefined, { retry: 1 });
  const controlledClub = clubStateQuery.data?.controlledClub ?? null;

  return (
    <>
      <section className="hero-panel">
        <div className="hero-image"><img src={ASSETS.stadium} alt="Estádio vazio em perspectiva editorial" /><div className="hero-scrim" /><div className="hero-pitch-lines" aria-hidden="true"><span /><span /><span /></div></div>
        <div className="hero-copy"><span className="eyebrow light">SEU CLUBE / CENTRO DE COMANDO</span><h1>Seu clube.<br /><em>Sob seu comando.</em></h1><p>Elenco, caixa, estádio e calendário em uma só leitura. O estado do clube entra aqui, sem atalhos.</p><button className="primary-action" onClick={() => onSectionChange("partidas")}>Ver nossas partidas <ArrowUpRight size={16} /></button></div>
        <div className="hero-stamp"><img src={ASSETS.mark} alt="" /><div><span>FUT</span><strong>MANAGER</strong><small>GESTÃO · CAMPO · FUTURO</small></div></div>
        <div className="hero-meta"><span>ESTÁDIO / VISÃO GERAL</span><span>LAT 00° · LONG 00°</span></div>
      </section>
      <div className="metrics-grid">
        <Metric label="CAIXA" value="—" note="Caixa do clube aguardando estado" accent="green" icon={CircleDollarSign} />
        <Metric label="REPUTAÇÃO" value="—" note="Reputação do clube aguardando estado" accent="blue" icon={Sparkles} />
        <Metric label="COMPETIÇÃO" value="—" note="Classificação aguardando estado" accent="coral" icon={Flag} />
        <Metric label="ELENCO" value="—" note="Elenco aguardando estado oficial" accent="ink" icon={Users} />
      </div>
      <section className="content-grid">
        <div className="main-column">
          <div className="section-heading"><div><span className="eyebrow">AGENDA DO CLUBE</span><h2>Próxima partida</h2></div><button className="text-action" onClick={() => onSectionChange("time")}>Ver time <ArrowUpRight size={15} /></button></div>
          <article className="fixture-card">
            <div className="fixture-date"><span>PRÓXIMO COMPROMISSO</span><strong>—</strong><small>Data a confirmar</small></div>
            <div className="fixture-match"><div>{controlledClub ? <EntityAsset className="crest-placeholder" entityType="team" entityId={controlledClub.clubId} entityName={controlledClub.name} /> : <span className="crest-placeholder">?</span>}<b>{controlledClub?.name ?? "Seu clube"}</b><small>MANDANTE / —</small></div><div className="versus">VS</div><div><span className="crest-placeholder away">?</span><b>Adversário</b><small>VISITANTE / —</small></div></div>
            <div className="fixture-note"><CalendarDays size={15} /><span>O próximo compromisso virá do calendário oficial.</span></div>
          </article>
          <div className="section-heading news-heading"><div><span className="eyebrow">SINAL DO MUNDO</span><h2>Feed de notícias</h2></div><button className="filter-btn" onClick={() => toast("Filtros serão alimentados pelos acontecimentos do clube.")}><SlidersHorizontal size={15} /> Filtrar</button></div>
          <div className="news-list">{events.map((event) => <EventCard key={event.type} {...event} />)}</div>
        </div>
        <aside className="side-column">
          <div className="section-heading compact"><div><span className="eyebrow">SITUAÇÃO ATUAL</span><h2>Seu clube</h2></div><button className="more-btn" aria-label="Mais opções" onClick={() => toast("O retrato do clube virá do estado oficial.")}>···</button></div>
          <article className="club-card"><div className="club-card-top">{controlledClub ? <EntityAsset entityType="team" entityId={controlledClub.clubId} entityName={controlledClub.name} /> : <span className="crest-large">?</span>}<div><span className="eyebrow">CLUBE CONTROLADO</span><h3>{controlledClub?.name ?? "Não conectado"}</h3><p>{controlledClub ? "Ativo resolvido pelo vínculo oficial" : "Selecione um estado de carreira"}</p></div></div><div className="club-lines"><div><span>ESTÁDIO</span><b>—</b></div><div><span>CT</span><b>—</b></div><div><span>TORCIDA</span><b>—</b></div></div><button className="secondary-action" onClick={() => onSectionChange("estadio")}>Ver estruturas <ChevronRight size={15} /></button></article>
          <article className="read-card" style={{ backgroundImage: `url(${ASSETS.texture})` }}><span className="eyebrow">LEITURA DO DIA</span><h3>Leia o cenário<br />antes de mexer<br /><em>no elenco.</em></h3><div className="read-footer"><span>EDITORIAL / 001</span><ArrowUpRight size={16} /></div></article>
          <div className="integrity-note"><span className="live-dot" /><div><b>ESTADO COMO FONTE OFICIAL</b><p>A interface apresenta decisões; o motor guarda as consequências.</p></div></div>
        </aside>
      </section>
    </>
  );
}

function EventCard({ type, tone, label, title, detail, time, icon: Icon }: { type: string; tone: string; label: string; title: string; detail: string; time: string; icon: typeof Activity }) {
  return <button className={`event-card event-${tone}`} onClick={() => toast(`${type}: o detalhe será aberto a partir do evento persistido.`)}><div className="event-icon"><Icon size={17} /></div><div className="event-content"><div className="event-label"><span>{label}</span><time>{time}</time></div><h3>{title}</h3><p>{detail}</p></div><ArrowUpRight className="event-open" size={16} /></button>;
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

export function MatchesPage({ initialView = "competicoes" }: { initialView?: "competicoes" | "tabela" | "calendario" | "resultados" }) {
  const [view, setView] = useState<"competicoes" | "tabela" | "calendario" | "resultados">(initialView);
  const [competitionId, setCompetitionId] = useState<number | undefined>();
  const queryInput = useMemo(() => (competitionId ? { competitionId } : undefined), [competitionId]);
  const dashboardQuery = trpc.matches.dashboard.useQuery(queryInput, { retry: 1 });
  const dashboard = dashboardQuery.data;
  const selectedCompetition = dashboard?.selectedCompetition ?? null;
  const controlledClub = dashboard?.controlledClub ?? null;
  const filteredFixtures = controlledClub
    ? dashboard?.upcomingFixtures.filter((match) => match.homeClub.clubId === controlledClub.clubId || match.awayClub.clubId === controlledClub.clubId) ?? []
    : dashboard?.upcomingFixtures ?? [];
  const filteredResults = controlledClub
    ? dashboard?.recentResults.filter((match) => match.homeClub.clubId === controlledClub.clubId || match.awayClub.clubId === controlledClub.clubId) ?? []
    : dashboard?.recentResults ?? [];
  const nextMatch = filteredFixtures[0] ?? null;
  const totalMatches = (dashboard?.upcomingFixtures.length ?? 0) + (dashboard?.recentResults.length ?? 0);
  const tabs = [
    ["competicoes", "Competições"],
    ["tabela", "Tabela"],
    ["calendario", "Calendário"],
    ["resultados", "Resultados"],
  ] as const;
  const waitingMessage = dashboardQuery.isLoading
    ? "Consultando o estado oficial do motor…"
    : dashboardQuery.error
      ? "Não foi possível consultar o estado do motor neste momento."
      : dashboard?.source.message ?? "Aguardando a leitura do estado do motor.";

  return <>
    <section className="page-intro match-intro"><div><span className="eyebrow">SEU CLUBE / CICLO ESPORTIVO</span><h1>Nossas partidas</h1><p>Competições, calendário, classificação e resultados em uma única leitura. O estado exibido vem diretamente do motor.</p></div><div className="match-score-mark"><span>JOGOS</span><strong>{dashboardQuery.isLoading ? "—" : totalMatches}</strong><small>{selectedCompetition?.seasonYear ? `temporada ${selectedCompetition.seasonYear}` : "estado atual"}</small></div></section>
    <section className="matches-command"><div className="matches-heading"><div><span className="eyebrow">PAINEL DE COMPETIÇÃO</span><h2>{selectedCompetition ? selectedCompetition.name : "Leia o jogo antes da rodada."}</h2></div><span className="match-state"><span className="status-pip" /> {dashboard?.source.available ? "estado SQL conectado" : dashboardQuery.isLoading ? "consultando estado" : "estado indisponível"}</span></div><div className="match-tabs" role="tablist" aria-label="Visões de partidas">{tabs.map(([id, label]) => <button key={id} className={view === id ? "selected" : ""} onClick={() => setView(id)} role="tab" aria-selected={view === id}>{label}</button>)}</div></section>
    {view === "competicoes" && <section className="competition-layout"><article className="competition-main"><div className="section-heading compact"><div><span className="eyebrow">COMPETIÇÕES PERSISTIDAS</span><h2>{selectedCompetition ? `${dashboard?.competitions.length ?? 0} competição(ões) disponível(is)` : "Nenhuma competição persistida"}</h2></div><Flag size={18} /></div>{dashboard?.competitions.length ? <div className="competition-select-list">{dashboard.competitions.map((competition) => <button key={competition.competitionId} className={`competition-select ${competition.competitionId === dashboard.selectedCompetitionId ? "is-selected" : ""}`} onClick={() => setCompetitionId(competition.competitionId)}><span className="competition-badge">{competition.seasonYear ?? "—"}</span><span><b>{competition.name}</b><small>{competition.type} · {competition.format} · {competition.status}</small></span><em>{competition.playedMatches} realizados · {competition.scheduledFixtures} agendados</em></button>)}</div> : <div className="competition-empty"><span className="competition-badge">—</span><div><b>{dashboardQuery.isLoading ? "Lendo o estado esportivo" : "Nenhuma competição foi criada na carreira."}</b><p>{waitingMessage}</p></div></div>}</article><aside className="competition-side"><span className="eyebrow">PRÓXIMO JOGO</span>{nextMatch ? <><h3>{nextMatch.homeClub.name}<br />× {nextMatch.awayClub.name}</h3><p>{selectedCompetition?.name} · rodada {nextMatch.round ?? "—"}</p><div className="side-rule" /><span className="mini-label">AGENDA</span><b>{formatMatchDate(nextMatch.scheduledAt)}</b></> : <><h3>Sem compromisso<br />confirmado.</h3><p>{controlledClub ? "Não há fixture futuro para o clube controlado nesta competição." : "A carreira ainda não possui clube controlado ou fixture persistido."}</p><div className="side-rule" /><span className="mini-label">CONTEXTO</span><b>—</b></>}</aside></section>}
    {view === "tabela" && <section className="standings-panel"><div className="section-heading compact"><div><span className="eyebrow">CLASSIFICAÇÃO</span><h2>{selectedCompetition ? selectedCompetition.name : "Tabela da competição"}</h2></div><span className="table-legend">P · J · V · E · D · SG</span></div><div className="table-scroll"><table><thead><tr><th>#</th><th>CLUBE</th><th>P</th><th>J</th><th>V</th><th>E</th><th>D</th><th>SG</th></tr></thead><tbody>{dashboard?.standings.length ? dashboard.standings.map((row) => <tr key={row.clubId} className={row.isControlledClub ? "controlled-row" : ""}><td>{row.position}</td><td>{row.clubName}</td><td>{row.points}</td><td>{row.played}</td><td>{row.wins}</td><td>{row.draws}</td><td>{row.losses}</td><td>{row.goalDifference > 0 ? `+${row.goalDifference}` : row.goalDifference}</td></tr>) : <tr className="waiting-row"><td>—</td><td colSpan={7}>{waitingMessage}</td></tr>}</tbody></table></div></section>}
    {view === "calendario" && <section className="calendar-layout"><article className="calendar-main"><span className="eyebrow">{controlledClub ? `CALENDÁRIO DE ${controlledClub.name.toUpperCase()}` : "CALENDÁRIO DA COMPETIÇÃO"}</span><h2>{selectedCompetition ? "Próximos compromissos" : "Agenda esportiva"}</h2><div className="calendar-list">{filteredFixtures.length ? filteredFixtures.map((match) => <div key={match.key}><span>{formatMatchDate(match.scheduledAt).split(" ")[0]}</span><b>{match.homeClub.name} × {match.awayClub.name}</b><small>{selectedCompetition?.name ?? "Competição"} · rodada {match.round ?? "—"} · {formatMatchTime(match.scheduledAt)}</small></div>) : <div><span>—</span><b>Nenhuma partida agendada</b><small>{waitingMessage}</small></div>}</div></article><aside className="calendar-aside"><CalendarDays size={26} /><h3>O calendário<br />decide o ritmo.</h3><p>{controlledClub ? "Os compromissos exibidos pertencem ao clube controlado no estado da carreira." : "Sem clube controlado, a agenda mostra a competição selecionada assim que houver fixtures."}</p></aside></section>}
    {view === "resultados" && <section className="results-layout"><article className="results-main"><div className="section-heading compact"><div><span className="eyebrow">ÚLTIMOS RESULTADOS</span><h2>{selectedCompetition ? selectedCompetition.name : "Histórico de partidas"}</h2></div><Goal size={18} /></div>{filteredResults.length ? <div className="result-list">{filteredResults.map((match) => <div className="result-row" key={match.key}><span>{formatMatchDate(match.scheduledAt)}</span><b>{match.homeClub.name}</b><strong>{match.homeGoals} — {match.awayGoals}</strong><b>{match.awayClub.name}</b><small>rodada {match.round ?? "—"}</small></div>)}</div> : <div className="result-empty"><span>—</span><h3>Ainda não há resultado registrado.</h3><p>{waitingMessage}</p></div>}</article><aside className="form-aside"><span className="eyebrow">PLACARES RECENTES</span><div className="form-slots">{filteredResults.slice(0, 5).map((match) => <i key={match.key}>{match.homeGoals}-{match.awayGoals}</i>)}{Array.from({ length: Math.max(0, 5 - filteredResults.slice(0, 5).length) }).map((_, index) => <i key={`empty-${index}`}>—</i>)}</div><p>Somente placares persistidos pelo motor aparecem nesta sequência.</p></aside></section>}
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

  return <section className="entity-lookup" aria-labelledby="entity-lookup-title"><div className="section-heading compact"><div><span className="eyebrow">IDENTIDADE OFICIAL</span><h2 id="entity-lookup-title">Consultar escudo ou seleção</h2></div><Search size={18} /></div><p>Informe o ID da entidade no SQL do motor. A tela consulta somente o vínculo oficial e não cria clube, seleção ou ativo.</p><div className="entity-lookup-controls"><label><span>TIPO</span><select value={entityType} onChange={(event) => setEntityType(event.target.value as "team" | "selection")}><option value="team">Clube</option><option value="selection">Seleção</option></select></label><label><span>ID OFICIAL</span><input value={rawEntityId} onChange={(event) => setRawEntityId(event.target.value.replace(/\D/g, ""))} inputMode="numeric" placeholder={entityType === "team" ? "Ex.: 1" : "Ex.: 6"} /></label></div>{!rawEntityId && <div className="entity-lookup-empty">Informe um ID para resolver o ativo diretamente no estado do motor.</div>}{hasValidId && <div className={`entity-asset-preview asset-${presentation.tone}`}>{assetQuery.isLoading ? <span className="crest-large">…</span> : <EntityAsset entityType={entityType} entityId={entityId} entityName={selectedName} />}<div><span className="eyebrow">{entityType === "team" ? "CLUBE" : "SELEÇÃO"} · ID {entityId}</span><h3>{assetQuery.isLoading ? "Lendo vínculo oficial" : selectedName}</h3><p>{assetQuery.isLoading ? "Consultando o SQLite do motor…" : presentation.label}</p>{asset?.primaryKitUrl && <small>Camisa primária original disponível.</small>}</div></div>}</section>;
}

function StructurePage({ section, onSectionChange }: { section: AppSection; onSectionChange: (section: AppSection) => void }) {
  const isStadium = section === "estadio";
  const isTeam = section === "time";
  const isCt = section === "ct";
  const isMarket = section === "mercado" || section === "transferencias";
  const title = isStadium ? "Estádio" : isTeam ? "Time" : isCt ? "Centro de treinamento" : section === "transferencias" ? "Transferências" : "Mercado";
  const intro = isStadium ? "O palco é uma operação. Capacidade, experiência e receita em camadas separadas." : isTeam ? "O elenco é uma fotografia viva — identidade, condição e contrato sem atalhos." : isCt ? "Desenvolvimento com contexto: comissão, carga e recuperação em uma mesma leitura." : "Leia a oportunidade antes de mover o mercado. Toda decisão passa pelo motor.";
  return <>
    <section className="page-intro"><div><span className="eyebrow">FUTMANAGER / {formatSection(section).toUpperCase()}</span><h1>{title}</h1><p>{intro}</p></div><span className="page-code">{section === "estadio" ? "ST-01" : section === "time" ? "TM-01" : section === "ct" ? "CT-01" : "MK-01"}</span></section>
    <section className="feature-banner"><img src={isCt ? ASSETS.training : ASSETS.stadium} alt="" /><div className="banner-overlay" /><div className="banner-copy"><span className="eyebrow light">DADOS DO MOTOR</span><h2>{isStadium ? "Construído para o dia de jogo." : isTeam ? "Uma só identidade por jogador." : isCt ? "Treino não é força. É processo." : "Toda proposta deixa um rastro."}</h2><p>Estrutura visual pronta para receber o estado persistido.</p></div></section>
    {isTeam && <EntityLookupPanel />}
    <div className="detail-grid">
      <article className="detail-panel"><div className="section-heading compact"><div><span className="eyebrow">{isTeam ? "CATEGORIAS" : isStadium ? "QUATRO CAMADAS" : isCt ? "EIXOS" : "PAINEL"}</span><h2>{isTeam ? "Estado do elenco" : isStadium ? "Estrutura do estádio" : isCt ? "Ciclo de desenvolvimento" : "Estado do mercado"}</h2></div><Gauge size={18} /></div>{isTeam ? rosterRows.map((row) => <div className="roster-row" key={row.position}><span className="roster-number">{row.number}</span><div><b>{row.name}</b><small>{row.position}</small></div><span className="muted-status">{row.status}</span><ChevronRight size={15} /></div>) : <div className="layer-list">{(isStadium ? ["Arquibancada", "Campo", "Estrutura", "Equipes"] : isCt ? ["Comissão", "Treinamento", "Recuperação", "Desenvolvimento"] : ["Janela", "Propostas", "Scouting", "Histórico"]).map((item, i) => <div className="layer-row" key={item}><span>0{i + 1}</span><b>{item}</b><em>indisponível</em><ChevronRight size={15} /></div>)}</div>}<button className="outline-action" onClick={() => toast("Esta ação será habilitada quando o serviço correspondente estiver conectado.")}>Consultar estado <ArrowUpRight size={15} /></button></article>
      <aside className="detail-side"><div className="empty-panel"><span className="empty-mark">—</span><span className="eyebrow">ESTADO NÃO CONECTADO</span><h3>Sem dados inventados.</h3><p>Esta tela já está preparada para os serviços do motor, mas ainda não substitui o estado oficial por uma cópia local.</p><button className="primary-action dark" onClick={() => onSectionChange("clube")}>Voltar ao clube <ArrowUpRight size={16} /></button></div></aside>
    </div>
  </>;
}

export default function Home({ section = "clube", onSectionChange = () => undefined }: { section?: AppSection; onSectionChange?: (section: AppSection) => void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const careerQuery = trpc.career.current.useQuery(undefined, { retry: 1 });
  const main = useMemo(() => section === "clube" ? <Dashboard onSectionChange={onSectionChange} /> : section === "partidas" ? <MatchesPage /> : <StructurePage section={section} onSectionChange={onSectionChange} />, [section, onSectionChange]);

  if (!careerQuery.isLoading && careerQuery.data?.started === false) {
    return <CareerStart onStarted={() => onSectionChange("clube")} />;
  }
  return <div className="app-shell"><Sidebar section={section} onSectionChange={onSectionChange} open={menuOpen} onClose={() => setMenuOpen(false)} /><main className="app-main"><Header section={section} onMenu={() => setMenuOpen(true)} /><div className="page-wrap">{main}</div><footer className="page-footer"><span>FUTMANAGER / EDITORIAL DE ARQUIBANCADA</span><span>SQL · STATE · SERVICES</span></footer></main></div>;
}
