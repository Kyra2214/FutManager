from __future__ import annotations

import json
from pathlib import Path

ROOT = Path('/home/ubuntu/futmanager_frontend')
manifest_path = ROOT / 'docs' / 'shared_gateway_contracts.json'
policy_path = ROOT / 'docs' / 'plugin_extension_policy.md'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
policy = policy_path.read_text(encoding='utf-8')

required = {
    'version', 'source_of_truth', 'transport', 'read_contracts',
    'command_contracts', 'serialization', 'rules'
}
missing = sorted(required - set(manifest))
assert not missing, f'MANIFEST_KEYS_MISSING:{missing}'
assert manifest['source_of_truth'] == 'SQL/GameState'
assert manifest['serialization']['encoding'] == 'UTF-8 JSON'
assert manifest['serialization']['errors'].startswith('DomainErrorCode')
assert manifest['read_contracts'] and manifest['command_contracts']
assert all(isinstance(item, str) and item for item in manifest['read_contracts'] + manifest['command_contracts'])
for forbidden in ('React may not write SQLite', 'Domain rules remain in Python services', 'New commands require a service method'):
    assert any(forbidden in rule for rule in manifest['rules']), f'MANIFEST_RULE_MISSING:{forbidden}'
for required_phrase in ('SQLite/GameState', 'banco-base', 'RoadmapGate', 'managed_transaction'):
    assert required_phrase in policy, f'PLUGIN_POLICY_MISSING:{required_phrase}'

print({
    'manifest': str(manifest_path),
    'read_contracts': len(manifest['read_contracts']),
    'command_contracts': len(manifest['command_contracts']),
    'status': 'VALID',
})
