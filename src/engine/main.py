import sys
from time import time
from typing import Iterable
from functools import partial
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QLineEdit
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QEventLoop, pyqtSlot
from PyQt5.QtGui import QTextCursor
from src.gui.main_menu import Ui_MainWindow
from src.gui.config_ui import Ui_ConfigWindow
from src.gui.processing_ui import Ui_ProcessingWindow
from src.engine.config import Config
from src.images.output_writer import CSVWriter, TiffWriter
from src.engine.images_queue import LazyQueue



class ProcessingWorker(QObject):
    output = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal()
    get_label = pyqtSignal()

    def __init__(self, config: Config, *, live: bool=True):
        super().__init__()
        self._config = config
        self._live = live
        self._stopped = False
        self._img_writer = None
        if self._config.write_labels:
            self._previous_label = None
            self._wait_loop = None
        self._header = ['filename', 'fluorescence', 'label'] if self._config.write_labels else ['filename', 'fluorescence']
        if self._config.write_roi:
            self._img_writer = TiffWriter(self._config.output_directory)

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
        to_process = len(queue)
        with CSVWriter(self._config.output_directory, header = self._header) as writer:
            begin_time = time()
            count = 1
            while not queue.is_empty() and not self._stopped:
                current_image = queue.front()
                if current_image is not None:
                    try:
                        label = self._receive_combo_value() or ""
                        queue.dequeue()
                        results = processor.process(current_image)
                        writer.write_row([str(current_image), f'{results.mean_fluorescence:.3f}'])
                        self.output.emit(f'{count}/{to_process} - {current_image}: {results.mean_fluorescence:.3f}')
                        if self._img_writer is not None:
                            center_y, center_x = results.center
                            self._img_writer.write_roi(results.writeable_img, current_image.name, current_image.white_point, center_y, center_x, results.radius)
                    except Exception as e:
                        self.error.emit(f'Error processing {current_image}: {str(e)}')
                    finally:
                        count += 1
        completion_time = time()
        self.output.emit(f'Total time: {completion_time - begin_time:.4f} sec')
        self.output.emit(f'Average time per image: {(completion_time - begin_time) / to_process:.4f} sec')
        self.finished.emit()

    def _live_process(self) -> None:
        queue = self._config.create_queue()
        processor = self._config.create_processor()
        with CSVWriter(self._config.output_directory, header = self._header) as writer:
            while not self._stopped:
                queue.update()
                current_image = queue.front()
                if current_image is not None:
                    try:
                        if self._config.write_labels:
                            label = self._receive_combo_value()
                        queue.dequeue()
                        results = processor.process(current_image)
                        writer.write_row([str(current_image), f'{results.mean_fluorescence:.3f}']+
                                         ([label] if self._config.write_labels else []))
                        self.output.emit(f'{current_image}: {results.mean_fluorescence:.3f}')
                        if self._img_writer is not None:
                            center_y, center_x = results.center
                            self._img_writer.write_roi(results.writeable_img, current_image.name, current_image.white_point, center_y, center_x, results.radius)
                    except Exception as e:
                        self.error.emit(f'Error processing {current_image}: {str(e)}')
        self.finished.emit()

    @pyqtSlot(str)
    def _on_label_receive(self, label: str) -> None:
        self._previous_label = label
        if self._wait_loop and self._wait_loop.isRunning():
            self._wait_loop.quit()

    def _receive_combo_value(self) -> str:
        self._wait_loop = QEventLoop()
        self.get_label.emit()
        self._wait_loop.exec_()
        return self._previous_label

class BayesianWorker(QObject):
    output = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, conf: Config, mode: str):
        super().__init__()
        self._config = conf
        self._mode = mode
        self._stopped = False
        factory = partial(self._config.create_image, reader=self._config.stable_reader())
        direc = self._config.training_directory_raw if self._mode.lower() == 'train' else self._config.testing_directory_raw
        self._queue = LazyQueue(direc, image_factory=factory, file_format=self._config.image_format,
                          enqueue_existing=True)
        self._processor = self._config.create_processor()
        self._max = len(self._queue)
        self._counter = 1

    def run(self):
        if self._mode.lower() == 'train':
            self._train()
        elif self._mode.lower() == 'test':
            self._test()

    def _train(self):
        trainer = self._config.create_trainer()
        while not self._queue.is_empty() and not self._stopped:
            raw_image = self._queue.front()
            if raw_image is not None:
                try:
                    self._queue.dequeue()
                    trainer.update(raw_image=raw_image, truth_image=None)
                    self.output.emit(f'Training {raw_image.name} Complete: {self._counter}/{self._max}')
                except Exception as e:
                    self.error.emit(f'Error training with {raw_image.name}: {str(e)}')
                finally:
                    self._counter += 1
        self.output.emit('Calculating...')
        self.output.emit(f'Suggested Threshold: {trainer.train():.4f}')
        self.finished.emit()

    def _test(self):
        tester = self._config.create_tester()
        begin_time = time()
        while not self._queue.is_empty() and not self._stopped:
            current_image = self._queue.front()
            if current_image is not None:
                try:
                    self._queue.dequeue()
                    tester.update(img_name = current_image.name, white_point=current_image.white_point,
                                  scaling=current_image.scaling)
                    self.output.emit(f'Testing {current_image} Complete: {self._counter}/{self._max}')
                except Exception as e:
                    self.error.emit(f'Error testing with {current_image}: {str(e)}')
                finally:
                    self._counter += 1
        completion_time = time()
        self.output.emit(tester.report())
        self.output.emit(f'Total time: {completion_time - begin_time:.4f} sec')
        self.output.emit(f'Average time per image: {(completion_time - begin_time) / self._max:.4f} sec')
        self.finished.emit()

    def stop(self):
        self._stopped = True

