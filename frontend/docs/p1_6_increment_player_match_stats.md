# Incremento P1-6 — Estatísticas individuais por partida

O serviço esportivo reutiliza a tabela canônica `player_match_stats` para registrar minutos, gols, assistências, cartões e avaliação do atleta. O comando `record_player_match_stats` valida identificadores, limita minutos a 120, rejeita valores negativos e aceita avaliação entre 0 e 10.

A chave `(match_id, player_id)` garante upsert idempotente: uma nova apuração da mesma participação substitui o registro lógico anterior, sem linhas duplicadas. A leitura `player_match_stats` ordena por atleta e permanece no GameState.

A cobertura focada passou em 8 testes, incluindo persistência, substituições, escalação automática, formações por competição, lesão e determinismo de partidas. Integração automática dessas estatísticas ao motor de partidas permanece como próximo passo.
