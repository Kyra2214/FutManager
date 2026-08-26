# Validação dos atalhos de contratação do CT

Com o estado atual do Flamengo sem profissionais e departamentos persistidos, as quatro linhas do CT são interativas. Ao acionar **Comissão Técnica**, a interface exibiu a mensagem:

> Comissão técnica ainda não possui registros. Vá ao Mercado para contratar.

Em seguida, a navegação foi direcionada para `?section=mercado`. O mesmo mecanismo é aplicado a Médicos, Auxiliares e Departamentos. Quando o SQL passar a registrar dados para uma dessas áreas, o clique deixa de redirecionar e confirma que os dados persistidos já estão disponíveis.

Em viewport móvel de 375 × 812 px, as quatro linhas permanecem visíveis, alcançáveis e com área de toque adequada. A cobertura de interface executa os quatro cenários, confirma a mensagem específica de cada área e verifica a navegação para `mercado` em estado SQL vazio.

O cenário responsivo automatizado força largura de viewport de 375 px, executa Comissão Técnica, Médicos, Auxiliares e Departamentos em sequência e confirma quatro mensagens e quatro chamadas de navegação para `mercado`.
