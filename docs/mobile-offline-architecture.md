# FutManager — arquitetura do APK offline-first

## Objetivo

A versão Android deverá funcionar sem servidor remoto, sem OAuth, sem tRPC, sem S3 e sem chamadas de rede para executar uma carreira. O APK deverá conter a interface, o catálogo inicial, os escudos, o banco local e as regras necessárias para criar, avançar e retomar uma carreira.

## Decisão arquitetural

A base de distribuição será um contêiner **Capacitor Android** sobre o frontend React existente. Essa escolha preserva a maior parte da interface web responsiva já construída e permite adicionar plugins nativos para SQLite, sistema de arquivos, compartilhamento e ciclo de vida do aplicativo. O build de produção não iniciará Express/Vite e não dependerá de uma URL externa.

O tRPC continuará apenas como contrato transitório durante a migração. No APK, cada procedimento será substituído por uma chamada para `localDomain`, uma camada TypeScript local que implementará os mesmos contratos públicos e delegará a persistência ao SQLite do dispositivo.

## Camadas no APK

| Camada | Responsabilidade | Fonte de verdade |
| --- | --- | --- |
| React + Capacitor | Navegação, telas, partidas, timeline e interação | Estado derivado do domínio |
| `localDomain` | Casos de uso equivalentes às procedures atuais | Serviços locais |
| `localStore` | Transações, migrações, backup e restauração | SQLite/GameState local |
| Engine local | Ciclo semanal, calendário, partidas, economia e regras | SQLite/GameState local |
| Assets embarcados | Escudos, ícones e imagens licenciadas já auditadas | Arquivos incluídos no APK |

## O que será removido do caminho offline

A versão instalada não usará `server/_core/index.ts`, Express, `careerGateway.ts` via `execFileSync`, banco MySQL/TiDB, Manus OAuth, chamadas Forge, proxy de storage, notificações server-side, LLM remoto ou qualquer endpoint `/api/trpc`. Recursos que dependem de rede deverão aparecer como indisponíveis, nunca como erro de execução da carreira.

## Engine Python

O Python atual não pode ser executado diretamente pelo navegador ou por um APK Capacitor sem um runtime nativo adicional. Para manter o APK simples e confiável, a regra de negócio será portada gradualmente para TypeScript, começando pelos contratos usados no fluxo principal: criação da carreira, leitura do clube, calendário, avanço semanal, ida até a partida, partida controlada, eventos da timeline e persistência de decisões táticas.

A engine Python continuará sendo a referência de comportamento durante a portabilidade. Cada contrato portado deverá possuir comparação determinística contra uma cópia temporária do GameState, usando seed explícita e sem inventar dados. O SQL/GameState permanece a fonte única da verdade; o frontend não criará placares, jogadores, clubes ou eventos.

## Persistência e dados embarcados

O banco-base canônico será empacotado como recurso somente leitura de inicialização. Na primeira execução, o aplicativo copiará esse banco para o armazenamento privado do Android e aplicará migrações versionadas. A carreira e as mutações ocorrerão apenas na cópia local do GameState. O banco-base nunca será aberto como destino de escrita.

O backup local será exportado por arquivo, com versão de esquema, integridade SQLite e identificação da carreira. A restauração deverá ocorrer em transação, com validação antes da substituição do estado ativo.

## Sequência de migração

1. Criar o shell Android e uma configuração de build sem servidor.
2. Extrair contratos públicos do gateway para tipos compartilhados.
3. Criar `localStore` e a ponte SQLite nativa.
4. Portar o bootstrap e a leitura de carreira.
5. Portar avanço semanal, viagem e timeline.
6. Portar partida controlada e decisões táticas.
7. Substituir progressivamente o cliente tRPC por `localDomain`.
8. Embarcar banco-base e assets com manifesto e verificação de integridade.
9. Implementar backup/restauração e migrações locais.
10. Gerar e testar o APK em dispositivo Android real.

## Critérios de aceite

O APK será considerado preparado quando iniciar sem rede, criar uma carreira, listar entidades e escudos, avançar semanas, simular apenas o mundo externo, abrir a partida controlada, persistir decisões táticas, exibir a timeline acionável, fechar e reabrir mantendo o GameState, e exportar/restaurar um backup válido.

## Limitação atual do ambiente

A auditoria encontrou Node e Java, mas não encontrou `adb`, Gradle ou projeto Expo/Capacitor no repositório. Portanto, a configuração de código pode ser preparada agora, mas a instalação em aparelho e a geração final assinada do APK exigirão a toolchain Android disponível ou um ambiente de build equivalente.

## Referências técnicas

[1]: https://developer.android.com/tools — Android Developers, “Command-line tools”.
[2]: https://developer.android.com/tools/sdkmanager — Android Developers, “sdkmanager”.

A documentação oficial confirma que o SDK é composto por pacotes instaláveis via `sdkmanager`, que o `platform-tools` fornece o `adb` e que plataformas/build-tools específicos podem ser instalados por caminhos como `platforms;android-36` e `build-tools;36.0.0` [1] [2].

## Estratégia da engine

A auditoria do repositório encontrou **341 módulos Python** e um gateway de **3.038 linhas**, sem manifesto de dependências externas; os imports observados são majoritariamente biblioteca padrão, SQLite e módulos internos. Copiar os `.py` para o APK não os torna executáveis pelo WebView. Há duas estratégias tecnicamente válidas: portar os casos de uso gradualmente para TypeScript/SQLite, ou incorporar um runtime Python por bridge nativa Android. A implementação atual segue o port gradual, porque preserva o GameState como fonte única e evita introduzir um runtime nativo adicional antes de medir o escopo de cada contrato.

A documentação do Chaquopy 17.0 confirma que o plugin pode ser aplicado ao módulo Android, exige `minSdk` 24, configura o Python em `src/main/python` e requer `abiFilters`; também informa que cada ABI acrescenta alguns megabytes ao aplicativo e que o Python precisa estar disponível na máquina de build [3]. Como a engine atual possui 341 módulos e um gateway de 3.038 linhas, essa opção é viável em princípio, mas aumentará o tamanho e a complexidade do APK.

[3]: https://chaquo.com/chaquopy/doc/current/android.html — Chaquopy 17.0, “Gradle plugin”.
