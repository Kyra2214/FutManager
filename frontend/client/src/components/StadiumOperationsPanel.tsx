import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import { trpc } from "@/lib/trpc";
import { Building2, CircleDollarSign, Gauge, Landmark, Sparkles, Users } from "lucide-react";

const componentLabels = {
  arquibancada: "Arquibancada",
  campo: "Campo",
  estrutura: "Estrutura",
  equipes: "Equipes",
} as const;

function formatCash(value: number | null | undefined) {
  return value === null || value === undefined ? "—" : new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(value);
}

export function StadiumOperationsPanel() {
  const utils = trpc.useUtils();
  const summaryQuery = trpc.stadium.summary.useQuery(undefined, { retry: 1 });
  const summary = summaryQuery.data;
  const [ticketPrice, setTicketPrice] = useState("35");
  const [previewComponent, setPreviewComponent] = useState<keyof typeof componentLabels | null>(null);
  const previewQuery = trpc.stadium.preview.useQuery(previewComponent ? { component: previewComponent } : { component: "campo" }, { enabled: Boolean(previewComponent), retry: 1 });

  useEffect(() => {
    if (summary?.ticket_price) setTicketPrice(String(summary.ticket_price));
  }, [summary?.ticket_price]);

  const refresh = async () => {
    await Promise.all([
      utils.stadium.summary.invalidate(),
      utils.club.workspace.invalidate(),
      utils.sponsorship.summary.invalidate(),
    ]);
  };
  const bootstrap = trpc.stadium.bootstrap.useMutation({
    onSuccess: async () => { await refresh(); toast.success("Estádio registrado no estado do motor."); },
    onError: (error) => toast.error(error.message),
  });
  const upgrade = trpc.stadium.upgrade.useMutation({
    onSuccess: async () => { await refresh(); toast.success("Evolução registrada no ledger do clube."); },
    onError: (error) => toast.error(error.message),
  });
  const savePrice = trpc.stadium.ticketPrice.useMutation({
    onSuccess: async () => { await refresh(); toast.success("Preço-base de ingresso atualizado."); },
    onError: (error) => toast.error(error.message),
  });
  const advance = trpc.stadium.advanceWeek.useMutation({
    onSuccess: async (result) => {
      await Promise.all([refresh(), utils.matches.dashboard.invalidate(), utils.staffMarket.summary.invalidate(), utils.sponsorship.offers.invalidate()]);
      toast.success(result.status === "ALREADY_PROCESSED" ? "A semana solicitada já estava processada." : `Semana ${result.week} processada: ${result.matches ?? 0} partida(s).`);
    },
    onError: (error) => toast.error(error.message),
  });

  if (summaryQuery.isLoading) return <section className="stadium-operations loading"><span className="eyebrow">ESTÁDIO / MOTOR</span><h2>Lendo operação de dia de jogo…</h2></section>;
  if (summaryQuery.error) return <section className="stadium-operations error"><span className="eyebrow">ESTÁDIO / ESTADO INDISPONÍVEL</span><h2>Não foi possível ler a operação do estádio.</h2><p>{summaryQuery.error.message}</p></section>;
  if (!summary?.initialized || !summary.stadium) {
    return <section className="stadium-operations empty"><div><span className="eyebrow">ESTÁDIO / AÇÃO NECESSÁRIA</span><h2>O estádio ainda não foi preparado para a gestão.</h2><p>O clube possui identidade de estádio no SQL, mas os quatro componentes econômicos precisam ser registrados explicitamente antes de gerar público, preço e receita.</p></div><button className="primary-action" onClick={() => bootstrap.mutate()} disabled={bootstrap.isPending}><Landmark size={16} />{bootstrap.isPending ? "Registrando…" : "Preparar estádio"}</button></section>;
  }

  const { stadium, fan_base: fans, reputation, attendance } = summary;
  return <section className="stadium-operations">
    <div className="stadium-operations-head"><div><span className="eyebrow">ESTÁDIO / OPERAÇÃO PERSISTIDA</span><h2>{stadium.name}</h2><p>Arquibancada, campo, estrutura e equipes evoluem separadamente. O público e a bilheteria são calculados somente quando uma partida real for processada.</p></div><button className="advance-week" onClick={() => advance.mutate({})} disabled={advance.isPending}>{advance.isPending ? "Processando semana…" : "Avançar uma semana"}<Sparkles size={16} /></button></div>
    <div className="stadium-metrics"><article><Landmark size={18} /><span>CAPACIDADE</span><b>{stadium.capacity.toLocaleString("pt-BR")}</b><small>base {stadium.base_capacity.toLocaleString("pt-BR")}</small></article><article><Gauge size={18} /><span>QUALIDADE DE JOGO</span><b>{stadium.matchday_quality.toFixed(0)}</b><small>campo · estrutura · equipes</small></article><article><CircleDollarSign size={18} /><span>MANUTENÇÃO / SEMANA</span><b>{formatCash(stadium.maintenance)}</b><small>quatro componentes</small></article><article><Users size={18} /><span>TORCIDA</span><b>{fans?.size?.toLocaleString("pt-BR") ?? "—"}</b><small>{fans ? `satisfação ${fans.satisfaction}` : "sem base registrada"}</small></article></div>
    <div className="stadium-grid"><article className="stadium-components"><div className="section-heading compact"><div><span className="eyebrow">PLANO DE EVOLUÇÃO</span><h3>Quatro frentes</h3></div><Building2 size={18} /></div>{stadium.components.map((component) => <div className="stadium-component" key={component.component}><div><span>NÍVEL {component.level}/10</span><b>{componentLabels[component.component]}</b><small>manutenção {formatCash(component.maintenance)}/semana</small></div>{component.next_level ? <button onClick={() => setPreviewComponent(component.component)} disabled={upgrade.isPending}>{previewComponent === component.component ? "Prévia aberta" : `Ver impacto · ${formatCash(component.upgrade_cost)}`}</button> : <em>Nível máximo</em>}{previewComponent === component.component && previewQuery.data && <div className="stadium-preview"><small>PRÉVIA · {previewQuery.data.from_level} → {previewQuery.data.target_level}</small><b>Caixa após: {formatCash(previewQuery.data.cash_after)}</b><span>Manutenção: {formatCash(previewQuery.data.maintenance_before)} → {formatCash(previewQuery.data.maintenance_after)}</span><button className="outline-action" onClick={() => upgrade.mutate({ component: component.component })} disabled={upgrade.isPending || !previewQuery.data.cash_sufficient}>{upgrade.isPending ? "Registrando…" : previewQuery.data.cash_sufficient ? "Confirmar evolução" : "Caixa insuficiente"}</button></div>}</div>)}</article><aside className="ticket-control"><span className="eyebrow">BILHETERIA</span><h3>Preço-base</h3><p>O motor ajusta o preço efetivo por importância e demanda na data de cada partida.</p><label><span>R$</span><input aria-label="Preço-base do ingresso" inputMode="numeric" value={ticketPrice} onChange={(event) => setTicketPrice(event.target.value.replace(/\D/g, ""))} /></label><button className="outline-action" onClick={() => savePrice.mutate({ basePrice: Number(ticketPrice) })} disabled={savePrice.isPending || Number(ticketPrice) < 1}>{savePrice.isPending ? "Salvando…" : "Salvar preço"}</button><div className="reputation-lines"><div><span>REPUTAÇÃO ESPORTIVA</span><b>{reputation?.sporting ?? "—"}</b></div><div><span>REPUTAÇÃO COMERCIAL</span><b>{reputation?.commercial ?? "—"}</b></div></div></aside></div>
    <div className="attendance-strip"><div><span className="eyebrow">ÚLTIMOS JOGOS EM CASA</span><h3>{attendance.length ? "Público e receita persistidos" : "Ainda não há bilheteria registrada"}</h3></div>{attendance.length ? <div className="attendance-list">{attendance.slice(0, 4).map((item) => <div key={item.match_id}><b>{item.actual_attendance.toLocaleString("pt-BR")}</b><span>{formatCash(item.revenue)}</span><small>ingresso {formatCash(item.ticket_price)}</small></div>)}</div> : <p>O primeiro registro será criado quando o ciclo semanal processar uma partida do clube como mandante.</p>}</div>
  </section>;
}
