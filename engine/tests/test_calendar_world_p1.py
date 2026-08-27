import sqlite3
from engine.world.calendar import CalendarService

def test_calendar_holidays_fifa_timezone_priority_and_adjustment():
    service=CalendarService(sqlite3.connect(':memory:'))
    holiday=service.add_national_holiday(55,'2027-02-15','Feriado')
    assert holiday == service.add_national_holiday(55,'2027-02-15','Feriado')
    window=service.add_fifa_window('2027-02-10','2027-02-20','Data FIFA')
    assert window == service.add_fifa_window('2027-02-10','2027-02-20','Data FIFA')
    assert service.set_stadium_timezone(1,'America/Sao_Paulo',-180)['timezone'] == 'America/Sao_Paulo'
    assert service.set_competition_priority(9,90)['priority'] == 90
    calendar_id=service.create_period(2027,'REGULAR','2027-02-15','2027-02-15',competition_id=9,club_id=1)
    assert service.international_window_conflicts(2027,1)[0]['fifa_window'] == 'Data FIFA'
    adjustment=service.adjust_fixture(calendar_id,'2027-02-16','FIFA_WINDOW',90)
    assert adjustment['new_start'] == '2027-02-16'
    assert service.adjust_fixture(calendar_id,'2027-02-16','FIFA_WINDOW',90)['adjustment_id'] == adjustment['adjustment_id']
    assert service.audit_changes(calendar_id)[0]['action'] == 'RESCHEDULE'
    assert service.add_registration_window(2027,'YOUTH','2027-01-01','2027-02-28')['category'] == 'YOUTH'
    assert service.set_travel_rule(55,99,'AIR',2,5000)['cost'] == 5000
    assert service.travel_preview(55,99,'AIR')['persisted'] is False
    assert service.minimum_rest(2027,1,'2027-02-20',2)['available'] is True
    assert service.overlap_preview(2027,1,'2027-02-16','2027-02-16')['blocked'] is True
    assert service.season_preview(2027)['persisted'] is False
    service.close()
