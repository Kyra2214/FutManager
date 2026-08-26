import sqlite3
from pathlib import Path

path = Path('/home/ubuntu/brasfoot_engine/data/database/game.db')
connection = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
for table in ('jogadores', 'times', 'selecoes'):
    print(table, [row[1] for row in connection.execute(f'PRAGMA table_info({table})')])
connection.close()
