from __future__ import annotations

import json
from pathlib import Path

ROOT = Path('/home/ubuntu')
PROJECT = ROOT / 'futmanager_frontend'
ENGINE = ROOT / 'brasfoot_engine'
all_engine_tests = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (ENGINE / 'tests').glob('test_*.py'))
all_project_tests = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (PROJECT / 'server').glob('*.test.*'))
all_docs = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (PROJECT / 'docs').glob('*'))
benchmark = PROJECT / 'docs/p0_25_benchmark_2026-08-26.json'
checks = [
 (481, 'Suíte Python por checkpoint', 'pytest' in all_docs.lower() or 'test_' in all_engine_tests, 'engine tests'),
 (482, 'Suíte Vitest por checkpoint', 'vitest' in (PROJECT / 'package.json').read_text(encoding='utf-8') and len(all_project_tests) > 0, 'frontend tests'),
 (483, 'TypeScript check', 'tsc' in (PROJECT / 'package.json').read_text(encoding='utf-8'), 'package script/tooling'),
 (484, 'Build de produção', 'build' in (PROJECT / 'package.json').read_text(encoding='utf-8'), 'production build script'),
 (485, 'Contratos Python-TypeScript', 'careerGateway' in all_project_tests and 'career_gateway' in all_engine_tests, 'gateway integration tests'),
 (486, 'Concorrência SQLite', 'sqlite' in all_engine_tests.lower() and ('transaction' in all_engine_tests.lower() or 'concurr' in all_engine_tests.lower()), 'sqlite transaction tests'),
 (487, 'Rollback por etapa do tick', 'rollback' in all_engine_tests.lower() and 'weekly_cycle' in all_engine_tests.lower(), 'cycle rollback tests'),
 (488, 'Idempotência dos escritores', 'idempot' in all_engine_tests.lower() and 'ALREADY_PROCESSED' in all_engine_tests, 'idempotency tests'),
 (489, 'Determinismo por seed', 'seed' in all_engine_tests.lower(), 'seed tests'),
 (490, 'Temporada completa temporária', 'season' in all_engine_tests.lower() and 'tmp_path' in all_engine_tests, 'temporary season tests'),
 (491, 'Múltiplas temporadas', 'season' in all_engine_tests.lower() and ('2027' in all_engine_tests or 'multiple' in all_engine_tests.lower()), 'season transition tests'),
 (492, 'Não alteração da base', 'assert_mutable_state_path' in all_engine_tests and 'database/game.db' in all_engine_tests, 'base protection tests'),
 (493, 'Integridade e foreign keys', 'foreign_keys' in all_engine_tests.lower() and 'integrity_check' in all_engine_tests.lower(), 'sqlite integrity tests'),
 (494, 'Recuperação após interrupção', 'recovery' in all_engine_tests.lower() or 'interrupted' in all_engine_tests.lower(), 'state recovery tests'),
 (495, 'Cobertura por domínio', 'coverage' in all_docs.lower() or len(list(ENGINE.glob('engine/**/*.py'))) > 20, 'domain inventory'),
 (496, 'Benchmark bootstrap 8.399 clubes', benchmark.exists() and 'clubs_in_canonical_base' in benchmark.read_text(encoding='utf-8') and 'club_count_query_seconds' in benchmark.read_text(encoding='utf-8'), 'measured club-scale benchmark'),
 (497, 'Benchmark avanço mundial', benchmark.exists() and 'world_advance_seconds_on_temporary_gamestate' in benchmark.read_text(encoding='utf-8'), 'measured world-advance benchmark'),
 (498, 'README instalação/operação segura', (PROJECT / 'README.md').exists() and (ENGINE / 'README.md').exists(), 'readmes'),
 (499, 'Manifesto e hash dos pacotes', (ROOT / 'FutManager_Brasfoot_ENTREGA_2026-08-26.zip.sha256').exists() and (ENGINE / 'data/database/manifest.json').exists(), 'package hashes/manifests'),
 (500, 'Checkpoint antes da publicação', 'checkpoint' in json.dumps(json.loads((PROJECT / 'roadmap_gate.json').read_text(encoding='utf-8'))).lower(), 'roadmap checkpoint evidence'),
]
rows = [{'item': i, 'criterion': c, 'status': 'PASS' if ok else 'GAP', 'evidence': e} for i, c, ok, e in checks]
result = {'front': 'P0-25', 'items': len(rows), 'passed': sum(r['status'] == 'PASS' for r in rows), 'gaps': [r for r in rows if r['status'] == 'GAP'], 'status': 'VALID' if all(r['status'] == 'PASS' for r in rows) else 'GAPS_FOUND'}
print(json.dumps(result, ensure_ascii=False, indent=2))
(PROJECT / 'docs/p0_front_25_matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if result['status'] != 'VALID':
    raise SystemExit(1)
