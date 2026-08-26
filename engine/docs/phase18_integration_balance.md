# Fase 18 — Integração Geral e Balanceamento

A Fase 18 adiciona o coordenador global sem criar nova fonte de verdade. `data/state/game.db` continua sendo o estado mutável e `data/database/game.db` continua protegido como banco-base.

## Ordem oficial do tick

O `GlobalIntegrationOrchestrator` registra e executa a sequência: relógio, contratos, obrigações, recuperação, lesões, treinamento, desenvolvimento, fadiga, forma, competições, partidas, estatísticas, classificação, estádio, torcida, mídia, patrocínios, receitas, finanças, IA dos clubes, mercado, carreira dos managers e auditoria.

O coordenador não reimplementa as regras de domínio. Ele registra a ordem, contexto temporal, status, seed, falhas e auditoria. O mesmo `tick_id` retorna `ALREADY_PROCESSED`.

## Consistência e balanceamento

`ConsistencyService` valida integridade SQLite, foreign keys, jogadores duplicados, partidas duplicadas, anomalias financeiras e público acima da capacidade. `BalanceConfig` concentra vantagem de casa, forma, condição, fadiga, comissão, estrutura, taxa de gols, risco de lesão e variação máxima de reputação.

## Recuperação e limites

Ticks possuem status `RUNNING`, `COMPLETED` ou `ROLLED_BACK`, com erro registrado. Índices são criados para ticks, auditoria e partidas pendentes. O sistema continua offline, transacional e auditável.

A etapa não reescreve os serviços de partidas, mercado, finanças ou carreira. A integração automática de todas as operações de domínio em cada etapa do tick ainda requer adaptadores adicionais; o coordenador atual fornece o contrato, a ordem e a auditoria global sem simular operações que não foram solicitadas.
