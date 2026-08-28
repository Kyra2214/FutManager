/*
 * ClubHUD — Submódulo 8: Dashboard como HUD
 *
 * O dashboard principal ("Seu Clube") vira uma leitura tipo HUD de jogo,
 * organizando as métricas estruturais do clube (elenco, CT, estádio, scouting)
 * como quadrantes numa tela de jogo, não como lista genérica de "estrutura".
 *
 * Cada quadrante (elenco, CT, estádio, scouting) ganha uma metáfora de jogo:
 * — Elenco: "ESCALAÇÃO" com miniatura de formação tática
 * — CT: "COMISSÃO" com resumo de departamentos
 * — Estádio: "ESTÁDIO" com capacidade e status
 * — Scouting: "PROSPECÇÃO" com missões ativas
 *
 * Layout: quadrante principal (elenco com formação) + três miniatura lateral
 * (CT, estádio, scouting) em padrão rearranjável conforme dados,
 * entrada cascata respeitando `prefers-reduced-motion`.
 */

import React, { useMemo } from "react";
import { ArrowUpRight, ChevronRight, AlertCircle, Users, Building2, Trophy } from "lucide-react";
import type { WorkspaceQueryResponse } from "@/types/workspace";
import { FormationPitch } from "./FormationPitch";
import { StatBar } from "./StatBar";

type ClubHUDProps = {
  workspace: WorkspaceQueryResponse;
  onNavigateToMarket?: () => void;
  onUpdateInfo?: () => void;
};

type QuadrantMeta = {
  icon: React.ReactNode;
  label: string;
  value: string;
  tone?: "grass" | "cobalt" | "coral";
};

