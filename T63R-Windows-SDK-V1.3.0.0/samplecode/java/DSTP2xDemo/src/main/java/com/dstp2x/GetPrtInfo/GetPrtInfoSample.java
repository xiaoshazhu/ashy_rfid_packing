package com.dstp2x.GetPrtInfo;

import com.dstp2x.DSTP2xLib.DSTP2x;
import com.dstp2x.DSTP2xLib.DSTP2xJnaLib;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.ptr.ByteByReference;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.LongByReference;

public class GetPrtInfoSample {
    protected DSTP2xJnaLib dstp2xJnaLib;
    protected static final int SZ_RESULT_SIZE=4096;
    protected Pointer szResult =new Memory(SZ_RESULT_SIZE),szEnumList=new Memory(512),szPrtFWVer=new Memory(128),szPrtSN=new Memory(128),szDesc=new Memory(1024);
    protected IntByReference szResultLength =new IntByReference(),iDevSize=new IntByReference(512),iDevNum=new IntByReference(),iPrtFWVerSize=new IntByReference(128),iPrtSNSize=new IntByReference(128), iIsReady =new IntByReference(),pMainStatus=new IntByReference(),iMainStatusNum=new IntByReference(),pWarning=new IntByReference(),iWarningNum=new IntByReference(),pError=new IntByReference(),iErrorNum=new IntByReference(),iDescLen=new IntByReference(1024);
    protected LongByReference pDevHdl=new LongByReference();//Used for 64 bit systems, 64 bit libraries
//    protected IntByReference pDevHdl=new IntByReference();//Used for 32 bit systems, 32 bit libraries
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
            System.out.println("DSTP2x_EnumDev error, errorCode:"+uiRet);
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
            System.out.println("DSTP2x_ConnEnumeratedDev error, errorCode:"+uiRet);
            closeDSTP2x();
            return;
        }
        System.out.println("Successfully connected to printer,device handle :"+pDevHdl.getValue());

        //4.Get printer firmware version
        uiRet=dstp2xJnaLib.DSTP2x_GetPrtFWVer(pDevHdl.getValue(),szPrtFWVer,iPrtFWVerSize);
        if (uiRet!=0){
            System.out.println("DSTP2x_GetPrtFWVer error, error code:"+uiRet);
            closeDSTP2x();
            return;
        }
        System.out.println("Printer firmware version:"+szPrtFWVer.getString(0,"UTF-8"));

        //5.Get printer serial number
        uiRet=dstp2xJnaLib.DSTP2x_GetPrtSN(pDevHdl.getValue(),szPrtSN,iPrtSNSize);
        if (uiRet!=0){
            System.out.println("DSTP2x_GetPrtSN error, error code:"+uiRet);
            closeDSTP2x();
            return;
        }
        System.out.println("Printer serial number:"+szPrtSN.getString(0));

        //6.Get printer status
        uiRet=dstp2xJnaLib.DSTP2x_GetPrtStatus(pDevHdl.getValue(), iIsReady,pMainStatus,iMainStatusNum,pWarning,iWarningNum,pError,iErrorNum,szDesc,iDescLen);
        if (uiRet!=0){
            System.out.println("DSTP2x_GetPrtStatus error,error code:"+uiRet);
            System.out.println(getErrorMsg(uiRet));
            closeDSTP2x();
            return;
        }
        System.out.println("Printer status:"+szDesc.getString(0,"UTF-8"));

        //7.Clear dynamic library
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
        GetPrtInfoSample sample=new GetPrtInfoSample();
        sample.startWork();
    }


}
