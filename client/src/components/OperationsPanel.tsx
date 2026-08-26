import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Archive, BarChart3, CheckCircle2, Play, RefreshCw, ShieldCheck } from "lucide-react";
import { trpc } from "@/lib/trpc";
import { useAuth } from "@/_core/hooks/useAuth";

type SnapshotAuditRow = { audit_id: number; snapshot_id: number; action: string; created_at: string };
type FinanceCategoryRow = { category: string; net: number; entries: number };

function PanelCard({ title, eyebrow, children }: { title: string; eyebrow: string; children: React.ReactNode }) {
  return <article className="detail-panel operations-card"><div className="section-heading compact"><div><span className="eyebrow">{eyebrow}</span><h2>{title}</h2></div><ShieldCheck size={18} /></div>{children}</article>;
}

export function OperationsPanel() {
  const auth = useAuth();
  const [tickId, setTickId] = useState("season-2027-week-01");
  const [season, setSeason] = useState("2027");
  const [month, setMonth] = useState("1");
  const [snapshotId, setSnapshotId] = useState<number | null>(null);
  const utils = trpc.useUtils();
  const current = trpc.career.current.useQuery(undefined, { retry: 1 });
  const audit = trpc.operations.snapshots.audit.useQuery(undefined, { retry: 1, enabled: auth.isAuthenticated });
  const progress = trpc.operations.simulation.progress.useQuery({ tickId }, { retry: 1, enabled: auth.isAuthenticated && Boolean(current.data?.started) && tickId.trim().length > 0 });
  const metrics = trpc.operations.simulation.metrics.useQuery({ tickId }, { retry: 1, enabled: auth.isAuthenticated && Boolean(current.data?.started) && tickId.trim().length > 0 });
  const close = trpc.operations.finance.monthlyClose.useQuery({ season: Number(season) || 2027, month: Number(month) || 1 }, { retry: 1, enabled: auth.isAuthenticated && Boolean(current.data?.started) });
  const createSnapshot = trpc.operations.snapshots.create.useMutation({ onSuccess: (data) => { setSnapshotId(data.snapshot_id); utils.operations.snapshots.audit.invalidate(); toast("Checkpoint de carreira persistido no GameState."); }, onError: (error) => toast(error.message) });
  const runBatch = trpc.operations.simulation.batch.useMutation({ onSuccess: () => { utils.operations.simulation.progress.invalidate(); utils.operations.simulation.metrics.invalidate(); toast("Lote de simulação processado pelo motor."); }, onError: (error) => toast(error.message) });
  const resume = trpc.operations.simulation.resume.useMutation({ onSuccess: () => { utils.operations.simulation.progress.invalidate(); utils.operations.simulation.metrics.invalidate(); toast("Retomada concluída pelo motor."); }, onError: (error) => toast(error.message) });
  const refreshFinance = () => { utils.operations.finance.monthlyClose.invalidate(); toast("Relatório mensal atualizado a partir do ledger."); };
  const snapshotRows = useMemo(() => (audit.data?.items ?? []) as SnapshotAuditRow[], [audit.data?.items]);
  const started = current.data?.started;
  const canOperate = auth.isAuthenticated && Boolean(started);
  return <section className="operations-page">
    <div className="page-intro"><div><span className="eyebrow">FUTMANAGER / OPERAÇÕES</span><h1>Estado, simulação e caixa.</h1><p>Três painéis de controle que leem o motor Python e não recalculam regras no navegador.</p></div><span className="page-code">OP-01</span></div>
    {!started && <div className="fixture-empty">Inicie uma carreira para consultar operações protegidas do manager.</div>}
    <div className="detail-grid operations-grid">
      <PanelCard eyebrow="CARREIRA / CHECKPOINTS" title="Snapshots de carreira">
        <p className="operations-note">Snapshots registram a carreira ativa; restaurações seletivas permanecem sujeitas ao contrato do motor.</p>
        <div className="operations-actions"><button className="primary-action compact-action" disabled={!canOperate || createSnapshot.isPending} onClick={() => createSnapshot.mutate()}><Archive size={15} />{createSnapshot.isPending ? "Salvando…" : "Criar snapshot"}</button>{snapshotId && <span className="operations-status"><CheckCircle2 size={15} /> Snapshot #{snapshotId}</span>}</div>
        {audit.isLoading ? <div className="entity-lookup-empty">Lendo auditoria de recuperação…</div> : snapshotRows.length ? <div className="operations-list">{snapshotRows.slice(-6).map((row) => <div className="layer-row" key={row.audit_id}><span>#{row.snapshot_id}</span><b>{row.action}</b><em>{row.created_at}</em></div>)}</div> : <div className="entity-lookup-empty">Nenhuma restauração auditada para esta carreira.</div>}
      </PanelCard>
      <PanelCard eyebrow="MUNDO / FILA" title="Simulação mundial">
        <label className="operations-field">Identificador do lote<input value={tickId} onChange={(event) => setTickId(event.target.value)} /></label>
        <div className="operations-actions"><button className="primary-action compact-action" disabled={!canOperate || runBatch.isPending} onClick={() => runBatch.mutate({ tickId, level: "ABSTRACT", batchSize: 100, seed: 0 })}><Play size={15} />Processar lote</button><button className="outline-action" disabled={!canOperate || resume.isPending} onClick={() => resume.mutate({ tickId, level: "ABSTRACT", batchSize: 100, seed: 0 })}><RefreshCw size={15} />Retomar</button></div>
        {progress.error ? <div className="fixture-empty">O lote ainda não possui checkpoint persistido.</div> : <div className="operations-list"><div className="layer-row"><span>STATUS</span><b>{progress.data?.status ?? "—"}</b><em>{progress.data?.processed ?? 0} processado(s)</em></div><div className="layer-row"><span>MÉTRICAS</span><b>{metrics.data?.throughput_estimate ?? 0} transação(ões)</b><em>{metrics.data?.checkpoints ?? 0} checkpoint(s)</em></div></div>}
      </PanelCard>
      <PanelCard eyebrow="FINANCELEDGER / FECHAMENTO" title="Auditoria financeira">
        <div className="operations-fields"><label className="operations-field">Temporada<input value={season} onChange={(event) => setSeason(event.target.value.replace(/\D/g, ""))} inputMode="numeric" /></label><label className="operations-field">Mês<input value={month} onChange={(event) => setMonth(event.target.value.replace(/\D/g, ""))} inputMode="numeric" /></label></div>
        <button className="outline-action" onClick={refreshFinance}><BarChart3 size={15} />Atualizar fechamento</button>
        {close.error ? <div className="fixture-empty">Fechamento indisponível para esta temporada.</div> : <div className="operations-list"><div className="layer-row"><span>NET</span><b>{close.data?.net ?? "—"}</b><em>fechamento persistido</em></div>{(close.data?.categories as FinanceCategoryRow[] | undefined)?.slice(0, 6).map((row) => <div className="layer-row" key={row.category}><span>{row.category}</span><b>{row.net}</b><em>{row.entries} lançamento(s)</em></div>)}</div>}
      </PanelCard>
    </div>
  </section>;
}
