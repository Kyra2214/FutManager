# Auditoria da liga principal

A consulta foi executada em modo somente leitura sobre `career_parallel_fixtures` no GameState. A carreira ativa com quatro divisões de 20 clubes possui 380 partidas por divisão (20 × 19), totalizando 1.520 partidas por temporada (4 × 380). Cada clube disputa 38 partidas na temporada, sendo 19 como mandante e 19 como visitante.

O total bruto de 3.880 registros observado inicialmente misturava três carreiras persistidas no mesmo GameState: uma carreira antiga com 15 clubes por divisão (840 partidas no total) e duas carreiras com 20 clubes por divisão (1.520 cada). A consulta do frontend já filtra a carreira ativa; portanto, o número correto da carreira de 80 clubes é 1.520, não 3.880.

O erro da seção Time tinha outra origem: a renderização chamava `workspace?.squad.players.length`, protegendo o objeto `workspace`, mas não o array `players`. Em estados de carregamento, ausência ou resposta parcial, isso produzia `Cannot read properties of undefined (reading 'length')`. A renderização foi normalizada para `(workspace?.squad.players ?? [])`, e os acessos equivalentes de comissão, departamentos e scouting também receberam fallback vazio.

## Regra de contagem

| Escopo | Quantidade |
|---|---:|
| Clubes por divisão | 20 |
| Partidas por divisão (ida e volta) | 380 |
| Divisões | 4 |
| Partidas por temporada | 1.520 |
| Partidas por clube | 38 |
| Partidas do clube em casa | 19 |
| Partidas do clube fora | 19 |

A fonte da verdade permanece o GameState SQLite; nenhum número foi inventado ou gravado pelo frontend.
