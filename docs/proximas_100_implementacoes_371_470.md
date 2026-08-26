# Próximas 100 implementações do FutManager

## Escopo e regra de execução

Esta lista cobre os passos **371–470**. Ela é uma proposta versionada para preencher a continuação do roadmap após o passo 370. Cada item deve ser executado em ordem; a implementação deve começar no motor/SQL, passar pelo gateway e contrato tRPC e só então chegar ao frontend. Nenhum saldo, resultado, nível, contrato ou entidade deve ser calculado ou persistido exclusivamente no cliente.

| Passo | Prioridade | Implementação | Dependência | Critério verificável |
|---:|:---:|---|---|---|
| 371 | P1 | Criar o modelo persistido de calendário operacional do clube para treinos, viagens e partidas. | P0-13 | Consulta read-only retorna agenda ordenada por data. |
| 372 | P1 | Registrar deslocamento estimado e impacto de recuperação por partida. | 371 | Tick semanal grava um único registro por fixture. |
| 373 | P1 | Expor previsão de carga semanal por atleta no GameState. | 371 | Relatório contém minutos, treino, viagem e descanso. |
| 374 | P1 | Criar alerta persistido de congestionamento individual. | 373 | Alerta é idempotente por clube, atleta e semana. |
| 375 | P1 | Implementar recomendação de descanso baseada em carga e saúde persistidas. | 373 | Recomendação não altera escalação automaticamente. |
| 376 | P1 | Integrar o relatório de carga à tela Nossas Partidas. | 373 | Frontend lê somente via tRPC. |
| 377 | P1 | Adicionar prévia de impacto de uma partida na recuperação do elenco. | 372–375 | Prévia não persiste nem altera forma. |
| 378 | P1 | Validar recuperação após semanas com partidas simultâneas. | 371–377 | Teste em GameState temporário cobre duas competições. |
| 379 | P1 | Cobrir rollback de calendário operacional e carga. | 371–378 | Falha transacional restaura relógio e registros. |
| 380 | P1 | Documentar o contrato operacional de calendário e carga. | 371–379 | Documento referencia tabelas, chaves e fórmulas. |
| 381 | P1 | Criar histórico persistido de reputação esportiva e comercial por temporada. | P0-14 | Cada alteração possui fonte e referência natural. |
| 382 | P1 | Derivar reputação do resultado, público e patrocínio sem estado paralelo. | 381 | Auditoria reproduz o valor a partir do ledger e eventos. |
| 383 | P1 | Implementar eventos sociais de torcida com severidade e impacto. | 381–382 | Evento é idempotente por origem. |
| 384 | P1 | Persistir evolução de tamanho, satisfação e engajamento da torcida. | 383 | Histórico contém antes, depois e data lógica. |
| 385 | P1 | Criar prévia de impacto de alteração de preço de ingresso. | 384 | Prévia informa público e receita estimados sem gravar. |
| 386 | P1 | Integrar risco de rejeição de preço ao painel de bilheteria. | 385 | Interface exibe a decisão do motor. |
| 387 | P1 | Implementar segmentação de torcida local, nacional e internacional. | 384 | Segmentos são derivados de registros persistidos. |
| 388 | P1 | Expor linha do tempo social do clube. | 381–387 | Consulta é paginada e read-only. |
| 389 | P1 | Testar determinismo social com seed e repetição de tick. | 383–388 | Mesmo contexto produz o mesmo resultado. |
| 390 | P1 | Documentar reputação, torcida e bilheteria como módulos do GameState. | 381–389 | Auditoria de governança passa sem escrita paralela. |
| 391 | P1 | Criar read model consolidado de competição por clube. | P0-12 | Retorna fase, tabela, próximos jogos e status. |
| 392 | P1 | Expor critérios de desempate aplicados em cada classificação. | 391 | Resposta inclui regra e ordem efetivamente usada. |
| 393 | P1 | Adicionar filtro de competição, temporada e fase na aba Nossas Partidas. | 391 | Filtros são parâmetros tRPC estáveis. |
| 394 | P1 | Exibir partidas suspensas, adiadas e remarcadas com motivo persistido. | P0-13 | Nenhum status é inferido no cliente. |
| 395 | P1 | Criar prévia de classificação após uma partida ainda não aplicada. | 391–394 | Prévia é descartável e não altera tabela. |
| 396 | P1 | Exibir histórico de campeões e premiações por temporada. | P0-12 | Dados vêm das tabelas canônicas. |
| 397 | P1 | Integrar alertas de classificação ao dashboard do clube. | 396 | Alertas são marcados como lidos via gateway. |
| 398 | P1 | Adicionar comparação de desempenho entre competições. | 391–397 | Agregados preservam temporada e competição. |
| 399 | P1 | Cobrir múltiplas competições no mesmo período com testes de leitura. | 391–398 | Teste não executa partidas oficiais. |
| 400 | P1 | Documentar o contrato tRPC de competições e classificação. | 391–399 | Campos e estados vazios são especificados. |
| 401 | P1 | Criar histórico de contratos de atletas com versões de salário e duração. | P1-15 | Cada versão tem vigência e referência natural. |
| 402 | P1 | Expor contratos próximos do vencimento no read model do elenco. | 401 | Consulta não cria alertas duplicados. |
| 403 | P1 | Implementar prévia de renovação com impacto na folha semanal. | 401–402 | Caixa e folha são retornados pelo motor. |
| 404 | P1 | Implementar aprovação explícita de renovação pelo manager. | 403 | Sem confirmação não há mutação. |
| 405 | P1 | Registrar bônus, luvas e custos acessórios de contrato. | 401–404 | Valores entram no FinanceLedger transacional. |
| 406 | P1 | Criar validação de teto salarial por clube e competição. | 405 | Violação gera DomainError catalogado. |
| 407 | P1 | Expor histórico de minutos, forma e saúde no perfil do atleta. | P1-6/P1-10 | Dados são agregados de tabelas existentes. |
| 408 | P1 | Adicionar comparação de evolução entre potencial e desempenho. | 407 | Comparação é read-only e identificável por temporada. |
| 409 | P1 | Cobrir transferência, renovação e rescisão em uma matriz transacional. | 401–408 | Testes verificam rollback e idempotência. |
| 410 | P1 | Documentar o ciclo de vida contratual do atleta. | 401–409 | Documento lista estados e writers autorizados. |
| 411 | P1 | Criar planos de treino por microciclo persistido. | P1-9 | Plano tem versão, semana e autor da decisão. |
| 412 | P1 | Adicionar objetivos técnicos mensuráveis por atleta. | 411 | Progresso deriva de estatísticas persistidas. |
| 413 | P1 | Implementar bônus de treino por departamento e staff ativo. | P1-8 | Fórmula vem do serviço, não do frontend. |
| 414 | P1 | Criar prévia de treino com carga, evolução e risco de lesão. | 411–413 | Prévia não altera saúde nem forma. |
| 415 | P1 | Adicionar aprovação e cancelamento de plano semanal. | 411–414 | Operações são idempotentes por versão. |
| 416 | P1 | Criar missões de scouting focadas em lacunas de posição. | P2-16 | Filtro usa relatório canônico de profundidade. |
| 417 | P1 | Expor incerteza do relatório de scouting e data de observação. | 416 | UI distingue observado de atributo real. |
| 418 | P1 | Criar comparação de oportunidades de base e mercado. | 416–417 | Comparação não promove nem contrata automaticamente. |
| 419 | P1 | Testar treino, scouting e saúde em ciclo semanal isolado. | 411–418 | Seed, rollback e expiração são cobertos. |
| 420 | P1 | Documentar contratos dos módulos de treino e scouting. | 411–419 | Fontes, entradas e efeitos são listados. |
| 421 | P1 | Implementar contraproposta com versão e expiração. | P1-15 | Só a versão vigente pode ser aceita. |
| 422 | P1 | Criar prévia completa de transferência com todos os custos. | 421 | Caixa, folha e ledger futuro são retornados. |
| 423 | P1 | Adicionar validação de registro internacional e janela. | 421–422 | Bloqueio gera erro de domínio estável. |
| 424 | P1 | Implementar empréstimo com marcos de retorno e opção de compra. | 421–423 | Datas e condições persistem no contrato. |
| 425 | P1 | Registrar solidariedade, comissão e custos acessórios por referência. | 422–424 | Ledger não duplica lançamentos. |
| 426 | P1 | Expor histórico de negociação por proposta e participante. | 421–425 | Histórico é cronológico e read-only. |
| 427 | P1 | Criar alertas de proposta expirada e contraproposta recebida. | 426 | Alertas são idempotentes. |
| 428 | P1 | Adicionar filtros de mercado por idade, posição, nível e orçamento. | 421–427 | Filtros não alteram o catálogo canônico. |
| 429 | P1 | Cobrir concorrência entre duas decisões de transferência. | 421–428 | Uma transação vence e a outra recebe conflito. |
| 430 | P1 | Documentar o protocolo de confirmação do mercado. | 421–429 | Prévia e confirmação têm contratos distintos. |
| 431 | P1 | Criar níveis de simulação mundial configuráveis por temporada. | P0-16 | Nível e seed ficam persistidos no contexto. |
| 432 | P1 | Implementar fila de processamento por competição e clube. | 431 | Ordem é determinística e auditável. |
| 433 | P1 | Adicionar cancelamento cooperativo entre lotes de simulação. | 432 | Cancelamento não deixa transação parcial. |
| 434 | P1 | Criar checkpoints de simulação para recuperação. | 432–433 | Reinício retoma sem duplicar eventos. |
| 435 | P1 | Expor progresso de simulação por consulta read-only. | 434 | Frontend não controla o worker diretamente. |
| 436 | P1 | Implementar relatório de divergência após reprocessamento. | 434–435 | Relatório compara referências canônicas. |
| 437 | P1 | Cobrir economia, calendário e partidas no lote mundial. | 431–436 | Teste usa GameState temporário. |
| 438 | P1 | Medir tempo, memória e número de transações por nível. | 431–437 | Benchmark reproduzível é salvo em docs. |
| 439 | P1 | Validar que simulação não escreve no banco-base. | 431–438 | Guarda de caminho falha em tentativa inválida. |
| 440 | P1 | Documentar o contrato de simulação e recuperação. | 431–439 | Entradas, saídas e limites são versionados. |
| 441 | P2 | Criar diagnóstico de IA por rodada com fatos e fontes. | P2-14 | Cada recomendação referencia tabelas persistidas. |
| 442 | P2 | Expor alternativas descartadas pela IA. | 441 | Histórico registra motivo e custo de cada alternativa. |
| 443 | P2 | Criar prévia de impacto de decisão de IA no clube. | 441–442 | Prévia não executa mutação. |
| 444 | P2 | Implementar aprovação humana de decisão automatizada. | 443 | Ação só ocorre após confirmação. |
| 445 | P2 | Adicionar limites de risco configuráveis pelo conselho. | 441–444 | Limites persistem por clube e temporada. |
| 446 | P2 | Criar alertas de decisões incompatíveis com orçamento. | 445 | Alertas usam o saldo canônico. |
| 447 | P2 | Expor histórico explicável da IA na interface. | 441–446 | UI apresenta fatos sem inventar justificativas. |
| 448 | P2 | Cobrir determinismo da IA em contexto idêntico. | 441–447 | Mesmo seed produz mesma decisão. |
| 449 | P2 | Medir custo de diagnóstico de 1.000 clubes. | 441–448 | Benchmark registra tempo e memória. |
| 450 | P2 | Documentar limites e não-invenção da IA. | 441–449 | Auditoria confirma entidades apenas do SQL. |
| 451 | P0 | Consolidar testes de contrato Python ↔ TypeScript do gateway. | P0 governança | Manifesto de contratos passa no validador. |
| 452 | P0 | Criar teste de cada action mutável contra GameState temporário. | 451 | Nenhuma action escreve no banco-base. |
| 453 | P0 | Adicionar teste de idempotência para todos os ticks semanais. | 452 | Segunda execução não altera totais. |
| 454 | P0 | Adicionar teste de rollback para cada serviço financeiro. | 452 | Falha restaura caixa e ledger. |
| 455 | P0 | Criar auditoria de consultas sem cálculo financeiro no frontend. | 451–454 | Scanner não encontra saldo calculado no cliente. |
| 456 | P0 | Cobrir estados de loading, vazio, erro e sucesso nas telas críticas. | 451–455 | Vitest verifica os quatro estados. |
| 457 | P0 | Executar teste responsivo das rotas principais em desktop e mobile. | 456 | Capturas e testes não exibem overflow crítico. |
| 458 | P0 | Criar relatório único de qualidade da entrega. | 451–457 | Relatório inclui testes, build e hashes. |
| 459 | P0 | Validar tamanho, integridade e exclusões do ZIP completo. | 458 | `unzip -t` e manifesto passam. |
| 460 | P0 | Documentar o procedimento de recuperação de checkpoint. | 451–459 | Procedimento reproduzível e versionado. |
| 461 | P0 | Criar manifesto de versão do esquema SQL/GameState. | P0-3 | Versão e migrações são idempotentes. |
| 462 | P0 | Adicionar verificação de foreign keys em cada boot do serviço. | 461 | Serviço falha cedo se integridade estiver desativada. |
| 463 | P0 | Criar auditoria de órfãos em jogadores, clubes e partidas. | 461–462 | Relatório é read-only e reproduzível. |
| 464 | P0 | Criar reconciliação de ledger contra estado econômico. | P0-17 | Diferenças são reportadas, não corrigidas automaticamente. |
| 465 | P0 | Adicionar verificação de hash do banco-base e do GameState. | 461–464 | Base alterada é recusada por writers. |
| 466 | P1 | Criar script de exportação segura de banco e manifesto. | 464–465 | Exportação omite segredos e valida hash. |
| 467 | P1 | Integrar observabilidade sanitizada de ticks e mutations. | 451–466 | Logs não contêm tokens ou dados desnecessários. |
| 468 | P1 | Criar checklist de release para frontend, motor e bancos. | 467 | Checklist bloqueia release sem testes. |
| 469 | P1 | Executar ensaio de restauração em cópia temporária. | 466–468 | Banco restaurado passa integridade e smoke tests. |
| 470 | P1 | Consolidar e publicar o marco 371–470 com checkpoint e changelog. | 461–469 | Checkpoint, changelog e manifesto possuem hashes. |

## Regra de promoção

Um passo só pode ser marcado como concluído depois de implementação no serviço canônico, teste automatizado, integração de gateway/tRPC quando houver interface, documentação mínima e validação de que o frontend não criou uma segunda fonte de verdade. A execução global dos 500 passos continua sendo um marco separado do preenchimento desta lista.
