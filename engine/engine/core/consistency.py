from __future__ import annotations
from dataclasses import dataclass,asdict
import sqlite3,json
@dataclass(frozen=True)
class BalanceConfig:
 home_advantage:float=.08; form_weight:float=.15; condition_weight:float=.10; fatigue_weight:float=.08; staff_weight:float=.05; structure_weight:float=.03; goal_rate:float=1.8; injury_risk:float=.02; max_reputation_change:float=5.0
@dataclass(frozen=True)
class ConsistencyReport:
 integrity:str;foreign_keys:int;duplicate_players:int;duplicate_matches:int;financial_anomalies:int;stadium_overcapacity:int;errors:tuple[str,...]
class ConsistencyService:
 def __init__(self,db,balance=None):self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db;self.connection.row_factory=sqlite3.Row;self.balance=balance or BalanceConfig()
 def validate(self):
  errs=[]
  integrity=self.connection.execute('pragma integrity_check').fetchone()[0]; fk=len(self.connection.execute('pragma foreign_key_check').fetchall())
  dup_p=self.connection.execute('select count(*) from (select jogador_id,count(*) c from jogadores group by jogador_id having c>1)').fetchone()[0] if self._has('jogadores') else 0
  dup_m=self.connection.execute('select count(*) from (select match_id,count(*) c from matches group by match_id having c>1)').fetchone()[0] if self._has('matches') else 0
  fin=self.connection.execute("select count(*) from club_economic_state where cash<0 and financial_status not in ('CRITICAL','INSOLVENT','BANKRUPT')").fetchone()[0] if self._has('club_economic_state') else 0
  over=self.connection.execute('select count(*) from club_stadiums where usable_capacity>capacity').fetchone()[0] if self._has('club_stadiums') else 0
  if integrity!='ok' or fk or dup_p or dup_m or fin or over:errs.append('CONSISTENCY_ERROR')
  return ConsistencyReport(integrity,fk,dup_p,dup_m,fin,over,tuple(errs))
 def _has(self,table):return bool(self.connection.execute("select 1 from sqlite_master where type='table' and name=?",(table,)).fetchone())
 def explain(self):return asdict(self.validate())
 def close(self):self.connection.close()
