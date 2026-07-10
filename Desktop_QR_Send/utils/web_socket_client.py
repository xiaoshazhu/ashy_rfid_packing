# web_socket_client.py
import asyncio
import websockets
import threading
import json
from asyncio import Queue

from PIL.ImageStat import Global

from utils.SQLite import Database
import logging # 导入 logging 模块


# WebSocket 客户端类
class WebSocketClient:
    # 初始化方法
    def __init__(self, uri, heartbeat_interval=None):
        """初始化 WebSocket 客户端
        :param uri: WebSocket 服务端地址
        :param heartbeat_interval: 心跳间隔（秒），若为空则不启用心跳
        """
        logging.info(f"WebSocketClient 初始化，URI: {uri}, 心跳间隔: {heartbeat_interval} 秒") # 添加日志：初始化
        self.uri = uri                  # 服务端 URI
        self.websocket = None           # WebSocket 连接对象
        self.connected = False          # 连接状态
        self._connection_listeners = [] # 连接状态监听器列表
        self._message_listeners = []    # 消息监听器列表
        self.heartbeat_interval = heartbeat_interval # 心跳间隔
        self._heartbeat_task = None     # 心跳任务
        logging.debug("WebSocketClient 对象创建完成，等待连接。") # 添加 debug 日志：对象创建完成

    async def connect(self):
        """连接到 WebSocket 服务端，并处理自动重连"""
        logging.info(f"开始连接 WebSocket 服务端: {self.uri}") # 添加日志：连接开始
        while True:
            try:
                self.websocket = await websockets.connect(self.uri)
                self.connected = True
                logging.info(f"成功连接到 WebSocket 服务端: {self.uri}") # 使用 logging.info 替换 print，记录连接成功
                await self._notify_connection_listeners(True)
                if self.heartbeat_interval:
                    self._start_heartbeat() # 启动心跳
                await self._receive_messages() # 开始接收消息
                break
            except Exception as e:
                self.connected = False
                await self._notify_connection_listeners(False)
                logging.warning(f"连接 WebSocket 服务端失败: {e}，正在重试...") # 使用 logging.warning 替换 print，记录连接失败和重试
                await asyncio.sleep(30) # 重试前等待 30 秒
        logging.info(f"WebSocket 客户端连接循环结束。") # 添加日志：连接循环结束

    async def _receive_messages(self):
        """持续接收 WebSocket 消息"""
        logging.info("开始接收 WebSocket 消息...") # 添加日志：接收消息开始
        try:
            async for message in self.websocket:
                await self._notify_message_listeners(message)
        except Exception as e:
            self.connected = False
            await self._notify_connection_listeners(False)
            logging.error(f"接收 WebSocket 消息出错: {e}") # 使用 logging.error 替换 print，记录接收消息错误
            await self.connect() # 自动重连
        finally:
            logging.info("停止接收 WebSocket 消息。") # 添加日志：接收消息停止


    async def send(self, message):
        """发送消息到 WebSocket 服务端
        :param message: 要发送的消息内容
        """
        logging.debug("准备发送消息到 WebSocket 服务端...") # 添加 debug 日志：准备发送消息
        if self.connected:
            json_message = json.dumps({"type": "message", "data": message}, default=str)
            logging.debug(f"准备发送 JSON 消息: {json_message}")
            try:
                await self.websocket.send(json_message)
                logging.info(f"发送 JSON 消息: {json_message}") # 使用 logging.debug 替换 print，记录发送的 JSON 消息 (debug 级别)
            except Exception as e:
                logging.error(f"发送 WebSocket 消息失败: {e}") # 记录发送消息失败的错误
        else:
            logging.warning("WebSocket 连接未打开，无法发送消息。") # 使用 logging.warning 替换 print，提示未连接无法发送

    async def close(self):
        """关闭 WebSocket 连接"""
        logging.info("开始关闭 WebSocket 连接...") # 添加日志：关闭连接开始
        if self.connected:
            if self._heartbeat_task:
                self._stop_heartbeat()
            try:
                await self.websocket.close()
                self.connected = False
                await self._notify_connection_listeners(False)
                logging.info("WebSocket 连接已成功关闭。") # 使用 logging.info 替换 print，记录连接已关闭
            except Exception as e:
                logging.error(f"关闭 WebSocket 连接时发生错误: {e}") # 记录关闭连接错误
        else:
            logging.info("WebSocket 连接之前未打开，无需关闭。") # 添加日志：连接未打开，无需关闭
        logging.info("WebSocket 连接关闭操作完成。") # 添加日志：关闭连接操作完成

    def get_connection_status(self):
        """获取当前连接状态
        :return: True 表示已连接，False 表示未连接
        """
        logging.debug(f"获取 WebSocket 连接状态: {'已连接' if self.connected else '未连接'}") # 添加 debug 日志：获取连接状态
        return self.connected

    async def _notify_connection_listeners(self, connected):
        """通知所有连接状态监听器
        :param connected: 当前连接状态
        """
        logging.debug(f"通知连接状态监听器，当前连接状态: {'已连接' if connected else '未连接'}") # 添加 debug 日志：通知连接监听器
        for listener in self._connection_listeners:
            await listener(connected)

    async def _notify_message_listeners(self, message):
        """通知所有消息监听器
        :param message: 接收到的消息
        """
        logging.debug(f"通知消息监听器，接收到消息: {message}") # 添加 debug 日志：通知消息监听器
        for listener in self._message_listeners:
            await listener(message)

    def add_connection_listener(self, listener):
        """添加连接状态监听器
        :param listener: 监听器函数
        """
        logging.debug(f"添加连接状态监听器: {listener.__name__ if hasattr(listener, '__name__') else listener}") # 添加 debug 日志：添加连接监听器
        self._connection_listeners.append(listener)

    def add_message_listener(self, listener):
        """添加消息监听器
        :param listener: 监听器函数
        """
        logging.debug(f"添加消息监听器: {listener.__name__ if hasattr(listener, '__name__') else listener}") # 添加 debug 日志：添加消息监听器
        self._message_listeners.append(listener)

    async def _heartbeat(self):
        """定时发送 Ping 帧作为心跳"""
        logging.debug("心跳任务开始...") # 添加 debug 日志：心跳任务开始
        while self.connected:
            try:
                await self.websocket.ping()
                logging.debug("发送 WebSocket Ping 心跳帧") # 添加 debug 日志：发送心跳
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logging.warning(f"心跳失败: {e}") # 使用 logging.warning 替换 print，记录心跳失败
                break
        logging.debug("心跳任务结束。") # 添加 debug 日志：心跳任务结束

    def _start_heartbeat(self):
        """启动心跳任务"""
        logging.info(f"启动心跳任务，心跳间隔: {self.heartbeat_interval} 秒") # 添加日志：启动心跳任务
        self._heartbeat_task = asyncio.create_task(self._heartbeat())

    def _stop_heartbeat(self):
        """停止心跳任务"""
        logging.info("停止心跳任务。") # 添加日志：停止心跳任务
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

