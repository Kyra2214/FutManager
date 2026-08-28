# Plano de mudança visual — FutManager "cara de jogo"

Documento vivo. Cada submódulo é implementado, testado visualmente e registrado
aqui antes de avançar para o próximo. Ordem escolhida por **menor impacto de
código primeiro**, não pela ordem de fases do plano original.

Direção geral: manter a paleta e a voz editorial ("Editorial de Arquibancada"),
trocando a unidade de informação de "linha de tabela" para "componente de jogo".

---

## Status geral dos submódulos

| # | Submódulo | Fase original | Status |
|---|-----------|----------------|--------|
| 1 | StatBar (barra de atributo) | Fase 1 | ✅ Concluído |
| 2 | PlayerCard (cartão de jogador) | Fase 1 | ✅ Concluído |
| 3 | Gráficos reais (recharts) | Fase 1 | ✅ Concluído |
| 4 | Micro-motion (framer-motion) | Fase 1 | ✅ Concluído |
| 5 | Elenco → formação tática | Fase 2 | ✅ Concluído |
| 6 | CT como planta baixa | Fase 2 | ✅ Concluído |
| 7 | Calendário como linha do tempo | Fase 2 | ✅ Concluído |
| 8 | Dashboard como HUD | Fase 2 | ✅ Concluído |
| 9 | Polimento (som, empty states, StatusChip) | Fase 3 | ✅ Concluído |

---

## Submódulo 1 — StatBar ✅

**Objetivo:** qualquer par `label → número` limitado (0..max) vira uma barra
preenchida com cor por faixa, em vez de texto puro.

**Arquivos novos**
- `frontend/client/src/components/StatBar.tsx` — componente `<StatBar label
  value max suffix tone compact />`. Cor automática por faixa: `< 40%` coral,
  `40–70%` cobalt, `> 70%` grass (tokens já existentes em `index.css`, sem
  paleta nova). Aceita `tone` explícito para casos futuros.

**Arquivos alterados**
- `frontend/client/src/index.css` — bloco `.stat-bar*` logo após o reset
  global; classes `.staff-card-stats` e ajuste de espaçamento dentro de
  `.ct-training-grid`.
- `frontend/client/src/components/StaffEconomyPanel.tsx`
  - Cartão de profissional no Mercado (`staff-market-card`): `REPUTAÇÃO`
    (0–100) e `POTENCIAL` (0–99, confirmado em
    `engine/data/reports/rules_engine_report.txt`) agora são `StatBar`
    compactas. `CUSTO-BENEFÍCIO` permanece texto — é uma razão sem teto
    definido, não faz sentido como barra 0..max.
  - Grid de treinamento (`ct-training-grid`): `EFICIÊNCIA` (derivada de
    `department.efficiency`, 0–1) agora é `StatBar` com `suffix="%"`.

**Decisão de escopo (menor impacto):** a linha de eficiência dentro de
`.ct-member-row` (lista "DEPARTAMENTOS ATUAIS") **não foi alterada** nesta
etapa — é um layout flex apertado (`b`/`small` + `strong` lateral) que exigiria
reestruturar o row inteiro. Fica mapeada para quando o submódulo 6 (CT como
planta baixa) reformular essa seção por completo, evitando retrabalho.

**Risco:** baixo. Nenhum contrato de dados (tRPC) mudou, nenhuma rota mudou,
componente é puramente apresentacional e aditivo.

---

## Submódulo 2 — PlayerCard ✅

**Objetivo:** substituir a linha de tabela do elenco (`.roster-row`) por um
"componente de jogo" — cartão com badge de posição, CR em destaque, potencial
como `StatBar` e selos de estrela / topo mundial. Sem toggle lista/card:
substituição direta, mais coeso com a direção de "cara de jogo".

**Arquivos novos**
- `frontend/client/src/components/PlayerCard.tsx` — componente
  `<PlayerCard player onClick? />`. Recebe o objeto de jogador já retornado
  por `workspace.squad.players` (nenhum contrato novo). Renderiza:
  - badge de posição (`player.position`) e status (`Titular`/reserva) no
    topo, reaproveitando a classe `.muted-status` já existente;
  - CR1 como número grande estilo cartão (`.player-card-cr`);
  - nome, idade, lado e categoria como legenda;
  - selos de `player.star` (ícone `Star`) e `player.topWorld` (ícone
    `Trophy`) — mesmos ícones já usados em `SponsorshipPanel.tsx`, sem
    introduzir novo conjunto visual;
  - CR2 (potencial, 0–99) como `StatBar compact`, no mesmo padrão de
    REPUTAÇÃO/POTENCIAL do Submódulo 1.
  - `onClick` é opcional: se ausente renderiza `<div>`, se presente vira
    `<button>`. Preparado para reuso em scouting e no seletor de
    substituições do `InteractiveMatchCenter` sem precisar reescrever o
    componente — esses dois pontos de reuso **não foram alterados** nesta
    etapa (fica mapeado para quando esses submódulos/telas forem abordados).

**Arquivos alterados**
- `frontend/client/src/pages/Home.tsx` — bloco `.roster-row` da view de
  elenco (`isTeam`) trocado por `<div className="player-grid">` mapeando
  `workspace.squad.players` para `<PlayerCard>`. Nenhum `onClick` passado
  nesta etapa (o comportamento anterior também não tinha ação de clique —
  o `ChevronRight` era decorativo). Import de `PlayerCard` adicionado;
  `ChevronRight` continua em uso em outros pontos do arquivo (`layer-row`).
- `frontend/client/src/index.css` — regras `.roster-row` / `.roster-number`
  removidas (sem uso restante no projeto, confirmado por busca) e
  substituídas por bloco `.player-grid` / `.player-card*`: grid responsivo
  (`auto-fill, minmax(215px,1fr)` → `minmax(150px,1fr)` em ≤760px, mesmo
  breakpoint usado pelo `staff-market-grid`), mesmo tratamento de hover
  (borda superior colorida + leve elevação) já usado em `.staff-market-card`,
  para manter a linguagem visual consistente entre os cartões do app.
  `.muted-status` foi mantida como está (sem variante `.active` nova — ela
  já não existia antes desta mudança).

