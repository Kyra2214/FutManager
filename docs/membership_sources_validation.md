# Validação de memberships oficiais

## Decisão de governança

O SQL/GameState continua sendo a fonte única do estado jogável. Uma membership só é classificada como oficial quando a fonte externa fornece a competição e a temporada, a lista é integralmente mapeável aos clubes canônicos e não há ambiguidades.

## Resultado atual

| País | Temporada/fonte | Resultado | Comportamento no motor |
|---|---|---|---|
| Brasil | 2026, CBF | Membership oficial existente e auditada | Usa lista oficial |
| Itália | Catálogo oficial validado | Membership oficial existente e auditada | Usa lista oficial |
| Espanha | Catálogo oficial validado | Membership oficial existente e auditada | Usa lista oficial |
| Portugal | Catálogo oficial validado | Membership oficial existente e auditada | Usa lista oficial |
| Alemanha | Bundesliga 2026/27 | Matching integral 18/18, sem ambiguidades | Usa lista oficial |
| França | Ligue 1 2026/27 | Matching integral 18/18, sem ambiguidades | Usa lista oficial |
| Inglaterra | Premier League 2026/27 | Fonte consultada confirma a temporada e clubes participantes, mas a composição integral não foi obtida de forma estável para matching canônico neste ciclo | Pool SQL válido, ordenado por overall institucional |
| Argentina | Liga Profesional 2026 | AFA confirma 30 clubes em duas zonas, mas há variações de grafia/entidade que exigem matching e auditoria adicionais | Pool SQL válido, ordenado por overall institucional |
| Turquia | Süper Lig 2026/27 | TFF confirma a competição e a temporada, mas a página pública consultada não expõe uma lista integral estável para matching | Pool SQL válido, ordenado por overall institucional |

## Regra aplicada

Para países sem membership oficial integralmente validada, o motor seleciona somente clubes válidos já presentes no SQL, exclui registros sem nome ou escudo, ordena por `institutional_overall DESC, club_id ASC` e preenche a competição paralela até quatro divisões de 20 clubes. A origem técnica não é exibida na interface.

As URLs, temporadas, listas capturadas e hashes determinísticos das fontes atualmente classificadas como oficiais estão em `docs/membership_checksums.json`.
