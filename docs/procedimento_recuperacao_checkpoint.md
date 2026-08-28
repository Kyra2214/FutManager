# Procedimento de recuperação de checkpoint

A recuperação do FutManager deve distinguir três artefatos: o checkpoint do código, o pacote remoto versionado de dados e o save local do usuário. O código é recuperado deste repositório; o GameState de instalação vem do release em [`Kyra2214/FutManager-data`](https://github.com/Kyra2214/FutManager-data/releases); a carreira do usuário vem do armazenamento privado do Android ou de um backup explícito.

## Recuperar uma instalação sem carreira

Selecione o checkpoint do código e gere o APK normalmente. Não inclua `database/game.db`, escudos ou assets editoriais no APK. O `offline-manifest.json` deve apontar para o manifesto remoto da versão desejada.

Na primeira abertura, o app baixa o manifesto e o ZIP, compara o SHA-256 indicado, verifica a estrutura `database/game.db`, executa a validação de integridade e instala o pacote em `/data/user/0/com.futmanager.app/files/futmanager-data/`. O SQLite operacional usa `/data/user/0/com.futmanager.app/databases/game.db`.

## Recuperar uma carreira existente

Antes de substituir o aplicativo, exporte o save pelo mecanismo de backup local. O save é dado do usuário e não deve ser publicado no repositório de dados. Depois da instalação do pacote remoto, importe o backup somente após conferir a versão de schema compatível e executar `PRAGMA integrity_check` e `PRAGMA foreign_key_check`.

Nunca sobrescreva manualmente o banco-base canônico ou o pacote remoto. Se o pacote remoto estiver corrompido, descarte somente o arquivo temporário e baixe novamente. Se o save estiver corrompido, preserve o arquivo original para diagnóstico e restaure o último backup íntegro.

## Validações obrigatórias

A recuperação só é válida quando o manifesto corresponde aos bytes publicados, o ZIP passa pelo checksum, o banco passa por `PRAGMA integrity_check`, as foreign keys não apresentam ocorrências, o `pnpm check`, a suíte Vitest e o build do APK passam e o validador confirma que não existem dados pesados embutidos.

A restauração deve registrar o checkpoint do código, a versão do pacote de dados, os hashes, a data UTC e a origem do save. Nenhuma correção automática deve reconciliar saldo, ledger ou resultados; divergências devem ser reportadas para decisão explícita.

## Referências legadas

Relatórios antigos podem citar `data/database/game.db`, `data/state/game.db` ou `/home/ubuntu/brasfoot_engine`. Essas referências descrevem execuções históricas e não substituem o fluxo híbrido documentado em [`docs/fluxo_hibrido_dados.md`](fluxo_hibrido_dados.md).
