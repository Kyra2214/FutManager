# P1-18 — Incremento de leitura financeira

A aplicação agora possui uma seção **Finanças** na navegação principal. A tela consulta o mesmo `club.workspace` que sustenta o dashboard e o novo procedimento tRPC `club.finance`, cuja resposta é exclusivamente o bloco financeiro do read model.

A apresentação expõe caixa atual, orçamento, folha semanal disponível e origem/atualização do estado. O texto da interface deixa explícito que o frontend não calcula nem altera o saldo; o valor é retornado pelo estado econômico persistido.

Este incremento não declara o Front P1-18 concluído. Permanecem pendentes os itens de ledger detalhado, filtros, CSV, prévias de impacto, contratos expirando, histórico sazonal e testes específicos de concorrência/arredondamento.
