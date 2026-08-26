from __future__ import annotations

import json
import platform
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path('/home/ubuntu')
ENGINE = ROOT / 'brasfoot_engine'
sys.path.insert(0, str(ENGINE))
from engine.world.orchestrator import IntegrationOrchestrator

base = ENGINE / 'data/database/game.db'
with sqlite3.connect(base) as connection:
    start = time.perf_counter()
    count = int(connection.execute('SELECT COUNT(*) FROM times').fetchone()[0])
    count_seconds = time.perf_counter() - start

with tempfile.TemporaryDirectory(prefix='futmanager-benchmark-') as directory:
    state = Path(directory) / 'game.db'
    shutil.copy2(ENGINE / 'data/state/game.db', state)
    start = time.perf_counter()
    orchestrator = IntegrationOrchestrator(state)
    orchestrator.advance_week(seed=2500)
    advance_seconds = time.perf_counter() - start
    orchestrator.close()

result = {
    'clubs_in_canonical_base': count,
    'expected_clubs': 8399,
    'club_count_query_seconds': round(count_seconds, 6),
    'world_advance_seconds_on_temporary_gamestate': round(advance_seconds, 6),
    'python': sys.version.split()[0],
    'platform': platform.platform(),
    'database': 'read-only base count + temporary GameState advance',
}
output = ROOT / 'futmanager_frontend/docs/p0_25_benchmark_2026-08-26.json'
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
if count != 8399:
    raise SystemExit('CANONICAL_CLUB_COUNT_MISMATCH')
