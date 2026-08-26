# Patrocínios e missões comerciais — base de design

## Inspiração confirmada

O sistema será uma adaptação própria ao futebol; não reproduz marcas, interfaces nem dados de F1 Manager. A referência pública confirma três princípios úteis: pacotes com componente imediato, componente condicionado a metas e componente condicionado ao desempenho; ciclos de plano de seis semanas; e qualidade de oportunidade determinada por avaliação geral, instalações e apelo do elenco.[1][2][3]

## Regras do FutManager

Cada clube terá uma janela de propostas comerciais. Uma proposta permanece disponível por **três semanas**. Caso não seja aceita até a expiração, ela é encerrada automaticamente e o motor cria uma nova proposta elegível, que pode ter menos, igual ou mais estrelas. A mudança não é uma punição fixa: resulta da rotação de mercado e do overall institucional do clube no momento da nova rodada.

| Elemento | Regra v1 |
|---|---|
| Estrelas | 1 a 5; definem faixas de sinal, receita semanal, bônus de missão e rigor das metas. |
| Overall institucional | Média ponderada preparada para `elenco` (60%), `CT` (25%) e `estádio` (15%). Componentes ausentes entram como zero e são identificados no resumo. |
| Elegibilidade | O overall estabelece a estrela-base; há variação limitada de mercado para preservar surpresa sem impedir progressão. |
| Oferta | Três candidatas exclusivas a patrocinador principal por janela. Todas têm data de expiração e versão de geração. Pacotes secundários poderão ser adicionados em uma etapa posterior. |
| Contrato | Aceitar libera sinal imediatamente e receita semanal; nenhum contrato é renovado silenciosamente. |
| Missões | Metas de desempenho, estrutura, elenco ou engajamento para um período. Recompensa só é creditada quando a condição se torna verdadeira; prazo vencido encerra a missão sem recompensa. |
| Rotação | Processamento semanal expira ofertas pendentes, encerra missões vencidas e gera substituições idempotentes. |

## Parâmetros a manter configuráveis

As durações, pesos, tabelas de estrelas, valores e limites de variação serão constantes versionadas no motor. Receitas não representarão dados do mundo real; são valores de equilíbrio de jogo vinculados à folha semanal e à reserva econômica atual.

## Referências

[1] [F1 Manager 2024 — Deliver for Sponsors](https://www.f1manager.com/en-US/features/new/navigating-the-challenges-of-f1)

[2] [Epic Games — Sponsor packages in F1 Manager 2024](https://store.epicgames.com/news/f1-manager-2024-create-a-team-guide?lang=en-US)

[3] [F1 Manager — Improving Marketability](https://www.f1manager.com/2024/news/improving-marketability-f1r-manager-2024)
