# P2-16 — Scouting e base

O scouting utiliza `scout_missions`, `scout_opportunities` e `scout_reports` como estado canônico. Missões têm região, duração, custo, prioridade, filtros de posição/idade/força/potencial, seed e ciclo de vida. A descoberta é separada da contratação: uma oportunidade só muda para `CONFIRMED` após aprovação explícita do manager.

Regiões habilitadas e multiplicadores de custo são persistidos em `scout_regions`. Relatórios são criados ao fim do prazo da missão, com resultados determinísticos pela seed. A comparação confronta a observação com o registro atual em `jogadores`, sem fabricar atributos quando a fonte não os oferece; nesses casos o texto persistido informa a ausência.

A base utiliza `academy_players` somente para atletas que já existem em `jogadores`. O ciclo suporta matrícula, custo de manutenção, progresso limitado a 100, estado `READY` e promoção aprovada para o vínculo profissional/reserva. A manutenção pode ser consultada por clube.

Foram validados filtros, prazo de missão, seed repetida, relatório persistido, separação descoberta/contratação, confirmação do manager, progressão da base e compilação/gateway. O módulo permanece compatível com bancos legados por migração aditiva de colunas.
