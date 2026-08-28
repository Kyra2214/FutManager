# FutManager — operação segura no modo híbrido

## Visão geral

O aplicativo Android é distribuído em duas partes. O APK contém o código, a interface, o bridge Capacitor e o motor Python/SQLite. O banco completo e os assets editoriais ficam no pacote remoto versionado em [`Kyra2214/FutManager-data`](https://github.com/Kyra2214/FutManager-data/releases).

Na primeira execução, o app exige internet para baixar o pacote. Depois da validação e da instalação no armazenamento privado, o banco e os assets ficam em cache local e o jogo funciona offline. A descrição completa do contrato está em [`docs/fluxo_hibrido_dados.md`](fluxo_hibrido_dados.md).

## Instalação inicial

O APK deve conter `offline-manifest.json`, mas não deve conter `database/game.db`, `escudos` nem os assets editoriais completos. `DataBootstrap` consulta o status nativo antes de iniciar qualquer catálogo. Se os dados não estiverem prontos, o usuário recebe uma tela de preparação.

O bridge baixa o manifesto, baixa o ZIP, verifica `packageSha256`, protege a extração contra Zip Slip, exige `database/game.db` e instala o conjunto de forma atômica. O banco operacional fica em `/data/user/0/com.futmanager.app/databases/game.db`; a cópia do pacote permanece em `/data/user/0/com.futmanager.app/files/futmanager-data/database/game.db`.

Uma falha no download não deve apagar o banco funcional anterior. Nunca abrir o SQLite antes de `NativeEngine.getDataStatus()` retornar `ready: true`.

## Desenvolvimento

Use Node.js 22, pnpm e Python 3.11:

```bash
pnpm install
pnpm dev
```

A prévia web usa tRPC e não exige o pacote Android. O modo nativo usa o bridge e o GameState local preparado.

## Validação antes de publicar

Execute os gates abaixo:

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

O validador deve confirmar o modo `hybrid`, encontrar `offline-manifest.json` e não encontrar arquivos pesados embutidos. Para validar a distribuição de dados, gere o pacote com `scripts/build-data-package.py`, calcule o SHA-256 dos bytes finais e publique o ZIP e o manifesto no mesmo release.

## Banco e mutações

O GameState baixado é a base de dados operacional do aplicativo. As mutações percorrem o bridge nativo, o gateway, o motor Python e o SQLite. O banco-base canônico usado no desenvolvimento continua somente leitura. Para testes e scripts, use cópias temporárias do GameState e nunca sobrescreva a base canônica.

O release seed não pode conter carreiras, managers ou atribuições de seleção pré-criadas. O sanitizador `engine/scripts/release_seed.py` deve ser executado antes de gerar o ZIP remoto.

## Assets

O índice `offline-asset-index.json` e o banco devem ser gerados a partir da mesma versão do pacote. O frontend resolve escudos e assets por caminhos relativos ao pacote instalado. O Android converte esses arquivos do armazenamento privado para URLs compatíveis com o WebView.

Se um asset não puder ser encontrado, a interface deve exibir o estado honesto de ausência de asset; não crie imagens ou nomes fictícios para mascarar erro de distribuição.

## Recuperação e atualização

Para atualizar dados, publique uma nova versão completa do pacote, por exemplo `v1.1.0`. O app deve baixar, validar e instalar o novo conjunto antes de substituir a versão anterior. A versão antiga continua sendo o fallback até a troca atômica terminar.

Backups de carreira devem ser exportados pelas rotinas locais existentes e tratados como dados do usuário, não como parte do pacote público. Segredos, tokens, cookies e arquivos `.env` nunca devem ser versionados.

## Referências históricas

Os relatórios JSON antigos em `docs/` podem conter caminhos de execução como `/home/ubuntu/brasfoot_engine`. Eles são evidências históricas e não devem ser usados como instrução de instalação. O caminho atual é o manifesto remoto de dados e os diretórios privados descritos acima.
