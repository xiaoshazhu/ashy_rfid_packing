"""只读查看真实打印后写入的本地测试数据。"""

import sqlite3
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

root = Path(__file__).resolve().parent
database_path = root / "data" / "local_test.db"

print("=" * 64)
print("高原安装箱扫码 - 本地打印测试数据（只读）")
print("=" * 64)
print(f"数据库：{database_path}")

if not database_path.exists():
    print("[暂无数据] 还没有成功完成‘打印标签 + RFID核验 + 本地入库’。")
    raise SystemExit(0)

uri = "file:" + database_path.as_posix() + "?mode=ro"
with sqlite3.connect(uri, uri=True) as conn:
    case_count = conn.execute("SELECT COUNT(*) FROM packing_case").fetchone()[0]
    box_count = conn.execute("SELECT COUNT(*) FROM packing_box").fetchone()[0]
    pending_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM packing_box AS box
        JOIN packing_case AS packing ON packing.id=box.packing_case_id
        WHERE packing.upload_status='PENDING'
        """
    ).fetchone()[0]
    print(f"打印记录：{case_count} 箱")
    print(f"盒码明细：{box_count} 条")
    print(f"待远程上传：{pending_count} 条（当前local_test模式不会上传）")
    print("-" * 64)
    rows = conn.execute(
        """
        SELECT id, case_code, rfid_written_value, print_status,
               upload_status, printed_at
        FROM packing_case
        ORDER BY id DESC
        LIMIT 10
        """
    ).fetchall()
    if not rows:
        print("没有打印记录。")
    else:
        print("最近10次真实打印记录：")
        for row in rows:
            print(
                f"  ID={row[0]} 箱码={row[1]} RFID={row[2] or '<空>'} "
                f"打印={row[3]} 上传={row[4]} 时间={row[5]}"
            )

