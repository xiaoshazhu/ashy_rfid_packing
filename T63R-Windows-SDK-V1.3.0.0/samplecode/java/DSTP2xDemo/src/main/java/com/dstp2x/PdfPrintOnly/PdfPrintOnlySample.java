package com.dstp2x.PdfPrintOnly;

import com.dstp2x.DSTP2xLib.DSTP2x;
import com.dstp2x.DSTP2xLib.DSTP2xJnaLib;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.LongByReference;

public class PdfPrintOnlySample {
    protected DSTP2xJnaLib dstp2xJnaLib;
    protected static final int SZ_RESULT_SIZE=4096;
    protected Pointer szResult =new Memory(SZ_RESULT_SIZE),szEnumList=new Memory(512),szOutFile=new Memory(1024),szOutRfid=new Memory(128);
    protected IntByReference szResultLength =new IntByReference(),iDevSize=new IntByReference(512),iDevNum=new IntByReference(),iPdfPageCount=new IntByReference(),iOutFileSize=new IntByReference(),iOutRfidSize=new IntByReference();
    protected LongByReference pDevHdl=new LongByReference(),pPdfHdl=new LongByReference();//Used for 64 bit systems, 64 bit libraries
//    protected IntByReference pDevHdl=new IntByReference(),pPdfHdl=new IntByReference();//Used for 32 bit systems, 32 bit libraries
    int uiRet,iEnumType=1;
    String devName;
    protected void startWork(){
        dstp2xJnaLib= DSTP2x.getInstance();
        //1.Load dynamic library
        uiRet=dstp2xJnaLib.DSTP2x_Lib_Init("",0, szResult, szResultLength);
        if (uiRet!=0){
            System.out.println("DSTP2x_Lib_Init error, error code:"+uiRet);
            return;
        }

        //2.Enum printer  iEnumType: 1->USB 2->TCP
        szEnumList.clear(512);
        uiRet=dstp2xJnaLib.DSTP2x_EnumDev(iEnumType,szEnumList,iDevSize,iDevNum);
        if(uiRet!=0){
            System.out.println("DSTP2x_EnumDev error , errorCode:"+uiRet);
            closeDSTP2x();
            releasePointer(szEnumList);
            return;
        }
        String szEnumListStr=szEnumList.getString(0);
        if (szEnumListStr.contains("\n")){
            devName=szEnumListStr.split("\n")[0];
        }else {
            devName=szEnumListStr;
        }
        releasePointer(szEnumList);

        //3.Connect the printer
        uiRet=dstp2xJnaLib.DSTP2x_ConnEnumeratedDev(devName,pDevHdl);
        if (uiRet!=0){
            System.out.println("DSTP2x_ConnEnumeratedDev error , errorCode:"+uiRet);
            closeDSTP2x();
            return;
        }
        System.out.println("Successfully connected to printer, device handle :"+pDevHdl.getValue());

        //Set emulation. 1-ZPL, 2-TSPL, 3-ESCPOS
        uiRet=dstp2xJnaLib.DSTP2x_SetPrnEmulation(pDevHdl.getValue(),1);
        if (uiRet!=0){
            System.out.println("DSTP2x_SetPrnEmulation error , errorCode:"+uiRet);
            closeDSTP2x();
            return;
        }

        //4.Load the file of pdf. 1-pdf file, 2-base64 of pdf.
        String pdfStr="E:/Java_Project/DSTP2x_Windows_SDK_JavaSample/DSTP2xDemo/src/main/resources/test.pdf";
        uiRet=dstp2xJnaLib.DSTP2x_LoadPdf(1,pdfStr,pdfStr.length(),pPdfHdl,iPdfPageCount);
        if (uiRet!=0){
            System.out.println("DSTP2x_LoadPdf error, errorCode:"+uiRet);
            System.out.println(getErrorMsg(uiRet));
            closeDSTP2x();
            return;
        }
        System.out.println("DSTP2x_LoadPdf success,label handle:"+pPdfHdl.getValue()+",pageCount:"+iPdfPageCount.getValue());

        //5.Set the print size
        uiRet = dstp2xJnaLib.DSTP2x_SetPdfPrnSize(pPdfHdl.getValue(),80,100);
        if (uiRet != 0)
        {
            System.out.println("DSTP2x_SetPdfPrnSize error,errorCode:" +uiRet );
            closeDSTP2x();
            return;
        }

        //6.Print the first page of pdf and write and read the data of EPC and USER

        //When printing in a loop or batch, please ensure that :
        // 1:the parameter values are initialized before each call to print!
        // 2:the initialized value is consistent with the initially declared length value
        szOutFile.clear(1024);
        iOutFileSize.setValue(1024);
        szOutRfid.clear(128);
        iOutRfidSize.setValue(128);

//        dstp2xJnaLib.DSTP2x_SetPdfPrnMode(pPdfHdl.getValue(),2);
        uiRet = dstp2xJnaLib.DSTP2x_PrintPdf(pDevHdl.getValue(),pPdfHdl.getValue(), 1,szOutFile,iOutFileSize,0,szOutRfid,iOutRfidSize); //set print mode
        if (uiRet != 0)
        {
            System.out.println("DSTP2x_PrintPdf error,errorCode:" +uiRet );
            closeDSTP2x();
            return;
        }


        //7.Delete pdf context
        dstp2xJnaLib.DSTP2x_DeletePdf(pPdfHdl.getValue());
        //8.Clear dynamic library
        closeDSTP2x();
    }

    private String getErrorMsg(int uiRet){
        Pointer szDesc=new Memory(128);
        szDesc.clear(128);
        IntByReference iDescLen=new IntByReference(128);
        int rs=dstp2xJnaLib.DSTP2x_ApiRtnCodeToMsg(uiRet,szDesc,iDescLen);
        if (rs!=0){
            System.out.println("DSTP2x_ApiRtnCodeToMsg error,error code:"+uiRet);
            releasePointer(szDesc);
            return "";
        }else {
            String errorMsg=szDesc.getString(0,"UTF-8");
            releasePointer(szDesc);
            return errorMsg;
        }
    }

    protected void closeDSTP2x(){
        if (szResult!=null){
            releasePointer(szResult);
        }
        if (dstp2xJnaLib==null)
            return;
        int uiRet;
        //Disconnect the device
        if (pDevHdl.getValue()>0){
            uiRet=dstp2xJnaLib.DSTP2x_DisconnDev(pDevHdl.getValue());
            if (uiRet!=0){
                System.out.println("DSTP2x_DisconnDev error, errorCode:"+uiRet);
            }
        }
        //Clear dynamic library
        uiRet=dstp2xJnaLib.DSTP2x_Lib_Clear();
        if (uiRet!=0){
            System.out.println("DSTP2x_Lib_Clear error, errorCode:"+uiRet);
        }
        dstp2xJnaLib=null;
        System.out.println("DSTP2x close");
    }

    public void releasePointer(Pointer p){
        if (p==null)
            return;
        Native.free(Pointer.nativeValue(p));
        Pointer.nativeValue(p,0);
    }

    public static void main(String[] args){
        PdfPrintOnlySample sample=new PdfPrintOnlySample();
        sample.startWork();
    }
}
