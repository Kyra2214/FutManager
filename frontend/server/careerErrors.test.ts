import { describe, expect, it } from "vitest";
import { getCareerStartErrorMessage } from "../client/src/lib/careerErrors";

describe("getCareerStartErrorMessage", () => {
  it.each([
    ["ACTIVE_CAREER_EXISTS", "Já existe uma carreira ativa neste estado."],
    ["CLUB_NOT_FOUND", "O clube escolhido não existe mais no estado do motor."],
    ["SELECTION_NOT_FOUND", "A seleção escolhida não existe mais no estado do motor."],
    ["CAREER_GATEWAY_UNAVAILABLE", "O motor local não está disponível para iniciar a carreira agora."],
  ])("expõe o erro %s de forma clara", (code, message) => {
    expect(getCareerStartErrorMessage(code)).toBe(message);
  });
});
