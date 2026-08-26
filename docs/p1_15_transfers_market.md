# P1-15 — Transferências e mercado

O mercado mantém `transfer_windows`, `player_market_state`, `transfer_offers`, `transfer_history` e `transfer_events` como fonte canônica. A lista de transferíveis é derivada de jogadores ativos vinculados ao clube vendedor. A janela deve estar aberta e comprador e vendedor precisam ser clubes distintos.

Propostas persistem valor, preço pedido, salário, comissão, custos acessórios, validade e contador de contrapropostas. O aceite do manager cria aprovação explícita; uma oferta aceita por outro caminho é rejeitada na conclusão se não possuir aprovação. A conclusão ocorre em transação única, valida saldo, debita o custo total do comprador, credita a taxa ao vendedor, atualiza o vínculo do jogador e registra histórico/evento.

Empréstimos têm clube de origem/destino, datas, taxa, opção de compra, taxa da opção e prazo da opção. Transferências são bloqueadas quando o jogador está em negociação, aposentado, suspenso em condição proibida ou quando o comprador atingiu 40 atletas persistidos. Propostas concorrentes são serializadas pelo status `NEGOTIATING`; falhas na conclusão executam rollback.

A validação passou com os testes existentes de mercado/gateway e três testes específicos para aprovação, custos, empréstimo, limite de elenco e suspensão. O modelo não inventa jogadores e permanece separado de dados de teste.
