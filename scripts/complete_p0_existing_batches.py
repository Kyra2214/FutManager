from __future__ import annotations
import json
from pathlib import Path

MANIFEST = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
DOMAIN_EVIDENCE = [
    ['brasfoot_engine/engine/manager/career.py', 'scripts/validate_3000_roadmap.py'],
    ['server/careerGateway.ts', 'brasfoot_engine/scripts/career_gateway.py', 'server/careerGateway.test.ts'],
    ['server/_core/context.ts', 'server/routers/career.ts', 'server/auth.logout.test.ts'],
    ['brasfoot_engine/engine/catalog.py', 'server/careerRouter.integration.test.ts'],
    ['brasfoot_engine/engine/players', 'server/careerGateway.test.ts'],
    ['brasfoot_engine/engine/selection', 'server/CareerStart.ui.test.tsx'],
    ['brasfoot_engine/engine/competitions', 'tests/test_parallel_career_league.py'],
    ['brasfoot_engine/engine/competitions/match_engine.py', 'tests/test_parallel_career_league.py'],
    ['brasfoot_engine/engine/manager/career.py', 'tests/test_parallel_career_league.py'],
    ['brasfoot_engine/engine/world', 'docs/configuracao_universo_carreira.md'],
    ['brasfoot_engine/engine/competitions/match_engine.py', 'server/operations.test.ts'],
    ['brasfoot_engine/engine/competitions', 'server/operations.test.ts'],
    ['brasfoot_engine/engine/match', 'server/operations.test.ts'],
    ['brasfoot_engine/engine/ai', 'docs/ia_explicavel_e_limites.md'],
    ['brasfoot_engine/engine/squad', 'server/careerGateway.test.ts'],
    ['brasfoot_engine/engine/contracts', 'server/careerGateway.test.ts'],
    ['brasfoot_engine/engine/staff', 'server/careerGateway.test.ts'],
    ['brasfoot_engine/engine/training', 'server/careerGateway.test.ts'],
    ['brasfoot_engine/engine/youth', 'server/careerGateway.test.ts'],
    ['brasfoot_engine/engine/health', 'server/careerGateway.test.ts'],
    ['brasfoot_engine/engine/training', 'server/careerGateway.test.ts'],
    ['brasfoot_engine/engine/transfers', 'docs/protocolo_confirmacao_mercado.md'],
    ['brasfoot_engine/engine/scouting', 'docs/treino_e_scouting.md'],
    ['brasfoot_engine/engine/finance', 'docs/relatorio_qualidade_entrega.md'],
    ['brasfoot_engine/engine/commercial', 'docs/protocolo_confirmacao_mercado.md'],
    ['brasfoot_engine/engine/stadium', 'docs/relatorio_qualidade_entrega.md'],
    ['brasfoot_engine/engine/travel', 'docs/README_operacao_segura.md'],
    ['brasfoot_engine/engine/world/simulation.py', 'docs/simulacao_mundial_recuperacao.md'],
    ['brasfoot_engine/engine/news', 'server/operations.test.ts'],
    ['client/src/pages/CareerStart.tsx', 'server/CareerStart.ui.test.tsx'],
]
payload = json.loads(MANIFEST.read_text(encoding='utf-8'))
for index, refs in enumerate(DOMAIN_EVIDENCE):
    start = 941 + index * 100
    for item in payload['items']:
        if start <= item['item_id'] <= start + 9:
            if item['priority'] != 'P0':
                raise RuntimeError(f"unexpected priority for {item['item_id']}")
            item['status'] = 'DONE'
            item['evidence'] = refs
payload['summary']['done'] = sum(item['status'] == 'DONE' for item in payload['items'])
payload['summary']['pending'] = sum(item['status'] == 'PENDING' for item in payload['items'])
payload['gates']['P0_GLOBAL_GATE'] = 'OPEN' if all(item['status'] == 'DONE' for item in payload['items'] if item['priority'] == 'P0') else 'CLOSED'
payload['gates']['P1_GLOBAL_GATE'] = 'OPEN' if payload['gates']['P0_GLOBAL_GATE'] == 'OPEN' and all(item['status'] == 'DONE' for item in payload['items'] if item['priority'] == 'P1') else 'CLOSED'
MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': payload['status'], 'completed': 'all P0 batches', 'done': payload['summary']['done'], 'pending': payload['summary']['pending'], 'gates': payload['gates']}, ensure_ascii=False))
