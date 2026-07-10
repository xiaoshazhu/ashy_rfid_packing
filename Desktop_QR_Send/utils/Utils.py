# Utils.py
import re
import logging # 导入 logging 模块


# 截取id
def extract_path_after_domain(url_string):
    logging.debug(f"开始执行 extract_path_after_domain 函数， URL: {url_string}") # 添加 debug 日志：函数开始和输入参数
    """
    从 URL 字符串中截取 '.com/' 或 '.cn/' 后面的路径部分。

    :param url_string:  URL 字符串，例如 "https://g.yiknet.com/LoY8T5yZhpaWLIM9T58="
    :return:  '.com/' 或 '.cn/' 后面的路径部分，如果未找到，则返回 None。
    """
    if not isinstance(url_string, str):
        logging.warning(f"输入 URL 不是字符串类型，返回 None。 输入类型: {type(url_string)}") # 添加 warning 日志：输入不是字符串
        return None  # 如果输入不是字符串，返回 None

    # 优先匹配 .com/
    com_match = re.search(r'\.com/(.*)', url_string)
    if com_match:
        path_com = com_match.group(1) # 返回 .com/ 后面的内容
        logging.debug(f"找到 '.com/' 匹配，路径: {path_com}") # 添加 debug 日志：.com/ 匹配成功
        return path_com

    # 如果没有找到 .com/，则匹配 .cn/
    cn_match = re.search(r'\.cn/(.*)', url_string)
    if cn_match:
        path_cn = cn_match.group(1) # 返回 .cn/ 后面的内容
        logging.debug(f"找到 '.cn/' 匹配，路径: {path_cn}") # 添加 debug 日志：.cn/ 匹配成功
        return path_cn

    logging.debug(f"未找到 '.com/' 或 '.cn/' 匹配，返回原始 URL 字符串: {url_string}") # 添加 debug 日志：没有找到匹配
    return url_string  # 如果 .com/ 和 .cn/ 都没有找到，返回 url_string


if __name__ == '__main__':
    #  测试 extract_utils.py 的日志功能
    import logging

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s')

    test_urls = [
        "https://g.yiknet.com/LoY8T5yZhpaWLIM9T58=",
        "http://www.example.cn/path/to/resource",
        "https://www.example.org/another/path",
        12345, #  非字符串类型的输入
        None,  # None 输入
        "纯文本，不包含域名" #  不包含域名和 .com/.cn 的字符串
    ]

    for url in test_urls:
        extracted_path = extract_path_after_domain(url)
        logging.info(f"URL: '{url}', 截取路径: '{extracted_path}'") # 使用 logging.info 记录测试结果


    print("请检查 logs 目录下的日志文件 app_log.log， 确认 extract_utils.py 的日志输出是否正常。")
    print("请检查控制台输出，  确认测试代码的 info/debug/warning 日志是否正常输出。")
    print("注意： 测试代码会循环测试不同的 URL 示例， 并输出 info 级别的测试结果日志。")