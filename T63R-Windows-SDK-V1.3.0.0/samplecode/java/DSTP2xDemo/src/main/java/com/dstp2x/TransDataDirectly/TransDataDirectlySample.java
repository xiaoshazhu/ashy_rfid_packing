package com.dstp2x.TransDataDirectly;

import com.dstp2x.DSTP2xLib.DSTP2x;
import com.dstp2x.DSTP2xLib.DSTP2xJnaLib;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.LongByReference;

public class TransDataDirectlySample {
    protected DSTP2xJnaLib dstp2xJnaLib;
    protected static final int SZ_RESULT_SIZE=4096;
    protected Pointer szResult =new Memory(SZ_RESULT_SIZE),szEnumList=new Memory(512);
    protected IntByReference szResultLength =new IntByReference(),iDevSize=new IntByReference(512),iDevNum=new IntByReference();
    protected LongByReference pDevHdl=new LongByReference();//Used for 64 bit systems, 64 bit libraries
//    protected IntByReference pDevHdl=new IntByReference();//Used for 32 bit systems, 32 bit libraries
    int uiRet,iEnumType=1,iEmulationType=1/*1-ZPL, 2-TSPL, 3-ESCPOS*/;
    String devName;
    String[] szEmulationPaths=new String[]{
            /*ZPL*/
            "^XA^PW600^LL200^SEE:GB18030.DAT^CI26^CWL,E:simsun.fnt^FO0,10^ALN,40,40^FD Print Test LABEL^FS^XZ",
            /*TSPL*/
            "CLS\r\nSIZE 4,1\r\nTEXT 110,50,\"3\",0,1,1,\"Print Test LABEL\"\r\nPRINT 1\r\n",
            /*ESCPOS*/
            "1b401c261d21001b4d001b2d001b45005072696E742054657374204C4142454C0a1d564100"
    };
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

        //4.According the emulation to transfer data
        Pointer pSendData;
        if (iEmulationType<3){
            pSendData=new Memory(szEmulationPaths[iEmulationType-1].length()+1);
            pSendData.clear(szEmulationPaths[iEmulationType-1].length()+1);
            pSendData.setString(0,szEmulationPaths[iEmulationType-1]);
            uiRet=dstp2xJnaLib.DSTP2x_TransRecvData(pDevHdl.getValue(),pSendData,szEmulationPaths[iEmulationType-1].length(),null,null);
        }else if (iEmulationType==3){
            byte[] byteArray=hexStringToByteArray(szEmulationPaths[iEmulationType-1]);
            pSendData=new Memory(byteArray.length);
            pSendData.clear(byteArray.length);
            pSendData.write(0,byteArray,0, byteArray.length);
            uiRet=dstp2xJnaLib.DSTP2x_TransRecvData(pDevHdl.getValue(),pSendData,byteArray.length,null,null);
        }

        if (uiRet!=0){
            System.out.println("DSTP2x_TransRecvData error , errorCode:"+uiRet);
            closeDSTP2x();
            return;
        }

        //5.Clear dynamic library
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

    public static byte[] hexStringToByteArray(String hexString) {
        int len = hexString.length();
        byte[] byteArray = new byte[len / 2];
        for (int i = 0; i < len; i += 2) {
            // 每两个十六进制字符表示一个字节
            byteArray[i / 2] = (byte) ((Character.digit(hexString.charAt(i), 16) << 4)
                    + Character.digit(hexString.charAt(i+1), 16));
        }
        return byteArray;
    }


    public static void main(String[] args){
        TransDataDirectlySample sample=new TransDataDirectlySample();
        sample.startWork();
    }
}
