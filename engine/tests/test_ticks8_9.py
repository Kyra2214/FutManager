from pathlib import Path
import sqlite3,sys,tempfile
from datetime import date
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.sports.cycle import SportStateStore,SquadCategory,TrainingType
from engine.competitions.match_engine import CompetitionService
BASE=ROOT/'data/database/game.db'
def clone(p):
 a=sqlite3.connect(BASE);b=sqlite3.connect(p);a.backup(b);a.close();b.close()

def test_squad_training_injury_recovery_lineup():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p);s=SportStateStore(p)
  for pid in (1,2,3):s.ensure_player(pid,1,SquadCategory.YOUTH)
  s.promote(1);s.promote(2);s.train(1,TrainingType.PHYSICAL,20,seed=1); assert s.squad(1,SquadCategory.RESERVE)
  s.injure(1,days=3);assert not s.is_available(1);s.recover(1,3);assert s.is_available(1)
  lineup=s.create_lineup(1,'4-3-3',[1,2]);assert s.team_strength(lineup.lineup_id)>0;s.close()

def test_competition_fixture_match_standings_and_replay():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p);c=CompetitionService(p);season=c.create_season(2026);comp=c.create_competition('Liga Teste',season,[1,2]);matches=c.generate_fixtures(comp);assert len(matches)==1
  r=c.play(matches[0],80,60,seed=4);assert r.match_id==matches[0]
  st=c.standings(comp);assert sum(x['played'] for x in st)==2
  try:c.play(matches[0],80,60,seed=4)
  except ValueError as e:assert str(e)=='ALREADY_PLAYED'
  else:raise AssertionError('replay aceito')
  c.close()

def test_match_replay_deterministic():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p);c=CompetitionService(p);season=c.create_season(2026);comp=c.create_competition('Liga',season,[1,2,3]);ids=c.generate_fixtures(comp);a=c.play(ids[0],70,70,seed=9);assert a.home_goals==c.connection.execute('select home_goals from matches where match_id=?',(ids[0],)).fetchone()[0];c.close()

def test_squad_summary_and_minimum_lineup_validation():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'summary.db';clone(p);s=SportStateStore(p)
  for pid in range(1,13):
   s.ensure_player(pid,1,SquadCategory.FIRST_TEAM if pid <= 8 else SquadCategory.RESERVE)
  summary=s.squad_summary(1)
  assert summary == {'club_id': 1, 'total': 12, 'starters': 8, 'reserves': 4, 'unavailable': 0, 'available': 12}
  assert s.validate_minimum_lineup(1)['valid'] is True
  s.injure(1,days=3)
  try:
   s.validate_minimum_lineup(1, minimum=12)
  except ValueError as error:
   assert str(error) == 'INSUFFICIENT_AVAILABLE_PLAYERS:11:12'
  else:
   raise AssertionError('escalação mínima inválida foi aceita')
  s.close()

def test_saved_formation_is_scoped_to_competition_and_match_lineup_is_validated():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'saved.db';clone(p);s=SportStateStore(p)
  for pid in range(1,13):
   s.ensure_player(pid,1,SquadCategory.FIRST_TEAM if pid <= 11 else SquadCategory.RESERVE)
  saved=s.save_formation(1, 42, 'Principal', '4-3-3', range(1,12))
  assert saved['competition_id'] == 42 and len(saved['player_ids']) == 11
  assert s.saved_formations(1,42)[0]['name'] == 'Principal'
  lineup=s.create_match_lineup(1,42,'Principal')
  assert lineup.formation == '4-3-3' and len(lineup.player_ids) == 11
  assert s.saved_formations(1,43) == []
  s.close()

def test_automatic_lineup_prioritizes_positions_and_is_deterministic():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'auto.db';clone(p);s=SportStateStore(p)
  for pid in range(1,13):
   s.ensure_player(pid,1,SquadCategory.FIRST_TEAM,position_code=pid if pid <= 11 else 3)
  lineup=s.auto_lineup(1,'4-3-3')
  assert lineup.player_ids == tuple(range(1,12))
  assert len(set(lineup.player_ids)) == 11
  s.close()

