import csv, sqlite3, unicodedata, re, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=Path('/home/ubuntu/work_modproj/players_complete.csv')
BASE=ROOT/'data/database/game.db'
STATE=ROOT/'data/state/game.db'

def norm(s):
    if not s: return ''
    return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()).strip()
def integer(v):
    try: return int(v)
    except: return None
def key(r):
    nn=norm(r['jogador']) or f'__sem_nome___{r["arquivo_time"]}_{r["categoria"]}'
    vals=(nn,integer(r['pais_id_jogador']),integer(r['idade']),integer(r['posicao_codigo']),integer(r['cr1']),integer(r['cr2']),integer(r['lado']),r['estrela']=='True',r['top_mundial']=='True')
    return '|'.join('' if v is None else str(int(v) if isinstance(v,bool) else v) for v in vals)
shutil.copy2(BASE,STATE)
con=sqlite3.connect(STATE)
con.execute('ALTER TABLE jogadores ADD COLUMN rating_hash INTEGER')
values={}
with RAW.open(encoding='utf-8-sig') as fh:
    for r in csv.DictReader(fh): values.setdefault(key(r),integer(r['hash']))
for ck,h in values.items(): con.execute('UPDATE jogadores SET rating_hash=? WHERE chave_canonica=?',(h,ck))
con.commit(); con.close()
print('state_rating_hash_values',len(values))
