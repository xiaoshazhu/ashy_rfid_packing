using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Runtime.InteropServices;
using DEV_HDL = System.UInt32;
using LC_HDL = System.UInt32;

namespace GetPrtInfo
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
        public static extern UInt32 DSTP2x_SetLibLang(Int32 nLanguage);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_GetPrtStatus(DEV_HDL ullDevHdl, ref int pIsReady, int[] pMainStatus, ref int pMainStatusNum, int[] pWarning, ref int pWarningNum, int[] pError, ref int pErrorNum, StringBuilder pDesc, ref int pDescLen);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_GetPrtSN(DEV_HDL ullDevHdl, StringBuilder szPrtSN, ref int pPrtSNSize);

        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_GetPrtFWVer(DEV_HDL ullDevHdl, StringBuilder szPrtFWVer, ref int pPrtFWVerSize);


        static void Main(string[] args)
        {
            UInt32 uRet = 0;
            StringBuilder pSzResult = new StringBuilder(256);
            Int32 pResultLen = 256;

            string[] pMainStatusDescGroup = {
		        "Device idle", 	//1
		        "Device busy"		, 	//2
		        "Cache is not empty", 	//3
		        "Cache is empty", 	//4
		        "The panel is in the set state", 	//5
		        "Label reading and writing completed", 	//6
		        "The retry and invalidation process is in progress", 	//7
		        "The make-up printing process is in progress", 	//8
		        "RFID automatic verification in progress", 	//9
		        "RFID custom command in progress", 	//10
		        "No RFID module" 	//11
	        };

	        string[] pWarnStatusDescGroup = {
		        "Paper is about to run out"  //1000
	        };
	
	        string[] pErrorStatusDescGroup = {
		        "Label or black label positioning error", //2000
		        "Paper jam", //2001
		        "Paper tearing error", //2002
		        "Lack of paper", //2003
		        "Knife error", //2004
		        "Paper loading error", //2005
		        "Carbon tape error", //2006
		        "Lifting the print head", //2007
		        "Printing head overheating"		, //2008
		        "EPC data missing in print data", //2009
		        "RFID re printing failed", //2010
		        "RFID calibration failed", //2011
		        "RFID error", //2012
		        "Pause or offline" //2013
	        };

            //1.Initialize the Library.
            uRet = DSTP2x_Lib_Init("", 0, pSzResult, ref pResultLen);
            if (uRet != 0)
            {
                Console.WriteLine("DSTP2x_Lib_Init，error code:[" + uRet.ToString() + "]");
                Console.ReadKey();
                return;
            }

            DEV_HDL dev_prt = 0;            
            StringBuilder pEnumList = new StringBuilder(500);
            Int32 enumListLen = 500;
            
            StringBuilder szPrtFWVer = new StringBuilder(128);
            Int32 pPrtFWVerSize = 128;
            
            StringBuilder szPrtSN = new StringBuilder(128);
            Int32 pPrtSNSize = 128;
            
            Int32 deviceNum = 0;
            String device = "";
            
            int isReady = 0;
            int[] pMainStatus = new int[15];
            int mainStatusLen = 15;
            int[] pWarningStatus = new int[2];
            int warningStatusLen = 2;
            int[] pErrorStatus = new int[15];
            int errorStatusLen = 15;
            StringBuilder szStatusDesc = new StringBuilder(500);
            Int32 szStatusDescLen = 500;

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

            //Non essential interface.
            uRet = DSTP2x_SetLibLang(1);//set language is English
            if (uRet != 0)
            {
                Console.WriteLine("Failed to set language，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //4.Get the printer serial number.
            uRet = DSTP2x_GetPrtSN(dev_prt, szPrtSN, ref pPrtSNSize );
            if (uRet != 0)
            {
                Console.WriteLine("Failed to obtain printer serial number，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }
            else
                Console.WriteLine("The printer serial number is " + szPrtSN.ToString(0, pPrtSNSize));

            //5.Get the firmware version of printer.
            uRet = DSTP2x_GetPrtFWVer(dev_prt, szPrtFWVer, ref pPrtFWVerSize);
            if (uRet != 0)
            {
                Console.WriteLine("Failed to obtain firmware version number，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }
            else
                Console.WriteLine("The firmware version number is " + szPrtFWVer.ToString(0, pPrtFWVerSize));

            //6.Get the status of printer.
            uRet = DSTP2x_GetPrtStatus(dev_prt, ref isReady, pMainStatus, ref mainStatusLen, pWarningStatus, ref warningStatusLen,
                pErrorStatus, ref errorStatusLen, szStatusDesc, ref szStatusDescLen); //szStatusDesc is utf-8
            if (uRet != 0)
            {
                Console.WriteLine("Failed to obtain device status，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }
            else
            {
                Console.WriteLine("Main status: "); 
                for (int i = 0; i < mainStatusLen; i++)
                {
                    int idx = pMainStatus[i] - 1;
                    Console.WriteLine(pMainStatusDescGroup[idx] + "; ");
                }
                Console.WriteLine("\nWarning status: ");
                for (int i = 0; i < warningStatusLen; i++)
                {
                    int idx = pWarningStatus[i] - 1000;
                    Console.WriteLine(pWarnStatusDescGroup[idx] + "; ");
                }
                Console.WriteLine("\nError status: ");
                for (int i = 0; i < errorStatusLen; i++)
                {
                    int idx = pErrorStatus[i] - 2000;
                    Console.WriteLine(pErrorStatusDescGroup[idx] + "; ");
                }
                Console.WriteLine("\nThe device status is" + szStatusDesc);
            }            
            
            //7.Disconnect the device.
            uRet = DSTP2x_DisconnDev(dev_prt);
            if (uRet != 0)
            {
                Console.WriteLine("Delete handle of device failed，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            Console.WriteLine("This example has been successfully demonstrated!");
        SAMPLE_END:
            //8.DeInit Library.
            uRet = DSTP2x_Lib_Clear();
            Console.ReadKey();

        }
    }
}
