# FutManager — 200 novas implementações (501–700)

## Escopo

Esta lista cobre a próxima fase após o marco 500. Ela não reabre nem repete a suíte de testes já executada. Cada item deve seguir a ordem **SQL/GameState → serviço canônico → gateway/tRPC → frontend**, quando houver interface. O frontend não calcula saldo, resultado, regra esportiva, nível, contrato ou elegibilidade; apenas apresenta respostas persistidas e estados honestos.

| Passo | Prioridade | Implementação | Dependência | Critério verificável |
|---:|:---:|---|---|---|
| 501 | P0 | Criar versão formal do schema de competição profissional. | 461 | Migração idempotente registrada em `schema_versions`. |
| 502 | P0 | Adicionar chave natural para temporada, competição e fase. | 501 | Duplicidade é recusada por constraint. |
| 503 | P0 | Registrar migrações com autor, data lógica e hash. | 501 | Auditoria retorna versão e hash. |
| 504 | P0 | Criar catálogo de códigos de erro dos novos módulos. | 501 | Cada erro possui código estável. |
| 505 | P0 | Adicionar validação de foreign keys no boot. | 501 | Serviço falha cedo em banco inválido. |
| 506 | P0 | Criar índice por clube, temporada e semana. | 501 | Plano de consulta usa índice esperado. |
| 507 | P0 | Criar índice do FinanceLedger por referência natural. | 501 | Lançamento duplicado é impedido. |
| 508 | P0 | Criar tabela de auditoria de mudanças de configuração. | 501 | Mudança guarda antes, depois e autor. |
| 509 | P0 | Versionar contratos de leitura do GameState. | 501 | Payload informa `contract_version`. |
| 510 | P0 | Documentar política de migração sem alteração da base-mãe. | 501 | Validador recusa writer apontando para a base. |
| 511 | P0 | Separar sessão do manager de preferências de jogo. | 501 | Preferências não alteram GameState. |
| 512 | P0 | Criar escopo de carreira por manager e clube. | 511 | Leituras respeitam o escopo persistido. |
| 513 | P0 | Adicionar auditoria de troca de clube controlado. | 512 | Toda troca possui origem e destino. |
| 514 | P0 | Implementar bloqueio de duas carreiras ativas no mesmo estado. | 512 | Segunda ativação retorna erro catalogado. |
| 515 | P0 | Criar encerramento de carreira com snapshot final. | 512 | Snapshot é imutável e referenciável. |
| 516 | P0 | Implementar retomada de carreira interrompida. | 515 | Retomada restaura contexto sem duplicar eventos. |
| 517 | P0 | Registrar versão do motor usada na carreira. | 512 | Consulta retorna versão e hash do motor. |
| 518 | P0 | Criar isolamento de dados entre managers. | 512 | Consulta cruzada retorna vazio/negado. |
| 519 | P0 | Adicionar auditoria de permissões do manager. | 512 | Ação não autorizada é registrada. |
| 520 | P0 | Documentar ciclo de vida da carreira. | 511–519 | Documento lista estados e transições. |
| 521 | P1 | Criar modelo persistido de comissão técnica por contrato. | 401 | Cada membro possui vigência e função. |
| 522 | P1 | Adicionar histórico de alteração de função da comissão. | 521 | Mudança preserva função anterior. |
| 523 | P1 | Implementar afinidade staff–departamento. | 521 | Afinidade vem de tabela canônica. |
| 524 | P1 | Criar prévia de impacto de contratação da comissão. | 521 | Prévia não altera caixa. |
| 525 | P1 | Adicionar aprovação do manager para contratação de staff. | 524 | Sem confirmação não há writer. |
| 526 | P1 | Implementar rescisão com multa contratual. | 521 | Multa entra no ledger transacional. |
| 527 | P1 | Criar férias e indisponibilidade de profissionais. | 521 | Agenda exclui períodos indisponíveis. |
| 528 | P1 | Registrar avaliação periódica de staff. | 521 | Avaliação possui data e autor. |
| 529 | P1 | Criar substituição temporária por função. | 527 | Substituto tem vigência explícita. |
| 530 | P1 | Documentar matriz de funções e responsabilidades. | 521–529 | Matriz referencia tabelas e writers. |
| 531 | P1 | Criar catálogo de perfis táticos. | 391 | Perfil possui formação e instruções. |
| 532 | P1 | Persistir formação titular e banco por partida. | 531 | Escalação vem do GameState. |
| 533 | P1 | Adicionar histórico de alterações de escalação. | 532 | Versões são ordenadas por partida. |
| 534 | P1 | Implementar prévia de escalação sem mutação. | 532 | Prévia não grava escalação. |
| 535 | P1 | Validar posição incompatível na escalação. | 532 | Erro de domínio indica atleta e posição. |
| 536 | P1 | Criar regras de capitão e cobradores. | 532 | Regra persistida aparece na leitura. |
| 537 | P1 | Adicionar rotação planejada por congestionamento. | 373 | Sugestão respeita saúde e minutos. |
| 538 | P1 | Criar aprovação da escalação oficial. | 534 | Apenas aprovação cria versão oficial. |
| 539 | P1 | Registrar ausência por suspensão ou lesão. | 532 | Motivo vem de registro canônico. |
| 540 | P1 | Documentar contrato da escalação. | 531–539 | Campos e transições são especificados. |
| 541 | P1 | Criar modelo de treino individual por atleta. | 411 | Plano guarda foco e vigência. |
| 542 | P1 | Adicionar carga por sessão de treino. | 541 | Carga é persistida por data lógica. |
| 543 | P1 | Implementar compatibilidade entre foco e posição. | 541 | Serviço retorna compatibilidade explicável. |
| 544 | P1 | Criar prévia de evolução por microciclo. | 541–543 | Prévia não altera atributos. |
| 545 | P1 | Adicionar limite de carga por saúde. | 542 | Excesso retorna risco catalogado. |
| 546 | P1 | Implementar recuperação automática no tick. | 542 | Recuperação é idempotente por semana. |
| 547 | P1 | Criar histórico de evolução técnica. | 544 | Cada evolução possui fonte estatística. |
| 548 | P1 | Adicionar aprovação de plano individual. | 544 | Plano não aprovado não produz efeito. |
| 549 | P1 | Registrar cancelamento por risco médico. | 545 | Cancelamento gera evento e motivo. |
| 550 | P1 | Documentar treino individual e evolução. | 541–549 | Documento lista fórmulas e tabelas. |
| 551 | P1 | Criar catálogo de lesões por gravidade. | P1-10 | Código e duração são persistidos. |
| 552 | P1 | Registrar diagnóstico médico por evento. | 551 | Diagnóstico possui profissional responsável. |
| 553 | P1 | Implementar fases de recuperação. | 551–552 | Fase atual é consultável. |
| 554 | P1 | Criar prévia de retorno ao treino. | 553 | Prévia mostra risco e data estimada. |
| 555 | P1 | Adicionar reavaliação médica agendada. | 553 | Agenda possui prazo e status. |
| 556 | P1 | Impedir escalação durante indisponibilidade. | 553 | Writer de escalação retorna conflito. |
| 557 | P1 | Registrar reincidência da lesão. | 551 | Histórico conecta eventos relacionados. |
| 558 | P1 | Criar alerta de carga incompatível com recuperação. | 553 | Alerta é idempotente por atleta/semana. |
| 559 | P1 | Integrar saúde ao relatório de elenco. | 553 | Read model expõe condição persistida. |
| 560 | P1 | Documentar ciclo médico. | 551–559 | Estados e transições são auditáveis. |
| 561 | P1 | Criar modelo de arbitragem de partidas. | 391 | Árbitro e critérios são persistidos. |
| 562 | P1 | Adicionar mando de campo e estádio neutro. | 561 | Campo da partida possui origem explícita. |
| 563 | P1 | Persistir condições climáticas do jogo. | 561 | Clima tem fonte e timestamp lógico. |
| 564 | P1 | Criar parâmetros de público e segurança. | 562 | Parâmetros vêm do serviço social. |
| 565 | P1 | Implementar prévia operacional da partida. | 561–564 | Prévia não altera resultado. |
| 566 | P1 | Registrar escalação confirmada no fixture. | 538 | Fixture referencia versão da escalação. |
| 567 | P1 | Criar validação de partida duplicada. | 561 | Mesmo fixture não é processado duas vezes. |
| 568 | P1 | Implementar cancelamento antes do início. | 561 | Cancelamento preserva motivo e auditoria. |
| 569 | P1 | Criar encerramento formal da partida. | 561–568 | Status final e horário são persistidos. |
| 570 | P1 | Documentar ciclo do fixture. | 561–569 | Contrato inclui estados e writers. |
| 571 | P1 | Criar motor de eventos por minuto de jogo. | 569 | Eventos possuem minuto e ordem. |
| 572 | P1 | Persistir gols, cartões e substituições. | 571 | Eventos são consultáveis por fixture. |
| 573 | P1 | Adicionar validação de sequência temporal. | 571 | Evento fora de ordem é rejeitado. |
| 574 | P1 | Criar resumo estatístico da partida. | 572 | Resumo é derivado de eventos SQL. |
| 575 | P1 | Implementar pós-jogo com resultado oficial. | 569–574 | Apenas fixture encerrado recebe resultado. |
| 576 | P1 | Registrar auditoria de reprocessamento. | 575 | Reprocessamento possui motivo e autor. |
| 577 | P1 | Criar prévia de alteração de resultado. | 575 | Prévia mostra impactos sem gravar. |
| 578 | P1 | Adicionar bloqueio de resultado manual fora do gateway. | 575 | Escrita direta é recusada. |
| 579 | P1 | Integrar estatísticas à forma do atleta. | 574 | Forma referencia eventos da partida. |
| 580 | P1 | Documentar eventos e resultado oficial. | 571–579 | Fontes, efeitos e idempotência listados. |
| 581 | P1 | Criar classificação de competição por pontos corridos. | 391 | Tabela retorna pontos e critérios. |
| 582 | P1 | Implementar fases eliminatórias. | 581 | Chave e confrontos são persistidos. |
| 583 | P1 | Adicionar desempate por confronto direto. | 581 | Critério usado aparece na resposta. |
| 584 | P1 | Criar cálculo de saldo de gols no serviço. | 581 | Valor vem de resultados oficiais. |
| 585 | P1 | Persistir classificação após cada rodada. | 581–584 | Versão da rodada é identificável. |
| 586 | P1 | Criar prévia de classificação. | 585 | Prévia não modifica tabela oficial. |
| 587 | P1 | Implementar suspensão de tabela por recurso. | 585 | Status e motivo são persistidos. |
| 588 | P1 | Adicionar promoção e rebaixamento. | 581 | Movimento possui origem e destino. |
| 589 | P1 | Registrar premiação por posição. | 588 | Valor entra no ledger por referência. |
| 590 | P1 | Documentar classificação e fases. | 581–589 | Contrato especifica critérios aplicados. |
| 591 | P1 | Criar calendário global de janelas esportivas. | 371 | Janelas possuem país e competição. |
| 592 | P1 | Persistir conflitos de calendário. | 591 | Conflito referencia fixtures envolvidos. |
| 593 | P1 | Implementar proposta de remarcação. | 592 | Proposta exige aprovação dos envolvidos. |
| 594 | P1 | Criar prévia de impacto da remarcação. | 593 | Prévia mostra viagens e descanso. |
| 595 | P1 | Registrar aceite ou recusa da remarcação. | 593 | Decisão é versionada e auditável. |
| 596 | P1 | Adicionar bloqueio para janela fechada. | 591 | Writer retorna erro de janela. |
| 597 | P1 | Criar agenda consolidada do clube. | 591–596 | Agenda ordena todos os compromissos. |
| 598 | P1 | Implementar alerta de conflito grave. | 592 | Alerta é idempotente. |
| 599 | P1 | Expor calendário com filtros estáveis. | 597 | tRPC recebe temporada e tipo. |
| 600 | P1 | Documentar calendário e remarcações. | 591–599 | Regras e permissões estão descritas. |
| 601 | P1 | Criar modelo de viagem por delegação. | 371 | Viagem referencia partida e grupo. |
| 602 | P1 | Adicionar opções doméstica, internacional e neutra. | 601 | Tipo e custo vêm do motor. |
| 603 | P1 | Persistir reservas de viagem. | 601 | Reserva tem status e fornecedor. |
| 604 | P1 | Criar prévia de custo e recuperação. | 601–603 | Caixa e carga retornam sem mutação. |
| 605 | P1 | Implementar aprovação financeira de viagem. | 604 | Sem aprovação não há reserva. |
| 606 | P1 | Registrar cancelamento e taxa. | 603 | Taxa entra no FinanceLedger. |
| 607 | P1 | Adicionar alerta de viagem incompatível. | 604 | Alerta referencia partida e semana. |
| 608 | P1 | Integrar viagem à capacidade do elenco. | 601 | Grupo de viagem é consultável. |
| 609 | P1 | Criar histórico de fornecedores. | 603 | Histórico não sobrescreve reservas. |
| 610 | P1 | Documentar custos e reservas. | 601–609 | Contrato lista categorias do ledger. |
| 611 | P1 | Criar modelo de receita de transmissão. | 401 | Contrato possui janela e região. |
| 612 | P1 | Adicionar distribuição por audiência. | 611 | Audiência vem de eventos persistidos. |
| 613 | P1 | Implementar prévia de receita de mídia. | 611–612 | Prévia não lança no ledger. |
| 614 | P1 | Registrar aceite de pacote de mídia. | 613 | Aceite gera versão contratual. |
| 615 | P1 | Criar recebimento parcelado. | 614 | Cada parcela possui referência natural. |
| 616 | P1 | Impedir recebimento duplicado. | 615 | Segunda liquidação é idempotente. |
| 617 | P1 | Adicionar bônus por audiência. | 612 | Bônus é calculado no serviço. |
| 618 | P1 | Criar alerta de contrato de mídia expirando. | 614 | Alerta é idempotente por contrato. |
| 619 | P1 | Expor histórico de mídia no financeiro. | 615 | Read model filtra por temporada. |
| 620 | P1 | Documentar mídia, transmissão e ledger. | 611–619 | Categorias e fórmulas versionadas. |
| 621 | P1 | Criar marketplace de produtos licenciados. | 401 | Produto possui marca e vigência. |
| 622 | P1 | Adicionar previsão de vendas por torcida. | 621 | Previsão usa segmentos persistidos. |
| 623 | P1 | Implementar prévia de contrato de licenciamento. | 621–622 | Caixa futuro é retornado sem gravar. |
| 624 | P1 | Criar aprovação do contrato comercial. | 623 | Aceite é explícito. |
| 625 | P1 | Registrar receita por lote vendido. | 624 | Lançamento aponta para lote. |
| 626 | P1 | Adicionar devolução e estorno. | 625 | Estorno referencia lançamento original. |
| 627 | P1 | Impedir vendas acima do estoque. | 625 | Serviço retorna disponibilidade real. |
| 628 | P1 | Criar alerta de estoque baixo. | 627 | Alerta é idempotente por produto. |
| 629 | P1 | Expor vendas por segmento. | 622–625 | Agregado preserva temporada e região. |
| 630 | P1 | Documentar licenciamento e estoque. | 621–629 | Writers e categorias financeiras listados. |
| 631 | P1 | Criar modelo de bilheteria por setor. | 384 | Setor possui capacidade persistida. |
| 632 | P1 | Adicionar preços por faixa de ingresso. | 631 | Preço é configurável no motor. |
| 633 | P1 | Implementar prévia de demanda por setor. | 631–632 | Público estimado não é persistido. |
| 634 | P1 | Registrar vendas realizadas. | 631 | Venda possui partida e setor. |
| 635 | P1 | Criar bloqueio de capacidade. | 634 | Venda excedente é recusada. |
| 636 | P1 | Adicionar gratuidade e cortesias auditáveis. | 634 | Cortesia possui motivo e responsável. |
| 637 | P1 | Implementar estorno de ingresso. | 634 | Estorno não duplica receita. |
| 638 | P1 | Integrar segurança à venda. | 635 | Risco de lotação bloqueia operação. |
| 639 | P1 | Expor ocupação esperada e realizada. | 633–634 | Painel lê dois valores persistidos. |
| 640 | P1 | Documentar bilheteria setorizada. | 631–639 | Capacidade, preço e receitas descritos. |
| 641 | P1 | Criar reputação por competição. | 381 | Registro guarda origem e competição. |
| 642 | P1 | Adicionar reputação de fair play. | 641 | Pontuação deriva de eventos oficiais. |
| 643 | P1 | Implementar impacto reputacional de punições. | 642 | Evento possui severidade. |
| 644 | P1 | Criar prévia de impacto de decisão disciplinar. | 643 | Prévia não altera reputação. |
| 645 | P1 | Registrar evolução reputacional mensal. | 641–643 | Snapshot tem data lógica. |
| 646 | P1 | Adicionar alertas de reputação crítica. | 645 | Alerta é deduplicado. |
| 647 | P1 | Expor comparação por temporada. | 645 | Agregado preserva a temporada. |
| 648 | P1 | Criar plano de recuperação reputacional. | 646 | Plano possui metas e prazo. |
| 649 | P1 | Aprovar ações de recuperação. | 648 | Ação só inicia após aceite. |
| 650 | P1 | Documentar reputação esportiva, comercial e disciplinar. | 641–649 | Fontes e pesos são versionados. |
| 651 | P1 | Criar catálogo de eventos noticiosos. | 421 | Tipo e severidade são persistidos. |
| 652 | P1 | Gerar notícia após partida concluída. | 651 | Origem aponta para fixture oficial. |
| 653 | P1 | Adicionar notícia de contratação e renovação. | 651 | Origem aponta para contrato. |
| 654 | P1 | Criar notícia de lesão e retorno. | 651 | Origem aponta para evento médico. |
| 655 | P1 | Implementar agrupamento por dia lógico. | 652 | Feed ordena por data do GameState. |
| 656 | P1 | Adicionar leitura e arquivamento de notícia. | 655 | Estado é persistido por manager. |
| 657 | P1 | Criar filtros por tipo e severidade. | 655 | Parâmetros tRPC são estáveis. |
| 658 | P1 | Implementar paginação cursor-based. | 655 | Próximo cursor é reproduzível. |
| 659 | P1 | Integrar notícias ao dashboard. | 652–658 | Frontend apenas lê o feed. |
| 660 | P1 | Documentar feed e ciclo de alertas. | 651–659 | Origem, leitura e retenção descritas. |
| 661 | P1 | Criar centro de notificações do manager. | 651 | Notificação referencia evento. |
| 662 | P1 | Adicionar preferências por tipo de alerta. | 661 | Preferência não muda regra do motor. |
| 663 | P1 | Implementar agrupamento de alertas iguais. | 661 | Grupo preserva todas as referências. |
| 664 | P1 | Criar snooze com prazo lógico. | 661 | Snooze expira pelo relógio do jogo. |
| 665 | P1 | Adicionar marcação individual como lida. | 661 | Estado é idempotente. |
| 666 | P1 | Implementar marcação em massa. | 665 | Apenas itens do escopo são alterados. |
| 667 | P1 | Criar severidade visual padronizada. | 651 | Tokens vêm do contrato de status. |
| 668 | P1 | Expor histórico de notificações. | 661–666 | Histórico não é apagado por leitura. |
| 669 | P1 | Criar alerta de falha operacional. | 661 | Falha possui código e origem. |
| 670 | P1 | Documentar notificações e preferências. | 661–669 | Retenção e permissões listadas. |
| 671 | P1 | Criar modo de observação de adversário. | 416 | Relatório referencia partidas observadas. |
| 672 | P1 | Adicionar filtros de estilo de jogo. | 671 | Estilo deriva de eventos persistidos. |
| 673 | P1 | Implementar relatório de fraquezas. | 671–672 | Cada fraqueza possui evidência. |
| 674 | P1 | Criar comparação entre adversários. | 671 | Comparação mantém competição e temporada. |
| 675 | P1 | Adicionar prévia de plano de jogo. | 673–674 | Prévia não muda escalação. |
| 676 | P1 | Registrar aprovação do plano de jogo. | 675 | Versão aprovada é persistida. |
| 677 | P1 | Criar relatório pós-jogo do adversário. | 675 | Resultado referencia hipóteses confirmadas. |
| 678 | P1 | Medir qualidade da observação. | 671 | Confiança e amostra são expostas. |
| 679 | P1 | Criar expiração de relatório antigo. | 671 | Expiração é idempotente. |
| 680 | P1 | Documentar scouting de adversários. | 671–679 | Fontes e limites de inferência descritos. |
| 681 | P2 | Criar diagnóstico estratégico do clube. | 441 | Diagnóstico referencia tabelas. |
| 682 | P2 | Adicionar alternativas de mercado ao diagnóstico. | 681 | Alternativas têm custo e motivo. |
| 683 | P2 | Criar prévia de estratégia financeira. | 681 | Prévia não executa mutação. |
| 684 | P2 | Implementar aprovação do conselho. | 683 | Decisão possui aprovador. |
| 685 | P2 | Adicionar teto de risco estratégico. | 684 | Limite é persistido por temporada. |
| 686 | P2 | Criar alerta de estratégia incompatível. | 685 | Alerta usa estado econômico canônico. |
| 687 | P2 | Registrar decisões descartadas. | 682 | Histórico preserva alternativas. |
| 688 | P2 | Implementar explicação baseada em fatos. | 681–687 | Cada frase aponta para fonte. |
| 689 | P2 | Criar repetição determinística do diagnóstico. | 681 | Mesmo seed produz mesmo pacote. |
| 690 | P2 | Documentar limites do diagnóstico. | 681–689 | Não há justificativa sem evidência. |
| 691 | P2 | Criar modelo de conselho administrativo. | 684 | Conselheiro possui mandato. |
| 692 | P2 | Adicionar votação de decisões relevantes. | 691 | Votos são persistidos por membro. |
| 693 | P2 | Implementar quórum configurável. | 692 | Decisão informa quórum aplicado. |
| 694 | P2 | Criar conflito de interesse. | 691 | Membro impedido não vota. |
| 695 | P2 | Registrar ata de reunião. | 692–694 | Ata referencia pauta e votos. |
| 696 | P2 | Adicionar aprovação extraordinária. | 693 | Exceção possui justificativa. |
| 697 | P2 | Criar histórico de composição do conselho. | 691 | Mandatos anteriores são preservados. |
| 698 | P2 | Integrar conselho a limites financeiros. | 693 | Serviço bloqueia violação de teto. |
| 699 | P2 | Expor pendências do conselho no dashboard. | 695–698 | Frontend lê apenas pendências persistidas. |
| 700 | P2 | Documentar governança e decisões do conselho. | 691–699 | Estados, quórum e writers descritos. |

## Regra de execução da fase 501–700

A ordem recomendada é concluir primeiro os itens P0 501–520, depois avançar por domínio. Cada implementação deve acrescentar contrato de leitura, writer autorizado quando necessário, teste específico e documentação mínima. Nenhum item desta lista autoriza a criação de uma segunda fonte de verdade no frontend, nem exige refazer os testes históricos já aprovados.