export function ClubHUD({ workspace, onNavigateToMarket, onUpdateInfo }: ClubHUDProps) {
  const starterPlayers = useMemo(
    () => (workspace?.squad.players ?? []).filter((player) => player.status === "Titular"),
    [workspace?.squad.players]
  );

  const benchPlayers = useMemo(
    () => (workspace?.squad.players ?? []).filter((player) => player.status !== "Titular"),
    [workspace?.squad.players]
  );

  const staffCount = (workspace?.staff.members ?? []).length;
  const departmentCount = (workspace?.staff.departments ?? []).length;
  const missionCount = (workspace?.scouting.missions ?? []).length;

  // Quadrante 1: ESCALAÇÃO (elenco com formação)
  const scalationQuadrant: QuadrantMeta = {
    icon: <Users size={18} strokeWidth={1.8} />,
    label: "ESCALAÇÃO",
    value: `${workspace?.squad.starters ?? 0} Titulares · ${workspace?.squad.reserves ?? 0} Reservas`,
    tone: "cobalt",
  };

  // Quadrante 2: COMISSÃO (CT)
  const commissionQuadrant: QuadrantMeta = {
    icon: <Trophy size={18} strokeWidth={1.8} />,
    label: "COMISSÃO",
    value: staffCount
      ? `${staffCount} profissional(is) · ${departmentCount} departamentos`
      : "Nenhum profissional contratado",
    tone: staffCount > 0 ? "grass" : "coral",
  };

  // Quadrante 3: ESTÁDIO
  const stadiumQuadrant: QuadrantMeta = {
    icon: <Building2 size={18} strokeWidth={1.8} />,
    label: "ESTÁDIO",
    value: workspace?.stadium.name
      ? `${workspace.stadium.capacity?.toLocaleString("pt-BR") ?? "—"} capacidade`
      : "Sem registro",
    tone: workspace?.stadium.capacity ? "grass" : "coral",
  };

  // Quadrante 4: PROSPECÇÃO (scouting)
  const prospectingQuadrant: QuadrantMeta = {
    icon: <Trophy size={18} strokeWidth={1.8} />,
    label: "PROSPECÇÃO",
    value: missionCount
      ? `${missionCount} missão(ões) ativa(s) · ${workspace?.scouting.opportunities ?? 0} oportunidade(s)`
      : `${workspace?.scouting.opportunities ?? 0} oportunidade(s) · sem missões ativas`,
    tone: missionCount > 0 ? "grass" : "cobalt",
  };

  const healthStatus = workspace?.health.count ?? 0;
  const healthTone = healthStatus === 0 ? "grass" : healthStatus < 3 ? "cobalt" : "coral";

  return (
    <div className="club-hud">
      {/* TOPO HUD: Barra de status do clube */}
      <div className="hud-status-bar">
        <div className="hud-status-item">
          <span className="hud-status-label">SAÚDE</span>
          <StatBar
            label=""
            value={20 - healthStatus}
            max={20}
            suffix="atletas"
            tone={healthTone}
            compact
          />
        </div>
        <div className="hud-status-divider" />
        <div className="hud-status-item">
          <span className="hud-status-label">COMISSÃO</span>
          <strong>{staffCount}</strong>
          <small>profissionais</small>
        </div>
        <div className="hud-status-divider" />
        <div className="hud-status-item">
          <span className="hud-status-label">ATUALIZAÇÕES</span>
          <span className={`hud-status-pip ${workspace?.source.available ? "is-online" : "is-offline"}`} />
          <small>{workspace?.source.available ? "Dados sincronizados" : "Sincronização pendente"}</small>
        </div>
      </div>

      {/* LAYOUT PRINCIPAL HUD: Quadrante grande + 3 mini-quadrantes */}
      <div className="hud-grid">
        {/* Quadrante principal: ESCALAÇÃO com formação */}
        <div className="hud-quadrant hud-quadrant-large hud-quadrant-escalacao" data-index="0">
          <div className="hud-quadrant-header">
            <div className="hud-quadrant-title">
              <span className="hud-quadrant-icon">{scalationQuadrant.icon}</span>
              <span className="hud-quadrant-label">{scalationQuadrant.label}</span>
            </div>
            <span className="hud-quadrant-meta">{scalationQuadrant.value}</span>
          </div>

          <div className="hud-quadrant-content">
            {starterPlayers.length > 0 ? (
              <>
                <div className="formation-container">
                  <FormationPitch players={starterPlayers} />
                </div>
                {benchPlayers.length > 0 && (
                  <div className="hud-bench-section">
                    <span className="hud-bench-label">BANCO · {benchPlayers.length} reserva(s)</span>
                    <div className="hud-bench-list">
                      {benchPlayers.slice(0, 4).map((player, idx) => (
                        <div key={player.playerId} className="hud-bench-item" data-index={idx}>
                          <span className="hud-bench-number">#{player.playerId}</span>
                          <span className="hud-bench-name">{player.name}</span>
                          <span className="hud-bench-position">{player.position}</span>
                        </div>
                      ))}
                      {benchPlayers.length > 4 && (
                        <div className="hud-bench-overflow">+{benchPlayers.length - 4}</div>
                      )}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="hud-empty-state">
                <AlertCircle size={24} />
                <h3>Sem elenco</h3>
                <p>Nenhum jogador está disponível para o clube controlado.</p>
                <button className="outline-action" onClick={onNavigateToMarket}>
                  Ir ao Mercado <ArrowUpRight size={14} />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Mini-quadrante: COMISSÃO */}
        <div className="hud-quadrant hud-quadrant-mini hud-quadrant-comissao" data-index="1">
          <div className="hud-quadrant-header">
            <span className="hud-quadrant-icon">{commissionQuadrant.icon}</span>
            <span className="hud-quadrant-label">{commissionQuadrant.label}</span>
          </div>
          <div className="hud-quadrant-content">
            <div className="hud-mini-stat">
              <span className="hud-mini-label">PROFISSIONAIS</span>
              <strong className={`hud-mini-value tone-${commissionQuadrant.tone ?? "cobalt"}`}>
                {staffCount}
              </strong>
            </div>
            <div className="hud-mini-stat">
              <span className="hud-mini-label">DEPARTAMENTOS</span>
              <strong className={`hud-mini-value tone-${commissionQuadrant.tone ?? "cobalt"}`}>
                {departmentCount}
              </strong>
            </div>
            <button className="hud-mini-action" onClick={onNavigateToMarket}>
              Contratar <ChevronRight size={14} />
            </button>
          </div>
        </div>

        {/* Mini-quadrante: ESTÁDIO */}
        <div className="hud-quadrant hud-quadrant-mini hud-quadrant-stadium" data-index="2">
          <div className="hud-quadrant-header">
            <span className="hud-quadrant-icon">{stadiumQuadrant.icon}</span>
            <span className="hud-quadrant-label">{stadiumQuadrant.label}</span>
          </div>
          <div className="hud-quadrant-content">
            <div className="hud-mini-stat">
              <span className="hud-mini-label">CAPACIDADE</span>
              <strong className={`hud-mini-value tone-${stadiumQuadrant.tone ?? "cobalt"}`}>
                {workspace?.stadium.capacity?.toLocaleString("pt-BR") ?? "—"}
              </strong>
            </div>
            <div className="hud-mini-stat">
              <span className="hud-mini-label">NÍVEL</span>
              <strong className={`hud-mini-value tone-${stadiumQuadrant.tone ?? "cobalt"}`}>
                {workspace?.stadium.level ?? "—"}
              </strong>
            </div>
            {workspace?.stadium.name && (
              <small className="hud-mini-name">{workspace.stadium.name}</small>
            )}
          </div>
        </div>

        {/* Mini-quadrante: PROSPECÇÃO */}
        <div className="hud-quadrant hud-quadrant-mini hud-quadrant-prospecting" data-index="3">
          <div className="hud-quadrant-header">
            <span className="hud-quadrant-icon">{prospectingQuadrant.icon}</span>
            <span className="hud-quadrant-label">{prospectingQuadrant.label}</span>
          </div>
          <div className="hud-quadrant-content">
            <div className="hud-mini-stat">
              <span className="hud-mini-label">MISSÕES</span>
              <strong className={`hud-mini-value tone-${prospectingQuadrant.tone ?? "cobalt"}`}>
                {missionCount}
              </strong>
            </div>
            <div className="hud-mini-stat">
              <span className="hud-mini-label">OPORTUNIDADES</span>
              <strong className={`hud-mini-value tone-${prospectingQuadrant.tone ?? "cobalt"}`}>
                {workspace?.scouting.opportunities ?? 0}
              </strong>
            </div>
            {missionCount > 0 && (
              <button className="hud-mini-action" onClick={() => {}}>
                Gerenciar <ChevronRight size={14} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* RODAPÉ HUD: Ação rápida de atualização */}
      <div className="hud-footer">
        <button className="outline-action" onClick={onUpdateInfo}>
          Atualizar Informações <ArrowUpRight size={14} />
        </button>
        <small>{workspace?.source.message ?? "Atualizando as informações do clube."}</small>
      </div>
    </div>
  );
}
