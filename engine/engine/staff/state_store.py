from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import json
import sqlite3
from datetime import date
from random import Random

from engine.staff.domain import StaffMember, StaffRole, StaffStatus, ClubDepartment

from engine.core.state_store import assert_mutable_state_path
SCHEMA = """
CREATE TABLE IF NOT EXISTS staff_members (
 staff_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, role TEXT NOT NULL,
 age INTEGER NOT NULL, club_id INTEGER, career_start_age INTEGER, experience INTEGER NOT NULL DEFAULT 0,
 reputation INTEGER NOT NULL DEFAULT 1, level INTEGER NOT NULL DEFAULT 1, potential INTEGER NOT NULL,
 specialization TEXT, salary INTEGER NOT NULL DEFAULT 0, contract_id INTEGER, status TEXT NOT NULL,
 created_at TEXT NOT NULL, retirement_age INTEGER, FOREIGN KEY(club_id) REFERENCES times(time_id)
);
CREATE TABLE IF NOT EXISTS staff_history (
 history_id INTEGER PRIMARY KEY AUTOINCREMENT, staff_id INTEGER NOT NULL, event_type TEXT NOT NULL,
 event_date TEXT NOT NULL, payload TEXT NOT NULL, FOREIGN KEY(staff_id) REFERENCES staff_members(staff_id)
);
CREATE TABLE IF NOT EXISTS club_departments (
 club_id INTEGER NOT NULL, department TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 1,
 cost INTEGER NOT NULL DEFAULT 0, capacity INTEGER NOT NULL DEFAULT 0,
 maintenance INTEGER NOT NULL DEFAULT 0, efficiency REAL NOT NULL DEFAULT 0,
 PRIMARY KEY(club_id,department), FOREIGN KEY(club_id) REFERENCES times(time_id)
);
"""

