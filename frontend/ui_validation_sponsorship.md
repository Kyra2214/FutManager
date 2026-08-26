# Validação visual — Patrocinadores

## Contexto validado

| Ambiente | Caminho | Resultado |
|---|---|---|
| Desktop 1280×720 | `/?section=patrocinadores` | Área comercial exibe overall 63,5, quatro estrelas elegíveis, componentes de elenco/CT/estádio, três ofertas reais do Flamengo e estado vazio de missões antes da assinatura. |
| Mobile 375×812 | `/?section=patrocinadores` | Navegação, headline, selo de overall, cartões de proposta e seção de missões se reorganizam em uma coluna sem corte horizontal. |

## Estado real confirmado

O Flamengo foi lido do SQLite de estado com overall institucional **63,53**, quatro estrelas elegíveis e três propostas pendentes: Alvorada (4 estrelas), Órbita (3) e Verve (3). Nenhuma proposta foi aceita durante a validação visual.

## Cobertura adicional

O aceite, o crédito de sinal, a missão persistida e a invalidação de cache foram exercitados em banco temporário pelos testes de gateway e de interface.