**Decisão de escopo (menor impacto):** não foi adicionado nenhum modal ou
navegação de detalhe ao clicar no card — a view de elenco continua
somente leitura, igual ao comportamento anterior. Reuso em scouting e no
seletor de substituições fica para quando esses submódulos/telas específicas
forem tratados, evitando mudar contratos de dados fora do escopo desta
etapa.

**Risco:** baixo. Nenhum contrato de dados (tRPC) mudou, nenhuma rota mudou;
`PlayerCardData` espelha exatamente o tipo já retornado por
`server/engineState.ts` (`squad.players`). Mudança é apresentacional e
localizada a `pages/Home.tsx` + `index.css` + um componente novo.

---

## Submódulo 3 — Gráficos reais (recharts) ✅

**Objetivo:** trocar a primeira lista textual que na verdade é dado
comparável (gols e assistências por atleta) por um gráfico de verdade, em
vez de continuar reaproveitando o componente de card de evento (ícone +
texto) para isso.

**Escolha de escopo (menor impacto):** dentre os candidatos possíveis —
caixa semanal, classificação (`standings-panel`, tabela com 6 colunas
numéricas), e "Atletas em destaque" (`PRODUÇÃO INDIVIDUAL`, painel geral) —
optou-se pelo último. A classificação já é bem servida por uma tabela (a
informação — V/E/D/SG/pontos — é densa demais para virar uma única barra
sem perder colunas) e o caixa semanal não tem série histórica persistida
(só o valor atual), então não há o que plotar como gráfico ainda. O ranking
de artilheiros/garçons, por outro lado, já era comparação entre atletas —
exatamente o que um gráfico de barras resolve melhor que uma lista.

**Arquivos novos**
- `frontend/client/src/components/PlayerProductionChart.tsx` — componente
  `<PlayerProductionChart data={PlayerProductionDatum[]} />` usando
  `recharts` (`BarChart` horizontal, uma barra para gols e outra para
  assistências por atleta). Tooltip e eixos customizados com a tipografia
  (`Space Grotesk`) e paleta do projeto — nada do estilo padrão do
  Recharts ficou visível. As cores são hex fixo espelhando os tokens de
  `:root` (comentário no arquivo explica por quê: Recharts define
  `fill`/`stroke` como atributos SVG, não propriedades CSS herdadas, então
  `var()` não é confiável ali).

**Arquivos alterados**
- `frontend/client/src/pages/Home.tsx` — seção `PRODUÇÃO INDIVIDUAL` do
  painel geral (`Dashboard`): a lista de até 5 `event-card` (ícone de bola +
  texto "X gol(s) · Y assistência(s)") foi trocada pelo gráfico. Um novo
  `useMemo` (`productionData`) ordena `playerStatsQuery.data.players` por
  gols+assistências, pega os 5 primeiros e resolve o nome de cada atleta via
  `workspace.squad.players` (mesmo padrão de `playerById` já usado na view
  de elenco) — a consulta de stats sozinha só tem `playerId`, sem nome.
  O `<span className="table-legend">G · A · MIN</span>` do cabeçalho da
  seção foi removido por ficar redundante com a legenda própria do gráfico
  (que também não mostra mais "MIN" nem "cartões" — informação que
  continua disponível, sem gráfico, na lista completa de
  `ESTATÍSTICAS DA TEMPORADA` dentro da view de elenco, que não foi
  alterada nesta etapa).
- `frontend/client/src/index.css` — bloco `.production-chart` /
  `.chart-legend` / `.chart-tooltip` adicionado logo após as regras de
  `.standings-panel`. Import do `Goal` (ícone usado só no `event-card`
  removido) continua em uso em outros pontos do arquivo, então não foi
  retirado.

**Decisão de escopo (menor impacto):** a lista `ESTATÍSTICAS DA TEMPORADA`
da view de elenco (filtrável por competição/atleta, com minutos e cartões)
**não foi alterada** — tem mais colunas de informação do que cabe bem em um
gráfico de 2 barras, e já é filtrável, o que um gráfico substituiria mal.
Fica como candidata a um gráfico mais rico (ex.: comparação com seletor de
métrica) numa etapa futura, se fizer sentido.

**Risco:** baixo. Nenhum contrato de dados (tRPC) mudou; `recharts` já era
dependência do projeto (`package.json`), só não estava em uso em nenhuma
tela. Mudança apresentacional localizada a uma seção de `pages/Home.tsx` +
`index.css` + um componente novo.

---

## Submódulo 4 — Micro-motion (framer-motion) ✅

**Objetivo:** dar vida a dois pontos que já existiam sem nenhum movimento —
o preenchimento de barra (`StatBar`) e a entrada da grade de cartões de
jogador (`PlayerCard`) — sem introduzir uma dependência de orquestração
nova nem tocar em telas que já não precisavam disso.

**Escolha de escopo (menor impacto):** hover/press já tinham micro-motion
resolvido em CSS puro (`.staff-market-card:hover`, `.player-card:hover`,
`.layer-row-button:active`) — não fazia sentido reescrever isso em
framer-motion só para trocar de tecnologia. Os dois pontos sem nenhuma
transição eram: a barra aparecendo já cheia (sem senso de "preenchimento")
e a grade de jogadores aparecendo tudo de uma vez, sem hierarquia de leitura
no primeiro carregamento. `framer-motion` já era dependência do projeto
(`package.json`), só não estava em uso em nenhum componente.

**Arquivos alterados**
- `frontend/client/src/components/StatBar.tsx` — a barra de preenchimento
  (`.stat-bar-fill`) virou `motion.div` com `initial={{ width: 0 }}` →
  `animate={{ width: ratio*100% }}`, 0.7s ease-out. Efeito propaga
  automaticamente para todo lugar que já usa `StatBar` (reputação/
  potencial/custo-benefício e eficiência de departamento em
  `StaffEconomyPanel`, potencial em `PlayerCard`) sem tocar em nenhum
  desses arquivos.
