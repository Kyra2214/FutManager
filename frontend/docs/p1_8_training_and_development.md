# P1-8 — Centro de Treinamento e Evolução

O Front P1-8 recebeu um serviço canônico de treinamento em `engine/sports/training.py`. O serviço inventaria os quatro departamentos persistidos, limita níveis a 10, calcula orçamento de próxima evolução e registra a evolução no histórico do CT. A manutenção semanal continua sincronizada com `club_payroll_profiles` e `club_economic_state` pelo serviço econômico existente.

Planos semanais são persistidos por clube, temporada e semana, com idempotência. Cada sessão registra carga, dias de recuperação, risco de lesão e status; atletas com lesão ativa são bloqueados para planos que não sejam descanso. O risco considera carga, fadiga, lesão e bônus médico persistidos. O relatório individual deriva potencial, forma, condição, fadiga, carga planejada e diferença entre potencial e desempenho.

O gateway e o router tRPC expõem inventário, orçamento, alertas de manutenção, desenvolvimento e criação de plano. A aba CT passou a mostrar inventário de treinamento e quantidade de atletas disponíveis para desenvolvimento, sem criar dados fictícios ou estado paralelo no cliente.

A cobertura inclui teste de idempotência de plano, bloqueio de lesão, risco, bônus médico, manutenção ausente, orçamento e relatório de evolução.
