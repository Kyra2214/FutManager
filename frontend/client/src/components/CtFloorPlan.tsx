import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { StatBar } from "@/components/StatBar";

/**
 * CtFloorPlan — substitui a lista "DEPARTAMENTOS ATUAIS" do CT (uma pilha de
 * `.ct-member-row`, mesma linguagem visual usada para pessoas em "EQUIPE
 * ATIVA") por uma leitura de planta baixa: cada departamento vira uma "sala"
 * num desenho técnico, em vez de mais uma linha de lista genérica.
 *
 * Ver Submódulo 6 em docs/PLANO_MUDANCA_VISUAL.md. Débito mapeado desde o
 * Submódulo 1 (StatBar): a linha de eficiência dentro de `.ct-member-row`
 * não virou StatBar naquela etapa justamente para não reformular esse
 * layout duas vezes — é reformulada por completo aqui.
 *
 * Não depende de nenhum dado novo: recebe exatamente
 * `workspace.staff.departments` (mesmo array já consumido pela lista que
 * substitui), sem nenhuma query adicional.
 */
export interface CtDepartmentDatum {
  department: string;
  level: number;
  capacity: number;
  efficiency: number;
}

function roomLabel(department: string) {
  return department.replaceAll("_", " ");
}

export function CtFloorPlan({ departments }: { departments: CtDepartmentDatum[] }) {
  const prefersReducedMotion = useReducedMotion();
  if (!departments.length) return null;

  return (
    <div className="ct-floor-plan" role="group" aria-label="Planta baixa dos departamentos do centro de treinamento">
      <div className="ct-floor-plan-grid">
        {departments.map((department, index) => (
          <motion.div
            className="ct-floor-plan-room"
            key={department.department}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: prefersReducedMotion ? 0 : 0.24,
              delay: prefersReducedMotion ? 0 : Math.min(index, 10) * 0.04,
              ease: "easeOut",
            }}
          >
            <span className="ct-floor-plan-room-tag">SALA {String(index + 1).padStart(2, "0")}</span>
            <b className="ct-floor-plan-room-label">{roomLabel(department.department)}</b>
            <span className="ct-floor-plan-room-level">NÍVEL {department.level}</span>
            <span className="ct-floor-plan-room-capacity">CAPACIDADE {department.capacity}</span>
            <StatBar label="EFICIÊNCIA" value={Math.round(department.efficiency * 100)} max={100} suffix="%" compact />
          </motion.div>
        ))}
      </div>
    </div>
  );
}
