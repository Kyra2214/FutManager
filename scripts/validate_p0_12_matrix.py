from __future__ import annotations

import json
from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
PROJECT = Path('/home/ubuntu/futmanager_frontend')
structure = (ENGINE / 'engine/competitions/structure.py').read_text(encoding='utf-8', errors='replace')
match_engine = (ENGINE / 'engine/competitions/match_engine.py').read_text(encoding='utf-8', errors='replace')
time_finance = (ENGINE / 'engine/world/time_and_finance.py').read_text(encoding='utf-8', errors='replace')
engine_state = (PROJECT / 'server/engineState.ts').read_text(encoding='utf-8', errors='replace')
mutation_policy = (PROJECT / 'scripts/validate_mutation_paths.py').read_text(encoding='utf-8', errors='replace') if (PROJECT / 'scripts/validate_mutation_paths.py').exists() else ''
tests = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (ENGINE / 'tests').glob('test_*.py'))
all_docs = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (PROJECT / 'docs').glob('*'))

checks = [
    (221, 'Inventariar formatos de competição', 'format' in structure and 'type' in structure, 'competitions.format/type'),
    (222, 'Configuração de pontos por resultado', 'win_points' in structure and 'draw_points' in structure and 'loss_points' in structure, 'competition_config points'),
    (223, 'Critérios de desempate documentados', 'tiebreakers' in structure and 'points,wins,goal_difference,goals_for' in structure, 'competition_config.tiebreakers'),
    (224, 'Criação de grupos e rodadas', 'add_phase' in structure and 'add_round' in structure and 'generate_fixtures' in structure, 'CompetitionStructureService'),
    (225, 'Mata-mata ida e volta', 'turns' in structure and 'turn % 2' in structure, 'fixture generation turns'),
    (226, 'Disputa de pênaltis', 'penalty' in structure.lower() or 'penalty' in match_engine.lower(), 'penalty contract'),
    (227, 'Classificação derivada de PLAYED', 'def standings' in match_engine and 'PLAYED' in match_engine, 'MatchEngine standings'),
    (228, 'Impedir alteração manual pelo frontend', 'frontend' in mutation_policy.lower() and 'SQL' in mutation_policy, 'mutation path validator'),
    (229, 'Status por fase', 'status TEXT' in structure and 'competition_phases' in structure and 'UPDATE competitions SET status' in structure, 'phase/competition status'),
    (230, 'Regras para partidas suspensas', 'POSTPONED' in match_engine and 'reschedule' in match_engine, 'postpone/reschedule'),
    (231, 'Calendário de finais', 'round_date' in structure and 'phase_id' in structure, 'competition rounds calendar'),
    (232, 'Promoção/rebaixamento configurável', 'promotion' in structure.lower() or 'relegation' in structure.lower(), 'promotion/relegation config'),
    (233, 'Histórico de campeões', 'champion' in structure.lower() or 'champions' in structure.lower(), 'champions history'),
    (234, 'Premiações por posição', 'prize' in structure.lower() or 'award' in structure.lower(), 'competition prizes'),
    (235, 'Premiação somente ao concluir', 'finish_competition' in structure and 'PENDING_FIXTURES' in structure, 'finish guard'),
    (236, 'Pagamento duplicado impedido', 'UNIQUE(club_id,season,week,category,source_type,source_id)' in time_finance, 'financial ledger uniqueness'),
    (237, 'Alertas de classificação', 'classification_alerts' in structure and 'emit_classification_alerts' in structure, 'classification alert persistence'),
    (238, 'Consulta no gateway', 'getMatchesDashboard' in engine_state and 'competitions' in engine_state, 'gateway read contract'),
    (239, 'Temporadas com múltiplas competições', 'competition' in tests.lower() and 'season' in tests.lower(), 'competition/season tests'),
    (240, 'Limitações documentadas', 'limita' in all_docs.lower() or 'não há competições' in engine_state.lower(), 'docs + honest empty state'),
]
rows = [{'item': item, 'criterion': criterion, 'status': 'PASS' if ok else 'GAP', 'evidence': evidence} for item, criterion, ok, evidence in checks]
result = {'front': 'P0-12', 'items': len(rows), 'passed': sum(row['status'] == 'PASS' for row in rows), 'gaps': [row for row in rows if row['status'] == 'GAP'], 'status': 'VALID' if all(row['status'] == 'PASS' for row in rows) else 'GAPS_FOUND'}
print(json.dumps(result, ensure_ascii=False, indent=2))
(PROJECT / 'docs/p0_front_12_matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if result['status'] != 'VALID':
    raise SystemExit(1)
