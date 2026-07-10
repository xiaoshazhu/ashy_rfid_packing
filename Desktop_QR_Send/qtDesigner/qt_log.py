# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'qt_log.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QListView, QPushButton,
    QSizePolicy, QWidget)

class Ui_Dialog_log(object):
    def setupUi(self, Dialog_log):
        if not Dialog_log.objectName():
            Dialog_log.setObjectName(u"Dialog_log")
        Dialog_log.resize(780, 622)
        self.listView_log = QListView(Dialog_log)
        self.listView_log.setObjectName(u"listView_log")
        self.listView_log.setGeometry(QRect(10, 10, 761, 531))
        self.pushButton_export_log = QPushButton(Dialog_log)
        self.pushButton_export_log.setObjectName(u"pushButton_export_log")
        self.pushButton_export_log.setGeometry(QRect(270, 570, 81, 31))
        self.pushButton_close_dialog = QPushButton(Dialog_log)
        self.pushButton_close_dialog.setObjectName(u"pushButton_close_dialog")
        self.pushButton_close_dialog.setGeometry(QRect(440, 570, 81, 31))

        self.retranslateUi(Dialog_log)

        QMetaObject.connectSlotsByName(Dialog_log)
    # setupUi

    def retranslateUi(self, Dialog_log):
        Dialog_log.setWindowTitle(QCoreApplication.translate("Dialog_log", u"\u65e5\u5fd7", None))
        self.pushButton_export_log.setText(QCoreApplication.translate("Dialog_log", u"\u5bfc\u51fa\u65e5\u5fd7", None))
        self.pushButton_close_dialog.setText(QCoreApplication.translate("Dialog_log", u"\u5173\u95ed", None))
    # retranslateUi

