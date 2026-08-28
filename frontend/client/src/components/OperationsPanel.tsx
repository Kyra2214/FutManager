import React, { useMemo, useState } from "react";
import { toast } from "sonner";
import { Archive, BarChart3, CheckCircle2, GitCompareArrows, ShieldCheck, Undo2 } from "lucide-react";
import { trpc } from "@/lib/trpc";
import { useAuth } from "@/_core/hooks/useAuth";
import { useFeedback } from "@/contexts/FeedbackContext";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";

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
  const [season, setSeason] = useState("2027");
  const [month, setMonth] = useState("1");
  const [snapshotId, setSnapshotId] = useState<number | null>(null);
  const [leftSnapshotId, setLeftSnapshotId] = useState<number | null>(null);
  const [rightSnapshotId, setRightSnapshotId] = useState<number | null>(null);
  const [restoreFields, setRestoreFields] = useState<RestoreField[]>(["current_club_id"]);
  const [restoreConfirm, setRestoreConfirm] = useState(false);
  const utils = trpc.useUtils();
  const { notify } = useFeedback();
  const current = trpc.career.current.useQuery(undefined, { retry: 1 });
  const started = current.data?.started;
  const canOperate = auth.isAuthenticated && Boolean(started);
  const snapshots = trpc.operations.snapshots.list.useQuery(undefined, { retry: 1, enabled: canOperate });
  const audit = trpc.operations.snapshots.audit.useQuery(undefined, { retry: 1, enabled: canOperate });
  const compareInput = useMemo(() => ({ leftId: leftSnapshotId ?? 1, rightId: rightSnapshotId ?? 1 }), [leftSnapshotId, rightSnapshotId]);
  const compare = trpc.operations.snapshots.compare.useQuery(compareInput, { retry: 1, enabled: canOperate && Boolean(leftSnapshotId && rightSnapshotId) });
  const close = trpc.operations.finance.monthlyClose.useQuery({ season: Number(season) || 2027, month: Number(month) || 1 }, { retry: 1, enabled: canOperate });
  const createSnapshot = trpc.operations.snapshots.create.useMutation({ onSuccess: (data) => { setSnapshotId(data.snapshot_id); utils.operations.snapshots.list.invalidate(); utils.operations.snapshots.audit.invalidate(); toast("Ponto de salvamento da carreira criado."); notify("success"); }, onError: (error) => { toast(error.message); notify("error"); } });
  const restoreSnapshot = trpc.operations.snapshots.restore.useMutation({ onSuccess: () => { setRestoreConfirm(false); utils.career.current.invalidate(); utils.operations.snapshots.audit.invalidate(); toast("Restauração seletiva confirmada pelo motor."); notify("success"); }, onError: (error) => { toast(error.message); notify("error"); } });
  const refreshFinance = () => { utils.operations.finance.monthlyClose.invalidate(); toast("Relatório mensal atualizado a partir do ledger."); };
  const snapshotRows = useMemo(() => (snapshots.data?.items ?? []) as SnapshotRow[], [snapshots.data?.items]);
  const auditRows = useMemo(() => (audit.data?.items ?? []) as SnapshotAuditRow[], [audit.data?.items]);
  const leftSnapshot = snapshotRows.find((row) => row.snapshot_id === leftSnapshotId);
  const rightSnapshot = snapshotRows.find((row) => row.snapshot_id === rightSnapshotId);
  const selectedRestoreSnapshot = rightSnapshotId ?? leftSnapshotId;

  const toggleRestoreField = (field: RestoreField) => setRestoreFields((currentFields) => currentFields.includes(field) ? currentFields.filter((item) => item !== field) : [...currentFields, field]);

  return <section className="operations-page">
    <div className="page-intro"><div><span className="eyebrow">FUTMANAGER / CARREIRA</span><h1>Operações da carreira.</h1><p>Salve, compare e acompanhe a situação financeira do seu clube com segurança.</p></div></div>
    {!started && <div className="fixture-empty">Inicie uma carreira para consultar operações protegidas do manager.</div>}
    <div className="detail-grid operations-grid">
      <PanelCard eyebrow="CARREIRA / CHECKPOINTS" title="Snapshots de carreira">
        <p className="operations-note">Os pontos de salvamento registram a carreira ativa. Comparações não alteram o jogo; restaurações sempre pedem confirmação.</p>
        <div className="operations-actions"><button className="primary-action compact-action" disabled={!canOperate || createSnapshot.isPending} onClick={() => createSnapshot.mutate()}><Archive size={15} />{createSnapshot.isPending ? "Salvando…" : "Criar snapshot"}</button>{snapshotId && <span className="operations-status"><CheckCircle2 size={15} /> Ponto de salvamento criado</span>}</div>
        {snapshots.isLoading ? <LoadingState label="Lendo checkpoints persistidos…" /> : snapshotRows.length ? <div className="snapshot-picker"><div className="snapshot-picker-head"><span>COMPARAR SALVAMENTOS</span><small>Selecione dois pontos para comparar</small></div>{snapshotRows.slice(0, 8).map((row) => <div className="snapshot-picker-row" key={row.snapshot_id}><div><b>#{row.snapshot_id}</b><small>{row.created_at} · {row.engine_version}</small></div><label><input type="radio" name="snapshot-left" checked={leftSnapshotId === row.snapshot_id} onChange={() => setLeftSnapshotId(row.snapshot_id)} /> A</label><label><input type="radio" name="snapshot-right" checked={rightSnapshotId === row.snapshot_id} onChange={() => setRightSnapshotId(row.snapshot_id)} /> B</label></div>)}</div> : <EmptyState icon={Archive} title="Nenhum snapshot persistido" description="Esta carreira ainda não tem checkpoints salvos." />}
        {compare.data && <div className="snapshot-compare" aria-live="polite"><div className="snapshot-compare-heading"><GitCompareArrows size={16} /><b>Comparação somente leitura</b><span>{compare.data.identical ? "Estados idênticos" : "Estados diferentes"}</span></div><div className="snapshot-columns"><div><strong>Snapshot #{compare.data.left_id}</strong><SnapshotValue label="Hash" value={compare.data.left_hash.slice(0, 16) + "…"} /><SnapshotValue label="Mesma carreira" value={compare.data.same_career ? "Sim" : "Não"} /></div><div><strong>Snapshot #{compare.data.right_id}</strong><SnapshotValue label="Hash" value={compare.data.right_hash.slice(0, 16) + "…"} /><SnapshotValue label="Somente leitura" value={compare.data.read_only ? "Sim" : "Não"} /></div></div></div>}
        {selectedRestoreSnapshot && <div className="snapshot-restore"><div className="snapshot-picker-head"><span>RESTAURAÇÃO SELETIVA</span><small>Destino: snapshot #{selectedRestoreSnapshot}</small></div><div className="restore-field-list">{RESTORE_FIELDS.map((field) => <label key={field.key} className="restore-field"><input type="checkbox" checked={restoreFields.includes(field.key)} onChange={() => toggleRestoreField(field.key)} /><span><b>{field.label}</b><small>{field.description}</small></span></label>)}</div><button className="outline-action" disabled={!canOperate || restoreFields.length === 0 || restoreSnapshot.isPending} onClick={() => setRestoreConfirm(true)}><Undo2 size={15} />Preparar restauração</button>{restoreConfirm && <div className="restore-confirm" role="alertdialog" aria-label="Confirmar restauração seletiva"><strong>Confirmar restauração?</strong><p>{restoreFields.length} informação(ões) serão restauradas. Esta ação ficará registrada.</p><div className="operations-actions"><button className="primary-action compact-action" disabled={restoreSnapshot.isPending} onClick={() => restoreSnapshot.mutate({ snapshotId: selectedRestoreSnapshot, fields: restoreFields })}>Confirmar restauração</button><button className="outline-action" onClick={() => setRestoreConfirm(false)}>Cancelar</button></div></div>}</div>}
        {audit.isLoading ? <LoadingState label="Lendo auditoria de recuperação…" /> : auditRows.length ? <div className="operations-list">{auditRows.slice(-6).map((row) => <div className="layer-row" key={row.audit_id}><span>#{row.snapshot_id}</span><b>{row.action}</b><em>{row.created_at}</em></div>)}</div> : <EmptyState icon={ShieldCheck} title="Nenhuma restauração auditada" description="Esta carreira ainda não tem eventos de restauração registrados." />}
      </PanelCard>
      <PanelCard eyebrow="FINANÇAS / FECHAMENTO" title="Resumo financeiro">
        <div className="operations-fields"><label className="operations-field">Temporada<input value={season} onChange={(event) => setSeason(event.target.value.replace(/\D/g, ""))} inputMode="numeric" /></label><label className="operations-field">Mês<input value={month} onChange={(event) => setMonth(event.target.value.replace(/\D/g, ""))} inputMode="numeric" /></label></div>
        <button className="outline-action" onClick={refreshFinance}><BarChart3 size={15} />Atualizar fechamento</button>
        {close.error ? <div className="fixture-empty">Fechamento indisponível para esta temporada.</div> : <div className="operations-list"><div className="layer-row"><span>NET</span><b>{close.data?.net ?? "—"}</b><em>fechamento persistido</em></div>{(close.data?.categories as FinanceCategoryRow[] | undefined)?.slice(0, 6).map((row) => <div className="layer-row" key={row.category}><span>{row.category}</span><b>{row.net}</b><em>{row.entries} lançamento(s)</em></div>)}</div>}
      </PanelCard>
    </div>
  </section>;
}
