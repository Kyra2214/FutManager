import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

/**
 * PlayerProductionChart — primeiro gráfico real do plano de mudança visual
 * (Submódulo 3). Substitui a lista de "event-card" usada para o resumo de
 * "Atletas em destaque" por uma barra horizontal comparando gols e
 * assistências, lida em um único golpe de vista em vez de cartão por cartão.
 *
 * As cores abaixo espelham os tokens de :root em `index.css`
 * (--grass, --cobalt, --ink, --line). Precisam estar em hex porque o
 * Recharts define `fill`/`stroke` como atributos SVG resolvidos pela
 * biblioteca, não como propriedades CSS herdadas — usar var() aqui não é
 * confiável entre navegadores. Se a paleta em :root mudar, atualizar aqui
 * também.
 */
const COLOR_GRASS = "#a7c957";
const COLOR_COBALT = "#3b5bc4";
const COLOR_INK = "#202222";
const COLOR_LINE = "#d8d5c9";
const COLOR_MUTED = "#8d8f86";

export interface PlayerProductionDatum {
  playerId: number;
  name: string;
  goals: number;
  assists: number;
  averageRating: number | null;
}

function ProductionTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  label?: string;
  payload?: Array<{ dataKey: string; value: number; color: string; payload: PlayerProductionDatum }>;
}) {
  if (!active || !payload?.length) return null;
  const datum = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <b>{label}</b>
      {payload.map((entry) => (
        <span key={entry.dataKey} style={{ color: entry.color }}>
          {entry.dataKey === "goals" ? "Gols" : "Assistências"} · {entry.value}
        </span>
      ))}
      {datum.averageRating !== null ? <em>nota média {datum.averageRating.toFixed(1)}</em> : null}
    </div>
  );
}

export function PlayerProductionChart({ data }: { data: PlayerProductionDatum[] }) {
  const height = Math.max(data.length, 1) * 40 + 16;

  return (
    <div className="production-chart">
      <div className="chart-legend">
        <span><i style={{ background: COLOR_GRASS }} /> Gols</span>
        <span><i style={{ background: COLOR_COBALT }} /> Assistências</span>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 2, right: 18, bottom: 2, left: 0 }}
          barCategoryGap={12}
        >
          <CartesianGrid horizontal={false} stroke={COLOR_LINE} />
          <XAxis
            type="number"
            allowDecimals={false}
            tick={{ fontFamily: "Space Grotesk", fontSize: 9, fill: COLOR_MUTED }}
            axisLine={{ stroke: COLOR_LINE }}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={112}
            tick={{ fontFamily: "Space Grotesk", fontSize: 10, fontWeight: 600, fill: COLOR_INK }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<ProductionTooltip />} cursor={{ fill: "rgba(59,91,196,.06)" }} />
          <Bar dataKey="goals" name="Gols" fill={COLOR_GRASS} radius={[0, 2, 2, 0]} maxBarSize={13} />
          <Bar dataKey="assists" name="Assistências" fill={COLOR_COBALT} radius={[0, 2, 2, 0]} maxBarSize={13} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
