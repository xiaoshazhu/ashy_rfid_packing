package com.dstp2x.DSTP2xLib;
import com.sun.jna.AltCallingConvention;
import com.sun.jna.Library;
import com.sun.jna.Pointer;
import com.sun.jna.ptr.DoubleByReference;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.LongByReference;
import com.sun.jna.win32.StdCallLibrary;


public interface DSTP2xJnaLib extends Library {
    /**
     * @brief  Dynamic library initialization
     * @par    explain：
     * Used to initialize SDK library resources; After this dynamic library is loaded, the process must and only needs to successfully call this interface once.
     * Checking the description of the content of pSzResult when a call fails can help analyze the problem.
     * @note   If this interface has not been successfully called within the process, other interfaces will not function properly!!!
     * @param[in] 		pSzInitInfo 	Custom description information (default to '')
     * @param[in] 		nInitInfoLen 	Custom description information length
     * @param[out] 		pSzResult 		Return an explanation message of successful initialization or an error message of failed initialization, character encoding: utf-8. It is recommended to allocate no less than 1024 bytes of space
     * @param[in,out]  	pResultLen 		Return the length of the information, with the input parameter being the memory size of pSzResult, and the output parameter indicating the actual length of memory written to pSzResult
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_Lib_Init( String pSzInitInfo, int nInitInfoLen, Pointer pSzResult,IntByReference pResultLen);

    /**
     * @brief  Dynamic library cleaning
     * @par    explain：
     * The dynamic library must be called before uninstallation, and the process can call it once
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_Lib_Clear();

    /**
     * @brief  Obtain the version number of this library
     * @par    explain：
     * The version number of this thermal library consists of five sets of digits.
     * @param[out]           pLibVer 	              Used to store the returned version number information, it is recommended to pre allocate a buffer of no less than 16 bytes
     * @param[in,out] 		 pLibVerLen               When entering the parameter, it represents the buffer size of pLibVer, and when exiting, it represents the actual length of data stored in pLibVer
     * @return 0 represents success, non-zero represents failure
     */
     public int DSTP2x_GetLibVersion(Pointer pLibVer,IntByReference pLibVerLen);

    /**
     * @brief  Get information about this SDK/Lib
     * @par    explain：
     * @param[out]           pLibInfo 	              Used to store the returned library information, it is recommended to pre allocate a buffer of no less than 256 bytes
     * @param[in,out] 		 pLibInfoLen             When entering the parameter, it represents the buffer size of pLibInfo, and when exiting, it represents the actual length of data stored in pLibInfo
     * @return 0 represents success, non-zero represents failure
     */
     public int DSTP2x_GetLibInfo(Pointer pLibInfo, IntByReference pLibInfoLen);