class ConfigWindow(QMainWindow):
    def __init__(self, config: Config):
        super().__init__()
        self._ui = Ui_ConfigWindow()
        self._ui.setupUi(self)
        self.setWindowTitle('Settings')
        self._config = config
        self._unsaved_changes = False

        self._ui.directory_push_button.clicked.connect(partial(self._select_directory, line_edit=self._ui.directory_line_edit))
        self._ui.output_directory_push_button.clicked.connect(partial(self._select_directory, line_edit=self._ui.output_directory_line_edit))
        self._ui.training_input_directory_button.clicked.connect(partial(self._select_directory, line_edit=self._ui.training_input_directory_line_edit))
        self._ui.training_mask_directory_button.clicked.connect(partial(self._select_directory, line_edit=self._ui.training_mask_directory_line_edit))
        self._ui.testing_input_directory_button.clicked.connect(partial(self._select_directory, line_edit=self._ui.testing_input_directory_line_edit))
        self._ui.testing_mask_directory_button.clicked.connect(partial(self._select_directory, line_edit=self._ui.testing_mask_directory_line_edit))
        self._ui.save_button.clicked.connect(self._save_config)
        self._ui.reset_button.clicked.connect(self._reset_config)
        self._ui.save_button.setEnabled(False)
        self._connect_disabled_buttons()
        self._load_config_to_ui()
        self._connect_save_signals()

    def _connect_disabled_buttons(self):
        self._ui.normalization_checkbox.stateChanged.connect(self._update_ui)
        self._ui.format_dropdown.currentIndexChanged.connect(self._update_ui)
        self._ui.masking_dropdown.currentIndexChanged.connect(self._update_ui)

    def _connect_save_signals(self):
        for widget in [self._ui.directory_line_edit, self._ui.scaling_line_edit,
                      self._ui.whitepoint_line_edit, self._ui.radius_line_edit,
                      self._ui.norm_percentile_line_edit, self._ui.thresh_intensity_line_edit,
                      self._ui.required_stable_line_edit, self._ui.check_delay_line_edit,
                      self._ui.max_checks_line_edit, self._ui.output_directory_line_edit,
                      self._ui.testing_input_directory_line_edit, self._ui.testing_mask_directory_line_edit,
                      self._ui.training_input_directory_line_edit, self._ui.training_mask_directory_line_edit,
                      self._ui.truth_intensity_line_edit]:
            widget.textChanged.connect(self._enable_save)

        for widget in [self._ui.queue_dropdown, self._ui.format_dropdown,
                       self._ui.masking_dropdown, self._ui.extraction_dropdown,
                       self._ui.testing_method_dropdown]:
            widget.currentTextChanged.connect(self._enable_save)

        for widget in [self._ui.enqueue_checkbox, self._ui.normalization_checkbox,
                       self._ui.tiff_checkbox, self._ui.label_checkbox]:
            widget.stateChanged.connect(self._enable_save)

    def _enable_save(self):
        self._ui.save_button.setEnabled(True)
        self._unsaved_changes=True

    def _select_directory(self, line_edit: QLineEdit):
        directory = QFileDialog.getExistingDirectory(self, 'Select Image Directory')
        if directory:
            line_edit.setText(directory)

    def _load_config_to_ui(self):
        if self._config.directory:
            self._ui.directory_line_edit.setText(str(self._config.directory))
        else:
            self._ui.directory_line_edit.setText('')
        if self._config.output_directory:
            self._ui.output_directory_line_edit.setText(str(self._config.output_directory))
        else:
            self._ui.output_directory_line_edit.setText('')
        queue_index = 0 if self._config.queue_type.lower() == 'file' else 1
        self._ui.queue_dropdown.setCurrentIndex(queue_index)
        self._ui.label_checkbox.setChecked(self._config.write_labels)
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

        if self._config.training_directory_raw:
            self._ui.training_input_directory_line_edit.setText(str(self._config.training_directory_raw))
        else:
            self._ui.training_input_directory_line_edit.setText('')
        if self._config.training_directory_truth:
            self._ui.training_mask_directory_line_edit.setText(str(self._config.training_directory_truth))
        else:
            self._ui.training_mask_directory_line_edit.setText('')
        if self._config.testing_directory_raw:
            self._ui.testing_input_directory_line_edit.setText(str(self._config.testing_directory_raw))
        else:
            self._ui.testing_input_directory_line_edit.setText('')
        if self._config.testing_directory_truth:
            self._ui.testing_mask_directory_line_edit.setText(str(self._config.testing_directory_truth))
        else:
            self._ui.testing_mask_directory_line_edit.setText('')
        self._ui.truth_intensity_line_edit.setText(str(self._config.truth_intensity))
        method_index = 0 if self._config.testing_method.lower() == 'circle' else 1
        self._ui.testing_method_dropdown.setCurrentIndex(method_index)

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
            self._config.set('files', 'Output_Directory', self._ui.output_directory_line_edit.text())
            queue_type = 'File' if self._ui.queue_dropdown.currentIndex() == 0 else 'Image'
            self._config.set('files', 'Queue_Type', queue_type)
            self._config.set('files', 'Write_Labels', self._ui.label_checkbox.isChecked())
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

            self._config.set('bayesian', 'Training_Directory_Raw', self._ui.training_input_directory_line_edit.text())
            self._config.set('bayesian', 'Training_Directory_Truth', self._ui.training_mask_directory_line_edit.text())
            self._config.set('bayesian', 'Testing_Directory_Raw', self._ui.testing_input_directory_line_edit.text())
            self._config.set('bayesian', 'Testing_Directory_Truth', self._ui.testing_mask_directory_line_edit.text())
            self._config.set('bayesian', 'Truth_Intensity', int(self._ui.truth_intensity_line_edit.text()))
            testing_method = 'Circle' if self._ui.testing_method_dropdown.currentIndex() == 0 else 'Mask'
            self._config.set('bayesian', 'Testing_Method', testing_method)

            self._config.validate()
            self._config.save()
            self._ui.save_button.setEnabled(False)
            self._unsaved_changes=False
            QMessageBox.information(self, 'Success', 'Configuration saved successfully!')
        except ValueError as e:
            QMessageBox.warning(self, 'Invalid Input', f'\n{str(e)}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save configuration:\n{str(e)}')

    def _reset_config(self):
        reset_warning = QMessageBox()
        reset_warning.setIcon(QMessageBox.Warning)
        reset_warning.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        reset_warning.setText('Are you sure you want to reset?')
        reset_warning.setInformativeText('All saved settings will be reverted to their defaults. This cannot be undone.')
        reset_warning.setDefaultButton(QMessageBox.No)
        response = reset_warning.exec_()
        if response == QMessageBox.Yes:
            self._config.reset()
            self._load_config_to_ui()
            self._unsaved_changes = False
            QMessageBox.information(self, 'Success', 'Configuration reset!')
            self._ui.save_button.setEnabled(False)
        elif response == QMessageBox.No:
            reset_warning.close()

    def closeEvent(self, event):
        if self._unsaved_changes:
            unsaved_warning = QMessageBox()
            unsaved_warning.setIcon(QMessageBox.Warning)
            unsaved_warning.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            unsaved_warning.setText('Are you sure you want to exit?')
            unsaved_warning.setInformativeText(
                'All unsaved settings will be lost. This cannot be undone.')
            unsaved_warning.setDefaultButton(QMessageBox.No)
            response = unsaved_warning.exec_()
            if response == QMessageBox.Yes:
                self._load_config_to_ui()
                event.accept()
            elif response == QMessageBox.No:
                event.ignore()
                unsaved_warning.close()
        else:
            event.accept()

