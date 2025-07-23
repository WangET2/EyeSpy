import numpy as np
from dataclasses import dataclass

@dataclass
class FluorescenceResult:
    normalized: bool
    writeable_img: np.ndarray
    binary_img: np.ndarray
    center: tuple[int, int]
    radius: int
    mean_fluorescence: float