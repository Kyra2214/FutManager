export function getCareerStartErrorMessage(code: string | undefined) {
  const messages: Record<string, string> = {
    ACTIVE_CAREER_EXISTS: "Já existe uma carreira ativa neste estado.",
    CLUB_NOT_FOUND: "O clube escolhido não existe mais no estado do motor.",
    SELECTION_NOT_FOUND: "A seleção escolhida não existe mais no estado do motor.",
    MANAGER_NAME_REQUIRED: "Informe o nome do manager para iniciar a carreira.",
    MANAGER_AGE_INVALID: "Escolha uma idade válida para o manager.",
    CAREER_TARGET_REQUIRED: "Escolha um clube ou uma seleção antes de começar.",
    CAREER_GATEWAY_UNAVAILABLE: "O motor local não está disponível para iniciar a carreira agora.",
  };
  return messages[code || ""] || "Não foi possível iniciar a carreira. Revise os dados e tente novamente.";
}
