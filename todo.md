# FutManager — TODO do projeto

## Migração offline Android

- [x] Embutir o React dentro de um WebView Capacitor para distribuição Android.
- [x] Embutir Python 3.11 com Chaquopy e bridge nativa para execução local da engine.
- [x] Usar o GameState SQLite como fonte única da verdade no runtime nativo.
- [x] Empacotar GameState, catálogo de assets, países e escudos no APK durante o build.
- [x] Implementar persistência local SQLite e backup/restauração JSON da carreira.
- [x] Portar contratos P0 de carreira, catálogo, dashboard, competições, calendário, viagens e partidas.
- [x] Integrar CareerStart e Home ao domínio local no Android.
- [x] Integrar avanço semanal, auto-travel e partida controlada ao Python/SQLite.
- [x] Implementar tela de partida com eventos, pausa, pênaltis, expulsões e decisões táticas.
- [x] Implementar retomada de carreira e fallback visual para estados sem dados.
- [x] Validar o smoke test nativo contra uma cópia do GameState correto.
- [x] Executar `pnpm android:sync` e gerar APK release.
- [x] Validar assinatura APK v2, ausência da permissão INTERNET e assets offline obrigatórios.
- [x] Gerar artefato release assinado para distribuição manual.

## Pendências conscientes

- [ ] Testar instalação e fluxo completo em dispositivo/emulador Android real.
- [ ] Portar contratos administrativos P1 restantes: estádio, comissão, patrocínios e mercado.
- [ ] Revisar visualmente todas as telas no WebView em diferentes tamanhos de celular.
- [ ] Configurar uma keystore de produção fornecida pelo responsável pela publicação.
- [ ] Publicar o código sincronizado no repositório GitHub selecionado pelo usuário.
