import numpy as np
import cv2 as cv
import math
from collections import namedtuple

Circle = namedtuple('Circle', ['center_y', 'center_x', 'radius'])

def normalize(img_array, white_point:int, percentile: float, **kwargs) -> np.ndarray:
    ubound = np.percentile(img_array, percentile)
    return np.clip(img_array * (white_point / ubound), None, white_point)

def kmeans(img_array: np.ndarray, **kwargs) -> np.ndarray:
    flattened = np.float32(img_array.flatten())
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    ret, label, center = cv.kmeans(flattened, 2, None, criteria, 15, cv.KMEANS_RANDOM_CENTERS)
    return center[label.flatten()].reshape(img_array.shape)

def threshold_image(img_array: np.ndarray, threshold: int, **kwargs) -> np.ndarray:
    return np.where(img_array > threshold, 1, 0)

def circle_params_contour(img_array: np.ndarray, img_scaling: float, max_radius: int, **kwargs) -> Circle:
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

def circle_params_eigenvalue(img_array: np.ndarray, img_scaling: float, max_radius: int, **kwargs) -> Circle:
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

