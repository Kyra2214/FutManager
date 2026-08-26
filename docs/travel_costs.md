# Custos de viagens

O FutManager registra custos de deslocamento no `FinanceLedger`, usando a categoria `TRAVEL` e referências naturais por `match_id`. O visitante é o único clube cobrado; partidas como mandante retornam `HOME_NO_TRAVEL`.

A classificação logística usa os países persistidos em `times.pais_id`. Os valores padrão ficam na tabela canônica `travel_cost_configs`: **R$ 25.000** para rota doméstica e **R$ 100.000** para rota internacional. Esses valores são configuráveis no banco e não são calculados no frontend.

A prévia (`travel_preview`) é somente leitura e informa rota, custo, moeda, disponibilidade e `persisted: false`. O lançamento ocorre no processamento oficial da partida dentro do ciclo semanal, com `INSERT OR IGNORE` no ledger para garantir idempotência. Quando existe estado econômico do clube, o caixa canônico `club_economic_state` é debitado na mesma transação; se o estado econômico ainda não estiver inicializado, o lançamento contábil permanece auditável sem criar saldo paralelo.

O gateway Python expõe `travel_preview` e `travel_summary`. O router tRPC disponibiliza `matches.travelPreview` e `matches.travelSummary`. A área de partidas mostra a previsão logística do próximo compromisso e o acumulado sazonal retornado pelo motor.
