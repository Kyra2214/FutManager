# Lote P1 1191–1200 — Revogação

O contrato de revogação do domínio 03 foi implementado no GameState SQLite com dez contratos, validação de estado, persistência idempotente por chave, hash SHA-256 do payload, leitura read-only, índice por carreira, entidade e status, auditoria e proteção de mutações pelo `AUTHORIZED_SQL_SERVICE`.

O `ManagerService` inicializa as tabelas e o `career_gateway.py` expõe contratos, estado, validação, persistência, proteção e auditoria. O lote depende de 1190, que estava consolidado antes desta implementação. Foram aprovados nove testes focados combinando revogação, escopo e convite, além da compilação Python do contrato, ManagerService e gateway.
