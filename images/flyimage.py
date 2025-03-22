import abc

import numpy as np
from pathlib import Path
import czifile

@ abc.ABC
class FlyImage:
    @property
    def array(self):
        return self._array

    @property
    def scaling(self):
        return self._scaling

    @property
    def white_point(self):
        return self._white_point

class OtherFlyImage(FlyImage):
    """Used for persistent storage of image arrays, preventing errors
    caused by attempting to follow paths that no longer exist."""

    def __init__(self, array: np.ndarray, scaling: int, white_point: int):
        #Handle reading the array from the file upstream, for flexibility.
        self._array = array
        #Scaling is provided by the config.
        self._scaling = scaling
        #White point is provided by the config.
        self._white_point = white_point


class CziFlyImage(FlyImage):
    """CZI fly image. Stores image arrays and scaling persistently
    upon object creation, but all other metadata is lost."""

    def __init__(self, image_directory: Path):
        try:
            img = czifile.CziFile(image_directory)
        except:
            raise FileNotFoundError(f'Could not find {image_directory}.')

        #TODO clean up this mess...
        metadata = img.metadata(raw=False)
        self._scaling = str(metadata['ImageDocument']['Metadata']['Scaling']['Items']['Distance'][0]['Value'])
        self._scaling = float(self._scaling[:self._scaling.index('e')])

        try:
            self._array = img.asarray()[:, 1, 1, :]
        except:
            raise ValueError("File format was not CZI or could not be loaded as expected.")

        #TODO Check metadata for white point
        self._white_point = 0

