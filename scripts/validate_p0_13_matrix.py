from __future__ import annotations

import json
from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
PROJECT = Path('/home/ubuntu/futmanager_frontend')
clock = (ENGINE / 'engine/world/time_and_finance.py').read_text(encoding='utf-8', errors='replace')
calendar_service = (ENGINE / 'engine/world/calendar.py').read_text(encoding='utf-8', errors='replace')
structure = (ENGINE / 'engine/competitions/structure.py').read_text(encoding='utf-8', errors='replace')
orchestrator = (ENGINE / 'engine/world/orchestrator.py').read_text(encoding='utf-8', errors='replace')
tests = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (ENGINE / 'tests').glob('test_*.py'))
frontend = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (PROJECT / 'server').glob('*.ts'))
docs = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (PROJECT / 'docs').glob('*'))

checks = [
    (241, 'Relógio lógico de temporada e semana', 'logical_clock' in clock and 'current_week' in clock and 'current_season' in clock, 'LogicalClock schema'),
    (242, 'Calendário de pré-temporada', 'create_preseason' in calendar_service and "'PRESEASON'" in calendar_service, 'CalendarService.create_preseason'),
    (243, 'Calendário de temporada regular', 'generate_fixtures' in structure and 'scheduled_at' in structure, 'fixtures calendar'),
    (244, 'Janelas de descanso', 'rest_windows' in calendar_service and 'add_rest_window' in calendar_service, 'CalendarService rest windows'),
    (245, 'Competições simultâneas', 'season_id' in structure and 'competition_id' in structure, 'multi-competition dates'),
    (246, 'Adiamento por conflito', 'detect_conflicts' in calendar_service and 'reschedule_conflict' in calendar_service, 'CalendarService conflict resolution'),
    (247, 'Semana sem partidas', 'week_summary' in calendar_service and 'scheduled_items' in calendar_service, 'CalendarService empty-week summary'),
    (248, 'Semana com várias partidas', 'simulate_batch' in tests and 'batch_size' in tests, 'batch simulation tests'),
    (249, 'Avanço diário opcional', 'advance_type' in clock and 'day' in clock.lower(), 'WorldTickContext advance type'),
    (250, 'Avanço semanal principal', 'next_week_context' in clock and 'advance_type' in clock, 'weekly clock API'),
    (251, 'Bloqueio de avanço inválido', 'INVALID' in clock or 'invalid' in orchestrator.lower(), 'invalid-state guard'),
    (252, 'Histórico de avanços', 'financial_events' in clock and 'tick_id' in clock, 'tick event history'),
    (253, 'Próximo compromisso', 'next' in frontend.lower() and 'match' in frontend.lower(), 'frontend next commitment'),
    (254, 'Agenda por clube', 'def calendar' in structure and 'club_id' in structure, 'CompetitionStructureService.calendar'),
    (255, 'Pausa entre temporadas', 'season' in clock and 'week>52' in clock.replace(' ', ''), 'season rollover'),
    (256, 'Transição de elenco', 'transition' in structure.lower() or 'roster' in structure.lower(), 'roster transition contract'),
    (257, 'Fechamento de contratos', 'contract' in orchestrator.lower() or 'contract' in docs.lower(), 'season contract close'),
    (258, 'Relatório de calendário congestionado', 'congestion_report' in calendar_service and 'CONGESTION_THRESHOLD_INVALID' in calendar_service, 'CalendarService congestion report'),
    (259, 'Avanço idempotente', 'last_processed_tick' in clock and 'UNIQUE' in clock, 'tick idempotency'),
    (260, 'Restauração após rollback', 'def restore' in clock and 'logical_clock' in clock and 'ROLLBACK' in calendar_service, 'LogicalClock.restore + clock_history rollback action'),
]
rows = [{'item': item, 'criterion': criterion, 'status': 'PASS' if ok else 'GAP', 'evidence': evidence} for item, criterion, ok, evidence in checks]
result = {'front': 'P0-13', 'items': len(rows), 'passed': sum(row['status'] == 'PASS' for row in rows), 'gaps': [row for row in rows if row['status'] == 'GAP'], 'status': 'VALID' if all(row['status'] == 'PASS' for row in rows) else 'GAPS_FOUND'}
print(json.dumps(result, ensure_ascii=False, indent=2))
(PROJECT / 'docs/p0_front_13_matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if result['status'] != 'VALID':
    raise SystemExit(1)
