# Ciclo de vida dos jogadores

O estado de carreira fica em `data/state/game.db`, separado da fonte `data/database/game.db`. A tabela `player_career_state` preserva `player_id`, `career_id`, `generation`, idade, status, clubes de nascimento/carreira/atual, potencial, força e temporadas fora.

Os estados suportados são `YOUTH`, `ACTIVE`, `RETIRING`, `RETIRED` e `RETURNED`. A aposentadoria é explícita e remove apenas o clube atual; a identidade e os eventos permanecem registrados.

Depois de pelo menos uma temporada fora, `return_generation` cria uma nova carreira para a mesma identidade histórica, com geração incrementada, idade inicial de 16 anos, novo potencial reproduzível por seed e clube inicial independente do clube anterior. Isso não é ressurreição literal nem reutilização do mesmo personagem ativo.

A progressão de idade está disponível por `age_player`, mas o avanço automático de temporadas ainda não existe. Não são geradas partidas, resultados, mercado, IA ou simulação global.
