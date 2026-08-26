import React, { useMemo, useState } from "react";
import { ArrowUpRight, BriefcaseBusiness, Building2, CircleDollarSign, HeartPulse, UsersRound } from "lucide-react";
import { toast } from "sonner";
import { trpc } from "@/lib/trpc";

type Mode = "market" | "ct";

const roles = [
  ["todos", "Todos"],
  ["treinador", "Treinadores"],
  ["auxiliar", "Auxiliares"],
  ["preparador_fisico", "Preparação"],
  ["medico", "Médicos"],
  ["scout", "Scouts"],
] as const;

function cash(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(value);
}

function roleLabel(role: string) {
  return roles.find(([key]) => key === role)?.[1] ?? role.replaceAll("_", " ");
}

export function StaffEconomyPanel({ mode, onNavigateToMarket }: { mode: Mode; onNavigateToMarket: () => void }) {
  const utils = trpc.useUtils();
  const [role, setRole] = useState<(typeof roles)[number][0]>("todos");
  const selectedRole = role === "todos" ? undefined : role;
  const catalogInput = useMemo(() => (selectedRole ? { role: selectedRole } : {}), [selectedRole]);
  const economyQuery = trpc.staffMarket.summary.useQuery(undefined, { retry: 1 });
  const catalogQuery = trpc.staffMarket.catalog.useQuery(catalogInput, { enabled: mode === "market", retry: 1 });
  const departmentQuery = trpc.staffMarket.departmentOffers.useQuery(undefined, { enabled: mode === "ct", retry: 1 });
  const workspaceQuery = trpc.club.workspace.useQuery(undefined, { enabled: mode === "ct", retry: 1 });
  const hireMutation = trpc.staffMarket.hire.useMutation({
    onSuccess: (result) => {
      toast.success(`${result.name} contratado(a) por ${cash(result.weekly_salary)} por semana.`);
      void utils.staffMarket.summary.invalidate();
      void utils.staffMarket.catalog.invalidate();
      void utils.staffMarket.departmentOffers.invalidate();
      void utils.club.workspace.invalidate();
    },
    onError: (error) => toast.error(error.message === "STAFF_UNAVAILABLE" ? "Esse profissional não está mais disponível." : "Não foi possível concluir a contratação."),
  });
  const departmentMutation = trpc.staffMarket.upgradeDepartment.useMutation({
    onSuccess: (result) => {
      toast.success(`${result.label} evoluiu para o nível ${result.target_level}.`);
      void utils.staffMarket.summary.invalidate();
      void utils.staffMarket.catalog.invalidate();
      void utils.staffMarket.departmentOffers.invalidate();
      void utils.club.workspace.invalidate();
    },
    onError: (error) => toast.error(error.message === "INSUFFICIENT_CASH" ? "O caixa não cobre esta evolução." : error.message === "DEPARTMENT_MAX_LEVEL" ? "Este departamento já está no nível máximo." : "Não foi possível evoluir o departamento."),
  });
  const economy = economyQuery.data;
  const loading = economyQuery.isLoading;

  return (
    <section className={`economy-command economy-command-${mode}`} aria-labelledby={`${mode}-economy-title`}>
      <div className="economy-command-head">
        <div>
          <span className="eyebrow">{mode === "market" ? "MERCADO / FOLHA SEMANAL" : "CT / ESTRUTURA E MANUTENÇÃO"}</span>
          <h2 id={`${mode}-economy-title`}>{mode === "market" ? "Comande a folha com contexto." : "Estrutura também pesa no caixa."}</h2>
          <p>{mode === "market" ? "Profissionais disponíveis, salários semanais e impacto imediato na comissão." : "Cada evolução cobra uma vez e amplia a manutenção semanal do centro de treinamento."}</p>
        </div>
        <span className="economy-status"><i /> ECONOMIA {economy ? "ATIVA" : loading ? "LENDO" : "INDISPONÍVEL"}</span>
      </div>

      <div className="economy-scorecard">
        <div><CircleDollarSign size={17} /><span>CAIXA ATUAL</span><strong>{loading ? "…" : cash(economy?.cash)}</strong><small>reserva inicial: {cash(economy?.initial_cash)}</small></div>
        <div><UsersRound size={17} /><span>FOLHA DO ELENCO</span><strong>{loading ? "…" : cash(economy?.weekly_player_payroll)}</strong><small>salários individuais por semana</small></div>
        <div><BriefcaseBusiness size={17} /><span>COMISSÃO</span><strong>{loading ? "…" : cash(economy?.weekly_staff_payroll)}</strong><small>contratos ativos por semana</small></div>
        <div><Building2 size={17} /><span>CT / MANUTENÇÃO</span><strong>{loading ? "…" : cash(economy?.weekly_department_maintenance)}</strong><small>estrutura contratada por semana</small></div>
        <div className="economy-total"><span>COMPROMISSO SEMANAL</span><strong>{loading ? "…" : cash(economy?.weekly_total)}</strong><small>{economy ? `poder ${economy.team_power.toFixed(1)} · fator país ${economy.country_factor.toFixed(2)}` : "aguardando perfil do clube"}</small></div>
      </div>

      <div className="economy-rule">
        <b>REGRA DE TEMPORADA</b>
        <p>O caixa inicial cobre <strong>39 semanas (3/4 da temporada)</strong>. Patrocínios, eventos, bilheteria e premiações deverão sustentar o trecho final.</p>
      </div>

      {mode === "market" ? (
        <div className="market-command-body">
          <div className="market-command-toolbar">
            <div><span className="eyebrow">CATÁLOGO PERSISTIDO</span><h3>Comissão técnica disponível</h3></div>
            <div className="role-filter" role="group" aria-label="Filtrar profissionais por função">
              {roles.map(([key, label]) => <button type="button" key={key} className={role === key ? "active" : ""} onClick={() => setRole(key)}>{label}</button>)}
            </div>
          </div>
          {catalogQuery.isLoading ? <div className="economy-empty">Consultando profissionais disponíveis no motor…</div> : catalogQuery.data?.length ? <div className="staff-market-grid">
            {catalogQuery.data.map((staff) => <article className="staff-market-card" key={staff.staff_id}>
              <div className="staff-card-top"><span>{roleLabel(staff.role).toUpperCase()}</span><b>NÍVEL {staff.level}</b></div>
              <h3>{staff.name}</h3>
              <p>{staff.specialization ?? "Especialização não informada"}</p>
              <dl><div><dt>REPUTAÇÃO</dt><dd>{staff.reputation}</dd></div><div><dt>POTENCIAL</dt><dd>{staff.potential}</dd></div><div><dt>IDADE</dt><dd>{staff.age} anos</dd></div></dl>
              <div className="staff-card-action"><div><span>SALÁRIO SEMANAL</span><strong>{cash(staff.weekly_salary)}</strong></div><button type="button" onClick={() => hireMutation.mutate({ staffId: staff.staff_id })} disabled={hireMutation.isPending}>{hireMutation.isPending ? "Contratando…" : "Contratar"}<ArrowUpRight size={15} /></button></div>
            </article>)}
          </div> : <div className="economy-empty">Não há profissional disponível nessa função.</div>}
        </div>
      ) : (
        <div className="department-command-body">
          <div className="ct-state-summary">
            <div className="market-command-toolbar"><div><span className="eyebrow">COMISSÃO ATIVA / ESTADO OFICIAL</span><h3>Quem sustenta o clube</h3></div><span className="economy-status"><i /> {workspaceQuery.isLoading ? "LENDO" : workspaceQuery.data?.staff.members.length ? `${workspaceQuery.data.staff.members.length} ATIVO(S)` : "SEM CONTRATOS"}</span></div>
            {workspaceQuery.isLoading ? <div className="economy-empty">Consultando comissão e departamentos persistidos…</div> : workspaceQuery.error ? <div className="economy-empty">A comissão técnica não pôde ser consultada.</div> : <><div className="ct-state-kpis"><div><span>PROFISSIONAIS</span><strong>{workspaceQuery.data?.staff.members.length ?? 0}</strong></div><div><span>MÉDIA DE NÍVEL</span><strong>{workspaceQuery.data?.staff.averageLevel?.toFixed(1) ?? "0.0"}</strong></div><div><span>DECISÕES REGISTRADAS</span><strong>{workspaceQuery.data?.staff.history.length ?? 0}</strong></div></div><div className="ct-state-grid"><div><span className="eyebrow">EQUIPE ATIVA</span>{workspaceQuery.data?.staff.members.length ? workspaceQuery.data.staff.members.map((member) => <div className="ct-member-row" key={member.staffId}><div><b>{member.name}</b><small>{roleLabel(member.role)} · {member.specialization ?? "especialização não informada"}</small></div><strong>NÍVEL {member.level}</strong></div>) : <p className="ct-state-empty">Nenhum profissional contratado. Consulte o Mercado para contratar.</p>}</div><div><span className="eyebrow">DEPARTAMENTOS ATUAIS</span>{workspaceQuery.data?.staff.departments.length ? workspaceQuery.data.staff.departments.map((department) => <div className="ct-member-row" key={department.department}><div><b>{department.department.replaceAll("_", " ")}</b><small>capacidade {department.capacity} · eficiência {(department.efficiency * 100).toFixed(0)}%</small></div><strong>NÍVEL {department.level}</strong></div>) : <p className="ct-state-empty">Nenhum departamento persistido. A primeira evolução pode ser feita abaixo.</p>}</div></div></>}
          </div>
          <div className="market-command-toolbar"><div><span className="eyebrow">DEPARTAMENTOS DO CT</span><h3>Comprar ou evoluir estrutura</h3></div><button type="button" className="economy-market-link" onClick={onNavigateToMarket}>Ver profissionais <ArrowUpRight size={15} /></button></div>
          {departmentQuery.isLoading ? <div className="economy-empty">Calculando ofertas de estrutura…</div> : departmentQuery.data?.length ? <div className="department-offer-grid">
            {departmentQuery.data.map((department) => <article className="department-offer-card" key={department.department}>
              <div className="department-icon">{department.department === "medicina" ? <HeartPulse size={22} /> : <Building2 size={22} />}</div>
              <span>{department.label.toUpperCase()}</span><h3>Nível {department.target_level}</h3><p>Capacidade projetada: {department.capacity}</p>
              <dl><div><dt>INVESTIMENTO</dt><dd>{cash(department.cost)}</dd></div><div><dt>MANUTENÇÃO / SEMANA</dt><dd>{cash(department.maintenance)}</dd></div></dl>
              <button type="button" onClick={() => departmentMutation.mutate({ department: department.department as "base" | "medicina" | "preparacao_fisica" | "analise" })} disabled={departmentMutation.isPending}>{departmentMutation.isPending ? "Processando…" : department.target_level === 1 ? "Comprar" : "Evoluir"}<ArrowUpRight size={15} /></button>
            </article>)}
          </div> : <div className="economy-empty">Não há oferta de departamento disponível.</div>}
        </div>
      )}
    </section>
  );
}
