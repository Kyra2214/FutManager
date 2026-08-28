import hashlib
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_delivery.py"
BASE = ROOT / "data" / "database" / "game.db"
STATE = ROOT / "data" / "state" / "game.db"


def test_base_manifest_accepts_canonical_copy_and_rejects_tampering(tmp_path: Path):
    base_copy = tmp_path / "game.db"
    archive_copy = tmp_path / "game.db.gz"
    manifest = tmp_path / "game.db.sha256"
    shutil.copy2(BASE, base_copy)
    shutil.copy2(BASE.with_suffix(BASE.suffix + ".gz"), archive_copy)
    manifest.write_text(hashlib.sha256(archive_copy.read_bytes()).hexdigest() + "  game.db.gz\n", encoding="utf-8")

    accepted = subprocess.run(
        [sys.executable, str(VALIDATOR), "--base", str(base_copy), "--state", str(STATE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert accepted.returncode == 0, accepted.stderr

    with archive_copy.open("ab") as handle:
        handle.write(b"\x01")
    rejected = subprocess.run(
        [sys.executable, str(VALIDATOR), "--base", str(base_copy), "--state", str(STATE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert rejected.returncode != 0


def test_state_is_mutable_and_not_required_to_match_stale_manifest():
    with sqlite3.connect(STATE) as connection:
        result = connection.execute("PRAGMA integrity_check").fetchone()[0]
    assert result == "ok"
