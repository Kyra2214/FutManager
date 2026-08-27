import sqlite3
from engine.events.service import ClubEventService

def test_news_catalog_feed_filters_cursor_read_and_archive():
    service = ClubEventService(sqlite3.connect(':memory:'))
    assert len(service.news_catalog()) == 3
    assert service.generate_match_news(1, 1, 'Vitória', 'Jogo oficial', 'HIGH')
    assert service.generate_health_news(1, 1, 'Retorno', 'Atleta voltou')
    assert not service.record(1, 'NOTICIA_PARTIDA', 'HIGH', 'Vitória', 'duplicada', 'match:1', origin='fixture:1')
    page = service.news_feed(1, limit=1)
    assert page['count'] == 1 and page['next_cursor'] is not None
    next_page = service.news_feed(1, limit=2, cursor=page['next_cursor'])
    assert next_page['count'] == 1
    event_id = page['items'][0]['event_id']
    assert service.mark_read(1, event_id) is True
    service.set_preference(1, 'NOTICIA_SAUDE', False)
    assert service.news_feed(1, type_='NOTICIA_SAUDE')['count'] == 0
    assert service.archive(1, event_id) is True
    assert service.group_by_day(1)[0]['count'] == 2
