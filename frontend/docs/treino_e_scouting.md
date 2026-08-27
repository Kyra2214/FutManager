# Contratos de treino e scouting

Os módulos de treino e scouting operam sobre o GameState SQLite. O frontend solicita prévias e resultados via tRPC, mas não calcula risco, evolução, confiança, custo ou disponibilidade.

## Treino

`TrainingService.create_weekly_plan` cria uma versão idempotente por clube, temporada e semana. Cada sessão guarda carga, recuperação, risco de lesão e estado, com bloqueio explícito para atleta lesionado. `create_objective` persiste metas mensuráveis por atleta e temporada. `preview_plan` retorna carga total, recuperação e risco sem persistir; `approve_plan` e `cancel_plan` são operações idempotentes do manager.

## Scouting

Uma missão pode ser focada por posição, idade, força, potencial e região. O relatório persiste a data de observação, seed, prioridade, observações e confiança. A confiança não é tratada como atributo real: oportunidades permanecem `OBSERVED` até confirmação explícita. `compare` confronta a oportunidade observada com o registro canônico do jogador, sem contratar ou promover automaticamente.

A comparação entre base e mercado é read-only. A confirmação de recrutamento exige aprovação e altera apenas o estado da oportunidade; contratação, transferência ou promoção continuam writers separados do motor.

> SQL/GameState é a fonte única da verdade; treino e scouting não criam uma segunda cópia de atributos de jogador no React.
