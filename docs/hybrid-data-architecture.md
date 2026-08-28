# Arquitetura híbrida de dados do FutManager

O APK Android contém somente o shell da aplicação, o bridge nativo, o runtime Python/SQLite e o manifesto do pacote remoto. O banco completo, os índices de catálogo e os assets editoriais são distribuídos no repositório público [`Kyra2214/FutManager-data`](https://github.com/Kyra2214/FutManager-data), por meio de releases versionados.

## Pacote atual

A versão inicial é `1.0.0` e está publicada em:

- Manifesto: `https://github.com/Kyra2214/FutManager-data/releases/download/v1.0.0/manifest.json`
- Pacote: `https://github.com/Kyra2214/FutManager-data/releases/download/v1.0.0/futmanager-data-v1.0.0.zip`

O manifesto informa a versão, o tamanho, o SHA-256 do ZIP e o SHA-256 do banco sanitizado. O ZIP contém `database/game.db`, `offline-countries.json`, `offline-asset-index.json`, os escudos e os assets editoriais.

## Primeira execução

A tela inicial consulta `NativeEngine.getDataStatus()`. Se o banco ainda não estiver instalado, nenhuma consulta de catálogo ou carreira é executada. Ao clicar em **Baixar dados e começar**, o bridge baixa o manifesto e o ZIP para o cache privado, verifica o SHA-256, protege a extração contra Zip Slip, confirma a presença de `database/game.db`, instala o diretório de forma atômica e copia o banco para o caminho SQLite privado.

Se a conexão cair, o banco definitivo permanece intacto e o usuário pode tentar novamente. Após a instalação, os catálogos são lidos de arquivos locais e as imagens são convertidas para URLs privadas do WebView. A partir desse momento, a execução é offline; internet somente é necessária para uma eventual atualização futura do pacote.

## Garantias de release

O preparador Android remove os diretórios pesados do conteúdo empacotado e escreve apenas `offline-manifest.json`. O validador do APK rejeita banco, escudos ou assets editoriais pesados dentro do APK e exige o manifesto híbrido. O workflow de release executa o mesmo gate antes de publicar o artefato.

O pacote de dados é gerado por `scripts/build-data-package.py`, que chama o sanitizador de release seed e reconstrói os índices a partir do mesmo banco que será distribuído. O seed não contém carreiras, managers ou atribuições de seleção pré-existentes.
