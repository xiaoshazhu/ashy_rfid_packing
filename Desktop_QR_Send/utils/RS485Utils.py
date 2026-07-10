# RS485Utils.py
import serial
import time
import logging # 导入 logging 模块


class RS485Utils:
    def __init__(self, port, baudrate, home_instance):
        logging.info(f"RS485Utils 初始化，端口: {port}, 波特率: {baudrate}") # 添加日志：类初始化
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.home_instance = home_instance  # 添加一个home_instance属性
        logging.debug("RS485Utils 对象创建完成，等待连接。") # 添加 debug 日志：对象创建完成

    def connect(self):
        logging.info(f"尝试连接到 RS485 串口，端口: {self.port}, 波特率: {self.baudrate}") # 添加日志：连接开始
        # 建立连接
        try:
            self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=1)
            logging.info(f"成功连接到串口: {self.port}") # 添加日志：连接成功
        except serial.SerialException as e:
            logging.error(f"连接串口失败: {self.port}, 错误信息: {e}") # 使用 logging.error 替换 print，记录错误信息
            # 可以选择在这里抛出异常或者进行其他错误处理
            raise #  选择重新抛出异常，让上层调用者处理

    def listen(self):
        logging.info("开始监听 RS485 串口数据...") # 添加日志：监听开始
        # 监听数据
        try:
            while True:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting) # 读取接收到的字节数据
                    hex_data = data.hex() # 将字节数据转换为十六进制字符串
                    logging.debug(f"接收到原始数据 (Hex): {hex_data}") # 使用 logging.debug 替换 print，记录接收到的原始数据 (debug 级别)
                    self.process_data(hex_data) # 将十六进制字符串传递给 process_data
                time.sleep(0.1)
        except serial.SerialException as e:
            logging.error(f"串行通信错误: {e}") # 使用 logging.error 替换 print，记录串行通信错误
        except Exception as e: # 捕获其他可能发生的异常
            logging.error(f"监听线程发生未知错误: {e}") # 记录未知错误
        finally:
            logging.info("停止监听 RS485 串口数据。") # 添加日志：监听停止


    def process_data(self, raw_data):
        logging.debug(f"开始处理接收到的数据: {raw_data}") # 添加 debug 日志：数据处理开始
        # 处理接收到的数据
        data_list = raw_data.split('2c') # 使用 '2c' (逗号的十六进制表示) 分割数据
        for data in data_list:
            if not data: #  跳过空数据
                continue
            logging.debug(f"处理数据段: {data}") # 添加 debug 日志：处理数据段
            # 判断是哪个设备，走哪个协议
            if len(data) == 6 and data[:2] == 'aa':
                # 开关采集器
                # 判断是哪个门，是什么开关状态
                door_number = int(data[2:4], 16)  # 门的编号,  从十六进制解析为十进制
                # true表示按压了，false表示释放了
                is_press = data[4:] == '01' #  直接比较十六进制字符串
                logging.info(f"开关{door_number}被{'按下' if is_press else '释放'}") # 使用 logging.info 替换 print，并使用更友好的 '按下'/'释放' 日志

                # 对按钮的触发进行处理
                if door_number == 1 and is_press == True:
                    # 拍照识别
                    # 增加操作延迟
                    time.sleep(0.5)  # 睡眠0.5秒
                    logging.info("触发按钮1 (拍照识别), 模拟点击 '手动识别' 按钮") # 添加日志：按钮1触发
                    self.home_instance.main_window.button_again.click()  # 模拟点击按钮
                # 光感触发复位
                if door_number == 1 and is_press == False:
                    # 3 开关被抬起
                    # 还原摄像机状态
                    # 还原初始化
                    logging.info("触发按钮1 (光感复位), 模拟点击 '初始化' 按钮") # 添加日志：按钮1抬起触发复位
                    self.home_instance.main_window.button_cancel.click()  # 模拟点击按钮
                # 按钮2被按下且抬起 (注意： 这里条件是 `is_press == False`,  和注释 “按钮2被按下且抬起” 一致)
                if door_number == 2 and is_press == False:
                    # 数据录入
                    logging.info("触发按钮2 (数据录入), 模拟点击 '确认录入' 按钮") # 添加日志：按钮2触发数据录入
                    self.home_instance.main_window.button_ok.click()  # 模拟点击按钮
                # 按钮3被按下且抬起 (注意： 这里条件是 `is_press == True`,  和注释 “按钮3被按下且抬起” 不一致，  按照代码逻辑 “按钮3被按下 重新识别” 理解)
                if door_number == 3 and is_press == True: #  修改条件为 `is_press == True` 以匹配注释 "按钮3被按下 重新识别"
                    # 3 开关被按下 重新识别
                    # self.home_instance.on_button_cancel_clicked()  # 还原初始化
                    # time.sleep(0.5)  # 睡眠0.5秒
                    logging.info("触发按钮3 (重新识别), 模拟点击 '手动识别' 按钮") # 添加日志：按钮3触发重新识别
                    self.home_instance.main_window.button_again.click()  # 模拟点击按钮
                # 按钮4被按下且抬起 (注意： 这里条件是 `is_press == False`,  和注释 “按钮4被按下且抬起” 一致)
                if door_number == 4 and is_press == False:
                    # 正在打印
                    logging.info("触发按钮4 (正在打印), 模拟点击 '打印箱码' 按钮") # 添加日志：按钮4触发打印
                    self.home_instance.main_window.button_print.click()  # 模拟点击按钮
            else:
                logging.debug(f"接收到未知数据或非开关采集器数据: {data}") # 添加 debug 日志：未知数据

        logging.debug("数据处理完成。") # 添加 debug 日志：数据处理完成


    def send_data(self, hex_data):
        logging.info(f"发送数据 (Hex): {hex_data}") # 添加日志：数据发送开始
        # 数据发送
        if self.ser and self.ser.is_open:
            try:
                data = bytes.fromhex(hex_data)
                self.ser.write(data)
                logging.debug(f"数据发送成功: {hex_data}") # 添加 debug 日志：数据发送成功
            except serial.SerialException as e:
                logging.error(f"串行端口发送数据失败: {e}") # 使用 logging.error 替换 print，记录发送数据失败错误
        else:
            logging.warning("串行端口未打开或未连接，无法发送数据。") # 使用 logging.warning 替换 print，提示端口未打开

    def close(self):
        logging.info("关闭 RS485 串口连接...") # 添加日志：关闭连接开始
        # 关闭连接
        if self.ser:
            self.ser.close()
            self.ser = None
            logging.info("串行连接已关闭。") # 使用 logging.info 替换 print，提示连接已关闭
        else:
            logging.info("串行连接之前未打开，无需关闭。") # 添加日志：连接未打开，无需关闭

# 使用示例

# if __name__ == "__main__":
#     rs485 = RS485Utils(port='COM100', baudrate=9600)
#     rs485.connect()
#     rs485.send_data('01 03 00 00 00 01 84 0A') # 发送示例数据
#     try:
#         rs485.listen() # 开始监听
#     except KeyboardInterrupt:
#     rs485.close() # 关闭连接