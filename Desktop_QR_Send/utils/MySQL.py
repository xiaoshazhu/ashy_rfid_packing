"""MySQL 数据库强保入库管理模块。"""
import time
import threading
import logging

try:
    import pymysql
    HAS_PYMYSQL = True
except ImportError:
    pymysql = None
    HAS_PYMYSQL = False


class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class MySQLDatabase(metaclass=SingletonMeta):
    def __init__(self, host=None, port=None, user=None, password=None, database=None):
        # 优先读取配置文件中的数据
        try:
            from utils.local_data_pipeline import load_pipeline_config
            cfg = load_pipeline_config()
            mysql_cfg = cfg.get("mysql", {})
        except Exception:
            mysql_cfg = {}

        self.host = host or mysql_cfg.get("host", "127.0.0.1")
        self.port = int(port or mysql_cfg.get("port", 3306))
        self.user = user or mysql_cfg.get("user", "root")
        raw_pwd = password if password is not None else mysql_cfg.get("password", "YOUR_PASSWORD_HERE")
        self.password = str(raw_pwd) if raw_pwd is not None else ""
        self.database = database or mysql_cfg.get("database", "gya_yudao_mini")
        self._lock = threading.Lock()
        if HAS_PYMYSQL:
            self._ensure_table_exists()
        else:
            logging.warning("当前 Python 环境未安装 pymysql，请运行: pip install pymysql")

    def _get_connection(self):
        if not HAS_PYMYSQL:
            raise ImportError("设备电脑未安装 pymysql 依赖库，请在命令行执行: pip install pymysql")
        
        target_host = str(self.host).strip() if self.host else "127.0.0.1"

        return pymysql.connect(
            host=target_host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset="utf8mb4",
            autocommit=True,
            connect_timeout=5
        )

    def _ensure_table_exists(self):
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS `yk_store_case_box` (
                  `id` bigint NOT NULL,
                  `case_content` varchar(255) NOT NULL,
                  `box_content` varchar(255) NOT NULL,
                  `type` varchar(255) DEFAULT NULL,
                  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
                  `update_time` datetime DEFAULT NULL,
                  `deleted` tinyint(1) DEFAULT 0,
                  `creator` varchar(255) DEFAULT '',
                  `updater` varchar(255) DEFAULT '',
                  PRIMARY KEY (`id`),
                  UNIQUE KEY `uk_case_box` (`case_content`,`box_content`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
            conn.close()
            logging.info(f"MySQL 连接与 yk_store_case_box 表校验成功！[host={self.host}, db={self.database}]")
        except Exception as e:
            logging.error(f"校验 MySQL yk_store_case_box 表失败: {e}")

    def box_case_insert_data(self, data):
        """插入一条识别的信息存入 MySQL yk_store_case_box。"""
        if not HAS_PYMYSQL:
            raise ImportError("设备电脑未安装 pymysql，请先运行: pip install pymysql")

        with self._lock:
            try:
                conn = self._get_connection()
                record_id = data.get('id')
                if not record_id:
                    record_id = int(time.time() * 1000000)
                case_cnt = data.get('caseContent', '')
                box_cnt = data.get('boxContent', '')
                record_type = data.get('type', '预装箱录入')
                create_tm = data.get('createTime', time.strftime("%Y-%m-%d %H:%M:%S"))

                with conn.cursor() as cursor:
                    sql = """
                    INSERT INTO yk_store_case_box 
                    (id, case_content, box_content, type, create_time, deleted, creator, updater)
                    VALUES (%s, %s, %s, %s, %s, 0, '', '')
                    ON DUPLICATE KEY UPDATE 
                    case_content=VALUES(case_content), box_content=VALUES(box_content), type=VALUES(type);
                    """
                    cursor.execute(sql, (record_id, case_cnt, box_cnt, record_type, create_tm))
                conn.close()
                logging.debug(f"MYSQL SUCCESS yk_store_case_box 插入成功 id={record_id} case={case_cnt} box={box_cnt}")
            except Exception as e:
                logging.error(f"插入 MySQL yk_store_case_box 数据失败: {e}")
                raise e

    def box_case_count_unuploaded(self):
        """统计 MySQL 中未删除记录。"""
        if not HAS_PYMYSQL:
            return 0
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM yk_store_case_box WHERE deleted = 0")
                cnt = cursor.fetchone()[0]
            conn.close()
            return cnt
        except Exception as e:
            logging.error(f"查询 MySQL 未上传统计失败: {e}")
            return 0
