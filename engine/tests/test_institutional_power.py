from engine.economy.institutional_power import InstitutionalPowerService
from test_staff_market_economy import make_db


def test_institutional_profile_prepares_squad_ct_and_stadium_scores(tmp_path):
    path = make_db(tmp_path)
    service = InstitutionalPowerService(path)
    initial = service.refresh(1)
    assert initial.squad_available is True
    assert initial.ct_available is False
    assert initial.stadium_available is False
    assert initial.overall_score > 0
    assert 1 <= initial.sponsor_stars <= 5

    service.connection.executescript("""
      CREATE TABLE club_stadiums(stadium_id INTEGER PRIMARY KEY,club_id INTEGER,name TEXT,capacity INTEGER,level INTEGER,status TEXT,is_primary INTEGER);
      INSERT INTO club_departments VALUES(1,'medicina',6,0,0,0,0);
      INSERT INTO staff_members(name,role,age,club_id,career_start_age,experience,reputation,level,potential,specialization,salary,status,created_at,retirement_age)
      VALUES('Profissional', 'medico',40,1,30,70,80,7,80,'saúde',0,'ativo','2026-01-01',67);
      INSERT INTO club_stadiums VALUES(1,1,'Arena',64000,5,'OPEN',1);
    """)
    enriched = service.refresh(1)
    assert enriched.ct_available is True and enriched.stadium_available is True
    assert enriched.ct_score > 0 and enriched.stadium_score > 0
    assert enriched.overall_score > initial.overall_score
    assert service.get(1) == enriched
    service.close()
