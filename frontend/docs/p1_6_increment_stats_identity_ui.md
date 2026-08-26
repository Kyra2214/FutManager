# Incremento P1-6 — Identidade dos agregados individuais

A aba Time passou a apresentar nome e posição canônicos junto dos agregados individuais. A resolução usa somente o elenco retornado por `club.workspace`; quando um atleta estatístico não está no elenco atual, a tela mostra `Atleta não localizado` em vez de inventar uma identidade.

O filtro de competição é enviado ao contrato tRPC e o filtro de atleta permanece local à apresentação. Nenhuma estatística é persistida no frontend.

O typecheck permaneceu limpo após a correção do JSX e a tela conserva estados de carregamento, erro e ausência.
