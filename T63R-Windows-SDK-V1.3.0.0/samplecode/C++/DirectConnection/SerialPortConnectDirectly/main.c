#include <stdio.h>
#include <string.h>
#include <stdlib.h>

//if language is English, please define en_US
#ifdef en_US      
#include "en-US/DSTP2x.h"
#else
#include "DSTP2x.h"
#endif

//Connect directly to the serial port based on the port number and baud rate
int main(int argc, char *argv[])
{
	char szResultInfo[1024] = { 0 };
	int iResultInfoSize = sizeof(szResultInfo);
	int serialPortNum = 1, baudRate = 9600;
	char c;

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

	printf("Please input the serial port like this \"3\":\n");	
	scanf("%d", &serialPortNum);

	printf("\nPlease input the baud rate like this \"115200\":\n");	
	scanf("%d", &baudRate);
	printf("\nThe serial port is %d and baud rate is %d\n", serialPortNum, baudRate);
	
	//just filter the enter key
	if(scanf("%c",&c)!= EOF)
	{
		while ( (c=getchar()) != '\n' && c != EOF ); 
	}

	//2.try to connect the net according to serial port and baud rate.
	uiRet = DSTP2x_ConnSerialDev(serialPortNum, baudRate, &devHdl);
	if(uiRet)
	{
		printf("DSTP2x_ConnNetworkDev error, error code:%d\n", uiRet);
		goto end;
	}
	else
	{
		printf("Connection successful!\n");
	}

	//3.Disconnect the device
	uiRet = DSTP2x_DisconnDev(devHdl);
	if(uiRet)
	{
		printf("DSTP2x_DisconnDev error, error code:%d\n", uiRet);
		goto end;
	}

	printf("This example has been successfully demonstrated!\n");
end:
	
	//4.Clear dynamic library
	DSTP2x_Lib_Clear();
	getchar();
	return 0;
}