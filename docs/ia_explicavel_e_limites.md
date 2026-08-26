# IA explicável e limites

O diagnóstico de IA do clube é derivado de elenco, disponibilidade, caixa, saúde financeira, calendário, objetivos e poder institucional persistidos. Cada decisão é gravada em `club_decision_history` com tipo, alvo, justificativa, alternativas, custo, resultado, seed e versão da IA.

As decisões de impacto têm uma etapa de prévia (`ai_preview`) que não grava e informa se o custo respeita o limite persistido do conselho em `club_ai_risk_limits`. A aprovação humana (`ai_approve`) é obrigatória antes de tratar uma decisão como aprovada e é idempotente. Alertas orçamentários consultam o custo da decisão e o limite por clube/temporada.

O histórico expõe alternativas descartadas, motivo, custo e fatos de origem sem inventar justificativas. A seed é parte do contexto para repetição determinística. A IA não cria jogadores, clubes, resultados, saldo ou atributos: quando a informação não existe nas tabelas canônicas, a resposta informa a ausência.

> A IA recomenda; o serviço canônico decide e persiste. O frontend apenas apresenta o diagnóstico e solicita prévias ou aprovações pelo gateway.
