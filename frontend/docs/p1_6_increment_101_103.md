# Incremento P1-6 — Elenco e gestão esportiva

Este incremento cobre os critérios iniciais de elenco: leitura SQL de titulares e reservas, contagem de atletas disponíveis e validação do mínimo configurável para uma escalação. O serviço `SportStateStore` persiste em `player_sport_state` e rejeita escritas no banco-base por guarda de caminho.

A prova foi executada em GameState temporário com 12 atletas, incluindo oito titulares e quatro reservas. A validação aceitou 12 disponíveis e rejeitou corretamente a exigência de 12 quando um atleta ficou lesionado, retornando `INSUFFICIENT_AVAILABLE_PLAYERS:11:12`. Foram aprovados 7 testes focados, incluindo regressão de formação, determinismo de partida e economia P0-17.

Os critérios restantes do Front P1-6 — formações por competição, escalação automática, substituições, minutos, estatísticas, entrosamento, moral, capitão, histórico tático e regras completas de campeonato — ainda não foram implementados neste incremento.
