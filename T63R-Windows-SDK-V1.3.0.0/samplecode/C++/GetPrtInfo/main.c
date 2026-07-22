#include <stdio.h>
#include <string.h>
#include <stdlib.h>


//if language is English, please define en_US
#ifdef en_US      
#include "en-US/DSTP2x.h"
#else
#include "DSTP2x.h"
#endif

#ifdef _WIN32
#include <Windows.h>
#endif

#define MAIN_STATUS_BEGIN 1
#define WARN_STATUS_BEGIN 1000
#define ERR_STATUS_BEGIN 2000

int main(int argc, char *argv[])
{
	char szResultInfo[1024] = { 0 }, szEnumList[4096] = { 0 }, szPrtFWVer[128] = { 0 }, szPrtSN[128] = { 0 }, szDesc[1024] = { 0 };
	int iEnumType = 1/*Enum Type*/, iResultInfoSize = sizeof(szResultInfo), iDevSize = sizeof(szEnumList), iDevNum = 0, iPrtFWVerSize = sizeof(szPrtFWVer), iPrtSNSize = sizeof(szPrtSN);
	int pMainStatus[8] = { 0 }, pWarning[8] = { 0 }, pError[8] = { 0 };
	int iIsReady = 0, iMainStatusNum = sizeof(pMainStatus), iWarningNum = sizeof(pWarning), iErrorNum = sizeof(pError), iDescLen = sizeof(szDesc);
	int nGroupIdx = 0;

	char pMainStatusDescGroup[][50] = {
		"Device idle", 	//1
		"Device busy"		, 	//2
		"Cache is not empty", 	//3
		"Cache is empty", 	//4
		"The panel is in the set state", 	//5
		"Label reading and writing completed", 	//6
		"The retry and invalidation process is in progress", 	//7
		"The make-up printing process is in progress", 	//8
		"RFID automatic verification in progress", 	//9
		"RFID custom command in progress", 	//10
		"No RFID module" 	//11
	};

	char pWarnStatusDescGroup[][50] = {
		"Paper is about to run out"  //1000
	};
	
	char pErrorStatusDescGroup[][50] = {
		"Label or black label positioning error", //2000
		"Paper jam", //2001
		"Paper tearing error", //2002
		"Lack of paper", //2003
		"Knife error", //2004
		"Paper loading error", //2005
		"Carbon tape error", //2006
		"Lifting the print head", //2007
		"Printing head overheating"		, //2008
		"EPC data missing in print data", //2009
		"RFID re printing failed", //2010
		"RFID calibration failed", //2011
		"RFID error", //2012
		"Pause or offline" //2013
	};
	
	unsigned int uiRet = 0;
	DEV_HDL devHdl = 0;

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

	//4.Get printer firmware version
	uiRet = DSTP2x_GetPrtFWVer(devHdl, szPrtFWVer, &iPrtFWVerSize);
	if (uiRet)
	{
		printf("DSTP2x_GetPrtFWVer error, error code:%d\n", uiRet);
		goto end;
	}
	printf("Printer firmware version:%s\n", szPrtFWVer);

	//5.Get printer serial number
	uiRet = DSTP2x_GetPrtSN(devHdl, szPrtSN, &iPrtSNSize);
	if (uiRet)
	{
		printf("DSTP2x_GetPrtSN error, error code:%d\n", uiRet);
		goto end;
	}
	printf("Printer serial number:%s\n", szPrtSN);

	//6.You can set it to English
	uiRet = DSTP2x_SetLibLang(1);
	if (uiRet)
	{
		printf("DSTP2x_SetLibLang error, error code:%d\n", uiRet);
		goto end;
	}

	//7.Get printer status
	uiRet = DSTP2x_GetPrtStatus(devHdl, &iIsReady, pMainStatus, &iMainStatusNum, pWarning, &iWarningNum, pError, &iErrorNum, szDesc, &iDescLen);
	if (uiRet)
	{
		printf("DSTP2x_GetPrtStatus error, error code:%d\n", uiRet);
		goto end;
	}
	else
	{
		printf("Main status: ");       //Get the main status
		for( nGroupIdx = 0 ; nGroupIdx < iMainStatusNum; nGroupIdx++)
		{
			int idx = pMainStatus[nGroupIdx] - MAIN_STATUS_BEGIN;
			printf("%s; ", pMainStatusDescGroup[idx]);
		}
		printf("\nWarning status: ");		//Get the warn status
		for( nGroupIdx = 0 ; nGroupIdx < iWarningNum; nGroupIdx++)
		{
			int idx = pWarning[nGroupIdx] - WARN_STATUS_BEGIN;
			printf("%s; ", pWarnStatusDescGroup[idx]);
		}
		printf("\nError status: ");			//Get the error status
		for( nGroupIdx = 0 ; nGroupIdx < iErrorNum; nGroupIdx++)
		{
			int idx = pError[nGroupIdx] - ERR_STATUS_BEGIN;
			printf("%s; ", pErrorStatusDescGroup[idx]);
		}
		
		printf("\nPrinter status: %s\n", szDesc);
	}
	
	//8.Disconnect the device
	uiRet = DSTP2x_DisconnDev(devHdl);
	if (uiRet)
	{
		printf("DSTP2x_DisconnDev error, error code:%d\n", uiRet);
		goto end;
	}
	printf("This example has been successfully demonstrated!\n");

end:
	//9.Clear dynamic library
	DSTP2x_Lib_Clear();
	getchar();
	return 0;
}