using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Runtime.InteropServices;
using DEV_HDL = System.UInt32;
using LABEL_TEMP_HDL = System.UInt32;

namespace ReadTid_TemplatePrint_RFID
{
    class Program
    {
        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_Lib_Init(string pSzInitInfo, Int32 nInitInfoLen, StringBuilder pSzResult, ref int pResultLen);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_Lib_Clear();

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_EnumDev(Int32 nEnumType, StringBuilder szEnumList, ref int pDevSize, ref int pDevNum);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_ConnEnumeratedDev(string szDevName, ref DEV_HDL pDevHdl);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_DisconnDev(DEV_HDL ullDevHdl);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_SetPrnEmulation(DEV_HDL ullDevHdl, Int32 nEmulation);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_SetImgDpi(DEV_HDL ullDevHdl, Int32 nDpi);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_LoadLabelTmpl(string szFileName, ref LABEL_TEMP_HDL pLTHdl);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_PrintTmpl(DEV_HDL ullDevHdl, LABEL_TEMP_HDL ullLTHdl, StringBuilder szOutFile, ref int pOutFileSize, StringBuilder szOutRFID, ref int pOutRFIDSize);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_DeleteTmpl(LABEL_TEMP_HDL ullLTHdl);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_SetTmplPrnMode(LABEL_TEMP_HDL ullLTHdl, Int32 nPrnMode);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_SetTmplPrnData(LABEL_TEMP_HDL ullLTHdl, string szElemID, string szActualData);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_SetTmplRFIDData(LABEL_TEMP_HDL ullLTHdl, string szElemID, string pActualData, Int32 nActualDataSize);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_RFID_ReadData(DEV_HDL ullDevHdl, StringBuilder pTid, ref int pTidSize, StringBuilder pEpc, ref int pEpcSize, StringBuilder pUser, ref int pUserSize);

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
            LABEL_TEMP_HDL tmp_prt = 0;
            StringBuilder pEnumList = new StringBuilder(500);
            Int32 enumListLen = 500;
            StringBuilder szOutFile = new StringBuilder(500);
            Int32 pOutFileSize = 500;
            StringBuilder szOutRFID = new StringBuilder(128);
            Int32 pOutRFIDSize = 128;
            Int32 deviceNum = 0;
            String device = "";

            String tmpPath = "../../samplecode/CSharp/ReadTid_TemplatePrint_RFID/templateRFID.dlt";

            String writeEPCData = "ABC123";
            String writeUSERData = "123ABC";

            StringBuilder pTIDData = new StringBuilder(64);
            Int32 pTIDDataLen = 64;
            Int32 pEPCDataLen = 0;
            Int32 pUSERDataLen = 0;

            //2.Enumerate devices.   1-USB, 2-NET
            uRet = DSTP2x_EnumDev(1, pEnumList, ref enumListLen, ref deviceNum); //USB connection
            if (uRet != 0)
            {
                Console.WriteLine("Enumerate device error，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            if (deviceNum > 1)
            {
                String[] enumList;
                enumList = pEnumList.ToString(0, enumListLen).Split('\n');
                device = enumList[0];
            }
            else if (deviceNum == 1)
                device = pEnumList.ToString(0, enumListLen);
            else
            {
                Console.WriteLine("No device");
                goto SAMPLE_END;
            }

            //3.Connect the device.
            uRet = DSTP2x_ConnEnumeratedDev(device, ref dev_prt);
            if (uRet != 0)
            {
                Console.WriteLine("Failed to connect device，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //Non essential interface. 1-ZPL, 2-TSPL, 3-ESCPOS
            uRet = DSTP2x_SetPrnEmulation(dev_prt, 1); //ZPL
            if (uRet != 0)
            {
                Console.WriteLine("Failed to set up print simulation，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //6.Load the template.
            uRet = DSTP2x_LoadLabelTmpl(tmpPath, ref tmp_prt);
            if (uRet != 0)
            {
                Console.WriteLine("Failed to load label template，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //7.Set the print mode. 0-print, 1-generate the prn file, 2-generate the preview image.
            uRet = DSTP2x_SetTmplPrnMode(tmp_prt, 0); //set print mode
            if (uRet != 0)
            {
                Console.WriteLine("Setting whether to print failed，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //8.Set the someone print data in template.
            uRet = DSTP2x_SetTmplPrnData(tmp_prt, "Text-01", "56789VWXYZ"); //The data must be utf-8
            if (uRet != 0)
            {
                Console.WriteLine("Failed to set someone data in template，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //9.Set the RFID data.
            uRet = DSTP2x_SetTmplRFIDData(tmp_prt, "EPC-01", writeEPCData, writeEPCData.Length);
            if (uRet != 0)
            {
                Console.WriteLine("Failed to set EPC data in template，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            uRet = DSTP2x_SetTmplRFIDData(tmp_prt, "USER-01", writeUSERData, writeUSERData.Length);
            if (uRet != 0)
            {
                Console.WriteLine("Failed to set USER data in template，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //10.Read TID data first
            uRet = DSTP2x_RFID_ReadData(dev_prt, pTIDData, ref pTIDDataLen, null, ref pEPCDataLen, null, ref pUSERDataLen);
            if (uRet != 0)
            {
                Console.WriteLine("Failed to get TID data firstly，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }
            else
                Console.WriteLine("Get the TID data is " + pTIDData.ToString(0, pTIDDataLen));

            //11.Print the template.
            uRet = DSTP2x_PrintTmpl(dev_prt, tmp_prt, szOutFile, ref pOutFileSize, szOutRFID, ref pOutRFIDSize);
            if (uRet != 0)
            {
                Console.WriteLine("Print template failed，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }
            else
                Console.WriteLine("The RFID data is " + szOutRFID.ToString(0, pOutRFIDSize));

            //12.Delete the handle of template.
            uRet = DSTP2x_DeleteTmpl(tmp_prt);
            if (uRet != 0)
            {
                Console.WriteLine("Delete handle of template failed，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //13.Disconnect the device.
            uRet = DSTP2x_DisconnDev(dev_prt);
            if (uRet != 0)
            {
                Console.WriteLine("Delete handle of device failed，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            Console.WriteLine("This example has been successfully demonstrated!");
        SAMPLE_END:
            //DeInit Library.
            uRet = DSTP2x_Lib_Clear();
            Console.ReadKey();

        }
    }
}
