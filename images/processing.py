# TODO
# Move processing logic from filehandler.py
# Generate statistically sound decision boundary for thresholding
# Test/optimize
import statistics as stat
import numpy as np
import cv2 as cv
from images.flyimage import FlyImage, CziFlyImage
import math

class Processor:
    pass

def get_contour(image: FlyImage|CziFlyImage, threshold1: float, threshold2: float) -> np.ndarray:
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

    processed_array = cv.normalize(processed_array, dst = None, alpha = 0, beta = 255,
                                   norm_type = cv.NORM_MINMAX, dtype = cv.CV_8U)
    #Morphological operations, for the same reasons as above.
    processed_array = cv.morphologyEx(processed_array, cv.MORPH_OPEN, np.ones((5, 5), np.uint8))
    processed_array = cv.morphologyEx(processed_array, cv.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    contours, hierarchy = cv.findContours(processed_array, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)

    try:
        return max(contours, key=cv.contourArea)
    except:
        raise ValueError(f'Image too dark!')

def get_mean_circular(image: FlyImage|CziFlyImage, contour: np.ndarray) -> float:
    ellipse = cv.fitEllipse(contour)
    cx, cy = ellipse[0]
    major, minor = ellipse[1]
    theta = math.radians(ellipse[2])

    while theta > 2 * math.pi:
        theta = theta - (2 * math.pi)
    while theta < 0:
        theta = theta + (2 * math.pi)
    if theta > math.pi:
        theta = theta - math.pi

    if theta <= (math.pi/2):
        y_radius = (major / 2) * math.sin(theta)
        x_radius = (major / 2) * math.cos(theta)
    elif (math.pi/2) < theta <= math.pi:
        theta = math.pi - theta
        y_radius = (major / 2) * math.sin(theta)
        x_radius = (major / 2) * math.cos(theta)

    y_shape, x_shape = image.array.shape
    if cy + y_radius > (y_shape - 1):
        y_radius = (y_shape - 1) - cy
    if cx + x_radius > (x_shape - 1):
        x_radius = (x_shape - 1) - cx
    if cy - y_radius < 0:
        y_radius = cy
    if cx - x_radius < 0:
        x_radius = cx
    radius = min(y_radius, x_radius, image.scaling)
    rad_squared = pow(radius, 2)
    intensity_sum, count = (0, 0)
    for i in range(image.array.shape[0]):
        y_radius_squared = (i - cy) ** 2
        if y_radius_squared < rad_squared:
            x_roi = np.where((np.arange(image.array.shape[1]) - cx) ** 2 + y_radius_squared < rad_squared)[0]
            intensity_sum += image.array[i, x_roi].sum()
            count += len(x_roi)
    return 0 if count == 0 else round(float(intensity_sum / count), 3)



def _proportional_scale(arr: np.ndarray, white_point: int) -> np.ndarray:
    """Scales the image proportionally to the 95th percentile
    of pixel brightness in the image array."""
    ubound = np.percentile(arr, 95)
    return np.clip(arr * (white_point / ubound), None, ubound)
