# Incremento P1-6 — Filtros de estatísticas no Time

A aba Time agora carrega as competições persistidas via `matches.dashboard` e permite selecionar uma competição e um atleta para filtrar a apresentação das estatísticas. A competição é enviada ao contrato `matches.playerStats`; o atleta é filtrado apenas na apresentação, sem copiar regras ou estado esportivo para o cliente.

As referências de consulta são estáveis e a tela preserva estados de carregamento, erro e ausência. A correção do JSX foi validada com typecheck e 9 testes focados de engineState e interface.
