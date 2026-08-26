# Roadmap 3 — Comissão técnica e estrutura do clube

Esta etapa adiciona ao motor profissionais persistentes e departamentos de clube, sem implementar partidas, simulação global, mercado automático ou IA autônoma.

## Profissionais

A entidade `StaffMember` suporta treinador, auxiliar, preparador físico, médico e scout. São preservados nome, função, idade, clube, início de carreira, experiência, reputação, nível, potencial, especialização, salário, contrato, status, aposentadoria e histórico.

Experiência e reputação são campos independentes. A eficiência é calculada por função a partir dos componentes do profissional; experiência não é convertida diretamente em força de jogador. O potencial é gerado com seed opcional e permanece limitado entre 30 e 99 para profissionais recém-criados.

A aposentadoria não depende de uma idade fixa obrigatória. O estado mantém o profissional e registra `STAFF_RETIRED`; somente o vínculo atual com o clube é removido.

## Estrutura do clube

`ClubDepartment` e `club_departments` permitem níveis independentes para treinamento, base, departamento médico, preparação física, scouting e outros departamentos. Cada departamento possui nível, custo, capacidade, manutenção e eficiência.

## Força conceitual

`ClubStrengthService` expõe os três componentes separados: média dos jogadores, eficiência média da comissão e média da infraestrutura. A soma serve como contrato para sistemas futuros; não é fórmula de partida nem previsão de resultado.

## Persistência

As tabelas `staff_members`, `staff_history` e `club_departments` ficam somente em `data/state/game.db`. As operações usam transações e chaves estrangeiras. `data/database/game.db` não é usado como arquivo de save e permanece intacto.

## Limitações

Promoção automática de auxiliar para treinador, mercado completo, salários recorrentes, contratos avançados, cursos, aposentadoria probabilística, efeitos detalhados por função, estádio, torcida e simulação ficam para as etapas posteriores. Nesta fase existem contratos e operações básicas para que esses sistemas sejam adicionados sem reescrever o núcleo.
