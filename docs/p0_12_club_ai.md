# P0-12 — IA dos clubes

A IA dos clubes opera sobre `club_ai_profiles`, `club_objectives` e `club_decision_history`. Personalidade, tolerância a risco, preferências e limite salarial são persistidos; não há estado esportivo paralelo nem geração de jogadores fora do banco canônico.

O diagnóstico agrega tamanho e categorias do elenco, indisponibilidade, caixa e saúde financeira. A avaliação de atleta usa idade, atributos nativos, forma e disponibilidade, e as propostas de treino e mercado derivam das necessidades observadas. Clubes abaixo do mínimo priorizam recrutamento; clubes com caixa ou saúde financeira restritos permanecem fora de decisões de mercado.

Objetivos do conselho têm prioridade, prazo, origem, progresso e status. Cada decisão registra alternativas, escolha, custo, motivo, seed, resultado e versão da IA. O ciclo semanal é idempotente para o mesmo clube e seed, evitando duplicidade de decisões. O gateway e o router tRPC expõem diagnóstico, histórico e ciclo semanal para leitura do frontend.
