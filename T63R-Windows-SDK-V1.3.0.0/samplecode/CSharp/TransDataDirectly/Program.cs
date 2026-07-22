using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Runtime.InteropServices;
using DEV_HDL = System.UInt32;
using LC_HDL = System.UInt32;

namespace TransDataDirectly
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
        public static extern UInt32 DSTP2x_TransRecvData(DEV_HDL ullDevHdl, Byte[] pInData, Int32 nInDataSize, StringBuilder pOutData, ref int nOutDataSize);

        static byte[] HexStringToBinary(string hexString)
        {
            hexString = hexString.Replace(" ", "");
            return Enumerable.Range(0, hexString.Length)
                             .Where(x => x % 2 == 0)
                             .Select(x => Convert.ToByte(hexString.Substring(x, 2), 16))
                             .ToArray();            
        }


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

            //1-ZPL, 2-TSPL, 3-ESCPOS
            int iEmulationType = 1; 

            string[] szEmulationPaths = {
                /***************ZPL*******************/
		        "^XA^PW600^LL200^SEE:GB18030.DAT^CI26^CWL,E:simsun.fnt^FO0,10^ALN,40,40^FD Print Test LABEL^FS^XZ", 
		        /**************TSPL******************/
		        "CLS\r\nSIZE 4,1\r\nTEXT 110,50,\"3\",0,1,1,\"Print Test LABEL\"\r\nPRINT 1\r\n", 
		        /**************ESCPOS**************/
		        "1b401c261d21001b4d001b2d001b45005072696E742054657374204C4142454C0a1d564100"};

            StringBuilder pEnumList = new StringBuilder(500);
            Int32 enumListLen = 500;

            Int32 deviceNum = 0;
            String device = "";

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

            //4.According the emulation to transfer data
            StringBuilder pOutData = new StringBuilder();
            int nOutDataSize = 0;
            
            if(iEmulationType == 3)
            {
                Byte[] cmdData = HexStringToBinary(szEmulationPaths[iEmulationType - 1]);
                uRet = DSTP2x_TransRecvData(dev_prt, cmdData, cmdData.Length, pOutData, ref nOutDataSize);
            }
            else
                uRet = DSTP2x_TransRecvData(dev_prt, System.Text.Encoding.Default.GetBytes(szEmulationPaths[iEmulationType - 1]), szEmulationPaths[iEmulationType - 1].Length, pOutData, ref nOutDataSize);

            if (uRet != 0)
            {
                Console.WriteLine("Failed to transfer data，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //5.Disconnect the device.
            uRet = DSTP2x_DisconnDev(dev_prt);
            if (uRet != 0)
            {
                Console.WriteLine("Delete handle of device failed，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            Console.WriteLine("This example has been successfully demonstrated!");
        SAMPLE_END:
            //6.DeInit Library.
            uRet = DSTP2x_Lib_Clear();
            Console.ReadKey();

        }
    }
}
