import React, { useMemo, useState } from "react";
import { toast } from "sonner";
import { Archive, BarChart3, CheckCircle2, GitCompareArrows, Play, RefreshCw, ShieldCheck, Undo2 } from "lucide-react";
import { trpc } from "@/lib/trpc";
import { useAuth } from "@/_core/hooks/useAuth";

type SnapshotRow = { snapshot_id: number; career_id: number; created_at: string; engine_version: string };
type SnapshotAuditRow = { audit_id: number; snapshot_id: number; action: string; created_at: string };
type FinanceCategoryRow = { category: string; net: number; entries: number };
type RestoreField = "current_club_id" | "season_id" | "status" | "name";

const RESTORE_FIELDS: Array<{ key: RestoreField; label: string; description: string }> = [
  { key: "current_club_id", label: "Clube atual", description: "Entidade controlada pelo manager" },
  { key: "season_id", label: "Temporada", description: "Temporada persistida da carreira" },
  { key: "status", label: "Status", description: "Estado ativo ou pausado" },
  { key: "name", label: "Nome da carreira", description: "Identidade deste save" },
];

function PanelCard({ title, eyebrow, children }: { title: string; eyebrow: string; children: React.ReactNode }) {
  return <article className="detail-panel operations-card"><div className="section-heading compact"><div><span className="eyebrow">{eyebrow}</span><h2>{title}</h2></div><ShieldCheck size={18} /></div>{children}</article>;
}

function SnapshotValue({ label, value }: { label: string; value: string | number | boolean | undefined }) {
  return <div className="snapshot-value"><span>{label}</span><b>{value === undefined ? "—" : String(value)}</b></div>;
}

