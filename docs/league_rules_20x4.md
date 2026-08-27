# Regra de ligas e seleção de clubes

A configuração com **um país** preserva a competição nacional e o calendário original. Quando o clube escolhido pertence à primeira divisão oficial importada, ele é reposicionado para a quarta divisão da carreira; a competição nacional não é transformada em liga paralela.

A configuração com **dois ou mais países** cria uma competição paralela com capacidade fixa de **80 clubes**, distribuídos em quatro divisões de **20 clubes cada**. O motor prioriza os clubes de primeira divisão com membership oficial resolvido. Se a soma não alcançar 80, completa as vagas com outros clubes canônicos do SQL que tenham nome não vazio e escudo principal ou mini escudo vinculado. Nenhum placeholder ou clube fictício é criado.

O clube escolhido pode pertencer a qualquer país, inclusive a um país que não esteja entre as ligas selecionadas. Nesse caso, ele é incluído na competição paralela e continua posicionado na quarta divisão. A seleção de país não funciona como restrição de nacionalidade do manager.

O catálogo de clubes retorna somente entidades com nome e ativo de escudo válidos. Países com nomenclatura oficial conhecida e pelo menos 20 clubes com escudo válido podem ser usados como pool SQL; países sem nome oficial ou sem dados suficientes permanecem ocultos até uma importação verificável.

## Evidências

- Motor: `engine/manager/career.py`, métodos `_eligible_clubs`, `preview_parallel_league` e `_materialize_parallel_league`.
- Dispatcher: `scripts/career_gateway.py`, filtro SQL do catálogo de clubes.
- Frontend: `client/src/pages/CareerStart.tsx`, sem bloqueio por país, prévia 20×4 e estados editoriais.
- Testes: `tests/test_career_selection_rules.py` e `tests/test_parallel_career_league.py`.
- Fontes consultadas: [Premier League](https://www.premierleague.com/en/tables/premier-league/2026-27/all-matchweeks), [Bundesliga](https://www.bundesliga.com/en/bundesliga/clubs), [Ligue 1](https://ligue1.com/en) e [TFF](https://www.tff.org/Default.aspx?pageID=449).
