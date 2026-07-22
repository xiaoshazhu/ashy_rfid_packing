/**
*
* @file DSTP2x.h
* @brief DS热式打印机SDK接口头文件
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
typedef unsigned long long PDF_HDL  ;				// pdf handle
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



/** @defgroup DynamicLibraryRelatived 库基本操作接口
*   @brief 动态库接口，如初始化、资源清理、设置库语言、解析错误码等
*
*  @{
*
*/


/**
* @brief  动态库初始化
* @par    说明：
* 用以初始化SDK库资源；当本动态库被加载后，进程内必须且仅需成功调用一次本接口。
* 调用失败时需要查看pSzResult的内容的描述有助于分析问题。
* @note   若进程内本接口未曾被成功调用过，其他接口将无法正常使用！！！
* @param [in] 		pSzInitInfo 	自定义描述信息(默认传"")
* @param [in] 		nInitInfoLen 	自定义描述信息长度
* @param [out] 		pSzResult 		返回初始化成功的说明信息或者初始化失败的出错信息，字符编码：utf-8，建议分配不小于1024字节的空间
* @param [in,out]  	pResultLen 		返回信息的长度，入参数为pSzResult的内存大小，出参数时表示实际写入pSzResult内存的长度
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Lib_Init(char *pSzInitInfo, int nInitInfoLen, char *pSzResult, int *pResultLen);

/**
* @brief  动态库清理
* @par    说明：
* 动态库被卸载前必须调用，进程调用一次即可
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Lib_Clear();


/**
* @brief  获取本库版本号
* @par    说明：
* 本热敏库的版本号为五组数字。
* @param [out]           pLibVer 	              用于存放返回的版本号信息，建议缓存区预分配不小于16字节
* @param [in,out] 		 pLibVerLen               入参时表示pLibVer的缓存区大小，出参时表示实际存入pLibVer的数据长度
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_GetLibVersion(char *pLibVer, int *pLibVerLen);


/**
* @brief  获取本库信息
* @par    说明：
* @param [out]           pLibInfo 	              用于存放返回的库信息，建议缓存区预分配不小于256字节
* @param [in,out] 		 pLibInfoLen              入参时表示pLibInfo的缓存区大小，出参时表示实际存入pLibInfo的数据长度
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_GetLibInfo(char *pLibInfo, int *pLibInfoLen);

/**
* @brief  设置库语言
* @par    说明：
* 能设置成中文或英文
* @param [in]        nLanguage               语言
* @n 0 - 中文（默认）
* @n 1 - 英文
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetLibLang(int nLanguage);


/**
* @brief  解析SDK接口返回的错误码
* @par    说明：
* 将SDK接口返回的错误码翻译成对应的解释
* @param [in]        unSDKErrCode            SDK接口返回的错误码
* @param [out]        szDesc                  输出字符串缓存区，大小：不少于1024字节，字符串的字符编码：utf-8
* @param [in, out]   pLen                    入参时：szDesc指向的缓存区大小，出参时：实际写入szDesc指向的缓存区的字符串长度
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_ApiRtnCodeToMsg(unsigned int unSDKErrCode, char *szDesc, int *pLen);

/**
*
* @}
*/



/** @defgroup DeviceConnection 设备连接
*   @brief 设备枚举、连接超时设置、选定设备等
*
*  @{
*
*/

/**
* @brief  设置网口枚举打印机接收应答时，允许连续读不到数据的次数
* @par    说明
* 需根据当前局域网网络环境动态调整
* @param [in]            nTimes              允许连续读不到数据的次数。如果网络较拥堵，可设置10；如果网络较空闲，可设置5
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetNetEnumRecvTimes(int nTimes);

/**
* @brief  设置网口枚举打印机时，需要进行枚举的多个子网段
* @par    说明
* 
* @param [in]        szSubNets              需要进行枚举的多个子网段，两个子网段之间以"|"分隔开；格式如：192.168.1.*|172.10.*.*
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetNetEnumSubNets(const char *szSubNets);


/**
* @brief  搜索在线设备
* @par    说明
* 请确保设备已开机且已连接到PC机
* @param [in]            nEnumType             枚举类型
* @n 1 - 枚举USB在线的设备
* @n 2 - 枚举TCP在线的设备
* @param [out]           szEnumList            枚举列表，若有多台设备则以“\n”分隔
* @param [in,out]        pDevSize              入参时指出szEnumList的大小，出参时指出实际填入szEnumList的字符串长度
* @param [out]           pDevNum               枚举到的在线的设备数量
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_EnumDev(int nEnumType, char *szEnumList, int *pDevSize, int *pDevNum);

/**
* @brief  通过设备名称连接设备
* @par    说明
* 根据DSTP2x_EnumDev接口枚举得到的设备集，连接其中的设备
* @param [in]            szDevName              来自DSTP2x_EnumDev返回的szEnumList中的一台设备的名称
* @param [out]           pDevHdl                设备句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_ConnEnumeratedDev(const char *szDevName, DEV_HDL *pDevHdl);

/**
* @brief  通过IP和端口连接设备
* @par    说明
* 通过IP和端口直接连接上设备，并获得设备句柄。
* @param [in]            szIpPort               通过传入Ip地址和端口号直接连接设备，如传入"165.469.2.23:5100"
* @param [out]           pDevHdl                设备句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_ConnNetworkDev(const char *szIpPort, DEV_HDL *pDevHdl);

/**
* @brief  通过串口号和波特率连接设备
* @par    说明
* 通过串口号和波特率直接连接设备，并获得设备句柄。
* @param [in]            nSerialNo              串口号
* @param [in]            nBaudRate              波特率
* @param [out]           pDevHdl                设备句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_ConnSerialDev( int nSerialNo, int nBaudRate, DEV_HDL *pDevHdl);

/**
* @brief  断开设备连接
* @par    说明：
* 
* @param [in]            ullDevHdl               设备句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_DisconnDev(DEV_HDL ullDevHdl);

/**
* @brief  设置连接的通讯超时
* @par    说明
* 
* @param [in]            ullDevHdl               设备句柄地址
* @param [in]            nCommType               设置通讯超时类型
* @n 1 - 设置USB超时
* @n 2 - 设置TCP超时
* @n 3 - 设置串口超时
* @param [in]            unSendTimeout           数据发送超时，单位：毫秒
* @param [in]            unRecvTimeout           数据接收超时，单位：毫秒
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetCommTimeout(DEV_HDL ullDevHdl, int nCommType, unsigned int unSendTimeout, unsigned int unRecvTimeout);


/**
* @brief  向打印机直传数据
* @par    说明
* 支持直接传指令或十六进制数据通讯; 也支持单向指令数据，此时pOutData可传0表示程序后续无需接收打印机的应答数据
* @param [in]            ullDevHdl                 设备句柄地址
* @param [in]            pInData 	               待发送数据，可为字符串类型或普通十六进制数据
* @param [in]            nInDataSize 	           表示pInData的数据对应的长度
* @param [out]           pOutData 	               用于存放打印机返回的应答数据的缓存区，请根据所发请求数据决定其应答数据的长度，建议缓存区预分配不小于1024字节
* @param [in,out] 		 nOutDataSize              入参时表示pOutData的缓存区大小，出参时表示实际存入pOutData的数据长度
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_TransRecvData(DEV_HDL ullDevHdl, const char *pInData, int nInDataSize, char *pOutData, int *nOutDataSize);


/**
* @brief 设置网口连接重试相关参数
* @par    Description:
* 当此接口没有被调用，默认重试次数为1，重试间隔为3000ms
* @param [in]       szIp				  设备Ip地址, 当传空字符串""时为针打所有网口连接的打印机
* @param [in]       iTryConnNum           网络重连次数
* @param [in]       iTryInterval          网络重连时间间隔, 单位: ms
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetNetworkReconnectPar(const char *szIp, int iTryConnNum, int iTryInterval);

/**
*
* @}
*/



/** @defgroup DeviceControl 常用功能
*  @brief 打印自检页、清缓存等
*
*  @{
*
*/


/**
* @brief  打印自检页
* @par    说明：
* 打印出设备的基本信息，有厂商，机型，机号、打印仿真类型等信息
* @param [in]            ullDevHdl                 设备句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_PrintSelfCheckPage(DEV_HDL ullDevHdl);


/**
* @brief  设备清缓存
* @par    说明：
* 实现效果：相当于硬重启打印机达到的效果，当然也包括清除缓存
* @param [in]            ullDevHdl                 设备句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RestartPrt(DEV_HDL ullDevHdl);


/**
* @brief  即时切纸
* @par    说明
* 使用条件：当前打印机内置了切刀模组且切刀功能已开启
* @param [in]            ullDevHdl                 设备句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_CutPaper(DEV_HDL ullDevHdl);


/**
* @brief  移动纸张
* @par    说明
* 使用条件：当前打印机内置了RFID模块且已开启
* @param [in]            ullDevHdl                 设备句柄地址
* @param [in]            nDir                      纸张移动方向
* @n 0 - 向前
* @n 1 - 向后
* @param [in]            dbDistance                纸张移动距离，单位：mm
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_MovePaper(DEV_HDL ullDevHdl, int nDir, double dbDistance);


/**
* @brief  普通标签定位
* @par    说明
* 使用条件：当前打印机纸张模式为标签纸
* @param [in]            ullDevHdl                 设备句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LocateLabel(DEV_HDL ullDevHdl);


/**
* @brief  连续纸黑标定位
* @par    说明
* 使用条件：当前打印机纸张模式为标签纸
* @param [in]            ullDevHdl                 设备句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LocateBlackMark(DEV_HDL ullDevHdl);

/**
*
* @}
*/



