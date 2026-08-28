# Auditoria do projeto Android

## Resultado da Fase 0

O projeto Android real foi localizado na branch `offline-android-release` do repositório `Kyra2214/FutManager`. A branch contém um projeto Capacitor/Gradle, o plugin nativo `com.futmanager.app.NativeEnginePlugin`, integração Chaquopy com Python 3.11 e a configuração `capacitor.config.ts`. A árvore de trabalho principal não contém esse projeto Android; por isso a correção foi mantida em uma branch de release Android derivada dela, sem sobrescrever o backend web mais recente da `main`.

## Pontos auditados

| Ponto | Evidência | Resultado |
|---|---|---|
| Bridge nativa | `android/app/src/main/java/com/futmanager/app/NativeEnginePlugin.java` | O plugin registra chamadas Capacitor para dashboard, início de carreira, avanço semanal, avanço até partida e partida controlada. |
| Runtime Python | `android/app/build.gradle`, `android/app/src/main/python/futmanager_native.py` | Chaquopy é configurado para Python 3.11 e o bridge passa o caminho do banco persistente do aplicativo. |
| Persistência | `NativeEnginePlugin.databasePath()` | O banco é copiado dos assets para o diretório privado de bancos do aplicativo na primeira execução; chamadas seguintes reutilizam o mesmo arquivo. |
| Banco-semente | `scripts/prepare-android-offline.mjs` | O banco é sanitizado em diretório temporário antes de ser copiado para `assets/public/assets/databases/game.db`. |
| Gate pós-build | `scripts/validate-android-apk.py` | O APK é aberto como ZIP, o banco embutido é extraído, a integridade SQLite é verificada e as tabelas de carreira precisam estar vazias. |
| Automação | `.github/workflows/android-release.yml` | O workflow prepara o seed, monta o APK release e executa a validação do banco antes de publicar o artefato. |

## Correção aplicada

A branch `android-roadmap-corrections` recebeu o commit `3e862eb0` (`fix: sanitize offline Android release seed`). O processo deixou de copiar diretamente o GameState local. Agora ele executa `scripts/release_seed.py sanitize`, que remove as linhas de `manager_selection_assignments`, `manager_careers` e `managers`, executa `VACUUM` e só então gera o índice de assets e o manifesto offline a partir do banco sanitizado.

Os fallbacks absolutos para `/home/ubuntu/brasfoot_engine` e `/home/ubuntu/webdev-static-assets` também foram removidos do preparador Android. O motor e os assets agora são recebidos por `FUTMANAGER_ENGINE_ROOT` e `FUTMANAGER_ASSET_ROOT`, com fallback relativo ao checkout.

## Validação reproduzida

A preparação offline foi executada com o engine e os assets do checkout. O APK release foi montado localmente com Gradle 8.14.3, API Android 36 e JDK 21. O validador encontrou o arquivo `assets/public/assets/databases/game.db`, confirmou `PRAGMA integrity_check = ok` e confirmou contagem zero nas três tabelas de estado de carreira.

A validação em aparelho ou emulador limpo continua sendo uma etapa operacional distinta: o código garante o estado inicial do APK e a bridge de primeira cópia, mas a interação física de toque deve ser executada no ambiente Android disponível para a equipe.
