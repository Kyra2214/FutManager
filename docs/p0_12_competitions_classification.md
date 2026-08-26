# P0-12 — Competições e classificação

O `CompetitionStructureService` mantém formatos, pontos, turnos, critérios de desempate, fases, rodadas, fixtures, configuração de pênaltis, transições, campeões, premiações e alertas em tabelas canônicas do GameState.

A classificação é derivada de `team_competition_stats`, que é atualizada a partir de partidas aplicadas pelo motor. O frontend possui apenas leitura via gateway; não há mutation para alterar manualmente a tabela. Mata-mata/pênaltis, ida e volta, status de competição, calendário de finais, promoção/rebaixamento e histórico de campeões possuem guardas de configuração.

Premiações só podem ser calculadas após a competição estar `FINISHED`; a chave primária de `competition_prize_payments` torna o pagamento idempotente. Alertas de líder e último colocado usam restrição única. Os limites atuais são honestos: formatos não configurados e regras ausentes são rejeitados em vez de inferidos.
