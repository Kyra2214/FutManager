# Governança social, reputação e bilheteria

O estado social do clube vive no GameState SQLite. `club_fan_base` contém tamanho, satisfação, interesse e engajamento; `club_reputation` contém reputações esportiva, nacional, internacional, comercial e histórica; `club_social_history` registra antes/depois por fonte e referência natural; `club_reputation_history` registra alterações de reputação com a mesma proteção idempotente.

Resultados de partidas processados pelo motor atualizam torcida e reputação em uma transação controlada. Eventos sociais usam `club_events.reference` como chave natural para impedir duplicidade. Segmentos local, nacional e internacional são derivados no serviço a partir do tamanho persistido e sempre totalizam exatamente o tamanho atual da torcida.

A prévia de preço de ingresso (`ticket_price_preview`) é somente leitura. Ela retorna preço, público esperado, receita esperada, risco de rejeição, `persisted: false` e a versão `ticket-price-v1`. A confirmação de alteração continua sendo `ticket_price`, pelo gateway autorizado, e a bilheteria efetiva só é lançada quando uma partida persistida é processada.

O frontend acessa essas informações exclusivamente por tRPC. Nenhum cálculo de saldo, público, receita ou reputação é realizado no cliente.
