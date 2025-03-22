import numpy as np
from pathlib import Path
import czifile

class FlyImage:
    """Used for persistent storage of image arrays, preventing errors
    caused by attempting to follow paths that no longer exist."""

    def __init__(self, array: np.ndarray, scaling: int):
        #Handle reading the array from the file upstream, for flexibility.
        self._array = array
        #Scaling is provided by the config.
        self._scaling = scaling

    @property
    def array(self) -> np.ndarray:
        """Array representation of the image."""
        return self._array

    @property
    def scaling(self) -> int:
        """Scaling of the image, in µm/pixel."""
        return self._scaling


class CziFlyImage:
    """CZI fly image. Stores image arrays and scaling persistently
    upon object creation, but all other metadata is lost."""

    def __init__(self, image_directory: Path):
        img = czifile.CziFile(image_directory)

        #TODO clean up this mess...
        metadata = img.metadata(raw=False)
        self._scaling = str(metadata['ImageDocument']['Metadata']['Scaling']['Items']['Distance'][0]['Value'])
        self._scaling = float(self._scaling[:self._scaling.index('e')])
        self._array = img.asarray()[:, 1, 1, :]

    @property
    def array(self) -> np.ndarray:
        """Array representation of the image."""
        return self._array

    @property
    def scaling(self):
        """Scaling of image, in µm/pixel."""
        return self._scaling
