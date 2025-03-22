# TODO
# Move processing logic from filehandler.py
# Generate statistically sound decision boundary for thresholding
# Test/optimize
import numpy as np

from images.flyimage import FlyImage, CziFlyImage

def get_mean_fluorescence(image: FlyImage|CziFlyImage):
    processed_array = np.copy(image.array)

    processed_array = _proportional_scale(processed_array)


    del image
    return

def _proportional_scale(arr: np.ndarray) -> np.ndarray:
    """Scales the image proportionally to the 95th percentile
    of pixel brightness in the image array."""