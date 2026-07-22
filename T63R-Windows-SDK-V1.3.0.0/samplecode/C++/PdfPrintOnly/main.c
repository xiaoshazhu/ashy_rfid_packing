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
	char szResultInfo[1024] = { 0 }, szEnumList[4096] = { 0 };
	int iEnumType = 1/*Enum Type*/, iDevSize = sizeof(szEnumList), iDevNum = 0, iResultInfoSize = sizeof(szResultInfo);
	unsigned int uiRet = 0;

#if defined(_MSC_VER)
	const char *szPDFFile = "../../../PdfPrintOnly/PDF.pdf";
#else
	const char *szPDFFile = "./PDF.pdf";
#endif
	
	int iPDFPagesCount = 0;

	DEV_HDL devHdl = 0;
	PDF_HDL pdfHdl = 0;

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

	//Set dpi, 1-203dpi, 2-300dpi, 3-600dpi
	uiRet = DSTP2x_SetImgDpi(devHdl, 1);
	if (uiRet)
	{
		printf("DSTP2x_SetImgDpi error, error code:%d\n", uiRet);
		goto end;
	}

	//Set emulation. 1-ZPL, 2-TSPL, 3-ESCPOS
	uiRet = DSTP2x_SetPrnEmulation(devHdl, 1);
	if (uiRet)
	{
		printf("DSTP2x_SetPrnEmulation error, error code:%d\n", uiRet);
		goto end;
	}

	//4.Load PDF
	uiRet = DSTP2x_LoadPdf(1, szPDFFile, strlen(szPDFFile), &pdfHdl, &iPDFPagesCount);
	if (uiRet)
	{
		printf("DSTP2x_LoadPdf error, error code:%d\n", uiRet);
		goto end;
	}
	printf("The count of page is %d\n", iPDFPagesCount);

	//5.Set the print mode. 0-print, 1-generate the prn file, 2-generate the preview image.
	uiRet = DSTP2x_SetPdfPrnMode(pdfHdl, 0); //set print mode
	if (uiRet)
	{
		printf("DSTP2x_SetPdfPrnMode error, error code:%d\n", uiRet);
		goto end;
	}

	//Set the pdf rotation
	uiRet = DSTP2x_SetPdfPrnRotate(pdfHdl, 0);
	if (uiRet)
	{
		printf("DSTP2x_SetPdfPrnRotate error, error code:%d\n", uiRet);
		goto end;
	}

	//Set the size of pdf
	uiRet = DSTP2x_SetPdfPrnSize(pdfHdl, 80, 100);
	if (uiRet)
	{
		printf("DSTP2x_SetPdfPrnSize error, error code:%d\n", uiRet);
		goto end;
	}

	//6.Print the first page of pdf
	uiRet = DSTP2x_PrintPdf(devHdl, pdfHdl, 1, NULL, NULL, 0, NULL, NULL);
	if (uiRet)
	{
		printf("DSTP2x_PrintPdf error, error code:%d\n", uiRet);
		goto end;
	}

	//7.Delete the handle of PDF
	uiRet = DSTP2x_DeletePdf(pdfHdl);
	if (uiRet)
	{
		printf("DSTP2x_DeletePdf error, error code:%d\n", uiRet);
		goto end;
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