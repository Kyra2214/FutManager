# FutManager/Brasfoot — 500 próximos passos

> Roadmap expandido em 25 frentes. A numeração é contínua para facilitar priorização, delegação e acompanhamento.

## Critérios de priorização

| Nível | Critério | Ordem recomendada |
|---|---|---|
| P0 | Fundação, integridade, fonte de verdade, ciclo jogável e bloqueios de entrega. | Executar primeiro. |
| P1 | Funcionalidades que aprofundam a carreira, a gestão e a experiência principal depois da fundação. | Executar após os pré-requisitos P0. |
| P2 | Sistemas avançados, expansão de simulação e melhorias de longo prazo. | Executar quando P0/P1 estiverem estáveis. |

A prioridade da frente orienta os 20 itens nela contidos; dentro de cada frente, a ordem numérica é a ordem sugerida de execução e dependência.

## Regra obrigatória de execução

> Nenhum item P1 ou P2 pode ser iniciado, mesclado ou marcado como concluído enquanto todos os itens P0 não estiverem consolidados com implementação, testes, integridade SQLite, documentação e evidência no gate versionado.

O roadmap registra planejamento; ele não é fonte de verdade do jogo. O estado esportivo, financeiro, social e de carreira continua vindo exclusivamente de SQL/GameState. O frontend apenas consulta e solicita comandos por tRPC/Gateway; não calcula, inventa ou grava estado de jogo.

Situação inicial deste documento: **P1 e P2 bloqueados** até o gate P0 ser aprovado.

## Matriz verificável de dependências

| Frente | Prioridade | Depende de |
|---:|:---:|:---|
| 1 | P0 | fundação |
| 2 | P0 | 1 |
| 3 | P0 | 1, 2 |
| 4 | P0 | 3 |
| 5 | P0 | 3, 4 |
| 6 | P1 | 4, 5 |
| 7 | P1 | 3, 5 |
| 8 | P1 | 3, 7 |
| 9 | P1 | 6, 8 |
| 10 | P1 | 6, 8, 9 |
| 11 | P0 | 2, 3, 4, 6, 9 |
| 12 | P0 | 3, 5, 11 |
| 13 | P0 | 2, 3, 12 |
| 14 | P2 | 6, 11, 12, 13 |
| 15 | P1 | 3, 4, 5, 6, 13 |
| 16 | P2 | 4, 6, 7, 8 |
| 17 | P0 | 2, 3, 5, 13 |
| 18 | P1 | 3, 17 |
| 19 | P1 | 3, 17 |
| 20 | P1 | 5, 11, 12, 19 |
| 21 | P1 | 17, 18, 19, 20 |
| 22 | P1 | 11, 17, 19, 20, 21 |
| 23 | P0 | 2, 3, 5, 11, 12, 13, 17 |
| 24 | P1 | 23 |
| 25 | P0 | 2, 3, 11, 12, 13, 17, 23 |

A matriz é de fronts; cada ação numerada herda a dependência de sua frente. Um front só pode ser aberto depois de seus dependentes e do gate P0, quando sua prioridade for P1 ou P2.

## [P0] 1. Governança e priorização

1. Definir a visão de produto para as próximas três temporadas simuladas.
2. Transformar o roadmap em épicos com critérios de aceite verificáveis.
3. Classificar cada iniciativa por valor, risco, dependência e esforço.
4. Criar um quadro de execução com estados descoberta, construção, validação e concluída.
5. Registrar decisões arquiteturais em documentos versionados.
6. Definir responsáveis por motor, dados, frontend, testes e operação.
7. Estabelecer uma cadência quinzenal de revisão do roadmap.
8. Criar um registro de riscos técnicos e de produto.
9. Definir métricas de sucesso para carreira, economia e partidas.
10. Separar claramente escopo essencial, avançado e experimental.
11. Criar critérios para não aceitar dados fictícios em produção.
12. Documentar quais módulos são fontes de verdade para cada domínio.
13. Definir política de compatibilidade para migrações do SQLite.
14. Criar processo de revisão antes de alterar o arquivo-mãe.
15. Registrar decisões de balanceamento com fórmula e justificativa.
16. Definir política de reprodutibilidade por seed.
17. Criar calendário de marcos para uma temporada completa.
18. Priorizar primeiro os fluxos que fecham o ciclo semanal.
19. Medir dívida técnica acumulada a cada checkpoint.
20. Publicar uma matriz de dependências entre os 500 passos.

