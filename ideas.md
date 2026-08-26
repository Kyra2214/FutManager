# FutManager — Direção visual

## Abordagens consideradas

### Tema: Editorial de Arquibancada
Introdução: Um painel esportivo inspirado em revistas de futebol e placares de estádio, com tipografia expressiva, blocos assimétricos e acentos de gramado. A sensação é de inteligência tática com energia de dia de jogo.
Probabilidade: 0.06

### Tema: Centro de Comando Noturno
Introdução: Uma central escura, técnica e imersiva para decisões rápidas, com dados compactos e sinais luminosos controlados. A sensação é de operar um clube sob pressão.
Probabilidade: 0.03

### Tema: Clube Modernista
Introdução: Uma interface clara, silenciosa e arquitetônica, inspirada em programas culturais e no desenho de estádios contemporâneos. A sensação é de clareza, confiança e gestão premium.
Probabilidade: 0.08

## Abordagem escolhida: Editorial de Arquibancada

### Design Movement
Modernismo editorial esportivo, cruzando direção de arte de revistas de futebol com sinalética de estádios e painéis táticos impressos.

### Core Principles
1. A interface deve parecer uma página editorial viva: hierarquia forte, cortes assimétricos, módulos com contexto e ritmo visual.
2. Dados de gestão recebem a mesma dignidade visual que o placar: números grandes, legendas precisas e estados sem ambiguidade.
3. O clube é contado por camadas: resultado, torcida, caixa, campo e pessoas, sem transformar tudo em um único rating.
4. A cor de destaque é econômica e funcional; ela marca ação, forma positiva e atenção, sem virar decoração constante.

### Color Philosophy
O fundo é um marfim frio de papel de programa, com carvão profundo para texto e navegação. Verde de gramado queimado representa crescimento, treino e ação positiva; azul-cobalto sinaliza informação confiável; coral de alerta é reservado a lesões, caixa e pendências. A paleta deve trazer a energia do estádio sem recorrer a neon ou gradientes roxos.

### Layout Paradigm
Sidebar vertical persistente como coluna de placar, com conteúdo em uma composição editorial assimétrica: uma faixa de contexto no topo, um painel principal de decisão e uma coluna lateral de acontecimentos. Evitar centralização total; a página deve ter uma linha de leitura diagonal entre próximo jogo, caixa e feed.

### Signature Elements
- Placas de seção com pequenos marcadores de campo e linha vertical de cor.
- Números-chave em display condensado, tratados como placar.
- Cartões de evento com uma tarja lateral por categoria e microstatus em caixa alta.

### Interaction Philosophy
Toda ação deve responder como uma decisão de gestão: botões com rótulos de verbo, estado selecionado visível, toasts curtos e nenhuma mudança silenciosa. O frontend apenas apresenta e encaminha ações ao serviço; itens ainda não suportados mostram estado “Em preparação”, nunca simulam sucesso.

### Animation
Entrada curta em cascata de 40ms entre blocos, com transform e opacity apenas. Hover desloca levemente a tarja lateral ou eleva o cartão em 2px. Botões usam compressão de 0.97 no clique. Nada deve exceder 260ms; respeitar prefers-reduced-motion.

### Typography System
Display: Space Grotesk, pesos 600–700, para títulos e números de placar. Corpo: Manrope, pesos 400–600, para leitura e labels. Hierarquia: eyebrow 11px em caixa alta e tracking amplo; título 30–44px; número principal 32–56px; texto 13–16px; microcopy 11–12px.

### Brand Essence
O FutManager é o painel de decisão para managers que querem sentir o clube vivo sem perder clareza sobre cada consequência. Personalidade: atento, editorial, competitivo.

### Brand Voice
Headlines são diretas e situacionais. CTAs começam com verbo e deixam a consequência clara. Microcopy é curta, factual e humana.
Exemplos: “O próximo jogo começa no caixa.” e “Leia o cenário antes de mexer no elenco.”

### Wordmark & Logo
Marca gráfica baseada em um escudo geométrico aberto por uma linha de campo diagonal, formando simultaneamente a letra F e uma pequena seta de avanço. O símbolo funciona sem texto e será usado como ícone de navegação e favicon.

### Signature Brand Color
Verde gramado queimado `#A7C957`, usado com parcimônia em ações, forma positiva e estados de avanço.

## Style Decisions

- Manter o sistema visual claro e editorial, com carvão, marfim, verde gramado queimado, azul-cobalto e coral.
- Usar sidebar persistente e composição assimétrica, evitando dashboard genérico centrado.
- Não usar imagens geradas como preenchimento repetido; cada visual deve ter função distinta.
- Tratar dados não disponíveis como ausência honesta, não como valores inventados.

### Emendas aceitas após a revisão visual

- O símbolo FutManager aparece como marca gráfica no topo lateral e como selo do hero, tratado como escudo geométrico e não apenas como texto com ícone.
- Métricas principais receberam índices, marcas diagonais e presença de placar editorial, mesmo quando o valor está indisponível.
- Eventos ganharam tarjas laterais por categoria; o hero recebeu linhas de campo discretas para parecer uma página de programa de jogo.
- A cópia pública evita nomes crus de serviços técnicos e traduz a situação para linguagem de clube, estado e consequência.
