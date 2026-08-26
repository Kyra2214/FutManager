export type EntityAssetStatus =
  | "COMPLETE"
  | "FULL_ONLY"
  | "MINI_ONLY"
  | "NO_SOURCE_ASSET"
  | "SOURCE_NOT_PROVIDED"
  | "ENTITY_NOT_FOUND"
  | "STATE_UNAVAILABLE";

export function getEntityAssetPresentation(status: EntityAssetStatus | undefined, entityType: "team" | "selection") {
  if (!status) return { label: "Aguardando entidade selecionada", tone: "pending" as const };

  const messages: Record<EntityAssetStatus, { label: string; tone: "ready" | "warning" | "missing" }> = {
    COMPLETE: { label: "Escudo original vinculado", tone: "ready" },
    FULL_ONLY: { label: "Escudo principal vinculado; mini ausente", tone: "warning" },
    MINI_ONLY: { label: "Somente escudo mini disponível", tone: "warning" },
    NO_SOURCE_ASSET: { label: "Escudo não fornecido no arquivo-mãe", tone: "missing" },
    SOURCE_NOT_PROVIDED: {
      label: entityType === "selection" ? "Escudo da seleção não fornecido; camisa disponível" : "Ativo não fornecido no arquivo-mãe",
      tone: "missing",
    },
    ENTITY_NOT_FOUND: { label: "Entidade não encontrada no estado", tone: "missing" },
    STATE_UNAVAILABLE: { label: "Estado de ativos indisponível", tone: "missing" },
  };

  return messages[status];
}
