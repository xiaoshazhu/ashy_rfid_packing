package com.dstp2x.TemplatePrint_RFID;

import com.dstp2x.DSTP2xLib.DSTP2x;
import com.dstp2x.DSTP2xLib.DSTP2xJnaLib;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.LongByReference;

public class TemplatePrint_RFIDSample {
    protected DSTP2xJnaLib dstp2xJnaLib;
    protected static final int SZ_RESULT_SIZE=4096;
    protected Pointer szResult =new Memory(SZ_RESULT_SIZE),szEnumList=new Memory(512),szTid=new Memory(128),szOutFile=new Memory(1024),szOutRfid=new Memory(128);
    protected IntByReference szResultLength =new IntByReference(),iDevSize=new IntByReference(512),iDevNum=new IntByReference(),iTidSize=new IntByReference(128),iOutFileSize=new IntByReference(1024),iPdfPageCount=new IntByReference(),iOutRfidSize=new IntByReference(128);
    protected LongByReference pDevHdl=new LongByReference(),pLabelTmplHdl=new LongByReference();//Used for 64 bit systems, 64 bit libraries
//    protected IntByReference pDevHdl=new IntByReference(),pLabelTmplHdl=new IntByReference();//Used for 32 bit systems, 32 bit libraries
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

        //4.Load label templates
        String fileStr="E:\\Java_Project\\DSTP2x-Windows-SDK-Develop\\1.1\\samplecode\\java\\DSTP2xDemo\\src\\main\\resources\\templateRFID.dlt";
        uiRet=dstp2xJnaLib.DSTP2x_LoadLabelTmpl(fileStr, pLabelTmplHdl);
        if (uiRet!=0){
            System.out.println("DSTP2x_LoadLabelTmpl error, errorCode:"+uiRet);
            System.out.println(getErrorMsg(uiRet));
            closeDSTP2x();
            return;
        }
        System.out.println("DSTP2x_LoadLabelTmpl success,labelTmpl handle:"+ pLabelTmplHdl.getValue());

        //5.Set the print data in template.
//        dstp2xJnaLib.DSTP2x_SetTmplPrnMode(pLabelTmplHdl.getValue(),2);
        long temp = pLabelTmplHdl.getValue();
        String str="56789VWXYZ";
        uiRet = dstp2xJnaLib.DSTP2x_SetTmplPrnData(temp, "Text-01", str); //set print mode
        if (uiRet != 0)
        {
            System.out.println("DSTP2x_SetTmplPrnData error, errorCode:"+uiRet);
            dstp2xJnaLib.DSTP2x_DeleteTmpl(pLabelTmplHdl.getValue());
            closeDSTP2x();
            return;
        }

        //6.Set the RFID data.
        String epcStr="ABC123";
        uiRet=dstp2xJnaLib.DSTP2x_SetTmplRFIDData(pLabelTmplHdl.getValue(),"EPC-01",epcStr,epcStr.length());
        if (uiRet != 0)
        {
            System.out.println("DSTP2x_SetTmplRFIDData(EPC) error, errorCode:"+uiRet);
            System.out.println(getErrorMsg(uiRet));
            dstp2xJnaLib.DSTP2x_DeleteTmpl(pLabelTmplHdl.getValue());
            closeDSTP2x();
            return;
        }
        String userStr="123ABC";
        uiRet=dstp2xJnaLib.DSTP2x_SetTmplRFIDData(pLabelTmplHdl.getValue(),"USER-01",userStr,userStr.length());
        if (uiRet != 0)
        {
            System.out.println("DSTP2x_SetTmplRFIDData(USER) error, errorCode:"+uiRet);
            dstp2xJnaLib.DSTP2x_DeleteTmpl(pLabelTmplHdl.getValue());
            closeDSTP2x();
            return;
        }
        //7.Print label templates and get the RFID data.

        //When printing in a loop or batch, please ensure that :
        // 1:the parameter values are initialized before each call to print!
        // 2:the initialized value is consistent with the initially declared length value
        szOutFile.clear(1024);
        iOutFileSize.setValue(1024);
        szOutRfid.clear(128);
        iOutRfidSize.setValue(128);

        uiRet=dstp2xJnaLib.DSTP2x_PrintTmpl(pDevHdl.getValue(), pLabelTmplHdl.getValue(),szOutFile,iOutFileSize,szOutRfid,iOutRfidSize);
        if (uiRet!=0){
            System.out.println("DSTP2x_PrintTmpl error, errorCode:"+uiRet);
            System.out.println("DSTP2x_PrintTmpl error, errorMsg:"+getErrorMsg(uiRet));
            dstp2xJnaLib.DSTP2x_DeleteTmpl(pLabelTmplHdl.getValue());
            closeDSTP2x();
            return;
        }
        System.out.println("DSTP2x_PrintTmpl success,Rfid info:"+szOutRfid.getString(0));


        //8.Delete label templates
        dstp2xJnaLib.DSTP2x_DeleteTmpl(pLabelTmplHdl.getValue());

        //9.Clear dynamic library
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
        TemplatePrint_RFIDSample sample=new TemplatePrint_RFIDSample();
        sample.startWork();
    }
}
