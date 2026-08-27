from pathlib import Path

START = 941
PER_DOMAIN = 100
DOMAINS = [
    ("Fundação do GameState", ["schema", "migração", "constraint", "índice", "backup", "checksum", "versão", "drift", "integridade", "telemetria"]),
    ("Persistência e recuperação", ["snapshot", "restore", "journal", "checkpoint", "replay", "retention", "export", "import", "rollback", "recovery"]),
    ("Gateway e contratos", ["payload", "procedure", "erro", "permissão", "idempotência", "versão", "timeout", "telemetria", "compatibilidade", "auditoria"]),
    ("Autenticação e governança de acesso", ["login", "sessão", "papel", "escopo", "convite", "revogação", "MFA", "consentimento", "auditoria", "privacidade"]),
    ("Catálogo de clubes", ["clube", "país", "cidade", "identidade", "alias", "escudo", "estádio", "reputação", "origem", "unicidade"]),
    ("Catálogo de jogadores", ["jogador", "posição", "atributo", "potencial", "idade", "alias", "nacionalidade", "histórico", "unicidade", "origem"]),
    ("Seleções nacionais", ["seleção", "convocação", "ranking", "data FIFA", "comissão", "torneio", "elegibilidade", "calendário", "lesão", "histórico"]),
    ("Ligas nacionais", ["divisão", "membership", "regulamento", "rodada", "tabela", "promoção", "rebaixamento", "registro", "calendário", "premiação"]),
    ("Liga paralela da carreira", ["universo", "membership", "sorteio", "divisão", "fixture", "rodada", "tabela", "promoção", "rebaixamento", "histórico"]),
    ("Competições continentais", ["vaga", "pote", "grupo", "mata-mata", "sorteio", "coeficiente", "registro", "premiação", "calendário", "histórico"]),
    ("Calendário mundial", ["semana", "feriado", "janela", "conflito", "reagendamento", "fuso", "clima", "segurança", "televisão", "auditoria"]),
    ("Motor de partidas", ["escalação", "tática", "evento", "placar", "posse", "finalização", "xG", "substituição", "árbitro", "reprocessamento"]),
    ("Estatísticas avançadas", ["xG", "xA", "posse", "duelo", "pressão", "mapa", "finalização", "passe", "defesa", "relatório"]),
    ("IA dos clubes", ["diagnóstico", "contratação", "venda", "escalação", "treino", "tática", "orçamento", "objetivo", "risco", "explicação"]),
    ("Elenco e hierarquia", ["titular", "reserva", "liderança", "promessa", "minutos", "camisa", "inscrição", "coesão", "profundidade", "relatório"]),
    ("Contratos de jogadores", ["salário", "duração", "bônus", "cláusula", "renovação", "rescisão", "empréstimo", "opção", "histórico", "auditoria"]),
    ("Comissão técnica", ["treinador", "auxiliar", "médico", "scout", "especialidade", "nível", "vaga", "contrato", "salário", "organograma"]),
    ("Centro de treinamento", ["departamento", "nível", "capacidade", "manutenção", "upgrade", "treino", "base", "medicina", "scouting", "auditoria"]),
    ("Base e formação", ["academia", "categoria", "captação", "desenvolvimento", "promoção", "bolsa", "educação", "minutos", "contrato", "relatório"]),
    ("Saúde e lesões", ["lesão", "diagnóstico", "tratamento", "fisioterapia", "retorno", "risco", "carga", "suspensão", "disponibilidade", "auditoria"]),
    ("Treinamento e evolução", ["microciclo", "carga", "objetivo", "intensidade", "descanso", "tática", "atributo", "potencial", "overtraining", "avaliação"]),
    ("Mercado e transferências", ["janela", "proposta", "contraproposta", "valor", "comissão", "empréstimo", "opção", "registro", "shortlist", "histórico"]),
    ("Scouting e observação", ["missão", "região", "posição", "filtro", "confiança", "evidência", "comparação", "relatório", "expiração", "aprovação"]),
    ("Finanças e contabilidade", ["caixa", "receita", "despesa", "salário", "bônus", "ledger", "orçamento", "projeção", "déficit", "fechamento"]),
    ("Patrocínios e comercial", ["oferta", "estrela", "missão", "audiência", "contrato", "expiração", "bônus", "inventário", "ativação", "relatório"]),
    ("Estádio e torcida", ["capacidade", "setor", "ingresso", "ocupação", "torcida", "reputação", "segurança", "concessão", "upgrade", "evento"]),
    ("Viagens e logística", ["rota", "distância", "custo", "hotel", "voo", "ônibus", "descanso", "segurança", "bagagem", "auditoria"]),
    ("Simulação mundial", ["fila", "lote", "seed", "checkpoint", "throughput", "falha", "retomada", "prioridade", "métrica", "relatório"]),
    ("Notícias e eventos", ["notícia", "evento", "feed", "severidade", "filtro", "paginação", "arquivamento", "preferência", "snooze", "histórico"]),
    ("Manager e carreira", ["save", "objetivo", "reputação", "experiência", "oferta", "troca", "aposentadoria", "legado", "conquista", "histórico"]),
    ("Interface e experiência móvel", ["dashboard", "navegação", "tabela", "filtro", "formulário", "acessibilidade", "responsividade", "offline", "animação", "feedback"]),
    ("Testes, observabilidade e entrega", ["unitário", "integração", "E2E", "benchmark", "log", "métrica", "alerta", "release", "rollback", "documentação"]),
]
VERBS = [
    "definir contrato para", "validar regras de", "persistir estado de", "expor leitura de", "proteger mutação de", "auditar fluxo de", "otimizar consulta de", "simular cenário de", "documentar ciclo de", "testar integração de",
]

