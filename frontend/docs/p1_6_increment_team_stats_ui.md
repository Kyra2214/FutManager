# Incremento P1-6 — Produção individual na aba Seu Clube

A tela inicial passou a consultar `matches.playerStats` por tRPC e exibir uma faixa de atletas em destaque com gols, assistências, minutos, cartões, aparições e avaliação média. A interface não mantém cópia local das estatísticas: todos os valores vêm do contrato somente leitura do GameState.

O componente diferencia carregamento, erro e ausência de registros persistidos. A consulta usa entrada memoizada pela competição selecionada para evitar reconsultas instáveis. Typecheck e os testes de engineState, workspace e início de carreira passaram em 6 casos.

A tela dedicada de elenco ainda pode ganhar filtros e paginação em um próximo incremento.
