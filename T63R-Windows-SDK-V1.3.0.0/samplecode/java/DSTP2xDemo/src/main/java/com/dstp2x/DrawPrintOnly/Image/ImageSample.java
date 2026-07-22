package com.dstp2x.DrawPrintOnly.Image;

import com.dstp2x.DSTP2xLib.DSTP2x;
import com.dstp2x.DSTP2xLib.DSTP2xJnaLib;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.OaIdl;
import com.sun.jna.ptr.ByReference;
import com.sun.jna.ptr.ByteByReference;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.LongByReference;
import com.sun.jna.win32.StdCallLibrary;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public class ImageSample {
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
        uiRet=dstp2xJnaLib.DSTP2x_SetPrnEmulation( pDevHdl.getValue(),1);
        if (uiRet!=0){
            System.out.println("DSTP2x_SetPrnEmulation error , errorCode:"+uiRet);
            closeDSTP2x();
            return;
        }

        //4.Create label context
        uiRet=dstp2xJnaLib.DSTP2x_CreateLabelContext(50,50,pLabelHdl);
        if (uiRet!=0){
            System.out.println("DSTP2x_CreateLabelContext error, errorCode:"+uiRet);
            closeDSTP2x();
            return;
        }
        System.out.println("DSTP2x_CreateLabelContext success,label handle:"+pLabelHdl.getValue());

        //5.Draw image
        int temp = 1;
        dstp2xJnaLib.DSTP2x_LcDraw_SetImageHalftoneAlgo(pLabelHdl.getValue(),temp,1,180);


        String imgStr="E:\\Java_Project\\DSTP2x-Windows-SDK-Develop\\1.1\\samplecode\\java\\DSTP2xDemo\\src\\main\\resources\\image.jpg";

        //You can Pass Image transmission path to the DSTP2x_Lbl_DrawImage function
//        dstp2xJnaLib.DSTP2x_Lbl_DrawImage(pLabelHdl.getValue(),0,10,40,40,1,0,imgStr,imgStr.length());

        //Or you can pass image data to the DSTP2x_Lbl_DrawImage function
        try {
            BufferedImage image = ImageIO.read(new File(imgStr));

            ByteArrayOutputStream baos = new ByteArrayOutputStream();

            ImageIO.write(image, "jpg", baos);

            byte[] byteArray = baos.toByteArray();
            Pointer pointerImgBytes=new Memory(byteArray.length);
            pointerImgBytes.write(0,byteArray,0,byteArray.length);
            dstp2xJnaLib.DSTP2x_Lbl_DrawImage(pLabelHdl.getValue(),0,10,40,40,1,1,pointerImgBytes,byteArray.length);
            releasePointer(pointerImgBytes);
        } catch (IOException e) {
            e.printStackTrace();
        }

        //6.Print label context`
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
        ImageSample sample=new ImageSample();
        sample.startWork();
    }
}
