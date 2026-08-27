import sqlite3
from difflib import get_close_matches
from engine.world.first_division import FIRST_DIVISION_SOURCES, normalize_club_name, resolve_first_division_members

DB = 'data/state/game.db'
c = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
for source in FIRST_DIVISION_SOURCES:
    report = resolve_first_division_members(c, source.country_id)
    names = [r[0] for r in c.execute('select nome from times where pais_id=?', (source.country_id,))]
    normalized = {normalize_club_name(name): name for name in names}
    print('\n'+source.country_code)
    for missing in report['unmatched']:
        suggestions = get_close_matches(normalize_club_name(missing), list(normalized), n=5, cutoff=0.35)
        print(missing, '=>', [normalized[item] for item in suggestions])
