# Procedimento de recuperação de checkpoint

A recuperação deve ser feita a partir de um checkpoint versionado do projeto e de uma cópia do GameState. Nunca se deve sobrescrever `data/database/game.db`, pois ele é a base imutável auditada por manifesto.

## Sequência

Primeiro, selecionar o checkpoint no histórico do projeto e restaurar o código pelo Management UI. Em seguida, copiar `data/state/game.db` para um arquivo temporário fora da base original. O serviço deve abrir a cópia por `open_mutable_state`/`assert_mutable_state_path`, habilitar `PRAGMA foreign_keys=ON` e executar `PRAGMA integrity_check` e `PRAGMA foreign_key_check`.

Depois, executar o smoke test do gateway e os testes focados do módulo alterado. Se o checkpoint contiver um lote de simulação, consultar `simulation_ticks` e `simulation_checkpoints`; um tick já `COMPLETED` ou `CANCELLED` deve retornar `ALREADY_PROCESSED` quando repetido, sem duplicar auditoria. Em falha, descartar a cópia temporária e recomeçar do checkpoint anterior.

A restauração só é considerada válida quando integridade, foreign keys, manifesto do banco-base, typecheck, testes e build passam. O resultado deve registrar versão do checkpoint, hashes das cópias e data UTC. Nenhuma correção automática deve reconciliar saldo ou ledger; divergências são reportadas para decisão explícita.
