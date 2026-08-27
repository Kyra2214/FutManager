# Regras de fluxo da primeira página

## Uma liga selecionada

Quando o manager seleciona somente uma liga, o mundo permanece no fluxo nacional dessa liga. O motor não cria `career_parallel_leagues`, não redistribui a primeira divisão em quatro blocos e não gera um calendário paralelo. Se o clube escolhido pertence à primeira divisão oficial, o GameState registra em `career_national_reassignments` a mudança de divisão original 1 para divisão de carreira 4. As competições nacionais, seus clubes, calendários e simulações continuam preservados.

Se o clube escolhido não pertence à primeira divisão oficial, ele não sofre rebaixamento automático. A regra é aplicada pelo motor, não pelo React.

## Duas ou mais ligas selecionadas

Quando duas ou mais ligas são selecionadas, o motor cria uma competição paralela isolada. Todos os clubes oficiais da primeira divisão de cada país selecionado entram nessa competição; a quantidade é variável conforme a fonte, sem completar artificialmente para 20. A competição paralela recebe quatro divisões, fixtures e classificação próprios, enquanto as ligas nacionais de origem continuam ativas.

## Catálogo de países

A primeira página exibe nomes principais conhecidos pelo catálogo canônico, incluindo Brasil, Itália, Espanha, Portugal, Inglaterra, Alemanha, França, Argentina e Turquia. Um país só pode ser selecionado quando o GameState possui membership oficial de primeira divisão normalizado para ele. Países sem membership disponível aparecem identificados como pendentes e ficam desabilitados, evitando que o frontend crie ou suponha clubes.

> O catálogo externo serve apenas como entrada auditável de importação. Em runtime, o único estado consumido é o ID canônico persistido no GameState SQLite.
