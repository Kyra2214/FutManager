# Contratos de atletas — contrato de leitura

O histórico de contratos é lido da tabela canônica `player_contract_history`, com relacionamento ao jogador por `player_id` e ao clube por `club_id`. A consulta `club.contracts` retorna contratos ativos, vigência, salário semanal, cláusula de rescisão, origem e semanas restantes quando temporada e semana são informadas.

`club.contractRenewalPreview` é uma operação somente leitura. Ela compara o salário semanal atual ao valor proposto e retorna delta, folha atual, folha projetada e versão da fórmula. A prévia declara `persisted: false`; portanto, não altera `player_contract_history`, folha, caixa ou FinanceLedger.

A confirmação de renovação não deve ser feita no cliente. Ela deverá ser encaminhada por um CommandService autorizado, com aprovação explícita do manager, validação de teto salarial e lançamento transacional de luvas, bônus e custos acessórios no FinanceLedger.
