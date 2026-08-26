# Rules Engine 2

O Rules Engine concentra as leis de carreira em `engine/rules/player_rules.py`. Os valores de idade, desenvolvimento, declínio, aposentadoria e retorno são **CONFIGURÁVEIS** e não representam fatos confirmados da fórmula original do Brasfoot.

O banco-base fornece apenas os campos nativos auditados. `cr1`, `cr2` e `rating_hash` permanecem separados e não são reinterpretados como potencial ou força.

A geração usa uma distribuição ponderada configurável e `seed` opcional para reprodutibilidade. O motor limita potencial e força ao intervalo configurado de 1 a 99.

A força própria do novo jogo é calculada como `potential * development_factor`, limitada pelo potencial. Essa é uma regra do novo motor, não uma reconstrução da fórmula original.

## Regras atuais

| Regra | Implementação |
|---|---|
| Idade inicial | Todo jogador criado pelo motor começa aos 16 anos |
| Potencial | Aleatório, entre 1 e 99, com seed opcional |
| Crescimento | Forte entre 16–22 e moderado entre 23–25 |
| Auge | Manutenção aproximada entre 26–30 |
| Declínio | Progressivo a partir da idade configurada |
| Aposentadoria | Evento explícito; não apaga identidade |
| Retorno | Nova geração após pelo menos uma temporada fora |
