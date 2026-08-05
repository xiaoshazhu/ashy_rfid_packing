import os, json, sqlite3

print("--- Checking Database Files ---")
for name in ['example.db', 'local_test.db']:
    if os.path.exists(name):
        print(f"{name} EXISTS, size={os.path.getsize(name)} bytes")
        try:
            conn = sqlite3.connect(name)
            c = conn.cursor()
            tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            print(f"  Tables in {name}:", tables)
            for t in tables:
                cnt = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                print(f"    Table {t} count:", cnt)
            conn.close()
        except Exception as e:
            print("  Error reading", name, e)
    else:
        print(f"{name} DOES NOT EXIST")

with open('config.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)
print("config.json pageData:", cfg.get("pageData"))
