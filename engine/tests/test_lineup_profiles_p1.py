from __future__ import annotations

import sqlite3

from engine.sports.cycle import SportStateStore


def make_store():
    connection = sqlite3.connect(':memory:')
    return SportStateStore(connection)


def test_tactical_profile_and_lineup_preview_are_persisted_separately():
    store = make_store()
    profile = store.create_tactical_profile(1, 'Pressão alta', '4-3-3', {'tempo': 'alto'})
    assert profile['formation'] == '4-3-3'
    assert store.tactical_profiles(1)[0]['instructions']['tempo'] == 'alto'
    for player_id in range(1, 12):
        store.ensure_player(player_id, 1, position_code=(player_id % 5) + 1)
    store.save_formation(1, 10, 'Principal', '4-3-3', range(1, 12))
    before = store.connection.total_changes
    preview = store.preview_lineup(1, 10, 'Principal')
    assert preview['valid'] is True and preview['persisted'] is False
    assert store.connection.total_changes == before
    lineup = store.create_match_lineup(1, 10, 'Principal')
    confirmed = store.confirm_lineup(1, 10, lineup.lineup_id, 99)
    assert confirmed['competition_id'] == 10
    assert store.lineup_history(1, lineup.lineup_id)[0]['event_type'] == 'LINEUP_CONFIRMED'
    store.close()
