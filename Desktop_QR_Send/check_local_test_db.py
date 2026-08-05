import os, sqlite3

lt_db = 'data/local_test.db'
print("Checking data/local_test.db:")
if os.path.exists(lt_db):
    print("Found data/local_test.db, size:", os.path.getsize(lt_db))
    conn = sqlite3.connect(lt_db)
    c = conn.cursor()
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print("Tables in local_test.db:", tables)
    for t in tables:
        cnt = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"  Table {t} count:", cnt)
    conn.close()
else:
    print("data/local_test.db does not exist")