# 连接状态变化监听器
async def connection_status_changed(connected):
    """监听连接状态变化
    :param connected: True 表示已连接，False 表示已断开
    """
    status_str = '已连接' if connected else '已断开'
    logging.info(f"WebSocket 连接状态: {status_str}") # 使用 logging.info 替换 print，记录连接状态变化
    # print(f"连接状态: {'已连接' if connected else '已断开'}")

# 消息接收监听器
async def message_received(message):
    """处理接收到的消息
    :param message: 服务端发送的消息
    """
    logging.info(f"接收到 WebSocket 消息: {message}") # 使用 logging.info 替换 print，记录接收到的消息
    # print(f"接收到消息: {message}")
    try:
        json_data = json.loads(message)
        logging.debug(f"解析 JSON 消息结果 - 类型: {json_data.get('type')}, 数据: {json_data.get('data')}") # 添加 debug 日志：解析 JSON 结果
        # print(f"解析结果 - 类型: {json_data['type']}, 数据: {json_data['data']}")
        try:
            if json_data.get('type') == 'echo': # 使用 .get() 方法安全地访问 'type' 字段
                # 处理回应的数据ID
                id = json_data.get('data') # 使用 .get() 方法安全地访问 'data' 字段
                logging.debug(f"接收到 'echo' 类型消息，数据 ID: {id}") # 添加 debug 日志：接收到 echo 消息
                db = Database()
                # 查询id对应的数据
                db_data = db.box_case_search_by_id(id)
                logging.debug(f"查询数据库 box_case 结果: {db_data}") # 添加 debug 日志：数据库查询结果
                # print(f"查询到的数据库信息: {db_data}")
                # 修改is_line  将数据存储到历史中
                if db_data:  # 先检查是否查询到了数据
                    db_data['isLine'] = 1
                    logging.info(f"更新 box_case 数据 'isLine' 状态为 1，数据 ID: {id}，准备插入历史记录") # 添加日志：更新 isLine 状态
                    # print("存储历史记录")
                    db.box_case_history_insert_data(db_data)
                    logging.info(f"成功插入 box_case 历史记录，数据 ID: {id}") # 添加日志：插入历史记录成功
                    # 删除对应ID的数据
                    logging.info(f"准备删除 box_case 数据，数据 ID: {id}") # 添加日志：准备删除数据
                    # print("删除数据")
                    db.box_case_delete_by_id(id)
                    logging.info(f"成功删除 box_case 数据，数据 ID: {id}") # 添加日志：删除数据成功
                else:
                    logging.warning(f"未找到数据，数据 ID: {id}，可能数据已被删除或不存在。") # 添加 warning 日志：未找到数据
            elif json_data.get('type') == 'error':
                # 返回提示内容
                message = json_data.get('data')
                logging.error(f"数据上传异常: {message}")

        except Exception as e:
            logging.error(f"数据库处理出错: {e}, 消息内容: {message}") # 使用 logging.error 替换 print，记录数据库处理错误和消息内容
            # print(f"数据库处理出错: {e}")
    except json.JSONDecodeError:
        logging.warning(f"接收到的消息不是有效的 JSON 格式: {message}") # 使用 logging.warning 替换 print，记录 JSON 解析错误和消息内容
        # print("消息不是有效的 JSON 格式")

