from pathlib import Path
from typing import Callable
from src.images.image import BaseImage
import numpy as np
import tifffile as tf
import czifile

class Trainer:
    def __init__(self, raw_dir: Path, truth_dir: Path, truth_intensity:int=255, raw_reader: Callable=czifile.imread,
                 truth_reader:Callable = tf.imread, raw_extension: str='czi',
                 truth_extension: str='tif', preprocessing: Callable=None, bins:int=4096):
        self._raw_dir = raw_dir
        self._truth_dir = truth_dir
        self._truth_intensity = truth_intensity
        self._raw_reader = raw_reader
        self._truth_reader = truth_reader
        self._raw_extension = raw_extension
        self._truth_extension = truth_extension
        self._preprocessing = preprocessing
        self._true = []
        self._false = []
        self._bins = bins

    def update(self, img_name:str, **kwargs) -> None:
        raw_image = self._raw_reader(self._raw_dir / Path(f'{img_name}.{self._raw_extension}'))
        if raw_image.ndim == 4:
            raw_image = raw_image[0,:,:,0]
        truth = self._truth_reader(self._truth_dir / Path(f'{img_name}.{self._truth_extension}'))
        if self._preprocessing is not None:
            raw_image = self._preprocessing(raw_image, **kwargs)
        self._true.append(raw_image[truth==self._truth_intensity])
        self._false.append(raw_image[truth==0])


    def train(self) -> int:
        current_true = np.concatenate(self._true)
        current_false = np.concatenate(self._false)
        p_true = len(current_true) / (len(current_true) + len(current_false))
        p_false = 1 - p_true
        hist_true, _ = np.histogram(current_true, bins=self._bins, range=(0, self._bins-1), density=True)
        hist_false, _ = np.histogram(current_false, bins=self._bins, range=(0, self._bins-1), density=True)
        return np.argmin(np.abs((hist_true * p_true) - (hist_false * p_false)))

class Trainer:
    def __init__(self, truth_intensity:int=255, preprocessing: Callable=None, bins:int=4096):
        self._truth_intensity = truth_intensity
        self._preprocessing = preprocessing
        self._bins = bins
        self._true = []
        self._false = []

    def update(self, raw_image: BaseImage, truth_image: BaseImage, **kwargs):
        raw_array = np.copy(raw_image.array)
        if self._preprocessing is not None:
            raw_array = self._preprocessing(raw_array, **kwargs)
        self._true.append(raw_array[truth_image.array==self._truth_intensity])
        self._false.append(raw_array[truth_image.array==0])

    def train(self) -> int:
        current_true = np.concatenate(self._true)
        current_false = np.concatenate(self._false)
        p_true = len(current_true) / (len(current_true) + len(current_false))
        p_false = 1 - p_true
        hist_true, _ = np.histogram(current_true, bins=self._bins, range=(0, self._bins-1), density=True)
        hist_false, _ = np.histogram(current_false, bins=self._bins, range=(0, self._bins-1), density=True)
        return np.argmin(np.abs((hist_true * p_true) - (hist_false * p_false)))


class Tester:
    def __init__(self, raw_dir: Path, truth_dir: Path, truth_intensity:int=255,
                 raw_extension: str='czi', truth_extension: str='tif',
                 raw_reader: Callable=czifile.imread, truth_reader:Callable = tf.imread, pipeline: Callable=None):
        self._raw_dir = raw_dir
        self._truth_dir = truth_dir
        self._truth_intensity = truth_intensity
        self._raw_reader = raw_reader
        self._truth_reader = truth_reader
        self._raw_extension = raw_extension
        self._truth_extension = truth_extension
        self._pipeline = pipeline
        self._true_positive = 0
        self._false_positive = 0
        self._true_negative = 0
        self._false_negative = 0
        self._total_pixels = 0
        self._actual = 0
        self._predicted = 0
        self._total_images = 0

    def update(self, img_name: str, **kwargs) -> None:
        current_image = self._raw_reader(self._raw_dir / Path(f'{img_name}.{self._raw_extension}'))
        if current_image.ndim == 4:
            current_image = current_image[0,:,:,0]
        processed_image = self._pipeline(current_image, **kwargs)
        current_mask = self._truth_reader(self._truth_dir / Path(f'{img_name}.{self._truth_extension}'))
        y_shape, x_shape = current_image.shape
        self._total_pixels += y_shape * x_shape
        self._true_positive += np.sum((processed_image==self._truth_intensity) & (current_mask==self._truth_intensity))
        self._false_positive += np.sum((processed_image==self._truth_intensity) & (current_mask==0))
        self._true_negative += np.sum((processed_image==0) & (current_mask==0))
        self._false_negative += np.sum((processed_image==0) & (current_mask==self._truth_intensity))
        self._actual +=  np.mean(current_image[current_mask==self._truth_intensity])
        self._predicted += np.mean(current_image[processed_image==self._truth_intensity])
        self._total_images += 1


    def report(self) -> str:
        precision = self._true_positive / (self._true_positive + self._false_positive)
        sensitivity = self._true_positive / (self._true_positive + self._false_negative)
        to_return = f'''Correctly Identified: {self._true_positive + self._true_negative} ~~~~~ {((self._true_positive + self._true_negative)/self._total_pixels)*100:.4f}%
        Incorrectly Identified: {self._false_positive + self._false_negative} ~~~~~ {((self._false_positive + self._false_negative)/self._total_pixels)*100:.4f}%
    
        True Positive: {self._true_positive} ~~~~~ {(self._true_positive /(self._true_positive + self._false_negative))*100:.4f}%
        False Positive: {self._false_positive} ~~~~~ {(self._false_positive /(self._false_positive + self._true_negative))*100:.4f}%
        
        True Negative: {self._true_negative} ~~~~~ {(self._true_negative / (self._true_negative + self._false_positive)) * 100:.4f}%
        False Negative: {self._false_negative} ~~~~~ {(self._false_negative / (self._false_negative + self._true_positive)) * 100:.4f}%
        
        PRECISION: {precision*100:.4f}%
        SENSITIVITY: {sensitivity*100:.4f}%
        F1 SCORE: {(2 * precision * sensitivity) / (precision + sensitivity) * 100:.4f}%
        
        Mean difference in fluorescence (actual vs. predicted): {np.abs(self._actual - self._predicted) / self._total_images:.4f}
        '''
        return to_return