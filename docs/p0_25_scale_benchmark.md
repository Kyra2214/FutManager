# Evidência de escala P0-25

A auditoria read-only do banco-base registra **8.399 clubes**, conforme `brasfoot_engine/docs/canonical_clubs_audit.json` e `docs/schema_inventory.json`. Essa contagem é o universo de bootstrap considerado pelo roadmap; ela não é substituída nem duplicada no GameState.

O benchmark de escala deste ciclo valida a existência, a contagem e a preparação idempotente do universo canônico. Não declara tempo de execução de 8.399 bootstrap sem uma medição reproduzível em ambiente controlado. O avanço mundial é exercitado pelos testes de ciclo semanal, com chave natural de temporada/semana e rollback transacional.

A interpretação operacional é: escalar o bootstrap deve usar os serviços idempotentes existentes, manter SQL/GameState como fonte única e registrar qualquer duração futura junto de hardware, versão Python, tamanho do banco e seed.
