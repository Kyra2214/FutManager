from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from datetime import date
import json
import sqlite3
from engine.world.time_and_finance import FinanceLedger, WorldTickContext, LogicalClock
from engine.economy.world_economy import EconomyService

from engine.core.state_store import assert_mutable_state_path
SCHEMA='''
CREATE TABLE IF NOT EXISTS club_finances (club_id INTEGER PRIMARY KEY, cash INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS transfer_windows(window_id INTEGER PRIMARY KEY AUTOINCREMENT,season INTEGER NOT NULL,number INTEGER NOT NULL,start_date TEXT NOT NULL,end_date TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'UPCOMING',rules TEXT NOT NULL DEFAULT '{}',UNIQUE(season,number));
CREATE TABLE IF NOT EXISTS player_market_state(player_id INTEGER PRIMARY KEY,club_id INTEGER,status TEXT NOT NULL DEFAULT 'ACTIVE',market_value INTEGER,asking_price INTEGER,release_clause INTEGER);
CREATE TABLE IF NOT EXISTS transfer_offers(offer_id INTEGER PRIMARY KEY AUTOINCREMENT,player_id INTEGER NOT NULL,buyer_club_id INTEGER NOT NULL,seller_club_id INTEGER NOT NULL,value INTEGER NOT NULL,asking_price INTEGER NOT NULL,window_id INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'PENDING',counter_count INTEGER NOT NULL DEFAULT 0,valid_until TEXT,created_at TEXT NOT NULL,FOREIGN KEY(window_id) REFERENCES transfer_windows(window_id));
CREATE TABLE IF NOT EXISTS transfer_history(transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,offer_id INTEGER NOT NULL UNIQUE,player_id INTEGER NOT NULL,old_club_id INTEGER,new_club_id INTEGER,value INTEGER NOT NULL,season INTEGER,window_id INTEGER,transfer_date TEXT NOT NULL,previous_contract TEXT,new_contract TEXT,source TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS transfer_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT,offer_id INTEGER NOT NULL,event_type TEXT NOT NULL,event_date TEXT NOT NULL,payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS transfer_loans(loan_id INTEGER PRIMARY KEY AUTOINCREMENT,player_id INTEGER NOT NULL,from_club_id INTEGER NOT NULL,to_club_id INTEGER NOT NULL,start_date TEXT NOT NULL,end_date TEXT NOT NULL,loan_fee INTEGER NOT NULL DEFAULT 0,option_fee INTEGER,option_deadline TEXT,status TEXT NOT NULL DEFAULT 'ACTIVE');
CREATE TABLE IF NOT EXISTS transfer_approvals(approval_id INTEGER PRIMARY KEY AUTOINCREMENT,offer_id INTEGER NOT NULL UNIQUE,approved_by TEXT NOT NULL,approved_at TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'APPROVED');
CREATE TABLE IF NOT EXISTS transfer_shortlist(shortlist_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,player_id INTEGER NOT NULL,priority INTEGER NOT NULL DEFAULT 0,notes TEXT NOT NULL DEFAULT '',status TEXT NOT NULL DEFAULT 'ACTIVE',created_at TEXT NOT NULL,UNIQUE(club_id,player_id));
'''
class OfferStatus(StrEnum): PENDING='PENDING'; ACCEPTED='ACCEPTED'; REJECTED='REJECTED'; EXPIRED='EXPIRED'; CANCELLED='CANCELLED'; COMPLETED='COMPLETED'
class NegotiationTemperature(StrEnum): COLD='COLD'; COOL='COOL'; NEUTRAL='NEUTRAL'; WARM='WARM'; HOT='HOT'
@dataclass(frozen=True)
class MarketValue:
    market_value:int
    asking_price:int
class MarketValueService:
    def estimate(self, strength:int|None=None, potential:int|None=None, asking_multiplier:float=1.4)->MarketValue:
        # Política própria e configurável; nunca interpreta cr1, cr2 ou rating_hash.
        base=max(1, int((strength or 40)*1000 + (potential or 0)*500))
        return MarketValue(base, int(base*asking_multiplier))
