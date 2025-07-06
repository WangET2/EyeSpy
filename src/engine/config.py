from collections.abc import Callable
from configparser import ConfigParser
from pathlib import Path
from functools import partial
from src.images.image import BaseImage, TiffImage, CziImage, stable_read
from src.engine.images_queue import BaseQueue, LazyQueue, EagerQueue
from src.images.bayesian import Trainer, Tester
from src.images.processing import Processor, normalize
from czifile import imread as cziread
from tifffile import imread as tiffread

class Config:
    def __init__(self):
        self._config = ConfigParser()
        if not Path('options.ini').exists():
            self._create_default()
        self._config.read('options.ini')

    @property
    def directory(self) -> Path:
        to_return = self._config.get('files', 'Directory', fallback='None')
        return Path(to_return) if to_return.lower() != 'none' else None

    @property
    def queue_type(self) -> str:
        return self._config.get('files', 'Queue_Type', fallback='File')

    @property
    def enqueue_existing(self) -> bool:
        return self._config.getboolean('files','Enqueue_Existing', fallback=False)

    @property
    def write_roi(self) -> bool:
        return self._config.getboolean('files', 'Write_ROI', fallback=False)

    @property
    def output_directory(self) -> Path:
        to_return =  self._config.get('files', 'Output_Directory', fallback=self.directory)
        return Path(to_return) if to_return.lower() != 'none' else None

    @property
    def image_format(self) -> str:
        return self._config.get('images','Image_Format',fallback='CZI')

    @property
    def white_point(self) -> int:
        return self._config.getint('images', 'White_Point', fallback=4095)

    @property
    def scaling(self) -> float:
        return self._config.getfloat('images', 'Scaling', fallback=3.45)

    @property
    def max_radius(self) -> int:
        return self._config.getint('images', 'Max_Radius', fallback = 2500)

    @property
    def masking_method(self) -> str:
        return self._config.get('processing', 'Masking_Method', fallback='Thresholding')

    @property
    def normalization(self) -> bool:
        return self._config.getboolean('processing', 'Normalization', fallback=True)

    @property
    def normalization_percentile(self) -> float:
        return self._config.getfloat('processing', 'Normalization_Percentile', fallback=99.5)

    @property
    def threshold_level(self) -> int:
        return self._config.getint('processing', 'Threshold_Level', fallback=1526)

    @property
    def center_method(self) -> str:
        return self._config.get('processing', 'Center_Method', fallback='Median')

    @property
    def radius_method(self) -> str:
        return self._config.get('processing', 'Radius_Method', fallback='Contour')

    @property
    def required_stable(self) -> int:
        return self._config.getint('processing', 'Required_Stable', fallback=3)

    @property
    def check_delay(self) -> float:
        return self._config.getfloat('processing', 'Check_Delay', fallback=0.2)

    @property
    def max_checks(self) -> int:
        return self._config.getint('processing', 'Max_Checks', fallback=10)

    @property
    def training_directory_raw(self) -> Path:
        to_return = self._config.get('bayesian', 'Training_Directory_Raw', fallback='./training/raw')
        return Path(to_return) if to_return.lower() != 'none' else None

    @property
    def training_directory_truth(self) -> Path:
        to_return = self._config.get('bayesian', 'Training_Directory_Truth', fallback='./training/truth')
        return Path(to_return) if to_return.lower() != 'none' else None

    @property
    def testing_directory_raw(self) -> Path:
        to_return = self._config.get('bayesian', 'Testing_Directory_Raw', fallback = './testing/raw')
        return Path(to_return) if to_return.lower() != 'none' else None

    @property
    def testing_directory_truth(self) -> Path:
        to_return = self._config.get('bayesian', 'Testing_Directory_Truth', fallback='./testing/truth')
        return Path(to_return) if to_return.lower() != 'none' else None

    @property
    def truth_intensity(self) -> int:
        return self._config.getint('bayesian', 'Truth_Intensity', fallback=255)

    @property
    def testing_method(self) -> str:
        return self._config.get('bayesian', 'Testing_Method', fallback='Circle')

    def _create_default(self):
        with open('options.ini', 'w') as config_file:
            self._config['files'] = {'Directory': 'None',
                                     'Queue_Type': 'File',
                                     'Enqueue_Existing': 'False',
                                     'Write_ROI': 'False',
                                     'Output_Directory': 'None'}
            self._config['images'] = {'Image_Format': 'CZI',
                                        'White_Point': '4095',
                                        'Scaling': '3.45',
                                        'Max_Radius': '2500'}
            self._config['processing'] = {'Masking_Method': 'Thresholding',
                                        'Normalization': 'True',
                                        'Normalization_Percentile': '99.5',
                                        'Threshold_Level': '1526',
                                        'Center_Method': 'Median',
                                        'Radius_Method': 'Eigenvalue',
                                        'Required_Stable': '3',
                                        'Check_Delay': '0.2',
                                        'Max_Checks': '10'}
            self._config['bayesian'] = {'Training_Directory_Raw': './training/raw',
                                        'Training_Directory_Truth': './training/truth',
                                        'Testing_Directory_Raw': './testing/raw',
                                        'Testing_Directory_Truth': './testing/truth',
                                        'Truth_Intensity': '255',
                                        'Testing_Method': 'Circle'}
            self._config.write(config_file)

    def save(self) -> None:
        with open('options.ini', 'w') as config_file:
            self._config.write(config_file)

    def set(self, section: str, option: str, value: str|int|float|bool) -> None:
        if section not in self._config:
            return
        self._config.set(section, option, str(value))

    def reset(self) -> None:
        self._create_default()

    def validate(self) -> None:
        if not self._config.get('images', 'White_Point').isdigit():
            raise ValueError('Image White Point must be an integer value.')
        if not self._config.get('images', 'Scaling').replace('.','',1).isdigit():
            raise ValueError('Image Scaling must be a numeric value.')
        if not self._config.get('images', 'Max_Radius').isdigit():
            raise ValueError('Maximum ROI Radius must be an integer value.')
        if not self._config.get('processing', 'Normalization_Percentile').replace('.','',1).isdigit():
            raise ValueError('Normalization Percentile must be a numeric value.')
        if not self._config.get('processing','Threshold_Level').isdigit():
            raise ValueError('Threshold Intensity must be an integer value.')
        if not self._config.get('processing', 'Required_Stable').isdigit():
            raise ValueError('Stability Checks must be an integer value.')
        if not self._config.get('processing', 'Check_Delay').replace('.','',1).isdigit():
            raise ValueError('Delay Between Stability Checks must be a numeric value.')
        if not self._config.get('processing', 'Max_Checks').isdigit():
            raise ValueError('Maximum Stability Checks must be an integer value.')
        if not self._config.get('bayesian', 'Truth_Intensity').isdigit():
            raise ValueError('Truth Intensity must be an integer value.')

    def create_image(self, img_path: Path, reader: Callable) -> BaseImage:
        if self.image_format == 'CZI':
            return CziImage(img_path, reader=reader)
        return TiffImage(img_path, scaling=self.scaling, white_point=self.white_point, reader=reader)

    def create_queue(self, reader: Callable=None) -> BaseQueue:
        if reader is None:
            reader = self.stable_reader()
        factory = partial(self.create_image, reader=reader)
        queue_type = EagerQueue if self.queue_type == 'Image' else LazyQueue
        return queue_type(self.directory, image_factory=factory, file_format=self.image_format, enqueue_existing=self.enqueue_existing)

    def create_processor(self) -> Processor:
        return Processor(normalization=self.normalization, normalization_percentile=self.normalization_percentile,
                         masking_method=self.masking_method, threshold_level=self.threshold_level,
                         radius_method=self.radius_method, max_radius=self.max_radius)

    def stable_reader(self) -> Callable:
        reader = cziread if self.image_format == 'CZI' else tiffread
        return partial(stable_read, reader=reader, max_attempts=self.max_checks, delay_s=self.check_delay, required_stable=self.required_stable)

    def create_trainer(self) -> Trainer:
        preprocessing = partial(normalize, percentile=self.normalization_percentile) if self.normalization else None
        return Trainer(raw_dir=self.training_directory_raw, truth_dir=self.training_directory_truth,
                       truth_intensity=self.truth_intensity, preprocessing=preprocessing)

    def create_tester(self) -> Tester:
        temp_processor = self.create_processor()
        pipeline = temp_processor.process
        if self.testing_method.lower() == 'circle':
            pipeline = temp_processor.circular_roi
        return Tester(raw_dir=self.testing_directory_raw, truth_dir=self.testing_directory_truth,
                      truth_intensity=self.truth_intensity, pipeline=pipeline)