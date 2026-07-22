/**
*
* @file DSTP2x.h
* @brief DS API header file for thermal printer SDK
* @author SDK Team
* @date 2024-06-15
*
*
*/

#ifndef __DSTP2x_H__
#define __DSTP2x_H__


#if defined(_WIN32)    // win32 and win64

#ifndef DSSDK
#define DSSDK __stdcall
#endif

#if defined(_WIN64)
typedef unsigned long long DEV_HDL;                 // device handle
typedef unsigned long long LC_HDL;                  // label context handle
typedef unsigned long long PDF_HDL;				// pdf handle
typedef unsigned long long LABEL_TEMP_HDL;          // label template handle
typedef unsigned long long TABLE_HDL;               // table handle
#elif defined(_WIN32)
typedef unsigned int DEV_HDL;                       // device handle
typedef unsigned int LC_HDL;                        // label context handle
typedef unsigned int PDF_HDL;						// pdf handle
typedef unsigned int LABEL_TEMP_HDL;                // label template handle
typedef unsigned int TABLE_HDL;                     // table handle
#else
#error Unknown Platform
#endif

#elif defined(__linux__)    // linux

#ifndef DSSDK
#define DSSDK __attribute ((visibility("default")))
#endif

typedef unsigned long long DEV_HDL;                 // device handle
typedef unsigned long long LC_HDL;                  // label context handle
typedef unsigned long long PDF_HDL;				    // pdf handle
typedef unsigned long long LABEL_TEMP_HDL;          // label template handle
typedef unsigned long long TABLE_HDL;               // table handle
#else
#error Unknown Platform
#endif


