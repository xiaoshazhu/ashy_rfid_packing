package com.dstp2x.DrawPrint_RFID;

import com.dstp2x.DSTP2xLib.DSTP2x;
import com.dstp2x.DSTP2xLib.DSTP2xJnaLib;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.LongByReference;

import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Base64;

public class DrawPrint_RFID_2Sample {
    protected DSTP2xJnaLib dstp2xJnaLib;
    protected static final int SZ_RESULT_SIZE=4096;
    protected Pointer szResult =new Memory(SZ_RESULT_SIZE),szEnumList=new Memory(512),szEPCData=new Memory(128),szOutRfid=new Memory(128),szDesc=new Memory(1024);
    protected IntByReference szResultLength =new IntByReference(),iDevSize=new IntByReference(512),iDevNum=new IntByReference(),iTidSize=new IntByReference(128),iOutRfidSize=new IntByReference(128),iIsReady =new IntByReference(),pMainStatus=new IntByReference(),iMainStatusNum=new IntByReference(),pWarning=new IntByReference(),iWarningNum=new IntByReference(),pError=new IntByReference(),iErrorNum=new IntByReference(),iDescLen=new IntByReference(1024);
    protected LongByReference pDevHdl=new LongByReference(),pLabelHdl=new LongByReference();//Used for 64 bit systems, 64 bit libraries
//    protected IntByReference pDevHdl=new IntByReference(),pLabelHdl=new IntByReference();//Used for 32 bit systems, 32 bit libraries
    int uiRet,iEnumType=1;
    String devName;
    boolean isEncryption=false;
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

        for (int i=0;i<1;i++){
            boolean waitRs=waitPrinterOk(pDevHdl.getValue(),20);
            if (!waitRs){
                System.out.println("wait fail");
                closeDSTP2x();
                return;
            }

            //4.Create label context
            uiRet=dstp2xJnaLib.DSTP2x_CreateLabelContext(70,30,pLabelHdl);
            if (uiRet!=0){
                System.out.println("DSTP2x_CreateLabelContext error, error code:"+uiRet);
                closeDSTP2x();
                return;
            }
            System.out.println("DSTP2x_CreateLabelContext success, label handle :"+pLabelHdl.getValue());
            //5.Write EPC data


            String tagPwdOld="00000000";
            String tagPwdNew="88888888";

            if (isEncryption){
                uiRet = dstp2xJnaLib.DSTP2x_RFID_ChangeAccessPassword(pDevHdl.getValue(), tagPwdOld, tagPwdNew);
                System.out.println("【得实750pro打印机】：1 设定access密码结果："+uiRet);

                uiRet=dstp2xJnaLib.DSTP2x_RFID_SetPasswordWithWrite(pDevHdl.getValue(),1,tagPwdNew);
                System.out.println("【得实750pro打印机】：3 写入 EPC 数据的密码结果:"+uiRet);

                uiRet=dstp2xJnaLib.DSTP2x_RFID_LockOperate(pDevHdl.getValue(), 1, tagPwdNew);
                System.out.println("【得实750pro打印机】：2 锁定 EPC 区域返回结果:"+uiRet);
            }

            String epc="12345678";
            byte[] epcData=epc.getBytes(StandardCharsets.UTF_8);
            uiRet=dstp2xJnaLib.DSTP2x_LcRfid_SetData(pLabelHdl.getValue(),1,2,epcData,epcData.length);
            if (uiRet!=0){
                System.out.println("Rfid set EPC data error, error code:"+uiRet);
                closeDSTP2x();
                return;
            }
            System.out.println("Write EPC data:"+epc);

//            dstp2xJnaLib.DSTP2x_LcDraw_SetImageHalftoneAlgo(pLabelHdl.getValue(),0,3,180);
            //7.Draw image
            String imgPathDS="E:\\Java_Project\\DSTP2x-Windows-SDK-Develop\\1.1\\samplecode\\java\\DSTP2xDemo\\src\\main\\resources\\testDrawRFID2.png";
            String base64Image = null;
            try {
                base64Image = encodeImageToBase64(imgPathDS);
            } catch (IOException e) {
                e.printStackTrace();
                dstp2xJnaLib.DSTP2x_DeleteLabelContext(pLabelHdl.getValue());
                closeDSTP2x();
                return;
            }
            base64Image="data:image/png;base64,"+base64Image;
            byte[] base64ImageBytes = base64Image.getBytes(StandardCharsets.UTF_8);
            int unImgDataSize = base64ImageBytes.length; // 获取实际内存大小
            uiRet=dstp2xJnaLib.DSTP2x_Lbl_DrawImage(pLabelHdl.getValue(),0,0,70,30,1,2,base64Image,unImgDataSize);
            if (uiRet!=0){
                System.out.println("DSTP2x_Lbl_DrawImage error, error code:"+uiRet);
                System.out.println(getErrorMsg(uiRet));
                dstp2xJnaLib.DSTP2x_DeleteLabelContext(pLabelHdl.getValue());
                closeDSTP2x();
                return;
            }

            //8.Print label content and read RFID data

            //When printing in a loop or batch, please ensure that :
            // 1:the parameter values are initialized before each call to print!
            // 2:the initialized value is consistent with the initially declared length value
            szOutRfid.clear(128);
            iOutRfidSize.setValue(128);

//        dstp2xJnaLib.DSTP2x_SetLcPrnMode(pLabelHdl.getValue(),2);
            uiRet=dstp2xJnaLib.DSTP2x_PrintLc(pDevHdl.getValue(), pLabelHdl.getValue(), szOutRfid, null, 3, szOutRfid, iOutRfidSize);
            if (uiRet!=0){
                System.out.println("DSTP2x_PrintLc error, error code:"+uiRet);
                System.out.println(getErrorMsg(uiRet));
                dstp2xJnaLib.DSTP2x_DeleteLabelContext(pLabelHdl.getValue());
                closeDSTP2x();
                return;
            }
            System.out.println("Read RFID data:"+szOutRfid.getString(0));
        }

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

