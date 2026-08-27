# Roadmap FutManager — passos 701–940

Esta lista contém 240 implementações posteriores ao marco 700. A ordem numérica é obrigatória; P1 e P2 dependem da consolidação dos P0. SQL/GameState permanece como única fonte da verdade, e cada item exige writer autorizado quando houver mutação, leitura pelo gateway e teste focado.

| Passo | Prioridade | Domínio | Implementação | Dependência | Critério verificável |
|---:|:---:|---|---|---|---|
| 701 | P0 | Persistência e migrações | Implementar inventário de tabelas pós-700. | 501–700 | Inventário de tabelas pós-700 é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 702 | P0 | Persistência e migrações | Implementar migração incremental v4. | 701 | Migração incremental v4 é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 703 | P0 | Persistência e migrações | Implementar chaves naturais. | 702 | Chaves naturais é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 704 | P1 | Persistência e migrações | Implementar índices de leitura. | 703 | Índices de leitura é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 705 | P1 | Persistência e migrações | Implementar índices de auditoria. | 704 | Índices de auditoria é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 706 | P1 | Persistência e migrações | Implementar constraints de domínio. | 705 | Constraints de domínio é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 707 | P1 | Persistência e migrações | Implementar versionamento de schema. | 706 | Versionamento de schema é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 708 | P1 | Persistência e migrações | Implementar rollback seguro. | 707 | Rollback seguro é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 709 | P1 | Persistência e migrações | Implementar checksum do GameState. | 708 | Checksum do gamestate é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 710 | P1 | Persistência e migrações | Implementar detector de drift. | 709 | Detector de drift é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 711 | P1 | Persistência e migrações | Implementar catálogo de enums. | 710 | Catálogo de enums é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 712 | P1 | Persistência e migrações | Implementar normalização de datas UTC. | 711 | Normalização de datas utc é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 713 | P1 | Persistência e migrações | Implementar retenção de auditoria. | 712 | Retenção de auditoria é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 714 | P1 | Persistência e migrações | Implementar snapshots transacionais. | 713 | Snapshots transacionais é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 715 | P1 | Persistência e migrações | Implementar restauração seletiva. | 714 | Restauração seletiva é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 716 | P1 | Persistência e migrações | Implementar validadores de foreign keys. | 715 | Validadores de foreign keys é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 717 | P1 | Persistência e migrações | Implementar testes de cópia física. | 716 | Testes de cópia física é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 718 | P1 | Persistência e migrações | Implementar relatório de migração. | 717 | Relatório de migração é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 719 | P2 | Persistência e migrações | Implementar compatibilidade v3. | 718 | Compatibilidade v3 é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 720 | P2 | Persistência e migrações | Implementar documentação de persistência. | 719 | Documentação de persistência é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 721 | P0 | Gateway e contratos | Implementar contrato de leitura consolidado. | 720 | Contrato de leitura consolidado é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 722 | P0 | Gateway e contratos | Implementar mapa de writers autorizados. | 721 | Mapa de writers autorizados é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 723 | P0 | Gateway e contratos | Implementar validação de payload. | 722 | Validação de payload é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 724 | P1 | Gateway e contratos | Implementar catálogo de erros. | 723 | Catálogo de erros é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 725 | P1 | Gateway e contratos | Implementar idempotência por comando. | 724 | Idempotência por comando é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 726 | P1 | Gateway e contratos | Implementar escopo de carreira. | 725 | Escopo de carreira é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 727 | P1 | Gateway e contratos | Implementar permissões por manager. | 726 | Permissões por manager é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 728 | P1 | Gateway e contratos | Implementar paginação estável. | 727 | Paginação estável é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 729 | P1 | Gateway e contratos | Implementar filtros tipados. | 728 | Filtros tipados é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 730 | P1 | Gateway e contratos | Implementar auditoria de mutação. | 729 | Auditoria de mutação é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 731 | P1 | Gateway e contratos | Implementar rollback de comando. | 730 | Rollback de comando é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 732 | P1 | Gateway e contratos | Implementar limites de lote. | 731 | Limites de lote é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 733 | P1 | Gateway e contratos | Implementar timeout controlado. | 732 | Timeout controlado é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 734 | P1 | Gateway e contratos | Implementar telemetria de RPC. | 733 | Telemetria de rpc é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 735 | P1 | Gateway e contratos | Implementar contratos de versão. | 734 | Contratos de versão é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 736 | P1 | Gateway e contratos | Implementar testes de integração. | 735 | Testes de integração é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 737 | P1 | Gateway e contratos | Implementar proteção contra escrita frontend. | 736 | Proteção contra escrita frontend é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 738 | P1 | Gateway e contratos | Implementar serialização de datas. | 737 | Serialização de datas é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 739 | P2 | Gateway e contratos | Implementar compatibilidade de clientes. | 738 | Compatibilidade de clientes é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 740 | P2 | Gateway e contratos | Implementar documentação do gateway. | 739 | Documentação do gateway é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 741 | P0 | Calendário mundial | Implementar feriados nacionais. | 740 | Feriados nacionais é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 742 | P0 | Calendário mundial | Implementar datas FIFA. | 741 | Datas fifa é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 743 | P0 | Calendário mundial | Implementar conflitos de seleção. | 742 | Conflitos de seleção é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 744 | P1 | Calendário mundial | Implementar janelas internacionais. | 743 | Janelas internacionais é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 745 | P1 | Calendário mundial | Implementar fuso do estádio. | 744 | Fuso do estádio é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 746 | P1 | Calendário mundial | Implementar mudança de horário. | 745 | Mudança de horário é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 747 | P1 | Calendário mundial | Implementar reagendamento por clima. | 746 | Reagendamento por clima é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 748 | P1 | Calendário mundial | Implementar reagendamento por segurança. | 747 | Reagendamento por segurança é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 749 | P1 | Calendário mundial | Implementar conflito de televisão. | 748 | Conflito de televisão é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 750 | P1 | Calendário mundial | Implementar prioridade de competição. | 749 | Prioridade de competição é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 751 | P1 | Calendário mundial | Implementar descanso mínimo. | 750 | Descanso mínimo é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 752 | P1 | Calendário mundial | Implementar viagem intercontinental. | 751 | Viagem intercontinental é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 753 | P1 | Calendário mundial | Implementar calendário juvenil. | 752 | Calendário juvenil é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 754 | P1 | Calendário mundial | Implementar calendário feminino. | 753 | Calendário feminino é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 755 | P1 | Calendário mundial | Implementar calendário de base. | 754 | Calendário de base é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 756 | P1 | Calendário mundial | Implementar datas de inscrição. | 755 | Datas de inscrição é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 757 | P1 | Calendário mundial | Implementar bloqueio de sobreposição. | 756 | Bloqueio de sobreposição é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 758 | P1 | Calendário mundial | Implementar prévia de temporada. | 757 | Prévia de temporada é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 759 | P2 | Calendário mundial | Implementar auditoria de alterações. | 758 | Auditoria de alterações é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 760 | P2 | Calendário mundial | Implementar documentação do calendário. | 759 | Documentação do calendário é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 761 | P0 | Competições avançadas | Implementar fase de grupos. | 760 | Fase de grupos é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 762 | P0 | Competições avançadas | Implementar sorteio com potes. | 761 | Sorteio com potes é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 763 | P0 | Competições avançadas | Implementar sorteio protegido. | 762 | Sorteio protegido é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 764 | P1 | Competições avançadas | Implementar mata-mata com ida e volta. | 763 | Mata-mata com ida e volta é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 765 | P1 | Competições avançadas | Implementar prorrogação. | 764 | Prorrogação é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 766 | P1 | Competições avançadas | Implementar disputa de pênaltis. | 765 | Disputa de pênaltis é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 767 | P1 | Competições avançadas | Implementar regra de gol fora configurável. | 766 | Regra de gol fora configurável é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 768 | P1 | Competições avançadas | Implementar critério de confronto direto. | 767 | Critério de confronto direto é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 769 | P1 | Competições avançadas | Implementar premiação por fase. | 768 | Premiação por fase é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 770 | P1 | Competições avançadas | Implementar vagas continentais. | 769 | Vagas continentais é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 771 | P1 | Competições avançadas | Implementar rebaixamento adicional. | 770 | Rebaixamento adicional é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 772 | P1 | Competições avançadas | Implementar repescagem. | 771 | Repescagem é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 773 | P1 | Competições avançadas | Implementar licença competitiva. | 772 | Licença competitiva é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 774 | P1 | Competições avançadas | Implementar fair play de competição. | 773 | Fair play de competição é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 775 | P1 | Competições avançadas | Implementar árbitros suspensos. | 774 | Árbitros suspensos é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 776 | P1 | Competições avançadas | Implementar delegado de partida. | 775 | Delegado de partida é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 777 | P1 | Competições avançadas | Implementar protesto oficial. | 776 | Protesto oficial é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 778 | P1 | Competições avançadas | Implementar revisão de resultado. | 777 | Revisão de resultado é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 779 | P2 | Competições avançadas | Implementar homologação de competição. | 778 | Homologação de competição é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 780 | P2 | Competições avançadas | Implementar documentação competitiva. | 779 | Documentação competitiva é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 781 | P0 | Motor de partidas | Implementar modelo de posse. | 780 | Modelo de posse é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 782 | P0 | Motor de partidas | Implementar finalizações persistidas. | 781 | Finalizações persistidas é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 783 | P0 | Motor de partidas | Implementar xG determinístico. | 782 | Xg determinístico é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 784 | P1 | Motor de partidas | Implementar duelos individuais. | 783 | Duelos individuais é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 785 | P1 | Motor de partidas | Implementar bolas paradas. | 784 | Bolas paradas é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 786 | P1 | Motor de partidas | Implementar escanteios. | 785 | Escanteios é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 787 | P1 | Motor de partidas | Implementar faltas táticas. | 786 | Faltas táticas é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 788 | P1 | Motor de partidas | Implementar substituições condicionais. | 787 | Substituições condicionais é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 789 | P1 | Motor de partidas | Implementar instruções de intervalo. | 788 | Instruções de intervalo é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 790 | P1 | Motor de partidas | Implementar plano de jogo. | 789 | Plano de jogo é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 791 | P1 | Motor de partidas | Implementar efeito de torcida. | 790 | Efeito de torcida é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 792 | P1 | Motor de partidas | Implementar efeito climático. | 791 | Efeito climático é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 793 | P1 | Motor de partidas | Implementar fadiga por minuto. | 792 | Fadiga por minuto é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 794 | P1 | Motor de partidas | Implementar lesão durante partida. | 793 | Lesão durante partida é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 795 | P1 | Motor de partidas | Implementar cartão acumulado. | 794 | Cartão acumulado é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 796 | P1 | Motor de partidas | Implementar VAR configurável. | 795 | Var configurável é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 797 | P1 | Motor de partidas | Implementar árbitro por perfil. | 796 | Árbitro por perfil é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 798 | P1 | Motor de partidas | Implementar eventos anulados. | 797 | Eventos anulados é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 799 | P2 | Motor de partidas | Implementar reprocessamento auditado. | 798 | Reprocessamento auditado é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 800 | P2 | Motor de partidas | Implementar documentação do motor. | 799 | Documentação do motor é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 801 | P0 | Elenco e contratos | Implementar status de inscrição. | 800 | Status de inscrição é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 802 | P0 | Elenco e contratos | Implementar limite de estrangeiros. | 801 | Limite de estrangeiros é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 803 | P0 | Elenco e contratos | Implementar número de camisa. | 802 | Número de camisa é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 804 | P1 | Elenco e contratos | Implementar hierarquia do elenco. | 803 | Hierarquia do elenco é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 805 | P1 | Elenco e contratos | Implementar liderança do vestiário. | 804 | Liderança do vestiário é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 806 | P1 | Elenco e contratos | Implementar promessa de minutos. | 805 | Promessa de minutos é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 807 | P1 | Elenco e contratos | Implementar cláusula de saída. | 806 | Cláusula de saída é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 808 | P1 | Elenco e contratos | Implementar bônus por presença. | 807 | Bônus por presença é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 809 | P1 | Elenco e contratos | Implementar bônus por gol. | 808 | Bônus por gol é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 810 | P1 | Elenco e contratos | Implementar bônus de título. | 809 | Bônus de título é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 811 | P1 | Elenco e contratos | Implementar renovação automática. | 810 | Renovação automática é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 812 | P1 | Elenco e contratos | Implementar opção unilateral. | 811 | Opção unilateral é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 813 | P1 | Elenco e contratos | Implementar rescisão por justa causa. | 812 | Rescisão por justa causa é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 814 | P1 | Elenco e contratos | Implementar compensação contratual. | 813 | Compensação contratual é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 815 | P1 | Elenco e contratos | Implementar contrato de base. | 814 | Contrato de base é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 816 | P1 | Elenco e contratos | Implementar contrato profissional. | 815 | Contrato profissional é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 817 | P1 | Elenco e contratos | Implementar registro federativo. | 816 | Registro federativo é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 818 | P1 | Elenco e contratos | Implementar bloqueio salarial. | 817 | Bloqueio salarial é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 819 | P2 | Elenco e contratos | Implementar auditoria contratual. | 818 | Auditoria contratual é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 820 | P2 | Elenco e contratos | Implementar documentação contratual. | 819 | Documentação contratual é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 821 | P0 | Treino e desenvolvimento | Implementar microciclo semanal. | 820 | Microciclo semanal é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 822 | P0 | Treino e desenvolvimento | Implementar periodização mensal. | 821 | Periodização mensal é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 823 | P0 | Treino e desenvolvimento | Implementar carga por posição. | 822 | Carga por posição é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 824 | P1 | Treino e desenvolvimento | Implementar carga individual adaptativa. | 823 | Carga individual adaptativa é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 825 | P1 | Treino e desenvolvimento | Implementar objetivo por atributo. | 824 | Objetivo por atributo é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 826 | P1 | Treino e desenvolvimento | Implementar treino técnico. | 825 | Treino técnico é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 827 | P1 | Treino e desenvolvimento | Implementar treino tático. | 826 | Treino tático é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 828 | P1 | Treino e desenvolvimento | Implementar treino físico. | 827 | Treino físico é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 829 | P1 | Treino e desenvolvimento | Implementar treino mental. | 828 | Treino mental é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 830 | P1 | Treino e desenvolvimento | Implementar integração com comissão. | 829 | Integração com comissão é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 831 | P1 | Treino e desenvolvimento | Implementar risco acumulado. | 830 | Risco acumulado é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 832 | P1 | Treino e desenvolvimento | Implementar recuperação ativa. | 831 | Recuperação ativa é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 833 | P1 | Treino e desenvolvimento | Implementar monitoramento de evolução. | 832 | Monitoramento de evolução é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 834 | P1 | Treino e desenvolvimento | Implementar potencial atualizado. | 833 | Potencial atualizado é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 835 | P1 | Treino e desenvolvimento | Implementar declínio por idade. | 834 | Declínio por idade é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 836 | P1 | Treino e desenvolvimento | Implementar tutoria de jovens. | 835 | Tutoria de jovens é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 837 | P1 | Treino e desenvolvimento | Implementar avaliação pós-treino. | 836 | Avaliação pós-treino é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 838 | P1 | Treino e desenvolvimento | Implementar aprovação médica. | 837 | Aprovação médica é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 839 | P2 | Treino e desenvolvimento | Implementar cancelamento transacional. | 838 | Cancelamento transacional é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 840 | P2 | Treino e desenvolvimento | Implementar documentação de desenvolvimento. | 839 | Documentação de desenvolvimento é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 841 | P0 | Saúde e performance | Implementar triagem pré-jogo. | 840 | Triagem pré-jogo é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 842 | P0 | Saúde e performance | Implementar risco de lesão. | 841 | Risco de lesão é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 843 | P0 | Saúde e performance | Implementar protocolo de concussão. | 842 | Protocolo de concussão é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 844 | P1 | Saúde e performance | Implementar retorno progressivo. | 843 | Retorno progressivo é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 845 | P1 | Saúde e performance | Implementar carga médica. | 844 | Carga médica é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 846 | P1 | Saúde e performance | Implementar histórico de sintomas. | 845 | Histórico de sintomas é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 847 | P1 | Saúde e performance | Implementar reincidência ponderada. | 846 | Reincidência ponderada é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 848 | P1 | Saúde e performance | Implementar suspensão médica. | 847 | Suspensão médica é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 849 | P1 | Saúde e performance | Implementar aptidão por minuto. | 848 | Aptidão por minuto é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 850 | P1 | Saúde e performance | Implementar monitoramento de sono. | 849 | Monitoramento de sono é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 851 | P1 | Saúde e performance | Implementar fadiga acumulada. | 850 | Fadiga acumulada é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 852 | P1 | Saúde e performance | Implementar fisioterapia por fase. | 851 | Fisioterapia por fase é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 853 | P1 | Saúde e performance | Implementar especialidade médica. | 852 | Especialidade médica é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 854 | P1 | Saúde e performance | Implementar fila de atendimento. | 853 | Fila de atendimento é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 855 | P1 | Saúde e performance | Implementar custo clínico. | 854 | Custo clínico é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 856 | P1 | Saúde e performance | Implementar alerta de risco. | 855 | Alerta de risco é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 857 | P1 | Saúde e performance | Implementar prévia de escalação. | 856 | Prévia de escalação é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 858 | P1 | Saúde e performance | Implementar auditoria de laudo. | 857 | Auditoria de laudo é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 859 | P2 | Saúde e performance | Implementar integração com treino. | 858 | Integração com treino é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 860 | P2 | Saúde e performance | Implementar documentação de saúde. | 859 | Documentação de saúde é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 861 | P0 | Mercado e scouting | Implementar shortlist por posição. | 860 | Shortlist por posição é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 862 | P0 | Mercado e scouting | Implementar shortlist por região. | 861 | Shortlist por região é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 863 | P0 | Mercado e scouting | Implementar shortlist por orçamento. | 862 | Shortlist por orçamento é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 864 | P1 | Mercado e scouting | Implementar avaliação de valor. | 863 | Avaliação de valor é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 865 | P1 | Mercado e scouting | Implementar avaliação de potencial. | 864 | Avaliação de potencial é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 866 | P1 | Mercado e scouting | Implementar proposta condicionada. | 865 | Proposta condicionada é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 867 | P1 | Mercado e scouting | Implementar contraproposta limitada. | 866 | Contraproposta limitada é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 868 | P1 | Mercado e scouting | Implementar comissão de agente. | 867 | Comissão de agente é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 869 | P1 | Mercado e scouting | Implementar luvas de contratação. | 868 | Luvas de contratação é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 870 | P1 | Mercado e scouting | Implementar janela internacional. | 869 | Janela internacional é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 871 | P1 | Mercado e scouting | Implementar empréstimo com opção. | 870 | Empréstimo com opção é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 872 | P1 | Mercado e scouting | Implementar cláusula de recompra. | 871 | Cláusula de recompra é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 873 | P1 | Mercado e scouting | Implementar venda com percentual futuro. | 872 | Venda com percentual futuro é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 874 | P1 | Mercado e scouting | Implementar bloqueio por registro. | 873 | Bloqueio por registro é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 875 | P1 | Mercado e scouting | Implementar scouting por evidência. | 874 | Scouting por evidência é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 876 | P1 | Mercado e scouting | Implementar relatório de adversário. | 875 | Relatório de adversário é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 877 | P1 | Mercado e scouting | Implementar qualidade de amostra. | 876 | Qualidade de amostra é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 878 | P1 | Mercado e scouting | Implementar expiração de relatório. | 877 | Expiração de relatório é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 879 | P2 | Mercado e scouting | Implementar auditoria de negociação. | 878 | Auditoria de negociação é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 880 | P2 | Mercado e scouting | Implementar documentação de mercado. | 879 | Documentação de mercado é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 881 | P0 | Economia e finanças | Implementar orçamento por departamento. | 880 | Orçamento por departamento é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 882 | P0 | Economia e finanças | Implementar forecast semanal. | 881 | Forecast semanal é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 883 | P0 | Economia e finanças | Implementar forecast mensal. | 882 | Forecast mensal é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 884 | P1 | Economia e finanças | Implementar fluxo de caixa. | 883 | Fluxo de caixa é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 885 | P1 | Economia e finanças | Implementar reserva de emergência. | 884 | Reserva de emergência é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 886 | P1 | Economia e finanças | Implementar limite de folha. | 885 | Limite de folha é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 887 | P1 | Economia e finanças | Implementar custo de oportunidade. | 886 | Custo de oportunidade é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 888 | P1 | Economia e finanças | Implementar receita de bilheteria. | 887 | Receita de bilheteria é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 889 | P1 | Economia e finanças | Implementar receita de mídia. | 888 | Receita de mídia é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 890 | P1 | Economia e finanças | Implementar receita comercial. | 889 | Receita comercial é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 891 | P1 | Economia e finanças | Implementar premiação competitiva. | 890 | Premiação competitiva é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 892 | P1 | Economia e finanças | Implementar impostos configuráveis. | 891 | Impostos configuráveis é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 893 | P1 | Economia e finanças | Implementar despesas extraordinárias. | 892 | Despesas extraordinárias é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 894 | P1 | Economia e finanças | Implementar auditoria de saldo. | 893 | Auditoria de saldo é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 895 | P1 | Economia e finanças | Implementar reconciliação por fonte. | 894 | Reconciliação por fonte é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 896 | P1 | Economia e finanças | Implementar alerta de caixa. | 895 | Alerta de caixa é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 897 | P1 | Economia e finanças | Implementar prévia financeira. | 896 | Prévia financeira é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 898 | P1 | Economia e finanças | Implementar aprovação de gasto. | 897 | Aprovação de gasto é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 899 | P2 | Economia e finanças | Implementar estorno financeiro. | 898 | Estorno financeiro é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 900 | P2 | Economia e finanças | Implementar documentação econômica. | 899 | Documentação econômica é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 901 | P0 | Estádio, torcida e mídia | Implementar setores de estádio. | 900 | Setores de estádio é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 902 | P0 | Estádio, torcida e mídia | Implementar preço dinâmico. | 901 | Preço dinâmico é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 903 | P0 | Estádio, torcida e mídia | Implementar demanda por setor. | 902 | Demanda por setor é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 904 | P1 | Estádio, torcida e mídia | Implementar cortesias auditáveis. | 903 | Cortesias auditáveis é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 905 | P1 | Estádio, torcida e mídia | Implementar estorno de ingresso. | 904 | Estorno de ingresso é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 906 | P1 | Estádio, torcida e mídia | Implementar segurança de lotação. | 905 | Segurança de lotação é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 907 | P1 | Estádio, torcida e mídia | Implementar conforto por setor. | 906 | Conforto por setor é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 908 | P1 | Estádio, torcida e mídia | Implementar receita de hospitalidade. | 907 | Receita de hospitalidade é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 909 | P1 | Estádio, torcida e mídia | Implementar lojas do estádio. | 908 | Lojas do estádio é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 910 | P1 | Estádio, torcida e mídia | Implementar bilheteria visitante. | 909 | Bilheteria visitante é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 911 | P1 | Estádio, torcida e mídia | Implementar torcida organizada. | 910 | Torcida organizada é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 912 | P1 | Estádio, torcida e mídia | Implementar satisfação de torcedores. | 911 | Satisfação de torcedores é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 913 | P1 | Estádio, torcida e mídia | Implementar reputação comercial. | 912 | Reputação comercial é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 914 | P1 | Estádio, torcida e mídia | Implementar direitos de transmissão. | 913 | Direitos de transmissão é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 915 | P1 | Estádio, torcida e mídia | Implementar audiência regional. | 914 | Audiência regional é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 916 | P1 | Estádio, torcida e mídia | Implementar audiência internacional. | 915 | Audiência internacional é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 917 | P1 | Estádio, torcida e mídia | Implementar catálogo de notícias. | 916 | Catálogo de notícias é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 918 | P1 | Estádio, torcida e mídia | Implementar feed por evento oficial. | 917 | Feed por evento oficial é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 919 | P2 | Estádio, torcida e mídia | Implementar alertas de mídia. | 918 | Alertas de mídia é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 920 | P2 | Estádio, torcida e mídia | Implementar documentação de estádio e mídia. | 919 | Documentação de estádio e mídia é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 921 | P0 | Governança e carreira | Implementar conselho administrativo. | 920 | Conselho administrativo é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 922 | P0 | Governança e carreira | Implementar mandatos de conselheiros. | 921 | Mandatos de conselheiros é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 923 | P0 | Governança e carreira | Implementar votação persistida. | 922 | Votação persistida é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 924 | P1 | Governança e carreira | Implementar quórum configurável. | 923 | Quórum configurável é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 925 | P1 | Governança e carreira | Implementar conflito de interesse. | 924 | Conflito de interesse é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 926 | P1 | Governança e carreira | Implementar ata de reunião. | 925 | Ata de reunião é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 927 | P1 | Governança e carreira | Implementar aprovação extraordinária. | 926 | Aprovação extraordinária é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 928 | P1 | Governança e carreira | Implementar limite financeiro do conselho. | 927 | Limite financeiro do conselho é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 929 | P1 | Governança e carreira | Implementar pendências do conselho. | 928 | Pendências do conselho é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 930 | P1 | Governança e carreira | Implementar histórico de composição. | 929 | Histórico de composição é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 931 | P1 | Governança e carreira | Implementar objetivos do manager. | 930 | Objetivos do manager é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 932 | P1 | Governança e carreira | Implementar avaliação do manager. | 931 | Avaliação do manager é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 933 | P1 | Governança e carreira | Implementar ofertas de emprego. | 932 | Ofertas de emprego é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 934 | P1 | Governança e carreira | Implementar negociação de contrato. | 933 | Negociação de contrato é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 935 | P1 | Governança e carreira | Implementar seleção nacional. | 934 | Seleção nacional é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 936 | P1 | Governança e carreira | Implementar reputação do manager. | 935 | Reputação do manager é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 937 | P1 | Governança e carreira | Implementar snapshot de carreira. | 936 | Snapshot de carreira é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 938 | P1 | Governança e carreira | Implementar retomada de carreira. | 937 | Retomada de carreira é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 939 | P2 | Governança e carreira | Implementar exportação de histórico. | 938 | Exportação de histórico é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |
| 940 | P2 | Governança e carreira | Implementar documentação de governança. | 939 | Documentação de governança é persistido no GameState, exposto por leitura autorizada e coberto por teste focado. |

## Distribuição

| Prioridade | Quantidade | Regra |
|---|---:|---|
| P0 | 36 | Infraestrutura, contratos e segurança de estado devem ser consolidados primeiro. |
| P1 | 180 | Domínios operacionais executados somente após P0 aberto. |
| P2 | 24 | Melhorias estratégicas executadas após P0 e P1 do domínio. |
| **Total** | **240** | Passos 701–940. |

## Regras de execução

Cada passo deve preservar a separação entre ReadRepository e CommandService, bloquear escrita direta no frontend, usar datas UTC no armazenamento e registrar auditoria para decisões mutáveis. Prévia não persiste alterações. Testes históricos não precisam ser refeitos; apenas testes focados novos devem ser adicionados.
