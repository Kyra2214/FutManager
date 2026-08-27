import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from engine.core.payload_contract import MAX_PAYLOAD_BYTES, payload_fingerprint, validate_payload


def test_payload_contract_normalizes_and_fingerprints_deterministically():
    left = validate_payload('current', {'z': 1, 'a': {'b': True}})
    right = validate_payload('current', {'a': {'b': True}, 'z': 1})
    assert left == right
    assert payload_fingerprint('current', left) == payload_fingerprint('current', right)


def test_payload_contract_rejects_invalid_shapes_and_size():
    with pytest.raises(ValueError, match='PAYLOAD_ACTION_REQUIRED'):
        validate_payload('', {})
    with pytest.raises(ValueError, match='PAYLOAD_OBJECT_REQUIRED'):
        validate_payload('current', [])
    with pytest.raises(ValueError, match='PAYLOAD_JSON_INVALID'):
        validate_payload('current', {'bad': object()})
    with pytest.raises(ValueError, match='PAYLOAD_TOO_LARGE'):
        validate_payload('current', {'blob': 'x' * (MAX_PAYLOAD_BYTES + 1)})


def test_gateway_emits_payload_fingerprint_and_stable_error(tmp_path):
    source = ROOT / 'data/state/game.db'
    target = tmp_path / 'game.db'
    target.write_bytes(source.read_bytes())
    gateway = ROOT / 'scripts/career_gateway.py'
    ok = subprocess.run([sys.executable, str(gateway), 'current', '--database', str(target)], input=json.dumps({'z': 1}), text=True, capture_output=True, check=True)
    result = json.loads(ok.stdout)
    assert result['ok'] is True
    assert len(result['payload_fingerprint']) == 64
    bad = subprocess.run([sys.executable, str(gateway), 'current', '--database', str(target)], input='[]', text=True, capture_output=True, check=True)
    assert json.loads(bad.stdout) == {'ok': False, 'error': 'PAYLOAD_OBJECT_REQUIRED'}
