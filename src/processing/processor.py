import numpy as np
import cv2 as cv
from src.processing.processing_functions import Circle
from src.processing.processing_result import FluorescenceResult
from src.images.image import BaseImage
from typing import Callable

class Processor:
    def __init__(self, normalizer: Callable, masker: Callable, fitter: Callable):
        self._normalizer = normalizer
        self._masker = masker
        self._fitter = fitter

    def circular_mean_fluorescence(self, img_array: np.ndarray, scaling: float, white_point: int) -> (float, Circle):
        processed_img = self.process(img_array, white_point)
        params = self._fitter(processed_img, scaling)
        return mean_intensity(img_array, params), params

    def process(self, img: BaseImage) -> FluorescenceResult:
        processed_img = np.copy(img.array)
        binary_img = self.binary_mask(img)
        fitting_img = cv.normalize(binary_img, dst=None, alpha=0, beta=255,
                                     norm_type=cv.NORM_MINMAX, dtype=cv.CV_8U)
        fitting_img = cv.morphologyEx(fitting_img, cv.MORPH_OPEN, np.ones((5, 5), np.uint8))
        fitting_img = cv.morphologyEx(fitting_img, cv.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        params = self._fitter(fitting_img, white_point=img.white_point, img_scaling=img.scaling)
        mean_fluorescence = mean_intensity(img.array, params)
        return FluorescenceResult(normalized=True if self._normalizer is not None else False,
                                writeable_img=processed_img, binary_img=binary_img, center=(params.center_y, params.center_x),
                                radius=params.radius, mean_fluorescence=mean_fluorescence)

    def binary_mask(self, img: BaseImage):
        processed_img = np.copy(img.array)
        if self._normalizer is not None:
            processed_img = self._normalizer(processed_img, white_point=img.white_point, scaling=img.scaling)
        return self._masker(processed_img, white_point=img.white_point, img_scaling=img.scaling)

    def circular_roi(self, img: BaseImage):
        results = self.process(img)
        y_coords, x_coords = np.ogrid[:img.array.shape[0], :img.array.shape[1]]
        center_x, center_y = results.center
        dist_squared = (y_coords - center_y) ** 2 + (x_coords - center_x) ** 2
        mask = dist_squared <= results.radius ** 2
        return np.where(mask, 255, 0)

def mean_intensity(img_array: np.ndarray, roi: Circle) -> float:
    y_coords, x_coords = np.ogrid[:img_array.shape[0], :img_array.shape[1]]
    dist_squared = (y_coords - roi.center_y) ** 2 + (x_coords - roi.center_x) ** 2
    mask = dist_squared <= roi.radius ** 2
    selected_pixels = img_array[mask]
    return np.mean(selected_pixels) if selected_pixels.size != 0 else 0.0