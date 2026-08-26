# Ciclo de vida contratual do atleta

O contrato do atleta é persistido no **GameState SQLite** e lido pelo read model do FutManager. O frontend não calcula folha, teto salarial, saldo ou vigência; ele apenas apresenta os contratos retornados pelo tRPC e envia decisões explícitas.

## Estados persistidos

| Estado | Significado | Transição autorizada |
|---|---|---|
| `ACTIVE` | Versão vigente para o atleta e clube | `PlayerContractService.approve_renewal` cria uma nova versão |
| `REPLACED` | Versão anterior encerrada por renovação | Writer de renovação, dentro da mesma transação |
| `EXPIRED` | Contrato encerrado pela passagem da vigência | Ciclo temporal canônico do motor |
| `TERMINATED` | Contrato rescindido antes do fim | Serviço de rescisão/transferência do motor |

Cada versão contém atleta, clube, temporada/semana de início e fim, salário semanal, cláusula de saída, status e fonte natural da decisão. O histórico é somente leitura no `getPlayerContracts` e no `getPlayerProfile`.

## Fluxos

A prévia `contractRenewalPreview` não grava dados. Ela informa salário atual, salário proposto, delta, folha atual e folha projetada. A mutação `contractRenewalApprove` exige `managerApproved: true`; sem essa confirmação o motor retorna `MANAGER_APPROVAL_REQUIRED` e não altera contrato, folha ou ledger.

A aprovação é delegada pelo tRPC ao `career_gateway.py`, que chama exclusivamente `PlayerContractService`. O serviço valida termos, localiza o contrato ativo, aplica o teto salarial do clube quando persistido, encerra a versão anterior, cria a nova versão e atualiza a folha de jogadores na mesma transação.

Luvas e bônus são custos acessórios da renovação. Quando informados, entram no `FinanceLedger` com categorias `CONTRACT_SIGNING` e `CONTRACT_BONUS`, valores negativos, `source_type=PLAYER_CONTRACT` e identificadores derivados da versão criada. A chave natural do ledger preserva idempotência por clube, temporada, semana, categoria, origem e origem-id.

## Fonte única e recuperação

> O SQL/GameState é a única fonte da verdade. O React não persiste contrato, não ajusta saldo e não reproduz a fórmula de teto salarial.

Falhas durante a aprovação provocam rollback da conexão SQLite. O teste transacional deve confirmar que a versão anterior permanece ativa, a nova versão não aparece, a folha não muda e nenhum lançamento acessório é criado. Transferência e rescisão devem seguir o mesmo padrão: decisão no gateway, writer canônico, operação idempotente e auditoria no estado econômico.