    /**
     * @brief  Set library language
     * @par    explain：
     * Can be set to Chinese or English
     * @param[in]        nLanguage               language
     * @n 0 - Chinese (default)
     * @n 1 - Engligh
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetLibLang(int nLanguage);

    /**
     * @brief  Analyze the error code returned by the SDK interface
     * @par    explain：
     * Translate the error codes returned by the SDK interface into corresponding explanations
     * @param[in]        unSDKErrCode            Error code returned by SDK interface
     * @param[out]        szDesc                 Output string buffer, size: not less than 1024 bytes, character encoding of string: utf-8
     * @param[in, out]   pLen                    When entering parameters: the size of the buffer pointed to by szDesc, when exiting parameters: the actual length of the string written to the buffer pointed to by szDesc
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_ApiRtnCodeToMsg( int unSDKErrCode, Pointer szDesc, IntByReference pLen);

    /**
     * @brief  Set the network port to enumerate the number of times the printer is allowed to receive responses without being able to read data continuously
     * @par    explain：
     * Need to dynamically adjust according to the current LAN network environment
     * @param[in]            nTimes              Allow the number of consecutive times data cannot be read. If the network is congested, you can set it to 10; If the network is idle, you can set 5
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetNetEnumRecvTimes(int nTimes);

    /**
     * @brief  When setting up a network port to enumerate printers, multiple sub network segments need to be enumerated
     * @par    explain：
     *
     * @param[in]        szSubNets              Multiple sub network segments that need to be enumerated, separated by a '|' between the two sub network segments; Format: 192.168.1. * | 172.10. **
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetNetEnumSubNets(String szSubNets);


    /**
     * @brief  Search for online devices
     * @par    explain
     * Please ensure that the device is turned on and connected to the PC
     * @param[in]            nEnumType             Enumeration type
     * @n 1 - List USB devices online
     * @n 2 - List TCP online devices
     * @param[out]           szEnumList            List enumeration, separated by "\ n" if there are multiple devices
     * @param[in,out]        pDevSize              When entering the parameter, indicate the size of szElementList, and when exiting, indicate the actual length of the string filled in szElementList
     * @param[out]           pDevNum               The number of online devices enumerated
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_EnumDev(int nEnumType, Pointer szEnumList, IntByReference pDevSize, IntByReference pDevNum);

    /**
     * @brief  Connect devices by device name
     * @par    explain
     * Connect the devices in the device set obtained by enumerating the DSTP2x-EnumDev interface
     * @param[in]            szDevName              The name of a device in the szVNet List returned by DSTP2x-EnumDev
     * @param[out]           pDevHdl                Device handle address
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_ConnEnumeratedDev(String szDevName,LongByReference pDevHdl);
    public int DSTP2x_ConnEnumeratedDev(String szDevName,IntByReference pDevHdl);

    /**
     * @brief  Connect devices through IP and ports
     * @par    explain
     * Connect to the device directly through IP and port, and obtain the device handle.
     * @param[in]            szIpPort              Connect the device directly by passing in the IP address and port number, such as "165.469.2.23:5100"
     * @param[out]           pDevHdl                Device handle address
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_ConnNetworkDev(String szIpPort,LongByReference pDevHdl);
    public int DSTP2x_ConnNetworkDev(String szIpPort,IntByReference pDevHdl);

    /**
     * @brief  Connect devices through serial port number and baud rate
     * @par    explain
     * Connect the device directly through the serial port number and baud rate, and obtain the device handle.
     * @param[in]            nSerialNo              Serial port number
     * @param[in]            nBaudRate              BAUD
     * @param[out]           pDevHdl                Device handle address
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_ConnSerialDev( int nSerialNo, int nBaudRate, LongByReference pDevHdl);
    public int DSTP2x_ConnSerialDev( int nSerialNo, int nBaudRate, IntByReference pDevHdl);
    /**
     * @brief  Disconnect the device connection
     * @par    explain：
     *
     * @param[in]            ullDevHdl               Device handle address
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_DisconnDev(long ullDevHdl);
    public int DSTP2x_DisconnDev(int ullDevHdl);

    /**
     * @brief  Set communication timeout for connection
     * @par    explain
     *
     * @param[in]            ullDevHdl               Device handle address
     * @param[in]            nCommType               Set communication timeout type
     * @n 1 - Set USB timeout
     * @n 2 - Set TCP timeout
     * @n 3 - Set serial port timeout
     * @param[in]            unSendTimeout          Data transmission timeout, unit: milliseconds
     * @param[in]            unRecvTimeout          Data reception timeout, unit: milliseconds
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetCommTimeout(long ullDevHdl, int nCommType, int unSendTimeout,int unRecvTimeout);
    public int DSTP2x_SetCommTimeout(int ullDevHdl, int nCommType, int unSendTimeout,int unRecvTimeout);
    /**
     * @brief  Directly transmit data to the printer
     * @par    explain
     * Support direct instruction transmission or hexadecimal data communication; It also supports one-way instruction data, where pOutData can transmit 0 to indicate that the program does not need to receive response data from the printer in the future
     * @param[in]            ullDevHdl                 Device handle address
     * @param[in]            pInData 	               The data to be sent can be of string type or regular hexadecimal data
     * @param[in]            nInDataSize 	           The length corresponding to the data representing pInData
     * @param[out]           pOutData 	               A buffer used to store the response data returned by the printer. Please determine the length of the response data based on the requested data. It is recommended to pre allocate the buffer to no less than 1024 bytes
     * @param[in,out] 		 nOutDataSize              When entering the parameter, it represents the buffer size of pOutData, and when exiting, it represents the actual length of data stored in pOutData
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_TransRecvData(long ullDevHdl, Pointer pInData, int nInDataSize, Pointer pOutData, IntByReference nOutDataSize);
    public int DSTP2x_TransRecvData(int ullDevHdl, Pointer pInData, int nInDataSize, Pointer pOutData, IntByReference nOutDataSize);
    /**
     * @brief  Print self check page
     * @par    explain：
     * Print out the basic information of the device, including manufacturer, model, machine number, printing simulation type, etc
     * @param[in]            ullDevHdl                 Device handle address
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_PrintSelfCheckPage(long ullDevHdl);
    public int DSTP2x_PrintSelfCheckPage(int ullDevHdl);

    /**
     * @brief  Device cache clearing
     * @par    explain：
     * Implementation effect: equivalent to the effect achieved by a hard restart of the printer, including clearing cache
     * @param[in]            ullDevHdl                 Device handle address
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RestartPrt(long ullDevHdl);
    public int DSTP2x_RestartPrt(int ullDevHdl);

    /**
     * @brief  Instant paper cutting
     * @par    explain
     * Usage conditions: The current printer has a built-in cutter module and the cutter function is turned on
     * @param[in]            ullDevHdl                 Device handle address
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_CutPaper(long ullDevHdl);
    public int DSTP2x_CutPaper(int ullDevHdl);

    /**
     * @brief  Moving paper
     * @par    explain
     * Usage conditions: The current printer has a built-in RFID module and is turned on
     * @param[in]            ullDevHdl                 Device handle address
     * @param[in]            nDir                      Paper movement direction
     * @n 0 - 向前
     * @n 1 - 向后
     * @param[in]            dbDistance                Paper movement distance, unit: mm
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_MovePaper(long ullDevHdl, int nDir, double dbDistance);
    public int DSTP2x_MovePaper(int ullDevHdl, int nDir, double dbDistance);

    /**
     * @brief  Ordinary label positioning
     * @par    explain
     * Usage condition: The current printer paper mode is label paper
     * @param[in]            ullDevHdl                 Device handle address
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LocateLabel(long ullDevHdl);
    public int DSTP2x_LocateLabel(int ullDevHdl);

    /**
     * @brief  Continuous paper black label positioning
     * @par    explain
     * Usage condition: The current printer paper mode is label paper
     * @param[in]            ullDevHdl                 Device handle address
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LocateBlackMark(long ullDevHdl);
    public int DSTP2x_LocateBlackMark(int ullDevHdl);

    /**
     * @brief  Query printer status
     * @par    explain
     * Due to the occurrence of multiple states, warnings, and errors at the same time in the printer, the actual number of messages stored in pMainStatus, pWarning, and pError when this function returns may be more than one
     * @param[in]            ullDevHdl                 Device handle address
     * @param[out]           pIsReady 				   Determine whether the printer can continue to work normally, return 1 yes, 0 no; If 0 is passed, it means that no non parameters are used
     * @param[out]           pMainStatus 	           The array used to store the main state when the function returns, it is recommended to pre allocate 8 array elements; If 0 is passed, it means that no non parameters are used
     * @param[in,out] 		 pMainStatusNum 	       When entering the parameter, it represents the size of the pMainStatus array, and when exiting, it represents the actual number of main states stored in pMainStatus; If 0 is passed, it means that no non parameters are used
     * @param[out]           pWarning 	               When the function returns, an array is used to store warnings. It is recommended to pre allocate 8 array elements; If 0 is passed, it means that no non parameters are used
     * @param[in,out] 		 pWarningNum 	           When entering the parameter, it represents the size of the pWarning array, and when exiting, it represents the actual number of warning messages stored in pWarning; If 0 is passed, it means that no non parameters are used
     * @param[out]           pError 	               The array used to store error information when the function returns, it is recommended to pre allocate 8 array elements; If 0 is passed, it means that no non parameters are used
     * @param[in,out] 		 pErrorNum 	               When entering the parameter, it represents the size of the pError array, and when exiting, it represents the actual number of error messages stored in pError; If 0 is passed, it means that no non parameters are used
     * @param[out]			 pDesc					   Detailed descriptions of status, warnings, and errors, returned in string format such as: main status: xxx, xxx | warning: none | error: xxx, xxx; if 0 is passed, it means no non parametric is used
     * @param[in,out] 		 pDescLen				   When entering the parameter, it represents the buffer length of pDesc, and when exiting, it represents the actual length of pDesc content returned; If 0 is passed, it means that no non parameters are used
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_GetPrtStatus(long ullDevHdl, IntByReference pIsReady, IntByReference pMainStatus, IntByReference pMainStatusNum, IntByReference pWarning, IntByReference pWarningNum,IntByReference pError, IntByReference pErrorNum, Pointer pDesc, IntByReference pDescLen);
    public int DSTP2x_GetPrtStatus(int ullDevHdl, IntByReference pIsReady, IntByReference pMainStatus, IntByReference pMainStatusNum, IntByReference pWarning, IntByReference pWarningNum,IntByReference pError, IntByReference pErrorNum, Pointer pDesc, IntByReference pDescLen);

    /**
     * @brief  Query printer serial number
     * @par    explain
     *
     * @param[in]            ullDevHdl                 Device handle address
     * @param[out]           szPrtSN 	               A buffer used to store printer serial number strings, with ASCII character encoding and format such as 228022200001. It is recommended to pre allocate a buffer of no less than 32 bytes
     * @param[in,out] 		 pPrtSNSize 	           When entering the parameter, it represents the buffer size of szPrtSN, and when exiting, it represents the actual length of the string stored in szPrtSN (excluding '\ 0')
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_GetPrtSN(long ullDevHdl, Pointer szPrtSN, IntByReference pPrtSNSize);
    public int DSTP2x_GetPrtSN(int ullDevHdl, Pointer szPrtSN, IntByReference pPrtSNSize);
    /**
     * @brief  Query the firmware version number of the printer
     * @par    explain
     *
     * @param[in]            ullDevHdl                 Device handle address
     * @param[out]           szPrtFWVer 	           A buffer used to store printer serial number strings, with ASCII character encoding and format such as 01.08.00.0a. It is recommended to pre allocate a buffer of no less than 32 bytes
     * @param[in,out] 		 pPrtFWVerSize             When entering the parameter, it represents the buffer size of szPrtFWVer, and when exiting, it represents the actual length of the string stored in szPrtFWVer (excluding '\ 0')
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_GetPrtFWVer(long ullDevHdl, Pointer szPrtFWVer, IntByReference pPrtFWVerSize);
    public int DSTP2x_GetPrtFWVer(int ullDevHdl, Pointer szPrtFWVer, IntByReference pPrtFWVerSize);


    /**
     * @brief  Query the rotation distance of the printer motor
     * @par    explain
     *
     * @param[in]            ullDevHdl                 Device handle address
     * @param[out]           pDistance 				   Return the distance of the printer motor rotation, in millimeters(mm)
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_GetPrtMotorTravelDistance(long ullDevHdl, IntByReference pDistance);
    public int DSTP2x_GetPrtMotorTravelDistance(int ullDevHdl, IntByReference pDistance);

    /**
     * @brief  Query printer model name
     * @par    explain
     *
     * @param[in]            ullDevHdl                 Device handle address
     * @param[out]           szPrtName 	           A buffer used to store the printer model name string, with ASCII character encoding. It is recommended to pre allocate the buffer to no less than 64 bytes
     * @param[in,out] 		 pPrtNameSize             When entering the parameter, it represents the buffer size of szPrtName, and when exiting, it represents the actual length of the string stored in szPrtName (excluding '\ 0')
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_GetPrtName(long ullDevHdl, Pointer szPrtName, IntByReference pPrtNameSize);
    public int DSTP2x_GetPrtName(int ullDevHdl, Pointer szPrtName, IntByReference pPrtNameSize);

    /**
     * @brief  Set printing offset
     * @par    explain
     * Due to the presence of substrates with varying distances around certain labels, in order to accurately print the content to the designated position on the label, users choose whether to call this function based on the actual situation of the label
     * @param[in]            ullDevHdl                 Device handle address
     * @param[in]            dbXOffset 	               The offset relative to the starting position of printing in the horizontal direction, unit: mm (millimeter)
     * @param[in] 		     dbYOffset                 Vertical offset relative to the starting position of printing, unit: mm (millimeter)
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetPrnOffset(long ullDevHdl, double dbXOffset, double dbYOffset);
    public int DSTP2x_SetPrnOffset(int ullDevHdl, double dbXOffset, double dbYOffset);

    /**
     * @brief  Set simulation type
     * @par    explain
     * Set the simulation type used for printing data
     * @param[in]            ullDevHdl                 Device handle address
     * @param[in]            nEmulation 	           emulation type
     * @n 0 - Automatically adapt to the current simulation of the printer (reserved)
     * @n 1 - ZPL
     * @n 2 - TSPL
     * @n 3 - ESCPOS
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetPrnEmulation(long ullDevHdl, int nEmulation);
    public int DSTP2x_SetPrnEmulation(int ullDevHdl, int nEmulation);

    /**
     * @brief  Set the resolution of the image to be drawn
     * @par    explain
     *
     * @param[in]            ullDevHdl                 Device handle address
     * @param[in]            nDpi 	                   Resolution of the image to be drawn
     * @n 1 - 203dpi
     * @n 2 - 300dpi
     * @n 3 - 600dpi
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetImgDpi(long ullDevHdl, int nDpi);
    public int DSTP2x_SetImgDpi(int ullDevHdl, int nDpi);

    /**
     * @brief  Set real-time status retrieval
     * @par    explain
     * If this function is not called, DSTP2x_GetPrtStatus will be non real time
     * @param[in]            ullDevHdl                 Device handle address
     * @param[in]            nRealtime                 real-time
     * @n 0 - Non real time; The printer supports non real time status retrieval by default (U port, network port, serial port); At this point, the printer executes instructions issued by the host in series, and status requests are not prioritized and processed in real-time
     * @n 1 - Real time; The printer currently only supports real-time status acquisition when connected through a USB port; At this point, the request to obtain status will be prioritized and processed in real-time
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetRTStatus(long ullDevHdl, int nRealtime);
    public int DSTP2x_SetRTStatus(int ullDevHdl, int nRealtime);

    /**
     * @brief  Activate the cutter function
     * @par    explain
     * If this function is not called, the cutting function will be turned off by default
     * @param[in]            ullDevHdl                 Device handle address
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_TurnOnCutter(long ullDevHdl);
    public int DSTP2x_TurnOnCutter(int ullDevHdl);

    /**
     * @brief  Turn off the cutter function
     * @par    explain
     *
     * @param[in]            ullDevHdl                 Device handle address
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_TurnOffCutter(long ullDevHdl);
    public int DSTP2x_TurnOffCutter(int ullDevHdl);

    /**
     * @brief  Set RFID reading power
     * @par    explain
     *
     * @param[in]            ullDevHdl                 Device handle address
     * @param[in]            dbPower                   RFID reading power, unit: dBm
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RFID_SetReadPower(long ullDevHdl, double dbPower);
    public int DSTP2x_RFID_SetReadPower(int ullDevHdl, double dbPower);

    /**
     * @brief  Set RFID write power
     * @par    explain
     *
     * @param[in]            ullDevHdl                 Device handle address
     * @param[in]            dbPower                   RFID write power, unit: dBm
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RFID_SetWritePower(long ullDevHdl, double dbPower);
    public int DSTP2x_RFID_SetWritePower(int ullDevHdl, double dbPower);

    /**
     * @brief  Obtain RFID reading power
     * @par    explain
     *
     * @param[in]            ullDevHdl                 Device handle address
     * @param[out]           pdbPower                  Pointer to the double variable used to obtain RFID read power, unit: dBm
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RFID_GetReadPower(long ullDevHdl, DoubleByReference pdbPower);
    public int DSTP2x_RFID_GetReadPower(int ullDevHdl, DoubleByReference pdbPower);

    /**
     * @brief  Obtain RFID write power
     * @par    explain
     *
     * @param[in]            ullDevHdl                 Device handle address
     * @param[out]           pdbPower                  Pointer to the double variable used to obtain RFID write power, unit: dBm
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RFID_GetWritePower(long ullDevHdl, DoubleByReference pdbPower);
    public int DSTP2x_RFID_GetWritePower(int ullDevHdl, DoubleByReference pdbPower);

    /**
     * @brief  Set RFID protocol
     * @par    explain
     *
     * @param[in]            ullDevHdl                 Device handle address
     * @param[in]            nProto                    Set protocol values
     * @n  0：ISO14443A protocol, (high-frequency module)
     * @n  1：ISO15693 protocol, (high-frequency module)
     * @n  5：ISO18000-6C protocol, (ultra-high frequency module)
     * @n  9：ISO18000-63 protocol, (military standard module)
     * @n  10：GB/T 29768 protocol, (National Military Standard Module)
     * @n  11：GJB 7377.1 protocol, (military standard module)
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RFID_SetProto(long ullDevHdl, int nProto);
    public int DSTP2x_RFID_SetProto(int ullDevHdl, int nProto);


    /**
     * @brief  Obtain RFID protocol
     * @par    explain
     *
     * @param[in]            ullDevHdl                 Device handle address
     * @param[out]           pProto					   Return protocol value
     * @n  0：ISO14443A protocol, (high-frequency module)
     * @n  1：ISO15693 protocol, (high-frequency module)
     * @n  5：ISO18000-6C protocol, (ultra-high frequency module)
     * @n  9：ISO18000-63 protocol, (military standard module)
     * @n  10：GB/T 29768 protocol, (National Military Standard Module)
     * @n  11：GJB 7377.1 protocol, (military standard module)
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RFID_GetProto(long ullDevHdl, IntByReference pProto);
    public int DSTP2x_RFID_GetProto(int ullDevHdl, IntByReference pProto);


    /**
     * @brief  RFID tag positioning
     * @par    explain
     *
     * @param[in]            ullDevHdl                 Device handle address
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RFID_LocateLabel(long ullDevHdl);
    public int DSTP2x_RFID_LocateLabel(int ullDevHdl);

    /**
     * @brief  Read TID,EPC,USER
     * @par    explain
     * This interface function is suitable for directly reading TID, EPC, and USER without printing
     * @param[in]            ullDevHdl                 Device handle address
     * @param[out]           pTid                      A buffer used to receive TID data read back from RFID tags; If TID data does not need to be read, this parameter can be passed as 0
     * @param[in,out] 		 pTidSize                  When entering the parameter, it represents the buffer size of pTid, and when exiting, it represents the actual length of data stored in pTid; If TID data does not need to be read, this parameter can be passed as 0
     * @param[out]           pEpc                      A buffer used to receive EPC data read back from RFID tags; If there is no need to read EPC data, this parameter can be passed as 0
     * @param[in,out] 		 pEpcSize                  When entering the parameter, it represents the buffer size of pEpc, and when exiting, it represents the actual length of data stored in pEpc; If there is no need to read EPC data, this parameter can be passed as 0
     * @param[out]           pUser                     A buffer used to receive USER data read back from RFID tags; If there is no need to read USER data, pass 0 for this parameter
     * @param[in,out] 		 pUserSize                 When entering the parameter, it represents the actual length of the USER data in the tag, and when exiting, it represents the actual length of the data stored in pUser; If there is no need to read USER data, pass 0 for this parameter
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RFID_ReadData(long ullDevHdl, Pointer pTid, IntByReference pTidSize, Pointer pEpc, IntByReference pEpcSize, Pointer pUser, IntByReference pUserSize);
    public int DSTP2x_RFID_ReadData(int ullDevHdl, Pointer pTid, IntByReference pTidSize, Pointer pEpc, IntByReference pEpcSize, Pointer pUser, IntByReference pUserSize);

    /**
     * @brief  Change the access password for RFID tags
     * @par    explain
     * Called before printing, valid for a single label;
     * Changing the password takes effect when printing;
     * @param[in]           ullDevHdl                 Device handle address
     * @param[in] 			szOldPw					  The initial password for RFID tags is an 8-bit hexadecimal string
     * @param[in]           szNewPw                   Set a new password for the RFID tag, which should be an 8-digit hexadecimal string, but not all zeros
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RFID_ChangeAccessPassword(long ullDevHdl, String tagPwdOld, String tagPwdNew);
    public int DSTP2x_RFID_ChangeAccessPassword(int ullDevHdl, String tagPwdOld, String tagPwdNew);

    /**
     * @brief  Set the destruction password for RFID tags
     * @par    explain
     * Called before printing, valid for a single label;
     * The password set will take effect when printing;
     * @param[in]           ullDevHdl                 Device handle address
     * @param[in] 			szPw					  The destruction password for RFID tags is an 8-digit hexadecimal string, please note that it cannot contain all zeros
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RFID_SetDestructionPassword(long ullDevHdl, String szPw);
    public int DSTP2x_RFID_SetDestructionPassword(int ullDevHdl, String szPw);

    /**
     * @brief  RFID lock type setting
     * @par    explain
     * Support repeated calls before printing, for example: the EPC and USER areas were originally permanently locked, and then the USER area was set as a temporary lock. At this time, the permanent lock of the EPC area remains valid;
     * When called repeatedly, nTemporal is based on the last call;
     * When this interface is not called, it defaults to a temporary lock;
     * @param[in]           ullDevHdl                 Device handle address
     * @param[in] 			nRFIDArea				  RFID area (or relationship), 1: EPC area, 2: User area, 8: Access password area, 16: Destruction password area
     * @param[in] 			nLockType				  0: Permanent lock, 1: Temporary lock
     * @param[in]           nTemporary                Is this setting temporary
     * @n 0 - Persistent until ullDevHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent print interface (PrintXXX) call
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RFID_LockTypeSetting(long ullDevHdl, int nRFIDArea, int nLockType, int nTemporary);
    public int DSTP2x_RFID_LockTypeSetting(int ullDevHdl, int nRFIDArea, int nLockType, int nTemporary);

    /**
     * @brief  Lock a specific RFID area
     * @par    explain
     * Support locking of EPC area, USER area, access password area, and password destruction area;
     * Called before printing, valid for a single label;
     * @param[in]           ullDevHdl                 Device handle address
     * @param[in] 			nRFIDArea				  RFID area (or relationship), 1: EPC area, 2: User area, 8: Access password area, 16: Destruction password area
     * @param[in] 			szPw					  The password for the RFID tag is an 8-bit hexadecimal string
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RFID_LockOperate(long ullDevHdl, int nRFIDArea, String szPw);
    public int DSTP2x_RFID_LockOperate(int ullDevHdl, int nRFIDArea, String szPw);

    /**
     * @brief  Unlock specific RFID areas
     * @par    explain
     * Support unlocking EPC area, USER area, access password area, and destroy password area;
     * Called before printing, valid for a single label;
     * @param[in]           ullDevHdl                 Device handle address
     * @param[in] 			nRFIDArea				  RFID area (or relationship), 1: EPC area, 2: User area, 8: Access password area, 16: Destruction password area
     * @param[in] 			szPw					  The password for the RFID tag is an 8-bit hexadecimal string
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RFID_UnlockOperate(long ullDevHdl, int nRFIDArea, String szPw);
    public int DSTP2x_RFID_UnlockOperate(int ullDevHdl, int nRFIDArea, String szPw);

    /**
     * @brief  Write a specific RFID area with password
     * @par    explain
     * Called before printing, valid for a single label;
     * If this interface is not called, writing without a password will be unsuccessful if the password has already been changed;
     * If the template already has a password field, it will be replaced;
     * @param[in]           ullDevHdl                 Device handle address
     * @param[in] 			nRFIDArea				  RFID area (or relationship), 1: EPC area, 2: User area
     * @param[in] 			szPw					  The password for the RFID tag is an 8-bit hexadecimal string, please note that the password for the same tag is the same
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_RFID_SetPasswordWithWrite(long ullDevHdl, int nRFIDArea, String szPw);
    public int DSTP2x_RFID_SetPasswordWithWrite(int ullDevHdl, int nRFIDArea, String szPw);

    /**
     * @brief  Load PDF data
     * @par    explain
     *
     * @param[in]            nPdfDataType              PDF data type
     * @n 1 - PDF data is the file name (including path)
     * @n 2 - PDF data is a string in base64 format
     * @param[in]            szPdfData 	               PDF data, character encoding: utf-8
     * @param[in]            nPdfDataSize 	           The length of the string representing szPdfData (excluding '\ 0') in bytes
     * @param[out]           pPdfHdl                   Address of PDF file handle
     * @param[out]           pPageCount                The total number of pages in the current PDF file
     * @return0 represents success, non-zero represents failure
     */
    public int DSTP2x_LoadPdf(int nPdfDataType, String szPdfData, int nPdfDataSize, LongByReference pPdfHdl, IntByReference pPageCount);
    public int DSTP2x_LoadPdf(int nPdfDataType, String szPdfData, int nPdfDataSize, IntByReference pPdfHdl, IntByReference pPageCount);

