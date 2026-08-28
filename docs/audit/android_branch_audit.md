# Auditoria do projeto Android — fluxo híbrido

## Resultado da auditoria

O projeto Android real está na branch `android-roadmap-corrections` do repositório `Kyra2214/FutManager`. Ele contém um projeto Capacitor/Gradle, o plugin nativo `com.futmanager.app.NativeEnginePlugin`, integração Chaquopy com Python e a interface React preparada para bloquear o uso até os dados remotos serem instalados.

A arquitetura vigente é **APK enxuto + download inicial obrigatório + operação offline posterior**. O banco completo e os assets editoriais não fazem parte do APK.

## Pontos auditados

| Ponto | Evidência | Resultado atual |
|---|---|---|
| Bridge nativa | `android/app/src/main/java/com/futmanager/app/NativeEnginePlugin.java` | Registra os métodos nativos de dashboard, início de carreira, avanço semanal, avanço até partida e partida controlada, além de status e preparação de dados. |
| Runtime Python | `android/app/build.gradle`, `android/app/src/main/python/futmanager_native.py` | Chaquopy executa a engine local e recebe o caminho do banco persistente no armazenamento privado. |
| Persistência | `NativeEnginePlugin.databasePath()` | Não copia banco dos assets. Se os dados não foram preparados, lança `NATIVE_ENGINE_DATA_NOT_PREPARED`. Depois da preparação, reutiliza o banco privado instalado. |
| Preparação | `DataBootstrap` e `NativeEnginePlugin.prepareData()` | Baixa manifesto e ZIP, valida SHA-256, extrai com segurança e instala o pacote atomicamente. |
| Preparador de APK | `scripts/prepare-android-offline.mjs` | Remove o banco e os assets pesados do conteúdo Android e escreve somente `offline-manifest.json`. |
| Gate pós-build | `scripts/validate-android-apk.py` | Exige o manifesto híbrido e falha se encontrar banco, escudos ou assets editoriais pesados dentro do APK. |
| Distribuição de dados | Release `v1.0.0` de `Kyra2214/FutManager-data` | Publica o ZIP completo de dados e o manifesto consumidos na primeira execução. |
| Automação | `.github/workflows/android-release.yml` | Monta o APK sem buscar o engine completo para embuti-lo e executa a validação do contrato híbrido. |

## Divergência identificada e corrigida

A auditoria original afirmava que `databasePath()` copiava o banco dos assets na primeira execução e que o validador extraía `assets/public/assets/databases/game.db` do APK. Essa descrição correspondia a um desenho anterior e não ao código atualmente publicado.

A implementação real faz o oposto: `databasePath()` exige que o banco já tenha sido preparado e lança `NATIVE_ENGINE_DATA_NOT_PREPARED` quando ele não existe. O banco é obtido pelo download inicial do pacote remoto. O APK não contém `database/game.db` e o validador rejeita esse arquivo caso ele apareça.

Essa diferença muda a conclusão da auditoria: a inspeção estática do APK prova que não há carreira pré-populada embutida, mas não prova sozinha que a primeira preparação funcionará. A confirmação completa exige baixar o pacote remoto, validar o SHA-256, instalar os dados e abrir o app em uma instalação limpa.

## Fluxo de dados comprovado

```text
APK
  └── offline-manifest.json
        └── FutManager-data/releases/download/v1.0.0/manifest.json
              └── futmanager-data-v1.0.0.zip
                    ├── database/game.db
                    ├── offline-countries.json
                    ├── offline-asset-index.json
                    └── assets/
```

Depois da preparação, os arquivos ficam no armazenamento privado:

```text
/data/user/0/com.futmanager.app/files/futmanager-data/
/data/user/0/com.futmanager.app/databases/game.db
```

A partir daí, o app funciona sem internet. Uma atualização futura deve baixar e validar um novo pacote completo antes de substituir a versão anterior.

## Validação reproduzida

O APK híbrido foi montado localmente com Gradle, API Android 36 e JDK 21. O validador retornou `mode: hybrid`, encontrou `offline-manifest.json` e retornou lista vazia de caminhos pesados proibidos. O pacote remoto `v1.0.0` possui aproximadamente 83 MB e o APK híbrido possui aproximadamente 42 MB.

A suíte frontend passou com 19 arquivos de teste e 67 testes. A instalação efetiva em aparelho ou emulador limpo continua sendo uma etapa operacional separada, necessária para comprovar visualmente a tela de preparação, a conclusão do download e a abertura offline após a instalação.

## Conclusão

O contrato correto para auditorias futuras é: **o APK não embute o banco; o manifesto aponta para o pacote remoto; o bridge prepara o banco; o SQLite só abre depois da preparação; e a execução posterior é offline**. Qualquer relatório que descreva cópia automática de assets ou banco embutido deve ser marcado como histórico/obsoleto.
