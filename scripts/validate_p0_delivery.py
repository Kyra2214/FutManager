from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path('/home/ubuntu')
PROJECT = ROOT / 'futmanager_frontend'
ZIP = ROOT / 'FutManager_Brasfoot_ENTREGA_2026-08-26.zip'
ZIP_HASH = ROOT / 'FutManager_Brasfoot_ENTREGA_2026-08-26.zip.sha256'
required_project_docs = [
    PROJECT / 'roadmap_500_proximos_passos.md',
    PROJECT / 'roadmap_gate.json',
    PROJECT / 'docs/roadmap_execution_policy.md',
    PROJECT / 'docs/p0_validation_evidence_2026-08-26.md',
]
required_external = [
    ROOT / 'brasfoot_engine/data/database/manifest.json',
    ROOT / 'brasfoot_engine/data/database/game.db.sha256',
    ROOT / 'brasfoot_engine/data/state/game.db.sha256',
    ROOT / 'brasfoot_engine/assets/asset_manifest.json',
]
missing = [str(p) for p in required_project_docs + required_external if not p.exists()]
hash_ok = False
if ZIP.exists() and ZIP_HASH.exists():
    expected = ZIP_HASH.read_text(encoding='utf-8').split()[0]
    hash_ok = hashlib.sha256(ZIP.read_bytes()).hexdigest() == expected
manifest_ok = True
for path in required_external:
    if path.suffix == '.json':
        try:
            json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            manifest_ok = False
result = {
    'front': 'P0-25',
    'zip_exists': ZIP.exists(),
    'zip_sha256_matches': hash_ok,
    'required_files_missing': missing,
    'json_manifests_parse': manifest_ok,
    'status': 'VALID' if ZIP.exists() and hash_ok and not missing and manifest_ok else 'GAPS_FOUND',
}
print(result)
if result['status'] != 'VALID':
    raise SystemExit(1)