def test_planned_substitution_is_persisted_and_idempotent():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'subs.db';clone(p);s=SportStateStore(p)
  for pid in range(1,13): s.ensure_player(pid,1,SquadCategory.FIRST_TEAM)
  lineup=s.create_lineup(1,'4-3-3',range(1,12))
  first=s.plan_substitution(lineup.lineup_id,60,1,12)
  second=s.plan_substitution(lineup.lineup_id,60,1,12)
  assert first['plan_id'] == second['plan_id']
  assert len(s.planned_substitutions(lineup.lineup_id)) == 1
  try: s.plan_substitution(lineup.lineup_id,60,99,12)
  except ValueError as error: assert str(error) == 'OUTGOING_PLAYER_NOT_IN_LINEUP'
  else: raise AssertionError('jogador de saída inválido foi aceito')
  s.close()

def test_player_match_stats_are_upserted_idempotently():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'stats.db';clone(p);s=SportStateStore(p)
  s.ensure_player(7,1,SquadCategory.FIRST_TEAM)
  first=s.record_player_match_stats(88,7,90,2,1,1,8.5)
  second=s.record_player_match_stats(88,7,75,1,0,0,7.5)
  assert first['minutes'] == 90 and second['minutes'] == 75
  assert s.player_match_stats(88) == [second]
  try: s.record_player_match_stats(88,7,121)
  except ValueError as error: assert str(error) == 'INVALID_PLAYER_MATCH_STATS'
  else: raise AssertionError('minutos inválidos foram aceitos')
  s.close()

def test_substitution_application_updates_effective_lineup_once():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'apply-sub.db';clone(p);s=SportStateStore(p)
  for pid in range(1,13): s.ensure_player(pid,1,SquadCategory.FIRST_TEAM)
  lineup=s.create_lineup(1,'4-3-3',range(1,12))
  plan=s.plan_substitution(lineup.lineup_id,60,1,12)
  s.record_player_match_stats(88,1,90)
  applied=s.apply_substitution(plan['plan_id'],65,match_id=88)
  reapplied=s.apply_substitution(plan['plan_id'],70,match_id=88)
  assert applied['status'] == 'APPLIED' and applied['applied_minute'] == 65
  assert reapplied['plan_id'] == applied['plan_id']
  stats={row['player_id']: row['minutes'] for row in s.player_match_stats(88)}
  assert stats[1] == 65 and stats[12] == 55
  active=s.connection.execute('SELECT player_id FROM lineup_players WHERE lineup_id=? AND starter=1 ORDER BY player_id',(lineup.lineup_id,)).fetchall()
  assert [row['player_id'] for row in active] == list(range(2,13))
  s.close()

def test_cards_are_recomputed_from_persisted_match_events():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'cards.db';clone(p);s=SportStateStore(p)
  s.connection.executemany("INSERT INTO match_events(match_id,event_type,minute,player_id,payload) VALUES(?,?,?,?,?)",[(88,'YELLOW_CARD',31,7,'{}'),(88,'CARD',80,7,'{}'),(88,'RED_CARD',90,8,'{}'),(88,'RESULT',90,None,'{}')])
  first=s.sync_cards_from_events(88)
  second=s.sync_cards_from_events(88)
  cards={row['player_id']: row['cards'] for row in second}
  assert cards == {7: 2, 8: 1}
  s.close()

def test_player_season_totals_are_read_only_aggregates():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'totals.db';clone(p);s=SportStateStore(p)
  s.record_player_match_stats(1,7,90,2,1,0,8.0)
  s.record_player_match_stats(2,7,60,1,0,1,7.0)
  s.record_player_match_stats(1,8,90,0,2,0,8.5)
  totals=s.player_season_totals(match_ids=[1,2])
  assert totals[0]['player_id'] == 7 and totals[0]['goals'] == 3 and totals[0]['minutes'] == 150
  assert totals[0]['appearances'] == 2 and round(totals[0]['average_rating'],1) == 7.5
  assert s.player_season_totals(player_id=8,match_ids=[1])[0]['assists'] == 2
  s.close()


