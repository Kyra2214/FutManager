# Contrato do ciclo semanal mundial

## Fonte de verdade e chave de processamento

O ciclo é executado sobre uma única conexão SQLite do banco de estado. A tabela `weekly_world_runs` terá unicidade por `season`, `week` e `scope`, com `scope='WORLD'`. Uma repetição retorna `ALREADY_PROCESSED` sem repetir partidas, receitas, folha, missões ou movimentações de caixa.

## Ordem determinística

1. Criar o contexto semanal a partir de `logical_clock`, usando seed opcional.
2. Processar partidas agendadas até a data do contexto, em ordem de `match_date, match_id`.
3. Atualizar estatísticas, forma, torcida e reputações a partir dos resultados persistidos.
4. Registrar público e bilheteria apenas para mandantes de partidas efetivamente jogadas.
5. Registrar premiações somente para competições que tenham encerramento verificável.
6. Atualizar progresso de missões comerciais por eventos persistidos.
7. Processar receitas de patrocínio, folha do elenco, staff e manutenção.
8. Recalcular perfis institucionais, registrar auditoria e avançar o relógio.

## Garantias

| Garantia | Regra |
|---|---|
| Idempotência | `weekly_world_runs` e as chaves únicas do `financial_ledger`, `attendance_records`, `simulation_audit` e `sponsor_weekly_runs` impedem duplicação. |
| Ledger | Toda receita ou despesa possui `source_type`, `source_id`, semana e clube. |
| Caixa | O saldo econômico é atualizado pelo mesmo lançamento que entrou no ledger. |
| Rollback | Falhas na execução deixam a execução semanal com status `ROLLED_BACK`; serviços vinculados recebem a mesma conexão e evitam commits intermediários. |
| Determinismo | A seed é registrada no run e derivada por partida quando não for fornecida. |
| Auditoria | O resumo de cada etapa, contagens e seed ficam em `weekly_world_audit`. |

## Limites desta etapa

Transferências continuam a ser tratadas pelo serviço próprio e não são iniciadas automaticamente pelo tick. O ciclo apenas consome transferências já concluídas e seus efeitos persistidos. Não há geração de clubes, jogadores, resultados ou receitas pelo frontend.
