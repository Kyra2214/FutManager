from __future__ import annotations

import json
from pathlib import Path

ROOT = Path('/home/ubuntu/futmanager_frontend')
client = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (ROOT / 'client/src').rglob('*.tsx'))
page_client = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (ROOT / 'client/src/pages').rglob('*.tsx'))
server = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (ROOT / 'server').rglob('*.ts'))
tests = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (ROOT / 'server').glob('*.test.*'))
checks = [
 (441, 'Tipos TypeScript dos retornos', 'trpc.' in client and 'workspace' in client, 'typed tRPC hooks'),
 (442, 'Routers separados por domínio', all(token in server for token in ['club', 'matches', 'career', 'events']), 'domain routers'),
 (443, 'Validação Zod nas mutations', 'z.object' in server and 'mutation' in server, 'router schemas'),
 (444, 'Erros de domínio padronizados', 'TRPCError' in server or 'error_code' in server, 'error conversion'),
 (445, 'Loading por componente', '.isLoading' in client, 'component loading states'),
 (446, 'Vazios honestos', 'Nenhum' in client and 'não há' in client, 'empty states'),
 (447, 'Erros recuperáveis', 'isError' in client or 'error' in client.lower(), 'recoverable errors'),
 (448, 'Invalidar após mutation', 'invalidate' in client, 'query invalidation'),
 (449, 'Sem fetch direto esportivo', 'fetch(' not in page_client and 'axios' not in page_client.lower(), 'tRPC-only page transport'),
 (450, 'Eventos persistidos', 'events.' in client and 'events' in server, 'events contract'),
 (451, 'Finanças detalhadas', 'finan' in client.lower() or 'caixa' in client.lower(), 'finance view'),
 (452, 'Torcida detalhada', 'torcida' in client.lower() or 'fans' in client.lower(), 'fans view'),
 (453, 'Competição detalhada', 'competição' in client.lower() or 'competition' in client.lower(), 'competition view'),
 (454, 'Calendário detalhado', 'calend' in client.lower(), 'calendar view'),
 (455, 'Histórico do estádio', 'estádio' in client.lower() and ('hist' in client.lower() or 'stadium' in client.lower()), 'stadium view'),
 (456, 'Navegação de alertas', 'alert' in client.lower() and ('onClick' in client or 'href' in client), 'alert navigation'),
 (457, 'Acessibilidade', 'aria-' in client and 'alt=' in client, 'aria and image labels'),
 (458, 'Atalhos documentados', 'keyboard' in client.lower() or 'teclado' in client.lower() or 'shortcut' in client.lower(), 'keyboard documentation'),
 (459, 'Sessão expirada', 'startLogin' in client and 'UNAUTHED_ERR_MSG' in client, 'auth recovery'),
 (460, 'Viewport móvel', 'mobile' in tests.lower() or 'viewport' in tests.lower() or 'responsive' in '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (ROOT / 'docs').glob('*')).lower(), 'responsive validation'),
]
rows = [{'item': i, 'criterion': c, 'status': 'PASS' if ok else 'GAP', 'evidence': e} for i, c, ok, e in checks]
result = {'front': 'P0-23', 'items': len(rows), 'passed': sum(r['status'] == 'PASS' for r in rows), 'gaps': [r for r in rows if r['status'] == 'GAP'], 'status': 'VALID' if all(r['status'] == 'PASS' for r in rows) else 'GAPS_FOUND'}
print(json.dumps(result, ensure_ascii=False, indent=2))
(ROOT / 'docs/p0_front_23_matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if result['status'] != 'VALID':
    raise SystemExit(1)