- `frontend/client/src/components/PlayerCard.tsx` — o cartão (`<div>` ou
  `<button>`, dependendo de `onClick`) virou `motion.div`/`motion.button`
  com fade + leve subida (`opacity 0→1`, `y 10→0`) ao montar. Novo prop
  opcional `index` (padrão `0`) escalona o atraso de entrada
  (`Math.min(index, 12) * 0.035s`, teto em 12 para grades grandes não
  demorarem demais a terminar de aparecer) — assim o cartão continua
  autossuficiente: não depende de nenhum container orquestrador do
  framer-motion no lugar onde é usado, então continua reaproveitável em
  scouting/seleção de substituições (mapeado desde o Submódulo 2) sem
  exigir nenhum wrapper extra.
- `frontend/client/src/pages/Home.tsx` — o `.map` que renderiza
  `PlayerCard` na view de elenco passou a incluir o índice
  (`(player, index) => <PlayerCard ... index={index} />`) para acionar a
  cascata acima. Nenhuma outra mudança neste arquivo.

**Acessibilidade:** ambos os componentes usam `useReducedMotion` do
framer-motion — com `prefers-reduced-motion` ativo no sistema, a duração
cai para `0` (StatBar) e o atraso/duração também caem para `0` (PlayerCard),
sem remover a animação por completo em código separado — é o mesmo
componente, só sem a transição.

**Risco:** baixo. Nenhum contrato de dados mudou; `framer-motion` já era
dependência declarada. Mudança é apresentacional, contida a dois
componentes já existentes e uma linha de integração em `Home.tsx`.

---

## Submódulo 5 — Elenco → formação tática ✅

**Objetivo:** a grade plana de `PlayerCard` (Submódulo 2) tratava titular e
reserva como a mesma unidade visual — só a etiqueta `Titular`/`Reserva`
dentro do card diferenciava. Fase 2 pede o elenco lido como "formação
tática": os 11 titulares agrupados por linha de campo (ataque, meio-campo,
defesa, goleiro), como uma escalação, com o banco separado abaixo.

**Escolha de escopo (menor impacto):** nenhuma posição tática (lateral-direito
vs. lateral-esquerdo, esquema 4-3-3 vs. 4-4-2 etc.) é persistida pelo motor —
`squad.players` só tem `position` (`Goleiro`/`Lateral`/`Zagueiro`/`Meia`/
`Atacante`), `side` (campo livre, sem enum documentado) e `status`
(`Titular`/`Reserva`). Por isso o agrupamento em linhas e a ordenação
esquerda→centro→direita dentro de cada linha são heurísticas 100%
client-side, sem inventar nem persistir nenhum dado que o motor não
fornece: `Lateral` e `Zagueiro` compartilham a linha de defesa (o rótulo de
posição no próprio token já distingue os dois), e a leitura de `side` usa
prefixo tolerante (`esq`/`dir`) em vez de comparação exata, já que o valor
exato não está documentado em nenhum contrato ou schema do projeto.

**Arquivos novos**
- `frontend/client/src/components/FormationPitch.tsx` — componente
  `<FormationPitch players={PlayerCardData[]} />`. Recebe exatamente o
  mesmo tipo já usado pelo `PlayerCard` (nenhum contrato novo). Agrupa os
  jogadores recebidos em 4 linhas (`ataque`/`meio`/`defesa`/`goleiro`) via
  `rowForPosition`, ordena cada linha por `side` via `sideRank`, e renderiza
  um "campo" (`.formation-pitch`, fundo escuro com linhas de campo
  decorativas) com uma linha por grupo não vazio. Cada jogador vira um
  `.formation-token` compacto (CR1 em destaque, nome, posição) — não é o
  `PlayerCard` completo, que é pensado para grade de leitura (dados de
  contrato/potencial/selos), enquanto o token de campo precisa ser pequeno o
  bastante para várias unidades caberem lado a lado numa mesma linha.
  Entrada com fade + leve escala por token, escalonada por ordem de
  aparição (mesmo padrão de cascata do Submódulo 4), respeitando
  `prefers-reduced-motion` via `useReducedMotion`.

**Arquivos alterados**
- `frontend/client/src/pages/Home.tsx`
  - Dois novos `useMemo` (`starterPlayers`, `benchPlayers`) derivam de
    `workspace.squad.players` filtrando por `status === "Titular"` — mesmo
    campo já lido por `squad.starters`/`squad.reserves` no card lateral,
    nenhuma query nova.
  - O bloco que renderizava todo `squad.players` como um único
    `player-grid` agora renderiza `<FormationPitch players={starterPlayers}
    />` (quando há titulares) seguido de um rótulo `BANCO · N reserva(s)` e
    o `player-grid` de `PlayerCard` já existente, agora só com os reservas.
    O `PlayerCard` e sua grade continuam exatamente como no Submódulo 4 —
    só o conjunto de jogadores que chega até ele mudou (reservas, não mais
    o elenco inteiro).
  - Import de `FormationPitch` adicionado; nenhum outro import mudou.
- `frontend/client/src/index.css` — bloco `.formation-pitch` /
  `.formation-row*` / `.formation-token*` / `.formation-bench-label`
  adicionado logo após as regras `.player-grid` existentes. Paleta reaproveita
  os tokens já declarados em `:root` (`--grass`, `--cobalt`, `--ink`); as
  linhas decorativas do campo (círculo central + linha de meio-campo) seguem
  o mesmo padrão visual já usado em `.hero-pitch-lines` (banner da página
  inicial), sem introduzir um novo motivo gráfico ao projeto.

**Decisão de escopo (menor impacto):** o token de campo não é clicável e não
abre detalhe — mesma leitura somente-leitura que a view de elenco já tinha
antes desta etapa. `FormationPitch` não foi conectado ao
`InteractiveMatchCenter` (que já tem sua própria lógica de escalação/
substituição) nem ao seletor de reservas mapeado desde o Submódulo 2 — o
escopo desta etapa é só a leitura do elenco no menu "Time", não a tela de
partida.

**Risco:** baixo. Nenhum contrato de dados (tRPC) mudou, nenhuma rota mudou;
`FormationPitch` consome o mesmo `PlayerCardData` do `PlayerCard`. Validado
com `tsc --noEmit` (sem novos erros — os únicos erros pré-existentes no
projeto são de tipos de `@testing-library/react` em arquivos de teste não
relacionados) e `vite build` (build de produção concluído sem erros).

---

## Submódulo 6 — CT como planta baixa ✅

