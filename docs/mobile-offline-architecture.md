# FutManager — arquitetura móvel híbrida e offline-first

## Objetivo

A versão Android funciona sem servidor remoto depois que o pacote inicial de dados é baixado. A conexão é necessária somente na primeira preparação ou quando o usuário optar por atualizar os dados. O APK não contém o banco completo nem os assets editoriais pesados; ele contém a interface, o bridge nativo, o runtime Python/SQLite e o manifesto do pacote remoto.

## Decisão arquitetural

A base Android é um contêiner Capacitor sobre o frontend React existente. Essa escolha preserva a interface responsiva e permite usar plugins nativos para SQLite, sistema de arquivos, compartilhamento e ciclo de vida. O build de produção não inicia Express/Vite e não depende de uma URL externa para executar uma carreira já preparada.

A fonte de dados de release é o repositório [`Kyra2214/FutManager-data`](https://github.com/Kyra2214/FutManager-data/releases). O APK consome o manifesto versionado, não arquivos diretamente de um branch Git.

## Camadas do aplicativo

| Camada | Responsabilidade | Fonte de verdade |
|---|---|---|
| React + Capacitor | Navegação, telas, partidas, timeline e interação | Estado derivado do domínio |
| `DataBootstrap` | Bloquear consultas até os dados serem preparados | Status retornado pelo bridge |
| `NativeEnginePlugin` | Manifesto, download, SHA-256, extração e instalação atômica | Pacote remoto validado |
| `localDomain` | Casos de uso locais equivalentes às procedures | Serviços e engine locais |
| `localStore` | Abertura, transações, migrações, backup e restauração | SQLite/GameState local |
| Assets locais | Escudos, ícones e imagens editoriais | Diretório privado do pacote |

## Preparação inicial

`databasePath()` não copia banco de assets e não possui fallback silencioso. Se o banco ainda não foi instalado, ele lança `NATIVE_ENGINE_DATA_NOT_PREPARED`. A preparação ocorre antes, por meio de `NativeEngine.prepareData()` acionado pela tela `DataBootstrap`.

O bridge baixa o manifesto remoto e o ZIP, compara o SHA-256 dos bytes recebidos, bloqueia caminhos de extração que escapem do diretório privado, exige `database/game.db` e promove o pacote por troca atômica. Só depois disso o banco é copiado para o caminho operacional do SQLite.

O banco e os assets são mantidos em:

```text
/data/user/0/com.futmanager.app/files/futmanager-data/
/data/user/0/com.futmanager.app/databases/game.db
```

Uma falha de rede ou checksum não substitui o pacote funcional anterior. Após a preparação, `localStore`, `localCatalog` e `EntityAsset` usam os arquivos locais.

## Execução offline

Depois da primeira preparação, o aplicativo pode iniciar sem rede, listar entidades, criar e continuar carreiras, avançar semanas, disputar partidas e consultar assets. Não há promessa de disponibilidade de atualizações sem internet; atualizações são opcionais e devem ser instaladas somente depois de baixar e validar um novo pacote completo.

## Conteúdo do APK e conteúdo remoto

| Conteúdo | APK | Pacote remoto |
|---|---:|---:|
| Interface React e CSS/JavaScript | Sim | Não |
| Bridge Capacitor/Android | Sim | Não |
| Runtime e regras Python | Sim | Não |
| Manifesto de dados | Sim | Também |
| `database/game.db` completo | Não | Sim |
| Índices de catálogo | Não | Sim |
| Escudos e assets editoriais | Não | Sim |

O validador `scripts/validate-android-apk.py` confirma esse contrato: exige `offline-manifest.json` e falha se encontrar banco ou diretórios pesados no APK.

## Motor Python

O runtime Python é incorporado por bridge nativa Android. A engine continua sendo a referência das regras, enquanto a interface chama o domínio local por métodos nativos. O banco local continua sendo a fonte única da verdade; o React não cria jogadores, placares, calendários ou estados contratuais em memória permanente.

## Pacote e atualizações

O pacote atual é `v1.0.0`. O gerador `scripts/build-data-package.py` sanitiza o release seed, reconstrói índices e escreve o ZIP e o manifesto. O seed não pode conter `manager_careers`, `managers` ou `manager_selection_assignments` de uma carreira pré-existente.

Cada atualização deve receber uma nova versão, com novo ZIP, novo SHA-256 e novo manifesto. O app deve conservar a versão anterior até que a nova instalação seja concluída e validada.

## Validação

A preparação de release deve executar:

```bash
pnpm check
pnpm test
pnpm build
pnpm android:sync
cd android
./gradlew assembleRelease
cd ..
python3 scripts/validate-android-apk.py android/app/build/outputs/apk/release/app-release.apk
```

A validação do APK prova que os dados pesados não estão embutidos e que o manifesto remoto está presente. A validação da carreira limpa exige também baixar o pacote remoto, instalar os dados e iniciar o app em uma instalação limpa. A inspeção estática do APK, sozinha, não prova a execução da primeira preparação.

## Limitações e histórico

A auditoria antiga descrevia um banco-base empacotado e uma cópia automática de assets. Essa descrição não corresponde ao código atual. A implementação vigente é APK enxuto com download inicial obrigatório e funcionamento offline posterior.

Relatórios históricos podem citar `/home/ubuntu/brasfoot_engine`, `data/state/game.db` ou um banco embutido. Esses valores devem ser preservados como evidência de época, mas não devem ser usados para configurar o aplicativo atual.
