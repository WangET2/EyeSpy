from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET
import numpy as np
from pathlib import Path
import czifile
import tifffile as tf
from typing import Callable

class BaseImage(ABC):
    def __init__(self, full_path: Path, reader: Callable):
        self._array = reader(full_path)

    @property
    def array(self) -> np.ndarray:
        return self._array

    @property
    @abstractmethod
    def scaling(self) -> float:
        raise NotImplementedError

    @property
    @abstractmethod
    def white_point(self) -> int:
        raise NotImplementedError

class TiffImage(BaseImage):
    def __init__(self, full_path: Path, scaling: float, white_point: int):
        super().__init__(full_path, tf.imread)
        self._scaling = scaling
        self._white_point = white_point

    @property
    def scaling(self) -> float:
        return self._scaling

    @property
    def white_point(self) -> int:
        return self._white_point

class CziImage(BaseImage):
    def __init__(self, full_path: Path):
        super().__init__(full_path, czifile.imread)
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
            self._array = img.asarray()[0, :, :, 0]
        except:
            raise ValueError("File format was not CZI or could not be loaded as expected.")

    @property
    def scaling(self) -> float:
        return self._scaling

    @property
    def white_point(self) -> int:
        return self._white_point