**Objetivo:** dívida deixada explicitamente pelo Submódulo 1 — a lista
"DEPARTAMENTOS ATUAIS" do CT (`.ct-member-row`, mesmo componente visual
genérico usado para "EQUIPE ATIVA", uma lista de pessoas) reformulada por
completo como planta baixa: cada departamento vira uma "sala" num desenho
técnico, em vez de mais uma linha de lista com nome + eficiência em texto.

**Escolha de escopo (menor impacto):** dentre as três leituras de
departamento que coexistem na tela do CT — "DEPARTAMENTOS ATUAIS"
(`workspace.staff.departments`, dentro de `ct-state-grid`), "TREINAMENTO /
INVENTÁRIO PERSISTIDO" (`ct-training-grid`, já tratado com `StatBar` no
Submódulo 1) e as ofertas de compra/evolução (`department-offer-grid`, já
com layout de cartão desde antes deste plano) — só a primeira foi
reformulada aqui. É a única que ainda usava o padrão de lista genérica
(texto + eficiência em string), é a que foi explicitamente mapeada para
esta etapa, e "planta baixa" como metáfora se aplica ao *estado atual* da
estrutura (o que já existe fisicamente no CT), não ao catálogo de ofertas
(que é uma vitrine de compra, já bem servida por cartões) nem ao inventário
de treinamento (que já tem sua própria leitura com `StatBar` e um parágrafo
de contexto sobre desenvolvimento individual, que uma planta baixa
substituiria mal).

**Arquivos novos**
- `frontend/client/src/components/CtFloorPlan.tsx` — componente
  `<CtFloorPlan departments={CtDepartmentDatum[]} />`. Recebe exatamente
  `workspace.staff.departments` (mesmo array já consultado pela lista que
  substitui — nenhuma query nova). Renderiza um contêiner com textura de
  papel milimetrado (`repeating-linear-gradient` reaproveitando `--cobalt`
  em baixa opacidade, sem paleta nova) e uma sala (`.ct-floor-plan-room`,
  borda tracejada) por departamento: rótulo do departamento, nível,
  capacidade e eficiência como `StatBar compact` — os mesmos três dados que
  a lista antiga já mostrava (nome, capacidade, eficiência) mais o nível
  que já aparecia à parte (`<strong>NÍVEL {level}</strong>`), nenhum dado
  novo inventado. Entrada com fade + leve subida por sala, escalonada por
  ordem (mesmo padrão de cascata dos Submódulos 4 e 5), respeitando
  `prefers-reduced-motion`.

**Arquivos alterados**
- `frontend/client/src/components/StaffEconomyPanel.tsx` — dentro de
  `ct-state-grid`, o `.map` que gerava uma `.ct-member-row` por departamento
  em "DEPARTAMENTOS ATUAIS" foi trocado por
  `<CtFloorPlan departments={workspaceQuery.data.staff.departments} />`.
  "EQUIPE ATIVA" (lista de profissionais, ao lado) **não foi alterada** —
  planta baixa é uma metáfora de espaço/estrutura, não se aplica bem a uma
  lista de pessoas. Import de `CtFloorPlan` adicionado; nenhum outro import
  ou query mudou.
- `frontend/client/src/index.css` — bloco `.ct-floor-plan` /
  `.ct-floor-plan-grid` / `.ct-floor-plan-room*` adicionado logo após as
  regras de `.ct-state-grid` existentes. `.ct-member-row` **não foi
  removida**: continua em uso em "EQUIPE ATIVA" nesta mesma tela.

**Decisão de escopo (menor impacto):** a planta baixa não é clicável e não
abre detalhe por departamento — mesma leitura somente-leitura que a lista
anterior já tinha. O card de oferta (`department-offer-grid`, com o botão
"Comprar"/"Evoluir") continua sendo o único ponto de ação sobre os
departamentos; a planta baixa é puramente informativa, mostrando o que já
foi construído. Unificar as três leituras de departamento (estado atual,
treinamento persistido, ofertas) num único desenho fica como candidata a
uma etapa futura, se fizer sentido depois que Fase 2 estiver completa —
nesta etapa optou-se por resolver a dívida específica já mapeada, sem
expandir escopo.

**Risco:** baixo. Nenhum contrato de dados (tRPC) mudou, nenhuma rota
mudou; `CtFloorPlan` consome o mesmo formato já retornado por
`workspace.staff.departments` (`server/engineState.ts`). Validado com
`tsc --noEmit` (mesmos erros pré-existentes de `@testing-library/react` em
arquivos de teste, nenhum erro novo) e `vite build` (build de produção
concluído sem erros).

---

## Submódulo 7 — Calendário como linha do tempo ✅

**Objetivo:** a aba "Calendário" de Dia do jogo (`view === "calendario"`)
mostrava `filteredFixtures` como uma lista plana (`.calendar-list`) — uma
linha por partida, todas com o mesmo peso visual, com "rodada N" apenas
como texto dentro da legenda de cada linha. Vira uma linha do tempo:
partidas agrupadas por rodada, cada rodada com seu próprio marcador num
trilho vertical, em vez de repetir "rodada" como metadado dentro de cada
linha.

**Escolha de escopo (menor impacto):** dentre as views de `MatchesPage`
("Competições", "Tabela", "Calendário", "Resultados"), só "Calendário" foi
reformulada. "Tabela" é uma classificação — tabela é exatamente a leitura
certa para 6 colunas numéricas comparáveis, uma linha do tempo serviria
mal. "Resultados" já tem sua própria leitura cronológica-de-placar
(`result-list` + `form-slots` com os últimos 5 resultados em sequência
horizontal) — decisão de manter fora do escopo, registrada abaixo. O app já
tinha um precedente visual de linha do tempo — `.week-summary-timeline`, no
modal de resumo de avanço de semana — mas esse é um componente de modal
tematizado (fundo escuro, paleta própria `#153b2d`/`#d8ef8e`) para um
contexto diferente (resumo de decisão, não navegação recorrente); o
`MatchTimeline` novo não o reaproveita diretamente porque a aba
Calendário vive num painel claro (`--paper-bright`), mas segue a mesma
ideia estrutural (trilho + marcador + entradas), então a metáfora de
"linha do tempo" fica consistente entre os dois lugares do app que já a
usam, só com paleta adaptada ao contexto claro.

