import abc
import xml.etree.ElementTree as ET
import numpy as np
from pathlib import Path
import czifile

class BaseFlyImage:
    @property
    def array(self):
        return self._array

    @property
    def scaling(self):
        return self._scaling

    @property
    def white_point(self):
        return self._white_point

class FlyImage(BaseFlyImage):
    """Used for persistent storage of image arrays, preventing errors
    caused by attempting to follow paths that no longer exist."""

    def __init__(self, array: np.ndarray, scaling: int, white_point: int):
        #Handle reading the array from the file upstream, for flexibility.
        self._array = array
        #Scaling is provided by the config.
        self._scaling = scaling
        #White point is provided by the config.
        self._white_point = white_point


class CziFlyImage(BaseFlyImage):
    """CZI fly image. Stores image arrays and scaling persistently
    upon object creation, but all other metadata is lost."""

    def __init__(self, image_directory: Path):
        try:
            img = czifile.CziFile(image_directory)
        except:
            raise FileNotFoundError(f'Could not find {image_directory}.')

        try:
            metadata = img.metadata()
            root = ET.fromstring(metadata)
            scaling = root.find(".//ImagePixelSize")
            self._scaling = float(scaling.text[0:scaling.text.index(',')])
            self._white_point = int(root.find(".//CameraPixelMaximum").text)
        except:
            raise FileNotFoundError(f'Metadata of {image_directory} could not be parsed!')

        try:
            self._array = img.asarray()[0, :, :, 0]
        except:
            raise ValueError("File format was not CZI or could not be loaded as expected.")


