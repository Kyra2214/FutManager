/*
 * FutManager — Editorial de Arquibancada.
 * Dashboard visual offline-first: apresenta o contrato visual do motor sem inventar
 * jogadores, caixa, resultados ou regras; dados ausentes são mostrados como estados honestos.
 */
import { useMemo, useState } from "react";
import { toast } from "sonner";
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
  { id: "inicio", label: "Início", short: "01", icon: LayoutDashboard },
  { id: "estadio", label: "Estádio", short: "02", icon: Landmark },
  { id: "time", label: "Time", short: "03", icon: Shield },
  { id: "ct", label: "CT", short: "04", icon: Dumbbell },
  { id: "mercado", label: "Mercado", short: "05", icon: ArrowUpRight },
  { id: "transferencias", label: "Transferências", short: "06", icon: ClipboardList },
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
  return (
    <>
      <section className="hero-panel">
        <div className="hero-image"><img src={ASSETS.stadium} alt="Estádio vazio em perspectiva editorial" /><div className="hero-scrim" /><div className="hero-pitch-lines" aria-hidden="true"><span /><span /><span /></div></div>
        <div className="hero-copy"><span className="eyebrow light">CENTRO DE COMANDO / 01</span><h1>O próximo jogo<br /><em>começa no caixa.</em></h1><p>Tenha o pulso do clube em uma só leitura. O estado do clube entra aqui, sem atalhos.</p><button className="primary-action" onClick={() => onSectionChange("time")}>Abrir o time <ArrowUpRight size={16} /></button></div>
        <div className="hero-stamp"><img src={ASSETS.mark} alt="" /><div><span>FUT</span><strong>MANAGER</strong><small>GESTÃO · CAMPO · FUTURO</small></div></div>
        <div className="hero-meta"><span>ESTÁDIO / VISÃO GERAL</span><span>LAT 00° · LONG 00°</span></div>
      </section>
      <div className="metrics-grid">
        <Metric label="CAIXA" value="—" note="Caixa do clube aguardando estado" accent="green" icon={CircleDollarSign} />
        <Metric label="REPUTAÇÃO" value="—" note="Club reputation não disponível" accent="blue" icon={Sparkles} />
        <Metric label="COMPETIÇÃO" value="—" note="Classificação aguardando estado" accent="coral" icon={Flag} />
        <Metric label="ELENCO" value="—" note="Elenco aguardando estado oficial" accent="ink" icon={Users} />
      </div>
      <section className="content-grid">
        <div className="main-column">
          <div className="section-heading"><div><span className="eyebrow">AGENDA DO CLUBE</span><h2>Próxima partida</h2></div><button className="text-action" onClick={() => onSectionChange("time")}>Ver time <ArrowUpRight size={15} /></button></div>
          <article className="fixture-card">
            <div className="fixture-date"><span>PRÓXIMO COMPROMISSO</span><strong>—</strong><small>Data a confirmar</small></div>
            <div className="fixture-match"><div><span className="crest-placeholder">?</span><b>Seu clube</b><small>MANDANTE / —</small></div><div className="versus">VS</div><div><span className="crest-placeholder away">?</span><b>Adversário</b><small>VISITANTE / —</small></div></div>
            <div className="fixture-note"><CalendarDays size={15} /><span>O próximo compromisso virá do calendário oficial.</span></div>
          </article>
          <div className="section-heading news-heading"><div><span className="eyebrow">SINAL DO MUNDO</span><h2>Feed de notícias</h2></div><button className="filter-btn" onClick={() => toast("Filtros serão alimentados pelos acontecimentos do clube.")}><SlidersHorizontal size={15} /> Filtrar</button></div>
          <div className="news-list">{events.map((event) => <EventCard key={event.type} {...event} />)}</div>
        </div>
        <aside className="side-column">
          <div className="section-heading compact"><div><span className="eyebrow">SITUAÇÃO ATUAL</span><h2>Seu clube</h2></div><button className="more-btn" aria-label="Mais opções" onClick={() => toast("O retrato do clube virá do estado oficial.")}>···</button></div>
          <article className="club-card"><div className="club-card-top"><span className="crest-large">?</span><div><span className="eyebrow">CLUBE CONTROLADO</span><h3>Não conectado</h3><p>Selecione um estado de carreira</p></div></div><div className="club-lines"><div><span>ESTÁDIO</span><b>—</b></div><div><span>CT</span><b>—</b></div><div><span>TORCIDA</span><b>—</b></div></div><button className="secondary-action" onClick={() => onSectionChange("estadio")}>Ver estruturas <ChevronRight size={15} /></button></article>
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
    <div className="detail-grid">
      <article className="detail-panel"><div className="section-heading compact"><div><span className="eyebrow">{isTeam ? "CATEGORIAS" : isStadium ? "QUATRO CAMADAS" : isCt ? "EIXOS" : "PAINEL"}</span><h2>{isTeam ? "Estado do elenco" : isStadium ? "Estrutura do estádio" : isCt ? "Ciclo de desenvolvimento" : "Estado do mercado"}</h2></div><Gauge size={18} /></div>{isTeam ? rosterRows.map((row) => <div className="roster-row" key={row.position}><span className="roster-number">{row.number}</span><div><b>{row.name}</b><small>{row.position}</small></div><span className="muted-status">{row.status}</span><ChevronRight size={15} /></div>) : <div className="layer-list">{(isStadium ? ["Arquibancada", "Campo", "Estrutura", "Equipes"] : isCt ? ["Comissão", "Treinamento", "Recuperação", "Desenvolvimento"] : ["Janela", "Propostas", "Scouting", "Histórico"]).map((item, i) => <div className="layer-row" key={item}><span>0{i + 1}</span><b>{item}</b><em>indisponível</em><ChevronRight size={15} /></div>)}</div>}<button className="outline-action" onClick={() => toast("Esta ação será habilitada quando o serviço correspondente estiver conectado.")}>Consultar estado <ArrowUpRight size={15} /></button></article>
      <aside className="detail-side"><div className="empty-panel"><span className="empty-mark">—</span><span className="eyebrow">ESTADO NÃO CONECTADO</span><h3>Sem dados inventados.</h3><p>Esta tela já está preparada para os serviços do motor, mas ainda não substitui o GameState por uma cópia local.</p><button className="primary-action dark" onClick={() => onSectionChange("inicio")}>Voltar ao comando <ArrowUpRight size={16} /></button></div></aside>
    </div>
  </>;
}

export default function Home({ section = "inicio", onSectionChange = () => undefined }: { section?: AppSection; onSectionChange?: (section: AppSection) => void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const main = useMemo(() => section === "inicio" ? <Dashboard onSectionChange={onSectionChange} /> : <StructurePage section={section} onSectionChange={onSectionChange} />, [section, onSectionChange]);
  return <div className="app-shell"><Sidebar section={section} onSectionChange={onSectionChange} open={menuOpen} onClose={() => setMenuOpen(false)} /><main className="app-main"><Header section={section} onMenu={() => setMenuOpen(true)} /><div className="page-wrap">{main}</div><footer className="page-footer"><span>FUTMANAGER / EDITORIAL DE ARQUIBANCADA</span><span>SQL · STATE · SERVICES</span></footer></main></div>;
}