# 命令处理协程
async def handle_commands(client, command_queue):
    """处理用户输入的命令
    :param client: WebSocket 客户端实例
    :param command_queue: 命令队列
    """
    logging.info("命令处理协程已启动，等待用户输入命令...") # 添加日志：命令处理协程启动
    while True:
        command = await command_queue.get()
        logging.debug(f"接收到命令: {command}") # 添加 debug 日志：接收到命令
        if command == "exit":
            if client.get_connection_status():
                await client.close()
            logging.info("退出命令接收，命令处理协程结束。") # 添加日志：退出命令
            break
        elif command == "close":
            await client.close()
            logging.info("关闭 WebSocket 连接命令执行完成。") # 添加日志：关闭连接命令
        elif command.startswith("send:"):
            message = command[5:]
            await client.send(message)
            logging.info(f"发送消息命令执行完成，消息内容: {message}") # 添加日志：发送消息命令
        elif command == "status":
            status = client.get_connection_status()
            status_str = '已连接' if status else '已断开'
            logging.info(f"查询连接状态命令执行完成，当前连接状态: {status_str}") # 添加日志：查询状态命令
        else:
            logging.warning(f"接收到无效命令: {command}") # 使用 logging.warning 记录无效命令
        command_queue.task_done()

# 命令行输入线程
def command_line_thread(command_queue):
    """在单独线程中处理命令行输入
    :param command_queue: 用于传递命令的队列
    """
    logging.info("命令行输入线程已启动，等待用户输入...") # 添加日志：命令行线程启动
    while True:
        command = input("输入命令 (send/close/status/exit): ").lower()
        logging.debug(f"用户输入命令: {command}") # 添加 debug 日志：用户输入命令
        if command in ["close", "status", "exit"]:
            command_queue.put_nowait(command)
        elif command == "send":
            message = input("输入要发送的消息: ")
            command_queue.put_nowait(f"send:{message}")
            logging.debug(f"用户输入发送消息内容: {message}") # 添加 debug 日志：用户输入发送消息内容
        else:
            logging.warning(f"无效命令输入: {command}") # 使用 logging.warning 记录无效命令输入
        if command == "exit":
            logging.info("接收到 'exit' 命令，命令行输入线程即将退出。") # 添加日志：退出命令行线程
            break
    logging.info("命令行输入线程已退出。") # 添加日志：命令行线程退出