## [P0] 2. Arquitetura do motor

21. Separar contratos de domínio, persistência e apresentação em módulos explícitos.
22. Documentar o fluxo ARQUIVO-MÃE → SQL → serviço → gateway → tRPC.
23. Criar interfaces comuns para serviços transacionais.
24. Padronizar o parâmetro managed_transaction em todos os escritores.
25. Eliminar commits implícitos em context managers internos.
26. Adicionar um coordenador de unidade de trabalho para o ciclo semanal.
27. Formalizar códigos de erro de domínio em um catálogo único.
28. Criar contexto de execução com temporada, semana, seed e escopo.
29. Adicionar validação de pré-condições antes de cada etapa do tick.
30. Criar contratos de retorno serializáveis para o gateway Python.
31. Versionar o contrato de ações aceitas pelo gateway.
32. Adicionar logs estruturados sem registrar dados sensíveis.
33. Definir limites de tempo para operações mundiais em lote.
34. Criar mecanismo de cancelamento seguro para simulações longas.
35. Separar consultas de leitura de comandos mutáveis no motor.
36. Padronizar nomes de IDs, temporadas, semanas e referências naturais.
37. Adicionar verificação de esquema na inicialização dos serviços.
38. Criar relatório de dependências circulares entre módulos.
39. Documentar pontos seguros para extensão por plugins internos.
40. Construir uma suíte de contratos compartilhados entre Python e TypeScript.

## [P0] 3. Banco de dados e migrações

41. Inventariar todas as tabelas do banco-base e do banco de estado.
42. Documentar as chaves naturais de cada tabela mutável.
43. Criar uma tabela de versão de esquema do estado.
44. Adicionar migrações idempotentes para todos os módulos novos.
45. Validar foreign keys após cada migração em cópia temporária.
46. Criar índices para consultas por clube e semana.
47. Criar índices para ledger por categoria e referência.
48. Criar índices para eventos por status e data.
49. Adicionar constraints contra valores negativos indevidos.
50. Adicionar constraints para níveis de estádio entre 1 e 10.
51. Adicionar constraints para público não exceder capacidade.
52. Adicionar constraints para saldo e lançamentos coerentes.
53. Documentar todas as colunas derivadas e suas fontes.
54. Criar ferramenta para comparar esquema-base e esquema de estado.
55. Criar verificação de tabelas órfãs após importação.
56. Adicionar testes de migração a partir de estados antigos.
57. Criar rotina de backup antes de migrações destrutivas.
58. Documentar estratégia de rollback de migrações não destrutivas.
59. Criar compactação controlada do SQLite após grandes temporadas.
60. Medir planos de consulta das operações mais frequentes.

## [P0] 4. Jogadores e dados canônicos

61. Catalogar todas as posições originais presentes no arquivo-mãe.
62. Normalizar abreviações de posição sem perder o valor original.
63. Validar unicidade global de cada jogador.
64. Mapear histórico de vínculos entre jogador e clube.
65. Preservar status, lado, categoria e titularidade originais.
66. Adicionar validação de faixa para CR1 e CR2.
67. Adicionar evolução temporal de idade e potencial.
68. Criar histórico de atributos por temporada.
69. Criar histórico de contratos individuais.
70. Modelar cláusulas e duração de contrato.
71. Adicionar preferência de posição ao perfil do jogador.
72. Adicionar pé dominante e versatilidade quando disponíveis.
73. Criar perfil de personalidade sem inventar campos ausentes.
74. Registrar disponibilidade e suspensão em tabelas de domínio.
75. Criar consulta de topo mundial por posição.
76. Validar jogadores duplicados em importações futuras.
77. Criar relatório de jogadores sem clube.
78. Criar relatório de clubes com elenco incompleto.
79. Testar serialização de todos os perfis para o frontend.
80. Documentar o mapeamento completo do arquivo-mãe para SQL.

## [P0] 5. Clubes, seleções e identidades

