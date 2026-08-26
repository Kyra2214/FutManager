import React, { useMemo, useState } from "react";
import { ArrowRight, Check, Search, Shield, UserRound } from "lucide-react";
import { trpc } from "@/lib/trpc";
import { getEntityAssetPresentation } from "@/lib/entityAsset";
import { getCareerStartErrorMessage } from "@/lib/careerErrors";

type TargetType = "club" | "selection";
type ActiveSave = { careerName: string; targetName: string; targetType: TargetType };

export default function CareerStart({ onStarted, onContinue }: { onStarted: () => void; onContinue?: () => void }) {
  const [targetType, setTargetType] = useState<TargetType>("club");
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [managerName, setManagerName] = useState("");
  const [careerName, setCareerName] = useState("Minha carreira");
  const [age, setAge] = useState("30");
  const [nationality, setNationality] = useState("");
  const utils = trpc.useUtils();
  const currentCareer = trpc.career.current.useQuery(undefined, { retry: 1 });
  const catalogInput = useMemo(() => ({ targetType, search, limit: 48 }), [targetType, search]);
  const catalogQuery = trpc.career.catalog.useQuery(catalogInput, { retry: 1 });
  const startMutation = trpc.career.start.useMutation({
    onSuccess: async () => {
      await utils.career.current.invalidate();
      onStarted();
    },
  });
  const selectedTarget = catalogQuery.data?.find((item) => item.entityId === selectedId) ?? null;
  const canStart = Boolean(selectedTarget && managerName.trim() && careerName.trim() && Number(age) >= 18 && !startMutation.isPending);

  const selectTargetType = (nextType: TargetType) => {
    setTargetType(nextType);
    setSelectedId(null);
  };

  const activeSave = currentCareer.data?.started ? currentCareer.data as unknown as ActiveSave : null;

  return <main className="career-start-shell"><section className="career-start-hero"><div className="career-start-brand"><span>FUT</span><b>MANAGER</b></div><div className="career-start-kicker">NOVA CARREIRA · ESTADO OFICIAL</div><h1>Escolha <em>o seu lugar</em><br />no futebol.</h1><p>A escolha inicia uma única carreira no motor local. Clube, seleção e ativos são lidos diretamente do SQL oficial.</p><div className="career-start-steps"><span className="active">01 Identidade</span><span>02 Destino</span><span>03 Começar</span></div></section><section className="career-start-panel">{activeSave && <div className="active-save-card"><div><span className="eyebrow">SAVE ATIVO</span><strong>{activeSave.careerName}</strong><small>{activeSave.targetName} · {activeSave.targetType === "club" ? "Clube" : "Seleção"}</small></div><button className="outline-action" type="button" onClick={onContinue}>Continuar save <ArrowRight size={16} /></button></div>}<header><span className="eyebrow">PRIMEIRO APITO</span><h2>Monte o ponto de partida</h2><p>Você poderá seguir o clube no dia a dia ou assumir uma seleção nacional.</p></header><div className="career-form-grid"><label><span>SEU NOME</span><input value={managerName} onChange={(event) => setManagerName(event.target.value)} maxLength={60} placeholder="Como o manager será chamado?" /></label><label><span>NOME DA CARREIRA</span><input value={careerName} onChange={(event) => setCareerName(event.target.value)} maxLength={80} /></label><label><span>IDADE</span><input value={age} onChange={(event) => setAge(event.target.value.replace(/\D/g, ""))} inputMode="numeric" /></label><label><span>NACIONALIDADE <i>opcional</i></span><input value={nationality} onChange={(event) => setNationality(event.target.value)} maxLength={60} placeholder="Ex.: Brasil" /></label></div><div className="career-target-head"><div><span className="eyebrow">DESTINO</span><h3>Escolha a entidade</h3></div><div className="career-type-toggle"><button className={targetType === "club" ? "active" : ""} onClick={() => selectTargetType("club")}><Shield size={14} /> Clube</button><button className={targetType === "selection" ? "active" : ""} onClick={() => selectTargetType("selection")}><UserRound size={14} /> Seleção</button></div></div><label className="career-search"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={targetType === "club" ? "Buscar clube por nome" : "Buscar seleção por nome ou código"} /></label><div className="career-targets" aria-live="polite">{catalogQuery.isLoading && <div className="career-target-loading">Carregando entidades oficiais…</div>}{catalogQuery.isError && <div className="career-target-loading error">Não foi possível consultar o estado do motor.</div>}{!catalogQuery.isLoading && !catalogQuery.isError && catalogQuery.data?.length === 0 && <div className="career-target-loading">Nenhuma entidade encontrada para essa busca.</div>}{catalogQuery.data?.map((item) => { const presentation = getEntityAssetPresentation(item.mappingStatus as Parameters<typeof getEntityAssetPresentation>[0], targetType === "club" ? "team" : "selection"); const selected = item.entityId === selectedId; return <button key={item.entityId} className={`career-target-card ${selected ? "selected" : ""}`} onClick={() => setSelectedId(item.entityId)}><span className="career-target-asset">{item.assetUrl ? <img src={item.assetUrl} alt={item.assetKind === "kit" ? `Camisa de ${item.name}` : `Escudo de ${item.name}`} /> : <span>?</span>}</span><span className="career-target-copy"><b>{item.name}</b><small>{presentation.label}</small></span>{selected && <span className="career-selected"><Check size={15} /></span>}</button>; })}</div>{selectedTarget && <div className="career-confirm-target"><span className="eyebrow">ESCOLHIDO</span><strong>{selectedTarget.name}</strong><span>{targetType === "club" ? "Clube" : "Seleção"} · ID oficial {selectedTarget.entityId}</span></div>}{startMutation.error && <p className="career-error">{getCareerStartErrorMessage(startMutation.error.message)}</p>}<button className="career-start-action" disabled={!canStart} onClick={() => selectedTarget && startMutation.mutate({ managerName: managerName.trim(), nationality: nationality.trim() || undefined, age: Number(age), careerName: careerName.trim(), targetType, targetId: selectedTarget.entityId })}>{startMutation.isPending ? "Iniciando carreira…" : "Começar carreira"}<ArrowRight size={18} /></button></section></main>;
}
