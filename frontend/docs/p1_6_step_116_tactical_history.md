# P1-6 / passo 116 — Histórico de decisões táticas

O GameState agora persiste decisões em `tactical_decision_history`, vinculando clube, partida opcional, tipo de decisão, data UTC lógica do ciclo e payload JSON canônico ordenado. `record_tactical_decision` rejeita clube desconhecido e eventos vazios; `tactical_decision_history` lê em ordem crescente de decisão e permite filtrar por partida.

O teste focado confirmou payload estruturado, ordenação cronológica, filtro sem resultados e rejeição de clube inexistente.
