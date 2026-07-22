
target_DrawPrint_RFID	= ./bin/linux/DrawPrint_RFID
c_main_DrawPrint_RFID	+= ./DrawPrint_RFID/main.c

target_GetPrtInfo	= ./bin/linux/GetPrtInfo
c_main_GetPrtInfo	+= ./GetPrtInfo/main.c

target_PdfPrint_RFID	= ./bin/linux/PdfPrint_RFID
c_main_PdfPrint_RFID	+= ./PdfPrint_RFID/main.c

target_PdfPrintOnly	= ./bin/linux/PdfPrintOnly
c_main_PdfPrintOnly	+= ./PdfPrintOnly/main.c

target_ReadTid_DrawPrint_RFID	= ./bin/linux/ReadTid_DrawPrint_RFID
c_main_ReadTid_DrawPrint_RFID	+= ./ReadTid_DrawPrint_RFID/main.c

target_ReadTid_PdfPrint_RFID	= ./bin/linux/ReadTid_PdfPrint_RFID
c_main_ReadTid_PdfPrint_RFID	+= ./ReadTid_PdfPrint_RFID/main.c

target_ReadTid_TemplatePrint_RFID	= ./bin/linux/ReadTid_TemplatePrint_RFID
c_main_ReadTid_TemplatePrint_RFID	+= ./ReadTid_TemplatePrint_RFID/main.c

target_TemplatePrint_RFID	= ./bin/linux/TemplatePrint_RFID
c_main_TemplatePrint_RFID	+= ./TemplatePrint_RFID/main.c

target_TemplatePrintOnly	= ./bin/linux/TemplatePrintOnly
c_main_TemplatePrintOnly	+= ./TemplatePrintOnly/main.c

target_TransDataDirectly	= ./bin/linux/TransDataDirectly
c_main_TransDataDirectly	+= ./TransDataDirectly/main.c

target_Barcode	= ./bin/linux/Barcode
c_main_Barcode	+= ./DrawPrintOnly/Barcode/main.c

target_Combination	= ./bin/linux/Combination
c_main_Combination	+= ./DrawPrintOnly/Combination/main.c

target_Line	= ./bin/linux/Line
c_main_Line	+= ./DrawPrintOnly/Line/main.c

target_Image	= ./bin/linux/Image
c_main_Image	+= ./DrawPrintOnly/Image/main.c

target_Text	= ./bin/linux/Text
c_main_Text	+= ./DrawPrintOnly/Text/main.c

target_Ellipse	= ./bin/linux/Ellipse
c_main_Ellipse	+= ./DrawPrintOnly/Ellipse/main.c

target_Rectangle	= ./bin/linux/Rectangle
c_main_Rectangle	+= ./DrawPrintOnly/Rectangle/main.c

target_RFIDLockPW = ./bin/linux/RFIDLockPW
c_main_RFIDLockPW += ./RFID_Lock_Pw/main.c

target_NetConnectDirectly = ./bin/linux/NetConnectDirectly
c_main_NetConnectDirectly += ./DirectConnection/NetConnectDirectly/main.c

target_SerialPortConnectDirectly = ./bin/linux/SerialPortConnectDirectly
c_main_SerialPortConnectDirectly += ./DirectConnection/SerialPortConnectDirectly/main.c

include_path += -I ../../include/ -I ./ 		
lib_path=-L ../../lib/ -lDSThermal

dump = -g
link = -pthread -ldl -Wl,-rpath=./
envs = -std=c++11

all : clean $(target_DrawPrint_RFID) $(target_GetPrtInfo) $(target_PdfPrint_RFID) $(target_PdfPrintOnly) $(target_ReadTid_DrawPrint_RFID) $(target_ReadTid_PdfPrint_RFID) $(target_ReadTid_TemplatePrint_RFID) $(target_TemplatePrint_RFID) $(target_TemplatePrintOnly) $(target_TransDataDirectly) $(target_Barcode) $(target_Combination) $(target_Image) $(target_Text) $(target_RFIDLockPW) $(target_SerialPortConnectDirectly) $(target_NetConnectDirectly) $(target_Line) $(target_Ellipse) $(target_Rectangle)
PHONY : all 

$(target_DrawPrint_RFID):$(c_main_DrawPrint_RFID)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_GetPrtInfo):$(c_main_GetPrtInfo)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_PdfPrint_RFID):$(c_main_PdfPrint_RFID)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_PdfPrintOnly):$(c_main_PdfPrintOnly)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_ReadTid_DrawPrint_RFID):$(c_main_ReadTid_DrawPrint_RFID)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_ReadTid_PdfPrint_RFID):$(c_main_ReadTid_PdfPrint_RFID)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_ReadTid_TemplatePrint_RFID):$(c_main_ReadTid_TemplatePrint_RFID)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_TemplatePrint_RFID):$(c_main_TemplatePrint_RFID)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_TemplatePrintOnly):$(c_main_TemplatePrintOnly)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_TransDataDirectly):$(c_main_TransDataDirectly)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_Barcode):$(c_main_Barcode)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_Combination):$(c_main_Combination)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_Image):$(c_main_Image)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_Text):$(c_main_Text)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_Ellipse):$(c_main_Ellipse)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_Rectangle):$(c_main_Rectangle)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_RFIDLockPW):$(c_main_RFIDLockPW)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_NetConnectDirectly):$(c_main_NetConnectDirectly)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_SerialPortConnectDirectly):$(c_main_SerialPortConnectDirectly)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)

$(target_Line):$(c_main_Line)
	$(CXX) $(dump) $(envs) $^ -o $@ $(include_path) $(lib_path) $(link)


clean:	
	mkdir -p ./bin/linux/	
	$(RM) $(target_DrawPrint_RFID) $(target_GetPrtInfo) $(target_PdfPrint_RFID) $(target_PdfPrintOnly) $(target_ReadTid_DrawPrint_RFID) $(target_ReadTid_PdfPrint_RFID) $(target_ReadTid_TemplatePrint_RFID) $(target_TemplatePrint_RFID) $(target_TemplatePrintOnly) $(target_TransDataDirectly) $(target_Barcode) $(target_Combination) $(target_Image) $(target_Text) $(target_RFIDLockPW) $(target_SerialPortConnectDirectly) $(target_NetConnectDirectly) $(target_Line) $(target_Ellipse) $(target_Rectangle)
	$(RM) ./*.o
