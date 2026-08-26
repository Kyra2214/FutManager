# Validação da integração frontend–backend

O dashboard consulta o procedimento `club.workspace`, que abre o SQLite do motor em modo somente leitura. Com a carreira ativa de **Kyra** no **Flamengo**, a interface mostrou o clube, o escudo original, o Maracanã e o elenco persistido de 32 jogadores, incluindo 19 titulares e 13 reservas.

As tabelas de caixa, reputação, estádio detalhado e CT ainda não têm registros para o Flamengo. Em vez de preencher dados ilustrativos, o frontend apresenta essas ausências de modo explícito. As visões de competições, agenda e resultados continuam ligadas ao procedimento `matches.dashboard`, também em leitura direta.

As telas **Seu Clube**, **Time**, **Estádio** e **CT** foram verificadas em desktop e em viewport móvel de 375 × 812 px. A suíte contém 26 testes cobrindo a leitura SQLite, os ativos, a carreira, os contratos de dados, o componente de início e a integração tRPC em banco temporário.
