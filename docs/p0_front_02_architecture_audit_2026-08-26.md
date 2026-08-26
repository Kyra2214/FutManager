# Auditoria do Front P0-2 — Arquitetura do motor

## Escopo e decisão

A auditoria executável `scripts/validate_p0_architecture.py` verificou dez contratos arquiteturais reais entre o motor, o gateway e a política do projeto. O resultado foi `VALID`, sem arquivos ausentes ou tokens ausentes, e os testes específicos de execução/orquestração retornaram **8 aprovados**.

| Contrato | Evidência |
|---|---|
| Catálogo de erros | `engine/core/domain_errors.py` e `tests/test_execution_contracts.py` |
| Contexto de execução | `engine/core/execution.py`, com temporada, semana, seed e escopo |
| Gate e dependências | `engine/core/roadmap_gate.py` e `tests/test_roadmap_gate.py` |
| Proteção de estado | `engine/core/state_store.py` e guardas dos writers |
| Orquestração semanal | `engine/world/orchestrator.py`, auditoria e `managed_transaction` |
| Simulação em lote | `engine/world/simulation.py`, auditoria e idempotência |
| Contrato do gateway | `scripts/career_gateway.py`, `run`, choices e delegação a serviços |
| Separação de testes | `tests/test_execution_contracts.py` e `tests/test_career_gateway.py` |
| Política de fonte única | `docs/roadmap_execution_policy.md` |
| Validação executável | `scripts/validate_p0_architecture.py` |

## Limite de consolidação

Esta auditoria comprova a fundação arquitetural observada, mas **não marca o Front P0-2 como CONSOLIDATED**. Ainda faltam critérios item a item para os 20 passos do roadmap, especialmente limites operacionais de lotes, cancelamento seguro, relatório automatizado de dependências circulares, pontos de extensão por plugins e suíte de contratos compartilhados Python/TypeScript. O `roadmap_gate.json` permanece com Front P0-2 `PENDING`, e P0/P1/P2 seguem governados sem liberação indevida.
