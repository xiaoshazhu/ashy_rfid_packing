import os, json, sqlite3

db_path = 'example.db'
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("DELETE FROM yk_box_case;")
        c.execute("DELETE FROM yk_case;")
        c.execute("DELETE FROM yk_box_case_history;")
        conn.commit()
        conn.close()
        print("example.db cleared successfully!")
    except Exception as e:
        print("Error clearing example.db:", e)
        try:
            os.remove(db_path)
            print("example.db deleted successfully!")
        except Exception as e2:
            print("Error deleting example.db:", e2)

cfg_path = 'config.json'
if os.path.exists(cfg_path):
    with open(cfg_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    cfg['pageData'] = {
        'label_data_box': 0,
        'label_data_case': 0,
        'label_data_unline': 0
    }
    cfg['caseData'] = []
    cfg['caseCode'] = None
    with open(cfg_path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=4)
    print("config.json pageData reset to 0 OK!")