class StaffStateStore:
    def __init__(self, state_db: str | Path):
        assert_mutable_state_path(state_db);self.connection=sqlite3.connect(state_db)
        self.connection.row_factory=sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.executescript(SCHEMA); self.connection.commit()

    @contextmanager
    def transaction(self):
        try:
            self.connection.execute('BEGIN'); yield self.connection; self.connection.commit()
        except Exception:
            self.connection.rollback(); raise

    def create_staff(self, name: str, role: StaffRole, age: int, club_id: int|None=None, seed: int|None=None, salary: int=0) -> int:
        rng=Random(seed); potential=rng.randint(30,99)
        with self.transaction() as con:
            cur=con.execute('''INSERT INTO staff_members(name,role,age,club_id,career_start_age,experience,reputation,level,potential,salary,status,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',(name,role.value,age,club_id,age,0,1,1,potential,salary,StaffStatus.ACTIVE.value,date.today().isoformat()))
            sid=int(cur.lastrowid)
            self.add_history(sid,'STAFF_CREATED',{'role':role.value,'seed':seed},con)
            return sid

    def add_experience(self, staff_id:int, amount:int, reason:str):
        with self.transaction() as con:
            row=con.execute('SELECT * FROM staff_members WHERE staff_id=?',(staff_id,)).fetchone()
            if row is None: raise KeyError(staff_id)
            experience=max(0,min(100,row['experience']+amount))
            level=max(1,min(10,1+experience//15))
            con.execute('UPDATE staff_members SET experience=?,level=? WHERE staff_id=?',(experience,level,staff_id))
            self.add_history(staff_id,'STAFF_EXPERIENCE',{'amount':amount,'reason':reason},con)

    def transfer(self, staff_id:int, new_club_id:int|None):
        with self.transaction() as con:
            if con.execute('SELECT 1 FROM staff_members WHERE staff_id=?',(staff_id,)).fetchone() is None: raise KeyError(staff_id)
            con.execute('UPDATE staff_members SET club_id=?,status=? WHERE staff_id=?',(new_club_id,StaffStatus.ACTIVE.value,staff_id))
            self.add_history(staff_id,'STAFF_TRANSFERRED',{'club_id':new_club_id},con)

    def retire(self, staff_id:int):
        with self.transaction() as con:
            con.execute('UPDATE staff_members SET club_id=NULL,status=? WHERE staff_id=?',(StaffStatus.RETIRED.value,staff_id))
            self.add_history(staff_id,'STAFF_RETIRED',{},con)

    def active_staff(self, club_id:int, role:str|None=None):
        query='SELECT * FROM staff_members WHERE club_id=? AND status=?'; args=[int(club_id), StaffStatus.ACTIVE.value]
        if role is not None: query+=' AND role=?'; args.append(role.value if hasattr(role,'value') else str(role))
        query+=' ORDER BY role,level DESC,reputation DESC,staff_id'
        return [dict(row) for row in self.connection.execute(query,args).fetchall()]

    def staff_summary(self, club_id:int):
        members=self.active_staff(club_id)
        counts={}
        for member in members: counts[member['role']]=counts.get(member['role'],0)+1
        return {'club_id':int(club_id),'total':len(members),'by_role':counts,'average_level':round(sum(member['level'] for member in members)/len(members),2) if members else 0.0,'members':members}

    def departments(self, club_id:int):
        return [dict(row) for row in self.connection.execute('SELECT * FROM club_departments WHERE club_id=? ORDER BY department',(int(club_id),)).fetchall()]

    def domain_effects(self, club_id:int):
        mapping={'treinador':'TACTICS','auxiliar':'TRANSITION','preparador_fisico':'PHYSICAL','medico':'HEALTH','scout':'SCOUTING'}
        effects={key:{'effect':value,'members':0,'average_level':0.0,'bonus':0.0} for key,value in mapping.items()}
        for role, count, level in self.connection.execute("SELECT role,COUNT(*) AS members,AVG(level) AS average_level FROM staff_members WHERE club_id=? AND status='ativo' GROUP BY role",(int(club_id),)).fetchall():
            key=str(role)
            if key in effects:
                effects[key]['members']=int(count); effects[key]['average_level']=round(float(level or 0),2); effects[key]['bonus']=round(min(0.25,float(level or 0)*0.025),4)
        return effects

    def department_capacity(self, club_id:int):
        role_by_department={'medicina':'medico','preparacao_fisica':'preparador_fisico','analise':'auxiliar','base':'scout'}
        active=self.staff_summary(club_id)['by_role']; result=[]
        for row in self.departments(club_id):
            role=role_by_department.get(row['department']); used=int(active.get(role,0)) if role else 0; capacity=int(row['capacity'])
            result.append({'department':row['department'],'capacity':capacity,'used':used,'vacancies':max(0,capacity-used),'role':role})
        return result

    def commission_bonus(self, club_id:int):
        effects=self.domain_effects(club_id)
        total=sum(value['bonus'] for value in effects.values())
        return {'club_id':int(club_id),'bonus':round(min(1.0,total),4),'by_role':effects}

    def specialists(self, club_id:int, role:str):
        if role not in {'medico','auxiliar'}: raise ValueError('SPECIALIZATION_ROLE_INVALID')
        return [member for member in self.active_staff(club_id,role) if member.get('specialization')]

    def staff_history(self, club_id:int, staff_id:int|None=None):
        query='SELECT h.* FROM staff_history h JOIN staff_members s ON s.staff_id=h.staff_id WHERE s.club_id=?'; args=[int(club_id)]
        if staff_id is not None: query+=' AND h.staff_id=?'; args.append(int(staff_id))
        query+=' ORDER BY h.history_id'
        return [dict(row, payload=json.loads(row['payload'])) for row in self.connection.execute(query,args).fetchall()]

    def set_department(self, club_id:int, department:str, level:int=1, cost:int=0, capacity:int=0, maintenance:int=0, efficiency:float=0.0):
        if not 1<=level<=10: raise ValueError('nível deve estar entre 1 e 10')
        with self.transaction() as con:
            con.execute('''INSERT INTO club_departments(club_id,department,level,cost,capacity,maintenance,efficiency)
                VALUES (?,?,?,?,?,?,?) ON CONFLICT(club_id,department) DO UPDATE SET level=excluded.level,cost=excluded.cost,capacity=excluded.capacity,maintenance=excluded.maintenance,efficiency=excluded.efficiency''',(club_id,department,level,cost,capacity,maintenance,efficiency))

    def add_history(self, staff_id:int, event_type:str, payload:dict, con=None):
        target=con or self.connection
        target.execute('INSERT INTO staff_history(staff_id,event_type,event_date,payload) VALUES (?,?,?,?)',(staff_id,event_type,date.today().isoformat(),json.dumps(payload,ensure_ascii=False,sort_keys=True)))

    def close(self): self.connection.close()
