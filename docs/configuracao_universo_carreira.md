# Configuração do universo da carreira

A primeira tela da carreira agora coleta uma lista de países participantes antes de liberar o início do save. A seleção é enviada pelo procedimento `career.start` como `selectedCountryIds` e é validada pelo motor Python; o frontend não calcula país, divisão ou elegibilidade.

## Regra de início

Toda carreira iniciada com clube grava `starting_division = 4` em `manager_careers` e em `career_world_configs`. O `career_world_configs` representa o universo combinado, com `combined_name` formado pelos países selecionados na ordem escolhida. A leitura oficial `career.current` retorna `startingDivision`, `selectedCountryIds`, `selectedCountries` e `combinedLeagueName`.

O motor também verifica que o país do clube escolhido está entre os países participantes. Caso contrário, a criação é rejeitada com `TARGET_COUNTRY_NOT_SELECTED`. A seleção precisa conter pelo menos um país; o catálogo tRPC é `career.worldCountries` e usa os países com clubes existentes no GameState.

## Persistência

`career_world_configs` mantém a configuração principal por carreira. `career_world_countries` mantém a relação sem duplicidade entre save e país, incluindo o nome e o código observados no momento da criação. O GameState SQLite continua sendo a única fonte da verdade; snapshots incluem a configuração por estar relacionada à carreira e a coluna `starting_division`.

Os IDs canônicos priorizados no catálogo são Brasil (`29`), Itália (`104`) e Espanha (`65`), porque são o cenário de seleção mais comum desta configuração. Os nomes são derivados do cadastro do motor quando disponível e possuem fallback controlado para esses IDs históricos quando a base-mãe ainda contém rótulos genéricos.

## Próxima integração do motor

A configuração já está persistida e disponível para o compilador de competições. A etapa seguinte deve materializar as quatro divisões e os entries/calendário do universo combinado consumindo `career_world_configs` e `career_world_countries`, sem mover essa regra para React ou tRPC.
