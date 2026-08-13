# config.py
import json
import os
import logging  # 导入 logging 模块

# 初始化CONFIG_DATA字典
CONFIG_DATA = {
    'combobox_printSelect': None,  # 打印机
    'combobox_comSelect': None,  # 串口
    'edit_service': None,  # 服务器地址
    'edit_max_jian': None,  # 一捆数量
    'edit_max_xiang': None,  # 一箱数量
    'edit_min_x': None,  # X轴起始
    'edit_max_x': None,  # X轴截至
    'edit_min_y': None,  # Y轴起始
    'edit_max_y': None,  # Y轴截至
    'edit_page_width': None,  # 打印机纸张的宽度
    'edit_page_height': None,  # 打印机纸张的高度
    'edit_page_num': None,  # 打印份数
    'pageData': None,#页面数据
    'caseData':None, #盒码
    'caseCode':None #箱码
}

def setConfig(data):
    global CONFIG_DATA
    try:
        for key, value in data.items():
            CONFIG_DATA[key] = value
        # 将CONFIG_DATA的参数存储到本地文件config.json中
        with open('config.json', 'w', encoding='utf-8') as config_file:
            json.dump(CONFIG_DATA, config_file, indent=4, ensure_ascii=False)
        logging.info("配置已保存到文件 config.json") # 使用 logging.info 记录配置保存事件
    except Exception as e:
        logging.error(f"无法保存配置到文件: {e}") # 使用 logging.error 替换 print
        # 这里可以添加更多的错误处理逻辑，例如显示错误消息给用户

def loadConfig():
    global CONFIG_DATA
    # 判断本地是否存储了config文件
    if os.path.exists('config.json'):
        try:
            # 如果有config文件那么将文件内的参数存储到CONFIG_DATA
            with open('config.json', 'r', encoding='utf-8-sig') as config_file:
                CONFIG_DATA.update(json.load(config_file))
            logging.info("成功加载配置文件 config.json") # 使用 logging.info 记录配置文件加载成功事件
        except json.JSONDecodeError as e:
            logging.error(f"配置文件格式错误: {e}") # 使用 logging.error 替换 print
            # 这里可以添加代码来处理配置文件格式错误的情况
        except Exception as e:
            logging.error(f"无法读取配置文件: {e}") # 使用 logging.error 替换 print
            # 这里可以添加更多的错误处理逻辑
    else:
        logging.warning("未找到配置文件 config.json，将使用默认配置。") # 使用 logging.warning 替换 print
        # 如果没有config文件，使用默认配置

if __name__ == '__main__':
    #  测试 config.py 的日志功能
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s')

    test_config_data = {
        'combobox_printSelect': '打印机1',
        'combobox_comSelect': 'COM3',
        'edit_service': 'ws://localhost:8080',
        'edit_max_jian': '10',
        'edit_max_xiang': '100',
        'edit_min_x': '0',
        'edit_max_x': '100',
        'edit_min_y': '0',
        'edit_max_y': '100',
        'edit_page_width': '210',
        'edit_page_height': '297',
        'edit_page_num': '2',
        'pageData': {},
        'caseData': {},
        'caseCode': None
    }

    setConfig(test_config_data) # 保存配置
    loadConfig() # 加载配置

    print("请检查 logs 目录下的日志文件 app_log.log，确认 config.py 的日志输出是否正常。")