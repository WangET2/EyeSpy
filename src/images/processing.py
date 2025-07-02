import numpy as np
import cv2 as cv
import math
from functools import partial
from collections import namedtuple

Circle = namedtuple('Circle', ['center_y', 'center_x', 'radius'])

class Processor:
    def __init__(self, normalization: bool=True, normalization_percentile:float=99.7,
                 masking_method:str='Thresholding', threshold_level:int=1526,
                 radius_method:str='Eigenvalue', max_radius:int=2500):
        self._normalizer = None
        if normalization:
            self._normalizer = partial(normalize, percentile=normalization_percentile)
        self._masker = partial(threshold_image, threshold=threshold_level)
        if masking_method == 'K-Means':
            self._masker = kmeans
        self._fitter = partial(circle_params_contour, max_radius=max_radius)
        if radius_method == 'Eigenvalue':
            self._fitter = partial(circle_params_eigenvalue, max_radius=max_radius)


    def circular_mean_fluorescence(self, img_array: np.ndarray, scaling: float, white_point: int) -> (float, Circle):
        processed_img = np.copy(img_array)
        if self._normalizer:
            processed_img = self._normalizer(img_array, white_point)
        processed_img = self._masker(processed_img)

        processed_img = cv.normalize(processed_img, dst = None, alpha = 0, beta = 255,
                                       norm_type = cv.NORM_MINMAX, dtype = cv.CV_8U)
        processed_img = cv.morphologyEx(processed_img, cv.MORPH_OPEN, np.ones((5, 5), np.uint8))
        processed_img = cv.morphologyEx(processed_img, cv.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        params = self._fitter(processed_img, scaling)
        return mean_intensity(img_array, params), params

def normalize(img_array, white_point:int, percentile: float) -> np.ndarray:
    ubound = np.percentile(img_array, percentile)
    return np.clip(img_array * (white_point / ubound), None, white_point)

def kmeans(img_array: np.ndarray) -> np.ndarray:
    flattened = np.float32(img_array.flatten())
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    ret, label, center = cv.kmeans(flattened, 2, None, criteria, 15, cv.KMEANS_RANDOM_CENTERS)
    return center[label.flatten()].reshape(img_array.shape)

def threshold_image(img_array: np.ndarray, threshold: int) -> np.ndarray:
    return np.where(img_array > threshold, 1, 0)

def circle_params_contour(img_array: np.ndarray, img_scaling: float, max_radius: int) -> Circle:
    #Distance Transform
    img_array = cv.distanceTransform(img_array, cv.DIST_L2, 5)
    img_array = np.where(img_array > 7, 1, 0)
    img_array = cv.normalize(img_array, dst = None, alpha = 0, beta = 255,
                                 norm_type = cv.NORM_MINMAX, dtype = cv.CV_8U)
    img_array = cv.morphologyEx(img_array, cv.MORPH_OPEN, np.ones((5, 5), np.uint8))
    img_array = cv.morphologyEx(img_array, cv.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    #Contour Fitting
    contours, _ = cv.findContours(img_array, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    eye = max(contours, key=cv.contourArea)

    #Ellipse Fitting (calculate center)
    ellipse = cv.fitEllipse(eye)
    center_x, center_y = ellipse[0]
    major, minor = ellipse[1]
    theta = math.radians(ellipse[2])

    #Calculate Radius
    radius = min(minor // 2, max_radius // img_scaling)
    return Circle(center_y, center_x, radius)

def circle_params_eigenvalue(img_array: np.ndarray, img_scaling: float, max_radius: int) -> Circle:
    y_coords, x_coords = np.where(img_array > 0)
    #Estimate center with median
    center_y = np.partition(y_coords, y_coords.size // 2)[y_coords.size // 2]
    center_x = np.partition(x_coords, x_coords.size // 2)[x_coords.size // 2]

    #Recenter data to (0,0)
    recentered_y = y_coords - center_y
    recentered_x = x_coords - center_x

    #Covariance matrix and eigenvalues to estimate radius
    covar_matrix = np.cov(np.vstack((recentered_y, recentered_x)))
    eigenvalues = np.linalg.eigvals(covar_matrix)
    min_eigenvalue = min(eigenvalues[0], eigenvalues[1])
    est_radius =  2 * math.sqrt(min_eigenvalue)
    radius = min(est_radius, max_radius // img_scaling)
    return Circle(center_y, center_x, radius)

def mean_intensity(img_array: np.ndarray, roi: Circle) -> float:
    y_coords, x_coords = np.ogrid[:img_array.shape[0], :img_array.shape[1]]
    dist_squared = (y_coords - roi.center_y) ** 2 + (x_coords - roi.center_x) ** 2
    mask = dist_squared <= roi.radius ** 2
    selected_pixels = img_array[mask]
    return np.mean(selected_pixels) if selected_pixels.size != 0 else 0.0