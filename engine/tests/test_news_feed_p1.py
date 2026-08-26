import sqlite3
from engine.events.service import ClubEventService

def test_news_catalog_feed_filters_cursor_read_and_archive():
    service = ClubEventService(sqlite3.connect(':memory:'))
    assert len(service.news_catalog()) == 3
    assert service.record(1, 'NOTICIA_PARTIDA', 'HIGH', 'Vitória', 'Jogo oficial', 'match:1', origin='fixture:1', event_date='2026-01-02')
    assert service.record(1, 'NOTICIA_SAUDE', 'NORMAL', 'Retorno', 'Atleta voltou', 'health:1', origin='health:1', event_date='2026-01-01')
    assert not service.record(1, 'NOTICIA_PARTIDA', 'HIGH', 'Vitória', 'duplicada', 'match:1', origin='fixture:1')
    page = service.news_feed(1, limit=1)
    assert page['count'] == 1 and page['next_cursor'] is not None
    next_page = service.news_feed(1, limit=2, cursor=page['next_cursor'])
    assert next_page['count'] == 1
    event_id = page['items'][0]['event_id']
    assert service.mark_read(1, event_id) is True
    assert service.archive(1, event_id) is True
    assert service.group_by_day(1)[0]['count'] == 1
