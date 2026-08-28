import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = Path(__file__).resolve().parents[2] / 'frontend' / 'roadmap_gate.json'
STATE = ROOT / 'data' / 'state' / 'game.db'
GATEWAY = ROOT / 'scripts' / 'career_gateway.py'


def invoke_action(state: Path, action: str, payload: dict, gate: Path | None = None) -> dict:
    environment = os.environ.copy()
    environment['PYTHONPATH'] = str(ROOT)
    if gate is not None:
        environment['FUTMANAGER_ROADMAP_GATE_PATH'] = str(gate)
    result = subprocess.run(
        [sys.executable, str(GATEWAY), action, '--database', str(state)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=environment,
        check=True,
    )
    return json.loads(result.stdout)


def invoke(state: Path, gate: Path, priority: str, front: int | None = None) -> dict:
    return invoke_action(state, 'roadmap_guard', {'priority': priority, **({'front': front} if front is not None else {})}, gate)


def test_gateway_serializes_immutable_base_domain_error():
    environment = os.environ.copy()
    environment['PYTHONPATH'] = str(ROOT)
    result = subprocess.run(
        [sys.executable, str(GATEWAY), 'start', '--database', str(ROOT / 'data/database/game.db')],
        input=json.dumps({'manager_name': 'Teste', 'nationality': 'BR', 'age': 30, 'target_type': 'club', 'target_id': 1}),
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=environment,
        check=True,
    )
    assert json.loads(result.stdout) == {'ok': False, 'error': 'IMMUTABLE_BASE_DATABASE'}


def test_front_dependency_is_enforced_by_real_gateway(tmp_path: Path):
    state = tmp_path / 'state.db'
    gate = tmp_path / 'gate.json'
    shutil.copy2(STATE, state)
    shutil.copy2(GATE, gate)
    payload = json.loads(gate.read_text(encoding='utf-8'))
    payload['front_priorities'] = {'1': 'P0', '2': 'P0'}
    payload['front_dependencies'] = {'1': [], '2': [1]}
    payload['front_statuses'] = {'1': 'PENDING', '2': 'PENDING'}
    gate.write_text(json.dumps(payload), encoding='utf-8')
    blocked = invoke(state, gate, 'P0', front=2)
    assert blocked == {'ok': False, 'error': 'FRONT_2_BLOCKED_DEPENDENCIES:1'}
    payload['front_statuses']['1'] = 'CONSOLIDATED'
    gate.write_text(json.dumps(payload), encoding='utf-8')
    released = invoke(state, gate, 'P0', front=2)
    assert released['ok'] is True
    assert released['front'] == 2


def test_p2_is_blocked_and_released_only_after_both_gates_open(tmp_path: Path):
    state = tmp_path / 'state.db'
    gate = tmp_path / 'gate.json'
    shutil.copy2(STATE, state)
    shutil.copy2(GATE, gate)
    payload = json.loads(gate.read_text(encoding='utf-8'))
    payload['p0_gate'] = 'CLOSED'
    payload['p1_gate'] = 'CLOSED'
    gate.write_text(json.dumps(payload), encoding='utf-8')

    blocked = invoke(state, gate, 'P2')
    assert blocked == {'ok': False, 'error': 'P2_BLOCKED_UNTIL_P0_CONSOLIDATED'}

    payload = json.loads(gate.read_text(encoding='utf-8'))
    payload['p0_gate'] = 'OPEN'
    payload['p1_gate'] = 'CLOSED'
    gate.write_text(json.dumps(payload), encoding='utf-8')
    blocked_by_p1 = invoke(state, gate, 'P2')
    assert blocked_by_p1 == {'ok': False, 'error': 'P2_BLOCKED_UNTIL_P1_STABLE'}

    payload['p1_gate'] = 'OPEN'
    gate.write_text(json.dumps(payload), encoding='utf-8')
    released = invoke(state, gate, 'P2')
    assert released['ok'] is True
    assert released['allowed'] is True
    assert released['priority'] == 'P2'


def test_gateway_serializes_mutable_service_domain_error(tmp_path: Path):
    state = tmp_path / 'state.db'
    shutil.copy2(STATE, state)
    started = invoke_action(
        state,
        'start',
        {'manager_name': 'Teste', 'nationality': 'BR', 'age': 30, 'career_name': 'Validação', 'target_type': 'club', 'target_id': 3280},
    )
    assert started['ok'] is True
    result = invoke_action(state, 'ticket_price', {'club_id': 3280, 'base_price': 0})
    assert result == {'ok': False, 'error': 'INVALID_TICKET_PRICE'}
