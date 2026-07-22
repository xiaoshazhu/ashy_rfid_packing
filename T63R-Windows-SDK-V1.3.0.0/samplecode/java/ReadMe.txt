===============================================================================
	Java示例代码目录概述
===============================================================================
DSTP2xDemo为示例代码目录,里面代码主要为cApiDemo,接口调用依赖DSTP2xLib,其中里面的代码为传统C语言接口的调用示例。

DSTP2xLib为JNA接口文件,主要用途为加载所需dll/so文件,并对调用c/c++接口作了一层封装

------------------------------------------------------------------------------------------------------------------------------------
目录下提供以下功能调用示例

1. GetPrtInfo：获取打印机信息

2. drawPrintOnly：绘图打印相关
  2.1 Text 文字打印
  2.2 Barcode 一维码与二维码打印
  2.3 Image 图片打印
  2.4 Combination 组合打印

3.DrawPrintAndRFID:绘图打印同时写入并读取RFID

4.Pdf:Pdf打印

5.PdfAndRFID:Pdf打印同时写入并读取RFID

6.TemplatePrint:模板打印

7.TemplatePrintAndRFID:模板打印同事写入并读取RFID

8.ReadTidAndDrawPrintAndRFID:先读Tid,后绘图打印同时写入并读取RFID

9.ReadTidAndTemplatePrintAndRFID:先读Tid,后模板打印同时写入并读取RFID

10.ReadTidAndPdfPrintAndRFID:先读Tid,后Pdf打印同时写入并读取RFID

11.RFID_Lock_Pw：RFID动态锁定，加密等相关操作

12.TransDataDirectly：数据直传打印机示例。

===============================================================================
使用方法：
1、双击运行用idea运行pom.xml项目文件/或者打开idea,在idea内打开java文件夹（需安装idea）
2、运行示例程序(任意一个xxxSample文件都可直接运行)
===============================================================================