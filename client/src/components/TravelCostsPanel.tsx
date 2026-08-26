import React from "react";
import { trpc } from "@/lib/trpc";
import { Plane, MapPin, CircleDollarSign, Info } from "lucide-react";

interface TravelCostsPanelProps {
  matchId: number;
  clubId?: number;
  season?: number;
}

export function TravelCostsPanel({ matchId, clubId, season }: TravelCostsPanelProps) {
  const previewQuery = trpc.matches.travelPreview.useQuery({ matchId, clubId }, { retry: 1 });
  const summaryQuery = trpc.matches.travelSummary.useQuery({ season }, { retry: 1 });

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(value);
  };

  const preview = previewQuery.data;
  const summary = summaryQuery.data;

  if (previewQuery.isLoading || summaryQuery.isLoading) {
    return <div className="travel-panel-loading">Consultando logística de viagem...</div>;
  }

  return (
    <section className="travel-costs-panel">
      <div className="travel-preview-card">
        <div className="panel-header">
          <Plane size={18} />
          <span>LOGÍSTICA DE DESLOCAMENTO</span>
        </div>
        
        {preview?.status === "AVAILABLE" ? (
          <div className="preview-content">
            <div className="route-info">
              <MapPin size={16} />
              <b>{preview.route_type === "DOMESTIC" ? "Viagem Nacional" : "Viagem Internacional"}</b>
              <span className="cost-badge">{formatCurrency(preview.cost)}</span>
            </div>
            <p className="preview-note">
              {preview.route_type === "DOMESTIC" 
                ? "Deslocamento padrão para partida fora de casa no mesmo país." 
                : "Custo adicional para logística internacional e trâmites de fronteira."}
            </p>
          </div>
        ) : preview?.route_type === "HOME_NO_TRAVEL" ? (
          <div className="preview-empty">
            <Info size={16} />
            <span>Partida em casa: sem custos de deslocamento registrados.</span>
          </div>
        ) : (
          <div className="preview-error">
            <Info size={16} />
            <span>{preview?.reason === "MATCH_NOT_FOUND" ? "Partida não localizada." : "Logística indisponível para este confronto."}</span>
          </div>
        )}
      </div>

      {summary && summary.trips > 0 && (
        <div className="travel-summary-mini">
          <div className="summary-item">
            <CircleDollarSign size={14} />
            <span>Acumulado: <b>{formatCurrency(summary.total_cost)}</b></span>
          </div>
          <div className="summary-item">
            <Plane size={14} />
            <span>Viagens: <b>{summary.trips}</b></span>
          </div>
        </div>
      )}
    </section>
  );
}
