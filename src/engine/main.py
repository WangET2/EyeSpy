import sys
import os
os.environ["QT_QPA_PLATFORM"] = "wayland"
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtCore import pyqtSignal, QObject, QThread
from PyQt5.QtGui import QTextCursor
from src.gui.main_menu import Ui_MainWindow
from src.gui.config_ui import Ui_ConfigWindow
from src.gui.processing_ui import Ui_ProcessingWindow
from src.engine.config import Config
from src.images.output_writer import CSVWriter, TiffWriter
from src.engine.images_queue import LazyQueue
from functools import partial



class ProcessingWorker(QObject):
    output = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal()

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
        factory = partial(self._config.create_image, reader=self._config.stable_reader())
        queue = LazyQueue(self._config.directory, image_factory=factory, file_format=self._config.image_format, enqueue_existing=True)
        processor = self._config.create_processor()
        with CSVWriter(self._config.directory, header = ['filename', 'fluorescence']) as writer:
            while not queue.is_empty() and not self._stopped:
                current_image = queue.front()
                if current_image is not None:
                    try:
                        queue.dequeue()
                        result, roi = processor.circular_mean_fluorescence(current_image.array, current_image.scaling, current_image.white_point)
                        writer.write_row([str(current_image), f'{result:.3f}'])
                        self.output.emit(f'{current_image}: {result:.3f}')
                    except Exception as e:
                        self.error.emit(f'Error processing {current_image}: {str(e)}')

    def _live_process(self) -> None:
        queue = self._config.create_queue()
        processor = self._config.create_processor()
        with CSVWriter(self._config.directory, header = ['filename', 'fluorescence']) as writer:
            while not self._stopped:
                queue.update()
                current_image = queue.front()
                if current_image is not None:
                    try:
                        queue.dequeue()
                        result, roi = processor.circular_mean_fluorescence(current_image.array, current_image.scaling, current_image.white_point)
                        writer.write_row([str(current_image), f'{result:.3f}'])
                        self.output.emit(f'{current_image}: {result:.3f}')
                    except Exception as e:
                        self.error.emit(f'Error processing {current_image}: {str(e)}')
        self.finished.emit()

