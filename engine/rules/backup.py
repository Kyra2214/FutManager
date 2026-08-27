from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil


class StateBackupService:
    """Cria snapshots do banco de carreira; nunca usa o banco-base como save."""
    def __init__(self, state_path: str | Path):
        self.state_path = Path(state_path)
        self.backup_dir = self.state_path.parent / "backups"

    def create_backup(self, label: str | None = None) -> Path:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        suffix = label or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destination = self.backup_dir / f"game_{suffix}.db"
        shutil.copy2(self.state_path, destination)
        return destination

    def restore(self, backup_path: str | Path) -> None:
        shutil.copy2(backup_path, self.state_path)
