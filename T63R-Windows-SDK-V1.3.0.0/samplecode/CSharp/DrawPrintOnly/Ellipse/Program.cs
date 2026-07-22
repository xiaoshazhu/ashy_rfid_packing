using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Runtime.InteropServices;
using DEV_HDL = System.UInt32;
using LC_HDL = System.UInt32;

namespace Ellipse
{
    class Program
    {
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_Lib_Init(string pSzInitInfo, Int32 nInitInfoLen, StringBuilder pSzResult, ref int pResultLen);
        
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_Lib_Clear();
        
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_EnumDev(Int32 nEnumType, StringBuilder szEnumList, ref int pDevSize, ref int pDevNum);
        
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_ConnEnumeratedDev(string szDevName, ref DEV_HDL pDevHdl);
        
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_DisconnDev(DEV_HDL ullDevHdl);      
        
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_SetPrnEmulation(DEV_HDL ullDevHdl, Int32 nEmulation);
        
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_SetImgDpi(DEV_HDL ullDevHdl, Int32 nDpi);
        
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_CreateLabelContext(Double dbWidth, Double dbHeight, ref LC_HDL pLCHdl);
        
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_LcDraw_SetEllipseRotation(LC_HDL ullLcHdl, Int32 nTemporary, Int32 nAngle, Int32 nAnchorPoint);

        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_Lbl_DrawEllipse(LC_HDL ullLcHdl, Double dbX, Double dbY, Double dbW, Double dbH, Int32 nLineWidth, Int32 nLineType, Int32 nIsFill);

        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_PrintLc(DEV_HDL ullDevHdl, LC_HDL ullLcHdl, StringBuilder szOutFile, ref int pOutFileSize, Int32 nRfidReadType, StringBuilder szOutRFID, ref int pOutRFIDSize);
        
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_DeleteLabelContext(LC_HDL ullLcHdl);
        
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_SetLcPrnMode(LC_HDL ullLcHdl, Int32 nPrnMode);       
        

        static void Main(string[] args)
        {
            UInt32 uRet = 0;
            StringBuilder pSzResult = new StringBuilder(256);
            Int32 pResultLen = 256;

            //1.Initialize the Library.
            uRet = DSTP2x_Lib_Init("", 0, pSzResult, ref pResultLen);
            if (uRet != 0)
            {
                Console.WriteLine("DSTP2x_Lib_Init，error code:[" + uRet.ToString() + "]");
                Console.ReadKey();
                return;
            }

            DEV_HDL dev_prt = 0;
            LC_HDL lc_prt = 0;
            StringBuilder pEnumList = new StringBuilder(500);            
            Int32 enumListLen = 500;
            StringBuilder szOutFile = new StringBuilder(500);
            Int32 pOutFileSize = 500;
             StringBuilder szOutRFID = new StringBuilder(128);
            Int32 pOutRFIDSize = 128;
            Int32 deviceNum = 0;
            String device = "";

            //2.Enumerate devices.   1-USB, 2-NET
            uRet = DSTP2x_EnumDev(1, pEnumList, ref enumListLen, ref deviceNum); //USB connection
            if (uRet != 0)
            {
                Console.WriteLine("Enumerate device error，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            if(deviceNum > 1)
            {
                String[] enumList;
                enumList = pEnumList.ToString(0, enumListLen).Split('\n');
                device = enumList[0];
            }
            else if(deviceNum == 1)
                device = pEnumList.ToString(0, enumListLen);
            else
            {
                Console.WriteLine("No device");
                goto SAMPLE_END;
            }

            //3.Connect the device.
            uRet = DSTP2x_ConnEnumeratedDev(device, ref dev_prt);
            if(uRet != 0)
            {
                Console.WriteLine("Failed to connect device，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //Non essential interface. 1-203dpi, 2-300dpi, 3-600dpi
            uRet = DSTP2x_SetImgDpi(dev_prt, 1);//set 203dpi
            if (uRet != 0)
            {
                Console.WriteLine("Failed to set dpi，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //Non essential interface. 1-ZPL, 2-TSPL, 3-ESCPOS
            uRet = DSTP2x_SetPrnEmulation(dev_prt, 1); //ZPL
            if (uRet != 0)
            {
                Console.WriteLine("Failed to set up print simulation，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //4.Create the label.
            uRet = DSTP2x_CreateLabelContext(50, 100, ref lc_prt);
            if (uRet != 0)
            {
                Console.WriteLine("Failed to set label drawing canvas，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //Non essential interface.  0-print, 1-generate prn file, 2-generate preview image
            uRet = DSTP2x_SetLcPrnMode(lc_prt, 0); //set print mode
            if (uRet != 0)
            {
                Console.WriteLine("Setting whether to print failed，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //5.ellipse
            uRet = DSTP2x_LcDraw_SetEllipseRotation(lc_prt, 0, 30, 0);
            if (uRet != 0)
            {
                Console.WriteLine("Setting rotate for ellipse，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            uRet = DSTP2x_Lbl_DrawEllipse(lc_prt, 10, 10, 20, 20, 5, 0, 0);
            if (uRet != 0)
            {
                Console.WriteLine("draw ellipse，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //6.Print label
            uRet = DSTP2x_PrintLc(dev_prt, lc_prt, szOutFile, ref pOutFileSize, 0, szOutRFID, ref pOutRFIDSize);
            if (uRet != 0)
            {
                Console.WriteLine("Print label failed，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //7.Delete the handle of label.
            uRet = DSTP2x_DeleteLabelContext(lc_prt);
            if (uRet != 0)
            {
                Console.WriteLine("Delete handle of label failed，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //8.Disconnect the device.
            uRet = DSTP2x_DisconnDev(dev_prt);
            if (uRet != 0)
            {
                Console.WriteLine("Delete handle of device failed，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            Console.WriteLine("This example has been successfully demonstrated!");
SAMPLE_END:
            //9.DeInit Library
            uRet = DSTP2x_Lib_Clear();
            Console.ReadKey();

        }
    }
}
