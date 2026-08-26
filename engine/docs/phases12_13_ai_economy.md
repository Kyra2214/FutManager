# Fases 12 e 13 — IA dos clubes e economia mundial

A IA dos clubes foi implementada como camada de decisão sobre o estado existente. `ClubAI` não possui banco próprio, jogadores próprios, dinheiro próprio ou clube paralelo. Ela lê o SQL, gera diagnóstico, avalia jogadores, escolhe prioridade de treinamento e registra decisões auditáveis.

Perfis configuráveis incluem estratégias conservadora, equilibrada, agressiva, focada em jovens, focada em estrelas e financeira. Objetivos possuem prioridade, prazo, origem, status e progresso. A avaliação usa idade, posição, forma, condição, disponibilidade e atributos nativos existentes, sem inventar ratings.

A economia usa o `FinanceLedger` existente. `EconomyService` mantém estado econômico, orçamento, receitas e despesas acumuladas, folha, obrigações, dívida e saúde financeira. Obrigações podem ser pagas ou ficar atrasadas sem serem apagadas. A saúde considera caixa, dívida e atrasos, não apenas o saldo de caixa.

A camada econômica também suporta recuperação, insolvência, falência controlada, histórico financeiro, investimentos, ownership histórico e mudança de controle para SAF. Entrada de capital passa pelo ledger. O proprietário anterior não é apagado.

As operações são locais, offline e persistidas em SQLite. O banco-base permanece separado do estado mutável. As regras são parametrizadas para que clube rico, pequeno ou em crise possa emergir dos dados e do orçamento, sem scripts específicos por clube.

## Limitações

A etapa não implementa IA externa, API, frontend, economia mundial real, sistema bancário, impostos jurídicos específicos, mídia, torcida, simulação mundial, multiplayer ou regras legais reais de SAF. A IA também não executa contratação automática completa: ela produz decisões auditáveis e deve solicitar os serviços de mercado e contratos para executar ações válidas.
