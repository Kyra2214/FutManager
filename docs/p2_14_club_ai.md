# P2-14 — IA dos clubes

A IA dos clubes opera em banco isolado ou GameState real através de `ClubAI`, preservando as transações do motor. Perfis de personalidade e orçamento são persistidos em `club_ai_profiles`; objetivos esportivos e seu progresso em `club_objectives`; decisões, alternativas, escolha, custo, motivo, seed e versão em `club_decision_history`.

O diagnóstico utiliza elenco, disponibilidade, forma, caixa, saúde financeira, poder institucional e reputação persistida. A avaliação de atletas não cria identidades. A escalação automática seleciona somente atletas disponíveis do clube, reutiliza `player_positions` e rejeita elencos abaixo de 11. A tática é derivada da personalidade e sofre contenção quando o contexto institucional é baixo.

O ciclo semanal produz treino, mercado, tática, prioridade de competição, plano de janela e escalação. O mesmo seed e clube retornam a decisão persistida, evitando duplicidade. Propostas de contratação, venda, renovação e evolução de departamento são decisões explicáveis; qualquer mutation efetiva continua delegada aos serviços econômicos e esportivos autorizados.

A priorização pode seguir um objetivo `COMPETITION:<id>` ativo e o calendário existente. Reputação é calculada somente quando suas colunas estão persistidas. A validação final cobriu banco isolado, determinismo por seed, 1.000 diagnósticos abaixo do limite de desempenho, limites econômicos, escalação automática e jogador inexistente.