**Arquivos novos**
- `frontend/client/src/components/MatchTimeline.tsx` — componente
  `<MatchTimeline fixtures={TimelineFixture[]} competitionName={string} />`.
  Recebe exatamente `filteredFixtures` (mesmo array já usado pela lista
  antiga — nenhuma query nova) e agrupa por `round` preservando a ordem de
  chegada (a API já entrega `upcomingFixtures` em ordem cronológica).
  Renderiza um marcador de rodada (ponto + rótulo `RODADA N`, ou `RODADA A
  DEFINIR` quando `round` é `null`) seguido das partidas daquela rodada.
  `formatDate`/`formatTime` duplicam de propósito as funções homônimas já
  existentes em `pages/Home.tsx` (mesma lógica de `Intl.DateTimeFormat`) —
  duplicação pequena e deliberada para manter o componente autossuficiente,
  sem import circular com a página que o consome, mesmo padrão de
  auto-suficiência do `PlayerCard` (Submódulo 2) e do `FormationPitch`
  (Submódulo 5). Entrada com fade + leve deslocamento horizontal por
  partida, escalonada por ordem de aparição (mesmo padrão de cascata dos
  Submódulos 4, 5 e 6), respeitando `prefers-reduced-motion`.

**Arquivos alterados**
- `frontend/client/src/pages/Home.tsx` — dentro de `view === "calendario"`,
  o `.map` que gerava uma linha de `.calendar-list` por partida foi trocado
  por `<MatchTimeline fixtures={filteredFixtures} competitionName={...} />`.
  O estado vazio ("Nenhuma partida agendada") passou a usar
  `.entity-lookup-empty`, uma classe de estado vazio já padronizada no
  projeto (usada em `EntityLookupPanel`), em vez de reaproveitar o layout
  de linha de `.calendar-list` que deixou de existir. Import de
  `MatchTimeline` adicionado; nenhuma query ou outro trecho do arquivo
  mudou.
- `frontend/client/src/index.css` — `.calendar-list` (linha antiga) removida
  e substituída por `.match-timeline` / `.match-timeline-round*` /
  `.match-timeline-entries` / `.match-timeline-entry*`, reaproveitando os
  tokens já declarados em `:root` (`--cobalt`, `--line`, `--paper-bright`),
  sem paleta nova. `.calendar-main`/`.calendar-aside` (moldura da aba) não
  mudaram.

**Decisão de escopo (menor impacto):** a linha do tempo não é clicável —
mesma leitura somente-informativa que a lista anterior já tinha; nenhum
comportamento de navegação foi adicionado ou removido. "Resultados"
(histórico de placares) fica como candidata a uma leitura cronológica
equivalente numa etapa futura, se fizer sentido — não foi tocada aqui para
não expandir o escopo desta etapa além da dívida específica do calendário
de próximos compromissos.

**Risco:** baixo. Nenhum contrato de dados (tRPC) mudou, nenhuma rota
mudou; `MatchTimeline` consome o mesmo formato já retornado por
`dashboard.upcomingFixtures` (`server/engineState.ts`, tipo `MatchCard`).
Validado com `tsc --noEmit` (mesmos erros pré-existentes de
`@testing-library/react` em arquivos de teste, nenhum erro novo) e
`vite build` (build de produção concluído sem erros).

---

## Submódulo 8 — Dashboard como HUD ✅

**Objetivo:** a página inicial ("Seu Clube") que mostrava um layout genérico
(hero + métricas + seções de conteúdo em coluna) vira um HUD estilo jogo, com
quadrantes de leitura rápida (Escalação, Comissão, Estádio, Prospecção) e uma
barra de status no topo. O dashboard passa de "painel administrativo" para
"painel de jogo".

**Escolha de escopo (menor impacto):** o novo `ClubHUD` é um componente que
encapsula exatamente a leitura dos quadrantes estruturais do clube
(`squad`, `staff`, `stadium`, `scouting`) — dados que já fluem pela query
`workspace` existente. A seção anterior de "SITUAÇÃO ATUAL" (club-card) fica
preservada no layout; o ClubHUD se insere logo após o hero panel e antes dos
gráficos de produção individual, oferecendo uma visão HUD nova sem remover a
leitura histórica. Fica como candidata a fase futura a unificação completa do
novo HUD com as métricas históricas, consolidando-as num único painel.

**Arquivos novos**
- `frontend/client/src/components/ClubHUD.tsx` — componente
  `<ClubHUD workspace={WorkspaceQueryResponse} onNavigateToMarket? onUpdateInfo? />`.
  Renderiza:
  - `.hud-status-bar` (topo): resumo rápido — contador de saúde (atletas não
    lesionados), profissionais contratados, status de sincronização (pip
    animado online/offline), sem dados novos inventados;
  - `.hud-grid`: layout adaptável de quadrantes com `.hud-quadrant-large`
    (elenco com formação tática embutida + banco de reservas em mini-lista) e
    três `.hud-quadrant-mini` (comissão, estádio, prospecção), cada um com
    ícone, label, meta (resumo) e conteúdo (mini-stats ou ações);
  - `.hud-footer`: botão de atualizar informações + mensagem contextual;
  - estados vazios e fallbacks honesto, reutilizando a lógica já existente em
    `pages/Home.tsx` (sem inventar dados ausentes);
  - entrada cascata (por quadrante via `data-index`) + fade-in dos bench items,
    respeitando `prefers-reduced-motion`.

**Arquivos alterados**
- `frontend/client/src/pages/Home.tsx` — dentro de `Dashboard()`, logo após
  `</section>` do hero panel, adicionada uma `<section className="hud-section">
  <ClubHUD ... /></section>`. Nenhuma query ou contrato de dados mudou;
  `ClubHUD` consome `workspace` que já estava sendo consultado. Import de
  `ClubHUD` adicionado ao topo. Nenhuma outra renderização foi removida —
  métricas, produução individual e "SITUAÇÃO ATUAL" permanecem como estavam,
  garantindo compatibilidade com fluxos existentes.
