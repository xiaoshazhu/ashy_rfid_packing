using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Runtime.InteropServices;
using DEV_HDL = System.UInt32;
using PDF_HDL = System.UInt32;

namespace PdfPrintOnly
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
        public static extern UInt32 DSTP2x_LoadPdf(Int32 nPdfDataType, string szPdfData, Int32 nPdfDataSize, ref PDF_HDL pPdfHdl, ref int pPageCount);
        
        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_PrintPdf(DEV_HDL ullDevHdl, PDF_HDL ullPdfHdl, Int32 nPageNo, StringBuilder szOutFile, ref int pOutFileSize, Int32 nRfidReadType, StringBuilder szOutRFID, ref int pOutRFIDSize);
        
        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_DeletePdf(PDF_HDL ullPdfHdl);
        
        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_SetPdfPrnMode(PDF_HDL ullPdfHdl, Int32 nPrnMode);
        
        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_SetPdfPrnSize(PDF_HDL ullPdfHdl, Double dbWidth, Double dbHeight);
        
        [DllImport("../../../../../lib/Win32/libDSThermal.dll", CallingConvention = CallingConvention.StdCall, CharSet = CharSet.Ansi)]
        public static extern UInt32 DSTP2x_SetPdfPrnRotate(PDF_HDL ullPdfHdl, Int32 nAngle);


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
            PDF_HDL pdf_prt = 0;
            StringBuilder pEnumList = new StringBuilder(500);
            Int32 enumListLen = 500;
            StringBuilder szOutFile = new StringBuilder(500);
            Int32 pOutFileSize = 500;
            StringBuilder szOutRFID = new StringBuilder(128);
            Int32 pOutRFIDSize = 128;
            Int32 deviceNum = 0;
            String device = "";

            String pdfPath = "../../samplecode/CSharp/PdfPrintOnly/PDF.pdf";
            int pdfPagesCount = 0;

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

            //4.Load the file of pdf. 1-pdf file, 2-base64 of pdf.
            uRet = DSTP2x_LoadPdf(1, pdfPath, pdfPath.Length, ref pdf_prt, ref pdfPagesCount);
            if (uRet != 0)
            {
                Console.WriteLine("Failed to load pdf，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //5.Set the print mode. 0-print, 1-generate the prn file, 2-generate the preview image.
            uRet = DSTP2x_SetPdfPrnMode(pdf_prt, 0); //set print mode
            if (uRet != 0)
            {
                Console.WriteLine("Setting whether to print failed，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //Non essential interface.
            uRet = DSTP2x_SetPdfPrnRotate(pdf_prt, 0);
            if (uRet != 0)
            {
                Console.WriteLine("Failed to set pdf rotation，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //Non essential interface.
            uRet = DSTP2x_SetPdfPrnSize(pdf_prt, 80, 100);
            if (uRet != 0)
            {
                Console.WriteLine("Setting the size of pdf failed，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //6.Print the first page of pdf
            uRet = DSTP2x_PrintPdf(dev_prt, pdf_prt, 1, szOutFile, ref pOutFileSize, 0, szOutRFID, ref pOutRFIDSize);//print the first page of pdf
            if (uRet != 0)
            {
                Console.WriteLine("Print pdf failed，error code:[" + uRet.ToString() + "]");
                goto SAMPLE_END;
            }

            //7.Delete the handle of pdf.
            uRet = DSTP2x_DeletePdf(pdf_prt);
            if (uRet != 0)
            {
                Console.WriteLine("Delete handle of pdf failed，error code:[" + uRet.ToString() + "]");
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
            //9.DeInit Library.
            uRet = DSTP2x_Lib_Clear();
            Console.ReadKey();
        }
    }
}
