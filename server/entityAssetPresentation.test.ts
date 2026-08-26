import { describe, expect, it } from "vitest";
import { getEntityAssetPresentation, type EntityAssetStatus } from "../client/src/lib/entityAsset";

describe("getEntityAssetPresentation", () => {
  it.each([
    ["COMPLETE", "team", "Escudo original vinculado"],
    ["FULL_ONLY", "team", "Escudo principal vinculado; mini ausente"],
    ["MINI_ONLY", "team", "Somente escudo mini disponível"],
    ["NO_SOURCE_ASSET", "team", "Escudo não fornecido no arquivo-mãe"],
    ["SOURCE_NOT_PROVIDED", "selection", "Escudo da seleção não fornecido; camisa disponível"],
    ["ENTITY_NOT_FOUND", "selection", "Entidade não encontrada no estado"],
    ["STATE_UNAVAILABLE", "selection", "Estado de ativos indisponível"],
  ] as const)("explica o status %s sem inventar ativo", (status, entityType, expectedLabel) => {
    expect(getEntityAssetPresentation(status as EntityAssetStatus, entityType)).toMatchObject({ label: expectedLabel });
  });
});
