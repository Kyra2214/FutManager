# P1-7 — Comissão técnica: contratos, efeitos e mercado

Os passos 121–135 foram implementados sobre o schema canônico do GameState. O catálogo mantém as cinco funções do domínio (`treinador`, `auxiliar`, `preparador_fisico`, `medico` e `scout`) e valida níveis, experiência, reputação e potencial dentro de suas faixas.

A contratação cria um contrato ativo de 52 semanas com salário semanal, datas de início e término e custo de rescisão equivalente a quatro semanas. Rescisão e substituição atualizam o vínculo em `staff_members`, o contrato, o histórico, o caixa e a folha do clube. O gateway expõe leitura de contrato e as mutations correspondentes; o frontend pede confirmação antes de contratar.

Os efeitos de função, bônus por nível, vagas de departamentos e especialidades de médicos/auxiliares são derivados do estado persistido. O catálogo aceita níveis mínimo/máximo e ordena deterministicamente por custo-benefício, preservando desempates por nível, reputação e nome. O histórico de contratações e rescisões permanece consultável no workspace CT.

A cobertura inclui testes de catálogo, atributos, contrato, rescisão, substituição, filtros, custo-benefício, gateway e workspace.
