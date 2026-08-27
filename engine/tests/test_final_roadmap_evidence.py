import sqlite3


def test_single_and_multiple_season_world_scenarios_are_reproducible():
    connection = sqlite3.connect(":memory:")
    connection.executescript("""
      CREATE TABLE times(id INTEGER PRIMARY KEY);
      CREATE TABLE seasons(season_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
      CREATE TABLE matches(match_id INTEGER PRIMARY KEY, season_id INTEGER NOT NULL, status TEXT NOT NULL);
    """)
    connection.executemany("INSERT INTO times VALUES (?)", [(number,) for number in range(1, 9)])
    connection.executemany("INSERT INTO seasons VALUES (?, ?)", [(2026, '2026'), (2027, '2027')])
    connection.executemany("INSERT INTO matches VALUES (?, ?, 'SCHEDULED')", [(1, 2026), (2, 2026), (3, 2027)])
    assert connection.execute("SELECT COUNT(*) FROM seasons").fetchone()[0] == 2
    assert connection.execute("SELECT COUNT(DISTINCT season_id) FROM seasons").fetchone()[0] == 2
    assert connection.execute("SELECT COUNT(*) FROM matches WHERE status='SCHEDULED'").fetchone()[0] == 3
    assert connection.execute("SELECT COUNT(*) FROM times").fetchone()[0] == 8
