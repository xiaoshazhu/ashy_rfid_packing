# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'qt_setting.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QWidget)

class Ui_form_settings(object):
    def setupUi(self, form_settings):
        if not form_settings.objectName():
            form_settings.setObjectName(u"form_settings")
        form_settings.resize(540, 525)
        form_settings.setMinimumSize(QSize(540, 480))
        form_settings.setMaximumSize(QSize(540, 525))
        form_settings.setStyleSheet(u"background-color: #E0E0E0;")
        self.groupParam = QGroupBox(form_settings)
        self.groupParam.setObjectName(u"groupParam")
        self.groupParam.setEnabled(True)
        self.groupParam.setGeometry(QRect(280, 260, 221, 201))
        self.gridLayoutWidget_3 = QWidget(self.groupParam)
        self.gridLayoutWidget_3.setObjectName(u"gridLayoutWidget_3")
        self.gridLayoutWidget_3.setGeometry(QRect(10, 20, 201, 171))
        self.gridLayoutParam = QGridLayout(self.gridLayoutWidget_3)
        self.gridLayoutParam.setObjectName(u"gridLayoutParam")
        self.gridLayoutParam.setContentsMargins(0, 0, 0, 0)
        self.label_7 = QLabel(self.gridLayoutWidget_3)
        self.label_7.setObjectName(u"label_7")

        self.gridLayoutParam.addWidget(self.label_7, 4, 0, 1, 1)

        self.label_6 = QLabel(self.gridLayoutWidget_3)
        self.label_6.setObjectName(u"label_6")

        self.gridLayoutParam.addWidget(self.label_6, 3, 0, 1, 1)

        self.edit_min_y = QLineEdit(self.gridLayoutWidget_3)
        self.edit_min_y.setObjectName(u"edit_min_y")
        self.edit_min_y.setStyleSheet(u"background-color: #efefef ;")

        self.gridLayoutParam.addWidget(self.edit_min_y, 3, 1, 1, 1)

        self.label_4 = QLabel(self.gridLayoutWidget_3)
        self.label_4.setObjectName(u"label_4")

        self.gridLayoutParam.addWidget(self.label_4, 0, 0, 1, 1)

        self.edit_max_x = QLineEdit(self.gridLayoutWidget_3)
        self.edit_max_x.setObjectName(u"edit_max_x")
        self.edit_max_x.setStyleSheet(u"background-color: #efefef ;")

        self.gridLayoutParam.addWidget(self.edit_max_x, 1, 1, 1, 1)

        self.edit_min_x = QLineEdit(self.gridLayoutWidget_3)
        self.edit_min_x.setObjectName(u"edit_min_x")
        self.edit_min_x.setStyleSheet(u"background-color: #efefef ;")

        self.gridLayoutParam.addWidget(self.edit_min_x, 0, 1, 1, 1)

        self.edit_max_y = QLineEdit(self.gridLayoutWidget_3)
        self.edit_max_y.setObjectName(u"edit_max_y")
        self.edit_max_y.setStyleSheet(u"background-color: #efefef ;")

        self.gridLayoutParam.addWidget(self.edit_max_y, 4, 1, 1, 1)

        self.label_5 = QLabel(self.gridLayoutWidget_3)
        self.label_5.setObjectName(u"label_5")

        self.gridLayoutParam.addWidget(self.label_5, 1, 0, 1, 1)

        self.gridLayoutParam.setColumnStretch(0, 2)
        self.groupBox = QGroupBox(form_settings)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(40, 20, 461, 61))
        self.combobox_printSelect = QComboBox(self.groupBox)
        self.combobox_printSelect.setObjectName(u"combobox_printSelect")
        self.combobox_printSelect.setGeometry(QRect(10, 25, 441, 22))
        self.combobox_printSelect.setStyleSheet(u"background-color: #efefef ;")
        self.groupBox_2 = QGroupBox(form_settings)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setGeometry(QRect(40, 180, 461, 61))
        self.edit_service = QLineEdit(self.groupBox_2)
        self.edit_service.setObjectName(u"edit_service")
        self.edit_service.setGeometry(QRect(10, 25, 441, 21))
        self.edit_service.setStyleSheet(u"background-color: #efefef ;")
        self.groupParam_2 = QGroupBox(form_settings)
        self.groupParam_2.setObjectName(u"groupParam_2")
        self.groupParam_2.setEnabled(True)
        self.groupParam_2.setGeometry(QRect(40, 260, 221, 91))
        self.gridLayoutWidget_4 = QWidget(self.groupParam_2)
        self.gridLayoutWidget_4.setObjectName(u"gridLayoutWidget_4")
        self.gridLayoutWidget_4.setGeometry(QRect(10, 20, 201, 61))
        self.gridLayoutParam_2 = QGridLayout(self.gridLayoutWidget_4)
        self.gridLayoutParam_2.setObjectName(u"gridLayoutParam_2")
        self.gridLayoutParam_2.setContentsMargins(0, 0, 0, 0)
        self.edit_max_xiang = QLineEdit(self.gridLayoutWidget_4)
        self.edit_max_xiang.setObjectName(u"edit_max_xiang")
        self.edit_max_xiang.setEnabled(True)
        self.edit_max_xiang.setStyleSheet(u"background-color: #efefef ;")

        self.gridLayoutParam_2.addWidget(self.edit_max_xiang, 1, 1, 1, 1)

        self.edit_max_jian = QLineEdit(self.gridLayoutWidget_4)
        self.edit_max_jian.setObjectName(u"edit_max_jian")
        self.edit_max_jian.setEnabled(True)
        self.edit_max_jian.setStyleSheet(u"background-color: #efefef ;")

        self.gridLayoutParam_2.addWidget(self.edit_max_jian, 0, 1, 1, 1)

        self.label_8 = QLabel(self.gridLayoutWidget_4)
        self.label_8.setObjectName(u"label_8")

        self.gridLayoutParam_2.addWidget(self.label_8, 1, 0, 1, 1)

        self.label = QLabel(self.gridLayoutWidget_4)
        self.label.setObjectName(u"label")

        self.gridLayoutParam_2.addWidget(self.label, 0, 0, 1, 1)

        self.gridLayoutParam_2.setColumnStretch(0, 2)
        self.groupBox_3 = QGroupBox(form_settings)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.groupBox_3.setGeometry(QRect(40, 100, 461, 61))
        self.combobox_comSelect = QComboBox(self.groupBox_3)
        self.combobox_comSelect.setObjectName(u"combobox_comSelect")
        self.combobox_comSelect.setGeometry(QRect(10, 25, 441, 22))
        self.combobox_comSelect.setStyleSheet(u"background-color: #efefef ;")
        self.button_setting_save = QPushButton(form_settings)
        self.button_setting_save.setObjectName(u"button_setting_save")
        self.button_setting_save.setGeometry(QRect(380, 480, 100, 30))
        self.button_setting_cancel = QPushButton(form_settings)
        self.button_setting_cancel.setObjectName(u"button_setting_cancel")
        self.button_setting_cancel.setGeometry(QRect(60, 480, 100, 30))
        self.groupParam_3 = QGroupBox(form_settings)
        self.groupParam_3.setObjectName(u"groupParam_3")
        self.groupParam_3.setEnabled(True)
        self.groupParam_3.setGeometry(QRect(40, 350, 221, 111))
        self.gridLayoutWidget_5 = QWidget(self.groupParam_3)
        self.gridLayoutWidget_5.setObjectName(u"gridLayoutWidget_5")
        self.gridLayoutWidget_5.setGeometry(QRect(10, 20, 201, 81))
        self.gridLayoutParam_3 = QGridLayout(self.gridLayoutWidget_5)
        self.gridLayoutParam_3.setObjectName(u"gridLayoutParam_3")
        self.gridLayoutParam_3.setContentsMargins(0, 0, 0, 0)
        self.label_9 = QLabel(self.gridLayoutWidget_5)
        self.label_9.setObjectName(u"label_9")

        self.gridLayoutParam_3.addWidget(self.label_9, 1, 0, 1, 1)

        self.label_2 = QLabel(self.gridLayoutWidget_5)
        self.label_2.setObjectName(u"label_2")

        self.gridLayoutParam_3.addWidget(self.label_2, 0, 0, 1, 1)

        self.edit_page_height = QLineEdit(self.gridLayoutWidget_5)
        self.edit_page_height.setObjectName(u"edit_page_height")
        self.edit_page_height.setEnabled(True)
        self.edit_page_height.setStyleSheet(u"background-color: #efefef ;")

        self.gridLayoutParam_3.addWidget(self.edit_page_height, 1, 1, 1, 1)

        self.edit_page_width = QLineEdit(self.gridLayoutWidget_5)
        self.edit_page_width.setObjectName(u"edit_page_width")
        self.edit_page_width.setEnabled(True)
        self.edit_page_width.setStyleSheet(u"background-color: #efefef ;")

        self.gridLayoutParam_3.addWidget(self.edit_page_width, 0, 1, 1, 1)

        self.label_10 = QLabel(self.gridLayoutWidget_5)
        self.label_10.setObjectName(u"label_10")

        self.gridLayoutParam_3.addWidget(self.label_10, 2, 0, 1, 1)

        self.edit_page_num = QLineEdit(self.gridLayoutWidget_5)
        self.edit_page_num.setObjectName(u"edit_page_num")
        self.edit_page_num.setEnabled(True)
        self.edit_page_num.setStyleSheet(u"background-color: #efefef ;")

        self.gridLayoutParam_3.addWidget(self.edit_page_num, 2, 1, 1, 1)

        self.gridLayoutParam_3.setColumnStretch(0, 2)

        self.retranslateUi(form_settings)

        QMetaObject.connectSlotsByName(form_settings)
    # setupUi

    def retranslateUi(self, form_settings):
        form_settings.setWindowTitle(QCoreApplication.translate("form_settings", u"\u8bbe\u7f6e", None))
        self.groupParam.setTitle(QCoreApplication.translate("form_settings", u"\u8bc6\u522b\u533a\u57df", None))
        self.label_7.setText(QCoreApplication.translate("form_settings", u"Y\u8f74\u622a\u81f3", None))
        self.label_6.setText(QCoreApplication.translate("form_settings", u"Y\u8f74\u8d77\u59cb", None))
        self.edit_min_y.setText(QCoreApplication.translate("form_settings", u"0", None))
        self.label_4.setText(QCoreApplication.translate("form_settings", u"X\u8f74\u8d77\u59cb", None))
        self.edit_max_x.setText(QCoreApplication.translate("form_settings", u"0", None))
        self.edit_min_x.setText(QCoreApplication.translate("form_settings", u"0", None))
        self.edit_max_y.setText(QCoreApplication.translate("form_settings", u"0", None))
        self.label_5.setText(QCoreApplication.translate("form_settings", u"X\u8f74\u622a\u81f3", None))
        self.groupBox.setTitle(QCoreApplication.translate("form_settings", u"\u9009\u62e9\u6253\u5370\u673a", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("form_settings", u"\u8bbe\u7f6e\u670d\u52a1\u5668\u5730\u5740", None))
#if QT_CONFIG(tooltip)
        self.edit_service.setToolTip(QCoreApplication.translate("form_settings", u"<html><head/><body><p>ws://172.20.0.24/scanCode</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.edit_service.setText("")
        self.groupParam_2.setTitle(QCoreApplication.translate("form_settings", u"\u88c5\u7bb1\u53c2\u6570", None))
        self.edit_max_xiang.setText(QCoreApplication.translate("form_settings", u"0", None))
        self.edit_max_jian.setText(QCoreApplication.translate("form_settings", u"0", None))
        self.label_8.setText(QCoreApplication.translate("form_settings", u"\u4e00\u7bb1\u6570\u91cf\uff08\u6346\uff09", None))
        self.label.setText(QCoreApplication.translate("form_settings", u"\u4e00\u6346\u6570\u91cf\uff08\u76d2\uff09", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("form_settings", u"\u9009\u62e9\u4e32\u53e3", None))
        self.button_setting_save.setText(QCoreApplication.translate("form_settings", u"\u4fdd\u5b58", None))
        self.button_setting_cancel.setText(QCoreApplication.translate("form_settings", u"\u53d6\u6d88", None))
        self.groupParam_3.setTitle(QCoreApplication.translate("form_settings", u"\u6253\u5370\u673a\u53c2\u6570", None))
        self.label_9.setText(QCoreApplication.translate("form_settings", u"\u7eb8\u5f20\u9ad8\u5ea6\uff08mm\uff09", None))
        self.label_2.setText(QCoreApplication.translate("form_settings", u"\u7eb8\u5f20\u5bbd\u5ea6\uff08mm\uff09", None))
        self.edit_page_height.setText(QCoreApplication.translate("form_settings", u"0", None))
        self.edit_page_width.setText(QCoreApplication.translate("form_settings", u"0", None))
        self.label_10.setText(QCoreApplication.translate("form_settings", u"\u6253\u5370\u6570\u91cf\uff08\u4efd\uff09", None))
        self.edit_page_num.setText(QCoreApplication.translate("form_settings", u"0", None))
    # retranslateUi