class ProcessingWindow(QMainWindow):
    send_label = pyqtSignal(str)

    def __init__(self, config: Config, *, live=True):
        super().__init__()
        self._config = config
        self._live = live
        self._processing_thread = None
        self._worker = None
        self._ui = Ui_ProcessingWindow()
        self._ui.setupUi(self)
        self._ui.label_group_box.setEnabled(self._config.write_labels)
        title = 'Live Processing' if live else 'Batch Processing'
        self.setWindowTitle(title)
        self._ui.exit_button.clicked.connect(self._exit)
        self._ui.label_save_button.clicked.connect(self._add_label_to_dropdown)
        self.start_processing()

    def start_processing(self) -> None:
        if self._processing_thread or self._worker:
            return
        self._processing_thread = QThread()
        self._worker = ProcessingWorker(self._config, live=self._live)
        self._worker.moveToThread(self._processing_thread)
        self._processing_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._processing_thread.quit)
        self._worker.output.connect(self._show_output)
        self._worker.error.connect(self._show_output)
        self._worker.window = self
        if self._config.write_labels:
            self._worker.get_label.connect(self._send_label)
            self.send_label.connect(self._worker._on_label_receive)
        self._processing_thread.start()

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

    def _add_label_to_dropdown(self) -> None:
        new_label = self._ui.label_combo_box.currentText()
        if new_label.strip() and new_label not in [self._ui.label_combo_box.itemText(i) for i in range(self._ui.label_combo_box.count())]:
            self._ui.label_combo_box.addItem(new_label)

    def _send_label(self) -> None:
         self.send_label.emit(self._ui.label_combo_box.currentText())