    /**
     * @brief  Print PDF
     * @par    explain
     * The szOutFile parameter needs to call DSTP2x_SetPdfPrnMode and nPrnMode is 1 or 2 to generate. png or. prn local files;
     * In order to use RFID functionality, DSTP2x_SetPdfPrnMode needs to be set to 0;
     * For RFID that requires both write and read functionality, it is necessary to first call DSTP2x_SetPdfRFIDData, set the read type in nRFidReadType, and allocate szOutRFID memory;
     * For read-only functions that require RFID, there is no need to call the DSTP2x_SetPdfRFIDData interface, but it is necessary to allocate memory for szOutRFID;
     * RFID reading function is not required, nRFidReadType and szOutRFID need to be set to 0.
     * @param[in]            ullDevHdl                 Device handle address
     * @param[in]            ullPdfHdl                 Handle to PDF file returned by DSTP2x_LoadPdf function
     * @param[in]            nPageNo 	               Page numbers of the PDF file to be printed
     * @param[out]           szOutFile                 Used to store the local data file name (. prn or. png) (including the path) generated by this printing operation, it is recommended to pre allocate space of no less than 1024 bytes; If you do not need to obtain the local data file name generated by this printing operation, simply pass in 0 for this parameter
     * @param[in,out] 		 pOutFileSize              When entering the parameter, it represents the buffer size of szOutFile, and when exiting, it represents the actual string length stored in szOutFile; If szOutFile is 0, this parameter will be ignored
     * @param[in]            nRfidReadType             Is RFID data read and how to read it during the process of printing the current page data
     * @n 0 - Do not read
     * @n 1 - Read TID
     * @n 2 - Read EPC
     * @n 4 - Read User
     * @param[out]           szOutRFID                The buffer used to store the RFID data read during the printing process, please determine the pre allocated buffer space size based on the nRFidReadType (combination) type;
     *                                                The read RFID data is returned after dynamic RFID execution;
     *                                                The content format is as follows: "TID: 82309360 | EPC: 0123456789 | User: abcdef";
     *                                                If it is not necessary to obtain the RFID data read during the printing process, this parameter can be set to 0
     * @param[in,out] 		 pOutRFIDSize             When entering the parameter, it represents the buffer size of szOutRFID, and when exiting, it represents the actual length of data stored in szOutRFID; If szOutRFID is 0, this parameter will be ignored
     * @return0 represents success, non-zero represents failure
     */
    public int DSTP2x_PrintPdf(long ullDevHdl, long ullPdfHdl, int nPageNo,Pointer szOutFile,IntByReference pOutFileSize, int nRfidReadType, Pointer szOutRFID, IntByReference pOutRFIDSize);
    public int DSTP2x_PrintPdf(int ullDevHdl, int ullPdfHdl, int nPageNo,Pointer szOutFile,IntByReference pOutFileSize, int nRfidReadType, Pointer szOutRFID, IntByReference pOutRFIDSize);