81. Validar os 8.399 clubes contra seus IDs oficiais.
82. Criar consulta de clubes por país e divisão.
83. Criar consulta de seleções por código e confederação.
84. Completar vínculos de escudos presentes no arquivo-mãe.
85. Registrar explicitamente ativos de clube ausentes.
86. Registrar explicitamente ativos de seleção ausentes.
87. Adicionar uniforme primário e secundário quando disponíveis.
88. Criar fallback visual consistente para identidade ausente.
89. Validar nomes duplicados com IDs distintos.
90. Criar aliases de busca sem alterar o nome canônico.
91. Adicionar dados de rivalidade somente quando documentados.
92. Modelar país, região e competição de origem.
93. Criar perfil institucional por clube.
94. Criar histórico de mudanças de nome do clube.
95. Validar relações clube-estádio sem duplicidade.
96. Criar consulta de elenco por clube controlado.
97. Adicionar filtros de clubes por força e país.
98. Testar início de carreira com clube e seleção.
99. Criar proteção contra seleção de entidade inexistente.
100. Documentar todos os fallbacks de identidade no frontend.

## [P1] 6. Elenco e gestão esportiva

101. Criar visão persistida de titulares e reservas.
102. Adicionar formação titular como comando do manager.
103. Validar quantidade mínima de jogadores disponíveis.
104. Criar banco de formações salvas por competição.
105. Adicionar escalação automática baseada em posição.
106. Adicionar substituições planejadas para partidas.
107. Registrar minutos jogados por atleta.
108. Registrar gols, assistências e cartões por partida.
109. Criar cálculo de entrosamento do elenco.
110. Criar impacto de moral na escalação.
111. Adicionar bloqueio de atleta lesionado.
112. Adicionar bloqueio de atleta suspenso.
113. Criar relatório de profundidade por posição.
114. Sinalizar posições sem cobertura adequada.
115. Adicionar gestão de capitão e cobradores.
116. Criar histórico de decisões táticas.
117. Exibir condição física antes da partida.
118. Exibir risco de fadiga por calendário.
119. Adicionar confirmação de escalação antes do jogo.
120. Testar todas as escalações contra regras do campeonato.

## [P1] 7. Comissão técnica e departamentos

121. Completar catálogo de funções profissionais do motor.
122. Validar níveis e atributos de cada profissional.
123. Adicionar contratos e duração para staff contratado.
124. Criar custo de rescisão de profissionais.
125. Adicionar substituição de profissional ativo.
126. Registrar efeito de cada função no domínio correspondente.
127. Criar limites de vagas por departamento.
128. Adicionar bônus de comissão por nível.
129. Adicionar médicos por especialidade quando existirem.
130. Adicionar auxiliares por área tática.
131. Criar histórico de contratações da comissão.
132. Criar consulta de folha individual de staff.
133. Adicionar filtro de mercado por função e nível.
134. Adicionar ordenação por custo-benefício.
135. Criar confirmação antes de contratar profissional.
136. Exibir ausência real de staff no CT.
137. Adicionar alertas de contrato prestes a expirar.
138. Criar impacto de staff na recuperação de atletas.
139. Testar contratação simultânea com concorrência SQLite.
140. Documentar o catálogo sem criar profissionais fictícios em produção.

## [P1] 8. Centro de treinamento e evolução

141. Inventariar todos os departamentos de CT disponíveis.
142. Definir níveis máximos e custos por departamento.
143. Adicionar histórico de evolução do CT.
144. Criar manutenção semanal específica por departamento.
145. Calcular impacto de CT no overall institucional.
146. Adicionar instalações de base quando existirem no SQL.
147. Criar programa de desenvolvimento individual.
148. Adicionar carga de treino por grupo.
149. Adicionar recuperação e descanso planejados.
150. Criar plano semanal de treinamento persistido.
151. Impedir treino incompatível com lesão ativa.
152. Calcular risco de lesão por carga.
153. Adicionar bônus de staff ao treinamento.
154. Criar relatório de evolução por atleta.
155. Adicionar comparação entre potencial e desempenho.
156. Criar tela de orçamento de melhorias.
157. Adicionar previsão de retorno de cada departamento.
158. Emitir alerta para falta de manutenção.
159. Testar rollback de compra de departamento.
160. Validar sincronização de CT com folha semanal.

## [P1] 9. Treinamento, forma e moral

