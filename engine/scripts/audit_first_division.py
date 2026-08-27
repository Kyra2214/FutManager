import json
import sqlite3
from pathlib import Path
from engine.world.first_division import FIRST_DIVISION_SOURCES, resolve_first_division_members

DB = Path(__file__).resolve().parents[1] / 'data/state/game.db'
connection = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
connection.row_factory = sqlite3.Row
report = [resolve_first_division_members(connection, source.country_id) for source in FIRST_DIVISION_SOURCES]
print(json.dumps(report, ensure_ascii=False, indent=2))
