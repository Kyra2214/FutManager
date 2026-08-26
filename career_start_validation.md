# Validação do início de carreira

O estado real não possui managers nem carreiras ativas. A rota inicial exibiu a tela **Nova Carreira**, carregando um catálogo de clubes reais com seus escudos originais. A suíte do frontend validou o catálogo, a criação e a leitura de uma carreira em banco temporário; a suíte do motor validou início para clube e seleção.

A gravação no estado real exige os dados escolhidos pelo jogador e a ação explícita no botão **Começar carreira**. Nenhum manager, clube controlado ou seleção foi inventado para fins de validação.

A tela também foi verificada com o catálogo de seleções: ela mostra as camisas originais e informa explicitamente que os escudos nacionais não são fornecidos pelo pacote de origem.

Em viewport móvel de 375 × 812 px, o fluxo reorganiza o painel em uma coluna, mantém os campos de identidade, os controles de destino, o catálogo rolável e o botão de início acessíveis.

Os testes do gateway abrangem o início bem-sucedido, a leitura da carreira após a gravação, o conflito de carreira já ativa e o erro de clube inexistente. As mensagens de interface também possuem cobertura para conflito, entidade removida e indisponibilidade do motor.

O teste DOM da tela inicial cobre o clique de seleção, a chamada de início, a invalidação de `career.current`, a transição para o dashboard em estado isolado e a exibição de erro de carreira já ativa.

Uma instância web temporária, apontada para uma cópia isolada de `game.db`, também foi validada no navegador: a carreira **Manager E2E** foi iniciada no clube **07 Vestur**, a tela avançou ao dashboard e o escudo apareceu no clube controlado. O estado real permaneceu com `0` managers e `0` carreiras.

Além da validação no navegador, o teste integrado `careerRouter.integration.test.ts` usa o caller tRPC e o gateway Python reais com uma cópia temporária do estado, cobrindo catálogo, início, persistência e a leitura da carreira criada.
