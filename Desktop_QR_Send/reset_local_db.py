import os
import sqlite3
from pathlib import Path

root = Path(__file__).resolve().parent

print("===================================================")
print("Executing database table reset...")
print(f"Current Path: {root}")
print("===================================================")

# 1. 清理 example.db (SQLite)
for db_file in [root / "example.db", Path("D:/激光扫码/Desktop_QR_Send/example.db")]:
    if db_file.exists():
        try:
            conn = sqlite3.connect(str(db_file))
            c = conn.cursor()
            c.execute("DELETE FROM yk_box_case;")
            c.execute("DELETE FROM yk_case;")
            c.execute("DELETE FROM yk_box_case_history;")
            conn.commit()
            conn.close()
            print(f"[OK] SQLite {db_file.name} (yk_box_case/yk_case) cleared successfully!")
        except Exception as e:
            print(f"[ERR] Failed to clear {db_file}:", e)

# 2. 清理 data/local_test.db (SQLite)
for db_file in [root / "data" / "local_test.db", Path("D:/激光扫码/Desktop_QR_Send/data/local_test.db")]:
    if db_file.exists():
        try:
            conn = sqlite3.connect(str(db_file))
            c = conn.cursor()
            c.execute("DELETE FROM packing_box;")
            c.execute("DELETE FROM packing_case;")
            try:
                c.execute("DELETE FROM local_test_print_records;")
            except Exception:
                pass
            conn.commit()
            conn.close()
            print(f"[OK] SQLite {db_file.name} (packing_box/packing_case) cleared successfully!")
        except Exception as e:
            print(f"[ERR] Failed to clear {db_file}:", e)

# 3. 清理 MySQL 本地库 (若设备电脑开启了 MySQL)
try:
    from utils.MySQL import MySQLDatabase, HAS_PYMYSQL
    if HAS_PYMYSQL:
        mysql_db = MySQLDatabase()
        conn = mysql_db._get_connection()
        with conn.cursor() as cursor:
            cursor.execute("UPDATE yk_store_case_box SET deleted = 1 WHERE deleted = 0;")
        conn.commit()
        conn.close()
        print("[OK] MySQL yk_store_case_box marked as deleted!")
except Exception as m_err:
    print("[INFO] MySQL cleanup skipped or not active:", m_err)

# 4. 清空 records/print_records.csv 避免历史箱码卡控造成 RFID 误判跳过
for csv_file in [root / "records" / "print_records.csv", Path("D:/激光扫码/Desktop_QR_Send/records/print_records.csv")]:
    if csv_file.exists():
        try:
            with open(csv_file, "w", encoding="utf-8-sig") as f:
                f.write("timestamp,box_code,target_region,written_value,read_tid,read_epc,read_user,read_ascii,result,elapsed_ms,error_code,error_message\n")
            print(f"[OK] {csv_file.name} cleared successfully!")
        except Exception as e:
            print(f"[ERR] Failed to clear {csv_file}:", e)

print("===================================================")
print("[SUCCESS] All database records cleared to 0!")
print("===================================================")
