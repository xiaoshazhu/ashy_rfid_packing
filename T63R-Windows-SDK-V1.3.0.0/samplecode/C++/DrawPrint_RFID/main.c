#include <stdio.h>
#include <string.h>
#include <stdlib.h>

//if language is English, please define en_US
#ifdef en_US      
#include "en-US/DSTP2x.h"
#else
#include "DSTP2x.h"
#endif

int main(int argc, char *argv[])
{
	char szResultInfo[1024] = { 0 }, szEnumList[4096] = { 0 }, szOutRFID[128] = { 0 };
	int iEnumType = 1/*Enum type*/, iDevSize = sizeof(szEnumList), iDevNum = 0, iResultInfoSize = sizeof(szResultInfo), iOutRFIDSize = sizeof(szOutRFID);
	const char *szEPCData = "ABC123"/*EPC data */, *szUSERData = "123ABC"/*USER data */;
	unsigned int uiRet = 0;
	DEV_HDL devHdl = 0;
	LC_HDL labelHdl = 0;

	//1.Initialize the Library.
	uiRet = DSTP2x_Lib_Init(0, 0, szResultInfo, &iResultInfoSize);
	if (uiRet)
	{
		printf("DSTP2x_Lib_Init error, error code:%d\n", uiRet);
		getchar();
		return uiRet;
	}

	//2.Enum printer  iEnumType: 1->USB 2->TCP
	uiRet = DSTP2x_EnumDev(iEnumType, szEnumList, &iDevSize, &iDevNum);
	if (uiRet)
	{
		printf("DSTP2x_EnumDev error, error code:%d\n", uiRet);
		goto end;
	}

	//3.Connect the printer
	uiRet = DSTP2x_ConnEnumeratedDev(szEnumList, &devHdl);
	if (uiRet)
	{
		printf("DSTP2x_ConnEnumeratedDev error, error code:%d\n", uiRet);
		goto end;
	}

	//1-203dpi, 2-300dpi, 3-600dpi
	uiRet = DSTP2x_SetImgDpi(devHdl, 1);
	if (uiRet)
	{
		printf("DSTP2x_SetImgDpi error, error code:%d\n", uiRet);
		goto end;
	}

	//1-ZPL, 2-TSPL, 3-ESCPOS
	uiRet = DSTP2x_SetPrnEmulation(devHdl, 1);
	if (uiRet)
	{
		printf("DSTP2x_SetPrnEmulation error, error code:%d\n", uiRet);
		goto end;
	}

	//4.Create label context
	uiRet = DSTP2x_CreateLabelContext(100, 50, &labelHdl);
	if (uiRet)
	{
		printf("DSTP2x_CreateLabelContext error, error code:%d\n", uiRet);
		goto end;
	}

	// 0-print, 1-generate prn file, 2-generate preview image
	uiRet = DSTP2x_SetLcPrnMode(labelHdl, 0);
	if (uiRet)
	{
		printf("DSTP2x_SetLcPrnMode error, error code:%d\n", uiRet);
		goto end;
	}

	//5.Draw barcode
	uiRet = DSTP2x_Lbl_DrawBarCode(labelHdl, 0, 0, 40, 30, 20, "123456");//data must be utf-8
	if (uiRet)
	{
		printf("DSTP2x_Lbl_DrawBarCode error, error code:%d\n", uiRet);
		goto end;
	}

	//6.Write EPC data
	uiRet = DSTP2x_LcRfid_SetData(labelHdl, 1, 1, szEPCData, strlen(szEPCData));
	if (uiRet)
	{
		printf("Rfid set EPC data error, error code:%d\n", uiRet);
		goto end;
	}

	//Write USER data
	uiRet = DSTP2x_LcRfid_SetData(labelHdl, 2, 1, szUSERData, strlen(szUSERData));
	if (uiRet)
	{
		printf("Rfid set USER data error, error code:%d\n", uiRet);
		goto end;
	}
	printf("Write EPC data:%s\n", szEPCData);
	printf("Write USER data:%s\n", szUSERData);


	//7.Print label content and read RFID data
	uiRet = DSTP2x_PrintLc(devHdl, labelHdl, 0, 0, 7, szOutRFID, &iOutRFIDSize);
	if (uiRet)
	{
		printf("DSTP2x_PrintLc error, error code:%d\n", uiRet);
		goto end;
	}
	printf("Read RFID data:%s\n", szOutRFID);

	//8.Delete the handle of label
	uiRet = DSTP2x_DeleteLabelContext(labelHdl);
	if(uiRet)
	{
		printf("DSTP2x_DeleteLabelContext error, error code:%d\n", uiRet);
		goto end;
	}

	//9.Disconnect the device
	uiRet = DSTP2x_DisconnDev(devHdl);
	if(uiRet)
	{
		printf("DSTP2x_DisconnDev error, error code:%d\n", uiRet);
		goto end;
	}
	printf("This example has been successfully demonstrated!\n");

end:
	
	//10.Clear dynamic library
	DSTP2x_Lib_Clear();
	getchar();
	return 0;
}