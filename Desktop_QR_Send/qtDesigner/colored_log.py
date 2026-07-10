import logging

class ColoredFormatter(logging.Formatter):
    """
    一个自定义的日志格式化器，为不同级别的日志消息添加颜色。
    """
    COLOR_CODES = {
        'DEBUG':    '\033[0;36m',  # Cyan
        'INFO':     '\033[0;32m',  # Green
        'WARNING':  '\033[0;33m',  # Yellow
        'ERROR':    '\033[0;31m',  # Red
        'CRITICAL': '\033[0;35m',  # Magenta
        'RESET':    '\033[0m'      # Reset color
    }

    def format(self, record):
        log_level_color = self.COLOR_CODES.get(record.levelname, self.COLOR_CODES['RESET'])
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s') # 你可以自定义你喜欢的格式
        formatted_message = formatter.format(record)
        return f"{log_level_color}{formatted_message}{self.COLOR_CODES['RESET']}"