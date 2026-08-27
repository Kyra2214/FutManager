# Revisão visual da abertura e do Dia do Jogo

A viewport móvel de 390×844 foi verificada após o redesenho. A tela de abertura apresenta contraste adequado, hierarquia clara e formulário legível. A seção de partidas foi renomeada para Dia do Jogo e mostra 1.520 jogos na temporada, a competição ativa e o próximo compromisso real.

A central de simulação foi adicionada como experiência guiada de pré-jogo. Ela não cria placar nem eventos fictícios: informa que os eventos e o resultado só aparecem quando persistidos pelo motor. O próximo passo é conectar fases/eventos reais do contrato de simulação do GameState.

Validação técnica desta rodada: `pnpm check` e `pnpm build` aprovados; nenhum erro TypeScript ativo no servidor de desenvolvimento.
