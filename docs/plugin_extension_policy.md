# Política de extensão por plugins internos

Plugins internos podem ampliar consultas, relatórios e adaptadores do FutManager, mas não podem criar uma fonte de estado concorrente. O único estado esportivo, financeiro, social e de carreira continua no SQLite/GameState.

| Extensão permitida | Regra de segurança |
|---|---|
| Consulta read-only | Pode ler por repository/serviço aprovado e retornar JSON serializável. |
| Novo comando de domínio | Deve ser método de serviço, receber contexto e `managed_transaction`, passar pelo gateway e ter teste de sucesso, erro, rollback e idempotência. |
| Novo contrato tRPC | Deve apontar para uma ação existente no gateway; não pode executar SQL diretamente no React. |
| Relatório derivado | Deve ser calculado a partir de uma leitura persistida, sem ser salvo como estado paralelo. |
| Migração de esquema | Deve ser idempotente, versionada e aplicada apenas ao GameState mutável. |

É proibido que um plugin abra o banco-base para escrita, mantenha cache que substitua o GameState, invente entidades, altere regras no frontend ou contorne o `RoadmapGate`. A inclusão de qualquer plugin exige revisão de dependências, teste automatizado, auditoria de caminhos de mutação e evidência no manifesto do gate.