/** @defgroup PrinterInfoQuery 设备信息查询
*   @brief 打印机状态、打印机序列号、固件版本号等
*
*  @{
*
*/


/**
* @brief  查询打印机状态
* @par    说明
* 因打印机存在同一时刻不止状态、警告、错误同时出现的情况，本函数返回时实际存入pMainStatus、pWarning、pError的信息个数可能不止一个
* @param [in]            ullDevHdl                 设备句柄地址
* @param [out]           pIsReady 				   判断打印机是否能继续正常工作，返回1能，0否；如传0，则表示不使用该参数
* @param [out]           pMainStatus 	           函数返回时用于存放主状态的数组，建议预分配8个数组元素；如传0，则表示不使用该参数
* @param [in,out] 		 pMainStatusNum 	       入参时表示pMainStatus的数组大小，出参时表示实际存入pMainStatus的主状态个数；如传0，则表示不使用该参数
* @param [out]           pWarning 	               函数返回时用于存放警告的数组，建议预分配8个数组元素；如传0，则表示不使用该参数
* @param [in,out] 		 pWarningNum 	           入参时表示pWarning的数组大小，出参时表示实际存入pWarnings的警告信息个数；如传0，则表示不使用该参数
* @param [out]           pError 	               函数返回时用于存放出错信息的数组，建议预分配8个数组元素；如传0，则表示不使用该参数
* @param [in,out] 		 pErrorNum 	               入参时表示pError的数组大小，出参时表示实际存入pError的出错信息个数；如传0，则表示不使用该参数
* @param [out]			 pDesc					   状态，警告和错误等详细描述，返回字符串格式如：\n
主状态:xxx,xxx|警告:无|错误:xxx,xxx|纸张类型|打印模式|切刀状态|剥离器状态|传感器状态；\n如传0，则表示不使用该参数
* @param [in,out] 		 pDescLen				   入参时表示pDesc的buffer长度，出参时表示实际返回的pDesc内容长度；如传0，则表示不使用该参数
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_GetPrtStatus(DEV_HDL ullDevHdl, int *pIsReady, int *pMainStatus, int *pMainStatusNum, int *pWarning, int *pWarningNum, int *pError, int *pErrorNum, char* pDesc, int *pDescLen);

/**
* @brief  查询打印机序列号
* @par    说明
* 
* @param [in]            ullDevHdl                 设备句柄地址
* @param [out]           szPrtSN 	               用于存放打印机序列号字符串的缓存区，字符编码为ASCII，格式如：228022200001，建议缓存区预分配不小于32字节
* @param [in,out] 		 pPrtSNSize 	           入参时表示szPrtSN的缓存区大小，出参时表示实际存入szPrtSN的字符串长度（不含'\0'）
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_GetPrtSN(DEV_HDL ullDevHdl, char *szPrtSN, int *pPrtSNSize);

/**
* @brief  查询打印机固件版本号
* @par    说明
* 
* @param [in]            ullDevHdl                 设备句柄地址
* @param [out]           szPrtFWVer 	           用于存放打印机序列号字符串的缓存区，字符编码为ASCII，格式如：01.08.00.0a，建议缓存区预分配不小于32字节
* @param [in,out] 		 pPrtFWVerSize             入参时表示szPrtFWVer的缓存区大小，出参时表示实际存入szPrtFWVer的字符串长度（不含'\0'）
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_GetPrtFWVer(DEV_HDL ullDevHdl, char *szPrtFWVer, int *pPrtFWVerSize);



/**
* @brief  查询打印机电机转动路程
* @par    说明
* 
* @param [in]            ullDevHdl                 设备句柄地址
* @param [out]           pDistance 				   返回打印机电机转动路程距离，单位mm	
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_GetPrtMotorTravelDistance(DEV_HDL ullDevHdl, unsigned int *pDistance);


/**
* @brief  查询打印机机型名
* @par    说明
*
* @param [in]            ullDevHdl                 设备句柄地址
* @param [out]           szPrtName 	           用于存放打印机机型名字符串的缓存区，字符编码为ASCII，建议缓存区预分配不小于64字节
* @param [in,out] 		 pPrtNameSize             入参时表示szPrtName的缓存区大小，出参时表示实际存入szPrtName的字符串长度（不含'\0'）
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_GetPrtName(DEV_HDL ullDevHdl, char *szPrtName, int *pPrtNameSize);


/**
*
* @}
*/



/** @defgroup PrinterSettings 功能设置
*  @brief 打印偏移、打印仿真、图像分辨率等设置
*
*  @{
*
*/


/**
* @brief  设置打印偏移
* @par    说明
* 因某些标签周边存在距离不等的衬底，为使打印内容准确打印到标签指定位置，用户按标签实际情况选择是否调用本函数
* @param [in]            ullDevHdl                 设备句柄地址
* @param [in]            dbXOffset 	               水平方向上相对打印起始位置的偏移量，单位：mm（毫米）
* @param [in] 		     dbYOffset                 垂直方向上相对打印起始位置的偏移量，单位：mm（毫米）
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetPrnOffset(DEV_HDL ullDevHdl, double dbXOffset, double dbYOffset);


/**
* @brief  设置仿真类型
* @par    说明
* 设置打印数据使用的仿真类型
* @param [in]            ullDevHdl                 设备句柄地址
* @param [in]            nEmulation 	           仿真类型
* @n 0 - 自动适配打印机当前仿真（预留）
* @n 1 - ZPL
* @n 2 - TSPL
* @n 3 - ESCPOS
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetPrnEmulation(DEV_HDL ullDevHdl, int nEmulation);


/**
* @brief  设置待绘制图像的分辨率
* @par    说明
* 
* @param [in]            ullDevHdl                 设备句柄地址
* @param [in]            nDpi 	                   待绘制图像的分辨率
* @n 1 - 203dpi
* @n 2 - 300dpi
* @n 3 - 600dpi
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetImgDpi(DEV_HDL ullDevHdl, int nDpi);


/**
* @brief  设置获取状态的实时性
* @par    说明
* 如不调用本函数，则DSTP2x_GetPrtStatus将是非实时的
* @param [in]            ullDevHdl                 设备句柄地址
* @param [in]            nRealtime                 实时性
* @n 0 - 非实时；打印机默认（U口、网口、串口）都支持非实时获取状态；此时，打印机串行地执行主机下发的指令，获取状态请求不会被优先、实时处理
* @n 1 - 实时；打印机目前只有在U口连接方式下才支持实时获取状态；此时，获取状态请求会被优先、实时处理
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetRTStatus(DEV_HDL ullDevHdl, int nRealtime);


/**
* @brief  开启切刀功能
* @par    说明
* 如不调用本函数，则切刀功能默认关闭
* @param [in]            ullDevHdl                 设备句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_TurnOnCutter(DEV_HDL ullDevHdl);


/**
* @brief  关闭切刀功能
* @par    说明
* 
* @param [in]            ullDevHdl                 设备句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_TurnOffCutter(DEV_HDL ullDevHdl);


/**
*
* @}
*/



/** @defgroup RFIDFuncs RFID功能
*  @brief 切纸、直传数据等
*
*  @{
*
*/


