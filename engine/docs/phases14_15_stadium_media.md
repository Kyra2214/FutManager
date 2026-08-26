# Fases 14 e 15 — Estádios, torcida, reputação, mídia e receitas

O motor agora possui estado agregado de estádio, torcida, reputação, presença, bilheteria, eventos, patrocinadores, contratos, metas, exposição e direitos de mídia no mesmo SQLite mutável.

## Fase 14

`SocialService` cria estádios com capacidade validada, capacidade utilizável, conforto, segurança, qualidade, estado e manutenção. Expansões possuem custo, histórico e lançamento no `FinanceLedger`; não alteram força esportiva.

A torcida é representada por um estado agregado, sem registros individuais. Reputação é separada em dimensões esportiva, nacional, internacional, comercial e histórica. A presença é calculada por capacidade, torcida, reputação, importância, visitante, estádio, preço e seed. A mesma partida retorna a presença já persistida, sem duplicar público.

## Fase 15

`CommercialService` cria patrocinadores fictícios, contratos, metas e bônus. Uma meta atingida usa referência idempotente e não pode ser paga duas vezes. O serviço também mantém perfil de mídia, eventos de exposição, receita de mídia e expiração de contratos.

Todas as receitas e despesas relevantes passam pelo `FinanceLedger`. Eventos e histórico preservam a origem da operação. O sistema não usa empresas reais, redes sociais reais ou serviços externos.

## Limitações

A integração automática completa do dia de jogo com resultado, público, reputação, mídia e IA ainda é uma extensão futura. Também não foram implementados dados reais de audiência, torcedores individuais, mídia real, regras fiscais, frontend, internet ou simulação mundial.
