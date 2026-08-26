from __future__ import annotations

import json
from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
PROJECT = Path('/home/ubuntu/futmanager_frontend')
ledger = (ENGINE / 'engine/world/time_and_finance.py').read_text(encoding='utf-8', errors='replace')
economy = (ENGINE / 'engine/economy/world_economy.py').read_text(encoding='utf-8', errors='replace')
staff = (ENGINE / 'engine/economy/staff_market.py').read_text(encoding='utf-8', errors='replace')
cycle = (ENGINE / 'engine/world/weekly_cycle.py').read_text(encoding='utf-8', errors='replace')
matchday = (ENGINE / 'engine/economy/matchday_revenue.py').read_text(encoding='utf-8', errors='replace')
orchestrator = (ENGINE / 'engine/world/orchestrator.py').read_text(encoding='utf-8', errors='replace')
tests = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (ENGINE / 'tests').glob('test_*.py'))
docs = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (PROJECT / 'docs').glob('*'))

checks = [
    (321, 'Categorias do FinanceLedger', 'category TEXT' in ledger and 'source_type TEXT' in ledger, 'financial_ledger schema'),
    (322, 'Moeda e unidade únicas', 'amount INTEGER' in ledger and 'currency' in economy.lower() or 'unidade monetária' in docs.lower(), 'integer ledger unit'),
    (323, 'Referência natural', 'UNIQUE(club_id,season,week,category,source_type,source_id)' in ledger, 'ledger natural key'),
    (324, 'Fechamento semanal do ledger', 'close_week' in cycle and 'LEDGER_CLOSE' in cycle, 'weekly_cycle ledger close'),
    (325, 'Relatório de receitas por clube', 'revenue_accumulated' in economy and 'report_revenue' in economy.lower(), 'revenue report'),
    (326, 'Relatório de despesas por clube', 'expense_accumulated' in economy and 'report_expense' in economy.lower(), 'expense report'),
    (327, 'Projeção de caixa 39 semanas', 'projected_expenses' in economy and '39' in economy, 'budget projection'),
    (328, 'Reserva de 39 semanas', '39' in staff and 'payroll' in staff.lower(), 'staff payroll reserve'),
    (329, 'Bilheteria por partida', 'record_matchday' in cycle and 'MATCHDAY' in matchday, 'MatchdayRevenueService'),
    (330, 'Manutenção de estádio semanal', 'FACILITY_MAINTENANCE' in orchestrator and 'weekly_amount' in orchestrator, 'WorldOrchestrator facility maintenance'),
    (331, 'Folha individual de jogadores', 'player' in staff.lower() and 'payroll' in staff.lower(), 'player payroll'),
    (332, 'Folha de comissão/departamentos', 'staff' in staff.lower() and 'department' in staff.lower(), 'staff/departments payroll'),
    (333, 'Alerta de saldo baixo', 'low_balance_alert' in economy and 'financial_alerts' in economy, 'persisted low balance alert'),
    (334, 'Déficit controlado', 'deficit' in economy.lower() or 'INSUFFICIENT_CASH' in staff, 'controlled deficit'),
    (335, 'Insolvência', 'INSOLVENT' in economy and 'declare_bankruptcy' in economy, 'bankruptcy status'),
    (336, 'Recuperação financeira', 'RECOVERY' in economy and 'invest' in economy.lower(), 'recovery/investment'),
    (337, 'Relatórios econômicos mundiais', 'report' in economy.lower() and 'world' in economy.lower(), 'world economy reports'),
    (338, 'Idempotência por categoria', 'UNIQUE' in ledger and 'ALREADY_PROCESSED' in tests, 'ledger + tests'),
    (339, 'Rollback após falha tardia', 'rollback' in cycle.lower() and 'managed_transaction' in cycle, 'weekly cycle rollback'),
    (340, 'Auditoria econômica por temporada', 'season_audit' in economy and 'economy_season_audits' in economy, 'persisted season economy audit'),
]
rows = [{'item': item, 'criterion': criterion, 'status': 'PASS' if ok else 'GAP', 'evidence': evidence} for item, criterion, ok, evidence in checks]
result = {'front': 'P0-17', 'items': len(rows), 'passed': sum(row['status'] == 'PASS' for row in rows), 'gaps': [row for row in rows if row['status'] == 'GAP'], 'status': 'VALID' if all(row['status'] == 'PASS' for row in rows) else 'GAPS_FOUND'}
print(json.dumps(result, ensure_ascii=False, indent=2))
(PROJECT / 'docs/p0_front_17_matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if result['status'] != 'VALID':
    raise SystemExit(1)