- `frontend/client/src/index.css` — bloco `.club-hud` / `.hud-status-bar` /
  `.hud-grid` / `.hud-quadrant*` / `.hud-mini-*` / `.hud-bench-*` /
  `.hud-empty-state` / `.hud-footer` adicionado ao final. Reutiliza tokens já
  declarados (`:root`): `--cobalt`, `--coral`, `--grass`, `--paper`,
  `--line`, `--ink`, `--ink-muted`, sem paleta nova. Animações: fade +
  slide-in na entrada (cascata por `data-index`), pulse para `.hud-status-pip`,
  sem transições em `prefers-reduced-motion`. Breakpoint responsivo 760px para
  grid de quadrantes passar a 1 coluna em mobile.

**Decisão de escopo (menor impacto):** o ClubHUD não é interativo além dos
botões "Contratar" e "Gerenciar" (que disparam `onNavigateToMarket`). A formação
tática no quadrante principal reaproveita `<FormationPitch>` já pronto do
Submódulo 5 — nenhuma lógica nova, só reuso visual. Banco de reservas é uma
micro-lista (máximo 4 visíveis, com "+N" para overflow) — não é editável e não
abre detalhes de jogador nesta etapa; clique em um banco item fica mapeado para
quando o seletor de substituições do `InteractiveMatchCenter` for reformulado
para usar cards (Submódulo futuro). Mini-stats dos quadrantes 2–4 são leitura
somente, com tons de cor (grass/cobalt/coral) indicando saúde (profissionais
contratados, capacidade do estádio, missões ativas), mas sem hover interativo
além da ação explícita do botão mini-action.

**Risco:** baixo. Nenhum contrato de dados (tRPC) mudou, nenhuma rota mudou;
`ClubHUD` consome `workspace` (tipo `WorkspaceQueryResponse`) que já existe.
Validado com `tsc --noEmit` (sem erros novos) e `vite build` (build de
produção sem erros).

---

## Submódulo 9 — Polimento ✅

**Objetivo:** os quatro itens da Fase 3 (som/háptico, empty states,
StatusChip, revisão de timing). Como os quatro têm risco e escopo bem
diferentes entre si, a etapa foi tratada com a mesma régua de "menor
impacto primeiro" dos submódulos anteriores: os três itens de escopo
puramente visual (9a StatusChip, 9b empty/loading states, 9c timing) foram
implementados e validados numa primeira passada; o quarto (9d, som/háptico)
ficou registrado como pendência explícita e foi implementado numa segunda
passada, depois que a decisão de produto (usar síntese local em vez de
assets licenciados, ver detalhes abaixo) ficou clara — sem exigir retrabalho
nos itens 9a–9c.

### 9a. StatusChip ✅

**Arquivos novos**
- `frontend/client/src/components/StatusChip.tsx` — componente
  `<StatusChip label tone icon? badge? compact />`. Cinco tons (`grass`,
  `cobalt`, `coral`, `ink`, `neutral`), todos mapeados para os tokens já
  existentes em `:root` — nenhuma cor nova, mesmo princípio do `StatBar`
  (Submódulo 1).

**Arquivos alterados**
- `frontend/client/src/components/PlayerCard.tsx` — o status
  (`Titular`/`Reserva`), que era texto puro em `.muted-status`/
  `.muted-status.active`, virou `<StatusChip tone="grass|neutral" compact />`.
- `frontend/client/src/index.css` — bloco `.status-chip*` adicionado ao
  final, reaproveitando `--grass`/`--cobalt`/`--coral`/`--ink`/`--line`.
  `.muted-status` **não foi removida** — ainda é usada em `.layer-row`
  (Submódulo 6/CT) para o rótulo lateral discreto da lista de camadas, um
  contexto onde um chip com borda seria ruído visual, não clareza.

**Decisão de escopo (menor impacto):** o `StatusChip` não substituiu os
outros rótulos de status ad hoc do app (`.asset-ready`/`.asset-warning`/
`.asset-missing`/`.asset-pending` na prévia de identidade, o `em` verde de
`.stadium-component`, o `.finance-alert.is-warning/.is-ok`). Cada um desses
já tem um tratamento visual próprio pensado para seu painel (borda lateral
colorida no card de identidade, selo textual no componente de estádio,
faixa colorida nas finanças) — trocar por chip genérico apagaria uma pista
visual que já funciona nesses contextos específicos, então ficam de fora
desta etapa. `PlayerCard` foi o primeiro uso porque era o caso mais puro de
"rótulo de status sem nenhum tratamento visual próprio", exatamente o que o
componente resolve.

### 9b. Empty states polidos ✅ (com loading states separados)

**Arquivos novos**
- `frontend/client/src/components/EmptyState.tsx` — componente
  `<EmptyState icon title description? actionLabel? onAction? />`.
  Generaliza o padrão que já existia em `.hud-empty-state` (Submódulo 8:
  ícone apagado + título + frase + ação opcional) para uso fora do HUD,
  reaproveitando a mesma classe-base (`.empty-state`, variante standalone de
  `.hud-empty-state`) — sem paleta nova.
- `frontend/client/src/components/LoadingState.tsx` — componente
  `<LoadingState label />`. Criado na continuação desta etapa para resolver
  a lacuna identificada na primeira passada: vários pontos usavam a mesma
  classe (`.entity-lookup-empty`/`.ct-state-empty`) tanto para "carregando"
  quanto para "vazio de verdade", sem nenhuma pista visual de qual dos dois
  era. `LoadingState` usa um ícone `Loader2` girando (`.spin`, já existente
  e usado em `InteractiveMatchCenter`/`AIChatBox` — nenhuma animação nova) e
  fundo neutro sem borda tracejada, para que só o `EmptyState` (borda
  tracejada, ícone parado) signifique "não há dados".

**Arquivos alterados**
- `frontend/client/src/components/StaffEconomyPanel.tsx` — os dois estados
  vazios de "EQUIPE ATIVA" e "DEPARTAMENTOS ATUAIS" (que eram um `<p
  className="ct-state-empty">` com frase solta) agora usam `<EmptyState>`
  com ícone (`UsersRound`/`Building2`, já importados no arquivo) e, no caso
  de equipe ativa, um botão "Ir para o Mercado" (`onNavigateToMarket`, prop
  que o componente já recebia).
