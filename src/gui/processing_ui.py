# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'processing.ui'
#
# Created by: PyQt5 UI code generator 5.15.11


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ProcessingWindow(object):
    def setupUi(self, ProcessingWindow):
        ProcessingWindow.setObjectName("ProcessingWindow")
        ProcessingWindow.resize(429, 329)
        self.centralwidget = QtWidgets.QWidget(ProcessingWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.exit_button = QtWidgets.QPushButton(self.centralwidget)
        self.exit_button.setObjectName("exit_button")
        self.gridLayout.addWidget(self.exit_button, 1, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 1, 1, 1)
        self.output_textbox = QtWidgets.QTextBrowser(self.centralwidget)
        self.output_textbox.setAcceptRichText(True)
        self.output_textbox.setObjectName("output_textbox")
        self.gridLayout.addWidget(self.output_textbox, 0, 0, 1, 2)
        ProcessingWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(ProcessingWindow)
        self.statusbar.setObjectName("statusbar")
        ProcessingWindow.setStatusBar(self.statusbar)

        self.retranslateUi(ProcessingWindow)
        QtCore.QMetaObject.connectSlotsByName(ProcessingWindow)

    def retranslateUi(self, ProcessingWindow):
        _translate = QtCore.QCoreApplication.translate
        ProcessingWindow.setWindowTitle(_translate("ProcessingWindow", "MainWindow"))
        self.exit_button.setText(_translate("ProcessingWindow", "Save and Quit"))
        self.output_textbox.setHtml(_translate("ProcessingWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:7.8pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ProcessingWindow = QtWidgets.QMainWindow()
    ui = Ui_ProcessingWindow()
    ui.setupUi(ProcessingWindow)
    ProcessingWindow.show()
    sys.exit(app.exec_())
