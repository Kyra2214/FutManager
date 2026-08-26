from __future__ import annotations

from pathlib import Path

ROOT = Path('/home/ubuntu/futmanager_frontend/client/src')
GAME_PAGES = [ROOT / 'pages/Home.tsx', ROOT / 'pages/CareerStart.tsx']
required_trpc = ('trpc.', 'useQuery', 'useMutation')
forbidden_network = ('fetch(', 'axios.', 'XMLHttpRequest')
missing_files = [str(path) for path in GAME_PAGES if not path.exists()]
forbidden: dict[str, list[str]] = {}
missing_contracts: dict[str, list[str]] = {}
for path in GAME_PAGES:
    if not path.exists():
        continue
    text = path.read_text(encoding='utf-8', errors='replace')
    bad = [token for token in forbidden_network if token in text]
    missing = [token for token in required_trpc if token not in text]
    if bad:
        forbidden[str(path.relative_to(ROOT))] = bad
    if missing:
        missing_contracts[str(path.relative_to(ROOT))] = missing
result = {
    'front': 'P0-23',
    'game_pages_checked': len(GAME_PAGES),
    'missing_files': missing_files,
    'forbidden_direct_network': forbidden,
    'missing_trpc_contracts': missing_contracts,
    'showcase_excluded': True,
    'status': 'VALID' if not missing_files and not forbidden and not missing_contracts else 'GAPS_FOUND',
}
print(result)
if result['status'] != 'VALID':
    raise SystemExit(1)
