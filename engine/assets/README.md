# Ativos de clubes e seleções

Os arquivos desta pasta são cópias sem transformação dos ativos do pacote original. O banco imutável `data/database/game.db` não foi alterado. Os vínculos são mantidos exclusivamente em `data/state/game.db`, nas tabelas `asset_catalog`, `team_asset_links` e `selection_asset_links`.

| Entidade | Ativo disponível | Chave de origem | Caminho armazenado |
| --- | --- | --- | --- |
| Clube | Escudo principal e variante mini, quando presentes | `times.arquivo_origem` sem `.ban` | `assets/escudos/clubes/*.png` e `assets/escudos/clubes_mini/*.png` |
| Seleção | Camisa primária | `selecoes.codigo` | `assets/selecoes/camisas/*.png` |

O pacote original não fornece arquivos de escudo para seleções. Por isso, `selection_asset_links.crest_asset_id` permanece nulo e `crest_status` é `SOURCE_NOT_PROVIDED`; a interface não deve apresentar a camisa como se fosse um escudo.

## Consulta para clube selecionado

```sql
SELECT
  team.time_id,
  team.nome,
  full_asset.relative_path AS crest_path,
  mini_asset.relative_path AS crest_mini_path,
  link.mapping_status
FROM times AS team
INNER JOIN team_asset_links AS link ON link.time_id = team.time_id
LEFT JOIN asset_catalog AS full_asset ON full_asset.asset_id = link.crest_asset_id
LEFT JOIN asset_catalog AS mini_asset ON mini_asset.asset_id = link.crest_mini_asset_id
WHERE team.time_id = ?;
```

## Consulta para seleção selecionada

```sql
SELECT
  selection.selecao_id,
  selection.codigo,
  selection.nome,
  crest_asset.relative_path AS crest_path,
  kit_asset.relative_path AS primary_kit_path,
  link.crest_status
FROM selecoes AS selection
INNER JOIN selection_asset_links AS link ON link.selecao_id = selection.selecao_id
LEFT JOIN asset_catalog AS crest_asset ON crest_asset.asset_id = link.crest_asset_id
INNER JOIN asset_catalog AS kit_asset ON kit_asset.asset_id = link.primary_kit_asset_id
WHERE selection.selecao_id = ?;
```
