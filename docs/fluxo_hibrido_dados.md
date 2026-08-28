# Fluxo híbrido de dados do FutManager

## 1. Objetivo

O FutManager usa uma arquitetura **híbrida e offline-first**. O APK é enxuto e contém a interface, o runtime nativo e o motor Python, mas não carrega o banco completo nem os assets editoriais. Na primeira execução, o aplicativo precisa de internet para baixar um pacote versionado. Depois da instalação validada, todas as operações do jogo funcionam sem conexão.

Essa separação reduz o tamanho do instalador, permite atualizar os dados sem recompilar o aplicativo e mantém o banco do usuário no armazenamento privado do Android.

## 2. Repositórios

O código-fonte do aplicativo está no repositório [`Kyra2214/FutManager`](https://github.com/Kyra2214/FutManager). O conteúdo pesado de dados está no repositório [`Kyra2214/FutManager-data`](https://github.com/Kyra2214/FutManager-data), distribuído somente por releases.

O aplicativo não deve baixar arquivos do branch Git. Ele deve consumir um manifesto e um artefato imutável de release:

| Recurso | URL da versão atual |
|---|---|
| Manifesto | `https://github.com/Kyra2214/FutManager-data/releases/download/v1.0.0/manifest.json` |
| ZIP de dados | `https://github.com/Kyra2214/FutManager-data/releases/download/v1.0.0/futmanager-data-v1.0.0.zip` |

O endereço pode ser substituído em build por `VITE_FUTMANAGER_DATA_MANIFEST_URL` no frontend ou por `FUTMANAGER_DATA_MANIFEST_URL` no preparador Android.

## 3. Contrato do manifesto

O manifesto é JSON e deve conter, no mínimo, os campos abaixo:

```json
{
  "format": 1,
  "version": "1.0.0",
  "packageUrl": "https://.../futmanager-data-v1.0.0.zip",
  "packageSha256": "<64 caracteres hexadecimais>",
  "packageBytes": 83066627,
  "databaseSha256": "<64 caracteres hexadecimais>"
}
```

`packageSha256` é calculado sobre os bytes exatos do ZIP publicado. O aplicativo baixa o manifesto primeiro, baixa o pacote indicado, calcula o SHA-256 localmente e rejeita qualquer divergência antes de extrair ou substituir dados existentes.

## 4. Estrutura do pacote

O ZIP de dados atual contém:

```text
database/game.db
offline-countries.json
offline-asset-index.json
assets/escudos/...
app/...
```

O arquivo `database/game.db` é o GameState sanitizado para release. Ele contém os dados canônicos de clubes, jogadores, países, competições, calendário e regras, mas não contém uma carreira de usuário pré-criada. Os índices JSON são gerados a partir do mesmo banco incluído no pacote, evitando que o catálogo e o SQLite fiquem desencontrados.

## 5. Primeira execução no Android

A entrada global do frontend é envolvida por `DataBootstrap`. No Android, o componente chama `NativeEngine.getDataStatus()` antes que `Home`, `CareerStart` ou qualquer catálogo execute consultas locais.

Quando o resultado indica `ready: false`, o app mostra uma tela de preparação. O usuário precisa tocar em **Baixar dados e começar**. O bridge nativo então:

1. baixa o manifesto pela URL configurada;
2. resolve a URL do ZIP, inclusive quando ela é relativa ao manifesto;
3. baixa o ZIP para o cache privado temporário;
4. calcula e compara o SHA-256 esperado;
5. extrai o ZIP com proteção contra Zip Slip;
6. exige a presença de `database/game.db`;
7. instala o diretório de dados por troca atômica;
8. copia o banco para o caminho privado usado pelo SQLite;
9. retorna a versão instalada à interface.

Se ocorrer erro de conexão, HTTP, checksum, extração ou banco ausente, o banco anterior permanece intacto. A interface mostra uma mensagem de erro e permite nova tentativa.

## 6. Armazenamento local

O diretório de dados persistente é:

```text
/data/user/0/com.futmanager.app/files/futmanager-data/
```

Dentro dele, o banco completo fica em:

```text
/data/user/0/com.futmanager.app/files/futmanager-data/database/game.db
```

O bridge também coloca uma cópia operacional em:

```text
/data/user/0/com.futmanager.app/databases/game.db
```

O SQLite só é aberto depois que `getDataStatus()` confirmar manifesto e banco instalados. Em seguida, `localCatalog.ts` lê países e catálogos do pacote local, enquanto `EntityAsset.tsx` transforma os caminhos privados em URLs que o WebView consegue exibir.

## 7. Comportamento offline

Depois da preparação, nenhuma chamada de internet é necessária para consultar clubes, países, seleções, escudos, calendário, carreira, partidas, economia ou demais regras já presentes no GameState. O estado mutável da carreira é gravado no banco local e permanece no aparelho.

A ausência de internet em uma abertura posterior não deve bloquear o usuário se o pacote já estiver pronto. A conexão volta a ser necessária somente quando uma atualização futura de dados for oferecida.

## 8. Atualizações futuras

Cada atualização deve receber uma nova versão, por exemplo `v1.1.0`, com um novo ZIP e um novo manifesto. O app pode consultar um manifesto atualizado somente quando houver internet. O pacote atual deve permanecer funcional até que o novo pacote seja completamente baixado e validado.

A estratégia inicial usa pacotes completos, por serem mais simples e seguros para SQLite. Atualizações diferenciais só devem ser adotadas depois de existir um mecanismo de migração, rollback e validação equivalente.

## 9. Gerar o pacote remoto

O script `scripts/build-data-package.py` gera a distribuição de dados. Ele recebe o diretório do engine e dos assets, chama o sanitizador de release seed, reconstrói os índices, cria um ZIP determinístico e escreve o manifesto.

```bash
python3 scripts/build-data-package.py \
  --engine-root /caminho/para/engine \
  --asset-root /caminho/para/assets \
  --output-dir /tmp/futmanager-data \
  --version 1.0.0 \
  --base-url https://github.com/Kyra2214/FutManager-data/releases/download/v1.0.0
```

Depois, publique o ZIP e o manifesto no release com o mesmo nome e confirme que `packageUrl`, `packageSha256` e `packageBytes` correspondem aos arquivos publicados.

## 10. Build do APK

O script `scripts/prepare-android-offline.mjs` remove do conteúdo Android os diretórios pesados e escreve apenas `offline-manifest.json`. O workflow de release não precisa mais baixar o engine canônico para embutir o GameState.

```bash
pnpm install
pnpm check
pnpm test
pnpm build
pnpm android:sync
cd android
./gradlew assembleRelease
cd ..
python3 scripts/validate-android-apk.py android/app/build/outputs/apk/release/app-release.apk
```

O validador deve confirmar `mode: hybrid`, exigir o manifesto e retornar uma lista vazia de caminhos pesados proibidos. Um APK que contenha `database/game.db`, `escudos` ou os assets editoriais deve falhar o gate.

## 11. Diagnóstico

| Sintoma | Causa provável | Ação |
|---|---|---|
| Tela de preparação aparece sempre | Manifesto ou banco não persistiu | Verificar armazenamento privado e repetir o download |
| Checksum inválido | ZIP diferente do manifesto ou download corrompido | Republicar o manifesto com hash do arquivo exato |
| Banco ausente após extração | Estrutura do ZIP incorreta | Confirmar `database/game.db` na raiz do pacote |
| Imagens não aparecem | Caminho ausente ou índice incompatível | Regenerar `offline-asset-index.json` a partir do mesmo banco |
| App abre sem internet após preparação | Comportamento esperado | Consultas e assets devem usar somente o cache local |
| APK continua grande | Dados pesados ainda foram copiados no sync | Executar o preparador e o validador; procurar arquivos gerados ignorados |

## 12. Segurança e integridade

O pacote remoto não deve conter tokens, cookies, credenciais ou dados pessoais. A extração bloqueia caminhos que escapem do diretório de destino. O banco somente é promovido depois de validado; falhas não devem destruir a instalação funcional anterior.

O banco-base canônico usado no desenvolvimento continua somente leitura. O release seed deve ser sanitizado antes da publicação para remover `manager_careers`, `managers` e `manager_selection_assignments` pré-existentes.

## 13. Documentos históricos

Arquivos JSON como `docs/auditoria_funcional_471_500.json`, `docs/benchmark_final_471_499.json` e `docs/manifesto_marco_371_470.json` preservam evidências de execuções antigas. Referências a `/home/ubuntu/brasfoot_engine` ou a bancos locais nesses arquivos são históricas e não representam o caminho usado pelo APK atual.

O contrato vigente é este documento, o [README principal](../README.md) e o [guia operacional](README_operacao_segura.md).
