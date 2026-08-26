# Comissão técnica — contrato canônico 521–530

As operações de comissão técnica são persistidas no GameState mutável e executadas pelo `StaffMarketService`. A interface deve solicitar uma prévia e uma aprovação explícita antes de contratar; nenhuma regra de salário, caixa, afinidade ou disponibilidade é calculada no frontend.

| Operação | Fonte persistida | Writer autorizado | Regra principal |
|---|---|---|---|
| Prévia de contratação | `staff_members`, `staff_hire_proposals` | `preview_staff_hire` | Não contrata; cria proposta auditável e retorna salário, multa e afinidade. |
| Aprovação | `staff_hire_proposals`, `staff_contracts` | `approve_staff_hire` | Requer confirmação booleana; é idempotente por status da proposta. |
| Alteração de função | `staff_members`, `staff_role_history` | `change_staff_role` | Preserva a função anterior e exige referência natural. |
| Avaliação | `staff_evaluations` | `evaluate_staff` | Score persistido entre 0 e 100 com data e observação. |
| Ausência | `staff_absences` | `schedule_staff_absence` | Vigência e motivo são explícitos; duplicidade é bloqueada. |
| Histórico | `staff_history` | `list_staff_history` | Leitura ordenada por data e identificador, filtrada pelo clube. |

A rescisão existente permanece transacional e lança a multa no `FinanceLedger`. A substituição de staff continua composta pela rescisão e contratação existentes; uma futura extensão deve adicionar vigência explícita em `staff_replacements` sem alterar retroativamente contratos encerrados.
