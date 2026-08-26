# Incremento P1-6 — Aplicação de substituição planejada

O GameState agora permite aplicar uma substituição planejada a partir do minuto-alvo. A operação valida que o plano existe, que o minuto está entre o alvo e 120, que o atleta de saída ainda é titular e que o atleta de entrada não está na escalação. Em uma transação única, o titular de saída passa a reserva efetiva, o atleta de entrada assume sua posição e o plano recebe status `APPLIED` e minuto aplicado.

A reaplicação de um plano já aplicado é idempotente e retorna o mesmo registro, sem inserir nova linha na escalação. A cobertura focada passou em 9 testes, incluindo formação, escalação automática, estatísticas, substituições planejadas e aplicação efetiva.

A atualização automática de minutos individuais após a substituição e a derivação de cartões a partir de eventos continuam como próximos incrementos do Front P1-6.