    /**
     * @brief  Delete PDF handle
     * @par    explain
     *
     * @param[in]            ullPdfHdl                 Handle to PDF file returned by DSTP2x_LoadPdf function
     * @return0 represents success, non-zero represents failure
     */
    public int DSTP2x_DeletePdf(long ullPdfHdl);
    public int DSTP2x_DeletePdf(int ullPdfHdl);

    /**
     * @brief  Set PDF printing mode
     * @par    explain
     * Valid for the current handle.If this function is not called, the print mode defaults to 0
     * @param[in]            ullPdfHdl                 Handle to PDF file returned by DSTP2x_LoadPdf function
     * @param[in]            nPrnMode                  Printing mode; If this function is not called, the default printing mode is to print through a printer
     * @n 0 - Printing through a printer
     * @n 1 - Print to. prn file
     * @n 2 - Generate PNG format effect preview image file
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetPdfPrnMode(long ullPdfHdl, int nPrnMode);
    public int DSTP2x_SetPdfPrnMode(int ullPdfHdl, int nPrnMode);

    /**
     * @brief  Set whether DSTP2x-PrintPdf prints synchronization results in a single call
     * @par    explain
     * Valid for the current handle.If this function is not called, the PDF single print will synchronize the results
     * @param[in]            ullPdfHdl                 Handle to PDF file returned by DSTP2x_LoadPdf function
     * @param[in]            nSyncType                 Whether to print synchronization results
     * @n 0 - Non synchronous printing results, as long as the printing data of the current page is sent, this function returns; At this time, RFID read operations for DSTP2x_PrintPdf are not supported
     * @n 1 - Synchronize printing results. After the printing data of the current page is sent, this function continuously monitors the printing status internally until the printing is successfully completed before returning; If the printer encounters an error, the function returns immediately
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetPdfPrnSyncType(long ullPdfHdl, int nSyncType);
    public int DSTP2x_SetPdfPrnSyncType(int ullPdfHdl, int nSyncType);

    /**
     * @brief  Set the maximum timeout time for a single call of DSTP2x_PrintPdf
     * @par    explain
     * Valid for the current handle.If this function is not called, the default maximum timeout for a single PDF print is 15000 milliseconds
     * @param[in]            ullPdfHdl                 Handle to PDF file returned by DSTP2x_LoadPdf function
     * @param[in]            nTimeout                  Timeout, unit: milliseconds; It only takes effect when DSTP2x_PrintPdf is called as a synchronous result in a single call
     * @n -1 - If there are no software/hardware or communication errors during the printing process, DSTP2x_PrintPdf will wait indefinitely for the printing end condition to be met before returning
     * @n >0 - If there are no software/hardware or communication errors during the printing process, DSTP2x_PrintPdf will check whether the overall time consumption is greater than or equal to nTimeout while waiting for the printing end condition to be met;
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetPdfPrnTimeout(long ullPdfHdl, int nTimeout);
    public int DSTP2x_SetPdfPrnTimeout(int ullPdfHdl, int nTimeout);

    /**
     * @brief  Set the RFID data to be written during the PDF printing process
     * @par    explain
     * If this function is not called, RFID reading/writing will not be performed during the printing process
     * @param[in]            ullPdfHdl                 Handle to PDF file returned by DSTP2x_LoadPdf function
     * @param[in]            nPageNo                   Page numbers of the PDF file to be printed
     * @param[in]            nRfidRgnType              The type of area where RFID data needs to be written during the printing process
     * @n 1 - EPC area
     * @n 2 - User area
     * @param[in]            nRfidDataFmt              The RFID data format that needs to be written during the printing process
     * @n 1 - ASCII encoded string
     * @n 2 - Hexadecimal string
     * @n 3 - Hexadecimal byte data
     * @param[in]            pData                     RFID data to be written during the printing process
     * @param[in]            nDataSize                 The length of RFID data to be written during the printing process, in bytes; If nRFidDataMmt is 1 or 2, this parameter represents the actual string length (excluding "\ 0") of pData
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetPdfRFIDData(long ullPdfHdl, int nPageNo, int nRfidRgnType, int nRfidDataFmt, byte[] pData, int nDataSize);
    public int DSTP2x_SetPdfRFIDData(int ullPdfHdl, int nPageNo, int nRfidRgnType, int nRfidDataFmt, byte[] pData, int nDataSize);
    public int DSTP2x_SetPdfRFIDData(long ullPdfHdl, int nPageNo, int nRfidRgnType, int nRfidDataFmt, String pData, int nDataSize);
    public int DSTP2x_SetPdfRFIDData(int ullPdfHdl, int nPageNo, int nRfidRgnType, int nRfidDataFmt, String pData, int nDataSize);

    /**
     * @brief  Set PDF target print size
     * @par    explain
     * Valid for the current handle.
     * @param[in]            ullPdfHdl                 Handle to PDF file returned by DSTP2x_LoadPdf function
     * @param[in]            dbWidth                   Print width, unit: mm
     * @param[in]            dbHeight                  Printing height, unit: mm
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetPdfPrnSize(long ullPdfHdl, double dbWidth, double dbHeight);
    public int DSTP2x_SetPdfPrnSize(int ullPdfHdl, double dbWidth, double dbHeight);

    /**
     * @brief  Set PDF target printing rotation angle
     * @par    explain
     * Valid for the current handle.
     * @param[in]            ullPdfHdl                 Handle to PDF file returned by DSTP2x_LoadPdf function
     * @param[in]            nAngle                    Rotation angle, range [0, 90, 180, 270]
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetPdfPrnRotate(long ullPdfHdl, int nAngle);
    public int DSTP2x_SetPdfPrnRotate(int ullPdfHdl, int nAngle);

    /**
     * @brief  Set up a halftone processing algorithm for PDF images
     * @par    explain：
     *
     * @param[in]            ullPdfHdl                  Handle to PDF file returned by DSTP2x_LoadPdf function
     * @param[in]            nAlgorithm                Image algorithm
     * @n 1 - Error Diffusion
     * @n 2 - ordered dither
     * @n 3 - Threshold calculation algorithm (default)
     * @param[in]            nThreshold                 Threshold, effective when nAlgorithm is 3, range [0,255]
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetPdfHalftoneAlgo(long ullPdfHdl, int nAlgorithm, int nThreshold);
    public int DSTP2x_SetPdfHalftoneAlgo(int ullPdfHdl, int nAlgorithm, int nThreshold);

    /**
     * @brief  Load predefined label templates
     * @par    explain
     * The szFileName parameter must be generated by DSTP2xDemo.exe in the SDK package.
     * @param[in]            szFileName                Pre defined label template (including path) file name, character encoding: utf-8
     * @param[out]           pLTHdl                    Handle address of tag template file
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LoadLabelTmpl(String szFileName, LongByReference pLTHdl);
    public int DSTP2x_LoadLabelTmpl(String szFileName, IntByReference pLTHdl);

    /**
     * @brief  Print label template
     * @par    explain
     *
     * @param[in]            ullDevHdl                 Device handle address
     * @param[in]            ullLTHdl                  The label template file handle returned by the DSTP2x_LoadLabelTmpl function
     * @param[out]           szOutFile                 Used to store the local data file name (. prn or. png) (including the path) generated by this printing operation, it is recommended to pre allocate space of no less than 256 bytes; If you do not need to obtain the local data file name generated by this printing operation, simply pass in 0 for this parameter
     * @param[in,out] 		 pOutFileSize              When entering the parameter, it represents the buffer size of szOutFile, and when exiting, it represents the actual string length stored in szOutFile; If szOutFile is 0, this parameter will be ignored
     * @param[out]           szOutRFID                 The buffer used to store the RFID data read during the printing process, please determine the pre allocated buffer space size based on the nRFidReadType (combination) type;
     *                                                 The content format is as follows: "TID: 82309360 | EPC: 0123456789 | User: abcdef"
     *                                                 If it is not necessary to obtain the RFID data read during the printing process, this parameter can be set to 0
     * @param[in,out] 		 pOutRFIDSize              When entering the parameter, it represents the buffer size of szOutRFID, and when exiting, it represents the actual length of data stored in szOutRFID; If szOutRFID is 0, this parameter will be ignored
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_PrintTmpl(long ullDevHdl, long ullLTHdl,Pointer szOutFile, IntByReference pOutFileSize,Pointer szOutRFID,IntByReference pOutRFIDSize);
    public int DSTP2x_PrintTmpl(int ullDevHdl, int ullLTHdl,Pointer szOutFile, IntByReference pOutFileSize,Pointer szOutRFID,IntByReference pOutRFIDSize);

    /**
     * @brief  Delete tag template file handle
     * @par    explain
     *
     * @param[in]            ullLTHdl                   The label template file handle returned by the DSTP2x_LoadLabelTmpl function
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_DeleteTmpl(long ullLTHdl);
    public int DSTP2x_DeleteTmpl(int ullLTHdl);

    /**
     * @brief  Set the printing mode for label templates
     * @par    explain
     * If this function is not called, the print mode defaults to 0
     * @param[in]            ullLTHdl                  The label template file handle returned by the DSTP2x_LoadLabelTmpl function
     * @param[in]            nPrnMode                  Printing mode; If this function is not called, the default printing mode is to print through a printer
     * @n 0 - Printing through a printer
     * @n 1 - Print to. prn file
     * @n 2 - Generate PNG format effect preview image file
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetTmplPrnMode(long ullLTHdl, int nPrnMode);
    public int DSTP2x_SetTmplPrnMode(int ullLTHdl, int nPrnMode);

    /**
     * @brief  Set whether DSTP2x_PrintTmpl prints synchronization results in a single call
     * @par    explain
     * If this function is not called, the template will synchronize the results for a single print
     * @param[in]            ullLTHdl                  The label template file handle returned by the DSTP2x_LoadLabelTmpl function
     * @param[in]            nSyncType                 Whether to print synchronization results
     * @n 0 - Non synchronous printing results, as long as the printing data of the current page is sent, this function returns; At this time, RFID read operations for DSTP2x_PrintTmpl are not supported
     * @n 1 - Synchronize printing results. After the printing data of the current page is sent, this function continuously monitors the printing status internally until the printing is successfully completed before returning; If the printer encounters an error, the function returns immediately
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetTmplPrnSyncType(long ullLTHdl, int nSyncType);
    public int DSTP2x_SetTmplPrnSyncType(int ullLTHdl, int nSyncType);

    /**
     * @brief  Set the maximum timeout time for a single call of DSTP2x_PrintTmpl
     * @par    explain
     * If this function is not called, the default maximum timeout time for a single print of the template is 15000 milliseconds
     * @param[in]            ullLTHdl                  The label template file handle returned by the DSTP2x_LoadLabelTmpl function
     * @param[in]            nTimeout                  Timeout, unit: milliseconds; It only takes effect when DSTP2x_PrintTmpl is called as a synchronous result in a single call
     * @n -1 - If there are no software/hardware or communication errors during the printing process, DSTP2x_PrintTmpl will wait indefinitely for the printing end condition to be met before returning
     * @n >0 - If there are no software/hardware or communication errors during the printing process, DSTP2x_PrintTmpl will check whether the overall time consumption is greater than or equal to nTimeout while waiting for the printing end condition to be met;
     *         If so, return 'Operation execution timeout'
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetTmplPrnTimeout(long ullLTHdl, int nTimeout);
    public int DSTP2x_SetTmplPrnTimeout(int ullLTHdl, int nTimeout);

    /**
     * @brief  Set the actual RFID write substitute data for the element with the specified ID in the tag template
     * @par    explain
     * If this function is not called to set real replacement data for certain elements of the tag template that have already been created with IDs, the original IDs created in the template will be written to RFID using preset values during the subsequent printing process
     * @param[in]            ullLTHdl                  The label template file handle returned by the DSTP2x_LoadLabelTmpl function
     * @param[in]            szElemID                  Indicate the ID of a specific element in the tag template that requires actual data for RFID writing
     * @param[in]            pActualData               RFID data that needs to be written during the printing process
     * @param[in]            nActualDataSize           The length of RFID data to be written during the printing process, in bytes;
     *                                                 If pActualData is a string, then this parameter represents the actual string length (excluding "\ 0") of pActualData
     *                                                 If pActualData is hexadecimal byte data, then this parameter represents the actual length of data that pActualData should be written to
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetTmplRFIDData(long ullLTHdl,String szElemID, byte[] pActualData, int nActualDataSize);
    public int DSTP2x_SetTmplRFIDData(int ullLTHdl,String szElemID, byte[] pActualData, int nActualDataSize);
    public int DSTP2x_SetTmplRFIDData(long ullLTHdl,String szElemID, String pActualData, int nActualDataSize);
    public int DSTP2x_SetTmplRFIDData(int ullLTHdl,String szElemID, String pActualData, int nActualDataSize);

    /**
     * @brief  Set actual print substitution data for elements with specified IDs in the label template
     * @par    explain
     * If this function is not called to set real replacement data for certain elements with created IDs in the label template, the original ID created in the template will be printed using the preset values during the subsequent printing process
     * @param[in]            ullLTHdl                  The label template file handle returned by the DSTP2x_LoadLabelTmpl function
     * @param[in]            szElemID                  The ID of a specific element in the label template that needs to be printed using actual data
     * @param[in]            szActualData              Actual data to be printed (UTF-8)
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetTmplPrnData(long ullLTHdl, String szElemID, String szActualData);
    public int DSTP2x_SetTmplPrnData(int ullLTHdl, String szElemID, String szActualData);

    /**
     * @brief  Set alternative attribute values for elements with specified IDs in the tag template based on existing key values
     * @par    explain
     * If this function is not called to set real replacement data for certain elements with created IDs in the label template, the original ID created in the template will be printed using the preset values during the subsequent printing process
     * @param[in]            ullLTHdl                  The label template file handle returned by the DSTP2x_LoadLabelTmpl function
     * @param[in]            szElemID                  The ID of a specific element in the label template that needs to be printed using actual data
     * @param[in]            szKey					   The index key to which the data value belongs
     * @param[in]            szValue				   Actual data values that need to be printed (UTF-8)
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetTmplValByKey(long ullLTHdl, String szElemID, String szKey, String szValue);
    public int DSTP2x_SetTmplValByKey(int ullLTHdl, String szElemID, String szKey, String szValue);

    /**
     * @brief  Return the template file (. dlt) of the current label template
     * @par    explain
     * If you have previously modified some content or attribute data of the label template through the DSTP2x_SetTmplxxx interface and want to obtain the modified dlt template file, then call this interface. \n
     * Note: Before calling this interface, you need to first call DSTP2x-PrintTmpl to combine with the modification item to obtain the correct result.
     * @param[in]            ullLTHdl              The label template file handle returned by the DSTP2x_LoadLabelTmpl function
     * @param[out]           pFileName              If successful, return the template file path
     * @param[in,out]        pFileNameLen			When entering the parameter, it represents the buffer size of pFileName, and when exiting, it represents the actual length of data stored in pFileName
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_GetBackTmpl(long ullLTHdl, String pFileName, IntByReference pFileNameLen);
    public int DSTP2x_GetBackTmpl(int ullLTHdl, String pFileName, IntByReference pFileNameLen);

    /**
     * @brief  Create tag context
     * @par    explain
     *
     * @param[in]            dbWidth                   Target label width to be printed, unit: mm
     * @param[in]            dbHeight                  Target label height to be printed, unit: mm
     * @param[out]           pLCHdl                    Handle address of tag context
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_CreateLabelContext(double dbWidth, double dbHeight,LongByReference pLCHdl);
    public int DSTP2x_CreateLabelContext(double dbWidth, double dbHeight,IntByReference pLCHdl);

    /**
     * @brief  Draw text in the specified tag context
     * @par    explain：
     *
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[in]            dbX                       The horizontal axis of the text content block relative to the upper left corner of the label, in millimeters (mm)
     * @param[in]            dbY                       The vertical axis of the text content block relative to the upper left corner of the label, in millimeters (mm)
     * @param[in]            dbW                       The width of the text content block is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
     * @param[in]            dbH                       The height of the text content block is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
     * @param[in]            szText                    The text content that needs to be drawn in the drawing context, with character encoding: utf-8.
     * @return 0 represents success, non-zero represents failure
     */
    public int  DSTP2x_Lbl_DrawText(long ullLcHdl, double dbX, double dbY, double dbW, double dbH, String szText);
    public int  DSTP2x_Lbl_DrawText(int ullLcHdl, double dbX, double dbY, double dbW, double dbH, String szText);