class ConfigWindow(QMainWindow):
    def __init__(self, config: Config):
        super().__init__()
        self._ui = Ui_ConfigWindow()
        self._ui.setupUi(self)
        self.setWindowTitle("Settings")
        self._config = config

        self._ui.directory_push_button.clicked.connect(self._select_directory)
        self._ui.save_button.clicked.connect(self._save_config)
        self._ui.reset_button.clicked.connect(self._reset_config)
        self._connect_save_signals()
        self._connect_disabled_buttons()
        self._load_config_to_ui()

    def _connect_disabled_buttons(self):
        self._ui.normalization_checkbox.stateChanged.connect(self._update_ui)
        self._ui.format_dropdown.currentIndexChanged.connect(self._update_ui)
        self._ui.masking_dropdown.currentIndexChanged.connect(self._update_ui)

    def _connect_save_signals(self):
        for widget in [self._ui.directory_line_edit, self._ui.scaling_line_edit,
                      self._ui.whitepoint_line_edit, self._ui.radius_line_edit,
                      self._ui.norm_percentile_line_edit, self._ui.thresh_intensity_line_edit,
                      self._ui.required_stable_line_edit, self._ui.check_delay_line_edit,
                      self._ui.max_checks_line_edit]:
            widget.textChanged.connect(self._enable_save)

        for widget in [self._ui.queue_dropdown, self._ui.format_dropdown,
                       self._ui.masking_dropdown, self._ui.extraction_dropdown]:
            widget.currentTextChanged.connect(self._enable_save)

        for widget in [self._ui.enqueue_checkbox, self._ui.normalization_checkbox,
                       self._ui.tiff_checkbox]:
            widget.stateChanged.connect(self._enable_save)

    def _enable_save(self):
        self._ui.save_button.setEnabled(True)

    def _select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        if directory:
            self._ui.directory_line_edit.setText(directory)

    def _load_config_to_ui(self):
        if self._config.directory:
            self._ui.directory_line_edit.setText(str(self._config.directory))
        queue_index = 0 if self._config.queue_type.lower() == 'file' else 1
        self._ui.queue_dropdown.setCurrentIndex(queue_index)
        self._ui.enqueue_checkbox.setChecked(self._config.enqueue_existing)
        self._ui.tiff_checkbox.setChecked(self._config.write_roi)

        format_index = 0 if self._config.image_format.lower() == 'czi' else 1
        self._ui.format_dropdown.setCurrentIndex(format_index)
        self._ui.whitepoint_line_edit.setText(str(self._config.white_point))
        self._ui.scaling_line_edit.setText(str(self._config.scaling))
        self._ui.radius_line_edit.setText(str(self._config.max_radius))

        self._ui.normalization_checkbox.setChecked(True)
        self._ui.norm_percentile_line_edit.setText(str(self._config.normalization_percentile))
        masking_index = 0 if self._config.masking_method.lower() == 'thresholding' else 1
        self._ui.masking_dropdown.setCurrentIndex(masking_index)
        self._ui.thresh_intensity_line_edit.setText(str(self._config.threshold_level))
        extraction_index = 0 if self._config.radius_method.lower() == 'contour' else 1
        self._ui.extraction_dropdown.setCurrentIndex(extraction_index)

        self._ui.required_stable_line_edit.setText(str(self._config.required_stable))
        self._ui.check_delay_line_edit.setText(str(self._config.check_delay))
        self._ui.max_checks_line_edit.setText(str(self._config.max_checks))

        self._update_ui()

    def _update_ui(self):
        norm_enabled = self._ui.normalization_checkbox.isChecked()
        self._ui.norm_percentile_label.setEnabled(norm_enabled)
        self._ui.norm_percentile_line_edit.setEnabled(norm_enabled)

        is_tiff = self._ui.format_dropdown.currentText() == '.tiff'
        self._ui.scaling_label.setEnabled(is_tiff)
        self._ui.scaling_line_edit.setEnabled(is_tiff)
        self._ui.whitepoint_label.setEnabled(is_tiff)
        self._ui.whitepoint_line_edit.setEnabled(is_tiff)

        is_threshold = self._ui.masking_dropdown.currentText() == 'Thresholding (Faster)'
        self._ui.thresh_intensity_label.setEnabled(is_threshold)
        self._ui.thresh_intensity_line_edit.setEnabled(is_threshold)

    def _save_config(self):
        try:
            self._config.set('files', 'Directory', self._ui.directory_line_edit.text())
            queue_type = 'File' if self._ui.queue_dropdown.currentIndex() == 0 else 'Image'
            self._config.set('files', 'Queue_Type', queue_type)
            self._config.set('files', 'Enqueue_Existing', self._ui.enqueue_checkbox.isChecked())
            self._config.set('files', 'Write_ROI', self._ui.tiff_checkbox.isChecked())

            image_format = 'CZI' if self._ui.format_dropdown.currentIndex() == 0 else 'TIFF'
            self._config.set('images', 'Image_Format', image_format)
            self._config.set('images', 'Scaling', float(self._ui.scaling_line_edit.text()))
            self._config.set('images', 'White_Point', int(self._ui.whitepoint_line_edit.text()))
            self._config.set('images', 'Max_Radius', int(self._ui.radius_line_edit.text()))

            self._config.set('processing', 'Normalization', self._ui.normalization_checkbox.isChecked())
            self._config.set('processing', 'Normalization_Percentile',
                            float(self._ui.norm_percentile_line_edit.text()))
            masking_method = 'Thresholding' if self._ui.masking_dropdown.currentIndex() == 0 else 'K-Means'
            self._config.set('processing', 'Masking_Method', masking_method)
            self._config.set('processing', 'Threshold_Level',
                            int(self._ui.thresh_intensity_line_edit.text()))
            radius_method = 'Contour' if self._ui.extraction_dropdown.currentIndex() == 0 else 'Eigenvalue'
            self._config.set('processing', 'Radius_Method', radius_method)

            self._config.set('processing', 'Required_Stable',
                            int(self._ui.required_stable_line_edit.text()))
            self._config.set('processing', 'Check_Delay', float(self._ui.check_delay_line_edit.text()))
            self._config.set('processing', 'Max_Checks', int(self._ui.max_checks_line_edit.text()))

            self._config.validate()
            self._config.save()
            self._ui.save_button.setEnabled(False)
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", f"\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration:\n{str(e)}")

    def _reset_config(self):
        self._config.reset()
        self._ui.save_button.setEnabled(False)
        self._load_config_to_ui()

