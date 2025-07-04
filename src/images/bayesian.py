from pathlib import Path
from typing import Callable
import numpy as np
import tifffile as tf
import czifile

class Trainer:
    def __init__(self, raw_dir: Path, truth_dir: Path, truth_intensity:int=255, raw_reader: Callable=czifile.imread,
                 truth_reader:Callable = tf.imread, preprocessing: Callable=None, bins:int=4096):
        self._raw_dir = raw_dir
        self._truth_dir = truth_dir
        self._truth_intensity = truth_intensity
        self._raw_reader = raw_reader
        self._truth_reader = truth_reader
        self._preprocessing = preprocessing
        self._true = []
        self._false = []
        self._bins = bins

    def update(self, img_name:str) -> None:
        raw_image = self._raw_reader(self._raw_dir / Path(img_name))
        if raw_image.ndim == 4:
            raw_image = raw_image[0,:,:,0]
        truth = self._truth_reader(self._truth_dir / Path(img_name))
        if self._preprocessing is not None:
            raw_image = self._preprocessing(raw_image)
        self._true.append(raw_image[truth==self._truth_intensity])
        self._false.append(raw_image[truth==0])


    def train(self) -> np.int_:
        current_true = np.concatenate(self._true)
        current_false = np.concatenate(self._false)
        p_true = len(current_true) / (len(current_true) + len(current_false))
        p_false = 1 - p_true
        hist_true, _ = np.histogram(current_true, bins=self._bins, range=(0, self._bins), density=True)
        hist_false, _ = np.histogram(current_false, bins=self._bins, range=(0, self._bins), density=True)
        return np.argmin(np.abs((hist_true * p_true) - (hist_false * p_false)))

class Tester:
    def __init__(self, direc: Path, pipeline: Callable):
        self._direc = direc
        self._pipeline = pipeline

    def update(self) -> None:
        pass

    def report(self): -> str:
        pass