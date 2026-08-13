# SQLite.py
import sqlite3
import time
import threading  # 导入 threading 模块
import logging  # 导入 logging 模块

class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class Database(metaclass=SingletonMeta):
    def __init__(self):
        if not hasattr(self, 'conn'):
            logging.info("初始化数据库连接...") # 添加日志：数据库连接初始化开始
            self.conn = sqlite3.connect("example.db", check_same_thread=False)
            self.c = self.conn.cursor()
            self._lock = threading.Lock()  # 初始化锁对象
            with self._lock:
                try:
                    self.c.execute("""
                    CREATE TABLE IF NOT EXISTS yk_case (
                        case_code TEXT,
                        create_time TEXT
                    )
                    """)
                    self.c.execute("""
                    CREATE TABLE IF NOT EXISTS yk_box_case (
                        id TEXT PRIMARY KEY,
                        case_content TEXT,
                        box_content TEXT,
                        type TEXT,
                        create_time TEXT,
                        is_line INTEGER DEFAULT 0
                    )
                    """)
                    self.c.execute("""
                    CREATE TABLE IF NOT EXISTS yk_box_case_history (
                        id TEXT PRIMARY KEY,
                        case_content TEXT,
                        box_content TEXT,
                        type TEXT,
                        create_time TEXT,
                        is_line INTEGER DEFAULT 0
                    )
                    """)
                    # 自动字段类型迁移：若旧表 id 字段类型为 INTEGER，自动迁移升级为 TEXT
                    for tbl in ["yk_box_case", "yk_box_case_history"]:
                        info = self.c.execute(f"PRAGMA table_info({tbl})").fetchall()
                        id_col_type = next((col[2] for col in info if col[1] == 'id'), '')
                        if id_col_type.upper() == 'INTEGER':
                            logging.info(f"升级 SQLite 表 {tbl} schema: id 字段从 INTEGER 迁移为 TEXT...")
                            self.c.executescript(f"""
                            CREATE TABLE {tbl}_migrating (
                                id TEXT PRIMARY KEY,
                                case_content TEXT,
                                box_content TEXT,
                                type TEXT,
                                create_time TEXT,
                                is_line INTEGER DEFAULT 0
                            );
                            INSERT INTO {tbl}_migrating SELECT CAST(id AS TEXT), case_content, box_content, type, create_time, is_line FROM {tbl};
                            DROP TABLE {tbl};
                            ALTER TABLE {tbl}_migrating RENAME TO {tbl};
                            """)
                    self.conn.commit()
                except Exception as exc:
                    logging.warning(f"自动初始化 SQLite 数据表提示: {exc}")
            logging.info("数据库连接初始化完成，锁对象与默认表已创建。") # 添加日志：数据库连接初始化完成
        else:
            logging.debug("数据库实例已存在，直接返回现有实例。") # 添加 debug 日志：返回现有实例


    def case_insert_data(self, case_code):
        logging.debug(f"开始插入 case 数据，case_code: {case_code}") # 添加 debug 日志：方法开始
        with self._lock: # 获取锁
            try:
                # 不需要为datetime('now')提供参数
                self.c.execute("INSERT INTO yk_case (case_code, create_time) VALUES (?, datetime('now'))",
                               (case_code,))  # 注意这里的逗号，它将case_code变成一个元组
                self.conn.commit()
                logging.debug(f"成功插入 case 数据，case_code: {case_code}") # 添加 debug 日志：插入成功
            except sqlite3.Error as e:
                self.conn.rollback()
                logging.error(f"插入 case 数据失败，case_code: {case_code}, 错误信息: {e}") # 使用 logging.error 记录错误信息
                raise e # 重新抛出异常，防止错误被忽略
        logging.debug(f"完成插入 case 数据，case_code: {case_code}") # 添加 debug 日志：方法结束


    # =========================================================盒馬箱码绑定表  STAR ==========================================
    # 插入一条识别的信息
    def box_case_insert_data(self, data):
        logging.debug(f"开始插入 box_case 数据，data: {data}") # 添加 debug 日志：方法开始
        with self._lock: # 获取锁
            try:
                self.c.execute("INSERT OR IGNORE INTO yk_box_case (id,case_content, box_content, type, create_time, is_line ) VALUES (?,?, ?, ?, ?, ?)",
                               (data['id'],data['caseContent'], data['boxContent'],  data['type'],data['createTime'], data['isLine']))
                self.conn.commit()
                logging.debug(f"成功插入 box_case 数据，id: {data['id']}") # 添加 debug 日志：插入成功
            except sqlite3.Error as e:
                self.conn.rollback()
                logging.error(f"插入 box_case 数据失败，id: {data['id']}, 错误信息: {e}") # 使用 logging.error 记录错误信息
                raise e # 重新抛出异常，防止错误被忽略
        logging.debug(f"完成插入 box_case 数据，id: {data['id']}") # 添加 debug 日志：方法结束


    # 插入一条识别的历史信息 API在线的时候直接存储到历史记录
    def box_case_history_insert_data(self, data):
        logging.debug(f"开始插入 box_case_history 数据，data: {data}") # 添加 debug 日志：方法开始
        with self._lock: # 获取锁
            try:
                self.c.execute(
                    "INSERT OR IGNORE INTO yk_box_case_history (id,case_content, box_content, type, create_time, is_line ) VALUES (?,?, ?, ?, ?, ?)",
                    (data['id'], data['caseContent'], data['boxContent'],  data['type'],data['createTime'], data['isLine']))
                self.conn.commit()
                logging.debug(f"成功插入 box_case_history 数据，id: {data['id']}") # 添加 debug 日志：插入成功
            except sqlite3.Error as e:
                self.conn.rollback()
                logging.error(f"插入 box_case_history 数据失败，id: {data['id']}, 错误信息: {e}") # 使用 logging.error 记录错误信息
                raise e # 重新抛出异常，防止错误被忽略
        logging.debug(f"完成插入 box_case_history 数据，id: {data['id']}") # 添加 debug 日志：方法结束

    # 检查某个 ID 是否已经在历史表（即已成功上传过）
    def is_uploaded(self, id):
        with self._lock:
            self.c.execute("SELECT 1 FROM yk_box_case_history WHERE id = ? LIMIT 1", (id,))
            return self.c.fetchone() is not None


    # 查询最早的一条信息没有上传的信息,根据create_time和is_line；is_line中0表示未上传，1表示已上传
    def box_case_unuploaded(self):
        logging.debug("开始查询最早的未上传 box_case 数据") # 添加 debug 日志：方法开始
        with self._lock: # 获取锁
            self.c.execute("""
                SELECT id,
                       case_content AS caseContent,
                       box_content AS boxContent,
                       type,
                       create_time AS createTime,
                       is_line AS isLine
                FROM yk_box_case
                WHERE is_line = 0
                ORDER BY create_time ASC
                LIMIT 1
            """)
            result = self.c.fetchone()
            if result:
                logging.debug(f"查询到未上传 box_case 数据，id: {result[0]}") # 添加 debug 日志：查询到数据
                # 将元组转换为字典
                return {
                    'id': result[0],
                    'caseContent': result[1],
                    'boxContent': result[2],
                    'type': result[3],
                    'createTime': result[4],
                    'isLine': result[5]
                }
            else:
                logging.debug("没有查询到未上传 box_case 数据") # 添加 debug 日志：没有查询到数据
                return None
        logging.debug("完成查询最早的未上传 box_case 数据") # 添加 debug 日志：方法结束


    # 根据ID查询数据
    def box_case_search_by_id(self, id):
        logging.debug(f"开始根据 ID 查询 box_case 数据，id: {id}") # 添加 debug 日志：方法开始
        with self._lock:  # 获取锁
            self.c.execute("""
                SELECT id,
                        case_content AS caseContent,
                       box_content AS boxContent,
                       type,
                       create_time AS createTime,
                       is_line AS isLine
                FROM yk_box_case
                WHERE id = ?
            """, (id,))
            row = self.c.fetchone()  # 先获取 fetchone() 的元组结果
            if row:  # 如果查询到记录 (fetchone() 返回了元组，而不是 None)
                logging.debug(f"查询到 box_case 数据，id: {id}") # 添加 debug 日志：查询到数据
                # 将元组转换为字典，键为字段名，值为元组对应位置的值
                return {
                    'id': row[0],
                    'caseContent': row[1],
                    'boxContent': row[2],
                    'type': row[3],
                    'createTime': row[4],
                    'isLine': row[5]
                }
            else:
                logging.debug(f"没有查询到 box_case 数据，id: {id}") # 添加 debug 日志：没有查询到数据
                return None
        logging.debug(f"完成根据 ID 查询 box_case 数据，id: {id}") # 添加 debug 日志：方法结束


    # 根据ID删除一条数据
    def  box_case_delete_by_id(self, id):
        logging.debug(f"开始根据 ID 删除 box_case 数据，id: {id}") # 添加 debug 日志：方法开始
        with self._lock: # 获取锁
            try:
                self.c.execute("""
                    DELETE FROM yk_box_case
                    WHERE id = ?
                """, (id,))
                self.conn.commit()
                logging.debug(f"成功删除 box_case 数据，id: {id}") # 添加 debug 日志：删除成功
            except sqlite3.Error as e:
                self.conn.rollback()
                logging.error(f"删除 box_case 数据失败，id: {id}, 错误信息: {e}") # 使用 logging.error 记录错误信息
                raise e # 重新抛出异常，防止错误被忽略
        logging.debug(f"完成根据 ID 删除 box_case 数据，id: {id}") # 添加 debug 日志：方法结束


    # 统计有多少条信息没有上传；统计一共有多少条is_line为0的数据
    def  box_case_count_unuploaded(self):
        logging.debug("开始统计未上传 box_case 数据数量") # 添加 debug 日志：方法开始
        with self._lock: # 获取锁
            self.c.execute("""
                SELECT COUNT(*) FROM yk_box_case
                WHERE is_line = 0
            """)
            count = self.c.fetchone()[0]
            logging.debug(f"统计到未上传 box_case 数据数量: {count}") # 添加 debug 日志：统计结果
            return count
        logging.debug("完成统计未上传 box_case 数据数量") # 添加 debug 日志：方法结束

    def clear_unuploaded(self):
        """归零重置：将所有未上传 is_line=0 数据标记更新为 1。"""
        with self._lock:
            self.c.execute("UPDATE yk_box_case SET is_line = 1 WHERE is_line = 0")
            self.conn.commit()

        #查询最老的数据
    def box_case_search_by_time_range(self, limit: int = 1000):
        """
        查询 yk_box_case 表数据，按照 create_time 由旧到新排序，最多查询指定数量的数据。

        :param limit:  最大查询数量，默认为 1000 条。
        :return:  一个列表，列表中每个元素是一个字典，代表查询到的一条记录。
                  如果查询结果为空，则返回空列表。
        """
        logging.debug(f"开始查询 box_case 数据，按时间范围，限制数量: {limit}") # 添加 debug 日志：方法开始
        with self._lock: # 获取锁
            try:
                self.c.execute("""
                    SELECT id,
                           case_content AS caseContent,
                           box_content AS boxContent,
                           type,
                           create_time AS createTime,
                           is_line AS isLine
                    FROM yk_box_case
                    WHERE is_line = 0
                    ORDER BY create_time ASC  -- 按照 create_time 升序排列 (由旧到新)
                    LIMIT ?                     -- 限制查询数量
                """, (limit,)) # 使用参数化查询，防止 SQL 注入，并传入 limit 参数

                rows =  self.c.fetchall() # 获取所有查询结果 (fetchall 返回的是一个列表，每个元素是一个元组)
                logging.debug(f"查询到 box_case 数据，数量: {len(rows)}") # 添加 debug 日志：查询结果数量
                return rows # 获取所有查询结果 (fetchall 返回的是一个列表，每个元素是一个元组)

            except sqlite3.Error as e:
                logging.error(f"box_case_search_by_time_range 查询数据库错误: {e}") # 使用 logging.error 替换 print，记录错误日志
                return [] # 发生错误时返回空列表
        logging.debug(f"完成查询 box_case 数据，按时间范围，限制数量: {limit}") # 添加 debug 日志：方法结束

    # 删除所有数据
    def  box_case_history_delete_all(self):
        logging.debug("开始删除所有 box_case_history 数据") # 添加 debug 日志：方法开始
        with self._lock: # 获取锁
            try:
                self.c.execute("""
                    DELETE FROM yk_box_case_history
                """)
                self.conn.commit()
                logging.debug("成功删除所有 box_case_history 数据") # 添加 debug 日志：删除成功
            except sqlite3.Error as e:
                self.conn.rollback()
                logging.error(f"删除所有 box_case_history 数据失败: {e}") # 使用 logging.error 记录错误信息
                raise e # 重新抛出异常，防止错误被忽略
        logging.debug("完成删除所有 box_case_history 数据") # 添加 debug 日志：方法结束


    # 将上传的数据保存到本地表中
    def box_case_history_insert_data(self, data):
        logging.debug(f"开始插入 box_case_history 数据，data: {data}") # 添加 debug 日志：方法开始
        with self._lock: # 获取锁
            try:
                self.c.execute("INSERT OR REPLACE INTO yk_box_case_history (id, case_content, box_content, type, create_time, is_line ) VALUES (?, ?, ?, ?, ?, ?)",
                               (data['id'], data['caseContent'], data['boxContent'], data['type'], data['createTime'], data['isLine']))
                self.conn.commit()
                logging.debug(f"成功插入 box_case_history 数据，id: {data['id']}") # 添加 debug 日志：插入成功
            except sqlite3.Error as e:
                self.conn.rollback()
                logging.error(f"插入 box_case_history 数据失败，id: {data['id']}, 错误信息: {e}") # 使用 logging.error 记录错误信息
                raise e # 重新抛出异常，防止错误被忽略
        logging.debug(f"完成插入 box_case_history 数据，id: {data['id']}") # 添加 debug 日志：方法结束


    # =========================================================盒馬箱码绑定表  END==========================================

    # 不再需要close方法，因为我们希望连接一直保持开启状态
    # def close(self):
    #     self.conn.close()
    #