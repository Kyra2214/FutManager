# Pesquisa de memberships oficiais

Em 27/08/2026 foram consultadas duas fontes oficiais. A página da Premier League confirma a temporada 2026/27 e oferece a tabela oficial: https://www.premierleague.com/en/tables/premier-league/2026-27/all-matchweeks.

A página oficial da Bundesliga confirma a seção de clubes da temporada 2026–2027 e lista Bayern Munich, Borussia Dortmund, RB Leipzig, VfB Stuttgart, Hoffenheim, Bayer Leverkusen, Freiburg, Eintracht Frankfurt, Augsburg, Mainz, Union Berlin, Borussia Mönchengladbach, Hamburg, Cologne, Werder Bremen, Schalke, Elversberg e Paderborn: https://www.bundesliga.com/en/bundesliga/clubs.

Essas fontes servem como referência de temporada e nomenclatura. A persistência só deve ocorrer após resolver cada nome contra `times` e confirmar escudo válido no GameState; nomes sem correspondência não serão inventados nem inseridos.
A página oficial da Ligue 1 lista os clubes da competição e os links oficiais de cada equipe, incluindo Angers, Auxerre, Monaco, Brest, Lorient, Le Havre, Lille, Nice, Lyon, Marseille, Paris FC, PSG, Lens, Rennes, Strasbourg e Toulouse: https://ligue1.com/en.

A página consultada da Federação Turca de Futebol (TFF) é a fonte institucional para a classificação da primeira divisão turca: https://www.tff.org/Default.aspx?pageID=449. A renderização da página foi limitada no navegador, então nenhum nome turco será persistido sem resolver a lista diretamente contra o SQL e validar a fonte/temporada.

## Importações concluídas nesta correção

A fonte oficial da Bundesliga 2026/27 foi mapeada ao país SQL `3` (Alemanha) e a fonte oficial da Ligue 1 2026/27 ao país SQL `72` (França). O resolver canônico encontrou 18/18 clubes em cada fonte, sem nomes não correspondentes ou ambiguidades; a função de inicialização persistiu os vínculos na tabela `first_division_membership` do GameState. Inglaterra, Argentina e Turquia continuam como pools SQL elegíveis, mas aguardam fonte oficial com lista integralmente mapeável antes de serem classificados como membership oficial.

## Fontes adicionais consultadas

A página oficial da Premier League publicou os clubes da temporada 2026/27 em 20/08/2026, incluindo Arsenal, Aston Villa, Bournemouth, Brentford, Brighton, Chelsea, Coventry, Crystal Palace, Everton, Fulham, Hull, Ipswich, Leeds, Liverpool, Manchester City, Manchester United, Newcastle, Nottingham Forest, Sunderland e Tottenham: https://www.premierleague.com/en/news/4672981/premier-league-club-kits-for-202627-season. A página oficial da AFA confirmou para 2026 duas zonas de 15 clubes da Liga Profesional, totalizando 30 entidades, com seus nomes publicados na matéria: https://www.afa.com.ar/fixture/posts/se-realizo-el-sorteo-de-la-liga-profesional-2026-ya-se-conocen-los-grupos-del-torneo-apertura-y-torneo-clausura. A página oficial da TFF confirmou o contexto da temporada 2026/27, mas a extração consultada não exibiu a lista integral da Süper Lig; por isso, Turquia permanece como pool SQL e não é classificada como membership oficial até haver matching completo.