def test_calculate_chemistry_is_derived_and_deterministic():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'chemistry.db';clone(p);s=SportStateStore(p)
        for pid in range(1,13): s.ensure_player(pid,1,SquadCategory.FIRST_TEAM,position_code=((pid-1)%5)+1)
        lineup=s.create_lineup(1,'4-3-3',range(1,12))
        first=s.calculate_chemistry(1,lineup.lineup_id);second=s.calculate_chemistry(1,lineup.lineup_id)
        assert first == second and first['valid'] is True and first['score'] == 100 and first['position_coverage'] == 5
        assert s.calculate_chemistry(99)['valid'] is False
        s.close()


def test_calculate_morale_impact_uses_persisted_form_and_fatigue():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'morale.db';clone(p);s=SportStateStore(p)
        for pid in range(1,13): s.ensure_player(pid,1,SquadCategory.FIRST_TEAM,position_code=((pid-1)%5)+1)
        lineup=s.create_lineup(1,'4-3-3',range(1,12))
        s.connection.execute('UPDATE player_sport_state SET fatigue=80 WHERE club_id=1');s.connection.commit()
        baseline=s.calculate_morale_impact(1,lineup.lineup_id)
        s.connection.execute('UPDATE player_sport_state SET form=90,fatigue=5 WHERE player_id=1');s.connection.commit()
        improved=s.calculate_morale_impact(1,lineup.lineup_id)
        assert baseline['valid'] is True and improved['modifier'] > baseline['modifier']
        assert s.calculate_morale_impact(99)['valid'] is False
        s.close()


def test_injured_player_is_blocked_from_saved_formation_and_lineup(tmp_path):
    store=SportStateStore(tmp_path/'injured-lineup.db')
    for pid in range(1,13): store.ensure_player(pid,1,SquadCategory.FIRST_TEAM)
    store.injure(1,days=4)
    try: store.save_formation(1,10,'Lesionada','4-3-3',range(1,12))
    except ValueError as error: assert str(error) == 'player unavailable or outside club'
    else: raise AssertionError('atleta lesionado aceito na formação')
    store.close()


def test_suspended_player_is_blocked_from_lineup(tmp_path):
    store=SportStateStore(tmp_path/'suspended-lineup.db')
    for pid in range(1,13): store.ensure_player(pid,1,SquadCategory.FIRST_TEAM)
    suspension=store.suspend(1,days=3,reason='cartões')
    assert suspension['active'] == 1 and store.is_suspended(1) and not store.is_available(1)
    assert store.squad_summary(1)['available'] == 11
    try: store.create_lineup(1,'4-3-3',range(1,12))
    except ValueError as error: assert str(error) == 'player unavailable or outside club'
    else: raise AssertionError('atleta suspenso aceito na escalação')
    store.close()


def test_squad_depth_report_is_grouped_by_canonical_position(tmp_path):
    store=SportStateStore(tmp_path/'depth.db')
    for pid in range(1,13): store.ensure_player(pid,1,SquadCategory.FIRST_TEAM if pid <= 8 else SquadCategory.RESERVE,position_code=1 if pid <= 6 else 2)
    store.injure(1,days=2);store.suspend(9,days=2)
    report=store.squad_depth_report(1)
    by_position={row['position_code']:row for row in report['positions']}
    assert by_position[1]['total'] == 6 and by_position[1]['unavailable'] == 1
    assert by_position[2]['total'] == 6 and by_position[2]['suspended'] == 1
    assert by_position[1]['first_team'] == 6 and by_position[2]['reserve'] == 4
    store.close()


def test_position_coverage_alerts_are_derived_and_configurable(tmp_path):
    store=SportStateStore(tmp_path/'coverage.db')
    for pid in range(1,4): store.ensure_player(pid,1,SquadCategory.FIRST_TEAM,position_code=1)
    alerts=store.position_coverage_alerts(1,minimum_available=4)
    assert alerts['valid'] is False and alerts['alerts'][0]['position_code'] == 1
    assert alerts['alerts'][0]['available'] == 3
    assert store.position_coverage_alerts(1,minimum_available=3)['valid'] is True
    try: store.position_coverage_alerts(1,minimum_available=-1)
    except ValueError as error: assert str(error) == 'INVALID_POSITION_COVERAGE_THRESHOLD'
    else: raise AssertionError('limiar inválido aceito')
    store.close()


