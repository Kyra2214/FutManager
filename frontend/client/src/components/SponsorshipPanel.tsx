import React from "react";
import { BadgeDollarSign, Building2, CircleCheck, CircleDashed, Clock3, Sparkles, Star, Target, Trophy } from "lucide-react";
import { toast } from "sonner";
import { trpc } from "@/lib/trpc";
import { useFeedback } from "@/contexts/FeedbackContext";

function formatCash(value: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(value);
}

function Stars({ value, label }: { value: number; label: string }) {
  return <span className="sponsor-stars" aria-label={`${value} de 5 estrelas: ${label}`}>{Array.from({ length: 5 }, (_, index) => <Star key={index} size={14} fill={index < value ? "currentColor" : "none"} className={index < value ? "is-on" : ""} />)}</span>;
}

function ScoreLine({ label, score, available, weight }: { label: string; score: number; available: boolean; weight: string }) {
  return <div className="institution-line"><div><b>{label}</b><small>{weight} do overall</small></div><strong>{score.toFixed(1)}</strong><span className={available ? "institution-state is-ready" : "institution-state"}>{available ? "medido" : "base preparatória"}</span></div>;
}

export function SponsorshipPanel() {
  const summaryQuery = trpc.sponsorship.summary.useQuery(undefined, { retry: 1 });
  const utils = trpc.useUtils();
  const { notify } = useFeedback();
  const acceptMutation = trpc.sponsorship.accept.useMutation({
    onSuccess: async (contract) => {
      toast.success(`${contract.sponsor} entrou no projeto. Sinal de ${formatCash(contract.upfront_payment)} registrado.`);
      notify("success");
      await Promise.all([
        utils.sponsorship.summary.invalidate(),
        utils.sponsorship.offers.invalidate(),
        utils.club.workspace.invalidate(),
        utils.staffMarket.summary.invalidate(),
      ]);
    },
    onError: (error) => { toast.error(error.message === "SPONSOR_REQUIREMENT_NOT_MET" ? "O overall institucional atual não atende à exigência da proposta." : "Não foi possível formalizar esse patrocínio."); notify("error"); },
  });
  const summary = summaryQuery.data;

  if (summaryQuery.isLoading) return <section className="sponsorship-panel sponsor-loading"><CircleDashed size={22} /><div><span className="eyebrow">MERCADO COMERCIAL</span><h2>Lendo propostas persistidas…</h2><p>O motor está consultando contratos, overall institucional e missões.</p></div></section>;
  if (summaryQuery.error || !summary) return <section className="sponsorship-panel sponsor-loading"><BadgeDollarSign size={22} /><div><span className="eyebrow">MERCADO COMERCIAL</span><h2>Patrocínios indisponíveis.</h2><p>O estado comercial não pôde ser consultado agora. Nenhum contrato foi alterado.</p></div></section>;

  const { institutional_profile: profile } = summary;
  const active = summary.active_contract;
  return <section className="sponsorship-panel" aria-label="Patrocínios e missões comerciais">
    <div className="sponsor-command-header"><div><span className="eyebrow">MERCADO COMERCIAL / ESTADO PERSISTIDO</span><h2>Valor que o clube<br /><em>constrói fora do campo.</em></h2><p>As propostas expiram após três semanas sem decisão. Uma nova janela pode trazer marcas de estrela melhor ou pior, conforme o overall institucional e a rotação do mercado.</p></div><div className="overall-seal"><span>OVERALL</span><strong>{summary.institutional_overall.toFixed(1)}</strong><Stars value={summary.sponsor_stars} label="qualidade elegível de patrocínio" /><small>{summary.sponsor_stars} de 5 estrelas elegíveis</small></div></div>

    <div className="institution-grid"><ScoreLine label="Elenco" score={profile.squad_score} available={profile.squad_available} weight="60%" /><ScoreLine label="Centro de treinamento" score={profile.ct_score} available={profile.ct_available} weight="25%" /><ScoreLine label="Estádio" score={profile.stadium_score} available={profile.stadium_available} weight="15%" /></div>

    {active ? <article className="active-sponsor"><div className="active-sponsor-mark"><Building2 size={23} /></div><div><span className="eyebrow">PATROCINADOR PRINCIPAL ATIVO</span><h3>{active.name}</h3><p>{active.industry} · ciclo até a semana {active.end_week} de {active.end_season}</p></div><div className="active-sponsor-values"><div><span>RECEITA SEMANAL</span><b>{formatCash(active.weekly_payment)}</b></div><div><span>BÔNUS DE MISSÃO</span><b>{formatCash(active.mission_bonus)}</b></div></div></article> : <section className="sponsor-offer-section"><div className="section-heading compact"><div><span className="eyebrow">JANELA DE PROPOSTAS</span><h2>Escolha um parceiro.</h2></div><span className="offer-window"><Clock3 size={15} /> expira na semana {summary.offers[0]?.expires_week ?? "—"}</span></div><div className="sponsor-offers">{summary.offers.length ? summary.offers.map((offer) => <article className="sponsor-offer" key={offer.offer_id}><div className="offer-top"><div><span className="eyebrow">{offer.industry}</span><h3>{offer.name}</h3></div><Stars value={offer.star_rating} label={`proposta ${offer.name}`} /></div><div className="offer-values"><div><span>SINAL</span><b>{formatCash(offer.upfront_payment)}</b></div><div><span>POR SEMANA</span><b>{formatCash(offer.weekly_payment)}</b></div><div><span>MISSÃO</span><b>{formatCash(offer.mission_bonus)}</b></div></div><div className="offer-requirement"><Sparkles size={15} /><span>Exige overall {offer.minimum_overall.toFixed(0)} · atual {summary.institutional_overall.toFixed(1)}</span></div><button className="sponsor-accept" onClick={() => acceptMutation.mutate({ offerId: offer.offer_id })} disabled={acceptMutation.isPending || summary.institutional_overall < offer.minimum_overall}>{acceptMutation.isPending ? "Formalizando…" : "Escolher patrocinador"}<Trophy size={15} /></button></article>) : <div className="sponsor-empty">Não há proposta ativa. O motor abrirá a próxima janela no ciclo comercial.</div>}</div></section>}

    <section className="sponsor-missions"><div className="section-heading compact"><div><span className="eyebrow">MISSÕES COMERCIAIS</span><h2>Entregue valor ao parceiro.</h2></div><Target size={18} /></div>{summary.missions.length ? <div className="mission-list">{summary.missions.map((mission) => { const progress = Math.min(100, mission.target_value > 0 ? mission.current_value / mission.target_value * 100 : 100); return <article className="sponsor-mission" key={mission.mission_id}><div className="mission-status">{mission.status === "COMPLETED" ? <CircleCheck size={18} /> : <Target size={18} />}</div><div><b>{mission.title}</b><small>Meta {mission.target_value.toFixed(1)} · atual {mission.current_value.toFixed(1)} · prazo: semana {mission.deadline_week}/{mission.deadline_season}</small><div className="mission-progress"><span style={{ width: `${progress}%` }} /></div></div><strong>{mission.status === "ACTIVE" ? formatCash(mission.reward) : mission.status === "COMPLETED" ? "CONCLUÍDA" : "ENCERRADA"}</strong></article>; })}</div> : <div className="sponsor-empty">Assine uma proposta para receber uma missão comercial persistida, com prazo e bônus próprio.</div>}</section>
  </section>;
}
