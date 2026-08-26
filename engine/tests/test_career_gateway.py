import json,sqlite3,subprocess,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/database/game.db'
GATEWAY=ROOT/'scripts/career_gateway.py'

def clone(destination):
 source=sqlite3.connect(BASE);target=sqlite3.connect(destination);source.backup(target);source.close();target.close()

def call(database,action,payload):
 result=subprocess.run([sys.executable,str(GATEWAY),action,'--database',str(database)],input=json.dumps(payload),text=True,capture_output=True,check=True)
 return json.loads(result.stdout)

def test_gateway_catalog_start_and_current_career():
 with tempfile.TemporaryDirectory() as directory:
  database=Path(directory)/'state.db';clone(database)
  connection=sqlite3.connect(database)
  connection.executescript("""
   CREATE TABLE asset_catalog(asset_id INTEGER PRIMARY KEY,relative_path TEXT NOT NULL);
   CREATE TABLE team_asset_links(time_id INTEGER PRIMARY KEY,mapping_status TEXT NOT NULL,crest_asset_id INTEGER,crest_mini_asset_id INTEGER);
   CREATE TABLE selection_asset_links(selecao_id INTEGER PRIMARY KEY,crest_status TEXT NOT NULL,crest_asset_id INTEGER,primary_kit_asset_id INTEGER);
   INSERT INTO asset_catalog VALUES(1,'assets/escudos/clubes/07vestur_fro.png');
   INSERT INTO team_asset_links VALUES(1,'COMPLETE',1,NULL);
  """)
  connection.commit();connection.close()
  catalog_result=call(database,'catalog',{'entity_type':'club','search':'07 Vestur'})
  assert catalog_result['ok'] and catalog_result['items'][0]['entityId']==1
  before=call(database,'current',{})
  assert before=={'ok':True,'started':False}
  started=call(database,'start',{'manager_name':'Ana','nationality':'BR','age':31,'career_name':'Carreira Ana','target_type':'club','target_id':1})
  assert started['ok'] and started['target_id']==1
  connection=sqlite3.connect(database)
  economy=connection.execute('SELECT cash,payroll FROM club_economic_state WHERE club_id=1').fetchone()
  profile=connection.execute('SELECT initial_cash,weekly_player_payroll FROM club_payroll_profiles WHERE club_id=1').fetchone()
  offers=connection.execute("SELECT COUNT(*) FROM sponsor_offers offer JOIN sponsor_offer_sets offer_set ON offer_set.offer_set_id=offer.offer_set_id WHERE offer_set.club_id=1 AND offer.status='PENDING'").fetchone()
  connection.close()
  assert economy is not None and profile is not None
  assert profile[0] == profile[1] * 39 and economy[0] == profile[0]
  assert offers[0] == 3
  commercial=call(database,'sponsor_summary',{})
  assert commercial['ok'] and len(commercial['offers']) == 3
  accepted=call(database,'sponsor_accept',{'offer_id':commercial['offers'][0]['offer_id']})
  assert accepted['ok'] and accepted['upfront_payment'] > 0
  after_contract=call(database,'sponsor_summary',{})
  assert after_contract['active_contract'] is not None and after_contract['offers'] == []
  connection=sqlite3.connect(database)
  columns={row[1] for row in connection.execute('PRAGMA table_info(times)')}
  if 'estadio' not in columns:
   connection.execute('ALTER TABLE times ADD COLUMN estadio TEXT')
  connection.execute("UPDATE times SET estadio='Estádio de Teste' WHERE time_id=1")
  connection.commit();connection.close()
  stadium=call(database,'stadium_bootstrap',{})
  assert stadium['ok'] and stadium['name']=='Estádio de Teste' and len(stadium['components'])==4
  upgraded=call(database,'stadium_upgrade',{'component':'arquibancada'})
  assert upgraded['ok'] and upgraded['target_level']==2
  stadium_summary=call(database,'stadium_summary',{})
  assert stadium_summary['ok'] and stadium_summary['initialized'] and stadium_summary['ticket_price']==35
  week=call(database,'weekly_advance',{'seed':17})
  assert week['ok'] and week['status']=='COMPLETED' and week['week']==2
  after=call(database,'current',{})
  assert after['started'] and after['targetType']=='club' and after['targetId']==1
