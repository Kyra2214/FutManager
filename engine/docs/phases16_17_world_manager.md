# Fases 16 e 17 — Simulação mundial e carreira humana

O motor agora possui `WorldSimulationService` para processar partidas pendentes em lotes sem carregar o mundo inteiro em memória. Os níveis `FULL`, `STANDARD`, `FAST` e `ABSTRACT` ficam registrados por tick, e partidas envolvendo um clube prioritário podem receber nível `FULL`.

Cada lote possui identificador de simulação, seed, data lógica, quantidade solicitada, quantidade processada, status e auditoria por partida. Repetir o mesmo tick retorna `ALREADY_PROCESSED`. Os resultados são delegados ao `MatchEngine` existente, sem criar um motor paralelo.

A carreira humana possui manager, carreira ativa, clube atual único, contrato próprio, objetivos, histórico, caixa de entrada e renúncia. A persistência ocorre em `data/state/game.db`; ao reabrir o banco, as entidades podem ser reconstruídas do SQL.

A camada de manager não escala jogadores automaticamente, não cria dinheiro e não substitui a decisão humana. Formação, treinamento, scouting, mercado, finanças e estrutura continuam usando os serviços oficiais.

## Limitações

A simulação mundial ainda processa partidas existentes e não cria calendário universal nem IA autônoma para todos os clubes. Não há frontend, multiplayer, internet, carreira humana visual, mercado automático completo ou simulação mundial detalhada de todas as ligas.
