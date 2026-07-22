中文说明：
===============================================================================
	C++示例代码目录概述
===============================================================================
本目录为C++调C接口的功能调用，提供以下示例：
1. GetPrtInfo：获取打印机信息（版本号，状态等）。
 
2. DrawPrintOnly：绘图套打，包含文本，条码，图片，线段以及组合打。
 
3. PdfPrintOnly：PDF打印。
 
4. TemplatePrintOnly：模板打印。
 
5. DrawPrint_RFID：绘图套打与RFID结合。
 
6. PdfPrint_RFID：PDF打印与RFID结合。
 
7. TemplatePrint_RFID：模板打印与RFID结合。
 
8. ReadTid_DrawPrint_RFID：先读TID，绘图套打与RFID结合。
 
9. ReadTid_PdfPrint_RFID：先读TID，PDF打印与RFID结合。
 
10.ReadTid_TemplatePrint_RFID：先读TID，模板打印与RFID结合。

11.RFID_Lock_Pw：RFID动态锁定，加密等相关操作。

12.TransDataDirectly：数据直传打印机示例。

13.DirectConnection: 通讯直连示例，包含网口和串口。

===============================================================================
Windows使用方法：
1、双击运行 win_copy_dependent.bat
2、双击运行sln项目文件（需安装Microsoft Visual Studio 2010）
3、编译运行示例程序
4、编译完成后,需要把SDK包根目录下的lib文件夹里的主动态库及相关依赖文件复制到程序生产目录下即可执行

Linux使用方法：
1、打开Linux终端，运行 linux_copy_dependent.sh
2、输入命令 make 编译示例程序;
3、编译完成后会生成bin目录，把SDK包根目录下的lib文件夹里的主动态库及相关依赖文件复制到该目录下；
4、打开功能文件夹，并用终端命令运行里面的执行程序；
===============================================================================



EN Description:
===============================================================================
Overview of C++Example Code Catalog
===============================================================================
This directory provides the following examples of C++API function calls:
1. GetPrtInfo: Retrieve printer information (version number, status, etc.).
 
2. DrawPrintOnly: Drawing set printing, including text, barcode, image, line and combination printing.
 
3. PdfPrintOnly: PDF printing.
 
4. TemplatePrintOnly: Template printing.
 
5. DrawPrint_RFID: Combining drawing kit printing with RFID.
 
6. PdfPrint_RFID: Combining PDF printing with RFID.
 
7. TemplatePrint_RFID: Template printing combined with RFID.
 
8. ReadTid_DrawPrint_RFID: Read the TID first, and combine the drawing kit with RFID.
 
9. ReadTid_PdfPrint_RFID: Read TID first, combine PDF printing with RFID.
 
10. ReadTid_TemplatePrint_RFID: Read TID first, and combine template printing with RFID.

11. RFID_Lock_Pw：RFID dynamic locking, encryption and other related operations.

12. TransDataDirectly：Example of data direct transfer printer.

13. DirectConnection: Communication direct connection example, including network and serial port.
===============================================================================
Windows usage method:
1. Double click to run the win_copy_dependent.bat
2. Double click to run the SLN project file (requires installation of Microsoft Visual Studio 2010)
3. Compile and run the sample program
4. After compilation, it is necessary to copy the active state library and related dependency files from the lib folder in the root directory of the SDK package to the production directory of the program for execution

Linux usage method:
1. Open the Linux terminal and enter the command 'linux_copy_dependent.sh'
2. enter the command 'make' to compile the sample program;
3. After compilation, a bin directory will be generated, and the active state library and related dependency files in the lib folder of the SDK package root directory will be copied to this directory;
4. Open the function folder and run the executing program inside using terminal commands;
===============================================================================