161. Criar estados de forma física e técnica.
162. Definir atualização de forma após cada partida.
163. Adicionar moral individual persistida.
164. Adicionar moral coletiva do elenco.
165. Modelar efeito de vitória e derrota na moral.
166. Modelar efeito de sequência de jogos.
167. Criar treinamento técnico por posição.
168. Criar treinamento tático por formação.
169. Criar treinamento físico com risco calculado.
170. Adicionar sessões de bola parada.
171. Adicionar preparação específica para adversário.
172. Registrar aderência do elenco ao plano.
173. Criar relatório de carga semanal.
174. Adicionar limite de carga por idade.
175. Adicionar descanso após partidas congestionadas.
176. Criar impacto do calendário internacional.
177. Exibir recomendações baseadas em fatos persistidos.
178. Testar determinismo da evolução por seed.
179. Testar rollback de forma após falha do tick.
180. Documentar fórmulas de forma e moral.

## [P1] 10. Lesões, saúde e suspensões

181. Inventariar tabelas de lesões já existentes.
182. Criar estados de lesão com início e previsão de retorno.
183. Registrar diagnóstico e gravidade.
184. Adicionar recuperação diária ou semanal.
185. Aplicar influência médica na recuperação.
186. Impedir escalação de lesionados.
187. Registrar recaída com regra determinística.
188. Adicionar suspensão por cartões.
189. Adicionar suspensão por expulsão.
190. Criar histórico médico do atleta.
191. Emitir alerta de lesão nova.
192. Emitir alerta de retorno ao elenco.
193. Criar tela de departamento médico.
194. Adicionar prognóstico sem prometer precisão clínica real.
195. Testar lesões em partidas de pré-temporada.
196. Testar lesão no meio do ciclo semanal.
197. Testar rollback de lesão após falha posterior.
198. Validar que saúde não inventa jogadores.
199. Adicionar filtros por gravidade e prazo.
200. Documentar limites do modelo de saúde do jogo.

## [P0] 11. Motor de partidas

201. Documentar todas as entradas do MatchEngine.
202. Separar geração de resultado e aplicação do resultado.
203. Fixar seed em cada partida persistida.
204. Calibrar vantagem de mando com dados internos.
205. Calibrar influência de força do elenco.
206. Adicionar influência de forma e moral.
207. Adicionar influência de tática escolhida.
208. Adicionar eventos de gol persistidos.
209. Adicionar cartões e substituições persistidos.
210. Adicionar estatísticas de finalizações.
211. Adicionar posse de bola quando suportada.
212. Adicionar expected goals somente com fórmula documentada.
213. Criar validação de placar não negativo.
214. Criar limite de eventos por partida.
215. Testar confrontos entre clubes reais.
216. Testar partida sem competição vinculada.
217. Testar partida adiada e remarcada.
218. Testar execução duplicada da mesma partida.
219. Testar rollback após resultado parcialmente aplicado.
220. Criar relatório de distribuição de placares por temporada.

## [P0] 12. Competições e classificação

221. Inventariar formatos de competição presentes no motor.
222. Criar configuração de pontos por resultado.
223. Adicionar critérios de desempate documentados.
224. Validar criação de grupos e rodadas.
225. Adicionar mata-mata com ida e volta.
226. Adicionar disputa de pênaltis quando aplicável.
227. Criar classificação derivada de partidas PLAYED.
228. Impedir alteração manual de tabela pelo frontend.
229. Adicionar status de competição por fase.
230. Criar regras para partidas suspensas.
231. Adicionar calendário de finais.
232. Adicionar promoção e rebaixamento configuráveis.
233. Criar histórico de campeões.
234. Configurar premiações por posição.
235. Validar premiação somente ao concluir competição.
236. Impedir pagamento duplicado de premiação.
237. Adicionar alertas de classificação.
238. Criar consulta de competição no gateway.
239. Testar temporadas com múltiplas competições.
240. Documentar limitações das competições ainda não configuradas.

## [P0] 13. Calendário e temporadas

