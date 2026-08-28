# FutManager

O FutManager é um aplicativo Android híbrido com frontend React, bridge Capacitor, motor Python/SQLite e distribuição externa de dados. O **código do aplicativo** é publicado neste repositório; o banco completo, os índices de catálogo e os assets editoriais são publicados separadamente em releases versionados no repositório [`Kyra2214/FutManager-data`](https://github.com/Kyra2214/FutManager-data).

> O APK não contém o GameState completo. Na primeira execução, o aplicativo baixa e valida um pacote de dados; depois da preparação inicial, o jogo funciona offline.

## Arquitetura atual

| Camada | Responsabilidade | Local de distribuição |
|---|---|---|
| Frontend React | Telas, navegação e estados de loading/erro | APK e código deste repositório |
| Bridge Capacitor | Download, checksum, extração segura e acesso aos arquivos locais | APK e `android/app/src/main/java` |
| Motor Python | Regras esportivas, carreira, calendário e mutações | APK, sem o banco completo |
| GameState SQLite | Clubes, jogadores, ligas, competições e estado persistido | Pacote remoto de dados |
| Escudos e assets editoriais | Imagens e índices de apresentação | Pacote remoto de dados |

O pacote atual é `v1.0.0` e pode ser consultado no [manifesto remoto](https://github.com/Kyra2214/FutManager-data/releases/download/v1.0.0/manifest.json). Ele aponta para o arquivo `futmanager-data-v1.0.0.zip`, que contém `database/game.db`, `offline-countries.json`, `offline-asset-index.json`, escudos e assets editoriais.

## Fluxo de primeira execução

Ao abrir o APK, `DataBootstrap` consulta `NativeEngine.getDataStatus()`. Se os dados ainda não estiverem instalados, o aplicativo mostra a tela **Baixar dados e começar** e não executa consultas de catálogo ou criação de carreira.

Depois que o usuário confirma, o bridge baixa o manifesto e o ZIP para o cache privado, verifica o SHA-256 do pacote, protege a extração contra caminhos maliciosos, confirma a presença do banco e instala os dados de forma atômica. O banco é então disponibilizado ao SQLite. Uma falha de conexão não substitui o banco válido anterior; o usuário pode tentar novamente.

Após a instalação, catálogos e imagens são lidos do armazenamento privado. O app não precisa de internet para criar ou continuar carreiras, avançar semanas, disputar partidas ou consultar os dados já baixados. A internet volta a ser necessária somente para futuras atualizações do pacote.

## Localização dos dados no Android

O pacote remoto contém:

```text
database/game.db
offline-countries.json
offline-asset-index.json
assets/escudos/...
app/...
```

Após a instalação, o banco é mantido em:

```text
/data/user/0/com.futmanager.app/files/futmanager-data/database/game.db
/data/user/0/com.futmanager.app/databases/game.db
```

Esses diretórios são privados do aplicativo. O usuário não precisa abrir ou editar o SQLite manualmente.

## Desenvolvimento local

Use Node.js 22, pnpm e Python 3.11. Para instalar dependências e executar a prévia web:

```bash
pnpm install
pnpm dev
```

Para validar o frontend:

```bash
pnpm check
pnpm test
pnpm build
```

Para gerar o pacote remoto de dados a partir do engine canônico, use:

```bash
python3 scripts/build-data-package.py \
  --engine-root /caminho/para/engine \
  --asset-root /caminho/para/assets \
  --output-dir /tmp/futmanager-data \
  --version 1.0.0 \
  --base-url https://github.com/Kyra2214/FutManager-data/releases/download/v1.0.0
```

O gerador sanitiza o GameState antes de empacotar. A seed de release não pode conter carreiras, managers ou atribuições de seleção pré-existentes.

Para preparar e montar o APK híbrido:

```bash
pnpm android:sync
cd android
./gradlew assembleRelease
cd ..
python3 scripts/validate-android-apk.py android/app/build/outputs/apk/release/app-release.apk
```

O validador exige `offline-manifest.json` e rejeita banco, escudos ou assets editoriais pesados dentro do APK.

## Operação segura

Todas as mutações percorrem o bridge, o gateway, o motor Python e o GameState SQLite. Não coloque regras esportivas, placares, caixa, elenco ou calendário em estado React permanente. Estados de loading, vazio e erro devem refletir o motor persistido.

Não versionar tokens, cookies, credenciais ou arquivos `.env`. O banco-base canônico permanece somente leitura. Para desenvolvimento, use cópias temporárias do GameState; para publicação, sempre execute o sanitizador de release e os validadores de integridade.

## Histórico documental

Alguns relatórios JSON em `docs/` registram execuções anteriores e mencionam `/home/ubuntu/brasfoot_engine`. Esses caminhos são **evidência histórica**, não o contrato atual do aplicativo. O contrato atual está descrito em [`docs/fluxo_hibrido_dados.md`](docs/fluxo_hibrido_dados.md) e usa o manifesto remoto e o armazenamento privado do Android.
