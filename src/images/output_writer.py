import csv
from datetime import datetime
from pathlib import Path
import numpy as np
import tifffile as tf
import os
from config import Config

class CSVWriter:
    def __init__(self, direc: Path, header: list[str]):
        name = self._create_name()
        self._header = header
        self._filepath = direc / f'{name}.csv'
        self._file = None
        self._writer = None

    def __enter__(self):
        self._file = open(self._filepath, 'w', newline='')
        self._writer = csv.writer(self._file)
        self._writer.writerow(self._header)
        return self

    def write_row(self, data: list):
        self._writer.writerow(data)
        self._file.flush()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.close()

    def _create_name(self):
        current_time = datetime.now()
        return current_time.strftime('%m%d%y_%H%M%S')

class TiffWriter:
    def __init__(self, direc: Path):
        self._direc = direc / Path('roi_drawn')
        if not os.path.exists(self._direc):
            os.mkdir(self._direc)

    def write_roi(self, img_array: np.ndarray, filename: str, center_y: int, center_x, radius: int) -> None:
        img_array = np.copy(img_array)
        y_coords, x_coords = np.ogrid[:img_array.shape[0], :img_array.shape[1]]
        dist_squared = (y_coords - center_y) ** 2 + (x_coords - center_x) ** 2
        inner = dist_squared < radius ** 2
        outline = dist_squared == radius ** 2
        img_array[inner] = 255
        img_array[outline] = 0
        tf.imwrite(self._direc / Path(filename + '.tiff'), img_array)