def test_player_roles_are_unique_and_require_available_club_member(tmp_path):
    store=SportStateStore(tmp_path/'roles.db')
    for pid in range(1,4): store.ensure_player(pid,1,SquadCategory.FIRST_TEAM)
    captain=store.set_player_role(1,'captain',1)
    updated=store.set_player_role(1,'CAPTAIN',2)
    assert captain['role'] == 'CAPTAIN' and updated['player_id'] == 2 and len(store.player_roles(1)) == 1
    store.injure(3,days=2)
    try: store.set_player_role(1,'PENALTY_TAKER',3)
    except ValueError as error: assert str(error) == 'player unavailable or outside club'
    else: raise AssertionError('atleta indisponível aceito como cobrador')
    store.close()


def test_tactical_decision_history_is_structured_and_chronological(tmp_path):
    store=SportStateStore(tmp_path/'tactics.db')
    store.ensure_player(1,7,SquadCategory.FIRST_TEAM)
    first=store.record_tactical_decision(7,'FORMATION_CONFIRMED',{'formation':'4-3-3','players':[1]},match_id=10)
    store.record_tactical_decision(7,'SUBSTITUTION_PLANNED',{'out':1,'in':2},match_id=10)
    assert first['payload']['formation'] == '4-3-3'
    assert [item['event_type'] for item in store.tactical_decision_history(7,10)] == ['FORMATION_CONFIRMED','SUBSTITUTION_PLANNED']
    assert store.tactical_decision_history(7,11) == []
    try: store.record_tactical_decision(99,'TACTIC',{})
    except ValueError as error: assert str(error) == 'UNKNOWN_CLUB'
    else: raise AssertionError('clube desconhecido aceito')
    store.close()


def test_physical_condition_and_fatigue_risk_are_derived(tmp_path):
    store=SportStateStore(tmp_path/'condition.db')
    store.ensure_player(1,4,SquadCategory.FIRST_TEAM)
    store.ensure_player(2,4,SquadCategory.FIRST_TEAM)
    store.connection.execute('UPDATE player_sport_state SET fatigue=75,condition=55 WHERE player_id=1')
    store.connection.execute('UPDATE player_sport_state SET fatigue=10,condition=90 WHERE player_id=2')
    store.connection.commit()
    report=store.physical_condition(4)
    assert report[0]['fatigue_risk'] == 'HIGH' and report[1]['fatigue_risk'] == 'LOW'
    store.injure(2,days=2)
    assert store.physical_condition(4,2)[0]['fatigue_risk'] == 'CRITICAL'
    try: store.physical_condition(99,1)
    except ValueError as error: assert str(error) == 'PLAYER_OUTSIDE_CLUB'
    else: raise AssertionError('atleta fora do clube aceito')
    store.close()


def test_lineup_confirmation_validates_competition_and_is_idempotent(tmp_path):
    store=SportStateStore(tmp_path/'confirm.db')
    for pid in range(1,13): store.ensure_player(pid,1,SquadCategory.FIRST_TEAM)
    lineup=store.create_lineup(1,'4-3-3',range(1,12))
    confirmation=store.confirm_lineup(1,42,lineup.lineup_id)
    repeated=store.confirm_lineup(1,42,lineup.lineup_id)
    assert confirmation['confirmation_id'] == repeated['confirmation_id']
    assert store.tactical_decision_history(1)[-1]['event_type'] == 'LINEUP_CONFIRMED'
    store.injure(1,days=2)
    try: store.confirm_lineup(1,43,lineup.lineup_id)
    except ValueError as error: assert str(error) == 'LINEUP_HAS_UNAVAILABLE_PLAYER'
    else: raise AssertionError('escalação indisponível confirmada')
    store.close()