241. Formalizar o relógio lógico de temporada e semana.
242. Criar calendário de pré-temporada.
243. Criar calendário de temporada regular.
244. Adicionar janelas de descanso.
245. Adicionar datas de competições simultâneas.
246. Criar mecanismo de adiamento por conflito.
247. Validar semana sem partidas.
248. Validar semana com várias partidas.
249. Criar avanço diário opcional para serviços internos.
250. Manter avanço semanal como comando principal do manager.
251. Adicionar bloqueio de avanço para estado inválido.
252. Criar histórico de cada avanço.
253. Adicionar previsão do próximo compromisso.
254. Criar consulta de agenda por clube.
255. Adicionar pausas entre temporadas.
256. Criar transição de elenco entre temporadas.
257. Fechar contratos ao término da temporada.
258. Gerar relatório de calendário congestionado.
259. Testar avanço repetido com a mesma chave.
260. Testar restauração de relógio após rollback.

## [P2] 14. IA dos clubes

261. Definir objetivos esportivos por clube.
262. Definir orçamento disponível para IA.
263. Criar avaliação automática de elenco.
264. Criar escalação automática da IA.
265. Adicionar escolha tática da IA.
266. Adicionar priorização de competições.
267. Criar contratação orientada por necessidade.
268. Criar venda orientada por orçamento.
269. Adicionar renovação de contratos da IA.
270. Adicionar evolução de departamentos pela IA.
271. Criar comportamento distinto por nível institucional.
272. Adicionar efeito da reputação nas decisões.
273. Criar planejamento de janela de transferências.
274. Registrar decisões da IA em histórico.
275. Criar explicação legível para decisões relevantes.
276. Impedir que a IA escreva fora das transações do motor.
277. Testar IA com seed determinística.
278. Testar IA em banco mundial isolado.
279. Medir tempo de simulação de milhares de clubes.
280. Criar limites para evitar decisões economicamente impossíveis.

## [P1] 15. Transferências e mercado

281. Inventariar contratos e vínculos atuais de jogadores.
282. Criar janela de transferências configurável.
283. Adicionar lista de jogadores transferíveis.
284. Adicionar propostas entre clubes do mundo.
285. Criar negociação de valor e salário.
286. Adicionar empréstimos com duração.
287. Adicionar opção de compra quando suportada.
288. Registrar taxa de transferência no ledger.
289. Registrar comissão e custos acessórios.
290. Validar saldo antes de concluir negócio.
291. Validar vagas de elenco antes de contratar.
292. Impedir transferência de jogador suspenso em condição proibida.
293. Criar histórico de cada negociação.
294. Adicionar aprovação do manager para propostas recebidas.
295. Emitir alerta de transferência concluída.
296. Criar evento de transferência cancelada.
297. Testar concorrência entre propostas.
298. Testar rollback após débito de transferência.
299. Separar dados fictícios de cenários de teste.
300. Documentar a política de não usar dados reais inventados.

## [P2] 16. Scouting e base

301. Inventariar missões de scouting existentes.
302. Criar regiões de observação configuráveis.
303. Adicionar duração e custo de cada missão.
304. Registrar relatório de observação persistido.
305. Separar descoberta de contratação.
306. Adicionar filtros por posição e faixa etária.
307. Adicionar filtro por potencial quando disponível.
308. Criar prioridade de missão por necessidade do elenco.
309. Adicionar staff de scouting ao cálculo.
310. Emitir alerta de relatório concluído.
311. Criar comparação entre relatório e atributos reais.
312. Impedir contratação sem confirmação do manager.
313. Adicionar base de formação quando houver dados canônicos.
314. Criar progressão de atletas da base.
315. Registrar promoção ao elenco profissional.
316. Adicionar custo de manutenção da base.
317. Testar determinismo de descobertas por seed.
318. Testar expiração de missão de scouting.
319. Criar tela de relatórios disponíveis.
320. Documentar campos que não existem no arquivo-mãe.

## [P0] 17. Economia mundial

321. Documentar todas as categorias do FinanceLedger.
322. Criar moeda e unidade monetária únicas no motor.
323. Validar lançamentos com referência natural.
324. Adicionar fechamento semanal do ledger.
325. Criar relatório de receitas por clube.
326. Criar relatório de despesas por clube.
327. Adicionar projeção de caixa para 39 semanas.
328. Preservar a reserva de 39 semanas da fórmula original.
329. Adicionar receita de bilheteria por partida.
330. Adicionar manutenção de estádio por semana.
331. Adicionar folha individual de jogadores.
332. Adicionar folha de comissão e departamentos.
333. Criar alerta de saldo baixo.
334. Criar regra de déficit controlado.
335. Definir comportamento de insolvência.
336. Modelar recuperação financeira sem valores arbitrários.
337. Adicionar relatórios de economia mundial.
338. Testar idempotência de cada categoria de lançamento.
339. Testar rollback de caixa após falha tardia.
340. Criar ferramenta de auditoria por temporada.

