import sqlite3
db = sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
c = db.cursor()
print('TABLES:', [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")])
for t in ['contributions', 'runs']:
    try:
        cols = [d[1] for d in c.execute('PRAGMA table_info(%s)' % t)]
        print(t, 'COLS:', cols)
    except Exception as e:
        print(t, 'ERR', e)