export function OperationsPanel() {
  const auth = useAuth();
  const [tickId, setTickId] = useState("season-2027-week-01");
  const [season, setSeason] = useState("2027");
  const [month, setMonth] = useState("1");
  const [snapshotId, setSnapshotId] = useState<number | null>(null);
  const [leftSnapshotId, setLeftSnapshotId] = useState<number | null>(null);
  const [rightSnapshotId, setRightSnapshotId] = useState<number | null>(null);
  const [restoreFields, setRestoreFields] = useState<RestoreField[]>(["current_club_id"]);
  const [restoreConfirm, setRestoreConfirm] = useState(false);
  const utils = trpc.useUtils();
  const current = trpc.career.current.useQuery(undefined, { retry: 1 });
  const started = current.data?.started;
  const canOperate = auth.isAuthenticated && Boolean(started);
  const snapshots = trpc.operations.snapshots.list.useQuery(undefined, { retry: 1, enabled: canOperate });
  const audit = trpc.operations.snapshots.audit.useQuery(undefined, { retry: 1, enabled: canOperate });
  const compareInput = useMemo(() => ({ leftId: leftSnapshotId ?? 1, rightId: rightSnapshotId ?? 1 }), [leftSnapshotId, rightSnapshotId]);
  const compare = trpc.operations.snapshots.compare.useQuery(compareInput, { retry: 1, enabled: canOperate && Boolean(leftSnapshotId && rightSnapshotId) });
  const progress = trpc.operations.simulation.progress.useQuery({ tickId }, { retry: 1, enabled: canOperate && tickId.trim().length > 0 });
  const metrics = trpc.operations.simulation.metrics.useQuery({ tickId }, { retry: 1, enabled: canOperate && tickId.trim().length > 0 });
  const close = trpc.operations.finance.monthlyClose.useQuery({ season: Number(season) || 2027, month: Number(month) || 1 }, { retry: 1, enabled: canOperate });
  const createSnapshot = trpc.operations.snapshots.create.useMutation({ onSuccess: (data) => { setSnapshotId(data.snapshot_id); utils.operations.snapshots.list.invalidate(); utils.operations.snapshots.audit.invalidate(); toast("Checkpoint de carreira persistido no GameState."); }, onError: (error) => toast(error.message) });
  const restoreSnapshot = trpc.operations.snapshots.restore.useMutation({ onSuccess: () => { setRestoreConfirm(false); utils.career.current.invalidate(); utils.operations.snapshots.audit.invalidate(); toast("Restauração seletiva confirmada pelo motor."); }, onError: (error) => toast(error.message) });
  const runBatch = trpc.operations.simulation.batch.useMutation({ onSuccess: () => { utils.operations.simulation.progress.invalidate(); utils.operations.simulation.metrics.invalidate(); toast("Lote de simulação processado pelo motor."); }, onError: (error) => toast(error.message) });
  const resume = trpc.operations.simulation.resume.useMutation({ onSuccess: () => { utils.operations.simulation.progress.invalidate(); utils.operations.simulation.metrics.invalidate(); toast("Retomada concluída pelo motor."); }, onError: (error) => toast(error.message) });
  const refreshFinance = () => { utils.operations.finance.monthlyClose.invalidate(); toast("Relatório mensal atualizado a partir do ledger."); };
  const snapshotRows = useMemo(() => (snapshots.data?.items ?? []) as SnapshotRow[], [snapshots.data?.items]);
  const auditRows = useMemo(() => (audit.data?.items ?? []) as SnapshotAuditRow[], [audit.data?.items]);
  const leftSnapshot = snapshotRows.find((row) => row.snapshot_id === leftSnapshotId);
  const rightSnapshot = snapshotRows.find((row) => row.snapshot_id === rightSnapshotId);
  const selectedRestoreSnapshot = rightSnapshotId ?? leftSnapshotId;

  const toggleRestoreField = (field: RestoreField) => setRestoreFields((currentFields) => currentFields.includes(field) ? currentFields.filter((item) => item !== field) : [...currentFields, field]);

  return <section className="operations-page">
    <div className="page-intro"><div><span className="eyebrow">FUTMANAGER / OPERAÇÕES</span><h1>Estado, simulação e caixa.</h1><p>Três painéis de controle que leem o motor Python e não recalculam regras no navegador.</p></div><span className="page-code">OP-01</span></div>
    {!started && <div className="fixture-empty">Inicie uma carreira para consultar operações protegidas do manager.</div>}
    <div className="detail-grid operations-grid">
      <PanelCard eyebrow="CARREIRA / CHECKPOINTS" title="Snapshots de carreira">
        <p className="operations-note">Snapshots registram a carreira ativa. Comparações são somente leitura; restaurações passam por confirmação e pelo contrato do motor.</p>
        <div className="operations-actions"><button className="primary-action compact-action" disabled={!canOperate || createSnapshot.isPending} onClick={() => createSnapshot.mutate()}><Archive size={15} />{createSnapshot.isPending ? "Salvando…" : "Criar snapshot"}</button>{snapshotId && <span className="operations-status"><CheckCircle2 size={15} /> Snapshot #{snapshotId}</span>}</div>
        {snapshots.isLoading ? <div className="entity-lookup-empty">Lendo checkpoints persistidos…</div> : snapshotRows.length ? <div className="snapshot-picker"><div className="snapshot-picker-head"><span>COMPARAÇÃO LADO A LADO</span><small>Selecione dois checkpoints</small></div>{snapshotRows.slice(0, 8).map((row) => <div className="snapshot-picker-row" key={row.snapshot_id}><div><b>#{row.snapshot_id}</b><small>{row.created_at} · {row.engine_version}</small></div><label><input type="radio" name="snapshot-left" checked={leftSnapshotId === row.snapshot_id} onChange={() => setLeftSnapshotId(row.snapshot_id)} /> A</label><label><input type="radio" name="snapshot-right" checked={rightSnapshotId === row.snapshot_id} onChange={() => setRightSnapshotId(row.snapshot_id)} /> B</label></div>)}</div> : <div className="entity-lookup-empty">Nenhum snapshot persistido para esta carreira.</div>}
        {compare.data && <div className="snapshot-compare" aria-live="polite"><div className="snapshot-compare-heading"><GitCompareArrows size={16} /><b>Comparação somente leitura</b><span>{compare.data.identical ? "Estados idênticos" : "Estados diferentes"}</span></div><div className="snapshot-columns"><div><strong>Snapshot #{compare.data.left_id}</strong><SnapshotValue label="Hash" value={compare.data.left_hash.slice(0, 16) + "…"} /><SnapshotValue label="Mesma carreira" value={compare.data.same_career ? "Sim" : "Não"} /></div><div><strong>Snapshot #{compare.data.right_id}</strong><SnapshotValue label="Hash" value={compare.data.right_hash.slice(0, 16) + "…"} /><SnapshotValue label="Somente leitura" value={compare.data.read_only ? "Sim" : "Não"} /></div></div></div>}
        {selectedRestoreSnapshot && <div className="snapshot-restore"><div className="snapshot-picker-head"><span>RESTAURAÇÃO SELETIVA</span><small>Destino: snapshot #{selectedRestoreSnapshot}</small></div><div className="restore-field-list">{RESTORE_FIELDS.map((field) => <label key={field.key} className="restore-field"><input type="checkbox" checked={restoreFields.includes(field.key)} onChange={() => toggleRestoreField(field.key)} /><span><b>{field.label}</b><small>{field.description}</small></span></label>)}</div><button className="outline-action" disabled={!canOperate || restoreFields.length === 0 || restoreSnapshot.isPending} onClick={() => setRestoreConfirm(true)}><Undo2 size={15} />Preparar restauração</button>{restoreConfirm && <div className="restore-confirm" role="alertdialog" aria-label="Confirmar restauração seletiva"><strong>Confirmar mutação no GameState?</strong><p>Serão restaurados {restoreFields.length} campo(s) do snapshot #{selectedRestoreSnapshot}. Esta ação será auditada.</p><div className="operations-actions"><button className="primary-action compact-action" disabled={restoreSnapshot.isPending} onClick={() => restoreSnapshot.mutate({ snapshotId: selectedRestoreSnapshot, fields: restoreFields })}>Confirmar restauração</button><button className="outline-action" onClick={() => setRestoreConfirm(false)}>Cancelar</button></div></div>}</div>}
        {audit.isLoading ? <div className="entity-lookup-empty">Lendo auditoria de recuperação…</div> : auditRows.length ? <div className="operations-list">{auditRows.slice(-6).map((row) => <div className="layer-row" key={row.audit_id}><span>#{row.snapshot_id}</span><b>{row.action}</b><em>{row.created_at}</em></div>)}</div> : <div className="entity-lookup-empty">Nenhuma restauração auditada para esta carreira.</div>}
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