/**
* @brief  设置RFID读功率
* @par    说明
* 
* @param [in]            ullDevHdl                 设备句柄地址
* @param [in]            dbPower                   RFID读功率，单位：dBm
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RFID_SetReadPower(DEV_HDL ullDevHdl, double dbPower);


/**
* @brief  设置RFID写功率
* @par    说明
*
* @param [in]            ullDevHdl                 设备句柄地址
* @param [in]            dbPower                   RFID写功率，单位：dBm
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RFID_SetWritePower(DEV_HDL ullDevHdl, double dbPower);


/**
* @brief  获取RFID读功率
* @par    说明
*
* @param [in]            ullDevHdl                 设备句柄地址
* @param [out]           pdbPower                  用于获取RFID读功率的double变量的指针，单位：dBm
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RFID_GetReadPower(DEV_HDL ullDevHdl, double *pdbPower);


/**
* @brief  获取RFID写功率
* @par    说明
*
* @param [in]            ullDevHdl                 设备句柄地址
* @param [out]           pdbPower                  用于获取RFID写功率的double变量的指针，单位：dBm
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RFID_GetWritePower(DEV_HDL ullDevHdl, double *pdbPower);


/**
* @brief  设置RFID协议
* @par    说明
*
* @param [in]            ullDevHdl                 设备句柄地址
* @param [in]            nProto                    设置协议值
* @n  0：ISO14443A协议，（高频模块）
* @n  1：ISO15693协议，（高频模块）
* @n  5：ISO18000-6C协议，（超高频模块）
* @n  9：ISO18000-63协议，（国军标模块）
* @n  10：GB/T 29768协议，（国军标模块）
* @n  11：GJB 7377.1协议，（国军标模块）
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RFID_SetProto(DEV_HDL ullDevHdl, int nProto);


/**
* @brief  获取RFID协议
* @par    说明
*
* @param [in]            ullDevHdl                 设备句柄地址
* @param [out]           pProto					   返回协议值
* @n  0：ISO14443A协议，（高频模块）
* @n  1：ISO15693协议，（高频模块）
* @n  5：ISO18000-6C协议，（超高频模块）
* @n  9：ISO18000-63协议，（国军标模块）
* @n  10：GB/T 29768协议，（国军标模块）
* @n  11：GJB 7377.1协议，（国军标模块）
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RFID_GetProto(DEV_HDL ullDevHdl, int *pProto);


/**
* @brief  带RFID标签定位
* @par    说明
*
* @param [in]            ullDevHdl                 设备句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RFID_LocateLabel(DEV_HDL ullDevHdl);


/**
* @brief  读取TID、EPC、USER
* @par    说明
* 本接口函数适用于直接读取TID、EPC、USER而无需打印的情况
* @param [in]            ullDevHdl                 设备句柄地址
* @param [out]           pTid                      用于接收从RFID标签读回的TID数据的缓存区，返回数据的十六进制字符串；如不需要读取TID数据，则本参数传0即可
* @param [in,out] 		 pTidSize                  入参时表示pTid的缓存区大小，出参时表示实际pTid数据的十六进制字符串长度；如不需要读取TID数据，则本参数传0即可
* @param [out]           pEpc                      用于接收从RFID标签读回的EPC数据的缓存区,返回数据的十六进制字符串；如不需要读取EPC数据，则本参数传0即可
* @param [in,out] 		 pEpcSize                  入参时表示pEpc的缓存区大小，出参时表示实际pEpc数据的十六进制字符串长度；如不需要读取EPC数据，则本参数传0即可
* @param [out]           pUser                     用于接收从RFID标签读回的USER数据的缓存区，返回数据的十六进制字符串；如不需要读取USER数据，则本参数传0即可
* @param [in,out] 		 pUserSize                 入参时表示标签中USER数据的实际长度的两倍（比如：传参的pUser缓存区大小为8，则实际只读取4字节user数据），出参时表示实际pUser数据的十六进制字符串长度；\n如不需要读取USER数据，则本参数传0即可
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RFID_ReadData(DEV_HDL ullDevHdl, char *pTid, int *pTidSize, char *pEpc, int *pEpcSize, char *pUser, int *pUserSize);



/**
* @brief  修改RFID标签的访问密码
* @par    说明
* 打印前调用，对单张标签有效；
* 修改密码在打印时生效；
* @param [in]            ullDevHdl                 设备句柄地址
* @param [in] 			szOldPw						RFID标签的初始密码，为8位十六进制字符串
* @param [in]           szNewPw                     设置RFID标签的新密码，为8位十六进制字符串，注意不能全0
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RFID_ChangeAccessPassword(DEV_HDL ullDevHdl, const char* szOldPw, const char* szNewPw);



/**
* @brief  设置RFID标签的销毁密码
* @par    说明
* 打印前调用，对单张标签有效；
* 设置的密码在打印时生效；
* @param [in]           ullDevHdl                 设备句柄地址
* @param [in] 			szPw					  RFID标签的销毁密码，为8位十六进制字符串，注意不能全0
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RFID_SetDestructionPassword(DEV_HDL ullDevHdl, const char* szPw);


/**
* @brief  RFID锁定类型设置
* @par    说明
* 在打印前支持重复调用，例如：原先EPC区和USER区为永久锁定，然后设置USER区为临时锁定，这时EPC区永久锁定继续有效；
* 重复调用时，nTemporary以最后一次调用为准；
* 不调用此接口时默认为临时锁；
* @param [in]           ullDevHdl                 设备句柄地址
* @param [in] 			nRFIDArea				  RFID区域（或关系），1：EPC区，2：USER区，8：访问密码区，16：销毁密码区
* @param [in] 			nLockType				  0：永久锁，1：临时锁
* @param [in]           nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullDevHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次打印接口(PrintXXX)调用后，本设置项即被还原	
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RFID_LockTypeSetting(DEV_HDL ullDevHdl, int nRFIDArea, int nLockType, int nTemporary);



/**
* @brief  锁定特定RFID区域
* @par    说明
* 支持对EPC区，USER区，访问密码区，销毁密码区进行锁定；
* 在打印前调用，对单张标签有效；
* @param [in]           ullDevHdl                 设备句柄地址
* @param [in] 			nRFIDArea				  RFID区域（或关系），1：EPC区，2：USER区，8：访问密码区，16：销毁密码区
* @param [in] 			szPw					  RFID标签的密码，为8位十六进制字符串
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RFID_LockOperate(DEV_HDL ullDevHdl, int nRFIDArea, const char* szPw);



/**
* @brief  解锁特定RFID区域
* @par    说明
* 支持对EPC区，USER区，访问密码区，销毁密码区进行解锁；
* 在打印前调用，对单张标签有效；
* @param [in]           ullDevHdl                 设备句柄地址
* @param [in] 			nRFIDArea				  RFID区域（或关系），1：EPC区，2：USER区，8：访问密码区，16：销毁密码区
* @param [in] 			szPw					  RFID标签的密码，为8位十六进制字符串
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RFID_UnlockOperate(DEV_HDL ullDevHdl, int nRFIDArea, const char* szPw);



/**
* @brief  带密码写特定RFID区域
* @par    说明
* 在打印前调用，对单张标签有效；
* 不调用本接口则写入不带密码，这时如果已经修改了密码，则写入时会不成功；
* 若模板已经有密码字段，则将被替换；
* @param [in]           ullDevHdl                 设备句柄地址
* @param [in] 			nRFIDArea				  RFID区域（或关系），1：EPC区，2：USER区
* @param [in] 			szPw					  RFID标签的密码，为8位十六进制字符串，注意同一标签密码是相同的
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_RFID_SetPasswordWithWrite(DEV_HDL ullDevHdl, int nRFIDArea, const char* szPw);



/**
*
* @}
*/




/** @defgroup PdfPrinting pdf打印功能
*  @brief pdf打印
*
*  @{
*
*/


