# Checklist de release do FutManager

A publicação do marco deve ocorrer somente após validar o motor Python, o frontend e os bancos. O checklist é executado contra uma cópia do GameState quando houver qualquer operação mutável.

| Área | Critério | Evidência |
|---|---|---|
| Motor | `py_compile` e testes Python aprovados | relatório de qualidade |
| Gateway | actions no mapa serviço → SQL | validador de mutation paths |
| Frontend | typecheck, Vitest, loading/empty/error/sucesso | CI local e validadores P0 |
| Banco-base | hash do manifesto confere; nenhuma escrita | `validate_p0_database.py` |
| GameState | integrity/foreign keys e schema version | manifesto de estado |
| Exportação | cópia sem segredos, hash e manifesto | `export_state_manifest.py` |
| ZIP | `unzip -tq`, arquivos obrigatórios e hash | `validate_p0_delivery.py` |
| Recuperação | smoke em cópia temporária e checkpoint disponível | `procedimento_recuperacao_checkpoint.md` |
| Publicação | checkpoint salvo e versão registrada | histórico WebDev/GitHub |

Observabilidade deve registrar somente identificadores de tick, status, duração, contagens e códigos de erro. Tokens, cookies, segredos e dados pessoais não entram nos logs. O marco 371–470 só é publicado depois de todas as linhas deste checklist estarem verdes e do changelog registrar a versão do projeto e os hashes relevantes.
