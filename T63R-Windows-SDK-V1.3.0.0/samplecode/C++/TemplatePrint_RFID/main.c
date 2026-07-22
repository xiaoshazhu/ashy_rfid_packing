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
	char szResultInfo[1024] = { 0 }, szEnumList[4096] = { 0 }, szTID[128] = { 0 }, szOutRFID[128] = { 0 };
	int iEnumType = 1/*Enum Type*/, iDevSize = sizeof(szEnumList), iDevNum = 0, iResultInfoSize = sizeof(szResultInfo), iTIDSize = sizeof(szTID), iOutRFIDSize = sizeof(szOutRFID);
	unsigned int uiRet = 0;
	const char *szEPCData = "ABC123"/*EPC data */, *szUSERData = "123ABC"/*USER data */;

#if defined(_MSC_VER)
	const char *sztemplatesFile = "../../../TemplatePrint_RFID/templateRFID.dlt";
#else
	const char *sztemplatesFile = "./templateRFID.dlt";
#endif

	DEV_HDL devHdl = 0;
	LABEL_TEMP_HDL labelTempHdl = 0;

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

	//Set emulation. 1-ZPL, 2-TSPL, 3-ESCPOS
	uiRet = DSTP2x_SetPrnEmulation(devHdl, 1); //ZPL
	if(uiRet)
	{
		printf("DSTP2x_SetPrnEmulation error, error code:%d\n", uiRet);
		goto end;
	}

	//4.Load label templates
	uiRet = DSTP2x_LoadLabelTmpl(sztemplatesFile, &labelTempHdl);
	if (uiRet)
	{
		printf("DSTP2x_LoadLabelTmpl error, error code:%d\n", uiRet);
		goto end;
	}

	//5.Set the print mode. 0-print, 1-generate the prn file, 2-generate the preview image.
	uiRet = DSTP2x_SetTmplPrnMode(labelTempHdl, 0); //set print mode
	if (uiRet)
	{
		printf("DSTP2x_SetTmplPrnMode error, error code:%d\n", uiRet);
		goto end;
	}

	//6.Set the print data in template.
	uiRet = DSTP2x_SetTmplPrnData(labelTempHdl, "Text-01", "56789VWXYZ"); //The data must be utf-8
	if (uiRet)
	{
		printf("DSTP2x_SetTmplPrnData error, error code:%d\n", uiRet);
		goto end;
	}

	//7.Set the RFID data.
	uiRet = DSTP2x_SetTmplRFIDData(labelTempHdl, "EPC-01", szEPCData, strlen(szEPCData));
	if (uiRet)
	{
		printf("DSTP2x_SetTmplRFIDData error, error code:%d\n", uiRet);
		goto end;
	}

	uiRet = DSTP2x_SetTmplRFIDData(labelTempHdl, "USER-01", szUSERData, strlen(szUSERData));
	if (uiRet)
	{
		printf("DSTP2x_SetTmplRFIDData error, error code:%d\n", uiRet);
		goto end;
	}

	//8.Print label templates and read RFID
	uiRet = DSTP2x_PrintTmpl(devHdl, labelTempHdl, NULL, NULL, szOutRFID, &iOutRFIDSize);
	if (uiRet)
	{
		printf("DSTP2x_PrintTmpl error, error code:%d\n", uiRet);
		goto end;
	}
	printf("Read RFID data:%s\n", szOutRFID);

	//9.Delete label templates
	uiRet = DSTP2x_DeleteTmpl(labelTempHdl);
	if (uiRet)
	{
		printf("DSTP2x_DeleteTmpl error, error code:%d\n", uiRet);
		goto end;
	}

	//10.Disconnect the device
	uiRet = DSTP2x_DisconnDev(devHdl);
	if (uiRet)
	{
		printf("DSTP2x_DisconnDev error, error code:%d\n", uiRet);
		goto end;
	}

	printf("This example has been successfully demonstrated!\n");

end:
	
	//11.Clear dynamic library
	DSTP2x_Lib_Clear();
	getchar();
	return 0;
}