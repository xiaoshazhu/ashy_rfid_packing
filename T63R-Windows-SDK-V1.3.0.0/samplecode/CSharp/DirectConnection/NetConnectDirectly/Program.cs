using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Runtime.InteropServices;
using DEV_HDL = System.UInt32;
using LC_HDL = System.UInt32;

namespace NetConnectDirectly
{
    //Connect directly to the network based on IP and port
    class Program
    {
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_Lib_Init(string pSzInitInfo, Int32 nInitInfoLen, StringBuilder pSzResult, ref int pResultLen);
        
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_Lib_Clear();
                
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_ConnNetworkDev(string szIpPort, ref DEV_HDL pDevHdl);
        
        [DllImport("../../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_DisconnDev(DEV_HDL ullDevHdl);      
        
       

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
            Console.WriteLine("Please input the IP and port like this \"192.168.0.7:9100\":");
            string input = Console.ReadLine();
            Console.WriteLine("\nThe ip and port is {0}\n", input);

            //2.Connect the device.
            uRet = DSTP2x_ConnNetworkDev(input, ref dev_prt);
            if (uRet != 0)
            {
                Console.WriteLine("Failed to connect device directly by net，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }
            else
            {
                Console.WriteLine("Connection successful!");
            }

            //3.Disconnect the device.
            uRet = DSTP2x_DisconnDev(dev_prt);
            if (uRet != 0)
            {
                Console.WriteLine("Delete handle of device failed，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            Console.WriteLine("This example has been successfully demonstrated!");
SAMPLE_END:
            //4.DeInit Library
            uRet = DSTP2x_Lib_Clear();
            Console.ReadKey();

        }
    }
}