    /**
     * @brief  Draw an image in the specified tag context
     * @par    explain：
     *
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[in]            dbX                       The horizontal axis of the image content block relative to the top left corner of the label, in millimeters (mm)
     * @param[in]            dbY                       The vertical axis of the image content block relative to the upper left corner of the label, in millimeters (mm)
     * @param[in]            dbW                       The width of the image content block is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
     * @param[in]            dbH                       The height of the image content block is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
     * @param[in]            dbScale                   The scaling factor relative to the original image size is a non negative floating-point number. If it is 0, it means this parameter is ignored, and the value range must be between 1 and 3
     * @param[in]            nImgDataType              Image data type
     * @n 0 - Local image files
     * @n 1 - Image memory data
     * @n 2 -Base64 format image data
     * @param[in]            szImage                   Image data needs to be drawn in the context of the drawing.
     * @param[in]            unImgDataSize             When nImgDataType is 1 and 2, the size of unImgDataSize is the actual memory size pointing to szImage. When nImgDataType is 0, the size of unImgDataSize is the length pointing to szImage.
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_Lbl_DrawImage(long ullLcHdl, double dbX, double dbY, double dbW, double dbH, double dbScale, int nImgDataType, String szImage, int unImgDataSize);
    public int DSTP2x_Lbl_DrawImage(int ullLcHdl, double dbX, double dbY, double dbW, double dbH, double dbScale, int nImgDataType, String szImage, int unImgDataSize);
    public int DSTP2x_Lbl_DrawImage(long ullLcHdl, double dbX, double dbY, double dbW, double dbH, double dbScale, int nImgDataType, Pointer szImage, int unImgDataSize);
    public int DSTP2x_Lbl_DrawImage(int ullLcHdl, double dbX, double dbY, double dbW, double dbH, double dbScale, int nImgDataType, Pointer szImage, int unImgDataSize);

    /**
     * @brief  Draw barcode in the specified label context
     * @par    explain：
     *
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[in]            dbX                       The horizontal axis of the image content block relative to the top left corner of the label, in millimeters (mm)
     * @param[in]            dbY                       The vertical axis of the image content block relative to the upper left corner of the label, in millimeters (mm)
     * @param[in]            dbW                       The width of the image content block is a non negative floating-point number, measured in millimeters (mm)
     * @param[in]            dbH                       The height of the image content block is a non negative floating-point number, measured in millimeters (mm)
     * @param[in]            nCodeType                 Generate barcode encoding type
     * @n 8 - CODE39
     * @n 20 - CODE128
     * @n 25 - CODE93
     * @n 34 - UPCA
     * @n 37 - UPCE
     * @n 55 - PDF417
     * @n 58 - QRCode
     * @n 72 - EAN14
     * @n 84 - MicroPDF417
     * @param[in]            szData                    Barcode data needs to be drawn in the context of the drawing.
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_Lbl_DrawBarCode(long ullLcHdl, double dbX, double dbY, double dbW, double dbH, int nCodeType, String szData);
    public int DSTP2x_Lbl_DrawBarCode(int ullLcHdl, double dbX, double dbY, double dbW, double dbH, int nCodeType, String szData);

    /**
     * @brief  Draw line segments in the specified label context
     * @par    explain：
     *
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_CreateLabelContext function
     * @param[in]            dbStartX                  The starting horizontal coordinate of the line segment relative to the upper left corner of the label as the origin, unit: mm (millimeter)
     * @param[in]            dbStartY                  The starting vertical coordinate of the line segment relative to the upper left corner of the label as the origin, unit: mm (millimeter)
     * @param[in]            dbEndX                    The end horizontal coordinate of the line segment relative to the upper left corner of the label as the origin, unit: mm (millimeter)
     * @param[in]            dbEndY                    The end vertical coordinate of the line segment relative to the upper left corner of the label as the origin, unit: mm (millimeter)
     * @param[in]            nLineWidth                Line segment width, unit: pixel
     * @param[in]            nLineType                 Line segment type, 0: solid line, 1: dashed line, 2: dotted line, 3: dotted line, 4: double dotted line
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_Lbl_DrawLine(long ullLcHdl, double dbStartX, double dbStartY, double dbEndX, double dbEndY, int nLineWidth, int nLineType);
    public int DSTP2x_Lbl_DrawLine(int ullLcHdl, double dbStartX, double dbStartY, double dbEndX, double dbEndY, int nLineWidth, int nLineType);

    /**
     * @brief  Print label template
     * @par    explain
     * The szOutFile parameter needs to call DSTP2x_SetLcPrnMode and nPrnMode is 1 or 2 to generate. png or. prn local files;
     * In order to use RFID functionality, DSTP2x_SetLcPrnMode needs to be set to 0;
     * For RFID that requires both write and read functions, it is necessary to first call DSTP2x_LcRfid_SetData, set the read type in nRFidReadType, and allocate szOutRFID memory;
     * For read-only functions that require RFID, there is no need to call the DSTP2x_LcRfid_SetData interface, but it is necessary to allocate memory for szOutRFID；
     * No need for RFID reading function, nRFidReadType and szOutRFID need to be set to 0。
     * @param[in]            ullDevHdl                 Device handle address
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[out]           szOutFile                 Used to store the local data file name (. prn or. png) (including the path) generated by this printing operation, it is recommended to pre allocate space of no less than 256 bytes; If you do not need to obtain the local data file name generated by this printing operation, simply pass in 0 for this parameter
     * @param[in,out] 		 pOutFileSize              When entering the parameter, it represents the buffer size of szOutFile, and when exiting, it represents the actual string length stored in szOutFile; If szOutFile is 0, this parameter will be ignored
     * @param[in]            nRfidReadType             Is RFID data read and how to read it during the process of printing the current page data
     * @n 0 - Do not read
     * @n 1 - Read TID
     * @n 2 - Read EPC
     * @n 4 - Read User
     * @param[out]           szOutRFID                 The buffer used to store the RFID data read during the printing process, please determine the pre allocated buffer space size based on the nRFidReadType (combination) type;
     *                                                 The read RFID data is returned after dynamic RFID execution;
     *                                                 The content format is as follows: "TID: 82309360 | EPC: 0123456789 | User: abcdef"；
     *                                                 If it is not necessary to obtain the RFID data read during the printing process, this parameter can be set to 0
     * @param[in,out] 		 pOutRFIDSize              When entering the parameter, it represents the buffer size of szOutRFID, and when exiting, it represents the actual length of data stored in szOutRFID; If szOutRFID is 0, this parameter will be ignored
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_PrintLc(long ullDevHdl, long ullLcHdl, Pointer szOutFile, IntByReference pOutFileSize, int nRfidReadType, Pointer szOutRFID,IntByReference pOutRFIDSize);
    public int DSTP2x_PrintLc(int ullDevHdl, int ullLcHdl, Pointer szOutFile, IntByReference pOutFileSize, int nRfidReadType, Pointer szOutRFID,IntByReference pOutRFIDSize);


    /**
     * @brief  Delete tag context handle
     * @par    explain
     *
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_Create LabelContext function
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_DeleteLabelContext(long ullLcHdl);
    public int DSTP2x_DeleteLabelContext(int ullLcHdl);

    /**
     * @brief  Set the printing mode for label context
     * @par     explain
     * If this function is not called, the print mode defaults to 0
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[in]            nPrnMode                  Printing mode; If this function is not called, the default printing mode is to print through a printer
     * @n 0 - Printing through a printer
     * @n 1 - Print to. prn file
     * @n 2 - Generate PNG format effect preview image file
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetLcPrnMode(long ullLcHdl, int nPrnMode);
    public int DSTP2x_SetLcPrnMode(int ullLcHdl, int nPrnMode);

    /**
     * @brief  Set the rotation angle of the entire canvas for label context
     * @par    explain
     * If this function is not called, the angle defaults to 0
     * @param[in]            ullLcHdl                 The label context handle returned by the DSTP2x_CreateLabelContext function
     * @param[in]            nAngle                   Rotation angle, range [0, 90, 180, 270]
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetLcPrnRotate(long ullLcHdl, int nAngle);
    public int DSTP2x_SetLcPrnRotate(int ullLcHdl, int nAngle);

    /**
     * @brief  Set whether DSTP2x_PrintLc prints synchronization results in a single call
     * @par    explain
     * If this function is not called, the template will synchronize the results for a single print
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_CreateLabelContext function
     * @param[in]            nSyncType                 Whether to print synchronization results
     * @n 0 - Non synchronous printing results, as long as the printing data of the current page is sent, this function returns; At this time, RFID read operations for DSTP2x_PrintLc are not supported
     * @n 1 - Synchronize printing results. After the printing data of the current page is sent, this function continuously monitors the printing status internally until the printing is successfully completed before returning; If the printer encounters an error, the function returns immediately
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetLcPrnSyncType(long ullLcHdl, int nSyncType);
    public int DSTP2x_SetLcPrnSyncType(int ullLcHdl, int nSyncType);

    /**
     * @brief  Set the maximum timeout time for a single call of DSTP2x_PrintLc
     * @par    explain
     * If this function is not called, the default maximum timeout time for a single print of the template is 15000 milliseconds
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_CreateLabelContext function
     * @param[in]            nTimeout                  Timeout, unit: milliseconds; It only takes effect when DSTP2x_PrintLc is called as a synchronous result in a single call
     * @n -1 - If there are no software/hardware or communication errors during the printing process, DSTP2x_PrintTmpl will wait indefinitely for the printing end condition to be met before returning
     * @n >0 - If there are no software/hardware or communication errors during the printing process, DSTP2x_PrintTmpl will check whether the overall time consumption is greater than or equal to nTimeout while waiting for the printing end condition to be met;
     *         If so, return 'Operation execution timeout'
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_SetLcPrnTimeout(long ullLcHdl, int nTimeout);
    public int DSTP2x_SetLcPrnTimeout(int ullLcHdl, int nTimeout);

    /**
     * @brief  Label Context Drawing Settings - Set the font name for the text content to be drawn
     * @par    explain：
     *
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[in]            nTemporary                Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent DSTP2x_Lbl_darawText or DSTP2x_Tbl_darawText call
     * @param[in]            szFontName                Font name, character encoding: utf-8
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LcDraw_SetTextFontName(long ullLcHdl, int nTemporary, String szFontName);
    public int DSTP2x_LcDraw_SetTextFontName(int ullLcHdl, int nTemporary, String szFontName);

    /**
     * @brief  Label Context Drawing Settings - Set the font size of the text content to be drawn
     * @par    explain：
     *
     * @param[in]            ullLcHdl                   The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[in]            nTemporary                Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a DSTP2x_SrawText call
     * @param[in]            dbFontSize                Font size, in pounds
     * @return 0 represents success, non-zero represents failure
     */
    public int  DSTP2x_LcDraw_SetTextFontSize(long ullLcHdl, int nTemporary, double dbFontSize);
    public int  DSTP2x_LcDraw_SetTextFontSize(int ullLcHdl, int nTemporary, double dbFontSize);

