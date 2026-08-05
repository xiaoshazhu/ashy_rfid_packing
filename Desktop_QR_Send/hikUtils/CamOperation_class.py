# CamOperation_class.py -- coding: utf-8 --
import sys
import threading
import msvcrt
import numpy as np
import time
import sys, os
import datetime
import inspect
import ctypes
from ctypes import *
import numpy as np
from ctypes import *
import cv2
import logging  # 导入 logging 模块

sys.path.append("hikUtils/MvImport")

from hikUtils.MvImport.MvCameraControl_class import *
from hikUtils.MvImport.CameraParams_header import *


# 强制关闭线程（保留设备电脑已验证可显示画面的原SDK取流方式）
def Async_raise(tid, exctype):
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def Stop_thread(thread):
    Async_raise(thread.ident, SystemExit)


# 转为16进制字符串
def To_hex_str(num):
    chaDic = {10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f'}
    hexStr = ""
    if num < 0:
        num = num + 2 ** 32
    while num >= 16:
        digit = num % 16
        hexStr = chaDic.get(digit, str(digit)) + hexStr
        num //= 16
    hexStr = chaDic.get(num, str(num)) + hexStr
    return hexStr


# 是否是Mono图像
def Is_mono_data(enGvspPixelType):
    if PixelType_Gvsp_Mono8 == enGvspPixelType or PixelType_Gvsp_Mono10 == enGvspPixelType \
            or PixelType_Gvsp_Mono10_Packed == enGvspPixelType or PixelType_Gvsp_Mono12 == enGvspPixelType \
            or PixelType_Gvsp_Mono12_Packed == enGvspPixelType:
        return True
    else:
        return False


# 是否是彩色图像
def Is_color_data(enGvspPixelType):
    if PixelType_Gvsp_BayerGR8 == enGvspPixelType or PixelType_Gvsp_BayerRG8 == enGvspPixelType \
            or PixelType_Gvsp_BayerGB8 == enGvspPixelType or PixelType_Gvsp_BayerBG8 == enGvspPixelType \
            or PixelType_Gvsp_BayerGR10 == enGvspPixelType or PixelType_Gvsp_BayerRG10 == enGvspPixelType \
            or PixelType_Gvsp_BayerGB10 == enGvspPixelType or PixelType_Gvsp_BayerBG10 == enGvspPixelType \
            or PixelType_Gvsp_BayerGR12 == enGvspPixelType or PixelType_Gvsp_BayerRG12 == enGvspPixelType \
            or PixelType_Gvsp_BayerGB12 == enGvspPixelType or PixelType_Gvsp_BayerBG12 == enGvspPixelType \
            or PixelType_Gvsp_BayerGR10_Packed == enGvspPixelType or PixelType_Gvsp_BayerRG10_Packed == enGvspPixelType \
            or PixelType_Gvsp_BayerGB10_Packed == enGvspPixelType or PixelType_Gvsp_BayerBG10_Packed == enGvspPixelType \
            or PixelType_Gvsp_BayerGR12_Packed == enGvspPixelType or PixelType_Gvsp_BayerRG12_Packed == enGvspPixelType \
            or PixelType_Gvsp_BayerGB12_Packed == enGvspPixelType or PixelType_Gvsp_BayerBG12_Packed == enGvspPixelType \
            or PixelType_Gvsp_YUV422_Packed == enGvspPixelType or PixelType_Gvsp_YUV422_YUYV_Packed == enGvspPixelType:
        return True
    else:
        return False


# Mono图像转为python数组
def Mono_numpy(data, nWidth, nHeight):
    data_ = np.frombuffer(data, count=int(nWidth * nHeight), dtype=np.uint8, offset=0)
    data_mono_arr = data_.reshape(nHeight, nWidth)
    numArray = np.zeros([nHeight, nWidth, 1], "uint8")
    numArray[:, :, 0] = data_mono_arr
    return numArray


# 彩色图像转为python数组
def Color_numpy(data, nWidth, nHeight):
    data_ = np.frombuffer(data, count=int(nWidth * nHeight * 3), dtype=np.uint8, offset=0)
    data_r = data_[0:nWidth * nHeight * 3:3]
    data_g = data_[1:nWidth * nHeight * 3:3]
    data_b = data_[2:nWidth * nHeight * 3:3]

    data_r_arr = data_r.reshape(nHeight, nWidth)
    data_g_arr = data_g.reshape(nHeight, nWidth)
    data_b_arr = data_b.reshape(nHeight, nWidth)
    numArray = np.zeros([nHeight, nWidth, 3], "uint8")

    numArray[:, :, 0] = data_r_arr
    numArray[:, :, 1] = data_g_arr
    numArray[:, :, 2] = data_b_arr
    return numArray

def Color_numpy_bayer_rg_8(data, nWidth, nHeight):
    # 首先，我们需要从原始数据创建一个单通道的图像数组
    data_ = np.frombuffer(data, count=int(nWidth * nHeight), dtype=np.uint8, offset=0)
    bayer_image = data_.reshape(nHeight, nWidth)

    # 然后，使用OpenCV的demosaicing函数将Bayer图像转换为RGB图像
    rgb_image = cv2.cvtColor(bayer_image, cv2.COLOR_BAYER_RG2RGB)

    return rgb_image

# 相机操作类
class CameraOperation:

    def __init__(self, obj_cam, st_device_list, n_connect_num=0, b_open_device=False, b_start_grabbing=False,
                 h_thread_handle=None,
                 b_thread_closed=False, st_frame_info=None, b_exit=False, b_save_bmp=False, b_save_jpg=False,
                 buf_save_image=None,
                 n_save_image_size=0, n_win_gui_id=0, frame_rate=0, exposure_time=0, gain=0):

        self.obj_cam = obj_cam
        self.st_device_list = st_device_list
        self.n_connect_num = n_connect_num
        self.b_open_device = b_open_device
        self.b_start_grabbing = b_start_grabbing
        self.b_thread_closed = b_thread_closed
        self.st_frame_info = st_frame_info
        self.b_exit = b_exit
        self.b_save_bmp = b_save_bmp
        self.b_save_jpg = b_save_jpg
        self.buf_save_image = buf_save_image
        self.n_save_image_size = n_save_image_size
        self.h_thread_handle = h_thread_handle
        self.b_thread_closed
        self.frame_rate = frame_rate
        self.exposure_time = exposure_time
        self.gain = gain
        self.buf_lock = threading.Lock()  # 取图和存图的buffer锁
        self.sacn_image = None
        self.recognition_boxes = ()
        self.recognition_boxes_expire_at = 0.0
        self.recognition_snapshot = None
        self.n_win_gui_id = n_win_gui_id
        self._stop_event = threading.Event()
        self._last_no_data_warning_at = 0.0
        self._last_display_warning_at = 0.0
        logging.debug("CameraOperation object initialized.")

    def set_recognition_boxes(self, boxes, display_seconds=2.0):
        """短暂在SDK实时帧上绘制识别红框，避免Qt透明层覆盖成白屏。"""
        self.recognition_boxes = tuple(tuple(map(int, box)) for box in boxes)
        self.recognition_boxes_expire_at = time.monotonic() + max(
            0.2, float(display_seconds)
        )

    def set_recognition_snapshot(self, image, boxes, display_seconds=2.0):
        """显示带红框的真实识别帧，确保框和被识别图像属于同一坐标系。"""
        if image is None or getattr(image, "size", 0) == 0:
            self.set_recognition_boxes(boxes, display_seconds)
            return
        snapshot = image.copy()
        if len(snapshot.shape) == 2:
            snapshot = cv2.cvtColor(snapshot, cv2.COLOR_GRAY2BGR)
        for x, y, width, height in boxes:
            cv2.rectangle(
                snapshot,
                (int(x), int(y)),
                (int(x + width), int(y + height)),
                (0, 0, 255),
                4,
            )
        self.recognition_snapshot = snapshot
        self.recognition_boxes = tuple(tuple(map(int, box)) for box in boxes)
        self.recognition_boxes_expire_at = time.monotonic() + max(
            0.2, float(display_seconds)
        )

    def clear_recognition_boxes(self):
        self.recognition_boxes = ()
        self.recognition_boxes_expire_at = 0.0
        self.recognition_snapshot = None

    # 打开相机
    def Open_device(self):
        if not self.b_open_device:
            if self.n_connect_num < 0:
                return MV_E_CALLORDER

            # ch:选择设备并创建句柄 | en:Select device and create handle
            nConnectionNum = int(self.n_connect_num)
            stDeviceList = cast(self.st_device_list.pDeviceInfo[int(nConnectionNum)],
                                POINTER(MV_CC_DEVICE_INFO)).contents
            self.obj_cam = MvCamera()
            ret = self.obj_cam.MV_CC_CreateHandle(stDeviceList)
            if ret != 0:
                self.obj_cam.MV_CC_DestroyHandle()
                return ret

            ret = self.obj_cam.MV_CC_OpenDevice()
            if ret != 0:
                return ret
            logging.info("open device successfully!")
            self.b_open_device = True
            self.b_thread_closed = False

            # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
            if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
                nPacketSize = self.obj_cam.MV_CC_GetOptimalPacketSize()
                if int(nPacketSize) > 0:
                    ret = self.obj_cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                    if ret != 0:
                        logging.warning("warning: set packet size fail! ret[0x%x]" % ret)
                else:
                    logging.warning("warning: set packet size fail! ret[0x%x]" % nPacketSize)

            stBool = c_bool(False)
            ret = self.obj_cam.MV_CC_GetBoolValue("AcquisitionFrameRateEnable", stBool)
            if ret != 0:
                logging.warning("get acquisition frame rate enable fail! ret[0x%x]" % ret)

            # ch:设置触发模式为off | en:Set trigger mode as off
            ret = self.obj_cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
            if ret != 0:
                logging.warning("set trigger mode fail! ret[0x%x]" % ret)

            return MV_OK

    # 开始取图
    def Start_grabbing(self, winHandle):
        if not self.b_start_grabbing and self.b_open_device:
            self.b_exit = False
            self._stop_event.clear()
            self.n_win_gui_id = int(winHandle)
            ret = self.obj_cam.MV_CC_StartGrabbing()
            if ret != 0:
                return ret
            self.b_start_grabbing = True
            logging.info("start grabbing successfully!")
            try:
                self.h_thread_handle = threading.Thread(target=CameraOperation.Work_thread, args=(self, winHandle))
                self.h_thread_handle.daemon = True
                self.h_thread_handle.start()
                self.b_thread_closed = True
            finally:
                pass
            return MV_OK

        return MV_E_CALLORDER

    # 停止取图
    def Stop_grabbing(self):
        if self.b_start_grabbing and self.b_open_device:
            # 先通知取流线程正常退出，禁止用异步异常强杀线程，避免SDK锁和缓冲区残留。
            self.b_exit = True
            self._stop_event.set()
            ret = self.obj_cam.MV_CC_StopGrabbing()
            if ret != 0:
                return ret
            if self.h_thread_handle and self.h_thread_handle.is_alive():
                self.h_thread_handle.join(timeout=1.5)
                if self.h_thread_handle.is_alive():
                    logging.warning("相机取流线程未在1.5秒内退出，将在后台自行结束")
            self.b_thread_closed = False
            self.h_thread_handle = None
            logging.info("stop grabbing successfully!")
            self.b_start_grabbing = False
            return MV_OK
        else:
            return MV_E_CALLORDER

    # 关闭相机
    def Close_device(self):
        if self.b_open_device:
            if self.b_start_grabbing:
                ret = self.Stop_grabbing()
                if ret != MV_OK:
                    return ret
            else:
                self.b_exit = True
                self._stop_event.set()
                if self.h_thread_handle and self.h_thread_handle.is_alive():
                    self.h_thread_handle.join(timeout=1.5)
                self.b_thread_closed = False
                self.h_thread_handle = None
            ret = self.obj_cam.MV_CC_CloseDevice()
            if ret != 0:
                return ret

        # ch:销毁句柄 | Destroy handle
        self.obj_cam.MV_CC_DestroyHandle()
        self.b_open_device = False
        self.b_start_grabbing = False
        self.b_exit = True
        logging.info("close device successfully!")

        return MV_OK

    # 设置触发模式
    def Set_trigger_mode(self, is_trigger_mode):
        if not self.b_open_device:
            return MV_E_CALLORDER

        if not is_trigger_mode:
            ret = self.obj_cam.MV_CC_SetEnumValue("TriggerMode", 0)
            if ret != 0:
                return ret
        else:
            ret = self.obj_cam.MV_CC_SetEnumValue("TriggerMode", 1)
            if ret != 0:
                return ret
            ret = self.obj_cam.MV_CC_SetEnumValue("TriggerSource", 7)
            if ret != 0:
                return ret

        return MV_OK

    # 软触发一次
    def Trigger_once(self):
        if self.b_open_device:
            return self.obj_cam.MV_CC_SetCommandValue("TriggerSoftware")

    # 获取参数
    def Get_parameter(self):
        if self.b_open_device:
            stFloatParam_FrameRate = MVCC_FLOATVALUE()
            memset(byref(stFloatParam_FrameRate), 0, sizeof(MVCC_FLOATVALUE))
            stFloatParam_exposureTime = MVCC_FLOATVALUE()
            memset(byref(stFloatParam_exposureTime), 0, sizeof(MVCC_FLOATVALUE))
            stFloatParam_gain = MVCC_FLOATVALUE()
            memset(byref(stFloatParam_gain), 0, sizeof(MVCC_FLOATVALUE))
            ret = self.obj_cam.MV_CC_GetFloatValue("AcquisitionFrameRate", stFloatParam_FrameRate)
            if ret != 0:
                return ret
            self.frame_rate = stFloatParam_FrameRate.fCurValue

            ret = self.obj_cam.MV_CC_GetFloatValue("ExposureTime", stFloatParam_exposureTime)
            if ret != 0:
                return ret
            self.exposure_time = stFloatParam_exposureTime.fCurValue

            ret = self.obj_cam.MV_CC_GetFloatValue("Gain", stFloatParam_gain)
            if ret != 0:
                return ret
            self.gain = stFloatParam_gain.fCurValue

            return MV_OK

    # 设置参数
    def Set_parameter(self, frameRate, exposureTime, gain):
        if '' == frameRate or '' == exposureTime or '' == gain:
            logging.warning('please type in the text box !')
            return MV_E_PARAMETER
        if self.b_open_device:
            ret = self.obj_cam.MV_CC_SetEnumValue("ExposureAuto", 0)
            time.sleep(0.2)
            ret = self.obj_cam.MV_CC_SetFloatValue("ExposureTime", float(exposureTime))
            if ret != 0:
                logging.error('set exposure time fail! ret = ' + To_hex_str(ret))
                return ret

            ret = self.obj_cam.MV_CC_SetFloatValue("Gain", float(gain))
            if ret != 0:
                logging.error('set gain fail! ret = ' + To_hex_str(ret))
                return ret

            ret = self.obj_cam.MV_CC_SetFloatValue("AcquisitionFrameRate", float(frameRate))
            if ret != 0:
                logging.error('set acquistion frame rate fail! ret = ' + To_hex_str(ret))
                return ret

            logging.info('set parameter success!')

            return MV_OK

    # 取图线程函数
    def Work_thread(self, winHandle):
        stOutFrame = MV_FRAME_OUT()
        memset(byref(stOutFrame), 0, sizeof(stOutFrame))

        while not self._stop_event.is_set():
            ret = self.obj_cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
            if 0 == ret:
                # 拷贝图像和图像信息

                if self.buf_save_image is None or len(self.buf_save_image) != stOutFrame.stFrameInfo.nFrameLen:
                    self.buf_save_image = (c_ubyte * stOutFrame.stFrameInfo.nFrameLen)()

                self.st_frame_info = stOutFrame.stFrameInfo

                # 获取缓存锁
                with self.buf_lock:
                    cdll.msvcrt.memcpy(byref(self.buf_save_image), stOutFrame.pBufAddr, self.st_frame_info.nFrameLen)

                logging.debug("get one frame: Width[%d], Height[%d], nFrameNum[%d]"
                      % (self.st_frame_info.nWidth, self.st_frame_info.nHeight, self.st_frame_info.nFrameNum))
                # 释放缓存
                self.obj_cam.MV_CC_FreeImageBuffer(stOutFrame)
            else:
                if self._stop_event.is_set():
                    break
                now = time.monotonic()
                if now - self._last_no_data_warning_at >= 5.0:
                    logging.warning("no data, ret = " + To_hex_str(ret))
                    self._last_no_data_warning_at = now
                continue
            # 使用Display接口显示图像。识别红框直接绘制到当前实时帧，显示约2秒后
            # 自动恢复原始SDK画面，不再使用会造成Windows白屏的Qt透明覆盖控件。
            active_boxes = self.recognition_boxes
            if active_boxes and time.monotonic() >= self.recognition_boxes_expire_at:
                self.clear_recognition_boxes()
                active_boxes = ()

            live_overlay_image = self.recognition_snapshot if active_boxes else None
            if active_boxes and live_overlay_image is None:
                live_overlay_image = self.get_np_array_image()
                if live_overlay_image is not None:
                    live_overlay_image = live_overlay_image.copy()
                    if len(live_overlay_image.shape) == 2:
                        live_overlay_image = cv2.cvtColor(
                            live_overlay_image, cv2.COLOR_GRAY2BGR
                        )
                    for x, y, width, height in active_boxes:
                        cv2.rectangle(
                            live_overlay_image,
                            (x, y),
                            (x + width, y + height),
                            (0, 0, 255),
                            4,
                        )

            if live_overlay_image is not None:
                height, width, channel = live_overlay_image.shape
                pData = (c_ubyte * live_overlay_image.size).from_buffer_copy(
                    live_overlay_image.tobytes()
                )
                stDisplayParam = MV_DISPLAY_FRAME_INFO()
                memset(byref(stDisplayParam), 0, sizeof(stDisplayParam))
                stDisplayParam.hWnd = int(winHandle)
                stDisplayParam.nWidth = width
                stDisplayParam.nHeight = height
                stDisplayParam.enPixelType = PixelType_Gvsp_BGR8_Packed
                stDisplayParam.pData = pData
                stDisplayParam.nDataLen = live_overlay_image.size
                display_ret = self.obj_cam.MV_CC_DisplayOneFrame(stDisplayParam)
            elif self.sacn_image is not None:
                height, width, channel = self.sacn_image.shape

                # 创建一个c_ubyte数组的指针，用于MV_CC_DisplayOneFrame函数
                pData = (c_ubyte * self.sacn_image.size).from_buffer_copy(self.sacn_image.tobytes())

                stDisplayParam = MV_DISPLAY_FRAME_INFO()
                memset(byref(stDisplayParam), 0, sizeof(stDisplayParam))
                stDisplayParam.hWnd = int(winHandle)
                stDisplayParam.nWidth = width
                stDisplayParam.nHeight = height
                stDisplayParam.enPixelType = PixelType_Gvsp_BGR8_Packed
                stDisplayParam.pData = pData
                stDisplayParam.nDataLen = self.sacn_image.size
                display_ret = self.obj_cam.MV_CC_DisplayOneFrame(stDisplayParam)

            else:
                stDisplayParam = MV_DISPLAY_FRAME_INFO()
                memset(byref(stDisplayParam), 0, sizeof(stDisplayParam))
                stDisplayParam.hWnd = int(winHandle)
                stDisplayParam.nWidth = self.st_frame_info.nWidth
                stDisplayParam.nHeight = self.st_frame_info.nHeight
                stDisplayParam.enPixelType = self.st_frame_info.enPixelType
                stDisplayParam.pData = self.buf_save_image
                stDisplayParam.nDataLen = self.st_frame_info.nFrameLen
                display_ret = self.obj_cam.MV_CC_DisplayOneFrame(stDisplayParam)

            if display_ret != MV_OK:
                now = time.monotonic()
                if now - self._last_display_warning_at >= 5.0:
                    logging.warning(
                        "相机画面渲染失败: HWND=%s ret=%s",
                        int(winHandle),
                        To_hex_str(display_ret),
                    )
                    self._last_display_warning_at = now

        # 保留属性本身，后续重新启动取流时可以安全重新分配缓冲区。
        self.buf_save_image = None

    # 存jpg图像
    def Save_jpg(self):

        if self.buf_save_image is None:
            return

        # 获取缓存锁
        self.buf_lock.acquire()

        file_path = str(self.st_frame_info.nFrameNum) + ".jpg"
        c_file_path = file_path.encode('ascii')
        stSaveParam = MV_SAVE_IMAGE_TO_FILE_PARAM_EX()
        stSaveParam.enPixelType = self.st_frame_info.enPixelType  # ch:相机对应的像素格式 | en:Camera pixel type
        stSaveParam.nWidth = self.st_frame_info.nWidth  # ch:相机对应的宽 | en:Width
        stSaveParam.nHeight = self.st_frame_info.nHeight  # ch:相机对应的高 | en:Height
        stSaveParam.nDataLen = self.st_frame_info.nFrameLen
        stSaveParam.pData = cast(self.buf_save_image, POINTER(c_ubyte))
        stSaveParam.enImageType = MV_Image_Jpeg  # ch:需要保存的图像类型 | en:Image format to save
        stSaveParam.nQuality = 80
        stSaveParam.pcImagePath = ctypes.create_string_buffer(c_file_path)
        stSaveParam.iMethodValue = 2
        ret = self.obj_cam.MV_CC_SaveImageToFileEx(stSaveParam)

        self.buf_lock.release()
        return ret

    # 存BMP图像
    def Save_Bmp(self):

        if 0 == self.buf_save_image:
            return

        # 获取缓存锁
        self.buf_lock.acquire()

        file_path = str(self.st_frame_info.nFrameNum) + ".bmp"
        c_file_path = file_path.encode('ascii')

        stSaveParam = MV_SAVE_IMAGE_TO_FILE_PARAM_EX()
        stSaveParam.enPixelType = self.st_frame_info.enPixelType  # ch:相机对应的像素格式 | en:Camera pixel type
        stSaveParam.nWidth = self.st_frame_info.nWidth  # ch:相机对应的宽 | en:Width
        stSaveParam.nHeight = self.st_frame_info.nHeight  # ch:相机对应的高 | en:Height
        stSaveParam.nDataLen = self.st_frame_info.nFrameLen
        stSaveParam.pData = cast(self.buf_save_image, POINTER(c_ubyte))
        stSaveParam.enImageType = MV_Image_Bmp  # ch:需要保存的图像类型 | en:Image format to save
        stSaveParam.nQuality = 8
        stSaveParam.pcImagePath = ctypes.create_string_buffer(c_file_path)
        stSaveParam.iMethodValue = 2
        ret = self.obj_cam.MV_CC_SaveImageToFileEx(stSaveParam)

        self.buf_lock.release()

        return ret


    def get_np_array_image(self):
        # 检查是否有保存的图像数据
        if self.buf_save_image is None:
            logging.warning("No save image")
            return None

        # 获取缓存锁
        self.buf_lock.acquire()

        try:
            # 检查图像类型并转换为NumPy数组
            if Is_mono_data(self.st_frame_info.enPixelType):
                np_array_image = Mono_numpy(self.buf_save_image, self.st_frame_info.nWidth, self.st_frame_info.nHeight)
            elif Is_color_data(self.st_frame_info.enPixelType):
                np_array_image = Color_numpy_bayer_rg_8(self.buf_save_image, self.st_frame_info.nWidth, self.st_frame_info.nHeight)
            else:
                # 如果不是Mono或Color图像，返回None
                np_array_image = None
        finally:
            # 释放缓存锁
            self.buf_lock.release()

        return np_array_image
