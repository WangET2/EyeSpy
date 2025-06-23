import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtCore import pyqtSignal, QObject, QThread
from PyQt5.QtGui import QTextCursor
from src.gui.main_menu import Ui_MainWindow
from src.gui.config_ui import Ui_ConfigWindow
from src.gui.processing_ui import Ui_ProcessingWindow
from src.engine.config import Config
from src.images.output_writer import OutputWriter
from src.images.processing import Processor
from src.engine.images_queue import create_queue_from_config, FileQueue

class Worker(QObject):
    output = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal

    def __init__(self, config: Config, *, live: bool=True):
        super().__init__()
        self._config = config
        self._live = live
        self._stopped = False

    def run(self) -> None:
        if self._live:
            self._live_process()
        else:
            self._batch_process()

    def stop(self) -> None:
        self._stopped = True

    def _batch_process(self) -> None:
        queue = FileQueue(self._config, enqueue_existing=True)
        processor = Processor(self._config)
        while not queue.is_empty():
            with OutputWriter(self._config.directory, header=['filename','fluorescence']) as writer:
                current_image = queue.front()
                if current_image is not None:
                    try:
                        queue.dequeue()
                        result = processor.circular_mean_fluorescence(current_image)
                        writer.write_row([str(current_image), f'{result:.3f}'])
                        self.output.emit(f'{current_image}: {result:.3f}')
                    except Exception as e:
                        self.error.emit(f'Error processing {current_image}: {str(e)}')
        self.finished.emit()

    def _live_process(self) -> None:
        queue = create_queue_from_config(self._config)
        processor = Processor(self._config)
        while not self._stopped:
            with OutputWriter(self._config.directory, header=['filename','fluorescence']) as writer:
                queue.update()
                current_image = queue.front()
                if current_image is not None:
                    try:
                        queue.dequeue()
                        result = processor.circular_mean_fluorescence(current_image)
                        writer.write_row([str(current_image), f'{result:.3f}'])
                        self.output.emit(f'{current_image}: {result:.3f}')
                    except Exception as e:
                        self.error.emit(f'Error processing {current_image}: {str(e)}')
        self.finished.emit()