- `frontend/client/src/pages/Home.tsx`
  - Elenco vazio ("Nenhum jogador está disponível..."): trocado de
    `.entity-lookup-empty` para `<EmptyState icon={Users} ... actionLabel="Ir
    para o Mercado" onAction={() => onSectionChange("mercado")} />` — ação
    nova porque o texto já indicava a solução (ir ao Mercado) sem oferecer o
    atalho.
  - Calendário vazio ("Nenhuma partida agendada"): trocado para
    `<EmptyState icon={CalendarDays} description={waitingMessage} />`, sem
    ação (não há um destino óbvio quando não há competição selecionada).
  - Elenco *carregando* ("Atualizando elenco…"): trocado de
    `.entity-lookup-empty` para `<LoadingState>` — antes usava a mesma
    aparência do "elenco vazio" acima, agora é visualmente distinto.
  - Ledger financeiro: os três estados (carregando, com lançamentos, vazio)
    que colapsavam carregando+vazio na mesma classe agora usam
    `<LoadingState label="Atualizando movimentações…" />` e
    `<EmptyState icon={CircleDollarSign} title="Nenhum lançamento
    financeiro" ... />` respectivamente.
- `frontend/client/src/components/OperationsPanel.tsx` — os dois pares
  carregando/vazio (snapshots e auditoria de restauração) migrados da mesma
  forma: `LoadingState` para o carregamento, `EmptyState` (ícones `Archive`
  e `ShieldCheck`, já importados no arquivo) para o vazio real.
- `frontend/client/src/index.css` — blocos `.empty-state` e `.loading-state`
  adicionados ao final do arquivo.

**O que ficou de fora, deliberadamente:** o único uso restante de
`.entity-lookup-empty` em `Home.tsx` é a dica de formulário "Informe uma
identificação para consultar o escudo ou ativo disponível" na área de
Identidade Oficial — não é nem carregamento nem vazio, é uma instrução de
preenchimento; migrar isso para `EmptyState`/`LoadingState` distorceria a
semântica dos dois componentes, então foi deixado como texto simples.
`.competition-empty`, `.result-empty`, `.sponsor-empty`,
`.stadium-operations.empty`, `.economy-empty` e `.empty-panel` continuam
como estavam — têm identidade editorial própria por painel (borda lateral
colorida, ícone temático, layout específico do painel) e trocá-los por um
componente genérico apagaria uma pista visual que já funciona nesses
contextos, mesmo raciocínio já registrado para o `StatusChip` acima.

### 9c. Revisão de timing de transições ✅ (auditoria, sem mudança de código)

Levantamento de todas as durações/easings usados nos Submódulos 1–8
(`StatBar`, `PlayerCard`, `FormationPitch`, `CtFloorPlan`, `MatchTimeline`,
`ClubHUD`): todos seguem o mesmo vocabulário — entrada com
`opacity`+`y`/`width`, `duration` entre `0.28s` e `0.7s`, `ease: "easeOut"`,
cascata por índice (`Math.min(index, N) * delay`) e todos checam
`useReducedMotion`/`prefers-reduced-motion` antes de animar (zerando a
duração, nunca escondendo o conteúdo). Hover/active de botões usa
consistentemente `160–180ms ease-out`. Conclusão da auditoria: os timings já
estão consistentes entre si — não havia divergência que justificasse
reescrever componentes que já funcionam, então nenhuma mudança de código foi
feita aqui, só o registro de que a checagem foi feita.

### 9d. Som e feedback háptico ✅

**Escolha de escopo (menor impacto):** a barreira registrada na primeira
passada — "adicionar som exige escolher/licenciar assets" — foi contornada
sem escolher nem licenciar nada: os tons são **sintetizados em tempo real**
via Web Audio API (osciladores simples, envelope de volume curto), então
nenhum arquivo de áudio novo entra no repositório e nenhuma dependência de
player (`howler`, `use-sound` etc.) foi adicionada — confirmado no
`package.json` do frontend antes de começar. O háptico usa
`navigator.vibrate` diretamente (Web API nativa, sem dependência), com todas
as limitações já registradas nesta etapa (só alguns navegadores móveis, só a
partir de gesto do usuário) — degradação silenciosa nos demais casos, o app
nunca depende do feedback tátil para funcionar.

O ponto de integração é exatamente o que a decisão original já apontava: os
eventos discretos de `toast.success(...)`/`toast.error(...)` (sonner) já
espalhados pela interface — cada um ganhou uma chamada irmã de `notify(...)`
no mesmo `onSuccess`/`onError`, sem alterar nenhuma lógica de mutação,
invalidação de cache ou mensagem de toast existente.

**Arquivos novos**
- `frontend/client/src/lib/feedback.ts` — módulo puro (sem React), duas
  funções: `playFeedbackTone(kind)` (sintetiza um tom curto via
  `AudioContext`/osciladores — dois timbres, um por `FeedbackKind`, mapeando
  a mesma leitura binária que `toast.success`/`toast.error` já usam) e
  `triggerHapticFeedback(kind)` (`navigator.vibrate` com padrão curto por
  tom). Ambas com fallback silencioso via `try/catch` e checagem de suporte
  (`typeof window`, `typeof navigator.vibrate`) — nenhuma delas lança erro
  nem interrompe o fluxo se o navegador não suportar.
- `frontend/client/src/contexts/FeedbackContext.tsx` — `FeedbackProvider`/
  `useFeedback()`, no mesmo formato do `ThemeContext` já existente
  (`switchable`/`localStorage`): estado `enabled` (padrão `true`) persistido
  em `localStorage` (`feedback-enabled`), `toggleFeedback()` e `notify(kind)`
  — que só chama as duas funções de `lib/feedback.ts` quando `enabled` é
  verdadeiro. Nenhuma paleta ou asset novo.

**Arquivos alterados**
- `frontend/client/src/App.tsx` — `FeedbackProvider` adicionado dentro do
  `ThemeProvider` já existente, envolvendo `TooltipProvider`/`Home`. Nenhuma
  outra mudança.