## [P1] 18. Finanças do clube

341. Criar painel de caixa atual e projetado.
342. Separar saldo disponível de receitas futuras.
343. Exibir folha semanal individualizada.
344. Exibir manutenção semanal consolidada.
345. Exibir receitas de patrocínio ativas.
346. Exibir bilheteria das últimas partidas.
347. Exibir premiações recebidas por competição.
348. Criar filtros por semana e categoria.
349. Criar detalhe de cada lançamento do ledger.
350. Adicionar exportação financeira em CSV.
351. Adicionar bloqueio visual para saldo insuficiente.
352. Criar confirmação para despesas irreversíveis.
353. Adicionar previsão de caixa pós-próxima partida.
354. Exibir impacto de uma contratação antes de confirmar.
355. Criar alerta para contratos comerciais expirando.
356. Adicionar comparação entre orçamento e realizado.
357. Criar histórico financeiro por temporada.
358. Testar arredondamentos monetários.
359. Testar transações concorrentes sobre o mesmo clube.
360. Documentar que o frontend nunca calcula o saldo.

## [P1] 19. Estádio e infraestrutura

361. Completar regras de custo por componente do estádio.
362. Validar níveis de arquibancada de 1 a 10.
363. Validar níveis de campo de 1 a 10.
364. Validar níveis de estrutura de 1 a 10.
365. Validar níveis de equipes de 1 a 10.
366. Adicionar histórico de cada upgrade.
367. Adicionar previsão de capacidade após upgrade.
368. Adicionar previsão de qualidade de matchday.
369. Calcular manutenção de cada componente.
370. Emitir alerta de evolução concluída.
371. Criar alerta de manutenção onerosa.
372. Adicionar estado de estádio indisponível.
373. Adicionar estádio neutro para partidas especiais.
374. Criar regras de reforma durante a temporada.
375. Adicionar limite de capacidade por competição.
376. Exibir estádio real no dashboard do clube.
377. Criar histórico visual de evolução.
378. Testar bootstrap mundial repetido.
379. Testar upgrade com caixa insuficiente.
380. Testar rollback de upgrade em falha do ledger.

## [P1] 20. Torcida, reputação e público

381. Separar torcida de reputação esportiva e comercial.
382. Definir tamanho inicial da torcida por dado canônico.
383. Atualizar satisfação após cada partida jogada.
384. Atualizar engajamento após cada partida jogada.
385. Atualizar interesse por competição.
386. Modelar efeito gradual de vitórias.
387. Modelar efeito gradual de derrotas.
388. Modelar efeito de sequência invicta.
389. Modelar efeito de estádio e conforto.
390. Calcular demanda com seed determinística.
391. Impedir público negativo.
392. Impedir público acima da capacidade.
393. Aplicar preço de ingresso do motor.
394. Registrar público esperado e realizado.
395. Criar histórico de público por partida.
396. Emitir alerta de recorde de público.
397. Emitir alerta de queda relevante de presença.
398. Criar painel de satisfação da torcida.
399. Testar repetição da mesma partida sem dupla atualização.
400. Documentar todas as fórmulas sociais.

## [P1] 21. Patrocínios e mídia

401. Completar catálogo de marcas por estrela.
402. Definir requisitos institucionais por proposta.
403. Rotacionar ofertas expiradas sem aceite automático.
404. Preservar propostas aceitas no histórico.
405. Adicionar contratos de seis semanas configuráveis.
406. Calcular sinal inicial no ledger.
407. Calcular receita semanal no ledger.
408. Adicionar missões por vitórias.
409. Adicionar missões por gols.
410. Adicionar missões por público.
411. Adicionar missão de classificação.
412. Registrar progresso somente por fatos SQL.
413. Impedir progresso duplicado por partida.
414. Emitir alerta de contrato aceito.
415. Emitir alerta de missão concluída.
416. Emitir alerta de proposta expirada.
417. Adicionar slots de patrocinadores secundários.
418. Criar mídia e direitos de transmissão configuráveis.
419. Testar rollback de aceitação comercial.
420. Documentar critérios de elegibilidade e estrelas.

