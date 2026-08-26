# Passos registrados no roadmap do FutManager

Este documento resume o conteúdo efetivamente registrado em `todo.md`. Os passos 371–470 possuem agora listas oficiais detalhadas e evidências de implementação. Os passos 471–500 ainda exigem detalhamento versionado antes de serem implementados; o marcador global de execução integral dos 500 passos permanece separado.

## Visão geral por frente

| Intervalo aproximado | Frente | Conteúdo registrado |
|---|---|---|
| 1–34 | Fundação e integração inicial | Navegação, aba Seu Clube, Nossas Partidas, dados reais de competições, escolha de clube/seleção, escudos, ativos, persistência de carreira, integração inicial frontend/backend e pacote ZIP. |
| 35–44 | Elenco, CT e estados vazios | Leitura de elenco, comissão, saúde e scouting; integração de Time, CT e Mercado; mensagens e atalhos quando faltam profissionais ou departamentos. |
| 45–60 | Staff, CT e economia inicial | Catálogo de profissionais, contratação, salários, departamentos, fórmula de caixa, projeção semanal, adaptação da fórmula do arquivo-mãe, reserva de 39 semanas, cobrança semanal e rollback. |
| 61–68 | Patrocinadores | Ofertas de 1–5 estrelas, expiração e substituição, overall institucional, missões, elegibilidade, contratos persistidos e interface tRPC responsiva. |
| 69–86 | Orquestração, estádio, torcida e receitas | Tick semanal idempotente, StadiumService, níveis 1–10, torcida, reputação, público, preço de ingresso, bilheteria, premiações, missões comerciais, alertas e entrega ZIP. |
| 87–108 | Roadmap, governança e auditorias | Documento de 500 passos, prioridades P0/P1/P2, gate P0, SQL/GameState como fonte única, auditores read-only, validação tRPC, hashes, ZIP e documentação operacional. |
| 109–167 | Governança P0 e migrações | Guarda de roadmap, schema_versions, índices, inventário e comparação de esquemas, proteção do banco-base, dependências, contexto serializável, erros de domínio, charter e consolidação de fronts P0. |
| 168–200 | Auditorias P0 | Auditorias de contratos, transações, SQLite, jogadores, clubes, partidas, competições, calendário, torcida, patrocínios, simulação mundial, economia e integridade do frontend. |
| 201–240 | Motor de partidas, IA e competições | Entradas do MatchEngine, seed, influências, eventos, cartões, substituições, finalizações, posse, xG, placar, adiamento, IA de elenco/caixa/saúde, objetivos, alternativas, formatos de competição, desempates, pênaltis, classificação e premiações. |
| 241–260 | Calendário e temporadas | Relógio lógico, pré-temporada, descanso, conflitos, adiamentos, semanas sem ou com várias partidas, auditoria de ticks, agenda por clube, transição de temporada, contratos e rollback. |
| 261–280 | IA esportiva | Objetivos e orçamento, avaliação de elenco, escalação, tática, prioridade de competição, contratação/venda/renovação, evolução de departamentos, explicações, determinismo e limites econômicos. |
| 281–300 | Mercado de transferências | Vínculos, janelas, transferíveis, propostas, salários, empréstimos, opção de compra, comissões, custos, vagas, suspensões, aprovação, histórico, concorrência e rollback. |
| 301–320 | Scouting e base | Missões, regiões, duração, custo, relatórios, filtros, prioridade, staff de scouting, descoberta separada de contratação, base, progressão, promoção, manutenção e expiração. |
| 321–340 | P0-17 Economia mundial | FinanceLedger, categorias, moeda única, fechamento semanal, receitas/despesas, orçamento, projeção de 39 semanas, reservas, alertas, obrigações, dívidas, juros, saúde financeira, insolvência, investimentos, SAF, controle, auditoria, idempotência e rollback. |
| 341–360 | P1-18 Finanças do clube | Caixa atual e projetado, folha de atletas/comissão/manutenção, patrocínio, bilheteria, premiações, filtros de ledger, exportação CSV, alerta de saldo, prévias de despesa e caixa pós-partida, prévia de contratação, auditoria sazonal, arredondamentos, concorrência e documentação da fonte canônica. Os passos 355/356 continuam indicados como pendentes no texto do item 354. |
| 361–370 | P1-19 Estádio e Infraestrutura | Componentes arquibancada/campo/estrutura/equipes, níveis 1–10, capacidade, custos de upgrade, manutenção, impacto operacional, prévia de upgrade, confirmação via gateway, rollback transacional, idempotência, testes e SQL/GameState como fonte única. |
| 371–390 | P1 | Calendário operacional, viagens, recuperação, reputação, torcida, bilheteria, segmentação e timeline social. Implementação documentada e validada. |
| 391–410 | P1 | Competições, desempates, filtros, histórico, contratos, renovação explícita, ledger de luvas/bônus, teto salarial e perfil/evolução de atletas. |
| 411–430 | P1 | Treino, objetivos, scouting focado, mercado, contrapropostas, janelas, empréstimos, histórico, alertas, filtros e confirmação transacional. |
| 431–440 | P1 | Simulação mundial com níveis, fila, cancelamento, checkpoints, progresso, divergência e benchmark. |
| 441–450 | P2 | IA explicável com alternativas, prévias, aprovação humana, limites, alertas e determinismo. |
| 451–470 | P0/P1 | Contratos, ações mutáveis, idempotência, rollback, scanners, release, exportação segura, hashes e recuperação. |

## Detalhamento do bloco P1-18

O bloco financeiro registra a leitura do caixa pelo `club_economic_state` e pelo `FinanceLedger`, sem cálculo de saldo no cliente. Inclui projeção de 39 semanas, componentes da folha, categorias de receita, filtros de temporada e categoria, exportação CSV, alertas persistidos, prévias somente leitura e auditoria sazonal. A política foi documentada em `brasfoot_engine/docs/finance_governance.md`.

## Detalhamento do bloco P1-19

O bloco de estádio usa `StadiumService` como fonte das regras. Cada estádio possui quatro componentes, cada um com nível de 1 a 10. O serviço calcula capacidade operacional, custo do próximo nível e manutenção semanal. A procedure tRPC `stadium.preview` consulta o motor antes da confirmação; a mutation de upgrade permanece transacional e registra a despesa no ledger.

## O que falta para completar 1–500

O roadmap persistido contém o detalhamento oficial e as evidências dos passos 371–470. Os passos 471–500 ainda precisam ser definidos e registrados antes de implementação. Também existe um marcador global não concluído para a execução integral dos 500 passos; ele só deve ser marcado quando todos os 500 itens tiverem implementação, teste, documentação e evidência.

A lista completa, linha a linha, permanece em `todo.md` na raiz do projeto.
