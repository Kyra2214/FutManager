# Validação visual — Estádio e ciclo semanal

| Viewport | Resultado |
|---|---|
| Desktop 1280×720 | A seção Estádio preserva a composição Editorial de Arquibancada. Quando os componentes econômicos ainda não existem, exibe o estado explícito de preparação e a ação `Preparar estádio`; não mostra capacidade ou bilheteria inventadas. |
| Mobile 375×812 | O título, banner, bloco de preparação e CTA permanecem legíveis em uma coluna, sem sobreposição de navegação ou corte do botão. |

O banco real do Flamengo não foi alterado durante a validação visual. A criação do estádio econômico é uma ação explícita, coberta pelo gateway e por testes em banco temporário.

## Estado persistido após bootstrap mundial

Após o bootstrap idempotente, o Maracanã passou a exibir os quatro componentes econômicos de nível inicial, capacidade de 12.000, manutenção semanal e controles de evolução. Em desktop, o painel mantém métricas e plano de evolução em duas colunas. Em 375×812, as métricas ficam em grade de duas colunas, os upgrades permanecem acionáveis e o controle de bilheteria segue legível sem transbordamento.

## Feed de alertas persistidos

As capturas finais de desktop e 375×812 confirmaram que o cabeçalho apresenta o sino de alertas e que a área “Feed de alertas” não simula notícias quando o SQLite não tem eventos para o Flamengo. O estado vazio informa essa ausência de forma explícita, sem desalinhamento em mobile. O popover de alertas possui suporte a contagem de não lidos e leitura confirmada pelo contrato tRPC; sua persistência foi validada em banco temporário pelos testes do gateway.
