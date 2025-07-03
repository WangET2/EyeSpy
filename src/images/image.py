from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET
import numpy as np
from pathlib import Path
import czifile
import tifffile as tf
from typing import Callable
import time

class BaseImage(ABC):
    def __init__(self, full_path: Path, reader: Callable):
        self._name = full_path.stem
        self._array = reader(full_path)

    def __repr__(self):
        return self.name

    @property
    def array(self) -> np.ndarray:
        return self._array

    @property
    def name(self) -> str:
        return self._name

    @property
    @abstractmethod
    def scaling(self) -> float:
        raise NotImplementedError

    @property
    @abstractmethod
    def white_point(self) -> int:
        raise NotImplementedError

class TiffImage(BaseImage):
    def __init__(self, full_path: Path, scaling: float, white_point: int, *, reader: Callable=tf.imread):
        super().__init__(full_path, reader)
        self._scaling = scaling
        self._white_point = white_point

    @property
    def scaling(self) -> float:
        return self._scaling

    @property
    def white_point(self) -> int:
        return self._white_point

class CziImage(BaseImage):
    def __init__(self, full_path: Path, *, reader:Callable=czifile.imread):
        super().__init__(full_path, reader)
        img = czifile.CziFile(full_path)
        try:
            metadata = img.metadata()
            root = ET.fromstring(metadata)
            scaling = root.find(".//ImagePixelSize")
            self._scaling = float(scaling.text[0:scaling.text.index(',')])
            self._white_point = int(root.find(".//CameraPixelMaximum").text)
        except:
            raise FileNotFoundError(f'Metadata of {full_path} could not be parsed!')
        try:
            self._array = self._array[0, :, :, 0]
        except:
            raise ValueError("File format was not CZI or could not be loaded as expected.")

    @property
    def scaling(self) -> float:
        return self._scaling

    @property
    def white_point(self) -> int:
        return self._white_point

def stable_read(img_path: Path, reader: Callable, max_attempts: int, delay_s: float, required_stable: int) -> np.ndarray | None:
    attempts = 0
    stable_count = 0
    try:
        while attempts <= max_attempts:
            if not img_path.exists():
                return None
            initial_size = img_path.stat().st_size
            time.sleep(delay_s)
            current_size = img_path.stat().st_size
            if initial_size == current_size and current_size > 0:
                stable_count += 1
            else:
                stable_count = 0
            if stable_count >= required_stable:
                break
            attempts += 1
        if attempts > max_attempts:
            return None
        return reader(img_path)
    except FileNotFoundError:
        print(f"Error accessing file: {img_path} no longer exists or cannot be accessed.")
    return None