DOMAINS[0] = ("Fundação e persistência do GameState", DOMAINS[0][1][:5] + DOMAINS[1][1][:5])
DOMAINS.pop(1)
DOMAINS[-2] = ("Interface, testes e entrega", DOMAINS[-2][1][:5] + DOMAINS[-1][1][:5])
DOMAINS.pop()
assert len(DOMAINS) == 30

lines = [
    "# FutManager — Roadmap de 3.000 melhorias (941–3.940)",
    "",
    "> Documento gerado de forma determinística para organizar as próximas 3.000 melhorias do FutManager. A numeração continua o roadmap anterior, que terminou no passo 940.",
    "",
    "## Regras de execução",
    "",
    "O **GameState SQLite é a única fonte da verdade**. O frontend apenas consulta contratos tRPC; regras esportivas, sorteios, calendário, classificação, finanças e mutações pertencem ao motor e aos serviços autorizados.",
    "",
    "O gate **P0_GLOBAL_GATE** bloqueia todos os itens P1 e P2 até que os 300 itens P0 estejam implementados, testados e auditados. Depois, **P1_GLOBAL_GATE** bloqueia P2 até que os 2.100 itens P1 estejam validados. Cada item também depende do item anterior do próprio domínio, salvo o primeiro item de cada faixa, que depende do gate global correspondente.",
    "",
    "| Campo | Regra |",
    "|---|---|",
    "| Escopo | 30 domínios × 100 melhorias = 3.000 itens |",
    "| Numeração | 941 a 3.940, sem lacunas |",
    "| P0 | 10 primeiros itens de cada domínio = 300 itens |",
    "| P1 | Itens 11–80 de cada domínio = 2.100 itens |",
    "| P2 | Itens 81–100 de cada domínio = 600 itens |",
    "| Fonte de estado | GameState SQLite |",
    "| Critério | Evidência reproduzível em teste, auditoria, métrica ou screenshot |",
    "",
    "## Índice de domínios",
    "",
    "| Domínio | Faixa | Quantidade | P0 | P1 | P2 |",
    "|---|---:|---:|---:|---:|---:|",
]

for index, (domain, _) in enumerate(DOMAINS):
    first = START + index * PER_DOMAIN
    last = first + PER_DOMAIN - 1
    lines.append(f"| {index + 1:02d}. {domain} | {first}–{last} | 100 | 10 | 70 | 20 |")

lines.extend(["", "## Lista completa", ""])
number = START
for domain_index, (domain, subjects) in enumerate(DOMAINS, start=1):
    lines.extend([f"### {domain_index:02d}. {domain}", ""])
    for row in range(1, PER_DOMAIN + 1):
        subject = subjects[(row - 1) // 10]
        verb = VERBS[(row - 1) % 10]
        priority = "P0" if row <= 10 else "P1" if row <= 80 else "P2"
        if row == 1:
            dependency = "P0_GLOBAL_GATE"
        elif row == 11:
            dependency = "P0_GLOBAL_GATE + passo anterior do domínio"
        elif row == 81:
            dependency = "P1_GLOBAL_GATE + passo anterior do domínio"
        else:
            dependency = str(number - 1)
        criterion = f"teste/fixture do domínio {domain_index:02d}, leitura SQLite e auditoria do contrato"
        lines.append(f"{number}. **[{priority}] {verb} {subject}** — Dependência: `{dependency}`. Critério: {criterion}.")
        number += 1
    lines.append("")

lines.extend([
    "## Distribuição e governança",
    "",
    "A execução deve ocorrer em ordem numérica dentro de cada domínio e respeitar os gates globais. Nenhum item P1 ou P2 pode ser considerado concluído apenas por renderização: cada entrega precisa comprovar persistência, contrato autorizado, teste automatizado e comportamento observável.",
    "",
    "## Critério de encerramento do roadmap",
    "",
    "O roadmap será considerado encerrado quando os 3.000 itens possuírem referência de implementação, teste ou evidência; a validação de numeração e unicidade retornar `VALID`; o GameState passar por `PRAGMA integrity_check`; e os gates globais registrarem a cadeia P0 → P1 → P2.",
    "",
])

assert number == START + 3000
output = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_melhorias_941_3940.md')
output.write_text('\n'.join(lines), encoding='utf-8')
print(output)
print(f'items={number - START}')