class TransferMarketService:
    def __init__(self,db):
        assert_mutable_state_path(db) if not isinstance(db,sqlite3.Connection) else None;self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db
        self.connection.row_factory=sqlite3.Row; self.connection.execute('PRAGMA foreign_keys=ON'); self.connection.executescript(SCHEMA)
        EconomyService(self.connection)
        if self.connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='club_finances'").fetchone():
            for legacy in self.connection.execute('SELECT club_id,cash FROM club_finances').fetchall():
                self.connection.execute("INSERT OR IGNORE INTO club_economic_state(club_id,cash,updated_at) VALUES(?,?,date('now'))", (legacy['club_id'], legacy['cash']))
        columns={row[1] for row in self.connection.execute('PRAGMA table_info(transfer_offers)')}
        for name,definition in {'salary':'INTEGER NOT NULL DEFAULT 0','commission':'INTEGER NOT NULL DEFAULT 0','accessory_cost':'INTEGER NOT NULL DEFAULT 0','manager_approved':'INTEGER NOT NULL DEFAULT 1'}.items():
            if name not in columns: self.connection.execute(f'ALTER TABLE transfer_offers ADD COLUMN {name} {definition}')
        self.connection.commit(); LogicalClock(self.connection); self.ledger=FinanceLedger(self.connection)
    def open_window(self,season:int,number:int,start_date:str,end_date:str,rules:dict|None=None)->int:
        cur=self.connection.execute('insert into transfer_windows(season,number,start_date,end_date,status,rules) values(?,?,?,?,?,?)',(season,number,start_date,end_date,'OPEN',json.dumps(rules or {}, ensure_ascii=False, sort_keys=True))); self.connection.commit(); return int(cur.lastrowid)
    def transferable_players(self,seller_club_id:int, age_min=None, age_max=None, position_code=None, min_strength=None, max_budget=None):
        has_players = self.connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='jogadores'").fetchone() is not None
        query = "SELECT market.* FROM player_market_state market WHERE market.club_id=? AND market.status='ACTIVE'"
        args = [seller_club_id]
        if has_players:
            query = "SELECT market.*, players.idade AS age, players.posicao_codigo AS position_code, players.cr1, players.cr2 FROM player_market_state market LEFT JOIN jogadores players ON players.jogador_id=market.player_id WHERE market.club_id=? AND market.status='ACTIVE'"
            if age_min is not None: query += " AND players.idade>=?"; args.append(age_min)
            if age_max is not None: query += " AND players.idade<=?"; args.append(age_max)
            if position_code is not None: query += " AND players.posicao_codigo=?"; args.append(position_code)
            if min_strength is not None: query += " AND ((players.cr1+players.cr2)/2)>=?"; args.append(min_strength)
        if max_budget is not None: query += " AND market.asking_price<=?"; args.append(max_budget)
        return self.connection.execute(query + " ORDER BY market.player_id", args).fetchall()
    def evaluate_player(self, player_id: int, strength: int | None = None, potential: int | None = None, asking_multiplier: float = 1.4) -> dict:
        row = self.connection.execute('SELECT * FROM player_market_state WHERE player_id=?',(int(player_id),)).fetchone()
        if row is None: raise KeyError(player_id)
        value=MarketValueService().estimate(strength, potential, asking_multiplier)
        return {'player_id':int(player_id),'market_value':value.market_value,'asking_price':value.asking_price,'persisted':False,'source':'MarketValueService'}

    def shortlist(self, club_id: int, player_id: int, priority: int = 0, notes: str = '') -> dict:
        if int(priority) < 0: raise ValueError('SHORTLIST_PRIORITY_INVALID')
        self.connection.execute('INSERT OR IGNORE INTO transfer_shortlist(club_id,player_id,priority,notes,created_at) VALUES(?,?,?,?,?)',(int(club_id),int(player_id),int(priority),str(notes),date.today().isoformat()))
        self.connection.execute('UPDATE transfer_shortlist SET priority=?,notes=?,status=\'ACTIVE\' WHERE club_id=? AND player_id=?',(int(priority),str(notes),int(club_id),int(player_id)))
        self.connection.commit()
        return dict(self.connection.execute('SELECT * FROM transfer_shortlist WHERE club_id=? AND player_id=?',(int(club_id),int(player_id))).fetchone())

    def shortlist_audit(self, club_id: int) -> dict:
        rows=[dict(row) for row in self.connection.execute('SELECT * FROM transfer_shortlist WHERE club_id=? AND status=\'ACTIVE\' ORDER BY priority DESC,player_id',(int(club_id),)).fetchall()]
        return {'club_id':int(club_id),'players':rows,'count':len(rows),'persisted':True}

    def approve_offer(self,offer_id:int,approved_by:str='manager'):
        self._offer(offer_id); self.connection.execute('INSERT OR REPLACE INTO transfer_approvals(offer_id,approved_by,approved_at,status) VALUES(?,?,?,?)',(offer_id,approved_by,date.today().isoformat(),'APPROVED')); self.connection.execute('UPDATE transfer_offers SET manager_approved=1 WHERE offer_id=?',(offer_id,)); self._event(offer_id,'TRANSFER_APPROVED',{'approved_by':approved_by}); self.connection.commit()
    def preview_offer(self,buyer_club_id:int,value:int,salary:int=0,commission:int=0,accessory_cost:int=0)->dict:
        if min(value,salary,commission,accessory_cost)<0: raise ValueError('TRANSFER_VALUES_INVALID')
        self._ensure_economic_club(buyer_club_id)
        finance=self.connection.execute('SELECT cash,payroll FROM club_economic_state WHERE club_id=?',(buyer_club_id,)).fetchone()
        profile=self.connection.execute('SELECT weekly_player_payroll,weekly_staff_payroll,weekly_department_maintenance FROM club_payroll_profiles WHERE club_id=?',(buyer_club_id,)).fetchone()
        cash=int(finance['cash']) if finance else 0
        weekly_before=sum(int(profile[key] or 0) for key in ('weekly_player_payroll','weekly_staff_payroll','weekly_department_maintenance')) if profile else 0
        upfront=int(value)+int(commission)+int(accessory_cost)
        return {'buyer_club_id':buyer_club_id,'transfer_value':int(value),'commission':int(commission),'accessory_cost':int(accessory_cost),'upfront_total':upfront,'cash_before':cash,'cash_after':cash-upfront,'weekly_salary_before':weekly_before,'weekly_salary_after':weekly_before+int(salary),'cash_sufficient':cash>=upfront,'formula_version':'transfer-impact-v1'}

    def create_offer(self,player_id:int,buyer_club_id:int,seller_club_id:int,value:int,window_id:int,asking_price:int|None=None,valid_until:str|None=None,salary:int=0,commission:int=0,accessory_cost:int=0,international:bool=False)->int:
        w=self.connection.execute('select * from transfer_windows where window_id=?',(window_id,)).fetchone()
        if not w or w['status']!='OPEN': raise ValueError('TRANSFER_WINDOW_CLOSED')
        if valid_until is not None and valid_until > w['end_date']: raise ValueError('TRANSFER_WINDOW_CLOSED')
        rules=json.loads(w['rules'] or '{}')
        if international and not bool(rules.get('international_registration_open', False)): raise ValueError('INTERNATIONAL_REGISTRATION_CLOSED')
        if buyer_club_id==seller_club_id: raise ValueError('buyer e seller devem ser diferentes')
        current=self.connection.execute('select club_id,status from player_market_state where player_id=?',(player_id,)).fetchone()
        if current and (current['club_id']!=seller_club_id or current['status'] in ('RETIRED','NEGOTIATING')): raise ValueError('TRANSFER_BLOCKED')
        if self.connection.execute("select 1 from sqlite_master where type='table' and name='player_sport_state'").fetchone():
            roster=self.connection.execute("select count(*) from player_sport_state where club_id=?",(buyer_club_id,)).fetchone()[0]
            if roster >= 40: raise ValueError('ROSTER_CAPACITY_REACHED')
        if self.connection.execute("select 1 from sqlite_master where type='table' and name='player_suspensions'").fetchone():
            suspended=self.connection.execute("select 1 from player_suspensions where player_id=? and active=1 and until_date>=date('now')",(player_id,)).fetchone()
            if suspended: raise ValueError('TRANSFER_BLOCKED_SUSPENDED')
        asking=asking_price if asking_price is not None else value
        if min(value, salary, commission, accessory_cost) < 0: raise ValueError('TRANSFER_VALUES_INVALID')
        cur=self.connection.execute('insert into transfer_offers(player_id,buyer_club_id,seller_club_id,value,asking_price,window_id,valid_until,created_at,salary,commission,accessory_cost,manager_approved) values(?,?,?,?,?,?,?,?,?,?,?,0)',(player_id,buyer_club_id,seller_club_id,value,asking,window_id,valid_until,date.today().isoformat(),salary,commission,accessory_cost))
        self.connection.execute('insert or replace into player_market_state(player_id,club_id,status,market_value,asking_price) values(?,?,?,?,?)',(player_id,seller_club_id,'NEGOTIATING',value,asking)); self._event(cur.lastrowid,'TRANSFER_OFFERED',{'value':value}); self.connection.commit(); return int(cur.lastrowid)
    def create_loan(self,player_id:int,from_club_id:int,to_club_id:int,start_date:str,end_date:str,loan_fee:int=0,option_fee:int|None=None,option_deadline:str|None=None)->int:
        if from_club_id==to_club_id or loan_fee<0 or (option_fee is not None and option_fee<0) or start_date>=end_date: raise ValueError('LOAN_INVALID')
        state=self.connection.execute('SELECT club_id,status FROM player_market_state WHERE player_id=?',(player_id,)).fetchone()
        if not state or int(state['club_id'])!=from_club_id or state['status']!='ACTIVE': raise ValueError('LOAN_PLAYER_UNAVAILABLE')
        cur=self.connection.execute('INSERT INTO transfer_loans(player_id,from_club_id,to_club_id,start_date,end_date,loan_fee,option_fee,option_deadline) VALUES(?,?,?,?,?,?,?,?)',(player_id,from_club_id,to_club_id,start_date,end_date,loan_fee,option_fee,option_deadline)); self.connection.commit(); return int(cur.lastrowid)
    def counter(self,offer_id:int,value:int,max_counters:int=1):
        if value < 0:
            raise ValueError('TRANSFER_VALUES_INVALID')
        row=self._offer(offer_id)
        if row['status']!='PENDING': raise ValueError('OFFER_NOT_PENDING')
        if row['counter_count']>=max_counters: raise ValueError('COUNTER_LIMIT_REACHED')
        self.connection.execute('update transfer_offers set value=?,counter_count=counter_count+1 where offer_id=?',(value,offer_id)); self._event(offer_id,'TRANSFER_COUNTERED',{'value':value}); self.connection.commit()
    def accept(self,offer_id:int):
        self._offer(offer_id); self._set_offer(offer_id,'ACCEPTED','TRANSFER_ACCEPTED'); self.approve_offer(offer_id,'manager')
    def expire_offers(self, as_of: str):
        rows = self.connection.execute("SELECT offer_id FROM transfer_offers WHERE status IN ('PENDING','ACCEPTED') AND valid_until IS NOT NULL AND valid_until < ?", (as_of,)).fetchall()
        for row in rows:
            self.connection.execute("UPDATE transfer_offers SET status='EXPIRED' WHERE offer_id=? AND status IN ('PENDING','ACCEPTED')", (row['offer_id'],))
            self._event(row['offer_id'], 'TRANSFER_EXPIRED', {'as_of': as_of})
        self.connection.commit()
        return len(rows)
    def market_audit(self, club_id: int, season: int | None = None) -> dict:
        offers=self.connection.execute('SELECT * FROM transfer_offers WHERE buyer_club_id=? OR seller_club_id=? ORDER BY offer_id',(club_id,club_id)).fetchall()
        loans=self.connection.execute('SELECT * FROM transfer_loans WHERE from_club_id=? OR to_club_id=? ORDER BY loan_id',(club_id,club_id)).fetchall()
        query='SELECT * FROM transfer_history WHERE old_club_id=? OR new_club_id=?'; args=[club_id,club_id]
        if season is not None: query+=' AND season=?'; args.append(season)
        history=self.connection.execute(query+' ORDER BY transfer_id',args).fetchall()
        return {'club_id':int(club_id),'season':season,'offers':[dict(r) for r in offers],'loans':[dict(r) for r in loans],'history':[dict(r) for r in history],'persisted':True}

    def negotiation_history(self, offer_id: int):
        self._offer(offer_id)
        return self.connection.execute("SELECT event_id,offer_id,event_type,event_date,payload FROM transfer_events WHERE offer_id=? ORDER BY event_id", (offer_id,)).fetchall()
    def negotiation_alerts(self, club_id: int):
        return self.connection.execute("SELECT offer.offer_id, offer.player_id, offer.status, offer.valid_until, offer.counter_count FROM transfer_offers offer WHERE (offer.buyer_club_id=? OR offer.seller_club_id=?) AND offer.status IN ('EXPIRED','PENDING') ORDER BY offer.offer_id DESC", (club_id, club_id)).fetchall()
    def reject(self,offer_id:int): self._set_offer(offer_id,'REJECTED','TRANSFER_REJECTED')
    def cancel(self,offer_id:int): self._set_offer(offer_id,'CANCELLED','TRANSFER_CANCELLED')
    def temperature(self,offer_id:int)->NegotiationTemperature:
        r=self._offer(offer_id); ratio=r['value']/max(1,r['asking_price'])
        return NegotiationTemperature.HOT if ratio>=1 else NegotiationTemperature.WARM if ratio>=.85 else NegotiationTemperature.NEUTRAL if ratio>=.65 else NegotiationTemperature.COOL if ratio>=.4 else NegotiationTemperature.COLD
    def complete(self,offer_id:int,context:WorldTickContext,previous_contract=None,new_contract=None):
        con=self.connection
        try:
            con.execute('BEGIN'); row=self._offer(offer_id)
            if row['status']=='COMPLETED': raise ValueError('ALREADY_COMPLETED')
            if row['status']!='ACCEPTED': raise ValueError('OFFER_NOT_ACCEPTED')
            if not row['manager_approved']: raise ValueError('MANAGER_APPROVAL_REQUIRED')
            state=con.execute('select * from player_market_state where player_id=?',(row['player_id'],)).fetchone()
            if not state or state['club_id']!=row['seller_club_id'] or state['status']=='RETIRED': raise ValueError('TRANSFER_BLOCKED')
            self._ensure_economic_club(row['buyer_club_id']); self._ensure_economic_club(row['seller_club_id'])
            buyer=con.execute('select cash from club_economic_state where club_id=?',(row['buyer_club_id'],)).fetchone()
            total_cost=int(row['value'])+int(row['commission'])+int(row['accessory_cost'])
            if not buyer or buyer['cash']<total_cost: raise ValueError('INSUFFICIENT_FUNDS')
            self.ledger.post(context,row['buyer_club_id'],'EXPENSE','TRANSFER_FEE',-total_cost,'transfer',str(offer_id),'Transferência e custos acessórios')
            self.ledger.post(context,row['seller_club_id'],'INCOME','TRANSFER_INCOME',row['value'],'transfer',str(offer_id),'Venda de jogador')
            con.execute('update club_economic_state set cash=cash-?,expense_accumulated=expense_accumulated+?,updated_at=? where club_id=?',(total_cost,total_cost,context.current_date.isoformat(),row['buyer_club_id'])); con.execute('update club_economic_state set cash=cash+?,revenue_accumulated=revenue_accumulated+?,updated_at=? where club_id=?',(int(row['value']),int(row['value']),context.current_date.isoformat(),row['seller_club_id']))
            if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='club_finances'").fetchone():
                con.execute('UPDATE club_finances SET cash=(SELECT cash FROM club_economic_state WHERE club_id=?) WHERE club_id=?',(row['buyer_club_id'],row['buyer_club_id']))
                con.execute('UPDATE club_finances SET cash=(SELECT cash FROM club_economic_state WHERE club_id=?) WHERE club_id=?',(row['seller_club_id'],row['seller_club_id']))
            con.execute('update player_market_state set club_id=?,status=? where player_id=?',(row['buyer_club_id'],'ACTIVE',row['player_id']))
            con.execute('update transfer_offers set status=? where offer_id=?',('COMPLETED',offer_id))
            con.execute('insert into transfer_history(offer_id,player_id,old_club_id,new_club_id,value,season,window_id,transfer_date,previous_contract,new_contract,source) values(?,?,?,?,?,?,?,?,?,?,?)',(offer_id,row['player_id'],row['seller_club_id'],row['buyer_club_id'],row['value'],context.season,row['window_id'],context.current_date.isoformat(),str(previous_contract),str(new_contract),'market'))
            self._event(offer_id,'TRANSFER_COMPLETED',{'new_club_id':row['buyer_club_id']}); con.commit()
        except Exception: con.rollback(); raise
    def _ensure_economic_club(self,club_id:int):
        legacy=self.connection.execute("SELECT cash FROM club_finances WHERE club_id=?",(club_id,)).fetchone() if self.connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='club_finances'").fetchone() else None
        if legacy:
            self.connection.execute("INSERT OR IGNORE INTO club_economic_state(club_id,cash,updated_at) VALUES(?,?,date('now'))",(club_id,int(legacy['cash'])))

    def _offer(self,offer_id):
        row=self.connection.execute('select * from transfer_offers where offer_id=?',(offer_id,)).fetchone()
        if row is None: raise KeyError(offer_id)
        return row
    def _set_offer(self,offer_id,status,event):
        self._offer(offer_id); self.connection.execute('update transfer_offers set status=? where offer_id=?',(status,offer_id)); self._event(offer_id,event,{}); self.connection.commit()
    def _event(self,offer_id,event,payload): self.connection.execute('insert into transfer_events(offer_id,event_type,event_date,payload) values(?,?,?,?)',(offer_id,event,date.today().isoformat(),str(payload)))
    def close(self): self.connection.close()