class BayesianWindow(QMainWindow):
    def __init__(self, config: Config, mode:str):
        super().__init__()
        self._config = config
        self._mode = mode
        self._ui = Ui_ProcessingWindow()
        self._ui.setupUi(self)
        title = 'Bayesian Training' if mode.lower() == 'training' else 'Bayesian Testing'
        self.setWindowTitle(title)
        self._bayesian_thread = None
        self._worker = None
        self._ui.exit_button.clicked.connect(self._exit)
        self.run_bayesian()

    def run_bayesian(self):
        if self._bayesian_thread or self._worker:
            return
        self._bayesian_thread = QThread()
        self._worker = BayesianWorker(self._config, self._mode)
        self._worker.moveToThread(self._bayesian_thread)
        self._bayesian_thread.started.connect(self._worker.run)
        self._worker.output.connect(self._show_output)
        self._worker.error.connect(self._show_output)
        self._worker.finished.connect(self._bayesian_thread.quit)
        self._bayesian_thread.start()

    def _exit(self):
        if self._worker:
            self._worker.stop()
        if self._bayesian_thread:
            self._bayesian_thread.quit()
            self._bayesian_thread.wait(1000)
        self.close()

    def closeEvent(self, event):
        if self._worker:
            self._worker.stop()
        if self._bayesian_thread:
            self._bayesian_thread.quit()
            self._bayesian_thread.wait(1000)
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
        self.setWindowTitle('EyeSpy')

        self._config = Config()
        self.processing_window = None
        self.config_window = None
        self.bayesian_window = None

        self._ui.live_process_button.clicked.connect(self.start_live_processing)
        self._ui.batch_process_button.clicked.connect(self.start_batch_processing)
        self._ui.training_button.clicked.connect(self.start_training)
        self._ui.testing_button.clicked.connect(self.start_testing)
        self._ui.config_button.clicked.connect(self.show_config)

    def _validate_directory(self, dirs: Iterable) -> bool:
        for directory in dirs:
            if not directory:
                QMessageBox.warning(self, 'Config Error', 'No director[y/ies] selected. Select directory in settings before testing.')
                return False
            if not directory.exists():
                QMessageBox.warning(self, 'Config Error', f'Selected directory {self._config.directory} does not appear to exist or cannot be accessed.')
                return False
        return True

    def start_live_processing(self) -> None:
        if not self._validate_directory([self._config.directory]):
            return
        if self.processing_window is None or not self.processing_window.isVisible():
            self.processing_window = ProcessingWindow(self._config)
        self.processing_window.show()
        self.processing_window.raise_()
        self.processing_window.activateWindow()

    def start_batch_processing(self):
        if not self._validate_directory([self._config.directory]):
            return
        if self.processing_window is None or not self.processing_window.isVisible():
            self.processing_window = ProcessingWindow(self._config, live=False)
        self.processing_window.show()
        self.processing_window.raise_()
        self.processing_window.activateWindow()

    def start_training(self):
        if not self._validate_directory([self._config.training_directory_raw, self._config.training_directory_truth]):
            return
        if self.bayesian_window is None or not self.bayesian_window.isVisible():
            self.bayesian_window = BayesianWindow(self._config, mode='train')
        self.bayesian_window.show()
        self.bayesian_window.raise_()
        self.bayesian_window.activateWindow()

    def start_testing(self):
        if not self._validate_directory([self._config.testing_directory_raw, self._config.testing_directory_truth]):
            return
        if self.bayesian_window is None or not self.bayesian_window.isVisible():
            self.bayesian_window = BayesianWindow(self._config, mode='test')
        self.bayesian_window.show()
        self.bayesian_window.raise_()
        self.bayesian_window.activateWindow()

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