    /**
     * @brief  Label Context Drawing Settings - Set whether to bold the text to be drawn
     * @par    explain：
     *
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[in]            nTemporary                Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent DSTP2x_Lbl_darawText or DSTP2x_Tbl_darawText call
     * @param[in]            nIsBold                   Bold or not, legal values: 0 and 1; Set [2,5] to bold level
     * @return 0 represents success, non-zero represents failure
     */
    public int  DSTP2x_LcDraw_SetTextBold(long ullLcHdl, int nTemporary, int nIsBold);
    public int  DSTP2x_LcDraw_SetTextBold(int ullLcHdl, int nTemporary, int nIsBold);

    /**
     * @brief  Label Context Drawing Settings - Set the horizontal alignment of the text to be drawn
     * @par    explain
     *
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_CreateLabelContext function
     * @param[in]            nTemporary                Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent DSTP2x_Lbl_darawText or DSTP2x_Tbl_darawText call
     * @param[in]            dbX                       The horizontal axis of the alignment line
     * @param[in]            nAlign                    justification
     * @n 0 - No alignment feature
     * @n 1 - Align to the left
     * @n 2 - center aligned
     * @n 3 - Right aligned
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LcDraw_SetTextHAlign(long ullLcHdl, int nTemporary, double dbX, int nAlign);
    public int DSTP2x_LcDraw_SetTextHAlign(int ullLcHdl, int nTemporary, double dbX, int nAlign);

    /**
     * @brief  Label Context Drawing Settings - Set the vertical alignment of the text to be drawn
     * @par    explain
     *
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_CreateLabelContext function
     * @param[in]            nTemporary                Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent DSTP2x_Lbl_darawText or DSTP2x_Tbl_darawText call
     * @param[in]            dbY                       The vertical axis of the alignment line
     * @param[in]            nAlign                    justification
     * @n 0 - No alignment feature
     * @n 1 - top align
     * @n 2 - center aligned
     * @n 3 - Bottom alignment
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LcDraw_SetTextVAlign(long ullLcHdl, int nTemporary, double dbY, int nAlign);
    public int DSTP2x_LcDraw_SetTextVAlign(int ullLcHdl, int nTemporary, double dbY, int nAlign);

    /**
     * @brief  Label Context Drawing Settings - Set whether the text to be drawn is italicized or not
     * @par    explain：
     *
     * @param[in]            ullLcHdl                The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[in]            nTemporary               Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent DSTP2x_Lbl_darawText or DSTP2x_Tbl_darawText call
     * @param[in]            nIsItalic                 Is it italicized? Value range: [0,1]
     * @n 0 - Do not use italics
     * @n 1 - Use italics
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LcDraw_SetTextItalic(long ullLcHdl, int nTemporary, int nIsItalic);
    public int DSTP2x_LcDraw_SetTextItalic(int ullLcHdl, int nTemporary, int nIsItalic);

    /**
     * @brief  Label Context Drawing Settings - Set whether the text to be drawn will automatically wrap
     * @par    explain：
     *
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_CreateLabelContext function
     * @param[in]            nTemporary                Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent DSTP2x_Lbl_darawText or DSTP2x_Tbl_darawText call
     * @param[in]            nIsAutoLineFeed           Does it automatically wrap? Value range: [0,1]
     * @n 0 - No Wrap
     * @n 1 - Automatic line wrapping
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LcDraw_SetTextAutoLineFeed(long ullLcHdl, int nTemporary, int nIsAutoLineFeed);
    public int DSTP2x_LcDraw_SetTextAutoLineFeed(int ullLcHdl, int nTemporary, int nIsAutoLineFeed);

    /**
     * @brief  Label Context Drawing Settings - Set the spacing between lines in the text to be drawn
     * @par    explain：
     *
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_CreateLabelContext function
     * @param[in]            nTemporary                Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent DSTP2x_Lbl_darawText or DSTP2x_Tbl_darawText call
     * @param[in]            dSpacing                  Row spacing, unit: pound
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LcDraw_SetTextLineSpacing(long ullLcHdl, int nTemporary, double dSpacing);
    public int DSTP2x_LcDraw_SetTextLineSpacing(int ullLcHdl, int nTemporary, double dSpacing);

    /**
     * @brief  Label Context Drawing Settings - Set the spacing between text characters to be drawn
     * @par    explain：
     *
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_CreateLabelContext function
     * @param[in]            nTemporary                Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent DSTP2x_Lbl_darawText or DSTP2x_Tbl_darawText call
     * @param[in]            dSpacing                  Word spacing, unit: pound
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LcDraw_SetTextCharSpacing(long ullLcHdl, int nTemporary, double dSpacing);
    public int DSTP2x_LcDraw_SetTextCharSpacing(int ullLcHdl, int nTemporary, double dSpacing);

    /**
     * @brief  Label Context Drawing Settings - Set Rotation Parameters for Text to be Drawn
     * @par    explain：
     *
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_CreateLabelContext function
     * @param[in]            nTemporary                Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent DSTP2x_Lbl_darawText or DSTP2x_Tbl_darawText call
     * @param[in]            nAngle                    Rotation angle, range [-360,360]
     * @param[in]            nAnchorPoint              Set the rotation reference center
     * @n 0 - top left corner
     * @n 1 - Middle point on the left
     * @n 2 - left lower corner
     * @n 3 - Center point
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LcDraw_SetTextRotation(long ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);
    public int DSTP2x_LcDraw_SetTextRotation(int ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);

    /**
     * @brief  Label context drawing settings - Set rotation parameters for the image to be drawn
     * @par    explain：
     *
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[in]            nTemporary                Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent DSTP2x_Lbl_darawImage or DSTP2x_Tbl_darawImage call
     * @param[in]            nAngle                    Rotation angle, range [-360,360]
     * @param[in]            nAnchorPoint              Set the rotation reference center
     * @n 0 - top left corner
     * @n 1 - Middle point on the left
     * @n 2 - left lower corner
     * @n 3 - Center point
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LcDraw_SetImageRotation(long ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);
    public int DSTP2x_LcDraw_SetImageRotation(int ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);

    /**
     * @brief  Label Context Drawing Settings - Set the Halftone Processing Algorithm for the Image to be Painted
     * @par    explain：
     *
     * @param[in]            ullLcHdl                 The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[in]            nTemporary                Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent DSTP2x_Lbl_darawImage or DSTP2x_Tbl_darawImage call
     * @param[in]            nAlgorithm               Image algorithm
     * @n 0 - Do not use algorithms (default)
     * @n 1 - Error Diffusion
     * @n 2 - ordered dither
     * @n 3 - Threshold operation algorithm
     * @param[in]            nThreshold               Threshold, effective when nAlgorithm is 3, range [0,255]
     * @return 0 represents success, non-zero represents failure
     */
    public int  DSTP2x_LcDraw_SetImageHalftoneAlgo(long ullLcHdl, int nTemporary, int nAlgorithm, int nThreshold);
    public int  DSTP2x_LcDraw_SetImageHalftoneAlgo(int ullLcHdl, int nTemporary, int nAlgorithm, int nThreshold);

