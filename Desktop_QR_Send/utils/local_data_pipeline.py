"""本地联调数据闭环。

当前阶段只在打印机和RFID闭环成功后写入独立的本地测试库；不会连接、
修改或上传到原项目的 example.db，也不会访问远程生产数据库。
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_CONFIG_PATH = PROJECT_ROOT / "config" / "data_pipeline.json"


def load_pipeline_config() -> dict:
    defaults = {
        "mode": "local_test",
        "database_path": "data/local_test.db",
        "remote_upload_enabled": False,
    }
    try:
        if PIPELINE_CONFIG_PATH.exists():
            loaded = json.loads(PIPELINE_CONFIG_PATH.read_text(encoding="utf-8-sig"))
            if isinstance(loaded, dict):
                defaults.update(loaded)
    except Exception as exc:
        logging.exception("读取本地数据流程配置失败，继续使用安全的local_test模式: %s", exc)
    # 未完成生产接口联调前，即使配置写错也不允许隐式开启远程上传。
    defaults["remote_upload_enabled"] = bool(
        defaults.get("remote_upload_enabled", False)
    )
    return defaults


def is_local_test_mode() -> bool:
    return str(load_pipeline_config().get("mode", "local_test")).lower() == "local_test"


def is_remote_upload_enabled() -> bool:
    cfg = load_pipeline_config()
    mode = str(cfg.get("mode", "local_test")).lower()
    return (
        bool(cfg.get("remote_upload_enabled", False))
        or mode in ["remote", "remote_ws"]
    )


class LocalTestDatabase:
    """独立SQLite测试库，每次成功打印以一个事务保存箱与全部盒码。"""

    _schema_lock = threading.Lock()

    def __init__(self, database_path=None):
        configured = database_path or load_pipeline_config().get(
            "database_path", "data/local_test.db"
        )
        path = Path(configured)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        self.database_path = path.resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self):
        conn = sqlite3.connect(str(self.database_path), timeout=10.0)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 10000")
        return conn

    def _ensure_schema(self):
        with self._schema_lock, self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS packing_case (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_code TEXT NOT NULL,
                    rfid_written_value TEXT,
                    rfid_read_epc TEXT,
                    rfid_read_tid TEXT,
                    print_status TEXT NOT NULL DEFAULT 'PRINTED',
                    upload_status TEXT NOT NULL DEFAULT 'PENDING',
                    printed_at TEXT NOT NULL,
                    print_elapsed_ms REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_packing_case_upload_status
                    ON packing_case(upload_status, id);
                CREATE INDEX IF NOT EXISTS idx_packing_case_case_code
                    ON packing_case(case_code);

                CREATE TABLE IF NOT EXISTS packing_box (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    packing_case_id INTEGER NOT NULL,
                    bundle_index INTEGER NOT NULL,
                    item_index INTEGER NOT NULL,
                    box_code TEXT NOT NULL,
                    code_type TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(packing_case_id) REFERENCES packing_case(id)
                        ON DELETE CASCADE,
                    UNIQUE(packing_case_id, bundle_index, item_index)
                );
                """
            )

    def save_successful_print(self, case_code, scan_case_data, print_result) -> int:
        """成功打印后原子保存；任一明细失败则整箱回滚。"""
        case_code = str(case_code or "").strip()
        if not case_code:
            raise ValueError("本地入库失败：箱码为空")
        bundles = list(scan_case_data or [])
        if not bundles:
            raise ValueError("本地入库失败：没有装箱明细")

        now = datetime.now().isoformat(timespec="seconds")
        result_dict = (
            print_result.to_dict()
            if hasattr(print_result, "to_dict")
            else {}
        )
        printed_at = str(result_dict.get("timestamp") or now)

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE")
            cursor.execute(
                """
                INSERT INTO packing_case (
                    case_code, rfid_written_value, rfid_read_epc, rfid_read_tid,
                    print_status, upload_status, printed_at, print_elapsed_ms,
                    created_at
                ) VALUES (?, ?, ?, ?, 'PRINTED', 'PENDING', ?, ?, ?)
                """,
                (
                    case_code,
                    str(result_dict.get("written_value") or ""),
                    str(result_dict.get("read_epc") or ""),
                    str(result_dict.get("read_tid") or ""),
                    printed_at,
                    float(result_dict.get("elapsed_ms") or 0.0),
                    now,
                ),
            )
            packing_case_id = int(cursor.lastrowid)

            row_count = 0
            for bundle_index, bundle in enumerate(bundles, start=1):
                contents = list((bundle or {}).get("boxContents") or [])
                for item_index, item in enumerate(contents, start=1):
                    box_code = str((item or {}).get("data") or "").strip()
                    if not box_code:
                        raise ValueError(
                            f"本地入库失败：第{bundle_index}捆第{item_index}盒码为空"
                        )
                    cursor.execute(
                        """
                        INSERT INTO packing_box (
                            packing_case_id, bundle_index, item_index,
                            box_code, code_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            packing_case_id,
                            bundle_index,
                            item_index,
                            box_code,
                            str((item or {}).get("type") or ""),
                            now,
                        ),
                    )
                    row_count += 1

            if row_count == 0:
                raise ValueError("本地入库失败：装箱明细为空")
            conn.commit()

        logging.info(
            "LOCAL-PRINT-SAVED case_id=%s case_code=%s bundles=%s boxes=%s db=%s",
            packing_case_id,
            case_code,
            len(bundles),
            row_count,
            self.database_path,
        )
        return packing_case_id

    def pending_upload_count(self) -> int:
        with self._connect() as conn:
            return int(
                conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM packing_box AS box
                    JOIN packing_case AS packing
                      ON packing.id = box.packing_case_id
                    WHERE packing.upload_status='PENDING'
                    """
                ).fetchone()[0]
            )

    def mark_as_uploaded(self, record_id: int) -> bool:
        """根据记录 ID 将 upload_status 标记更新为 'UPLOADED'。"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE packing_case SET upload_status='UPLOADED' WHERE id=?",
                (int(record_id),),
            )
            conn.commit()
            return cursor.rowcount > 0

    def clear_pending(self) -> int:
        """归零重置：将所有 PENDING 状态的记录标记更新为 'CLEARED'。"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE packing_case SET upload_status='CLEARED' WHERE upload_status='PENDING'")
            conn.commit()
            return cursor.rowcount

