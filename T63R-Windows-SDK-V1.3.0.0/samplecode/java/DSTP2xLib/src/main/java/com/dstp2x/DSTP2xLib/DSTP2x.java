package com.dstp2x.DSTP2xLib;

import com.sun.jna.Library;
import com.sun.jna.Native;
import com.sun.jna.win32.StdCallLibrary;

import java.io.File;
import java.nio.file.Paths;

public class DSTP2x {
    private static DSTP2xJnaLib INSTANCE;


    public synchronized static DSTP2xJnaLib loadLibrary(String path){
        if(INSTANCE==null){
            System.setProperty("jna.encoding","UTF-8");
            INSTANCE= Native.load(path,DSTP2xJnaLib.class);
        }
        return INSTANCE;
    }


    public synchronized static DSTP2xJnaLib getInstance(){
        String sysMsg = System.getProperty("os.name");
        String basePath = new File("").getAbsolutePath();
        System.out.println("basePath:"+basePath);
        String packagePath= Paths.get(basePath).getParent().getParent().toString();
//        String packagePath=basePath+"\\DSTP2xLib";
        System.out.println("JaveHome:"+System.getProperty("java.home"));
        System.out.println("JavaVersion:"+System.getProperty("java.version"));
        System.out.println("JVMName:"+System.getProperty("java.vm.name"));
        System.out.println("JVMVersion:"+System.getProperty("java.vm.version"));
        System.out.println("JREName:"+System.getProperty("java.runtime.name"));
        System.out.println("JREVersion:"+System.getProperty("java.runtime.version"));
        String libPath=null;
        if(sysMsg.contains("Windows")){
            //windows
            System.out.println("Window OS");
            if ("64".equals(System.getProperty("sun.arch.data.model"))) {
                libPath=packagePath+"\\lib\\x64\\libDSThermal.dll";
                System.out.println("64 Bit System");
            } else {
                libPath=packagePath+"\\lib\\x32\\libDSThermal.dll";
//                libPath=basePath+"\\lib\\x32\\libDSThermal.dll";
                System.out.println("32 Bit System");
            }
        } else if(sysMsg.contains("Linux")){
            //Linux
            System.out.println("Linux OS");
            if (System.getProperty("os.arch").contains("64")){
                libPath=packagePath+"/lib/libDSThermal.so";
                libPath=libPath.replace("//","/");
                System.out.println("64 Bit System");
            }else {
                libPath=packagePath+"/lib/libDSThermal.so";
                libPath=libPath.replace("//","/");
                System.out.println("32 Bit System");
            }

        }else {
            System.out.println("Unknown OS");
            System.out.println("return");
        }
        if (libPath==null||libPath.equals("")){
            System.out.println("The library path is empty, returning JNA call object failure");
            return null;
        }else {
            System.out.println("The library path:"+libPath);
            DSTP2xJnaLib dstp2xJnaLib=DSTP2x.loadLibrary(libPath);
            if (dstp2xJnaLib instanceof StdCallLibrary){
                System.out.println("inherit \'StdCallLibrary\' interface");
            }else if (dstp2xJnaLib instanceof Library){
                System.out.println("inherit \'Library\' interface");
            }
            return dstp2xJnaLib;
        }
    }
}