    /**
     * @brief  Label Context Drawing Settings - Set the Error Correction Level for the QR Code to be Drawn
     * @par    explain：
     * This setting is applicable to two-dimensional barcode types such as PDC417, MicroPDF417, QRCode, etc
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[in]            nTemporary                Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent DSTP2x_Lbl_SrawBarCode or DSTP2x_Tbl_SrawBarCode call
     * @param[in]            nErrorCorrectLevel        Error correction level, the specific value range depends on the nCodeType of the DSTP2x-DrawCode function
     *                                                  When nCodeType is QRCode, the range of values for the eErrorCorrectLevel parameter is [1,4]. If not set, there is no error correction level by default
     *                                                  When nCodeType is PDF417, the range of values for the eErrorCorrectLevel parameter is [0,8]. If not set, the default error correction level is 2
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LcDraw_SetBarCodeEcLvl(long ullLcHdl, int nTemporary, int nErrorCorrectLevel);
    public int DSTP2x_LcDraw_SetBarCodeEcLvl(int ullLcHdl, int nTemporary, int nErrorCorrectLevel);

    /**
     * @brief  Label Context Drawing Settings - Set whether to print annotation lines for the one-dimensional code to be drawn
     * @par    explain：
     * This setting is applicable to various one-dimensional barcode types such as CODE39, CODE128, CODE93, UPC-A, UPC-E, EAN-8, EAN-13, EAN-14, etc
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[in]            nTemporary               Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent DSTP2x_Lbl_SrawBarCode or DSTP2x_Tbl_SrawBarCode call
     * @param[in]            nExplanation              Does the barcode generate annotations
     * @n 0 - Do not generate comments
     * @n 1 - Generate comments
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LcDraw_SetBarCodeExpl(long ullLcHdl, int nTemporary, int nExplanation);
    public int DSTP2x_LcDraw_SetBarCodeExpl(int ullLcHdl, int nTemporary, int nExplanation);

    /**
     * @brief  Label Context Drawing Settings - Set rotation parameters for one-dimensional and two-dimensional codes to be drawn
     * @par    explain：
     * This setting is applicable to various one-dimensional barcode types such as CODE39, CODE128, CODE93, UPC-A, UPC-E, EAN-8, EAN-13, EAN-14, etc
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_CreateLabelContext function
     * @param[in]            nTemporary                Is this setting temporary
     * @n 0 - Persistent until ullLcHdl fails, unless modified again
     * @n 1 - Temporarily, this setting is restored after a subsequent DSTP2x_Lbl_SrawBarCode or DSTP2x_Tbl_SrawBarCode call
     * @param[in]            nAngle                    Rotation angle, range [-360,360]
     * @param[in]            nAnchorPoint              Set the rotation reference center
     * @n 0 - top left corner
     * @n 1 - Middle point on the left
     * @n 2 - left lower corner
     * @n 3 - Center point
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LcDraw_SetBarCodeRotation(long ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);
    public int DSTP2x_LcDraw_SetBarCodeRotation(int ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);

    /**
     * @brief  Create table
     * @par    explain
     * 1. If the function is executed successfully, the newly created table handle will be returned by pTblHdl;
     * 2. Once a table is created, the number of rows and columns cannot be changed
     * 3. Tables support modifying table width, height, column width, row height, merging/restoring cells, drawing text, one-dimensional and two-dimensional barcodes, images, and other operations within cells
     * 4. The cell name arrangement of the created table, such as 3x2, will be represented in the following form:
     *  0-0 0-1 0-2\n 1-0 1-1 1-2
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[in]            dbX                       The horizontal axis in the upper left corner of the table, unit: mm (millimeter)
     * @param[in]            dbY                       The vertical axis in the upper left corner of the table, unit: mm (millimeter)
     * @param[in]            dbW                       The width of the table is a non negative floating point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
     * @param[in]            dbH                       The height of the table is a non negative floating point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
     * @param[in]            nRowCount                 The number of rows in the table to be created
     * @param[in]            nColCount                 The number of columns in the table to be created
     * @param[in]            nLineWidth                The width of the line in the box of the table to be created, unit: dot, value range: [1,50]
     * @param[out]           pTblHdl                   Handle address of the table
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_CreateTable(long ullLcHdl, double dbX, double dbY, double dbW, double dbH, int nRowCount, int nColCount, int nLineWidth, LongByReference pTblHdl);
    public int DSTP2x_CreateTable(int ullLcHdl, double dbX, double dbY, double dbW, double dbH, int nRowCount, int nColCount, int nLineWidth, IntByReference pTblHdl);

    /**
     * @brief  Change the column width of the table by moving the boundary lines of the columns
     * @par    explain
     * 1. The number of boundary lines in a column is 1 more than the number of columns
     * 2. The boundary clues of the column, from left to right, are 0, 1, 2, 3
     * 3. Since the starting position of the table is predetermined, the leftmost column boundary line (with index value 0) cannot be moved left or right
     * 3. Moving the boundary line of the rightmost column to the left or right will directly change the width of the table. Moving the boundary line between the leftmost and rightmost columns to the left or right will only change the column width on both sides of the boundary line, showing a trade-off relationship.
     * @param[in]            ullTblHdl                 The table handle returned by the DSTP2x_CreateTable function
     * @param[in]            nColSepLineIdx            The boundary clue of the column is referenced, with a value range of [1, n], where n is equal to the number of columns
     * @param[in]            nMoveDir                  The direction of movement of the boundary line
     * @n 1 - left shift
     * @n 2 - right shift
     * @param[in]            dbStep                    Step value of moving boundary line, unit: mm (millimeter), accuracy: 0.01mm
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_Tbl_MoveColBoundary(long ullTblHdl, int nColSepLineIdx, int nMoveDir, double dbStep);
    public int DSTP2x_Tbl_MoveColBoundary(int ullTblHdl, int nColSepLineIdx, int nMoveDir, double dbStep);

    /**
     * @brief  Change the row height of the table by moving the boundary lines of rows
     * @par    explain
     * 1. The number of boundary lines in a row is 1 more than the number of rows
     * 2. The boundary clues of the rows are 0, 1, 2, 3, etc. from top to bottom
     * 3. Since the starting position of the table is predetermined, the top row boundary line (with an index value of 0) cannot be moved up or down
     * 4. Moving the bottom column boundary line up or down will directly change the width of the table, while moving the boundary line between the top and bottom will only change the row height on both sides of the boundary line, showing a trade-off relationship.
     * @param[in]            ullTblHdl                 The table handle returned by the DSTP2x_Create Table function
     * @param[in]            nRowSepLineIdx            The boundary clue of the row is referenced, with a value range of [1, n], where n is equal to the number of rows
     * @param[in]            nMoveDir                  The direction of movement of the boundary line
     * @n 1 - move up
     * @n 2 - Move Down
     * @param[in]            dbStep                    Step value of moving boundary line, unit: mm (millimeter), accuracy: 0.01mm
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_Tbl_MoveRowBoundary(long ullTblHdl, int nRowSepLineIdx, int nMoveDir, double dbStep);
    public int DSTP2x_Tbl_MoveRowBoundary(int ullTblHdl, int nRowSepLineIdx, int nMoveDir, double dbStep);

    /**
     * @brief  merge cell
     * @par    explain
     *
     * @param[in]            ullTblHdl                 The table handle returned by the DSTP2x_CreateTable function
     * @param[in]            nRowBegin                 Starting row of cells to be merged
     * @param[in]            nRowEnd                   End row of cells to be merged
     * @param[in]            nColBegin                 Starting column of cells to be merged
     * @param[in]            nColEnd                   End column of cells to be merged
     * @param[out] 		     szMergedGridName          Name of the merged new cell, character code: utf-8， For example: "Merged-0"， Suggest allocating no less than 32 bytes of space
     * @param[in,out]  	     pMergedGridNameSize       Return the length of the information, with the input parameter being the memory size of szMergedGridName, and the output parameter indicating the actual length of memory written to szMergedGridName
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_Tbl_MergeGrids(long ullTblHdl, int nRowBegin, int nRowEnd, int nColBegin, int nColEnd,Pointer szMergedGridName,IntByReference pMergedGridNameSize);
    public int DSTP2x_Tbl_MergeGrids(int ullTblHdl, int nRowBegin, int nRowEnd, int nColBegin, int nColEnd,Pointer szMergedGridName,IntByReference pMergedGridNameSize);

    /**
     * @brief  Restore (merged) cells
     * @par    explain
     *
     * @param[in]            ullTblHdl                 The table handle returned by the DSTP2x_Create Table function
     * @param[out] 		     szMergedGridName          The name of the merged new cell returned by the DSTP2x_Tbl_margeGrids function
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_Tbl_RevertMergedGrid(long ullTblHdl, Pointer szMergedGridName);
    public int DSTP2x_Tbl_RevertMergedGrid(int ullTblHdl, Pointer szMergedGridName);

    /**
     * @brief  Draw text on specified cells in the table
     * @par    explain
     *
     * @param[in]            ullTblHdl                 The table handle returned by the DSTP2x_Create Table function
     * @param[out] 		     szGridName                Cell name, character encoding: utf-8； For example, the basic cells are "0-0", "0-1", "1-0", "1-1", etc; The merged cells are "Merged-0", "Merged-1", etc
     * @param[in]            dbX                       The horizontal axis of the upper left corner of the text content block relative to the upper left corner of the cell, in millimeters (mm)
     * @param[in]            dbY                       The vertical axis of the upper left corner of the text content block relative to the upper left corner of the cell, in millimeters (mm)
     * @param[in]            dbW                       The width of the text content block is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
     * @param[in]            dbH                       The height of the text content block is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
     * @param[in]            szText                    The text content that needs to be drawn in the drawing context, character encoding: utf-8。
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_Tbl_DrawText(long ullTblHdl, Pointer szGridName, double dbX, double dbY, double dbW, double dbH, String szText);
    public int DSTP2x_Tbl_DrawText(int ullTblHdl, Pointer szGridName, double dbX, double dbY, double dbW, double dbH, String szText);

    /**
     * @brief  Draw one-dimensional and two-dimensional barcodes on specified cells in the table
     * @par    explain
     *
     * @param[in]            ullTblHdl                 The table handle returned by the DSTP2x_CreateTable function
     * @param[out] 		     szGridName                Cell name, character encoding: utf-8； For example, the basic cells are "0-0", "0-1", "1-0", "1-1", etc; The merged cells are "Merged-0", "Merged-1", etc
     * @param[in]            dbX                       The horizontal axis of the upper left corner of the text content block relative to the upper left corner of the cell, in millimeters (mm)
     * @param[in]            dbY                       The vertical axis of the upper left corner of the text content block relative to the upper left corner of the cell, in millimeters (mm)
     * @param[in]            dbW                       The width of the text content block is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
     * @param[in]            dbH                       The height of the text content block is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
     * @param[in]            nCodeType                 Generate barcode encoding type
     * @n 8 - CODE39
     * @n 20 - CODE128
     * @n 25 - CODE93
     * @n 34 - UPCA
     * @n 37 - UPCE
     * @n 55 - PDF417
     * @n 58 - QRCode
     * @n 71 - DataMatrix
     * @n 72 - EAN14
     * @n 84 - MicroPDF417
     * @n 116 - HanXin
     * @n 142 - GridMatrix
     * @param[in]            szData                    Barcode data needs to be drawn in the context of the drawing.
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_Tbl_DrawBarCode(long ullTblHdl, Pointer szGridName, double dbX, double dbY, double dbW, double dbH, int nCodeType, String szData);
    public int DSTP2x_Tbl_DrawBarCode(int ullTblHdl, Pointer szGridName, double dbX, double dbY, double dbW, double dbH, int nCodeType, String szData);

    /**
     * @brief  Draw an image on a specified cell in the table
     * @par    explain
     *
     * @param[in]            ullTblHdl                 The table handle returned by the DSTP2x_CreateTable function
     * @param[out] 		     szGridName                Cell name, character encoding: utf-8； For example, the basic cells are "0-0", "0-1", "1-0", "1-1", etc; The merged cells are "Merged-0", "Merged-1", etc
     * @param[in]            dbX                       The horizontal axis of the upper left corner of the text content block relative to the upper left corner of the cell, in millimeters (mm)
     * @param[in]            dbY                       The vertical axis of the upper left corner of the text content block relative to the upper left corner of the cell, in millimeters (mm)
     * @param[in]            dbW                       The width of the text content block is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
     * @param[in]            dbH                       The height of the text content block is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
     * @param[in]            dbScale                   The scaling factor relative to the original image size is a non negative floating-point number. If it is 0, it means this parameter is ignored, and the value range must be between 1 and 3
     * @param[in]            nImgDataType              Image data type
     * @n 0 - Local image files
     * @n 1 - Image memory data
     * @n 2 - Base64 format image data
     * @param[in]            szImage                   Image data needs to be drawn in the context of the drawing.
     * @param[in]            unImgDataSize             When nImgDataType is 1 and 2, the size of unImgDataSize is the actual memory size pointing to szImage. When nImgDataType is 0, the size of unImgDataSize is the length pointing to szImage.
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_Tbl_DrawImage(long ullTblHdl, Pointer szGridName, double dbX, double dbY, double dbW, double dbH, double dbScale, int nImgDataType, String szImage, int unImgDataSize);
    public int DSTP2x_Tbl_DrawImage(int ullTblHdl, Pointer szGridName, double dbX, double dbY, double dbW, double dbH, double dbScale, int nImgDataType, String szImage, int unImgDataSize);

    /**
     * @brief  Delete table handle
     * @par    explain
     *
     * @param[in]            ullTblHdl                 Handle returned by DSTP2x_CreateTable function
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_DeleteTable(long ullTblHdl);
    public int DSTP2x_DeleteTable(int ullTblHdl);

    /**
     * @brief  Set the RFID data that needs to be written during the tag context printing process
     * @par    explain
     * If this function is not called, RFID reading/writing will not be performed during the printing process
     * @param[in]            ullLcHdl                  The label context handle returned by the DSTP2x_Create LabelContext function
     * @param[in]            nRfidRgnType              The type of area where RFID data needs to be written during the printing process
     * @n 1 - EPC区
     * @n 2 - USER区
     * @param[in]            nRfidDataFmt              The RFID data format that needs to be written during the printing process
     * @n 1 - ASCII encoded string
     * @n 2 - Hexadecimal string
     * @n 3 - Hexadecimal byte data
     * @param[in]            pData                     RFID data to be written during the printing process
     * @param[in]            nDataSize                 The length of RFID data to be written during the printing process, in bytes;
     *                                                  If pData is a string, this parameter represents the actual string length of pData (excluding "\ 0");
     *                                                  If pData is hexadecimal byte data, this parameter represents the actual length of data that pData should write
     * @return 0 represents success, non-zero represents failure
     */
    public int DSTP2x_LcRfid_SetData(long ullLcHdl, int nRfidRgnType, int nRfidDataFmt, byte[] pData, int nDataSize);
    public int DSTP2x_LcRfid_SetData(int ullLcHdl, int nRfidRgnType, int nRfidDataFmt, byte[] pData, int nDataSize);
    public int DSTP2x_LcRfid_SetData(long ullLcHdl, int nRfidRgnType, int nRfidDataFmt, String pData, int nDataSize);
    public int DSTP2x_LcRfid_SetData(int ullLcHdl, int nRfidRgnType, int nRfidDataFmt, String pData, int nDataSize);


}
