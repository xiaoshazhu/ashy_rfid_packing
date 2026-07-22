package com.dstp2x.ReadTid_DrawPrint_RFID;

import com.dstp2x.DSTP2xLib.DSTP2x;
import com.dstp2x.DSTP2xLib.DSTP2xJnaLib;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.LongByReference;

import java.nio.charset.StandardCharsets;

public class ReadTid_DrawPrint_RFIDSample {
    protected DSTP2xJnaLib dstp2xJnaLib;
    protected static final int SZ_RESULT_SIZE=4096;
    protected Pointer szResult =new Memory(SZ_RESULT_SIZE),szEnumList=new Memory(512),szTid=new Memory(128),szOutFile=new Memory(128),szOutRfid=new Memory(128);
    protected IntByReference szResultLength =new IntByReference(),iDevSize=new IntByReference(512),iDevNum=new IntByReference(),iTidSize=new IntByReference(128),iOutFileSize=new IntByReference(128),iOutRfidSize=new IntByReference(128);
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

        //4.Read the tid data of tag
        szTid.clear(128);
        iTidSize.setValue(128);
        uiRet=dstp2xJnaLib.DSTP2x_RFID_ReadData(pDevHdl.getValue(),szTid,iTidSize,null,null,null,null);
        if (uiRet!=0){
            System.out.println("DSTP2x_RFID_ReadData error, error code:"+uiRet);
            closeDSTP2x();
            return;
        }
        System.out.println("DSTP2x_RFID_ReadData success,tid:"+szTid.getString(0));

        //5.Create the label.
        uiRet=dstp2xJnaLib.DSTP2x_CreateLabelContext(50,100, pLabelHdl);
        if (uiRet!=0){
            System.out.println("DSTP2x_CreateLabelContext error, error code:"+uiRet);
            closeDSTP2x();
            return;
        }
        System.out.println("DSTP2x_CreateLabelContext success,pLabelHdl:"+ pLabelHdl.getValue());

        //6.Draw bar code
        uiRet=dstp2xJnaLib.DSTP2x_Lbl_DrawBarCode(pLabelHdl.getValue(), 0, 60, 40, 30, 20, "123456"); //data must be utf-8
        if (uiRet!=0){
            System.out.println("DSTP2x_Lbl_DrawBarCode error, errorCode:"+uiRet);
            System.out.println(getErrorMsg(uiRet));
            closeDSTP2x();
            return;
        }

        //7.Set the RFID data.
        String epcStr="ABC123";
        uiRet=dstp2xJnaLib.DSTP2x_LcRfid_SetData(pLabelHdl.getValue(),1,1,epcStr,epcStr.length());
        if (uiRet != 0)
        {
            System.out.println("DSTP2x_LcRfid_SetData(EPC) error, errorCode:"+uiRet);
            System.out.println(getErrorMsg(uiRet));
            dstp2xJnaLib.DSTP2x_DeleteLabelContext(pLabelHdl.getValue());
            closeDSTP2x();
            return;
        }
        String userStr="123ABC";
        uiRet=dstp2xJnaLib.DSTP2x_LcRfid_SetData(pLabelHdl.getValue(),2,1,userStr,userStr.length());
        if (uiRet != 0)
        {
            System.out.println("DSTP2x_LcRfid_SetData(USER) error, errorCode:"+uiRet);
            dstp2xJnaLib.DSTP2x_DeleteLabelContext(pLabelHdl.getValue());
            closeDSTP2x();
            return;
        }


        //8.Print label templates and read RFID

        //When printing in a loop or batch, please ensure that :
        // 1:the parameter values are initialized before each call to print!
        // 2:the initialized value is consistent with the initially declared length value
        szOutRfid.clear(128);
        iOutRfidSize.setValue(128);

//        dstp2xJnaLib.DSTP2x_SetLcPrnMode(pLabelHdl.getValue(),2);
        uiRet=dstp2xJnaLib.DSTP2x_PrintLc(pDevHdl.getValue(), pLabelHdl.getValue(),null,null,6,szOutRfid,iOutRfidSize);
        if (uiRet!=0){
            System.out.println("DSTP2x_PrintLc error, errorCode:"+uiRet);
            dstp2xJnaLib.DSTP2x_DeleteLabelContext(pLabelHdl.getValue());
            closeDSTP2x();
            return;
        }
        System.out.println("DSTP2x_PrintLc success,Rfid info:"+szOutRfid.getString(0));

        //9.Delete label templates
        dstp2xJnaLib.DSTP2x_DeleteLabelContext(pLabelHdl.getValue());

        //10.Clear dynamic library
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
        ReadTid_DrawPrint_RFIDSample sample=new ReadTid_DrawPrint_RFIDSample();
        sample.startWork();
    }
}
