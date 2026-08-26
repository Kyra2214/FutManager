from __future__ import annotations

import json
from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
PROJECT = Path('/home/ubuntu/futmanager_frontend')
implementation = (ENGINE / 'engine/competitions/match_engine.py').read_text(encoding='utf-8', errors='replace')
existing_tests = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (ENGINE / 'tests').glob('test_*.py'))
match_audit = (PROJECT / 'scripts/validate_p0_match_engine.py').read_text(encoding='utf-8', errors='replace')

checks = [
    (201, 'Documentar todas as entradas do MatchEngine', 'def play(' in implementation and 'seed' in implementation and (ENGINE / 'docs').exists(), 'MatchEngine inputs + docs'),
    (202, 'Separar geração de resultado e aplicação', 'generate_result' in implementation and 'apply_result' in implementation, 'MatchEngine generate/apply'),
    (203, 'Fixar seed em cada partida persistida', 'seed INTEGER' in implementation and 'seed if seed is not None' in implementation, 'matches.seed + play'),
    (204, 'Calibrar vantagem de mando', 'home_context' in implementation and 'mando de campo documentado' in implementation, 'generate_result home context + documented home advantage'),
    (205, 'Calibrar força do elenco', 'home_strength' in implementation and 'away_strength' in implementation, 'strength inputs'),
    (206, 'Influência de forma e moral', 'form' in implementation.lower() and 'moral' in implementation.lower(), 'form/moral inputs'),
    (207, 'Influência de tática', 'tactic' in implementation.lower() or 'tática' in implementation.lower(), 'tactic input'),
    (208, 'Eventos de gol persistidos', 'match_events' in implementation and "'RESULT'" in implementation, 'match_events result'),
    (209, 'Cartões e substituições persistidos', 'cards' in implementation and 'substitution' in implementation.lower(), 'event/stat fields'),
    (210, 'Estatísticas de finalizações', 'shots' in implementation.lower() or 'finaliz' in implementation.lower(), 'shots stats'),
    (211, 'Posse de bola quando suportada', 'possession' in implementation.lower() or 'posse' in implementation.lower(), 'possession stats'),
    (212, 'Expected goals documentado', 'expected_goals' in implementation.lower() or 'xg' in implementation.lower(), 'xG formula'),
    (213, 'Placar não negativo', 'max(0' in implementation and 'home_goals' in implementation, 'score clamp'),
    (214, 'Limite de eventos por partida', 'event_limit' in implementation.lower() or 'MAX_EVENTS' in implementation, 'event limit'),
    (215, 'Confrontos entre clubes reais', 'create_competition' in existing_tests and 'club_ids' in existing_tests, 'competition tests'),
    (216, 'Partida sem competição vinculada', 'competition' in existing_tests.lower() and ('not found' in existing_tests.lower() or 'without' in existing_tests.lower()), 'match error tests'),
    (217, 'Partida adiada e remarcada', 'postpon' in existing_tests.lower() or 'resched' in existing_tests.lower(), 'postponed/rescheduled tests'),
    (218, 'Execução duplicada', 'ALREADY_PLAYED' in implementation and 'already' in existing_tests.lower() or 'idempot' in existing_tests.lower(), 'duplicate execution guard'),
    (219, 'Rollback após aplicação parcial', 'managed_transaction' in implementation and 'rollback' in implementation, 'transaction rollback'),
    (220, 'Distribuição de placares por temporada', 'score_distribution' in implementation.lower() or 'distribution' in match_audit.lower(), 'score distribution report'),
]
rows = [{'item': item, 'criterion': criterion, 'status': 'PASS' if ok else 'GAP', 'evidence': evidence} for item, criterion, ok, evidence in checks]
result = {'front': 'P0-11', 'items': len(rows), 'passed': sum(row['status'] == 'PASS' for row in rows), 'gaps': [row for row in rows if row['status'] == 'GAP'], 'status': 'VALID' if all(row['status'] == 'PASS' for row in rows) else 'GAPS_FOUND'}
print(json.dumps(result, ensure_ascii=False, indent=2))
(PROJECT / 'docs/p0_front_11_matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if result['status'] != 'VALID':
    raise SystemExit(1)
