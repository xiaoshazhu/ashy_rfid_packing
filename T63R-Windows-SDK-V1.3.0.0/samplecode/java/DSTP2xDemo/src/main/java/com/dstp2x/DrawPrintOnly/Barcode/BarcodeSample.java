package com.dstp2x.DrawPrintOnly.Barcode;

import com.dstp2x.DSTP2xLib.DSTP2x;
import com.dstp2x.DSTP2xLib.DSTP2xJnaLib;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.LongByReference;

public class BarcodeSample {
    protected DSTP2xJnaLib dstp2xJnaLib;
    protected static final int SZ_RESULT_SIZE=4096;
    protected Pointer szResult =new Memory(SZ_RESULT_SIZE),szEnumList=new Memory(512);
    protected IntByReference szResultLength =new IntByReference(),iDevSize=new IntByReference(512),iDevNum=new IntByReference();
    protected LongByReference pDevHdl=new LongByReference(),pLabelHdl=new LongByReference();//Used for 64 bit systems, 64 bit libraries
//    protected IntByReference pDevHdl=new IntByReference(),pLabelHdl=new IntByReference();//Used for 32 bit systems, 32 bit libraries
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

        //4.Create label context
        uiRet=dstp2xJnaLib.DSTP2x_CreateLabelContext(100,120,pLabelHdl);
        if (uiRet!=0){
            System.out.println("DSTP2x_CreateLabelContext error, errorCode:"+uiRet);
            closeDSTP2x();
            return;
        }
        System.out.println("DSTP2x_CreateLabelContext success,label handle:"+pLabelHdl.getValue());

        //5.Draw barcode


        dstp2xJnaLib.DSTP2x_LcDraw_SetBarCodeExpl(pLabelHdl.getValue(),0,1);
        dstp2xJnaLib.DSTP2x_Lbl_DrawBarCode(pLabelHdl.getValue(),0,10,40,20,20,"123456");

        dstp2xJnaLib.DSTP2x_LcDraw_SetBarCodeEcLvl(pLabelHdl.getValue(),1,2);
        dstp2xJnaLib.DSTP2x_Lbl_DrawBarCode(pLabelHdl.getValue(), 0,50,40,40,58,"123456");
        //6.Print label context

//        dstp2xJnaLib.DSTP2x_SetLcPrnMode(pLabelHdl.getValue(),2);
        uiRet=dstp2xJnaLib.DSTP2x_PrintLc(pDevHdl.getValue(),pLabelHdl.getValue(),null,null,0,null,null);
        if (uiRet!=0){
            System.out.println("DSTP2x_PrintLc error, errorCode:"+uiRet);
            System.out.println("DSTP2x_PrintLc error:"+getErrorMsg(uiRet));
            dstp2xJnaLib.DSTP2x_DeleteLabelContext(pLabelHdl.getValue());
            closeDSTP2x();
            return;
        }
        //7.Delete label context
        dstp2xJnaLib.DSTP2x_DeleteLabelContext(pLabelHdl.getValue());
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
        BarcodeSample sample=new BarcodeSample();
        sample.startWork();
    }
}