## [P1] 22. Eventos, alertas e notícias

421. Completar índices da tabela club_events.
422. Padronizar referências idempotentes de eventos.
423. Adicionar origem técnica de cada alerta.
424. Adicionar impacto financeiro estruturado.
425. Adicionar eventos de contratação de staff.
426. Adicionar eventos de departamento evoluído.
427. Adicionar eventos de transferência.
428. Adicionar eventos de lesão.
429. Adicionar eventos de suspensão.
430. Adicionar eventos de partida concluída.
431. Adicionar eventos de premiação paga.
432. Adicionar eventos de caixa baixo.
433. Adicionar eventos de reputação alterada.
434. Adicionar severidade calculada por impacto.
435. Adicionar leitura individual persistida.
436. Adicionar marcação de todos como lidos.
437. Criar paginação do feed por data.
438. Criar filtros por tipo e severidade.
439. Adicionar feed de notícias ao dashboard.
440. Testar deduplicação e rollback de eventos.

## [P0] 23. Frontend e tRPC

441. Completar tipos TypeScript para todos os retornos do gateway.
442. Separar routers tRPC por domínio de negócio.
443. Adicionar validação Zod a todas as mutations.
444. Padronizar conversão de erros de domínio.
445. Adicionar estados de carregamento por componente.
446. Adicionar estados de vazio honestos por consulta.
447. Adicionar estados de erro recuperáveis.
448. Invalidar queries após cada mutation relevante.
449. Evitar qualquer fetch direto de regras esportivas.
450. Adicionar consulta de eventos persistidos.
451. Adicionar tela detalhada de finanças.
452. Adicionar tela detalhada de torcida.
453. Adicionar tela detalhada de competição.
454. Adicionar tela detalhada de calendário.
455. Adicionar tela de histórico do estádio.
456. Adicionar navegação para detalhes de alertas.
457. Adicionar acessibilidade aos controles do manager.
458. Adicionar atalhos de teclado documentados.
459. Adicionar tratamento de sessão expirada.
460. Validar todos os fluxos em viewport móvel.

## [P1] 24. UX e design editorial

461. Refinar hierarquia tipográfica do Editorial de Arquibancada.
462. Padronizar espaçamento entre seções.
463. Criar tokens para cores de status.
464. Garantir contraste em todos os painéis.
465. Adicionar foco visível a todos os botões.
466. Revisar ordem de leitura para leitores de tela.
467. Adicionar textos alternativos para escudos e estádios.
468. Reduzir movimentos para prefers-reduced-motion.
469. Criar feedback visual para mutations em andamento.
470. Criar confirmação para ações financeiras.
471. Adicionar desfazer apenas onde houver comando seguro.
472. Criar skeletons específicos para tabelas.
473. Criar empty states com próxima ação clara.
474. Padronizar mensagens de erro em português.
475. Adicionar filtro persistente por seção.
476. Melhorar visualização em 375px.
477. Validar tablet em 768px.
478. Validar desktop amplo em 1440px.
479. Documentar decisões de composição visual.
480. Criar revisão visual a cada novo domínio.

## [P0] 25. Testes, entrega e operação

481. Executar a suíte Python completa em cada checkpoint.
482. Executar a suíte Vitest completa em cada checkpoint.
483. Executar TypeScript check antes de cada entrega.
484. Executar build de produção antes de publicar.
485. Criar testes de contrato Python-TypeScript.
486. Criar testes de concorrência SQLite.
487. Criar testes de rollback para cada etapa do tick.
488. Criar testes de idempotência para cada escritor.
489. Criar testes de determinismo por seed.
490. Criar cenário de temporada completa em banco temporário.
491. Criar cenário de múltiplas temporadas.
492. Criar teste de não alteração do banco-base.
493. Criar teste de integridade e foreign keys.
494. Criar teste de recuperação após processo interrompido.
495. Criar relatório de cobertura por domínio.
496. Criar benchmark do bootstrap dos 8.399 clubes.
497. Criar benchmark de avanço mundial.
498. Criar README de instalação e operação segura.
499. Gerar manifesto e hash de cada pacote entregue.
500. Salvar checkpoint antes de cada publicação.

