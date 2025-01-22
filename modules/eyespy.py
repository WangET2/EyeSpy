from qtpy.QtWidgets import *
import os
import csv
from pathlib import Path
import filehandler
from datetime import datetime
import configparser
import time

EXPOSURE = 1500

class ImageHandler:
    def __init__(self, parent: 'EyeSpy'):
        self.running = False
        self.parent = parent
        self.directory = Path(self.parent.directory)
        self.outputfile = Path(str('data' + datetime.now().strftime("%d-%m-%Y-%H-%M-%S") + '.csv'))
        
    def run(self):
        self.running = True
        currentfiles = os.listdir(self.directory)
        csvfile = open(self.outputfile, 'w', newline='')
        writer = csv.writer(csvfile)
        writer.writerow(['File Name', 'Fluorescence'])
        csvfile.flush()
        while self.running:
            QApplication.processEvents()
            previousfiles = currentfiles
            currentfiles = os.listdir(self.directory)
            queue = [item for item in currentfiles if item not in
                     previousfiles and 'LIVE' not in item.upper()
                     and 'PREVIEW' not in item.upper() and 'CSV' not in item.upper()]
            if queue:
                time.sleep((EXPOSURE / 1000) + 1.5)
            for file in queue:
                mean = filehandler.runprocessing(self.directory / file)
                outputrow = []
                outputrow.append(file)
                outputrow.append(mean)
                writer.writerow(outputrow)
                csvfile.flush()
                self.parent.update_textbox(str(file) + ': ' + str(mean))
                queue.remove(file)
                

class EyeSpy:
    def __init__(self):
        self.app = QApplication([])
        self.app.setApplicationDisplayName('EyeSpy')
        self.handler = None
        
        if 'options.ini' in os.listdir():
            config = configparser.ConfigParser()
            config.read('options.ini')
            self.directory = Path(config['DEFAULT']['Directory'])
        else:
            config = configparser.ConfigParser()
            directoryloc = QFileDialog.getExistingDirectory(None,
                                                            'Open Directory',
                                                            '/Pictures', QFileDialog.ShowDirsOnly |
                                                             QFileDialog.DontResolveSymlinks)
            config['DEFAULT'] = {'Directory': directoryloc}
            configfile = open('options.ini', 'w')
            config.write(configfile)
            self.directory = Path(directoryloc)
        
        self.rootwindow = QMainWindow()
        self.menu = QVBoxLayout()

        self.processingwindow = None
        self.processinglayout = None
        self.textbox = None

        self.configwindow, self.configlayout = self.create_window(QVBoxLayout)

        self.startbutton = self.create_button('Start', self.start, self.menu)
        self.configbutton = self.create_button('Config', self.settings, self.menu)
        
        self.menuwidget = QWidget()
        self.menuwidget.setLayout(self.menu)

        self.rootwindow.setCentralWidget(self.menuwidget)

    def show_gui(self):
        self.rootwindow.resize(500, 200)
        self.rootwindow.show()   
        self.app.exec_()

    def start(self, event):
        self.processingwindow, self.processinglayout = self.create_window(QVBoxLayout)
        self.textbox = QTextEdit()
        self.textbox.setReadOnly(True)
        self.processinglayout.addWidget(self.textbox)
        self.handler = ImageHandler(self)
        self.processingwindow.show()
        self.handler.run()

    def settings(self, event):
        self.configwindow.show()


    def create_button(self, text: str, function: callable, layout: QVBoxLayout) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(function)
        layout.addWidget(button)
        return button

    def create_window(self, layouttype: 'QVLayout') -> (QWidget, 'QVLayout'):
        window = QWidget()
        layout = layouttype()
        window.setLayout(layout)
        window.resize(500, 200)
        return (window, layout)

    def update_textbox(self, val: str) -> None:
        self.textbox.append(val)


if __name__ == '__main__':
    instance = EyeSpy()
    instance.show_gui()


