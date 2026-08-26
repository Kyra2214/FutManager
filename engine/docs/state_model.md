# Modelo de estado

`data/database/game.db` é a fonte inicial do universo e permanece imutável durante esta etapa. `data/state/game.db` é a cópia mutável utilizada pela carreira.

A camada de consulta continua sob demanda: jogadores e times são materializados somente quando solicitados pelos repositórios ou pelo Player Engine. A tabela original `jogadores` representa o universo; `player_career_state` representa carreiras ativas, aposentadas ou retornadas.

As transações são controladas por `CareerStateStore.transaction`. Operações de criação, envelhecimento, aposentadoria, retorno e atualização de temporadas fora executam commit em sucesso e rollback quando ocorre uma exceção.

`career_events` registra eventos de carreira em formato estruturado. `audit_log` fornece rastreabilidade compacta das alterações importantes. `StateBackupService` cria snapshots dentro de `data/state/backups` e nunca utiliza o banco-base como arquivo de save.
