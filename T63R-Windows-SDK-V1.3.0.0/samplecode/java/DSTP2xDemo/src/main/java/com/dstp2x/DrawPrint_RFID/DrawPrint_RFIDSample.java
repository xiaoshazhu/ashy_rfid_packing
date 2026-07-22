package com.dstp2x.DrawPrint_RFID;

import com.dstp2x.DSTP2xLib.DSTP2x;
import com.dstp2x.DSTP2xLib.DSTP2xJnaLib;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.LongByReference;

import java.io.UnsupportedEncodingException;
import java.nio.charset.StandardCharsets;

public class DrawPrint_RFIDSample {
    protected DSTP2xJnaLib dstp2xJnaLib;
    protected static final int SZ_RESULT_SIZE=4096;
    protected Pointer szResult =new Memory(SZ_RESULT_SIZE),szEnumList=new Memory(512),szEPCData=new Memory(128),szOutRfid=new Memory(128);
    protected IntByReference szResultLength =new IntByReference(),iDevSize=new IntByReference(512),iDevNum=new IntByReference(),iTidSize=new IntByReference(128),iOutRfidSize=new IntByReference(128);
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
            System.out.println(getErrorMsg(uiRet));
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
        uiRet=dstp2xJnaLib.DSTP2x_CreateLabelContext(100,30,pLabelHdl);
        if (uiRet!=0){
            System.out.println("DSTP2x_CreateLabelContext error, error code:"+uiRet);
            closeDSTP2x();
            return;
        }
        System.out.println("DSTP2x_CreateLabelContext success, label handle :"+pLabelHdl.getValue());
        //5.Write EPC data

        //you can pass string
        String epc="12345678";
        uiRet=dstp2xJnaLib.DSTP2x_LcRfid_SetData(pLabelHdl.getValue(),1,2,epc,epc.length());
        System.out.println("Write EPC data:"+epc);

        //or you can pass hexadecimal byte data
//        byte[] epcData={0x12,0x34,0x56,0x78};
//        uiRet=dstp2xJnaLib.DSTP2x_LcRfid_SetData(pLabelHdl.getValue(),1,3,epcData,epcData.length);
//        System.out.println("Write EPC data:"+bytesToHexString(epcData," "));
//
        if (uiRet!=0){
            System.out.println("Rfid set EPC data error, error code:"+uiRet);
            closeDSTP2x();
            return;
        }

        //6.Write User data
        //you can pass string
        String user="0011223344";
        uiRet=dstp2xJnaLib.DSTP2x_LcRfid_SetData(pLabelHdl.getValue(),2,2,user,user.length());
        System.out.println("Write USER data:"+user);

        //or you can pass hexadecimal byte data
//        byte[] userData={0x00,0x11,0x22,0x33,0x44};
//        uiRet=dstp2xJnaLib.DSTP2x_LcRfid_SetData(pLabelHdl.getValue(),2,3,userData,userData.length);
//        System.out.println("Write USER data:"+bytesToHexString(userData," "));

        if (uiRet!=0){
            System.out.println("Rfid set USER data error, error code:"+uiRet);
            closeDSTP2x();
            return;
        }


        //7.Draw text
        dstp2xJnaLib.DSTP2x_LcDraw_SetTextFontName(pLabelHdl.getValue(),0,"Arial");
        String test = "";
        try {
            byte[] gbkBytes="测试文本123456".getBytes(StandardCharsets.UTF_8);
            test=new String(gbkBytes,"GBK");
        } catch (UnsupportedEncodingException e) {
            e.printStackTrace();
        }
        dstp2xJnaLib.DSTP2x_Lbl_DrawText(pLabelHdl.getValue(),0,0,50,30,test);

        //8.Print label content and read RFID data

        //When printing in a loop or batch, please ensure that :
        // 1:the parameter values are initialized before each call to print!
        // 2:the initialized value is consistent with the initially declared length value
        szOutRfid.clear(128);
        iOutRfidSize.setValue(128);

//        dstp2xJnaLib.DSTP2x_SetLcPrnMode(pLabelHdl.getValue(),2);
        uiRet=dstp2xJnaLib.DSTP2x_PrintLc(pDevHdl.getValue(),pLabelHdl.getValue(),null,null,7,szOutRfid,iOutRfidSize);
        if (uiRet!=0){
            System.out.println("DSTP2x_PrintLc error, error code:"+uiRet);
            System.out.println(getErrorMsg(uiRet));
            dstp2xJnaLib.DSTP2x_DeleteLabelContext(pLabelHdl.getValue());
            closeDSTP2x();
            return;
        }
        System.out.println("Read RFID data:"+szOutRfid.getString(0));
        //9.Delete label content
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
            byte[] errorBytes=szDesc.getByteArray(0,iDescLen.getValue());
            String errorMsg= "";
            try {
                errorMsg = new String(errorBytes,"UTF-8");
            } catch (UnsupportedEncodingException e) {
                e.printStackTrace();
            }
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

    public String bytesToHexString(byte[] src,String splitStr) {
        if (src == null || src.length <= 0) {
            return "";
        }
        if (splitStr==null){
            splitStr="";
        }
        String [] str = new String[src.length];
        for (int i = 0; i < src.length; i++) {
            int v = src[i] & 0xFF;
            String hv = Integer.toHexString(v);
            if (hv.length() < 2) {
                str[i] = 0+"";
            }
            str[i] = hv;
        }

        StringBuffer s=new StringBuffer();
        for(int i=0;i<str.length;i++) {
            if(str[i].length()==1) {
                s.append("0"+str[i]);
            }else {
                s.append(str[i]);
            }
            if (i!= str.length-1){
                s.append(splitStr);
            }

        }
        return s.toString();
    }


    public static void main(String[] args){
        DrawPrint_RFIDSample sample=new DrawPrint_RFIDSample();
        sample.startWork();
    }
}
