# TODO
# Move processing logic from filehandler.py
# Generate statistically sound decision boundary for thresholding
# Test/optimize
import numpy as np
import cv2 as cv
from images.flyimage import FlyImage, CziFlyImage

class Processor:
    pass

def get_mean_fluorescence(image: FlyImage|CziFlyImage, threshold1: float, threshold2: float):
    processed_array = np.copy(image.array)

    #Scaling each value in the array proportionally to its 95th percentile of brightness
    processed_array = _proportional_scale(processed_array, image.white_point)

    #Apply thresholding to the array
    processed_array = np.where(processed_array > threshold1,1, 0)

    #High data precision is no longer necessary; reduce bit depth of the array for OpenCV compatability
    processed_array = cv.normalize(processed_array, dst=None, alpha=0, beta=255,
                                   norm_type=cv.NORM_MINMAX, dtype= cv.CV_8U)

    #Morphological Operations account for potential noise in the binary mask
    processed_array = cv.morphologyEx(processed_array, cv.MORPH_OPEN, np.ones((5, 5), np.uint8))
    processed_array = cv.morphologyEx(processed_array, cv.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    #The distance transform allows us to weight pixels relative to other 'on' pixels.
    processed_array = cv.distanceTransform(processed_array, cv.DIST_L2, 5)

    #Thresholding is applied, again. This allows us to filter low-connectivity regions of the image.
    processed_array = np.where(processed_array > threshold2, 1, 0)

    #Morphological operations, for the same reasons as above.


    del image
    return

def _proportional_scale(arr: np.ndarray, white_point: int) -> np.ndarray:
    """Scales the image proportionally to the 95th percentile
    of pixel brightness in the image array."""
    ubound = np.percentile(arr, 95)
    def scale(x):
        return ubound if x > ubound else (x * white_point) / ubound
    vectorize_scale = np.vectorize(scale)
    return vectorize_scale(arr)