#ifdef __cplusplus
extern "C"
{
#endif



	/** @defgroup DynamicLibraryRelatived, Basic library operation interface
	*   @brief Dynamic library interface, such as initialization, resource cleaning, setting library language, parsing error codes, etc
	*
	*  @{
	*
	*/


	/**
	* @brief dynamic library initialization
	* @par Explanation:
	* Used to initialize SDK library resources; After this dynamic library is loaded, the process must and only needs to successfully call this interface once.
	* Checking the description of the content of pSzResult when a call fails can help analyze the problem.
	* If this interface has not been successfully called within the process, other interfaces will not function properly!!!
	* 
	* @param [in] pSzInitInfo, Custom description information (default passed "")
	* 
	* @param [in] nInitInfoLen, Custom description information length
	* 
	* @param [out] pSzResult, It returns an explanation of successful initialization or an error message of failed initialization, with character encoding: utf-8£¬ Suggest allocating no less than 1024 bytes of space
	* 
	* @param [in, out] pResultLen, It returns the length of the information. The input parameter is the memory size of pSzResult, and the output parameter represents the actual length of memory written to pSzResult
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Lib_Init(char *pSzInitInfo, int nInitInfoLen, char *pSzResult, int *pResultLen);

	/**
	* @brief dynamic library cleaning
	* @par Explanation:
	* The dynamic library must be called before uninstallation, and the process can call it once
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Lib_Clear();


	/**
	* @brief Get the version number of this library
	* @par Explanation:
	* The version number of this thermal library consists of five sets of digits.
	* 
	* @param [out] pLibVer, It is used to store the returned version number information. It is recommended to pre allocate a buffer of no less than 16 bytes
	* 
	* @param [in, out] pLibVerLen, When it is input, it represents the buffer size of pLibVer, and when it is output, it represents the actual length of data stored in pLibVer
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_GetLibVersion(char *pLibVer, int *pLibVerLen);


	/**
	* @brief Get information from this library
	* @par Explanation:
	* 
	* @param [out] pLibInfo, It is used to store the returned library information. It is recommended to pre allocate a buffer of no less than 256 bytes
	* 
	* @param [in, out] pLibInfoLen, When parameterized, it represents the buffer size of pLibInfo, and when parameterized, it represents the actual length of data stored in pLibInfo
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_GetLibInfo(char *pLibInfo, int *pLibInfoLen);

	/**
	* @brief Set Library Language
	* @par Explanation:
	* Can be set to Chinese or English
	* 
	* @param [in] nLanguage language
	* @n 0- Chinese (default)
	* @n 1- English
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetLibLang(int nLanguage);


	/**
	* @brief parsing the error code returned by the SDK interface
	* @par Explanation:
	* Translate the error codes returned by the SDK interface into corresponding explanations
	* 
	* @param [in] unSDKErrCode, Error code returned by SDK interface
	* 
	* @param [out] szDesc, Output string buffer, size: not less than 1024 bytes, character encoding of string: utf-8
	* 
	* @param [in, out] pLen, Size of the buffer pointed to by szDesc when taking parameters, length of the string actually written to the buffer pointed to by szDesc when taking parameters out
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_ApiRtnCodeToMsg(unsigned int unSDKErrCode, char *szDesc, int *pLen);

	/**
	* 
	*  @}
	*/



	/** @defgroup DeviceConnection, Device Connect
	*    @brief Device enumeration, connection timeout settings, selected devices, etc
	* 
	*   @{
	* 
	*/

	/**
	* @brief: Set the network port to enumerate the number of consecutive times the printer cannot read data when receiving a response
	* @par Explanation
	* Need to dynamically adjust according to the current LAN network environment
	* 
	* @param [in] nTimes, It allows for the number of consecutive times data cannot be read. If the network is congested, you can set it to 10; If the network is idle, you can set 5
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetNetEnumRecvTimes(int nTimes);

	/**
	* When setting up a network port to enumerate printers, multiple sub network segments need to be enumerated
	* @par Explanation
	* 
	* @param [in] szSubNets, Multiple sub network segments that need to be enumerated, separated by a "|" between the two sub network segments; Format: 192.168.1.* | 172.10.*.*
	*
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetNetEnumSubNets(const char *szSubNets);


	/**
	* @brief Search for online devices
	* @par Explanation
	* Please ensure that the device is turned on and connected to the PC
	* 
	* @param [in] nEnumType, Enumeration type
	* @n 1- List USB devices online
	* @n 2- List TCP online devices
	* 
	* @param [out]szEnumList, enumeration list, separated by "\n" if there are multiple devices
	* 
	* @param [in, out] pDevSize, When entering the parameter, it indicates the size of szElementList, and when exiting, it indicates the actual length of the string filled in szElementList
	* 
	* @param [out] pDevNum, The number of online devices enumerated
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_EnumDev(int nEnumType, char *szEnumList, int *pDevSize, int *pDevNum);

	/**
	* @brief connects devices by device name
	* @par Explanation
	* Connect the devices in the device set obtained by enumerating the DSTP2x_EnumDev interface
	* 
	* @param [in] szDevName, This is the name of a device in the szVNet List returned by DSTP2x_EnumDev
	* 
	* @param [out] pDevHdl, The device handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_ConnEnumeratedDev(const char *szDevName, DEV_HDL *pDevHdl);

	/**
	* @brief connects devices through IP and port
	* @par Explanation
	* Connect to the device directly through IP and port, and obtain the device handle.
	* 
	* @param [in] szIpPort, Connect device directly by passing in the IP address and port number, such as "165.469.2.23:5100"
	* 
	* @param [out] pDevHdl, The device handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_ConnNetworkDev(const char *szIpPort, DEV_HDL *pDevHdl);

	/**
	* @brief Connect the device through serial port number and baud rate
	* @par Explanation
	* Connect the device directly through the serial port number and baud rate, and obtain the device handle.
	* 
	* @param [in] nSerialNo, The serial port number
	* 
	* @param [in] nBaudRate, The baud rate
	* 
	* @param [out] pDevHdl, The device handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_ConnSerialDev(int nSerialNo, int nBaudRate, DEV_HDL *pDevHdl);

	/**
	* @brief Disconnect the device
	* @par Explanation:
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_DisconnDev(DEV_HDL ullDevHdl);

	/**
	* @brief Set communication timeout for connection
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] nCommType, It Set communication timeout type
	* @n 1- Set USB timeout
	* @n 2- Set TCP timeout
	* @n 3- Set serial port timeout
	* 
	* @param [in] unSendTimeout, The Data transmission timeout, unit: milliseconds
	* 
	* @param [in] unRecvTimeout, The Data reception timeout, unit: milliseconds
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetCommTimeout(DEV_HDL ullDevHdl, int nCommType, unsigned int unSendTimeout, unsigned int unRecvTimeout);


	/**
	* @brief transfers data directly to the printer
	* @par Explanation
	* Support direct instruction transmission or hexadecimal data communication; It also supports one-way instruction data, where pOutData can transmit 0 to indicate that the program does not need to receive response data from the printer in the future
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] pInData, Data to be sent, can be a string type or regular hexadecimal data
	* 
	* @param [in] nInDataSize, It represents the length of the data corresponding to pInData
	* 
	* @param [out] pOutData, It is a buffer used to store the response data returned by the printer. Please determine the length of the response data based on the requested data. It is recommended to pre allocate the buffer to no less than 1024 bytes
	* 
	* @param [in, out] nOutDataSize, When it is input, it represents the buffer size of pOutData, and when it is output, it represents the actual length of data stored in pOutData
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_TransRecvData(DEV_HDL ullDevHdl, const char *pInData, int nInDataSize, char *pOutData, int *nOutDataSize);



	/**
	* @brief Set parameters related to network port connection retry
	* @par    Explanation:
	* When this interface is not called, the default retry count is 1 and the retry interval is 3000ms
	* 
	* @param [in]       szIp				  Device IP address, when an empty string is passed, it is used to print all printers connected to the network port
	* 
	* @param [in]       iTryConnNum           Number of network reconnections
	* 
	* @param [in]       iTryInterval          Network reconnection time interval, unit: ms
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetNetworkReconnectPar(const char *szIp, int iTryConnNum, int iTryInterval);

	/**
	* 
	*  @}
	*/



	/** @defgroup DeviceControl, Device functions
	*   @brief Print self checking pages, clear cache, etc
	* 
	*   @{
	* 
	*/


	/**
	* @brief Print self check page
	* @par Explanation:
	* Print out the basic information of the device, including manufacturer, model, machine number, printing simulation type, etc
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_PrintSelfCheckPage(DEV_HDL ullDevHdl);


	/**
	* @brief Device Clear Cache
	* @par Explanation:
	* Implementation effect: equivalent to the effect achieved by a hard restart of the printer, including clearing cache
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RestartPrt(DEV_HDL ullDevHdl);


	/**
	* @brief Instant Paper Cutting
	* @par Explanation
	* Usage conditions: The current printer has a built-in cutter module and the cutter function is turned on
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_CutPaper(DEV_HDL ullDevHdl);


	/**
	* @brief Move Paper
	* @par Explanation
	* Usage conditions: The current printer has a built-in RFID module and is turned on
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] nDir, The paper movement direction
	* @n 0- Forward
	* @n 1- Backward
	* 
	* @param [in] dbDistance, Paper movement distance, unit: mm
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_MovePaper(DEV_HDL ullDevHdl, int nDir, double dbDistance);


	/**
	* @brief ordinary label positioning
	* @par Explanation
	* Usage condition: The current printer paper mode is label paper
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LocateLabel(DEV_HDL ullDevHdl);


	/**
	* @brief Continuous paper black label positioning
	* @par Explanation
	* Usage condition: The current printer paper mode is label paper
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LocateBlackMark(DEV_HDL ullDevHdl);

	/**
	* 
	*  @}
	*/



	/** @defgroup PrinterInfoQuery, Device information query
	*    @brief Printer status, printer serial number, firmware version number, etc
	* 
	*   @{
	* 
	*/


	/**
	* @brief query printer status
	* @par Explanation
	* Due to the occurrence of multiple states, warnings, and errors at the same time in the printer, the actual number of messages stored in pMainStatus, pWarning, and pError when this function returns may be more than one
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [out] pIsReady, It determines whether the printer can continue to work normally, returns 1 yes, 0 no; If 0 is passed, it means that the parameter is not used
	*
	* @param [out] pMainStatus, It returns an array used to store the main state. It is recommended to pre allocate 8 array elements; If 0 is passed, it means that the parameter is not used
	* 
	* @param [in, out] pMainStatusNum, It represents the size of the pMainStatus array when entered, and represents the actual number of primary states stored in pMainStatus when exited; If 0 is passed, it means that the parameter is not used
	* 
	* @param [out] pWarning, When it returns, it is used to store an array of warnings. It is recommended to pre allocate 8 array elements; If 0 is passed, it means that the parameter is not used
	* 
	* @param [in, out] pWarningNum, When it is entered, it represents the size of the pWarning array, and when it is exited, it represents the actual number of warning messages stored in pWarning; If 0 is passed, it means that the parameter is not used
	*
	* @param [out] pError, It returns an array used to store error information. It is recommended to pre allocate 8 array elements; If 0 is passed, it means that the parameter is not used
	* 
	* @param [in, out] pErrorNum, It represents the size of the pError array, and when it is exited, it represents the actual number of error messages stored in pError; If 0 is passed, it means that the parameter is not used
	* 
	* @param [out] pDesc, This detailed description of status, warnings and errors, return string format such as:
	* MainStatus: xxx, xxx | Warning: None | Error: xxx, xxx | Paper type | Printing mode | Knife status | Stripper status | Sensor status; If 0 is passed, it means that the parameter is not used
	* 
	* @param [in, out] pDescLen, When it is input, it represents the buffer length of pDesc, and when it is output, it represents the actual length of pDesc content returned; If 0 is passed, it means that the parameter is not used
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_GetPrtStatus(DEV_HDL ullDevHdl, int *pIsReady, int *pMainStatus, int *pMainStatusNum, int *pWarning, int *pWarningNum, int *pError, int *pErrorNum, char* pDesc, int *pDescLen);

	/**
	* @brief query printer serial number
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [out] szPrtSN, It is a buffer used to store printer serial number strings, with ASCII character encoding and format such as 228022200001. It is recommended to pre allocate the buffer to no less than 32 bytes
	* 
	* @param [in, out] pPrtSNSize, It takes as input the buffer size of szPrtSN and takes as output the actual length of the string stored in szPrtSN (excluding '\ 0')
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_GetPrtSN(DEV_HDL ullDevHdl, char *szPrtSN, int *pPrtSNSize);

	/**
	* @brief query printer firmware version number
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [out] szPrtFWVer, It is a buffer used to store printer serial number strings, with ASCII character encoding and format such as 01.08.00.0a. It is recommended to pre allocate the buffer to no less than 32 bytes
	* 
	* @param [in, out] pPrtFWVerSize, It takes as input the buffer size, and takes as output the actual length of the string stored in szPrtFWVerer (excluding '\ 0')
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_GetPrtFWVer(DEV_HDL ullDevHdl, char *szPrtFWVer, int *pPrtFWVerSize);



	/**
	* @brief query printer motor rotation distance
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [out] pDistance, It returns the distance of the printer motor rotation, in millimeters
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_GetPrtMotorTravelDistance(DEV_HDL ullDevHdl, unsigned int *pDistance);


	/**
	* @brief query printer model name
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [out] szPrtName, It is a buffer used to store the printer model name string, with ASCII character encoding. It is recommended to pre allocate the buffer to no less than 64 bytes
	* 
	* @param [in, out] pPrtNameSize, It takes as input the buffer size of szPrtName and takes as output the actual length of the string stored in szPrtName (excluding '\0')
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_GetPrtName(DEV_HDL ullDevHdl, char *szPrtName, int *pPrtNameSize);


	/**
	* 
	*  @}
	*/



	/** @defgroup PrinterSettings, Setting
	*   @brief Print offset, print simulation, image resolution and other settings
	* 
	*   @{
	* 
	*/


	/**
	* @brief Set Print Offset
	* @par Explanation
	* Due to the presence of substrates with varying distances around certain labels, in order to accurately print the content to the designated position on the label, users choose whether to call this function based on the actual situation of the label
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] dbXOffset, It is the horizontal offset relative to the starting position of the print, measured in millimeters (mm)
	* 
	* @param [in] dbYOffset, It is the vertical offset relative to the starting position of the print, measured in millimeters (mm)
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetPrnOffset(DEV_HDL ullDevHdl, double dbXOffset, double dbYOffset);


	/**
	* @brief Set simulation type
	* @par Explanation
	* Set the simulation type used for printing data
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] nEimulation, The simulation type
	* @n 0- Automatic adaptation printer current simulation (reserved)
	* @n 1 - ZPL
	* @n 2 - TSPL
	* @n 3 - ESCPOS
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetPrnEmulation(DEV_HDL ullDevHdl, int nEmulation);


	/**
	* @brief Set the resolution of the image to be drawn
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] nDpi, The resolution of the image to be drawn
	*  @n 1 - 203dpi
	*  @n 2 - 300dpi
	*  @n 3 - 600dpi
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetImgDpi(DEV_HDL ullDevHdl, int nDpi);


	/**
	* @brief Set real-time status retrieval
	* @par Explanation
	* If this function is not called, DSTP2x_GetPrtStatus will be non real time
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] nRealtime,  real-time performance
	* @n 0- Non real time; The printer supports non real time status retrieval by default (U port, network port, serial port); At this point, the printer executes instructions issued by the host in series, and status requests are not prioritized and processed in real-time
	* @n 1- Real time; The printer currently only supports real-time status acquisition when connected through a USB port; At this point, the request to obtain status will be prioritized and processed in real-time
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetRTStatus(DEV_HDL ullDevHdl, int nRealtime);


	/**
	* @brief Enable cutter function
	* @par Explanation
	* If this function is not called, the cutting function will be turned off by default
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_TurnOnCutter(DEV_HDL ullDevHdl);


	/**
	* @brief Turn off the cutter function
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_TurnOffCutter(DEV_HDL ullDevHdl);


	/**
	* 
	*  @}
	*/



	/** @defgroup RFIDFuncs RFID functions
	*   @brief Cutting paper, direct data transmission, etc
	* 
	*   @{
	* 
	*/


	/**
	* @brief Set RFID read power
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] dbPower, The RFID read power, unit: dBm
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RFID_SetReadPower(DEV_HDL ullDevHdl, double dbPower);


	/**
	* @brief Set RFID write power
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] dbPower, The RFID write power, unit: dBm
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RFID_SetWritePower(DEV_HDL ullDevHdl, double dbPower);


	/**
	* @brief Get RFID read power
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [out] pdbPower, It is a pointer to the double variable used to obtain RFID read power, unit: dBm
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RFID_GetReadPower(DEV_HDL ullDevHdl, double *pdbPower);


	/**
	* @brief Get RFID write power
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [out] pdbPower, It is a pointer to the double variable used to obtain RFID write power, unit: dBm
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RFID_GetWritePower(DEV_HDL ullDevHdl, double *pdbPower);


	/**
	* @brief Set RFID Protocol
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] nProto sets protocol values
	* @n 0: ISO14443A protocol, (high-frequency module)
	* @n 1: ISO15693 protocol, (high-frequency module)
	* @n 5: ISO18000-6C protocol, (ultra-high frequency module)
	* @n 9: ISO18000-63 protocol, (military standard module)
	* @n 10: GB/T 29768 protocol, (military standard module)
	* @n 11: GJB 7377.1 protocol, (military standard module)
	*
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RFID_SetProto(DEV_HDL ullDevHdl, int nProto);


	/**
	* @brief Get RFID Protocol
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [out] pProto returns the protocol value
	* @n 0: ISO14443A protocol, (high-frequency module)
	* @n 1: ISO15693 protocol, (high-frequency module)
	* @n 5: ISO18000-6C protocol, (ultra-high frequency module)
	* @n 9: ISO18000-63 protocol, (military standard module)
	* @n 10: GB/T 29768 protocol, (military standard module)
	* @n 11: GJB 7377.1 protocol, (military standard module)
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RFID_GetProto(DEV_HDL ullDevHdl, int *pProto);


	/**
	* @brief RFID label positioning
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RFID_LocateLabel(DEV_HDL ullDevHdl);


	/**
	* @brief reads TID EPC¡¢USER
	* @par Explanation
	* This interface function is suitable for directly reading TID, EPC, and USER without printing
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [out] pTid, It is a buffer used to receive TID data read back from RFID labels and return the hexadecimal string of the data; If TID data does not need to be read, this parameter can be passed as 0
	* 
	* @param [in, out] pTidSize, When it is input, it represents the buffer size of pTid, and when it is output, it represents the hexadecimal string length of the actual pTid data; If TID data does not need to be read, this parameter can be passed as 0
	* 
	* @param [in, out] pEpc, It is a buffer used to receive EPC data read back from RFID labels and return the hexadecimal string of the data; If there is no need to read EPC data, this parameter can be passed as 0
	*
	* @param [in, out] pEpcSize, When it is entered, it represents the buffer size of pEpc, and when it is exited, it represents the hexadecimal string length of the actual pEpc data; If there is no need to read EPC data, this parameter can be passed as 0
	* 
	* @param [out] pUser, It is a buffer used to receive USER data read back from RFID labels, returning the hexadecimal string of the data; If there is no need to read USER data, pass 0 for this parameter
	* 
	* @param [in, out] pUserSize, When it is entered, it represents twice the actual length of the USER data in the label (for example, if the pUser buffer size passed as a parameter is 8, only 4 bytes of user data are actually read), and when it is exited, it represents the hexadecimal string length of the actual pUser data; If there is no need to read USER data, pass 0 for this parameter
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RFID_ReadData(DEV_HDL ullDevHdl, char *pTid, int *pTidSize, char *pEpc, int *pEpcSize, char *pUser, int *pUserSize);



	/**
	* @brief Change the access password for RFID labels
	* @par Explanation
	* Called before printing, valid for a single label;
	* Changing the password takes effect when printing;
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] szOldPw, The initial password for the RFID label is an 8-bit hexadecimal string
	* 
	* @param [in] szNewPw, It sets a new password for the RFID label, which is an 8-bit hexadecimal string. Please note that it cannot contain all zeros
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RFID_ChangeAccessPassword(DEV_HDL ullDevHdl, const char* szOldPw, const char* szNewPw);



	/**
	* @brief Set the destruction password for RFID labels
	* @par Explanation
	* Called before printing, valid for a single label;
	* The password set will take effect when printing;
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] szPw, RFID label destruction password, which is an 8-bit hexadecimal string, please note that it cannot be all 0s
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RFID_SetDestructionPassword(DEV_HDL ullDevHdl, const char* szPw);


	/**
	* @brief RFID lock type setting
	* @par Explanation
	* Support repeated calls before printing, for example: the EPC and USER areas were originally permanently locked, and then the USER area was set as a temporary lock. At this time, the permanent lock of the EPC area remains valid;
	* When called repeatedly, nTemporal is based on the last call;
	* When this interface is not called, it defaults to a temporary lock;
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] nRFIDArea, RFID area (or relationship), 1: EPC area, 2: USER area, 8: access password area, 16: destroy password area
	* 
	* @param [in] nLockType, 0: permanent lock, 1: temporary lock
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullDevHdl fails, unless modified again
	* @n 1- Temporary, this setting item is restored after a subsequent print interface (PrintXXX) call
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RFID_LockTypeSetting(DEV_HDL ullDevHdl, int nRFIDArea, int nLockType, int nTemporary);



	/**
	* @brief Lock specific RFID area
	* @par Explanation
	* Support locking of EPC area, USER area, access password area, and password destruction area;
	* Called before printing, valid for a single label;
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] nRFIDArea, RFID area (or relationship), 1: EPC area, 2: USER area, 8: access password area, 16: destroy password area
	* 
	* @param [in] szPw, RFID label password, which is an 8-bit hexadecimal string
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RFID_LockOperate(DEV_HDL ullDevHdl, int nRFIDArea, const char* szPw);



	/**
	* Unlock a specific RFID area with @brief
	* @par Explanation
	* Support unlocking EPC area, USER area, access password area, and destroy password area;
	* Called before printing, valid for a single label;
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] nRFIDArea, The RFID area (or relationship), 1: EPC area, 2: USER area, 8: access password area, 16: destroy password area
	* 
	* @param [in] szPw, RFID label password, which is an 8-bit hexadecimal string
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RFID_UnlockOperate(DEV_HDL ullDevHdl, int nRFIDArea, const char* szPw);



	/**
	* @brief Write a specific RFID area with password
	* @par Explanation
	* Called before printing, valid for a single label;
	* If this interface is not called, writing without a password will be unsuccessful if the password has already been changed;
	* If the template already has a password field, it will be replaced;
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] nRFIDArea, RFID area (or relationship), 1: EPC area, 2: USER area
	* 
	* @param [in] szPw, RFID label password, which is an 8-bit hexadecimal string. Please note that the password for the same label is the same
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_RFID_SetPasswordWithWrite(DEV_HDL ullDevHdl, int nRFIDArea, const char* szPw);



	/**
	* 
	*  @}
	*/




	/** @defgroup PdfPrinting, PDF printing function
	*   @brief PDF printing
	* 
	*   @{
	* 
	*/


	/**
	* @brief loading PDF data
	* @par Explanation
	* 
	* @param [in] nPdfDataType PDF data type
	* @n 1- PDF data is the file name (including path)
	* @n 2- PDF data is a base64 format string
	* 
	* @param [in] szPdfData, The pdf data, character encoding: utf-8
	* 
	* @param [in] nPdfDataSize, It represents the length of the string szPdfData (excluding "\0") in bytes
	* 
	* @param [out] pPdfHdl, The pdf file handle address
	* 
	* @param [out] pPageCount, The total number of pages in the current PDF file
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LoadPdf(int nPdfDataType, const char *szPdfData, int nPdfDataSize, PDF_HDL *pPdfHdl, int *pPageCount);


	/**
	* @brief Print PDF
	* @par Explanation
	* The szOutFile parameter needs to call DSTP2x_SetPdfPrnMode and nPrnMode is 1 or 2 to generate. png or. prn local files;
	* In order to use RFID functionality, DSTP2x_SetPdfPrnMode needs to be set to 0;
	* For RFID that requires both write and read functionality, it is necessary to first call DSTP2x_SetPdfRFIDData, set the read type in nRfidReadType, and allocate szOutRFID memory;
	* For read-only functions that require RFID, there is no need to call the DSTP2x_SetPdfRFIDData interface, but it is necessary to allocate memory for szOutRFID;
	* RFID reading function is not required, nRfidReadType and szOutRFID need to be set to 0.
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] ullPdfHdl, This is the handle to the PDF file returned by the DSTP2x_LoadPdf function
	* 
	* @param [in] nPageNo, Page number of the PDF file to be printed
	* 
	* @param [out] szOutFile, It is used to store the local data file name (.prn or .png) (including the path) generated during this printing operation. It is recommended to pre allocate space of no less than 1024 bytes; If you do not need to obtain the local data file name generated by this printing operation, simply pass in 0 for this parameter
	* 
	* @param [in, out] pOutFileSize, When it is entered, it represents the buffer size of szOutFile, and when it is exited, it represents the actual length of the string stored in szOutFile; If szOutFile is 0, this parameter will be ignored
	*	When the error code is 41943046, it indicates that the pOutFileSize cache is insufficient, and a new cache request should be made based on the size of this parameter.
	* 
	* @param [in] nRfidReadType, Whether to read and how to read RFID data during the process of printing the current page data
	* @n 0- Do not read
	* @n 1- Read TID
	* @n 2- Read EPC
	* @n 4- Read User
	* 
	* @param [out] szOutRFID, This is a buffer used to store RFID data read during the printing process. Please determine the pre allocated buffer space size based on the nRfidReadType (combination) type;
	* The read RFID data is returned after dynamic RFID execution, represented as a hexadecimal string;
	* The content format is as follows: "TID:82309360|EPC:0123456789|USER:abcdef"
	* If it is not necessary to obtain the RFID data read during the printing process, this parameter can be set to 0
	* 
	* @param [in, out] pOutRFIDSize When parameterized, represents the buffer size of szOutRFID, and when parameterized, represents the actual length of data stored in szOutRFID; If szOutRFID is 0, this parameter will be ignored
	*	When the error code is 41943046, it indicates that the pOutRFIDSize cache is insufficient, and a new cache request should be made based on the size of this parameter.
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_PrintPdf(DEV_HDL ullDevHdl, PDF_HDL ullPdfHdl, int nPageNo, char *szOutFile, int *pOutFileSize, int nRfidReadType, char *szOutRFID, int *pOutRFIDSize);


	/**
	* @brief Delete PDF handle
	* @par Explanation
	* 
	* @param [in] ullPdfHdl, This is the handle to the PDF file returned by the DSTP2x_LoadPdf function
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_DeletePdf(PDF_HDL ullPdfHdl);


	/**
	* @brief Set PDF printing mode
	* @par Explanation
	* Valid for the current handle. If this function is not called, the print mode defaults to 0
	* 
	* @param [in] ullPdfHdl, This is the handle to the PDF file returned by the DSTP2x_LoadPdf function
	* 
	* @param [in] nPrnMode, printing mode; If this function is not called, the default printing mode is to print through a printer
	* @n 0- Print through printer
	* @n 1- Print to prn file
	* @n 2- Generate PNG format preview image file
	* @n 3- Generate Base64 data for preview images
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetPdfPrnMode(PDF_HDL ullPdfHdl, int nPrnMode);


	/**
	* @brief Set whether DSTP2x-PrintPdf prints synchronization results in a single call
	* @par Explanation
	* Valid for the current handle. If this function is not called, the PDF single print will synchronize the results
	* 
	* @param [in] ullPdfHdl, This is the handle to the PDF file returned by the DSTP2x_LoadPdf function
	* 
	* @param [in] nSyncType, Whether to print synchronization results
	* @n 0- Non synchronous printing results, as long as the printing data of the current page is sent, this function returns; At this time, RFID read operations for DSTP2x-PrintPdf are not supported
	* @n 1- Synchronize printing results. After the printing data of the current page is sent, this function continuously monitors the printing status internally until the printing is successfully completed before returning; If the printer encounters an error, the function returns immediately
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetPdfPrnSyncType(PDF_HDL ullPdfHdl, int nSyncType);


	/**
	* @brief Set the maximum timeout time for a single call of DSTP2x-PrintPdf
	* @par Explanation
	* Valid for the current handle. If this function is not called, the default maximum timeout for a single PDF print is 15000 milliseconds
	* 
	* @param [in] ullPdfHdl, This is the handle to the PDF file returned by the DSTP2x_LoadPdf function
	* 
	* @param [in] nTimeout, unit: milliseconds; It only takes effect when DSTP2x-PrintPdf is called as a synchronous result in a single call
	* @n -1 - means that if there are no (software/hardware or communication) errors during the printing process, DSTP2x-PrintPdf will wait indefinitely for the printing end condition to be met before returning
	* @n >0 - means that if there are no (software/hardware or communication) errors during the printing process, DSTP2x-PrintPdf will check whether the overall time consumption is greater than or equal to nTimeout while waiting for the printing end condition to be met;
	* If so, return 'Operation execution timeout'
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetPdfPrnTimeout(PDF_HDL ullPdfHdl, int nTimeout);


	/**
	* @brief Set the RFID data to be written during the PDF printing process
	* @par Explanation
	* If this function is not called, RFID reading/writing will not be performed during the printing process
	* 
	* @param [in] ullPdfHdl, This is the handle to the PDF file returned by the DSTP2x_LoadPdf function
	* 
	* @param [in] nPageNo, Page number of the PDF file to be printed
	* 
	* @param [in] nRfidRgnType, It is the type of area where RFID data needs to be written during the printing process
	* @n 1- EPC area
	* @n 2- USER area
	* 
	*  @param [in] nRfidDataFmt, The format of RFID data that needs to be written during the printing process.
	* @n 1- ASCII encoded string
	* @n 2- Hexadecimal string
	* @n 3- Hexadecimal byte data
	* 
	* @param [in] pData, The RFID data that needs to be written into pData during the printing process
	* 
	* @param [in] nDataSize, The length of RFID data to be written during the printing process, in bytes; If nRFidDataMmt is 1 or 2, this parameter represents the actual string length (excluding "\ 0") of pData
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetPdfRFIDData(PDF_HDL ullPdfHdl, int nPageNo, int nRfidRgnType, int nRfidDataFmt, const char *pData, int nDataSize);


	/**
	* @brief Set PDF target print size
	* @par Explanation
	* Valid for the current handle
	* 
	* @param [in] ullPdfHdl, This is the handle to the PDF file returned by the DSTP2x_LoadPdf function
	* 
	* @param [in] dbWidth, Print width, unit: mm
	* 
	* @param [in] dbHeight, Print height, unit: mm
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetPdfPrnSize(PDF_HDL ullPdfHdl, double dbWidth, double dbHeight);


	/**
	* @brief Set PDF target printing rotation angle
	* @par Explanation
	* Valid for the current handle
	* 
	* @param [in] ullPdfHdl, This is the handle to the PDF file returned by the DSTP2x_LoadPdf function
	* 
	* @param [in] nAngle, The rotation angle, range [0, 90, 180, 270]
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetPdfPrnRotate(PDF_HDL ullPdfHdl, int nAngle);



	/**
	* @brief Set the Halftone Processing Algorithm for PDF Images
	* @par Explanation:
	* Valid for the current handle
	* 
	* @param [in] ullPdfHdl, This is the label context handle returned by the DSTP2x_LoadPdf function
	* 
	* @param [in] nAlgorithm, The image algorithm
	* @n 1- Error diffusion
	* @n 2- Ordered jitter algorithm
	* @n 3- Threshold operation algorithm (default)
	* 
	* @param [in] nThrehold, effective when nAlgorithm is 3, range [0,255]
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetPdfHalftoneAlgo(PDF_HDL ullPdfHdl, int nAlgorithm, int nThreshold);


	/**
	* 
	*  @}
	*/



	/** @defgroup LabelTemplatePrinting, Label template printing function
	*   @brief  Label template printing
	* 
	*   @{
	* 
	*/


	/**
	* @brief loads predefined label templates
	* @par Explanation
	* The szFileName parameter must be generated by DSTP2xDemo.exe in the SDK package.
	* 
	* @param [in] szFile, The predefined label template (including path) file name (character encoding: utf-8), or template data
	* 
	* @param [out] pLTHdl, The label template file handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LoadLabelTmpl(const char *szFile, LABEL_TEMP_HDL *pLTHdl);


	/**
	* @brief Print Label Template
	* @par Explanation
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] ullLTHdl, This is the label template file handle returned by the DSTP2x_LoadLabelTmpl function
	* 
	* @param [out] szOutFile, It is used to store the local data file name (. prn or. png) (including the path) generated during this printing operation. It is recommended to pre allocate space of no less than 256 bytes; If you do not need to obtain the local data file name generated by this printing operation, simply pass in 0 for this parameter
	* 
	* @param [in, out] pOutFileSize, When it is entered, it represents the buffer size of szOutFile, and when it is exited, it represents the actual length of the string stored in szOutFile; If szOutFile is 0, this parameter will be ignored
	*	When the error code is 41943046, it indicates that the pOutFileSize cache is insufficient, and a new cache request should be made based on the size of this parameter.
	* 
	* @param [out] szOutRFID, It is a buffer used to store RFID data read during the printing process. Please determine the pre allocated buffer space size based on the nRfidReadType (combination) type;
	* The content format is as follows: "TID: 82309360 | EPC: 0123456789 | User: abcdef", and RFID content data is represented as a hexadecimal string;
	* If it is not necessary to obtain the RFID data read during the printing process, this parameter can be set to 0
	* 
	* @param [in, out] pOutRFIDSize, When parameterized, represents the buffer size of szOutRFID, and when parameterized, represents the actual length of data stored in szOutRFID; If szOutRFID is 0, this parameter will be ignored
	*	When the error code is 41943046, it indicates that the pOutRFIDSize cache is insufficient, and a new cache request should be made based on the size of this parameter.
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_PrintTmpl(DEV_HDL ullDevHdl, LABEL_TEMP_HDL ullLTHdl, char *szOutFile, int *pOutFileSize, char *szOutRFID, int *pOutRFIDSize);


	/**
	* @brief Delete label template file handle
	* @par Explanation
	* 
	* @param [in] ullLTHdl, This is the label template file handle returned by the DSTP2x_LoadLabelTmpl function
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_DeleteTmpl(LABEL_TEMP_HDL ullLTHdl);


	/**
	* @brief Set the printing mode for label templates
	* @par Explanation
	* If this function is not called, the print mode defaults to 0
	* 
	* @param [in] ullLTHdl, This is the label template file handle returned by the DSTP2x_LoadLabelTmpl function
	* 
	* @param [in] nPrnMode, The printing mode; If this function is not called, the default printing mode is to print through a printer
	* @n 0- Print through printer
	* @n 1- Print to. prn file
	* @n 2- Generate PNG format preview image file
	* @n 3- Generate Base64 data for preview images
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetTmplPrnMode(LABEL_TEMP_HDL ullLTHdl, int nPrnMode);



	/**
	* @brief Set whether DSTP2x_PrintTmpl prints synchronization results in a single call
	* @par Explanation
	* If this function is not called, the template will synchronize the results for a single print
	* 
	* @param [in] ullLTHdl, This is the label template file handle returned by the DSTP2x_LoadLabelTmpl function
	* 
	* @param [in] nSyncType, Whether to print synchronization results
	* @n 0- Non synchronous printing results, as long as the printing data of the current page is sent, this function returns; At this time, RFID read operations for DSTP2x_PrintTmpl are not supported
	* @n 1- Synchronize printing results. After the printing data of the current page is sent, this function continuously monitors the printing status internally until the printing is successfully completed before returning; If the printer encounters an error, the function returns immediately
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetTmplPrnSyncType(LABEL_TEMP_HDL ullLTHdl, int nSyncType);


	/**
	* @brief Set the maximum timeout time for a single call of DSTP2x_PrintTmpl
	* @par Explanation
	* If this function is not called, the default maximum timeout time for a single print of the template is 15000 milliseconds
	* 
	* @param [in] ullLTHdl, This is the label template file handle returned by the DSTP2x_LoadLabelTmpl function
	* 
	* @param [in] nTimeout, timeout, unit: milliseconds; It only takes effect when DSTP2x_PrintTmpl is called as a synchronous result in a single call
	* @n -1 - means that if there are no (software/hardware or communication) errors during the printing process, DSTP2x_PrintTmpl will wait indefinitely for the printing end condition to be met before returning
	* @n >0 - means that if there are no (software/hardware or communication) errors during the printing process, DSTP2x_PrintTmpl will check whether the overall time consumption is greater than or equal to nTimeout while waiting for the printing end condition to be met;
	* If so, return 'Operation execution timeout'
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetTmplPrnTimeout(LABEL_TEMP_HDL ullLTHdl, int nTimeout);


	/**
	* @brief Set the actual RFID write substitute data for the element with the specified ID in the label template
	* @par Explanation
	* If this function is not called to set real replacement data for certain elements of the label template that have already been created with IDs, the original IDs created in the template will be written to RFID using preset values during the subsequent printing process
	* 
	* @param [in] ullLTHdl, This is the label template file handle returned by the DSTP2x_LoadLabelTmpl function
	* 
	* @param [in] szElemID, represents the ID of a specific element in the label template that requires actual data for RFID writing
	* 
	* @param [in] pActualData, is the RFID data that needs to be written during the printing process
	* 
	* @param [in] nActualDataSize, The length of RFID data to be written during the printing process, in bytes;
	* If pActualData is a string, then this parameter represents the actual string length (excluding "\0") of pActualData
	* If pActualData is hexadecimal byte data, then this parameter represents the actual length of data that pActualData should be written to
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetTmplRFIDData(LABEL_TEMP_HDL ullLTHdl, const char *szElemID, const char *pActualData, int nActualDataSize);


	/**
	* @brief: Set the actual print substitute data for the element with the specified ID in the label template
	* @par Explanation
	* If this function is not called to set real replacement data for certain elements with created IDs in the label template, the original ID created in the template will be printed using the preset values during the subsequent printing process
	* 
	* @param [in] ullLTHdl, This is the label template file handle returned by the DSTP2x_LoadLabelTmpl function
	* 
	* @param [in] szElemID, The represents the ID of a specific element in the label template that needs to be printed using actual data
	* 
	* @param [in] szActualData, The actual data that needs to be printed (utf-8)
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetTmplPrnData(LABEL_TEMP_HDL ullLTHdl, const char *szElemID, const char *szActualData);



	/**
	* @brief is the element with the specified ID in the label template, which sets the substitute attribute value based on the existing key value
	* @par Explanation
	* If this function is not called to set real replacement data for certain elements with created IDs in the label template, the original ID created in the template will be printed using the preset values during the subsequent printing process
	* 
	* @param [in] ullLTHdl, This is the label template file handle returned by the DSTP2x_LoadLabelTmpl function
	* 
	* @param [in] szElemID, represents the ID of a specific element in the label template that needs to be printed using actual data
	* 
	* @param [in] szKey, The index key to which the szKey data value belongs
	* 
	* @param [in] szValue, The actual data value that needs to be printed (utf-8)
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetTmplValByKey(LABEL_TEMP_HDL ullLTHdl, const char *szElemID, const char *szKey, const char *szValue);


	/**
	* @brief returns the template file (. dlt) of the current label template
	* @par Explanation
	* If you have previously modified some content or attribute data of the label template through the DSTP2x_SetTmplxxx interface and want to obtain the modified dlt template file, then call this interface.
	* 
	* @param [in] ullLTHdl, This is the label template file handle returned by the DSTP2x_LoadLabelTmpl function
	* 
	* @param [out] pFileName If successful, return the template file path
	* 
	* @param [in, out] pFileNameLen takes in the buffer size of pFileName and takes out the actual length of data stored in pFileName
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_GetBackTmpl(LABEL_TEMP_HDL ullLTHdl, char * pFileName, int *pFileNameLen);



	/**
	* @brief  Get all ID values of the current label template
	* @par Explanation
	*
	* @param [in] ullLTHdl, this is the label template file handle returned by the \"DSTP2x_LoadLabelTmpl\" function
	*
	* @param [in] cInterval, it setting returns the interval character between all ID values
	*
	* @param [in] nType, retrieves ID values based on type, 0: all ID values, 1: dynamically modifiable ID values, 2: non dynamically modifiable ID values
	*
	* @param [out] pIDValues, If pIDValues is successful, return all ID values with \"cInterval\" intervals between them
	*
	* @param [in, out] pIDValuesLen, represents the buffer size of \"pIDValues\" when parameterized, and represents the actual length of data stored in pIDValues when parameterized
	*
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_GetTmplAllIDValues(LABEL_TEMP_HDL ullLTHdl, char cInterval, int nType, char *pIDValues, int *pIDValuesLen);

	/**
	* 
	*  @}
	*/



	/** @defgroup LabelDrawPrinting Label drawing and printing function
	*   @brief Label drawing and printing
	* 
	*   @{
	* 
	*/


	/**
	* @brief Create label context
	* @par Explanation
	* 
	* @param [in] dbWidth, Target label width to be printed, unit: mm
	* 
	* @param [in] dbHeight, Target label height to be printed, unit: mm
	* 
	* @param [out] pLCHdl, The label context handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_CreateLabelContext(double dbWidth, double dbHeight, LC_HDL *pLCHdl);


	/**
	* @brief draws text in the specified label context
	* @par Explanation:
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] dbX, The horizontal axis of the text content block relative to the top left corner of the label, in millimeters (mm)
	* 
	* @param [in] dbY, The vertical axis of the text content block relative to the upper left corner of the label, in millimeters (mm)
	* 
	* @param [in] dbW, The width of the text content block, which is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
	* 
	* @param [in] dbH, The height of the text content block, which is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
	* 
	* @param [in] szText, The text content that needs to be drawn in the drawing context, character encoding: utf-8¡£
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Lbl_DrawText(LC_HDL ullLcHdl, double dbX, double dbY, double dbW, double dbH, const char *szText);


	/**
	* @brief draws an image in the specified label context
	* @par Explanation:
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] dbX, The horizontal axis of the image content block relative to the top left corner of the label, in millimeters (mm)
	* 
	* @param [in] dbY, The vertical axis of the image content block relative to the upper left corner of the label, in millimeters (mm)
	* 
	* @param [in] dbW, The width of the image content block, which is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
	* 
	* @param [in] dbH, The height of the image content block, which is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
	* 
	* @param [in] dbScale, The scaling factor of relative to the original image size, which is a non negative floating-point number. If it is 0, it means this parameter is ignored, and the value range must be between 1 and 3
	* 
	* @param [in] nImgDataType, The image data type
	* @n 0- Local image file
	* @n 1- Image Memory Data
	* @n 2- base64 format image data
	* 
	* @param [in] szImage, It needs to draw image data in the drawing context.
	* 
	* @param [in] unImgDataSize, When unImgDataSize is 1 or 2, the size of unImgDataSize is the actual memory size pointing to szImage. When nImgDataType is 0, the size of unImgDataSize is the length pointing to szImage.
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Lbl_DrawImage(LC_HDL ullLcHdl, double dbX, double dbY, double dbW, double dbH, double dbScale, int nImgDataType, const char *szImage, unsigned int unImgDataSize);


	/**
	* @brief Draw barcode in the specified label context
	* @par Explanation:
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] dbX, The horizontal axis of the image content block relative to the top left corner of the label, in millimeters (mm)
	* 
	* @param [in] dbY, The vertical axis of the image content block relative to the upper left corner of the label, in millimeters (mm)
	* 
	* @param [in] dbW, The width of the image content block, which is a non negative floating-point number, measured in millimeters (mm)
	* 
	* @param [in] dbH, The height of the image content block, which is a non negative floating-point number, measured in millimeters (mm)
	* 
	* @param [in] nCodeType, This is the encoding type used to generate barcodes
	*  @n 8 - CODE39
	*  @n 20 - CODE128
	*  @n 25 - CODE93
	*  @n 34 - UPCA
	*  @n 37 - UPCE
	*  @n 55 - PDF417
	*  @n 58 - QRCode
	*  @n 71 - DataMatrix
	*  @n 72 - EAN14
	*  @n 84 - MicroPDF417
	*  @n 116 - HanXin
	*  @n 142 - GridMatrix
	* 
	* @param [in] szData, It needs to draw barcode data in the drawing context.
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Lbl_DrawBarCode(LC_HDL ullLcHdl, double dbX, double dbY, double dbW, double dbH, int nCodeType, const char *szData);


	/**
	* @brief Draw line segments in the specified label context
	* @par Explanation:
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] dbStartX, The horizontal coordinate of the starting point of the line segment relative to the upper left corner of the label as the origin, in millimeters (mm)
	* 
	* @param [in] dbStartY, The vertical coordinate of the starting point of the line segment relative to the top left corner of the label as the origin, in millimeters (mm)
	* 
	* @param [in] dbEndX, The line segment's endpoint horizontal coordinate relative to the top left corner of the label as the origin, unit: mm (millimeters)
	* 
	* @param [in] dbEndY, The vertical coordinate of the endpoint of the line segment relative to the upper left corner of the label as the origin, in millimeters (mm)
	* 
	* @param [in] nLineWidth, The line segment width, unit: pixel
	* 
	* @param [in] nLineType, The line segment type, 0: solid line, 1: dashed line, 2: dotted line, 3: dotted solid line, 4: double dotted solid line
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Lbl_DrawLine(LC_HDL ullLcHdl, double dbStartX, double dbStartY, double dbEndX, double dbEndY, int nLineWidth, int nLineType);




	/**
	* @brief  Draw an ellipse in the specified label context
	* @par    Explanation
	*
	* @param [in]            ullLcHdl				, this is the table handle returned by the DSTP2x_CreateLabelContext function
	*
	* @param [in]            dbX					, The horizontal axis of the top left corner of the ellipse, unit: mm (millimeter)
	*
	* @param [in]            dbY					, The vertical axis of the top left corner of the ellipse, unit: mm (millimeter)
	*
	* @param [in]            dbW					, Width of ellipse, unit: mm (millimeter)
	*
	* @param [in]            dbH					, Height of ellipse, unit: mm (millimeter)
	*
	* @param [in]            nLineWidth				, Line width of ellipse, unit: pixel
	*
	* @param [in]            nLineType				, Types of elliptical lines, 0: solid line, 1: dashed line
	*
	* @param [in]            nIsFill				, Whether to fill, 1: Yes, 0: No
	*
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Lbl_DrawEllipse(LC_HDL ullLcHdl, double dbX, double dbY, double dbW, double dbH, int nLineWidth, int nLineType, int nIsFill);



	/**
	* @brief  Draw a rectangle in the specified label context
	* @par    Explanation
	*
	* @param [in]            ullLcHdl              , this is the table handle returned by the DSTP2x_CreateLabelContext function
	*
	* @param [in]            dbX					, The horizontal axis of the top left corner of the rectangle, unit: mm (millimeter)
	*
	* @param [in]            dbY					, The vertical axis of the top left corner of the rectangle, unit: mm (millimeter)
	*
	* @param [in]            dbW                    , Width of rectangle, unit: mm (millimeter)
	*
	* @param [in]            dbH                    , Height of rectangle, unit: mm (millimeter)
	*
	* @param [in]            nLineWidth             , Line width of rectangle, unit: pixel
	*
	* @param [in]            nLineType              , Rectangular line type, 0: solid line, 1: dashed line
	*
	* @param [in]            nIsFill                , Whether to fill, 1: Yes, 0: No
	*
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Lbl_DrawRectangle(LC_HDL ullLcHdl, double dbX, double dbY, double dbW, double dbH, int nLineWidth, int nLineType, int nIsFill);




	/**
	* @brief Print Label Template
	* @par Explanation
	* The szOutFile parameter needs to call DSTP2x_SetLcPrnMode and nPrnMode is 1 or 2 to generate. png or. prn local files;
	* In order to use RFID functionality, DSTP2x_SetLcPrnMode needs to be set to 0;
	* For RFID that requires both write and read functions, it is necessary to first call DSTP2x_LcRfid_SetData, set the read type in nRfidReadType, and allocate szOutRFID memory;
	* For read-only functions that require RFID, there is no need to call the DSTP2x_LcRfid_SetData interface, but it is necessary to allocate memory for szOutRFID;
	* RFID reading function is not required, nRfidReadType and szOutRFID need to be set to 0.
	* 
	* @param [in] ullDevHdl, The device handle address
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [out] szOutFile, This is used to store the local data file name (. prn or. png) (including the path) generated during this printing operation. It is recommended to pre allocate space of no less than 256 bytes; If you do not need to obtain the local data file name generated by this printing operation, simply pass in 0 for this parameter
	* 
	* @param [in, out] pOutFileSize, If is entered, it represents the buffer size of szOutFile, and when it is exited, it represents the actual length of the string stored in szOutFile; If szOutFile is 0, this parameter will be ignored
	*	When the error code is 41943046, it indicates that the pOutFileSize cache is insufficient, and a new cache request should be made based on the size of this parameter.
	* 
	* @param [in] nRfidReadType, Whether to read and how to read RFID data during the process of printing the current page data
	* @n 0- Do not read
	* @n 1- Read TID
	* @n 2- Read EPC
	* @n 4- Read User
	* 
	* @param [out] szOutRFID, This is a buffer used to store RFID data read during the printing process. Please determine the pre allocated buffer space size based on the nRfidReadType (combination) type;
	* The read RFID data is returned after dynamic RFID execution, represented as a hexadecimal string;
	* The content format is as follows: "TID:82309360|EPC:0123456789|USER:abcdef"
	* If it is not necessary to obtain the RFID data read during the printing process, this parameter can be set to 0
	* 
	* @param [in, out] pOutRFIDSize, When parameterized, represents the buffer size of szOutRFID, and when parameterized, represents the actual length of data stored in szOutRFID; If szOutRFID is 0, this parameter will be ignored
	*	When the error code is 41943046, it indicates that the pOutRFIDSize cache is insufficient, and a new cache request should be made based on the size of this parameter.
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_PrintLc(DEV_HDL ullDevHdl, LC_HDL ullLcHdl, char *szOutFile, int *pOutFileSize, int nRfidReadType, char *szOutRFID, int *pOutRFIDSize);


	/**
	* @brief Delete label context handle
	* @par Explanation
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_DeleteLabelContext(LC_HDL ullLcHdl);


	/**
	* @brief Set the printing mode for label context
	* @par Explanation
	* If this function is not called, the print mode defaults to 0
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nPrnMode, The printing mode; If this function is not called, the default printing mode is to print through a printer
	* @n 0- Print through printer
	* @n 1- Print to. prn file
	* @n 2- Generate PNG format preview image file
	* @n 3- Generate Base64 data for preview images
	*
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetLcPrnMode(LC_HDL ullLcHdl, int nPrnMode);

	/**
	* @brief Set the rotation angle of the entire canvas for label context
	* @par Explanation
	* If this function is not called, the angle defaults to 0
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nAngle, The rotation angle, range [0, 90, 180, 270]
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetLcPrnRotate(LC_HDL ullLcHdl, int nAngle);

	/**
	* @brief Set DSTP2x_PrintLc to print synchronization results in a single call
	* @par Explanation
	* If this function is not called, the template will synchronize the results for a single print
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nSyncType, whether to print synchronization results
	* @n 0- Non synchronous printing results, as long as the printing data of the current page is sent, this function returns; At this time, RFID read operations for DSTP2x_PrintLc are not supported
	* @n 1- Synchronize printing results. After the printing data of the current page is sent, this function continuously monitors the printing status internally until the printing is successfully completed before returning; If the printer encounters an error, the function returns immediately
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetLcPrnSyncType(LC_HDL ullLcHdl, int nSyncType);


	/**
	* @brief Set the maximum timeout time for a single call of DSTP2x_PrintLc
	* @par Explanation
	* If this function is not called, the default maximum timeout time for a single print of the template is 15000 milliseconds
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTimeout, Timeout, unit: milliseconds; It only takes effect when DSTP2x_PrintLc is called as a synchronous result in a single call
	* @n -1 - means that if there are no (software/hardware or communication) errors during the printing process, DSTP2x_PrintTmpl will wait indefinitely for the printing end condition to be met before returning
	* @n >0 - means that if there are no (software/hardware or communication) errors during the printing process, DSTP2x_PrintTmpl will check whether the overall time consumption is greater than or equal to nTimeout while waiting for the printing end condition to be met;
	* If so, return 'Operation execution timeout'
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_SetLcPrnTimeout(LC_HDL ullLcHdl, int nTimeout);


	/**
	* @brief label context drawing settings - Set the font name for the text content to be drawn
	* @par Explanation:
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting is restored after a DSTP2x_Lbl_DrawText or DSTP2x_Tbl_DrawText call
	* 
	* @param [in] szFontName, The font name, character encoding: utf-8
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetTextFontName(LC_HDL ullLcHdl, int nTemporary, const char *szFontName);


	/**
	* @brief label context drawing settings - Set the font size of the text content to be drawn
	* @par Explanation:
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting is restored after a DSTP2x_SrawText call
	* 
	* @param [in] dbFontSize, The font size, unit: pound
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetTextFontSize(LC_HDL ullLcHdl, int nTemporary, double dbFontSize);


	/**
	* @brief label context drawing settings - Set whether the text to be drawn is bolded
	* @par Explanation:
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting is restored after a DSTP2x_Lbl_DrawText or DSTP2x_Tbl_DrawText call
	* 
	* @param [in] nIsBold, Is bolded, legal values: 0 and 1, Or Set [2,5] to bold level
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetTextBold(LC_HDL ullLcHdl, int nTemporary, int nIsBold);


	/**
	* @brief label context drawing settings - Set the horizontal alignment of the text to be drawn
	* @par Explanation
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting is restored after a DSTP2x_Lbl_DrawText or DSTP2x_Tbl_DrawText call
	* 
	* @param [in] dbX, The horizontal axis of the alignment line
	* 
	* @param [in] nAlign, Alignment method
	* @n 0- No alignment feature
	* @n 1- Left aligned
	* @n 2- Center Alignment
	* @n 3- Right aligned
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetTextHAlign(LC_HDL ullLcHdl, int nTemporary, double dbX, int nAlign);


	/**
	* @brief label context drawing settings - Set the vertical alignment of the text to be drawn
	* @par Explanation
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting is restored after a DSTP2x_Lbl_DrawText or DSTP2x_Tbl_DrawText call
	* 
	* @param [in] dbY, The vertical axis of the alignment line
	* 
	* @param [in] nAlign, alignment method
	* @n 0- No alignment feature
	* @n 1- Top Alignment
	* @n 2- Center Alignment
	* @n 3- Bottom alignment
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetTextVAlign(LC_HDL ullLcHdl, int nTemporary, double dbY, int nAlign);


	/**
	* @brief label context drawing settings - Set whether the text to be drawn is italicized or not
	* @par Explanation:
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting is restored after a DSTP2x_Lbl_DrawText or DSTP2x_Tbl_DrawText call
	* 
	* @param [in] nIsItalic, italicized? Value range: [0,1]
	* @n 0- Do not use italics
	* @n 1- Use italics
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetTextItalic(LC_HDL ullLcHdl, int nTemporary, int nIsItalic);


	/**
	* @brief label context drawing settings - Set whether the text to be drawn will automatically wrap
	* @par Explanation:
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting is restored after a DSTP2x_Lbl_DrawText or DSTP2x_Tbl_DrawText call
	* 
	* @param [in] nIsAutoLineFeed. Does it automatically wrap? Value range: [0,1]
	* @n 0- Do not wrap automatically
	* @n 1- Automatic line wrapping
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetTextAutoLineFeed(LC_HDL ullLcHdl, int nTemporary, int nIsAutoLineFeed);


	/**
	* @brief label context drawing settings - Set the line spacing of the text to be drawn
	* @par Explanation:
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting is restored after a DSTP2x_Lbl_DrawText or DSTP2x_Tbl_DrawText call
	* 
	* @param [in] dSpacing, The line spacing, unit: pound
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetTextLineSpacing(LC_HDL ullLcHdl, int nTemporary, double dSpacing);


	/**
	* @brief label context drawing settings - Set the spacing between text characters to be drawn
	* @par Explanation:
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting is restored after a DSTP2x_Lbl_DrawText or DSTP2x_Tbl_DrawText call
	* 
	* @param [in] dSpacing, The spacing, unit: pound
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetTextCharSpacing(LC_HDL ullLcHdl, int nTemporary, double dSpacing);


	/**
	* @brief label context drawing settings - Set rotation parameters for the text to be drawn
	* @par Explanation:
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting is restored after a DSTP2x_Lbl_DrawText or DSTP2x_Tbl_DrawText call
	* 
	* @param [in] nAngle, The rotation angle, range [-360 360]
	* 
	* @param [in] nAnchorPoint, Set rotation reference center
	* @n 0- Upper left corner
	* @n 1- Left center point
	* @n 2- Bottom left corner
	* @n 3- Center point
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetTextRotation(LC_HDL ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);


	/**
	* @brief label context drawing settings - Set rotation parameters for the image to be drawn
	* @par Explanation:
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting will be restored after a DSTP2x_Lbl_darawImage or DSTP2x_Tbl_darawImage call
	* 
	* @param [in] nAngle, The rotation angle, range [-360 360]
	* 
	* @param [in] nAnchorPoint, Set rotation reference center
	* @n 0- Upper left corner
	* @n 1- Left center point
	* @n 2- Bottom left corner
	* @n 3- Center point
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetImageRotation(LC_HDL ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);



	/**
	* @brief  label context drawing settings - Set rotation parameters for the rectangle to be drawn
	* @par    Explanation£º
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting will be restored after a DSTP2x_Lbl_DrawRectangle or DSTP2x_Tbl_DrawRectangle call
	* 
	* @param [in] nAngle, The rotation angle, range [-360 360]
	* 
	* @param [in] nAnchorPoint, Set rotation reference center
	* @n 0- Upper left corner
	* @n 1- Left center point
	* @n 2- Bottom left corner
	* @n 3- Center point
	*
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetRectangleRotation(LC_HDL ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);


	/**
	* @brief  label context drawing settings - Set rotation parameters for the ellipse to be drawn
	* @par    Explanation£º
	*
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting will be restored after a DSTP2x_Lbl_DrawEllipse or DSTP2x_Tbl_DrawEllipse call
	* 
	* @param [in] nAngle, The rotation angle, range [-360 360]
	* 
	* @param [in] nAnchorPoint, Set rotation reference center
	* @n 0- Upper left corner
	* @n 1- Left center point
	* @n 2- Bottom left corner
	* @n 3- Center point
	*
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetEllipseRotation(LC_HDL ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);



	/**
	* @brief label context drawing settings - Set the halftone processing algorithm for the image to be drawn
	* @par Explanation:
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting will be restored after a DSTP2x_Lbl_darawImage or DSTP2x_Tbl_darawImage call
	* 
	* @param [in] nAlgorithm, The image algorithm
	* @n 0- Do not perform algorithm (default)
	* @n 1- Error diffusion
	* @n 2- Ordered jitter algorithm
	* @n 3- Threshold operation algorithm
	* 
	* @param [in] nThrehold, The threshold, effective when nAlgorithm is 3, range [0,255]
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetImageHalftoneAlgo(LC_HDL ullLcHdl, int nTemporary, int nAlgorithm, int nThreshold);



	/**
	* @brief label context drawing settings - Set the error correction level for the QR code to be drawn
	* @par Explanation:
	* This setting is applicable to QR code types such as PDC417, MicroPDF417, QRCode, etc
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting is restored after a DSTP2x_Lbl_DrawBarCode or DSTP2x_Tbl_DrawBarCode call
	* 
	* @param [in] nErrorCorrectLevel, Error Correction Level, the specific value range depends on the nCodeType of the DSTP2x_DrawCode function
	* When nCodeType is QRCode, the range of values for the eErrorCorrectLevel parameter is [1,4]. If not set, there is no error correction level by default
	* When nCodeType is PDF417, the range of values for the eErrorCorrectLevel parameter is [0,8]. If not set, the default error correction level is 2
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetBarCodeEcLvl(LC_HDL ullLcHdl, int nTemporary, int nErrorCorrectLevel);


	/**
	* @brief label context drawing settings - Set whether to print annotation lines for the barcode to be drawn
	* @par Explanation:
	* This setting is applicable to various barcode types such as CODE39, CODE128, CODE93, UPC-A, UPC-E, EAN-8, EAN-13, EAN-14, etc
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting is restored after a DSTP2x_Lbl_darawBarCode or DSTP2x_Tbl_darawBarCode call
	* 
	* @param [in] nExplanation, Whether annotation is generated for the eXplonation barcode
	* @n 0- Do not generate comments
	* @n 1- Generate comments
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetBarCodeExpl(LC_HDL ullLcHdl, int nTemporary, int nExplanation);


	/**
	* @brief label context drawing settings - Set rotation parameters for barcode and QR code to be drawn
	* @par Explanation:
	* This setting is applicable to various barcode types such as CODE39, CODE128, CODE93, UPC-A, UPC-E, EAN-8, EAN-13, EAN-14, etc
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] nTemporary, Is this setting temporary
	* @n 0- Persistent until ullLcHdl expires, unless modified again
	* @n 1- Temporary, this setting is restored after a DSTP2x_Lbl_DrawBarCode or DSTP2x_Tbl_DrawBarCode call
	* 
	* @param [in] nAngle, The rotation angle, range [-360,360]
	* 
	* @param [in] nAnchorPoint, Set rotation reference center
	* @n 0- Upper left corner
	* @n 1- Left center point
	* @n 2- Bottom left corner
	* @n 3- Center point
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcDraw_SetBarCodeRotation(LC_HDL ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);


	/**
	* @brief Create a table
	* @par Explanation
	*  1.  If the function is executed successfully, the newly created table handle will be returned by pTblHdl;
	*  2.  Once a table is created, the number of rows and columns cannot be changed
	*  3.  Tables support modifying table width, height, column width, row height, merging/restoring cells, drawing text, one-dimensional and two-dimensional barcodes, images, and other operations within cells
	*  4.  The cell name arrangement of the created table, such as 3x2, will be represented in the following form:   0-0 0-1 0-2 1-0 1-1 1-2	
	* 
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	* 
	* @param [in] dbX, The table top left horizontal axis, unit: mm (millimeter)
	* 
	* @param [in] dbY, The table top left vertical axis, unit: mm (millimeter)
	* 
	* @param [in] dbW, The width of the table, which is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeters)
	* 
	* @param [in] dbH, The height of the table, which is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
	* 
	* @param [in] nRowCount, The number of rows in the table to be created
	* 
	* @param [in] nColCount, The number of columns in the table to be created
	* 
	* @param [in] nLineWidth The width of the line in the box of the table to be created, unit: dot, value range: [1,50]
	* 
	* @param [out] pTblHdl, The table handle address
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_CreateTable(LC_HDL ullLcHdl, double dbX, double dbY, double dbW, double dbH, int nRowCount, int nColCount, int nLineWidth, TABLE_HDL *pTblHdl);


	/**
	* @brief changes the column width of the table by moving the boundary lines of the columns
	* @par Explanation
	*  1.  The number of boundary lines in a column is 1 more than the number of columns
	*  2.  The boundary clues of the column, from left to right, are 0, 1, 2, 3
	*  3.  Since the starting position of the table is predetermined, the leftmost column boundary line (with index value 0) cannot be moved left or right
	*  3.  Moving the boundary line of the rightmost column to the left or right will directly change the width of the table. Moving the boundary line between the leftmost and rightmost columns to the left or right will only change the column width on both sides of the boundary line, showing a trade-off relationship.
	* 
	* @param [in] ullTblHdl, This is the table handle returned by the DSTP2x_CreateTable function
	* 
	* @param [in] nColSepLineIdx, The column boundary clue index, value range [1, n], n equals the number of columns
	* 
	* @param [in] nMoveDir, The boundary line movement direction
	* @n 1- Left shift
	* @n 2- Right shift
	* 
	* @param [in] dbStep, The step value of the moving boundary line, unit: mm (millimeter), accuracy: 0.01mm
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Tbl_MoveColBoundary(TABLE_HDL ullTblHdl, int nColSepLineIdx, int nMoveDir, double dbStep);


	/**
	* @brief changes the row height of the table by moving the boundary lines of rows
	* @par Explanation
	*  1.  The number of boundary lines in a row is 1 more than the number of rows
	*  2.  The boundary clues of the rows are 0, 1, 2, 3, etc. from top to bottom
	*  3.  Since the starting position of the table is predetermined, the top row boundary line (with an index value of 0) cannot be moved up or down
	*  4.  Moving the bottom column boundary line up or down will directly change the width of the table, while moving the boundary line between the top and bottom will only change the row height on both sides of the boundary line, showing a trade-off relationship.
	* 
	* @param [in] ullTblHdl, This is the table handle returned by the DSTP2x_CreateTable function
	* 
	* @param [in] nRowSepLineIdx, The boundary clue index, value range [1, n], n equals the number of rows
	* 
	* @param [in] nMoveDir, The boundary line movement direction
	* @n 1- Move Up
	* @n 2- Move Down
	* 
	* @param [in] dbStep, The step value of the moving boundary line, unit: mm (millimeter), accuracy: 0.01mm
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Tbl_MoveRowBoundary(TABLE_HDL ullTblHdl, int nRowSepLineIdx, int nMoveDir, double dbStep);


	/**
	* @brief Merge Cells
	* @par Explanation
	* 
	* @param [in] ullTblHdl, This is the table handle returned by the DSTP2x_CreateTable function.
	* 
	* @param [in] nRowBegin The starting row of the cells to be merged.
	* 
	* @param [in] nRowEnd, The ending row of cells to be merged.
	* 
	* @param [in] nColBegin, The starting column of the cells to be merged.
	* 
	* @param [in] nColEnd, The ending column of cells to be merged.
	* 
	* @param [out] szMergedGridName, The name of the merged new cell, character encoding: utf-8£¬ For example: "Merged-0"£¬ Suggest allocating no less than 32 bytes of space
	* 
	* @param [in, out] pMergedGridNameSize, Returns the length of the information. The input parameter is the memory size of szMergedGridName, and the output parameter represents the actual length of memory written to szMergedGridName
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Tbl_MergeGrids(TABLE_HDL ullTblHdl, int nRowBegin, int nRowEnd, int nColBegin, int nColEnd, char *szMergedGridName, int *pMergedGridNameSize);


	/**
	* @brief Restore (merged) cells
	* @par Explanation
	* 
	* @param [in] ullTblHdl, This is the table handle returned by the DSTP2x_CreateTable function
	* 
	* @param [out] szMergedGridName, This is the name of the merged new cell returned by the DSTP2x_Tbl_MergeGrids function
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Tbl_RevertMergedGrid(TABLE_HDL ullTblHdl, const char *szMergedGridName);


	/**
	* @brief Draw text on specified cells in the table
	* @par Explanation
	* 
	* @param [in] ullTblHdl, This is the table handle returned by the DSTP2x_CreateTable function
	* 
	* @param [out] szGridName, The name of the cell, character encoding: utf-8£» For example, the basic cells are "0-0", "0-1", "1-0", "1-1", etc; The merged cells are "Merged-0", "Merged-1", etc
	* 
	* @param [in] dbX, The horizontal axis of the upper left corner of the text content block relative to the upper left corner of the cell, in millimeters (mm)
	* 
	* @param [in] dbY, The vertical axis of the upper left corner of the text content block relative to the upper left corner of the cell, in millimeters (mm)
	* 
	* @param [in] dbW, The width of the text content block, which is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
	* 
	* @param [in] dbH, The height of the text content block, which is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
	* 
	* @param [in] szText, The text content that needs to be drawn in the drawing context, character encoding: utf-8¡£
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Tbl_DrawText(TABLE_HDL ullTblHdl, const char *szGridName, double dbX, double dbY, double dbW, double dbH, const char *szText);


	/**
	* @brief Draw one-dimensional and two-dimensional barcodes on specified cells in the table
	* @par Explanation
	* 
	* @param [in] ullTblHdl, This is the table handle returned by the DSTP2x_CreateTable function
	* 
	* @param [out] szGridName, The name of the cell, character encoding: utf-8£» For example, the basic cells are "0-0", "0-1", "1-0", "1-1", etc; The merged cells are "Merged-0", "Merged-1", etc
	* 
	* @param [in] dbX, The horizontal axis of the upper left corner of the text content block relative to the upper left corner of the cell, in millimeters (mm)
	* 
	* @param [in] dbY, The vertical axis of the upper left corner of the text content block relative to the upper left corner of the cell, in millimeters (mm)
	* 
	* @param [in] dbW, The width of the text content block, which is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
	* 
	* @param [in] dbH, The height of the text content block, which is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
	* 
	* @param [in] nCodeType. This is the encoding type used to generate barcodes
	*  @n 8 - CODE39
	*  @n 20 - CODE128
	*  @n 25 - CODE93
	*  @n 34 - UPCA
	*  @n 37 - UPCE
	*  @n 55 - PDF417
	*  @n 58 - QRCode
	*  @n 71 - DataMatrix
	*  @n 72 - EAN14
	*  @n 84 - MicroPDF417
	*  @n 116 - HanXin
	*  @n 142 - GridMatrix
	* 
	* @param [in] szData, It needs to draw barcode data in the drawing context.
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Tbl_DrawBarCode(TABLE_HDL ullTblHdl, const char *szGridName, double dbX, double dbY, double dbW, double dbH, int nCodeType, const char *szData);


	/**
	* @brief Draw an image on the specified cell in the table
	* @par Explanation
	* 
	* @param [in] ullTblHdl, This is the table handle returned by the DSTP2x_CreateTable function
	* 
	* @param [out] szGridName, The name of the cell, character encoding: utf-8£» For example, the basic cells are "0-0", "0-1", "1-0", "1-1", etc; The merged cells are "Merged-0", "Merged-1", etc
	* 
	* @param [in] dbX, The horizontal axis of the upper left corner of the dbX text content block relative to the upper left corner of the cell, in millimeters (mm)
	* 
	* @param [in] dbY, The vertical axis of the upper left corner of the dbY text content block relative to the upper left corner of the cell, in millimeters (mm)
	* 
	* @param [in] dbW, The width of the text content block, which is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
	* 
	* @param [in] dbH, The height of the text content block, which is a non negative floating-point number. If it is 0, it means this parameter is ignored. Unit: mm (millimeter)
	* 
	* @param [in] dbScale, The scaling factor of it relative to the original image size, which is a non negative floating-point number. If it is 0, it means this parameter is ignored, and the value range must be between 1 and 3
	* 
	* @param [in] nImgDataType, Image data type	
	* @n 0- Local image file
	* @n 1- Image Memory Data
	* @n 2-base64 format image data
	* 
	* @param [in] szImage, It needs to draw image data in the drawing context.
	* When nImgDataType is 1 or 2, the size of unImgDataSize is the actual memory size pointing to szImage. When nImgDataType is 0, the size of unImgDataSize is the length pointing to szImage.
	*
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Tbl_DrawImage(TABLE_HDL ullTblHdl, const char *szGridName, double dbX, double dbY, double dbW, double dbH, double dbScale, int nImgDataType, const char *szImage, unsigned int unImgDataSize);



	/**
	* @brief Draw line segments on specified cells in the table
	* @par Explanation
	* 
	* @param [in] ullTblHdl, this is the table handle returned by the DSTP2x_CreateTable function
	*
	* @param [out] szGridName, The name of the cell, character encoding: utf-8£» For example, the basic cells are "0-0", "0-1", "1-0", "1-1", etc; The merged cells are "Merged-0", "Merged-1", etc
	*
	* @param [in] dbStartX, The horizontal coordinate of the starting point of the line segment relative to the upper left corner of the label as the origin, in millimeters (mm)
	* 
	* @param [in] dbStartY, The vertical coordinate of the starting point of the line segment relative to the top left corner of the label as the origin, in millimeters (mm)
	*
	* @param [in] dbEndX, The line segment's endpoint horizontal coordinate relative to the top left corner of the label as the origin, unit: mm (millimeters)
	*
	* @param [in] dbEndY, The vertical coordinate of the endpoint of the dbEndY line segment relative to the upper left corner of the label as the origin, in millimeters (mm)
	*
	* @param [in] nLineWidth, The line segment width, unit: pixel
	*
	* @param [in] nLineType, THe line segment type, 0: solid line, 1: dashed line, 2: dotted line, 3: dotted solid line, 4: double dotted solid line
	*
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Tbl_DrawLine(TABLE_HDL ullTblHdl, const char *szGridName, double dbStartX, double dbStartY, double dbEndX, double dbEndY, int nLineWidth, int nLineType);



	/**
	* @brief  Draw a rectangle on a specified cell in the table
	* @par    Explanation
	*
	* @param [in]            ullTblHdl              , this is the table handle returned by the DSTP2x_CreateTable function
	* 
	* @param [out] 		     szGridName             , The name of the cell, character encoding: utf-8£» For example, the basic cells are "0-0", "0-1", "1-0", "1-1", etc; The merged cells are "Merged-0", "Merged-1", etc
	* 
	* @param [in]            dbX					, The horizontal axis of the top left corner of the rectangle, unit: mm (millimeter)
	* 
	* @param [in]            dbY					, The vertical axis of the top left corner of the rectangle, unit: mm (millimeter)
	* 
	* @param [in]            dbW                    , Width of rectangle, unit: mm (millimeter)
	* 
	* @param [in]            dbH                    , Height of rectangle, unit: mm (millimeter)
	* 
	* @param [in]            nLineWidth             , Line width of rectangle, unit: pixel
	* 
	* @param [in]            nLineType              , Rectangular line type, 0: solid line, 1: dashed line
	* 
	* @param [in]            nIsFill                , Whether to fill, 1: Yes, 0: No
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Tbl_DrawRectangle(TABLE_HDL ullTblHdl, const char *szGridName, double dbX, double dbY, double dbW, double dbH, int nLineWidth, int nLineType, int nIsFill);

	/**
	* @brief  Draw an ellipse on a specified cell in the table
	* @par    Explanation
	*
	* @param [in]            ullTblHdl				, this is the table handle returned by the DSTP2x_CreateTable function
	* 
	* @param [out] 		     szGridName				, The name of the cell, character encoding: utf-8£» For example, the basic cells are "0-0", "0-1", "1-0", "1-1", etc; The merged cells are "Merged-0", "Merged-1", etc
	* 
	* @param [in]            dbX					, The horizontal axis of the top left corner of the ellipse, unit: mm (millimeter)
	* 
	* @param [in]            dbY					, The vertical axis of the top left corner of the ellipse, unit: mm (millimeter)
	* 
	* @param [in]            dbW					, Width of ellipse, unit: mm (millimeter)
	* 
	* @param [in]            dbH					, Height of ellipse, unit: mm (millimeter)
	* 
	* @param [in]            nLineWidth				, Line width of ellipse, unit: pixel
	* 
	* @param [in]            nLineType				, Types of elliptical lines, 0: solid line, 1: dashed line
	* 
	* @param [in]            nIsFill				, Whether to fill, 1: Yes, 0: No
	* 
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_Tbl_DrawEllipse(TABLE_HDL ullTblHdl, const char *szGridName, double dbX, double dbY, double dbW, double dbH, int nLineWidth, int nLineType, int nIsFill);



	/**
	* @brief Delete table handle
	* @par Explanation
	* 
	* @param [in] ullTblHdl, This is the handle of table returned by the DSTP2x_CreateTable function
	*
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_DeleteTable(TABLE_HDL ullTblHdl);


	/**
	* @brief Set the RFID data to be written during the label context printing process
	* @par Explanation
	* If this function is not called, RFID reading/writing will not be performed during the printing process
	* @param [in] ullLcHdl, This is the label context handle returned by the DSTP2x_CreateLabelContext function
	*
	* @param [in] nRfidRgnType, This is the type of area where RFID data needs to be written during the printing process
	* @n 1- EPC area
	* @n 2- USER area
	* 
	* @param [in] nRFidDataMmt, The format of RFID data that needs to be written during the printing process for it 
	* @n 1- ASCII encoded string
	* @n 2- Hexadecimal string
	* @n 3- Hexadecimal byte data
	*
	* @param [in] pData, The RFID data that needs to be written into pData during the printing process
	*
	* @param [in] nDataSize, The length of RFID data to be written during the printing process, in bytes;
	* If pData is a string, this parameter represents the actual string length of pData (excluding "\ 0")
	* If pData is hexadecimal byte data, this parameter represents the actual length of data that pData should write
	*
	* @return 0 indicates success, non-zero failure
	*/
	unsigned int DSSDK DSTP2x_LcRfid_SetData(LC_HDL ullLcHdl, int nRfidRgnType, int nRfidDataFmt, const char *pData, int nDataSize);


	/**
	* 
	*  @}
	*/
#ifdef __cplusplus
}
#endif
#endif /*- __DSTP2x_H__ -*/