/**
* @brief  加载pdf数据
* @par    说明
* 
* @param [in]            nPdfDataType              pdf数据类型
* @n 1 - pdf数据为（含路径）文件名
* @n 2 - pdf数据为base64格式字符串
* @param [in]            szPdfData 	               pdf数据，字符编码：utf-8
* @param [in]            nPdfDataSize 	           表示szPdfData的字符串（不含"\0"）长度，单位：字节
* @param [out]           pPdfHdl                   pdf文件句柄的地址
* @param [out]           pPageCount                当前pdf文件的总页数
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LoadPdf(int nPdfDataType, const char *szPdfData, int nPdfDataSize, PDF_HDL *pPdfHdl, int *pPageCount);


/**
* @brief  打印pdf
* @par    说明
* szOutFile参数需调用了DSTP2x_SetPdfPrnMode且nPrnMode为1或2时，才会生成.png或.prn本地文件；\n
* 为了能使用RFID功能，DSTP2x_SetPdfPrnMode需设置0；\n
* 对于需要RFID同时具有写和读功能，需要先调用DSTP2x_SetPdfRFIDData, 并且设置nRfidReadType里的读取类型和分配szOutRFID内存；\n
* 对于需要RFID的只读功能，无需调用DSTP2x_SetPdfRFIDData接口，但需要分配szOutRFID的内存；\n
* 不需要RFID的读取功能，需要设置nRfidReadType和szOutRFID为0。
* @param [in]            ullDevHdl                 设备句柄地址
* @param [in]            ullPdfHdl                 由DSTP2x_LoadPdf函数返回的pdf文件句柄
* @param [in]            nPageNo 	               待打印pdf文件的页码
* @param [out]           szOutFile                 用于存放本次打印操作生成的（.prn或.png）（含路径的）本地数据文件名，建议预分配空间不小于1024字节；如不需要取得本次打印操作生成的本地数据文件名，本参数传入0即可
* @param [in,out] 		 pOutFileSize              入参时表示szOutFile的缓存区大小，出参时表示实际存入szOutFile的字符串长度；如szOutFile为0，本参数将被忽略
*												   当返回错误码为41943046时，表示pOutFileSize缓存区不足，根据此参返参大小重新申请缓存。
* @param [in]            nRfidReadType             打印当前页数据过程中是否读取及如何rfid数据
* @n 0 - 不读取
* @n 1 - 读取TID
* @n 2 - 读取EPC
* @n 4 - 读取USER
* @param [out]           szOutRFID                 用于存放打印过程中读取到的rfid数据的缓存区，请根据nRfidReadType（组合）类型决定其缓存区预分配空间大小；\n
												   读取的RFID数据在动态执行RFID后返回，以十六进制字符串表示；\n
*                                                  内容格式如："TID:82309360|EPC:0123456789|USER:abcdef"；\n
*                                                  如不需要取得打印过程中读取到的rfid数据，本参数传0即可
* @param [in,out] 		 pOutRFIDSize              入参时表示szOutRFID的缓存区大小，出参时表示实际存入szOutRFID的数据长度；如szOutRFID为0，本参数将被忽略
*												   当返回错误码为41943046时，表示pOutRFIDSize缓存区不足，根据此参返参大小重新申请缓存。
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_PrintPdf(DEV_HDL ullDevHdl, PDF_HDL ullPdfHdl, int nPageNo, char *szOutFile, int *pOutFileSize, int nRfidReadType, char *szOutRFID, int *pOutRFIDSize);


/**
* @brief  删除pdf句柄
* @par    说明
*
* @param [in]            ullPdfHdl                 由DSTP2x_LoadPdf函数返回的pdf文件句柄
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_DeletePdf(PDF_HDL ullPdfHdl);


/**
* @brief  设置pdf打印模式
* @par    说明
* 对当前句柄有效，如不调用本函数，则打印模式默认为0
* @param [in]            ullPdfHdl                 由DSTP2x_LoadPdf函数返回的pdf文件句柄
* @param [in]            nPrnMode                  打印模式；若不调用本函数，默认打印模式为：通过打印机打印
* @n 0 - 通过打印机打印
* @n 1 - 打印到.prn文件
* @n 2 - 生成png格式的效果预览图文件
* @n 3 - 生成预览图的Base64数据
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetPdfPrnMode(PDF_HDL ullPdfHdl, int nPrnMode);


/**
* @brief  设置DSTP2x_PrintPdf单次调用是否打印同步结果
* @par    说明
* 对当前句柄有效，如不调用本函数，则pdf单次打印将同步结果
* @param [in]            ullPdfHdl                 由DSTP2x_LoadPdf函数返回的pdf文件句柄
* @param [in]            nSyncType                 是否打印同步结果
* @n 0 - 不同步打印结果，只要当前页的打印数据发送完，本函数即返回；此时不支持DSTP2x_PrintPdf的RFID读操作
* @n 1 - 同步打印结果，当前页的打印数据发送完后，本函数内部持续监听打印状态，直至打印成功完成才返回；如遇打印机报错，函数立即返回
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetPdfPrnSyncType(PDF_HDL ullPdfHdl, int nSyncType);


/**
* @brief  设置DSTP2x_PrintPdf单次调用最大超时时间
* @par    说明
* 对当前句柄有效，如不调用本函数，则pdf单次打印最大超时时间默认为15000毫秒
* @param [in]            ullPdfHdl                 由DSTP2x_LoadPdf函数返回的pdf文件句柄
* @param [in]            nTimeout                  超时时间，单位：毫秒；当DSTP2x_PrintPdf单次调用为同步结果时才生效
* @n -1 - 表示如打印过程中无任何（软/硬件或通讯）出错情况下，DSTP2x_PrintPdf将无限期等待打印结束条件满足才返回
* @n >0 - 表示如打印过程中无任何（软/硬件或通讯）出错情况下，DSTP2x_PrintPdf将在等待打印结束条件满足的过程中同时检查是否整体耗时是否大于或等于nTimeout；
*         如是，则返回“操作执行超时”
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetPdfPrnTimeout(PDF_HDL ullPdfHdl, int nTimeout);


/**
* @brief  设置pdf打印过程中需要写入的rfid数据
* @par    说明
* 如不调用本函数，则打印过程中不进行rfid读/写
* @param [in]            ullPdfHdl                 由DSTP2x_LoadPdf函数返回的pdf文件句柄
* @param [in]            nPageNo                   待打印pdf文件的页码
* @param [in]            nRfidRgnType              需在打印过程中写入rfid数据的区域类型
* @n 1 - EPC区
* @n 2 - USER区
* @param [in]            nRfidDataFmt              需在打印过程中写入的rfid数据格式
* @n 1 - ASCII编码字符串
* @n 2 - 十六进制字符串
* @n 3 - 十六进制字节数据
* @param [in]            pData                     需在打印过程中写入的rfid数据
* @param [in]            nDataSize                 需在打印过程中写入的rfid数据长度，单位：字节；如nRfidDataFmt为1或者2，则本参数表示pData的实际字符串（不含"\0"）长度
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetPdfRFIDData(PDF_HDL ullPdfHdl, int nPageNo, int nRfidRgnType, int nRfidDataFmt, const char *pData, int nDataSize);


/**
* @brief  设置pdf目标打印尺寸
* @par    说明
* 对当前句柄有效
* @param [in]            ullPdfHdl                 由DSTP2x_LoadPdf函数返回的pdf文件句柄
* @param [in]            dbWidth                   打印宽度，单位：mm
* @param [in]            dbHeight                  打印高度，单位：mm
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetPdfPrnSize(PDF_HDL ullPdfHdl, double dbWidth, double dbHeight);


/**
* @brief  设置pdf目标打印旋转角度
* @par    说明
* 对当前句柄有效
* @param [in]            ullPdfHdl                 由DSTP2x_LoadPdf函数返回的pdf文件句柄
* @param [in]            nAngle                    旋转角度，范围[0, 90, 180, 270]
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetPdfPrnRotate(PDF_HDL ullPdfHdl, int nAngle);



/**
* @brief  设置pdf图像的半色调处理算法
* @par    说明：
* 对当前句柄有效
* @param [in]            ullPdfHdl                  由DSTP2x_LoadPdf函数返回的标签上下文句柄
* @param [in]            nAlgorithm                 图片算法
* @n 1 - 误差扩散
* @n 2 - 有序抖动算法
* @n 3 - 阈值运算算法（默认）
* @param [in]            nThreshold                 阈值，当nAlgorithm为3时生效，范围[0,255]
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetPdfHalftoneAlgo(PDF_HDL ullPdfHdl, int nAlgorithm, int nThreshold);


/**
*
* @}
*/



/** @defgroup LabelTemplatePrinting 标签模板打印功能
*  @brief 标签模板打印
*
*  @{
*
*/


/**
* @brief  加载预定义标签模板
* @par    说明
* szFileName参数必须是由SDK包的DSTP2xDemo.exe生成。
* @param [in]            szFile                预定义标签模板（含路径）文件名（字符编码：utf-8）或模板文件内存数据
* @param [out]           pLTHdl                    标签模板文件的句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LoadLabelTmpl(const char *szFile, LABEL_TEMP_HDL *pLTHdl);


/**
* @brief  打印标签模板
* @par    说明
*
* @param [in]            ullDevHdl                 设备句柄地址
* @param [in]            ullLTHdl                  由DSTP2x_LoadLabelTmpl函数返回的标签模板文件句柄
* @param [out]           szOutFile                 用于存放本次打印操作生成的（.prn或.png）（含路径的）本地数据文件名，建议预分配空间不小于256字节；如不需要取得本次打印操作生成的本地数据文件名，本参数传入0即可
* @param [in,out] 		 pOutFileSize              入参时表示szOutFile的缓存区大小，出参时表示实际存入szOutFile的字符串长度；如szOutFile为0，本参数将被忽略
*												   当返回错误码为41943046时，表示pOutFileSize缓存区不足，根据此参返参大小重新申请缓存。
* @param [out]           szOutRFID                 用于存放打印过程中读取到的rfid数据的缓存区，请根据nRfidReadType（组合）类型决定其缓存区预分配空间大小；
*                                                  内容格式如："TID:82309360|EPC:0123456789|USER:abcdef"，RFID内容数据以十六进制字符串表示；
*                                                  如不需要取得打印过程中读取到的rfid数据，本参数传0即可
* @param [in,out] 		 pOutRFIDSize              入参时表示szOutRFID的缓存区大小，出参时表示实际存入szOutRFID的数据长度；如szOutRFID为0，本参数将被忽略
*												   当返回错误码为41943046时，表示pOutRFIDSize缓存区不足，根据此参返参大小重新申请缓存。
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_PrintTmpl(DEV_HDL ullDevHdl, LABEL_TEMP_HDL ullLTHdl, char *szOutFile, int *pOutFileSize, char *szOutRFID, int *pOutRFIDSize);


/**
* @brief  删除标签模板文件句柄
* @par    说明
*
* @param [in]            ullLTHdl                   由DSTP2x_LoadLabelTmpl函数返回的标签模板文件句柄
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_DeleteTmpl(LABEL_TEMP_HDL ullLTHdl);


/**
* @brief  设置标签模板的打印模式
* @par    说明
* 如不调用本函数，则打印模式默认为0
* @param [in]            ullLTHdl                  由DSTP2x_LoadLabelTmpl函数返回的标签模板文件句柄
* @param [in]            nPrnMode                  打印模式；若不调用本函数，默认打印模式为：通过打印机打印
* @n 0 - 通过打印机打印
* @n 1 - 打印到.prn文件
* @n 2 - 生成png格式的效果预览图文件
* @n 3 - 生成预览图的Base64数据
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetTmplPrnMode(LABEL_TEMP_HDL ullLTHdl, int nPrnMode);



/**
* @brief  设置DSTP2x_PrintTmpl单次调用是否打印同步结果
* @par    说明
* 如不调用本函数，则模板单次打印将同步结果
* @param [in]            ullLTHdl                  由DSTP2x_LoadLabelTmpl函数返回的标签模板文件句柄
* @param [in]            nSyncType                 是否打印同步结果
* @n 0 - 不同步打印结果，只要当前页的打印数据发送完，本函数即返回；此时不支持DSTP2x_PrintTmpl的RFID读操作
* @n 1 - 同步打印结果，当前页的打印数据发送完后，本函数内部持续监听打印状态，直至打印成功完成才返回；如遇打印机报错，函数立即返回
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetTmplPrnSyncType(LABEL_TEMP_HDL ullLTHdl, int nSyncType);


/**
* @brief  设置DSTP2x_PrintTmpl单次调用最大超时时间
* @par    说明
* 如不调用本函数，则模板单次打印最大超时时间默认为15000毫秒
* @param [in]            ullLTHdl                  由DSTP2x_LoadLabelTmpl函数返回的标签模板文件句柄
* @param [in]            nTimeout                  超时时间，单位：毫秒；当DSTP2x_PrintTmpl单次调用为同步结果时才生效
* @n -1 - 表示如打印过程中无任何（软/硬件或通讯）出错情况下，DSTP2x_PrintTmpl将无限期等待打印结束条件满足才返回
* @n >0 - 表示如打印过程中无任何（软/硬件或通讯）出错情况下，DSTP2x_PrintTmpl将在等待打印结束条件满足的过程中同时检查是否整体耗时是否大于或等于nTimeout；
*         如是，则返回“操作执行超时”
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetTmplPrnTimeout(LABEL_TEMP_HDL ullLTHdl, int nTimeout);


/**
* @brief  为标签模板内指定ID的元素设置实际的rfid写入替代数据
* @par    说明
* 如不调用本函数为标签模板某些已创建ID的元素设置真实替代数据，后续打印过程中模板里已创建ID的原始则使用预设值进行rfid写入
* @param [in]            ullLTHdl                  由DSTP2x_LoadLabelTmpl函数返回的标签模板文件句柄
* @param [in]            szElemID                  表示标签模板中需要使用实际数据进行rfid写入的特定元素的ID
* @param [in]            pActualData               实际需要在打印过程中写入的rfid数据
* @param [in]            nActualDataSize           需在打印过程中写入的rfid数据长度，单位：字节；
*                                                  如pActualData为字符串，则本参数表示pActualData的实际字符串（不含"\0"）长度
*                                                  如pActualData为十六进制字节数据，则本参数表示pActualData实际应写入数据长度
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetTmplRFIDData(LABEL_TEMP_HDL ullLTHdl, const char *szElemID, const char *pActualData, int nActualDataSize);


/**
* @brief  为标签模板内指定ID的元素设置实际的打印替代数据
* @par    说明
* 如不调用本函数为标签模板某些已创建ID的元素设置真实替代数据，后续打印过程中模板里已创建ID的原始则使用预设值进行打印
* @param [in]            ullLTHdl                  由DSTP2x_LoadLabelTmpl函数返回的标签模板文件句柄
* @param [in]            szElemID                  表示标签模板中需要使用实际数据进行打印的特定元素的ID
* @param [in]            szActualData              实际需要打印的数据（utf-8）
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetTmplPrnData(LABEL_TEMP_HDL ullLTHdl, const char *szElemID, const char *szActualData);



/**
* @brief  为标签模板内指定ID的元素，根据存在的键值设置替代的属性值
* @par    说明
* 如不调用本函数为标签模板某些已创建ID的元素设置真实替代数据，后续打印过程中模板里已创建ID的原始则使用预设值进行打印
* @param [in]            ullLTHdl                  由DSTP2x_LoadLabelTmpl函数返回的标签模板文件句柄
* @param [in]            szElemID                  表示标签模板中需要使用实际数据进行打印的特定元素的ID
* @param [in]            szKey					   数据值所归属的索引键
* @param [in]            szValue				   实际需要打印的数据值（utf-8）
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetTmplValByKey(LABEL_TEMP_HDL ullLTHdl, const char *szElemID, const char *szKey, const char *szValue);


/**
* @brief  返回当前标签模板的模板文件(.dlt)
* @par    说明
* 如果之前通过DSTP2x_SetTmplxxx接口修改了标签模板一些内容或属性数据，然后想获取修改后的dlt模板文件，则调用此接口。\n
* @param [in]            ullLTHdl               由DSTP2x_LoadLabelTmpl函数返回的标签模板文件句柄
* @param [out]           pFileName              如果成功，返回模板文件路径
* @param [in,out]        pFileNameLen			入参时表示pFileName的缓存区大小，出参时表示实际存入pFileName的数据长度
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_GetBackTmpl(LABEL_TEMP_HDL ullLTHdl, char * pFileName, int *pFileNameLen);



/**
* @brief  获取当前标签模板所有ID值
* @par    说明
*
* @param [in]            ullLTHdl               由DSTP2x_LoadLabelTmpl函数返回的标签模板文件句柄
* @param [in]            cInterval              设置返回所有ID值之间的间隔字符
* @param [in]            nType					根据类型获取ID值，0: 全部ID值, 1: 可动态修改的ID值, 2: 不可动态修改的ID值
* @param [out]           pIDValues              如果成功，返回所有ID值，值之间以cInterval作间隔
* @param [in,out]        pIDValuesLen			入参时表示pIDValues的缓存区大小，出参时表示实际存入pIDValues的数据长度
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_GetTmplAllIDValues(LABEL_TEMP_HDL ullLTHdl, char cInterval, int nType, char *pIDValues, int *pIDValuesLen);

/**
*
* @}
*/



