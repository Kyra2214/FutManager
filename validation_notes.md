# Validação de Nossas Partidas

## Estado verificado

- A consulta `matches.dashboard` alcança o SQLite de estado em modo somente leitura.
- Em 26 de agosto de 2026, o banco real não contém temporadas, competições, fixtures, partidas ou estatísticas de competição persistidas.
- A aba **Competições** informa esse vazio real com a fonte SQL conectada.
- A aba **Tabela** mantém a estrutura de classificação e informa a ausência de competições, sem preencher clubes ou resultados fictícios.
- A aba **Calendário** informa que não existem partidas agendadas e esclarece a ausência de clube controlado no estado atual.
- A aba **Resultados** preserva o histórico vazio e não calcula forma ou placares que não existam no motor.
- A suíte de testes renderiza cada uma das quatro visões com uma consulta simulada em andamento e confirma o feedback de carregamento específico.
