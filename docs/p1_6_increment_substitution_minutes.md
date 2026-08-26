# Incremento P1-6 — Minutos pós-substituição

`apply_substitution` aceita agora um `match_id` opcional. Quando informado, a mesma transação atualiza `player_match_stats`: o atleta de saída recebe os minutos transcorridos até a substituição e o atleta de entrada recebe o restante até 120 minutos, usando a chave canônica `(match_id, player_id)`.

A reaplicação de um plano já aplicado continua idempotente e não reprocessa os minutos. O comportamento legado sem `match_id` permanece compatível. A cobertura focada passou em 9 testes, incluindo persistência, escalação efetiva e atualização de minutos.

A integração de cartões derivados de eventos e a composição completa de minutos em prorrogação continuam pendentes.
