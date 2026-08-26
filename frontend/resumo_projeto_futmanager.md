# Resumo consolidado — FutManager / Brasfoot

**Estado do projeto:** funcionalmente integrado ao motor Python/SQLite, com carreira ativa de **Kyra no Flamengo**, economia semanal, mercado de profissionais, CT e patrocínios comerciais persistidos.

## 1. Base de dados e engenharia reversa

O arquivo-mãe foi analisado e seus dados foram normalizados para SQLite. Jogadores, clubes, seleções, vínculos de elenco, atributos, escudos e camisas foram preservados com identificadores oficiais. A fonte mutável do jogo é `brasfoot_engine/data/state/game.db`; o banco-base permanece imutável.

| Área | Entrega atual |
|---|---|
| Jogadores | Entidade canônica, idade, posição, CR1/CR2, lado, categoria, titularidade, estrela e topo mundial. |
| Clubes e seleções | IDs oficiais, país, vínculos de elenco e ativos visuais associados. |
| Ativos | Escudos e camisas extraídos e vinculados ao SQL; a interface usa fallback explícito quando o ativo não existe. |
| Carreira | Criação persistida de manager, escolha de clube ou seleção e bloqueio de carreira ativa duplicada. |

## 2. Frontend e integração real

O frontend React utiliza tRPC e consulta o SQLite do motor por contratos de leitura e por uma ponte Python para mutações. Não existe estado paralelo de elenco, profissionais, caixa ou patrocinadores no cliente.

| Tela | Situação |
|---|---|
| Seu Clube | Dashboard com Flamengo, Maracanã, escudo, elenco, caixa e leituras honestas de dados ausentes. |
| Nossas Partidas | Estrutura de competições, calendário, tabela e resultados ligada ao estado real; exibe vazio quando o motor ainda não possui os registros. |
| Time | Elenco real com atributos completos por jogador. |
| CT | Comissão, médicos, auxiliares, departamentos e atalhos ao Mercado quando não há profissional contratado. |
| Mercado | Catálogo persistido de profissionais, salários semanais e contratação. |
| Patrocinadores | Propostas, estrelas, overall institucional, contrato ativo e missões comerciais. |

## 3. Economia semanal

A fórmula provisória inicial foi substituída por uma adaptação auditável da lógica recuperada do arquivo-mãe. O salário é calculado individualmente por jogador a partir de força derivada de CR, divisão adaptada, país, idade, posição, estrela e topo mundial. A reserva inicial permanece em **39 semanas**, equivalentes a três quartos da temporada, para que receitas futuras tenham relevância.

| Componente | Regra atual |
|---|---|
| Caixa inicial | Folha semanal total multiplicada por 39 semanas. |
| Elenco | Salários individuais persistidos em `club_player_payrolls`. |
| Staff | Salário semanal por função, nível, reputação, potencial, poder do clube e fator do país. |
| CT | Compra com custo imediato e manutenção semanal. |
| Cobrança | Processamento mundial idempotente por clube, temporada e semana. |
| Segurança | Contratação de staff e atualização de folha são transacionais; rollback é coberto por teste. |

A economia foi inicializada de forma idempotente para **8.399 clubes**. A operação não contrata profissionais, não compra departamentos e não aceita patrocinadores automaticamente.

## 4. Profissionais e departamentos

O Mercado possui um catálogo persistido de treinadores, auxiliares, preparadores físicos, médicos e scouts. Cada profissional tem função, nível, reputação, potencial, especialização e salário semanal calculado pelo motor. A contratação atualiza o vínculo, o histórico e a folha do clube numa única transação.

Os departamentos de Base, Medicina, Preparação Física e Análise podem ser adquiridos e evoluídos do nível 1 ao 10. Cada oferta expõe custo, manutenção e capacidade antes da decisão.

## 5. Patrocinadores e missões comerciais

O sistema comercial é inspirado nos princípios de planejamento, metas e risco de F1 Manager, mas foi criado para o contexto de futebol e não usa marcas ou dados financeiros reais.

| Elemento | Implementação |
|---|---|
| Overall institucional | Elenco 60%, CT 25% e estádio 15%. Componentes ausentes ficam explicitamente identificados como base preparatória. |
| Estrelas | Patrocinadores de 1 a 5 estrelas, com sinal, receita semanal, bônus e exigências escalados. |
| Propostas | Três opções exclusivas por janela; expiram após três semanas sem escolha. A janela seguinte pode trazer qualidade maior ou menor. |
| Contrato | Seis semanas, com sinal imediato e receita semanal. Apenas uma proposta principal pode ficar ativa por vez. |
| Missões | Meta institucional, de CT ou de elenco; prazo, progresso, recompensa e falha persistidos. |
| Integração financeira | Receita de patrocínio e folha são processadas no ciclo econômico semanal, com lançamentos separados no ledger. |

No estado atual, o Flamengo possui overall institucional de aproximadamente **63,5**, elegibilidade de quatro estrelas e três ofertas reais pendentes. Nenhuma delas foi aceita automaticamente.

## 6. Qualidade e validação

| Verificação | Resultado mais recente |
|---|---|
| TypeScript | Compilação sem erros. |
| Frontend | 42 testes aprovados. |
| Motor Python | 13 testes aprovados para economia, overall institucional, patrocínios, gateway e ciclo mundial. |
| Build | Build de produção concluído. |
| Visual | Mercado, CT e Patrocinadores verificados em desktop e viewport móvel. |
| Checkpoint atual | `manus-webdev://0b463eee` |

## 7. Próximas etapas recomendadas

1. Conectar o avanço de calendário e partidas ao ciclo semanal mundial, para que folha, receitas, expiração de propostas e missões avancem junto da temporada.
2. Implementar receitas de bilheteria, premiações e patrocinadores secundários para complementar o orçamento da temporada.
3. Evoluir o estádio com capacidade, nível, eventos e receitas, substituindo a base preparatória atual por um score estrutural completo.
4. Ligar resultados esportivos, competições e desempenho de jogadores às missões comerciais e à reputação do clube.