- `frontend/client/src/pages/Home.tsx` — dentro de `Header` (barra de topo,
  `.top-actions`), um novo `<button className="icon-btn">` com ícone
  `Volume2`/`VolumeX` (já disponíveis em `lucide-react`, mesmo pacote de
  ícones do resto do app) alterna `toggleFeedback()`, reaproveitando a
  classe `.icon-btn` já usada pelo sino de alertas — nenhuma classe CSS
  nova. Dentro de `MatchesPage`, `notify("success"/"error")` adicionado às
  mutações `advanceUntilMatch` e `advanceWeek` (chegar à próxima partida e
  avançar a semana), junto dos `toast.success`/`toast.error` já existentes.
- `frontend/client/src/components/StaffEconomyPanel.tsx` — `notify(...)`
  adicionado às mutações de contratação (`hireMutation`) e evolução de
  departamento (`departmentMutation`).
- `frontend/client/src/components/InteractiveMatchCenter.tsx` — `notify(...)`
  adicionado ao resultado oficial da partida (sucesso) e à falha de registro
  (erro).
- `frontend/client/src/components/StadiumOperationsPanel.tsx` — `notify(...)`
  adicionado às três mutações do estádio (preparar temporada, evoluir
  componente, atualizar preço de ingresso).
- `frontend/client/src/components/SponsorshipPanel.tsx` — `notify(...)`
  adicionado à mutação de aceite de patrocínio.
- `frontend/client/src/components/OperationsPanel.tsx` — `notify(...)`
  adicionado às mutações de snapshot (criar/restaurar). O botão manual
  "Atualizar" do fechamento financeiro (`refreshFinance`) **não** recebeu
  `notify(...)` — não é uma mutação com risco de falha, é um `invalidate()`
  de leitura seguido de toast informativo, sem par sucesso/erro real.

**Decisão de escopo (menor impacto):** nem todo `toast(...)` do app foi
conectado a `notify(...)` — só os pares `toast.success`/`toast.error` que
representam o resultado de uma mutação real (contratar, evoluir, confirmar
resultado, patrocínio, snapshot, avançar semana/calendário). Toasts
puramente informativos sem risco de falha (ex.: "Perfil do manager será
conectado na próxima etapa", `refreshFinance`, o toast simples de
`markRead`) ficaram de fora — reforço sonoro/háptico em toda notificação
banalizaria o sinal nos momentos que de fato importam (dinheiro comprometido,
resultado oficial de partida), o mesmo raciocínio de "não virar ruído" já
usado para o `StatusChip` (9a) e os empty states (9b).

O toggle de mudo fica só na barra de topo (`Header`), sem página de
configurações dedicada — o app não tem uma tela de "Configurações" hoje;
criar uma só para este único controle expandiria escopo além do pedido.

**Risco:** baixo. Nenhum contrato de dados (tRPC) mudou, nenhuma rota mudou,
nenhuma dependência nova foi adicionada ao `package.json`. `lib/feedback.ts`
é puro e sem efeito colateral fora de `AudioContext`/`navigator.vibrate`
(ambos opcionais, com fallback). `FeedbackContext` segue exatamente o padrão
já validado pelo `ThemeContext`. Os arquivos com lógica tocados só ganharam
uma chamada adicional dentro de callbacks `onSuccess`/`onError` já
existentes — nenhuma mutação, invalidação de cache ou mensagem de toast foi
alterada.

**Validação:** revisão manual linha a linha de todos os arquivos alterados
(balanceamento de chaves/parênteses verificado programaticamente, escopo de
cada `notify(...)` conferido contra a declaração de `useFeedback()` no mesmo
componente). Checagem de sintaxe/tipos com `tsc` do ambiente nos dois
arquivos novos (mesma limitação já registrada nos Submódulos 1–9c: sem
`node_modules`/tipos de `react`/`react/jsx-runtime` disponíveis neste
ambiente sem rede — os erros retornados são exclusivamente dessa causa, um
deles corrigido preventivamente mesmo assim, `prev: boolean` tipado
explicitamente no `setEnabled` de `FeedbackContext`). Continua recomendado
rodar `pnpm install && pnpm exec tsc --noEmit && pnpm exec vite build` no
frontend assim que houver rede disponível, como nos Submódulos 1–9c.

**Risco geral do Submódulo 9 (9a–9d):** baixo. Nenhum contrato de dados
(tRPC) mudou, nenhuma rota mudou, nenhuma dependência nova foi adicionada.
`StatusChip`, `EmptyState`, `LoadingState` são componentes puramente
apresentacionais e aditivos; `lib/feedback.ts`/`FeedbackContext` (9d) são
puros e opcionais (com fallback silencioso). Os arquivos com lógica tocados
(`StaffEconomyPanel.tsx`, `Home.tsx`, `OperationsPanel.tsx`,
`InteractiveMatchCenter.tsx`, `StadiumOperationsPanel.tsx`,
`SponsorshipPanel.tsx`) só trocaram o JSX de apresentação de estados já
existentes (9b) ou adicionaram uma chamada a `notify(...)` dentro de
callbacks `onSuccess`/`onError` já existentes (9d), sem alterar nenhuma
query, mutação, invalidação de cache ou condição.

**Validação:** revisão manual linha a linha dos arquivos alterados
(consistência de imports, props, tipos e balanceamento de chaves/parênteses
verificado programaticamente) **mais** uma checagem de sintaxe/tipos com o
`tsc` global do ambiente (`tsc --noEmit --jsx react-jsx --skipLibCheck`,
sem o `tsconfig.json`/`node_modules` do projeto — não substitui o build
real). Todos os erros retornados são de dois tipos, nenhum deles causado
por esta etapa: (a) ambiente sem os tipos de `react/jsx-runtime` e sem
`lib es2021` do projeto (`replaceAll`), esperado ao rodar fora do
`node_modules` real; (b) problemas pré-existentes em arquivos não tocados
nesta etapa (`App.tsx`, `ErrorBoundary.tsx`, `ThemeContext.tsx`) e um alerta
estrutural pré-existente em `EventCard`/`Home.tsx` sobre a prop `key`, nada
relacionado a `StatusChip`/`EmptyState`/`LoadingState`. Continua
recomendado rodar `pnpm install && pnpm exec tsc --noEmit && pnpm exec vite
build` no frontend assim que houver rede disponível, para a validação
completa e oficial, como nos
Submódulos 1–8.
