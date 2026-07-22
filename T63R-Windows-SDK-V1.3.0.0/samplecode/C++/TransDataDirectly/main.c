#include <stdio.h>
#include <string.h>
#include <stdlib.h>

//if language is English, please define en_US
#ifdef en_US      
#include "en-US/DSTP2x.h"
#else
#include "DSTP2x.h"
#endif

int hex2bin(const char *hex, int len, char *out)
{
	int i; char h, l;
	int iout = (len / 2); out[iout] = 0;
	for (i = 0; i < len; i += 2) {
		h = hex[i]; l = hex[i + 1];
		if ((h >= '0') && (h <= '9')) { h -= 48; }
		else if (((h &= 0xdf) >= 'A') && (h <= 'F')) { h -= 55; }
		if ((l >= '0') && (l <= '9')) { l -= 48; }
		else if (((l &= 0xdf) >= 'A') && (l <= 'F')) { l -= 55; }
		out[i / 2] = (h * 16 + l);
	}
	return iout;
}


int main(int argc, char *argv[])
{
	char szResultInfo[1024] = { 0 }, szEnumList[4096] = { 0 }, szOutRFID[128] = { 0 };
	int iEnumType = 1/*Enum type*/, iDevSize = sizeof(szEnumList), iDevNum = 0, iResultInfoSize = sizeof(szResultInfo), iOutRFIDSize = sizeof(szOutRFID);

	//1-ZPL, 2-TSPL, 3-ESCPOS
	int iEmulationType = 1; 

	char szEmulationPaths[][500] = {
		/***************ZPL*******************/
		"^XA^PW600^LL200^SEE:GB18030.DAT^CI26^CWL,E:simsun.fnt^FO0,10^ALN,40,40^FD Print Test LABEL^FS^XZ", 
		/**************TSPL******************/
		"CLS\r\nSIZE 4,1\r\nTEXT 110,50,\"3\",0,1,1,\"Print Test LABEL\"\r\nPRINT 1\r\n", 
		/**************ESCPOS**************/
		"1b401c261d21001b4d001b2d001b45005072696E742054657374204C4142454C0a1d564100"};

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

	//4.According the emulation to transfer data
	if(iEmulationType == 3)
	{
		char pOut[500] ={0}; 
		int pOutSize = hex2bin(szEmulationPaths[iEmulationType - 1], strlen(szEmulationPaths[iEmulationType - 1]), pOut);
		uiRet = DSTP2x_TransRecvData(devHdl, pOut, pOutSize, 0, 0);
	}
	else
		uiRet = DSTP2x_TransRecvData(devHdl, szEmulationPaths[iEmulationType - 1], strlen(szEmulationPaths[iEmulationType - 1]), 0, 0);

	if(uiRet)
	{
		printf("DSTP2x_TransRecvData error, error code:%d\n", uiRet);
		goto end;
	}

	//5.Disconnect the device
	uiRet = DSTP2x_DisconnDev(devHdl);
	if(uiRet)
	{
		printf("DSTP2x_DisconnDev error, error code:%d\n", uiRet);
		goto end;
	}
	printf("This example has been successfully demonstrated!\n");

end:
	
	//6.Clear dynamic library
	DSTP2x_Lib_Clear();
	getchar();
	return 0;
}