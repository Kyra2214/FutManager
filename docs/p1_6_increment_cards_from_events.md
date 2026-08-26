# Incremento P1-6 — Cartões derivados de eventos

O `SportStateStore` agora expõe `sync_cards_from_events(match_id)`. A rotina lê exclusivamente `match_events` persistidos com tipos `YELLOW_CARD`, `RED_CARD` ou `CARD` e `player_id` presente, conta os eventos por atleta e atualiza o campo `cards` da tabela canônica `player_match_stats`.

A contagem é recomputada a partir dos eventos, portanto repetir a sincronização não soma cartões novamente. A tabela de eventos é inicializada de forma idempotente no armazenamento esportivo para permitir operação isolada e interoperável com o `MatchEngine`.

A cobertura focada passou em 10 testes, incluindo cartões, minutos, substituições e escalações. Eventos de cartão ainda precisam ser emitidos pelo motor de partida quando regras disciplinares forem implementadas.
