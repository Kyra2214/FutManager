# P1-6 / passos 119–120 — Confirmação de escalação

Foi criada a tabela `lineup_confirmations` e o comando `confirm_lineup`. A confirmação verifica que a escalação pertence ao clube, possui pelo menos 11 titulares, contém apenas atletas disponíveis e, quando uma partida é fornecida, que o fixture pertence à competição e envolve o clube.

A operação é idempotente por chave de clube, competição, escalação e partida e registra a decisão `LINEUP_CONFIRMED` no histórico tático. O teste focado confirmou repetição idempotente e rejeição de escalação com atleta lesionado.
