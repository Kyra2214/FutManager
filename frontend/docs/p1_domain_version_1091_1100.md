# Lote P1 1091–1100 — versão do domínio 02

O ciclo de versão do domínio 02 foi persistido em `roadmap_p1_domain_versions`, no mesmo GameState SQLite do motor. Os dez itens usam a versão semântica `1.0.0`, ações canônicas, JSON determinístico, estado `CONSOLIDATED`, índices e auditoria de mutações.

A validação confirma IDs 1091–1100, domínio 02, nome `domain_02`, versão semântica e fonte `SQL_GAMESTATE`. A leitura é somente leitura e qualquer mutação exige o serviço SQL autorizado. Evidências: `engine/core/p1_domain_version_contract.py`, `engine/manager/career.py`, `scripts/career_gateway.py` e `tests/test_p1_domain_version_contract.py`.
