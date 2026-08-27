import React, { useMemo, useState } from "react";
import { ArrowRight, Check, Search, Shield, UserRound } from "lucide-react";
import { trpc } from "@/lib/trpc";
import { getEntityAssetPresentation } from "@/lib/entityAsset";
import { getCareerStartErrorMessage } from "@/lib/careerErrors";

type TargetType = "club" | "selection";
type ActiveSave = { careerName: string; targetName: string; targetType: TargetType; selectedCountries?: Array<{ name: string }>; startingDivision?: number };
type WorldCountry = { countryId: number; name: string; code: string | null; clubCount: number; firstDivisionClubCount: number; firstDivisionName: string | null };

export default function CareerStart({ onStarted, onContinue }: { onStarted: () => void; onContinue?: () => void }) {
  const [targetType, setTargetType] = useState<TargetType>("club");
  const [search, setSearch] = useState("");
  const [worldSearch, setWorldSearch] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedCountryIds, setSelectedCountryIds] = useState<number[]>([]);
  const [managerName, setManagerName] = useState("");
  const [careerName, setCareerName] = useState("Minha carreira");
  const [age, setAge] = useState("30");
  const [nationality, setNationality] = useState("");
  const utils = trpc.useUtils();
  const currentCareer = trpc.career.current.useQuery(undefined, { retry: 1 });
  const catalogInput = useMemo(() => ({ targetType, search, limit: 48 }), [targetType, search]);
  const catalogQuery = trpc.career.catalog.useQuery(catalogInput, { retry: 1 });
  const worldCountriesQuery = trpc.career.worldCountries.useQuery({ search: worldSearch, limit: 48 }, { retry: 1 });
  const startMutation = trpc.career.start.useMutation({
    onSuccess: async () => {
      await utils.career.current.invalidate();
      onStarted();
    },
  });
  const selectedTarget = catalogQuery.data?.find((item) => item.entityId === selectedId) ?? null;
  const selectedCountries = (worldCountriesQuery.data?.items ?? []) as WorldCountry[];
  const selectedFirstDivisionClubCount = selectedCountries.filter((country) => selectedCountryIds.includes(country.countryId)).reduce((total, country) => total + (country.firstDivisionClubCount || 0), 0);
  const parallelPreviewInput = useMemo(() => ({ selectedCountryIds, targetType, targetId: selectedId ?? 0 }), [selectedCountryIds, targetType, selectedId]);
  const parallelPreview = trpc.career.parallelPreview.useQuery(parallelPreviewInput, { enabled: selectedCountryIds.length > 0 && selectedId !== null, retry: 0 });
  const targetCountryId = (selectedTarget as (typeof selectedTarget & { countryId?: number }) | null)?.countryId;
  const targetCountryMissing = Boolean(targetType === "club" && targetCountryId && !selectedCountryIds.includes(targetCountryId));
  const canStart = Boolean(selectedTarget && selectedCountryIds.length > 0 && !targetCountryMissing && managerName.trim() && careerName.trim() && Number(age) >= 18 && !startMutation.isPending);

  const selectTargetType = (nextType: TargetType) => {
    setTargetType(nextType);
    setSelectedId(null);
  };

  const toggleCountry = (countryId: number) => {
    setSelectedCountryIds((current) => current.includes(countryId) ? current.filter((id) => id !== countryId) : [...current, countryId]);
  };

  const activeSave = currentCareer.data?.started ? currentCareer.data as unknown as ActiveSave : null;

  return <main className="career-start-shell">
    <section className="career-start-hero">
      <div className="career-start-brand"><span>FUT</span><b>MANAGER</b></div>
      <div className="career-start-kicker">NOVA CARREIRA · ESTADO OFICIAL</div>
      <h1>Escolha <em>o seu lugar</em><br />no futebol.</h1>
      <p>A escolha inicia uma carreira no motor local. O universo de ligas e os ativos são lidos diretamente do SQL oficial.</p>
      <div className="career-start-steps"><span className="active">01 Identidade</span><span className={selectedCountryIds.length ? "active" : ""}>02 Ligas</span><span>03 Destino</span><span>04 Começar</span></div>
    </section>
    <section className="career-start-panel">
      {activeSave && <div className="active-save-card"><div><span className="eyebrow">SAVE ATIVO</span><strong>{activeSave.careerName}</strong><small>{activeSave.targetName} · {activeSave.targetType === "club" ? "Clube" : "Seleção"}</small><small>{activeSave.selectedCountries?.map((country) => country.name).join(" + ") || "Universo padrão"} · início na {activeSave.startingDivision || 4}ª divisão</small></div><button className="outline-action" type="button" onClick={onContinue}>Continuar save <ArrowRight size={16} /></button></div>}
      <header><span className="eyebrow">PRIMEIRO APITO</span><h2>Monte o ponto de partida</h2><p>Defina o universo esportivo antes de escolher quem você vai comandar.</p></header>
      <div className="career-form-grid"><label><span>SEU NOME</span><input value={managerName} onChange={(event) => setManagerName(event.target.value)} maxLength={60} placeholder="Como o manager será chamado?" /></label><label><span>NOME DA CARREIRA</span><input value={careerName} onChange={(event) => setCareerName(event.target.value)} maxLength={80} /></label><label><span>IDADE</span><input value={age} onChange={(event) => setAge(event.target.value.replace(/\D/g, ""))} inputMode="numeric" /><small className="career-field-hint">Mínimo de 18 anos</small></label><label><span>NACIONALIDADE <i>opcional</i></span><input value={nationality} onChange={(event) => setNationality(event.target.value)} maxLength={60} placeholder="Ex.: Brasil" /></label></div>
      <section className="career-world-config" aria-labelledby="world-config-title">
        <div className="career-target-head"><div><span className="eyebrow">UNIVERSO DA CARREIRA</span><h3 id="world-config-title">Escolha as ligas participantes</h3></div><strong className="career-division-badge">4ª DIVISÃO</strong></div>
        <p className="career-world-note">As ligas escolhidas formam um único universo. O time que você selecionar começará sempre na <b>4ª divisão</b>.</p>
        <label className="career-search career-world-search"><Search size={17} /><input value={worldSearch} onChange={(event) => setWorldSearch(event.target.value)} placeholder="Buscar país ou código" /></label>
        {worldCountriesQuery.isLoading ? <div className="career-target-loading">Carregando ligas oficiais…</div> : worldCountriesQuery.isError ? <div className="career-target-loading error">Não foi possível consultar os países do motor.</div> : <div className="career-world-countries">{selectedCountries.map((country) => <button type="button" key={country.countryId} className={`career-world-country ${selectedCountryIds.includes(country.countryId) ? "selected" : ""}`} onClick={() => toggleCountry(country.countryId)}><span><b>{country.name}</b><small>{country.code || "PAÍS"} · {country.firstDivisionClubCount || 0} clube(s) da 1ª divisão</small></span>{selectedCountryIds.includes(country.countryId) && <Check size={15} />}</button>)}</div>}
        <div className="career-world-summary" aria-live="polite"><span>{selectedCountryIds.length} liga(s) selecionada(s)</span><b>{selectedCountryIds.length ? selectedCountries.filter((country) => selectedCountryIds.includes(country.countryId)).map((country) => country.name).join(" + ") : "Escolha pelo menos uma liga"}</b><small>{selectedCountryIds.length ? `${selectedFirstDivisionClubCount} clube(s) formarão a liga paralela` : "Os clubes nacionais continuam em suas ligas originais"}</small></div>
        {parallelPreview.isLoading && selectedId !== null && <div className="career-parallel-preview-loading">Montando prévia oficial das divisões…</div>}
        {parallelPreview.isError && selectedId !== null && <div className="career-parallel-preview-error">O clube escolhido precisa pertencer à primeira divisão oficial das ligas selecionadas.</div>}
        {parallelPreview.data && <div className="career-parallel-preview" aria-label="Prévia da liga paralela"><div className="career-parallel-preview-head"><div><span className="eyebrow">PRÉVIA OFICIAL</span><strong>{parallelPreview.data.total_clubs} clubes · 4 divisões</strong></div><small>Sorteio persistirá no save · seed {parallelPreview.data.seed}</small></div><div className="career-parallel-divisions">{parallelPreview.data.divisions.map((division) => <details key={division.division} open={division.division === 4}><summary><span>{division.division}ª divisão</span><b>{division.clubs.length} clubes</b></summary><div className="career-parallel-club-list">{division.clubs.map((club) => <span key={club.club_id} className={club.club_id === selectedId ? "manager-club" : ""}>{club.name || `Clube #${club.club_id}`}{club.club_id === selectedId && " · seu time"}</span>)}</div></details>)}</div></div>}
      </section>
      <div className="career-target-head"><div><span className="eyebrow">DESTINO</span><h3>Escolha a entidade</h3></div><div className="career-type-toggle"><button type="button" className={targetType === "club" ? "active" : ""} onClick={() => selectTargetType("club")}><Shield size={14} /> Clube</button><button type="button" className={targetType === "selection" ? "active" : ""} onClick={() => selectTargetType("selection")}><UserRound size={14} /> Seleção</button></div></div>
      <label className="career-search"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={targetType === "club" ? "Buscar clube por nome" : "Buscar seleção por nome ou código"} /></label>
      <div className="career-targets" aria-live="polite">{catalogQuery.isLoading && <div className="career-target-loading">Carregando entidades oficiais…</div>}{catalogQuery.isError && <div className="career-target-loading error">Não foi possível consultar o estado do motor.</div>}{!catalogQuery.isLoading && !catalogQuery.isError && catalogQuery.data?.length === 0 && <div className="career-target-loading">Nenhuma entidade encontrada para essa busca.</div>}{catalogQuery.data?.map((item) => { const presentation = getEntityAssetPresentation(item.mappingStatus as Parameters<typeof getEntityAssetPresentation>[0], targetType === "club" ? "team" : "selection"); const selected = item.entityId === selectedId; return <button type="button" key={item.entityId} className={`career-target-card ${selected ? "selected" : ""}`} onClick={() => setSelectedId(item.entityId)}><span className="career-target-asset">{item.assetUrl ? <img src={item.assetUrl} alt={item.assetKind === "kit" ? `Camisa de ${item.name}` : `Escudo de ${item.name}`} /> : <span>?</span>}</span><span className="career-target-copy"><b>{item.name}</b><small>{presentation.label}</small></span>{selected && <span className="career-selected"><Check size={15} /></span>}</button>; })}</div>
      {selectedTarget && <div className="career-confirm-target"><span className="eyebrow">ESCOLHIDO</span><strong>{selectedTarget.name}</strong><span>{targetType === "club" ? "Clube" : "Seleção"} · ID oficial {selectedTarget.entityId}</span></div>}
      {targetCountryMissing && <p className="career-error">Este clube pertence a um país que ainda não foi incluído no universo. Selecione a liga correspondente acima.</p>}
      {startMutation.error?.message.includes("TARGET_CLUB_NOT_FIRST_DIVISION") && <p className="career-error">Este clube não pertence à primeira divisão oficial e não pode entrar na liga paralela.</p>}
      {selectedCountryIds.length === 0 && <p className="career-world-validation">Escolha pelo menos uma liga para liberar o início da carreira.</p>}
      {startMutation.error && <p className="career-error">{getCareerStartErrorMessage(startMutation.error.message)}</p>}
      <button className="career-start-action" disabled={!canStart} onClick={() => selectedTarget && startMutation.mutate({ managerName: managerName.trim(), nationality: nationality.trim() || undefined, age: Number(age), careerName: careerName.trim(), targetType, targetId: selectedTarget.entityId, selectedCountryIds })}>{startMutation.isPending ? "Iniciando carreira…" : "Começar carreira"}<ArrowRight size={18} /></button>
    </section>
  </main>;
}
