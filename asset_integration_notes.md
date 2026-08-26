# Validação de ativos do motor

O endpoint local `/engine-assets/escudos/clubes/07vestur_fro.png` entregou corretamente o PNG original de 60 × 60 px. A página **Seu Clube** permanece íntegra e exibe o fallback `?` porque a carreira atual não possui clube controlado; nenhum escudo foi inventado para esse estado. Quando `manager_careers.current_club_id` for definido, a consulta `assets.resolve` retorna o caminho oficial para o card renderizar o escudo vinculado.

O componente reutilizável `EntityAsset` resolve tanto clubes quanto seleções. Para seleções, ele prioriza escudo e mini-escudo quando existirem e usa a camisa primária apenas como ativo explicitamente rotulado quando o pacote original não fornecer escudo. Os testes cobrem os estados `COMPLETE`, `FULL_ONLY`, `MINI_ONLY`, `NO_SOURCE_ASSET`, `SOURCE_NOT_PROVIDED`, `ENTITY_NOT_FOUND` e `STATE_UNAVAILABLE`.

Na área **Time**, a consulta visual do clube de ID `1` retornou **07 Vestur** e exibiu `assets/escudos/clubes/07vestur_fro.png` com o status **Escudo original vinculado**.

Na mesma área, a consulta da seleção de ID `1` retornou **AFS**. Como o pacote original não possui escudo de seleção, a interface exibiu `assets/selecoes/camisas/AFS.png` como **Camisa de AFS**, com a mensagem explícita **Escudo da seleção não fornecido; camisa disponível**.