ws_client = None
# 启动 WebSocket 客户端的函数
def startWS(websocket_uri, heartbeat_interval=5):
    """启动 WebSocket 客户端并返回实例
    :param websocket_uri: WebSocket 服务端地址
    :param heartbeat_interval: 心跳间隔（秒），默认 5 秒
    :return: WebSocketClient 实例
    """
    logging.info(f"启动 WebSocket 客户端，WebSocket URI: {websocket_uri}, 心跳间隔: {heartbeat_interval} 秒") # 添加日志：启动 WebSocket 客户端
    client = WebSocketClient(websocket_uri, heartbeat_interval)

    # 添加默认监听器
    client.add_connection_listener(connection_status_changed)
    client.add_message_listener(message_received)
    logging.debug("添加默认连接状态监听器和消息监听器。") # 添加 debug 日志：添加监听器

    # 启动连接任务
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(client.connect(), loop=loop)
    global ws_client
    ws_client = client
    logging.debug("启动 WebSocket 连接任务到 asyncio 循环。") # 添加 debug 日志：启动连接任务
    logging.info("WebSocket 客户端启动完成，返回客户端实例。") # 添加日志：启动完成返回客户端实例
    return client

# 主协程
async def main():
    """程序主入口"""
    logging.info("程序主协程 main() 开始执行。") # 添加日志：主协程开始
    websocket_uri = "ws://localhost:34455/ws/websocket" # 服务端地址
    heartbeat_interval_sec = 5                       # 心跳间隔
    client = WebSocketClient(websocket_uri, heartbeat_interval=heartbeat_interval_sec)

    client.add_connection_listener(connection_status_changed)
    client.add_message_listener(message_received)
    logging.debug("在 main() 中添加连接状态监听器和消息监听器。") # 添加 debug 日志：main() 中添加监听器

    command_queue = asyncio.Queue() # 创建命令队列
    asyncio.create_task(client.connect()) # 启动 WebSocket 连接任务
    command_task = asyncio.create_task(handle_commands(client, command_queue)) # 启动命令处理任务
    logging.debug("在 main() 中启动 WebSocket 连接任务和命令处理任务。") # 添加 debug 日志：main() 中启动任务

    threading.Thread(target=command_line_thread, args=(command_queue,), daemon=True).start() # 启动命令行线程
    logging.debug("在 main() 中启动命令行输入线程。") # 添加 debug 日志：main() 中启动命令行线程
    await command_task # 等待命令处理完成
    logging.info("程序主协程 main() 执行完成，程序退出。") # 添加日志：主协程结束

if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s')
    asyncio.run(main()) # 运行主协程


# import asyncio
# from main import WS_CLIENT  # 导入全局 WS_CLIENT
#
# async def send_message(message):
#     """异步发送 WebSocket 消息
#     :param message: 要发送的消息内容
#     """
#     if WS_CLIENT:
#         await WS_CLIENT.send(message)
#     else:
#         print("WebSocket 客户端未初始化")
#
# def send_sync(message):
#     """同步发送 WebSocket 消息
#     :param message: 要发送的消息内容
#     """
#     if WS_CLIENT:
#         # 从 main.py 获取事件循环（假设 main 中定义了全局 LOOP）
#         from main import MainWindow
#         loop = MainWindow().loop  # 注意：这里需要实例化或通过其他方式获取 loop
#         asyncio.run_coroutine_threadsafe(send_message(message), loop)
#     else:
#         print("WebSocket 客户端未初始化")