/** @defgroup LabelDrawPrinting 标签绘图打印功能
*  @brief 标签绘图打印
*
*  @{
*
*/


/**
* @brief  创建标签上下文
* @par    说明
* 
* @param [in]            dbWidth                   目标待打印标签宽度，单位：mm
* @param [in]            dbHeight                  目标待打印标签高度，单位：mm
* @param [out]           pLCHdl                    标签上下文的句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_CreateLabelContext(double dbWidth, double dbHeight, LC_HDL *pLCHdl);


/**
* @brief  在指定的标签上下文绘制文本
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            dbX                       文本内容块相对于标签左上角的横坐标，单位：mm（毫米）
* @param [in]            dbY                       文本内容块相对于标签左上角的纵坐标，单位：mm（毫米）
* @param [in]            dbW                       文本内容块的宽度，为非负浮点数，若为0则表示忽略此参数，单位：mm（毫米）
* @param [in]            dbH                       文本内容块的高度，为非负浮点数，若为0则表示忽略此参数，单位：mm（毫米）
* @param [in]            szText                    需要绘制在绘图上下文的文本内容，字符编码：utf-8。
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Lbl_DrawText(LC_HDL ullLcHdl, double dbX, double dbY, double dbW, double dbH, const char *szText);


/**
* @brief  在指定的标签上下文绘制图像
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            dbX                       图像内容块相对于标签左上角的横坐标，单位：mm（毫米）
* @param [in]            dbY                       图像内容块相对于标签左上角的纵坐标，单位：mm（毫米）
* @param [in]            dbW                       图像内容块的宽度，为非负浮点数，若为0则表示忽略此参数，单位：mm（毫米）
* @param [in]            dbH                       图像内容块的高度，为非负浮点数，若为0则表示忽略此参数，单位：mm（毫米）
* @param [in]            dbScale                   相对于原图尺寸的缩放系数，为非负浮点数，若为0则表示忽略此参数，取值范围必须1到3之间
* @param [in]            nImgDataType              图像数据类型
* @n 0 - 本地图片文件
* @n 1 - 图片内存数据
* @n 2 - base64格式图片数据
* @param [in]            szImage                   需要绘制在绘图上下文的图像数据。
* @param [in]            unImgDataSize             当nImgDataType为1和2时，unImgDataSize的大小为指向szImage的实际内存大小\n 当nImgDataType为0时，unImgDataSize的大小为指向szImage的长度大小。
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Lbl_DrawImage(LC_HDL ullLcHdl, double dbX, double dbY, double dbW, double dbH, double dbScale, int nImgDataType, const char *szImage, unsigned int unImgDataSize);


/**
* @brief  在指定的标签上下文绘制条码
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            dbX                       图像内容块相对于标签左上角的横坐标，单位：mm（毫米）
* @param [in]            dbY                       图像内容块相对于标签左上角的纵坐标，单位：mm（毫米）
* @param [in]            dbW                       图像内容块的宽度，为非负浮点数，单位：mm（毫米）
* @param [in]            dbH                       图像内容块的高度，为非负浮点数，单位：mm（毫米）
* @param [in]            nCodeType                 生成条码的编码类型
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
* @param [in]            szData                    需要绘制在绘图上下文的条码数据。
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Lbl_DrawBarCode(LC_HDL ullLcHdl, double dbX, double dbY, double dbW, double dbH, int nCodeType, const char *szData);


/**
* @brief  在指定的标签上下文绘制线段
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            dbStartX                  线段相对于标签左上角为原点的起点横坐标，单位：mm（毫米）
* @param [in]            dbStartY                  线段相对于标签左上角为原点的起点纵坐标，单位：mm（毫米）
* @param [in]            dbEndX                    线段相对于标签左上角为原点的终点横坐标，单位：mm（毫米）
* @param [in]            dbEndY                    线段相对于标签左上角为原点的终点纵坐标，单位：mm（毫米）
* @param [in]            nLineWidth                线段宽度，单位：pixel（像素）
* @param [in]            nLineType                 线段类型，0:实线，1:虚线，2：点线，3：点划线，4：双点划线
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Lbl_DrawLine(LC_HDL ullLcHdl, double dbStartX, double dbStartY, double dbEndX, double dbEndY, int nLineWidth, int nLineType);



/**
* @brief  在指定的标签上下文绘制椭圆
* @par    说明：
*
* @param [in]            ullLcHdl               由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            dbX					椭圆左上角横坐标，单位：mm（毫米）
* @param [in]            dbY					椭圆左上角纵坐标，单位：mm（毫米）
* @param [in]            dbW					椭圆的宽度，单位：mm（毫米）
* @param [in]            dbH					椭圆的高度，单位：mm（毫米）
* @param [in]            nLineWidth				椭圆的线宽度，单位：pixel（像素）
* @param [in]            nLineType				椭圆的线类型，0:实线，1:虚线
* @param [in]            nIsFill				是否填充，1:是，0:否
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Lbl_DrawEllipse(LC_HDL ullLcHdl, double dbX, double dbY, double dbW, double dbH, int nLineWidth, int nLineType, int nIsFill);



/**
* @brief  在指定的标签上下文绘制矩形
* @par    说明：
*
* @param [in]            ullLcHdl               由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            dbX					矩形左上角横坐标，单位：mm（毫米）
* @param [in]            dbY					矩形左上角纵坐标，单位：mm（毫米）
* @param [in]            dbW					矩形的宽度，单位：mm（毫米）
* @param [in]            dbH					矩形的高度，单位：mm（毫米）
* @param [in]            nLineWidth				矩形的线宽度，单位：pixel（像素）
* @param [in]            nLineType				矩形的线类型，0:实线，1:虚线
* @param [in]            nIsFill				是否填充，1:是，0:否
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Lbl_DrawRectangle(LC_HDL ullLcHdl, double dbX, double dbY, double dbW, double dbH, int nLineWidth, int nLineType, int nIsFill);


/**
* @brief  打印标签模板
* @par    说明
* szOutFile参数需调用了DSTP2x_SetLcPrnMode且nPrnMode为1或2时，才会生成.png或.prn本地文件；\n
* 为了能使用RFID功能，DSTP2x_SetLcPrnMode需设置0；\n
* 对于需要RFID同时具有写和读功能，需要先调用DSTP2x_LcRfid_SetData, 并且设置nRfidReadType里的读取类型和分配szOutRFID内存；\n
* 对于需要RFID的只读功能，无需调用DSTP2x_LcRfid_SetData接口，但需要分配szOutRFID的内存；\n
* 不需要RFID的读取功能，需要设置nRfidReadType和szOutRFID为0。
* @param [in]            ullDevHdl                 设备句柄地址
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [out]           szOutFile                 用于存放本次打印操作生成的（.prn或.png）（含路径的）本地数据文件名，建议预分配空间不小于256字节；如不需要取得本次打印操作生成的本地数据文件名，本参数传入0即可
* @param [in,out] 		 pOutFileSize              入参时表示szOutFile的缓存区大小，出参时表示实际存入szOutFile的字符串长度；如szOutFile为0，本参数将被忽略
*												   当返回错误码为41943046时，表示szOutFile缓存区不足，根据此参返参大小重新申请缓存。
* @param [in]            nRfidReadType             打印当前页数据过程中是否读取及如何rfid数据
* @n 0 - 不读取
* @n 1 - 读取TID
* @n 2 - 读取EPC
* @n 4 - 读取USER
* @param [out]           szOutRFID                 用于存放打印过程中读取到的rfid数据的缓存区，请根据nRfidReadType（组合）类型决定其缓存区预分配空间大小；\n
*												   读取的RFID数据在动态执行RFID后返回，以十六进制字符串表示；\n
*                                                  内容格式如："TID:82309360|EPC:0123456789|USER:abcdef"；\n
*                                                  如不需要取得打印过程中读取到的rfid数据，本参数传0即可
* @param [in,out] 		 pOutRFIDSize              入参时表示szOutRFID的缓存区大小，出参时表示实际存入szOutRFID的数据长度；如szOutRFID为0，本参数将被忽略
*												   当返回错误码为41943046时，表示pOutRFIDSize缓存区不足，根据此参返参大小重新申请缓存。
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_PrintLc(DEV_HDL ullDevHdl, LC_HDL ullLcHdl, char *szOutFile, int *pOutFileSize, int nRfidReadType, char *szOutRFID, int *pOutRFIDSize);


/**
* @brief  删除标签上下文句柄
* @par    说明
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_DeleteLabelContext(LC_HDL ullLcHdl);


/**
* @brief  设置标签上下文的打印模式
* @par    说明
* 如不调用本函数，则打印模式默认为0
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nPrnMode                  打印模式；若不调用本函数，默认打印模式为：通过打印机打印
* @n 0 - 通过打印机打印
* @n 1 - 打印到.prn文件
* @n 2 - 生成png格式的效果预览图文件
* @n 3 - 生成预览图的Base64数据
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetLcPrnMode(LC_HDL ullLcHdl, int nPrnMode);

/**
* @brief  设置标签上下文的整张画布旋转角度
* @par    说明
* 如不调用本函数，则角度默认为0
* @param [in]            ullLcHdl                 由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nAngle                   旋转角度，范围[0, 90, 180, 270]
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetLcPrnRotate(LC_HDL ullLcHdl, int nAngle);

/**
* @brief  设置DSTP2x_PrintLc单次调用是否打印同步结果
* @par    说明
* 如不调用本函数，则模板单次打印将同步结果
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nSyncType                 是否打印同步结果
* @n 0 - 不同步打印结果，只要当前页的打印数据发送完，本函数即返回；此时不支持DSTP2x_PrintLc的RFID读操作
* @n 1 - 同步打印结果，当前页的打印数据发送完后，本函数内部持续监听打印状态，直至打印成功完成才返回；如遇打印机报错，函数立即返回
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetLcPrnSyncType(LC_HDL ullLcHdl, int nSyncType);


/**
* @brief  设置DSTP2x_PrintLc单次调用最大超时时间
* @par    说明
* 如不调用本函数，则模板单次打印最大超时时间默认为15000毫秒
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTimeout                  超时时间，单位：毫秒；当DSTP2x_PrintLc单次调用为同步结果时才生效
* @n -1 - 表示如打印过程中无任何（软/硬件或通讯）出错情况下，DSTP2x_PrintTmpl将无限期等待打印结束条件满足才返回
* @n >0 - 表示如打印过程中无任何（软/硬件或通讯）出错情况下，DSTP2x_PrintTmpl将在等待打印结束条件满足的过程中同时检查是否整体耗时是否大于或等于nTimeout；
*         如是，则返回“操作执行超时”
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_SetLcPrnTimeout(LC_HDL ullLcHdl, int nTimeout);

	
/**
* @brief  标签上下文绘图设置-设置待绘制文本内容的字体名称
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawText或DSTP2x_Tbl_DrawText调用后，本设置项即被还原
* @param [in]            szFontName                字体名称，字符编码：utf-8
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetTextFontName(LC_HDL ullLcHdl, int nTemporary, const char *szFontName);


/**
* @brief  标签上下文绘图设置-设置待绘制文本内容的字体大小
* @par    说明：
*
* @param [in]            ullLcHdl                   由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_DrawText调用后，本设置项即被还原
* @param [in]            dbFontSize                字体大小，单位：磅
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetTextFontSize(LC_HDL ullLcHdl, int nTemporary, double dbFontSize);


/**
* @brief  标签上下文绘图设置-设置待绘制文本是否加粗
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawText或DSTP2x_Tbl_DrawText调用后，本设置项即被还原
* @param [in]            nIsBold                   是否加粗，合法取值：0和1；设置[2,5]时为加粗程度
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetTextBold(LC_HDL ullLcHdl, int nTemporary, int nIsBold);


/**
* @brief  标签上下文绘图设置-设置待绘制文本水平对齐方式
* @par    说明
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawText或DSTP2x_Tbl_DrawText调用后，本设置项即被还原
* @param [in]            dbX                       对齐线的横坐标
* @param [in]            nAlign                    对齐方式
* @n 0 - 无对齐特性
* @n 1 - 居左对齐
* @n 2 - 居中对齐
* @n 3 - 居右对齐
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetTextHAlign(LC_HDL ullLcHdl, int nTemporary, double dbX, int nAlign);


/**
* @brief  标签上下文绘图设置-设置待绘制文本垂直对齐方式
* @par    说明
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawText或DSTP2x_Tbl_DrawText调用后，本设置项即被还原
* @param [in]            dbY                       对齐线的纵坐标
* @param [in]            nAlign                    对齐方式
* @n 0 - 无对齐特性
* @n 1 - 顶端对齐
* @n 2 - 居中对齐
* @n 3 - 底端对齐
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetTextVAlign(LC_HDL ullLcHdl, int nTemporary, double dbY, int nAlign);


/**
* @brief  标签上下文绘图设置-设置待绘制文本是否斜体
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawText或DSTP2x_Tbl_DrawText调用后，本设置项即被还原
* @param [in]            nIsItalic                 是否斜体，取值范围：[0,1]
* @n 0 - 不使用斜体
* @n 1 - 使用斜体
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetTextItalic(LC_HDL ullLcHdl, int nTemporary, int nIsItalic);


/**
* @brief  标签上下文绘图设置-设置待绘制文本是否自动换行
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawText或DSTP2x_Tbl_DrawText调用后，本设置项即被还原
* @param [in]            nIsAutoLineFeed           是否自动换行，取值范围：[0,1]
* @n 0 - 不自动换行
* @n 1 - 自动换行
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetTextAutoLineFeed(LC_HDL ullLcHdl, int nTemporary, int nIsAutoLineFeed);


/**
* @brief  标签上下文绘图设置-设置待绘制文本行间距
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawText或DSTP2x_Tbl_DrawText调用后，本设置项即被还原
* @param [in]            dSpacing                  行间距，单位：磅
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetTextLineSpacing(LC_HDL ullLcHdl, int nTemporary, double dSpacing);


/**
* @brief  标签上下文绘图设置-设置待绘制文本字间距
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawText或DSTP2x_Tbl_DrawText调用后，本设置项即被还原
* @param [in]            dSpacing                  字间距，单位：磅
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetTextCharSpacing(LC_HDL ullLcHdl, int nTemporary, double dSpacing);


/**
* @brief  标签上下文绘图设置-设置待绘制文本旋转参数
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawText或DSTP2x_Tbl_DrawText调用后，本设置项即被还原
* @param [in]            nAngle                    旋转角度，范围[-360,360]
* @param [in]            nAnchorPoint              设置旋转基准中心
* @n 0 - 左上角
* @n 1 - 左边中间点
* @n 2 - 左下角
* @n 3 - 中心点
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetTextRotation(LC_HDL ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);


/**
* @brief  标签上下文绘图设置-设置待绘制图像旋转参数
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawImage或DSTP2x_Tbl_DrawImage调用后，本设置项即被还原
* @param [in]            nAngle                    旋转角度，范围[-360,360]
* @param [in]            nAnchorPoint              设置旋转基准中心
* @n 0 - 左上角
* @n 1 - 左边中间点
* @n 2 - 左下角
* @n 3 - 中心点
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetImageRotation(LC_HDL ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);


/**
* @brief  标签上下文绘图设置-设置待绘制矩形旋转参数
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawRectangle或DSTP2x_Tbl_DrawRectangle调用后，本设置项即被还原
* @param [in]            nAngle                    旋转角度，范围[-360,360]
* @param [in]            nAnchorPoint              设置旋转基准中心
* @n 0 - 左上角
* @n 1 - 左边中间点
* @n 2 - 左下角
* @n 3 - 中心点
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetRectangleRotation(LC_HDL ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);


/**
* @brief  标签上下文绘图设置-设置待绘制椭圆旋转参数
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawEllipse或DSTP2x_Tbl_DrawEllipse调用后，本设置项即被还原
* @param [in]            nAngle                    旋转角度，范围[-360,360]
* @param [in]            nAnchorPoint              设置旋转基准中心
* @n 0 - 左上角
* @n 1 - 左边中间点
* @n 2 - 左下角
* @n 3 - 中心点
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetEllipseRotation(LC_HDL ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);


/**
* @brief  标签上下文绘图设置-设置待绘制图像的半色调处理算法
* @par    说明：
*
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawImage或DSTP2x_Tbl_DrawImage调用后，本设置项即被还原
* @param [in]            nAlgorithm                图片算法
* @n 0 - 不做算法（默认）
* @n 1 - 误差扩散
* @n 2 - 有序抖动算法
* @n 3 - 阈值运算算法
* @param [in]            nThreshold                阈值，当nAlgorithm为3时生效，范围[0,255]
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetImageHalftoneAlgo(LC_HDL ullLcHdl, int nTemporary, int nAlgorithm, int nThreshold);



/**
* @brief  标签上下文绘图设置-设置待绘制二维码纠错级别
* @par    说明：
* 本设置适用于PDC417、MicroPDF417、QRCode等二维条码类型
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawBarCode或DSTP2x_Tbl_DrawBarCode调用后，本设置项即被还原
* @param [in]            nErrorCorrectLevel        纠错级别，具体取值范围需根据DSTP2x_DrawCode函数的nCodeType而定
*                                                  当nCodeType为QRCode时，nErrorCorrectLevel参数取值范围为[1,4]，不设置时默认没有纠错级别
*                                                  当nCodeType为PDF417时，nErrorCorrectLevel参数取值范围为[0,8]，不设置时默认纠错级别为2
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetBarCodeEcLvl(LC_HDL ullLcHdl, int nTemporary, int nErrorCorrectLevel);


/**
* @brief  标签上下文绘图设置-设置待绘制一维码是否打印注释行
* @par    说明：
* 本设置适用于CODE39、CODE128、CODE93、UPC-A、UPC-E、EAN-8、EAN-13、EAN-14等多种一维条码类型
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawBarCode或DSTP2x_Tbl_DrawBarCode调用后，本设置项即被还原
* @param [in]            nExplanation              条码是否生成注释
* @n 0 - 不生成注释
* @n 1 - 生成注释
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetBarCodeExpl(LC_HDL ullLcHdl, int nTemporary, int nExplanation);


/**
* @brief  标签上下文绘图设置-设置待绘制一维码和二维码的旋转参数
* @par    说明：
* 本设置适用于CODE39、CODE128、CODE93、UPC-A、UPC-E、EAN-8、EAN-13、EAN-14等多种一维条码类型
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nTemporary                本设置项是否为临时性的
* @n 0 - 持久性的，直至ullLcHdl失效，除非再次被修改
* @n 1 - 临时性的，随后一次DSTP2x_Lbl_DrawBarCode或DSTP2x_Tbl_DrawBarCode调用后，本设置项即被还原
* @param [in]            nAngle                    旋转角度，范围[-360,360]
* @param [in]            nAnchorPoint              设置旋转基准中心
* @n 0 - 左上角
* @n 1 - 左边中间点
* @n 2 - 左下角
* @n 3 - 中心点
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcDraw_SetBarCodeRotation(LC_HDL ullLcHdl, int nTemporary, int nAngle, int nAnchorPoint);


/**
* @brief  创建表格
* @par    说明
* 1. 若函数执行成功，新建的表格句柄则由pTblHdl返回；
* 2. 表格一经创建，其行、列数均不可更改
* 3. 表格支持修改表格宽度、表格高度、列宽、行高，合并/还原单元格，在单元格内绘制文本、一维二维条码、图片等操作
* 4. 创建后的表格的格名排列比如3x2，将以以下形式表示：\n
*  0-0 0-1 0-2\n 1-0 1-1 1-2
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            dbX                       表格左上角横坐标，单位：mm（毫米）
* @param [in]            dbY                       表格左上角纵坐标，单位：mm（毫米）
* @param [in]            dbW                       表格的宽度，为非负浮点数，若为0则表示忽略此参数，单位：mm（毫米）
* @param [in]            dbH                       表格的高度，为非负浮点数，若为0则表示忽略此参数，单位：mm（毫米）
* @param [in]            nRowCount                 待创建表格的行数
* @param [in]            nColCount                 待创建表格的列数
* @param [in]            nLineWidth                待创建表格的框线的线条宽度，单位：dot（点），取值范围：[1,50]
* @param [out]           pTblHdl                   表格的句柄地址
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_CreateTable(LC_HDL ullLcHdl, double dbX, double dbY, double dbW, double dbH, int nRowCount, int nColCount, int nLineWidth, TABLE_HDL *pTblHdl);


/**
* @brief  通过移动列的边界线以更改表格的列宽
* @par    说明
* 1. 列的边界线数比列数多1
* 2. 列的边界线索引从左到右依次为0、1、2、3...
* 3. 因表格起始位置是既定的，因此（索引值为0的）最左侧列边界线不可进行左、右移动
* 3. 左、右移动最右侧的列边界线会直接改变表格宽度，左、右移动介于最左侧和最右侧间的边界线时，则会且仅会改变此列边界线两侧的列宽，呈此消彼长的关系。
* @param [in]            ullTblHdl                 由DSTP2x_CreateTable函数返回的表格句柄
* @param [in]            nColSepLineIdx            列的边界线索引，取值范围[1,n]，n等于列数
* @param [in]            nMoveDir                  边界线的移动方向
* @n 1 - 左移
* @n 2 - 右移
* @param [in]            dbStep                    移动边界线的步进值，单位：mm（毫米），精度：0.01mm
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Tbl_MoveColBoundary(TABLE_HDL ullTblHdl, int nColSepLineIdx, int nMoveDir, double dbStep);


/**
* @brief  通过移动行的边界线以更改表格的行高
* @par    说明
* 1. 行的边界线数比行数多1
* 2. 行的边界线索引从上到下依次为0、1、2、3...
* 3. 因表格起始位置是既定的，因此（索引值为0的）最顶端的行边界线不可进行上、下移动
* 4. 上、下移动最底端的列边界线会直接改变表格宽度，上、下移动介于最顶端和最底端间的边界线时，则会且仅会改变此行边界线两侧的行高，呈此消彼长的关系。
* @param [in]            ullTblHdl                 由DSTP2x_CreateTable函数返回的表格句柄
* @param [in]            nRowSepLineIdx            行的边界线索引，取值范围[1,n]，n等于行数
* @param [in]            nMoveDir                  边界线的移动方向
* @n 1 - 上移
* @n 2 - 下移
* @param [in]            dbStep                    移动边界线的步进值，单位：mm（毫米），精度：0.01mm
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Tbl_MoveRowBoundary(TABLE_HDL ullTblHdl, int nRowSepLineIdx, int nMoveDir, double dbStep);


/**
* @brief  合并单元格
* @par    说明
* 
* @param [in]            ullTblHdl                 由DSTP2x_CreateTable函数返回的表格句柄
* @param [in]            nRowBegin                 待合并单元格的起始行
* @param [in]            nRowEnd                   待合并单元格的结束行
* @param [in]            nColBegin                 待合并单元格的起始列
* @param [in]            nColEnd                   待合并单元格的结束列
* @param [out] 		     szMergedGridName          合并后的新单元格的名字，字符编码：utf-8，例如："Merged-0"，建议分配不小于32字节的空间
* @param [in,out]  	     pMergedGridNameSize       返回信息的长度，入参数为szMergedGridName的内存大小，出参数时表示实际写入szMergedGridName内存的长度
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Tbl_MergeGrids(TABLE_HDL ullTblHdl, int nRowBegin, int nRowEnd, int nColBegin, int nColEnd, char *szMergedGridName, int *pMergedGridNameSize);


/**
* @brief  还原（已合并的）单元格
* @par    说明
*
* @param [in]            ullTblHdl                 由DSTP2x_CreateTable函数返回的表格句柄
* @param [out] 		     szMergedGridName          由DSTP2x_Tbl_MergeGrids函数返回的合并后的新单元格的名字
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Tbl_RevertMergedGrid(TABLE_HDL ullTblHdl, const char *szMergedGridName);


/**
* @brief  在表格指定单元格上绘制文本
* @par    说明
*
* @param [in]            ullTblHdl                 由DSTP2x_CreateTable函数返回的表格句柄
* @param [out] 		     szGridName                单元格的名字，字符编码：utf-8；例如：基本单元格为"0-0"、"0-1"、"1-0"、"1-1"等；合并后的单元格为"Merged-0"、"Merged-1"等
* @param [in]            dbX                       文本内容块左上角相对于单元格左上角的横坐标，单位：mm（毫米）
* @param [in]            dbY                       文本内容块左上角相对于单元格左上角的纵坐标，单位：mm（毫米）
* @param [in]            dbW                       文本内容块的宽度，为非负浮点数，若为0则表示忽略此参数，单位：mm（毫米）
* @param [in]            dbH                       文本内容块的高度，为非负浮点数，若为0则表示忽略此参数，单位：mm（毫米）
* @param [in]            szText                    需要绘制在绘图上下文的文本内容，字符编码：utf-8。
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Tbl_DrawText(TABLE_HDL ullTblHdl, const char *szGridName, double dbX, double dbY, double dbW, double dbH, const char *szText);


/**
* @brief  在表格指定单元格上绘制一维、二维条码
* @par    说明
*
* @param [in]            ullTblHdl                 由DSTP2x_CreateTable函数返回的表格句柄
* @param [out] 		     szGridName                单元格的名字，字符编码：utf-8；例如：基本单元格为"0-0"、"0-1"、"1-0"、"1-1"等；合并后的单元格为"Merged-0"、"Merged-1"等
* @param [in]            dbX                       文本内容块左上角相对于单元格左上角的横坐标，单位：mm（毫米）
* @param [in]            dbY                       文本内容块左上角相对于单元格左上角的纵坐标，单位：mm（毫米）
* @param [in]            dbW                       文本内容块的宽度，为非负浮点数，若为0则表示忽略此参数，单位：mm（毫米）
* @param [in]            dbH                       文本内容块的高度，为非负浮点数，若为0则表示忽略此参数，单位：mm（毫米）
* @param [in]            nCodeType                 生成条码的编码类型
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
* @param [in]            szData                    需要绘制在绘图上下文的条码数据。
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Tbl_DrawBarCode(TABLE_HDL ullTblHdl, const char *szGridName, double dbX, double dbY, double dbW, double dbH, int nCodeType, const char *szData);


/**
* @brief  在表格指定单元格上绘制图像
* @par    说明
*
* @param [in]            ullTblHdl                 由DSTP2x_CreateTable函数返回的表格句柄
* @param [out] 		     szGridName                单元格的名字，字符编码：utf-8；例如：基本单元格为"0-0"、"0-1"、"1-0"、"1-1"等；合并后的单元格为"Merged-0"、"Merged-1"等
* @param [in]            dbX                       文本内容块左上角相对于单元格左上角的横坐标，单位：mm（毫米）
* @param [in]            dbY                       文本内容块左上角相对于单元格左上角的纵坐标，单位：mm（毫米）
* @param [in]            dbW                       文本内容块的宽度，为非负浮点数，若为0则表示忽略此参数，单位：mm（毫米）
* @param [in]            dbH                       文本内容块的高度，为非负浮点数，若为0则表示忽略此参数，单位：mm（毫米）
* @param [in]            dbScale                   相对于原图尺寸的缩放系数，为非负浮点数，若为0则表示忽略此参数，取值范围必须1到3之间
* @param [in]            nImgDataType              图像数据类型
* @n 0 - 本地图片文件
* @n 1 - 图片内存数据
* @n 2 - base64格式图片数据
* @param [in]            szImage                   需要绘制在绘图上下文的图像数据。
* @param [in]            unImgDataSize             当nImgDataType为1和2时，unImgDataSize的大小为指向szImage的实际内存大小\n 当nImgDataType为0时，unImgDataSize的大小为指向szImage的长度大小。
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Tbl_DrawImage(TABLE_HDL ullTblHdl, const char *szGridName, double dbX, double dbY, double dbW, double dbH, double dbScale, int nImgDataType, const char *szImage, unsigned int unImgDataSize);



/**
* @brief  在表格指定单元格上绘制线段
* @par    说明
*
* @param [in]            ullTblHdl                 由DSTP2x_CreateTable函数返回的表格句柄
* @param [out] 		     szGridName                单元格的名字，字符编码：utf-8；例如：基本单元格为"0-0"、"0-1"、"1-0"、"1-1"等；合并后的单元格为"Merged-0"、"Merged-1"等
* @param [in]            dbStartX                  线段相对于标签左上角为原点的起点横坐标，单位：mm（毫米）
* @param [in]            dbStartY                  线段相对于标签左上角为原点的起点纵坐标，单位：mm（毫米）
* @param [in]            dbEndX                    线段相对于标签左上角为原点的终点横坐标，单位：mm（毫米）
* @param [in]            dbEndY                    线段相对于标签左上角为原点的终点纵坐标，单位：mm（毫米）
* @param [in]            nLineWidth                线段宽度，单位：pixel（像素）
* @param [in]            nLineType                 线段类型，0:实线，1:虚线，2：点线，3：点划线，4：双点划线
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Tbl_DrawLine(TABLE_HDL ullTblHdl, const char *szGridName, double dbStartX, double dbStartY, double dbEndX, double dbEndY, int nLineWidth, int nLineType);

/**
* @brief  在表格指定单元格上绘制矩形
* @par    说明
*
* @param [in]            ullTblHdl              由DSTP2x_CreateTable函数返回的表格句柄
* @param [out] 		     szGridName             单元格的名字，字符编码：utf-8；例如：基本单元格为"0-0"、"0-1"、"1-0"、"1-1"等；合并后的单元格为"Merged-0"、"Merged-1"等
* @param [in]            dbX					矩形左上角横坐标，单位：mm（毫米）
* @param [in]            dbY					矩形左上角纵坐标，单位：mm（毫米）
* @param [in]            dbW                    矩形的宽度，单位：mm（毫米）
* @param [in]            dbH                    矩形的高度，单位：mm（毫米）
* @param [in]            nLineWidth             矩形的线宽度，单位：pixel（像素）
* @param [in]            nLineType              矩形的线类型，0:实线，1:虚线
* @param [in]            nIsFill                是否填充，1:是，0:否
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Tbl_DrawRectangle(TABLE_HDL ullTblHdl, const char *szGridName, double dbX, double dbY, double dbW, double dbH, int nLineWidth, int nLineType, int nIsFill);

/**
* @brief  在表格指定单元格上绘制椭圆
* @par    说明
*
* @param [in]            ullTblHdl				由DSTP2x_CreateTable函数返回的表格句柄
* @param [out] 		     szGridName				单元格的名字，字符编码：utf-8；例如：基本单元格为"0-0"、"0-1"、"1-0"、"1-1"等；合并后的单元格为"Merged-0"、"Merged-1"等
* @param [in]            dbX					椭圆左上角横坐标，单位：mm（毫米）
* @param [in]            dbY					椭圆左上角纵坐标，单位：mm（毫米）
* @param [in]            dbW					椭圆的宽度，单位：mm（毫米）
* @param [in]            dbH					椭圆的高度，单位：mm（毫米）
* @param [in]            nLineWidth				椭圆的线宽度，单位：pixel（像素）
* @param [in]            nLineType				椭圆的线类型，0:实线，1:虚线
* @param [in]            nIsFill				是否填充，1:是，0:否
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_Tbl_DrawEllipse(TABLE_HDL ullTblHdl, const char *szGridName, double dbX, double dbY, double dbW, double dbH, int nLineWidth, int nLineType, int nIsFill);

/**
* @brief  删除表格句柄
* @par    说明
*
* @param [in]            ullTblHdl                 由DSTP2x_CreateTable函数返回的表格句柄
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_DeleteTable(TABLE_HDL ullTblHdl);


/**
* @brief  设置标签上下文打印过程中需要写入的rfid数据
* @par    说明
* 如不调用本函数，则打印过程中不进行rfid读/写
* @param [in]            ullLcHdl                  由DSTP2x_CreateLabelContext函数返回的标签上下文句柄
* @param [in]            nRfidRgnType              需在打印过程中写入rfid数据的区域类型
* @n 1 - EPC区
* @n 2 - USER区
* @param [in]            nRfidDataFmt              需在打印过程中写入的rfid数据格式
* @n 1 - ASCII编码字符串
* @n 2 - 十六进制字符串
* @n 3 - 十六进制字节数据
* @param [in]            pData                     需在打印过程中写入的rfid数据
* @param [in]            nDataSize                 需在打印过程中写入的rfid数据长度，单位：字节；
*                                                  如pData为字符串，则本参数表示pData的实际字符串（不含"\0"）长度
*                                                  如pData为十六进制字节数据，则本参数表示pData实际应写入数据长度
* @return 0表示成功，非零失败
*/
unsigned int DSSDK DSTP2x_LcRfid_SetData(LC_HDL ullLcHdl, int nRfidRgnType, int nRfidDataFmt, const char *pData, int nDataSize);


/**
*
* @}
*/
#ifdef __cplusplus
}
#endif
#endif /*- __DSTP2x_H__ -*/
