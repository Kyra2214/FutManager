# Disponibilidade de dados SQL — carreira Flamengo

| Área | Tabela ou serviço existente | Registros para o Flamengo | Situação na interface |
| --- | --- | ---: | --- |
| Elenco | `jogadores` + `jogador_time` | 32 jogadores | Integrado com nome, posição, idade, CR1/CR2, lado, categoria, titularidade, estrela e topo mundial. |
| Lesões | `injuries` | 0 | Integrado; a interface mostra zero lesões ativas. |
| Comissão | `staff_members` | 0 | Integrado; CT informa que ainda não há profissionais persistidos. |
| Auxiliares | `staff_members.role = 'auxiliar'` | 0 | Estrutura disponível, sem registros. |
| Médicos | `staff_members.role = 'medico'` | 0 | Estrutura disponível, sem registros. |
| Scouts | `staff_members.role = 'scout'` | 0 | Estrutura disponível, sem registros. |
| Departamentos | `club_departments` | 0 | Estrutura disponível, sem registros. |
| Missões de scouting | `scout_missions` | 0 | Estrutura disponível, sem registros. |
| Oportunidades e relatórios | `scout_opportunities` + `scout_reports` | 0 | Estrutura disponível, sem registros. |

O motor já fornece os serviços de comissão (`engine/staff`) e scouting (`engine/scouting`). A próxima evolução deve criar os profissionais e departamentos por regras explícitas do motor; nenhum membro de comissão, médico ou scout foi inventado no frontend.