class ProcessingWindow(QMainWindow):
    def __init__(self, config: Config, *, live=True):
        super().__init__()
        self._config = config
        self._live = live
        self._processing_thread = None
        self._worker = None
        self._ui = Ui_ProcessingWindow()
        self._ui.setupUi(self)
        title = 'Live Processing' if live else 'Batch Processing'
        self.setWindowTitle(title)
        self._ui.exit_button.clicked.connect(self._exit)
        self.start_processing()

    def start_processing(self) -> None:
        if self._processing_thread or self._worker:
            return
        self._processing_thread = QThread()
        self._worker = ProcessingWorker(self._config, live=self._live)
        self._worker.moveToThread(self._processing_thread)
        self._processing_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._processing_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.output.connect(self._show_output)
        self._worker.error.connect(self._show_output)
        self._worker.finished.connect(self._processing_finished)
        self._processing_thread.finished.connect(self._processing_finished)

        self._processing_thread.start()

    def _processing_finished(self):
        self._worker = None
        self._processing_thread = None

    def _exit(self):
        if self._worker:
            self._worker.stop()
        if self._processing_thread:
            self._processing_thread.quit()
            self._processing_thread.wait(1000)
        self.close()

    def closeEvent(self, event):
        if self._worker:
            self._worker.stop()
        if self._processing_thread:
            self._processing_thread.quit()
            self._processing_thread.wait(1000)
        event.accept()

    def _show_output(self, output: str) -> None:
        self._ui.output_textbox.append(output)
        cursor = self._ui.output_textbox.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._ui.output_textbox.setTextCursor(cursor)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)
        self.setWindowTitle("EyeSpy")

        self._config = Config()
        self.processing_window = None
        self.config_window = None

        self._ui.live_process_button.clicked.connect(self.start_live_processing)
        self._ui.batch_process_button.clicked.connect(self.start_batch_processing)
        self._ui.config_button.clicked.connect(self.show_config)

    def _validate_directory(self) -> bool:
        if not self._config.directory:
            QMessageBox.warning(self, 'Config Error', 'No directory selected. Select directory in settings before processing.')
            return False
        if not self._config.directory.exists():
            QMessageBox.warning(self, 'Config Error', f'Selected directory {self._config.directory} does not appear to exist or cannot be accessed.')
            return False
        return True

    def start_live_processing(self) -> None:
        if not self._validate_directory():
            return
        if self.processing_window is None or not self.processing_window.isVisible():
            self.processing_window = ProcessingWindow(self._config)
        self.processing_window.show()
        self.processing_window.raise_()
        self.processing_window.activateWindow()

    def start_batch_processing(self):
        if not self._validate_directory():
            return
        if self.processing_window is None or not self.processing_window.isVisible():
            self.processing_window = ProcessingWindow(self._config, live=False)
        self.processing_window.show()
        self.processing_window.raise_()
        self.processing_window.activateWindow()

    def show_config(self):
        if self.config_window is None:
            self.config_window = ConfigWindow(self._config)
        self.config_window.show()
        self.config_window.raise_()
        self.config_window.activateWindow()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('EyeSpy')
    app.setApplicationVersion('1.0.0')

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())