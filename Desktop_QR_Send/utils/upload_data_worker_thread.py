# upload_data_worker_thread.py
import asyncio
import time

from PySide6 import QtCore

from utils.SQLite import Database
import logging  # 导入 logging 模块


# 工作线程类 (Worker Thread Class)
class UploadDataWorkerThread(QtCore.QThread):
    update_progress_signal = QtCore.Signal(float)

    def __init__(self, main_window, max_limit): # 构造函数，接收 main_window 和 max_limit 参数
        super().__init__()
        self.main_window = main_window
        self.max_limit = max_limit
        logging.info(f"UploadDataWorkerThread 初始化，max_limit: {max_limit}") # 添加日志：线程初始化

    def run(self): # 后台线程执行的代码
        logging.info("UploadDataWorkerThread 开始执行数据上传任务...") # 添加日志：run 方法开始
        db = Database() #  在线程内部创建 Database 实例，保证线程安全
        logging.debug("在 WorkerThread 内部创建 Database 实例") # 添加 debug 日志：创建 Database 实例
        data_list = db.box_case_search_by_time_range(self.max_limit) # <-- 数据库查询 (后台线程)
        max_rows = len(data_list)
        logging.debug(f"从数据库查询到 {max_rows} 条待上传数据，查询限制: {self.max_limit}") # 添加 debug 日志：查询数据量

        if max_rows == 0:
            logging.info("没有需要上传的数据，任务结束。") # 添加日志：没有数据上传
            self.update_progress_signal.emit(100.0) #  发送 100% 完成信号
            return

        logging.info(f"开始循环上传数据，共 {max_rows} 条数据") # 添加日志：开始循环上传
        for i, row in enumerate(data_list):
            time.sleep(0.001)#增加的延迟 慢慢优化
            raw_box = row[2]
            box_content_str = str(raw_box)
            if box_content_str.startswith("{") and "data" in box_content_str:
                try:
                    import json
                    parsed = json.loads(box_content_str.replace("'", '"'))
                    if isinstance(parsed, dict) and "data" in parsed:
                        box_content_str = parsed["data"]
                except Exception:
                    pass

            result_dict = {
                'id': row[0],
                'caseContent': row[1],
                'boxContent': box_content_str,
                'type': row[3],
                'createTime': row[4],
                'isLine': row[5]
            }
            logging.debug(f"准备上传数据，数据 ID: {result_dict['id']}") # 添加 debug 日志：准备上传数据

            try:
                from utils.local_data_pipeline import load_pipeline_config
                cfg = load_pipeline_config()
                mode = str(cfg.get("mode", "local_mysql")).lower()

                # 如果是 WS 线上模式（"remote" 或 "remote_ws"）且 client 连接可用
                if mode in ["remote", "remote_ws"] and getattr(self.main_window, "client", None) and getattr(self.main_window, "loop", None):
                    future = asyncio.run_coroutine_threadsafe(self.main_window.client.send(result_dict), self.main_window.loop)
                    logging.debug(f"数据已发往 WS 线上服务，ID: {result_dict['id']}")
                else:
                    # 本地 MySQL 模式：直接将 result_dict 数据包持久化保存到本地 MySQL yk_store_case_box 表
                    from utils.MySQL import MySQLDatabase
                    MySQLDatabase().box_case_insert_data(result_dict)
                    logging.info(f"本地 MySQL 落库成功: ID={result_dict['id']} 箱码={result_dict.get('caseContent')} 盒码={result_dict.get('boxContent')}")

            except Exception as e:
                logging.error(f"后台数据发送/落库出错: {e}, 数据 ID: {result_dict['id']}")

            # time.sleep(1)  # 暫停執行 1 秒
            percen = round((i + 1) / max_rows * 100, 2) if max_rows > 0 else 0
            self.update_progress_signal.emit(percen) # 发射信号，请求主线程更新 UI
            logging.debug(f"数据上传进度: {percen}%,  数据 ID: {result_dict['id']}") # 添加 debug 日志：上传进度

        # 循环结束后，发送完成信号 (可选， 例如可以发送 100% 百分比，或者发送一个特殊的完成信号)
        self.update_progress_signal.emit(100.0) #  发送 100% 完成信号 (或者其他完成标志)
        logging.info("UploadDataWorkerThread 数据上传任务执行完成，发送 100% 完成信号。") # 添加日志：run 方法结束


if __name__ == '__main__':
    #  测试 UploadDataWorkerThread 的日志功能
    import sys
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar
    import logging
    from unittest.mock import MagicMock

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s')

    class MockMainWindow(QWidget): #  Mock MainWindow， 简化版本， 仅包含 WorkerThread 需要的属性和方法
        def __init__(self):
            super().__init__()
            self.client = MockClient() #  Mock Client
            self.loop = asyncio.get_event_loop() #  获取 event loop

            self.progress_bar = QProgressBar() # Mock progress bar
            self.upload_button = QPushButton("开始上传数据") # Mock upload button

            layout = QVBoxLayout()
            layout.addWidget(self.progress_bar)
            layout.addWidget(self.upload_button)
            self.setLayout(layout)

        def update_progress(self, progress): # Mock update_progress method
            self.progress_bar.setValue(int(progress))
            logging.info(f"Mock MainWindow 进度条更新: {progress}%") #  添加日志：Mock MainWindow 进度条更新


    class MockClient: # Mock Client， 简化版本，  只模拟 send 方法
        async def send(self, data):
            await asyncio.sleep(0.1) # 模拟网络延迟
            logging.info(f"Mock Client 发送数据: {data}") #  添加日志：Mock Client 发送数据


    app = QApplication(sys.argv)
    main_window = MockMainWindow() # 创建 Mock MainWindow 实例

    worker_thread = UploadDataWorkerThread(main_window, max_limit=5) # 创建 WorkerThread 实例
    worker_thread.update_progress_signal.connect(main_window.update_progress) # 连接信号和槽

    main_window.upload_button.clicked.connect(worker_thread.start) #  连接按钮点击事件到线程启动

    main_window.show()
    sys.exit(app.exec_())