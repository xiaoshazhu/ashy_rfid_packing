# printUtils
import win32ui
from PIL import Image, ImageDraw, ImageFont, ImageWin
import code128

def print_barcode(case_code, printer_name, page_width, page_height, page_num=1, scale_factor=1.0, left_margin=0, top_margin=0):
    """
    打印条形码。

    Args:
        case_code (str): 条形码内容。
        printer_name (str): 打印机名称。
        page_width (int): 打印内容的原始宽度。
        page_height (int): 打印内容的原始高度。
        page_num (int, optional): 打印份数，默认为 1。
        scale_factor (float, optional): 缩放比例，默认为 1.0。
        left_margin (int, optional): 左边距，默认为 0。
        top_margin (int, optional): 上边距，默认为 0。
    """
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s')

    logging.info(f"开始打印箱码: {case_code}, 打印机: {printer_name}, 内容宽度: {page_width}, 内容高度: {page_height}, 打印份数: {page_num}, 缩放比例: {scale_factor}, 左边距: {left_margin}, 上边距: {top_margin}")

    for i in range(page_num):
        logging.info(f"开始打印第 {i + 1} 份...")
        # 生成原始条形码图像，尝试不使用 options 设置 quiet zones
        barcode_image = code128.image(case_code)

        original_barcode_width = barcode_image.width
        original_barcode_height = barcode_image.height

        # 设置文本高度
        text_height = 35
        font = ImageFont.load_default(text_height)
        bbox = ImageDraw.Draw(Image.new('RGB', (1, 1), 'white')).textbbox((0, 0), case_code, font=font)
        text_width = bbox[2] - bbox[0]

        # 创建原始大小的图像
        image = Image.new('RGB', (page_width, page_height), 'white')
        draw = ImageDraw.Draw(image)

        # 计算条形码在画布上的居中位置
        barcode_x = (page_width - original_barcode_width) // 2
        barcode_y = (page_height - original_barcode_height - text_height - 5) // 2

        # 将条形码粘贴到画布上
        image.paste(barcode_image, (barcode_x, barcode_y))

        # 计算文本在画布上的居中位置 (位于条形码下方)
        text_x = (page_width - text_width) // 2
        text_y = barcode_y + original_barcode_height + 5

        # 在图像上绘制文本
        draw.text((text_x, text_y), case_code, font=font, fill='black')

        # 计算缩放后的尺寸
        scaled_width = int(page_width * scale_factor)
        scaled_height = int(page_height * scale_factor)

        # 缩放整个图像
        scaled_image = image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

        # 打印图像
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)

        hDC.StartDoc(case_code) # 使用 case_code 作为文档名，而不是文件路径
        hDC.StartPage()

        dib = ImageWin.Dib(scaled_image)
        # 使用 left_margin 和 top_margin 设置打印的起始位置
        dib.draw(hDC.GetHandleOutput(), (left_margin, top_margin, left_margin + scaled_width, top_margin + scaled_height))

        hDC.EndPage()
        hDC.EndDoc()
        del hDC

        logging.info(f"箱码 '{case_code}' 第 {i + 1} 份打印完成，打印机: {printer_name}")

    logging.info(f"箱码 '{case_code}' 共打印 {page_num} 份，打印机: {printer_name}")

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s')

    test_case_code = "1234567890"
    test_printer_name = "HPRT N31C" # 请替换成您实际的测试打印机名称
    test_page_width = 500  # 设置生成内容的原始宽度
    test_page_height = 400 # 设置生成内容的原始高度
    test_page_num = 2   # 设置打印份数

    print_barcode(test_case_code, test_printer_name, test_page_width, test_page_height, test_page_num)