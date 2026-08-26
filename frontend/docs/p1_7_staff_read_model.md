# Front P1-7 — Modelo de leitura da comissão técnica

O contrato `ClubWorkspaceDashboard` foi ampliado com `staff.averageLevel` e `staff.history`. A leitura continua em modo `readOnly` diretamente do SQLite/GameState: profissionais ativos são agrupados por função, o nível médio é derivado em tempo de consulta, departamentos atuais são listados e o histórico é desserializado com payload seguro.

A tela CT passou a exibir equipe ativa, média de nível, quantidade de decisões registradas e departamentos persistidos, mantendo as ações de contratação e evolução no gateway transacional existente. Quando não há registros, a interface mostra estado vazio e direciona o manager ao Mercado.

O teste do workspace valida profissionais, contagens, média de nível, departamento e payload histórico.