    public String encodeImageToBase64(String imagePath) throws IOException {
        Path path = Paths.get(imagePath);
        byte[] imageBytes = Files.readAllBytes(path);

        return Base64.getEncoder().encodeToString(imageBytes);
    }

    public boolean waitPrinterOk(long ullDevHdl,int maxCount) {
        IntByReference iIsReady=new IntByReference(),pMainStatus=new IntByReference(),iMainStatusNum=new IntByReference(),pWarning=new IntByReference(),iWarningNum=new IntByReference(),pError=new IntByReference(),iErrorNum=new IntByReference(),iDescLen=new IntByReference(1024);
        Pointer szDesc=new Memory(1024);
        int retryCount = 0;
        do {
            boolean isReady=false;
            szDesc.clear(1024);
            iDescLen.setValue(1024);
            uiRet=dstp2xJnaLib.DSTP2x_GetPrtStatus(ullDevHdl, iIsReady,pMainStatus,iMainStatusNum,pWarning,iWarningNum,pError,iErrorNum,szDesc,iDescLen);
            if (uiRet!=0){
                System.out.println("waitPrinterOk DSTP2x_GetPrtStatus error, errorCode:"+uiRet);
                System.out.println("waitPrinterOk DSTP2x_GetPrtStatus error, errorMsg:"+getErrorMsg(uiRet));
                releasePointer(szDesc);
                return false;
            }else {
                isReady=iIsReady.getValue()==1;
                if (isReady) {
                    System.out.println("waitPrinterOk: Ok ,Don't Wait");
                    releasePointer(szDesc);
                    return true;
                } else {
                    retryCount++;
                    if (retryCount <= maxCount) {
                        System.out.println("waitPrinterOk: Wait:"+retryCount+"/"+maxCount);
                        try {
                            Thread.sleep(500);
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                    } else {
                        System.out.println("waitPrinterOk: Max Count,Don't Wait");
                        releasePointer(szDesc);
                        return false;
                    }
                }
            }

        } while (true);
    }

    public static void main(String[] args){
        DrawPrint_RFID_2Sample sample=new DrawPrint_RFID_2Sample();
        sample.startWork();
    }
}
