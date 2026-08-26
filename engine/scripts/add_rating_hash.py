import csv
import sqlite3
import unicodedata
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=Path('/home/ubuntu/work_modproj/players_complete.csv')
DB=ROOT/'data/database/game.db'

def norm(s):
    if s is None: return ''
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+',' ',s).strip()

def integer(v):
    try: return int(v)
    except: return None

def key(r):
    name=r['jogador'] if r['jogador'] else None
    nn=norm(name) or f'__sem_nome___{r["arquivo_time"]}_{r["categoria"]}'
    vals=(nn,integer(r['pais_id_jogador']),integer(r['idade']),integer(r['posicao_codigo']),integer(r['cr1']),integer(r['cr2']),integer(r['lado']),r['estrela']=='True',r['top_mundial']=='True')
    return '|'.join('' if v is None else str(int(v) if isinstance(v,bool) else v) for v in vals)

con=sqlite3.connect(DB)
cols={r[1] for r in con.execute('pragma table_info(jogadores)')}
if 'rating_hash' not in cols: con.execute('alter table jogadores add column rating_hash integer')
values={}
with RAW.open(encoding='utf-8-sig') as fh:
    for r in csv.DictReader(fh):
        values.setdefault(key(r),integer(r['hash']))
for ck,h in values.items():
    con.execute('update jogadores set rating_hash=? where chave_canonica=?',(h,ck))
con.commit(); con.close()
# copy to career state only after base migration is complete
import shutil
shutil.copy2(DB,ROOT/'data/state/game.db')
print('rating_hash_values',len(values))
